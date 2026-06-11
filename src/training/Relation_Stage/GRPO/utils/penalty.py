from .utils import is_overlapping,update_row,textset,find_context_robustly,find_all_occurrences,valid_mods_keys
import pandas as pd
from io import StringIO
import re
# from CQE import CQE
# from quantulum3 import parser
# cqe_parser = CQE.CQE()
import re
from datetime import datetime
import traceback
import json
import time
import uuid
import os
def penalty(docId,input):
    '''
        判断get过程中的惩罚
    '''
    try:
        # print(docId)
        penalty=0
        text = textset[docId]
        response = input
        # # --- 全新的、基于段落的解析流程 ---
        # timestamp = time.strftime('%Y%m%d_%H%M%S')
        # unique_id = uuid.uuid4().hex[:6]
        # filename = f"{docId}_{timestamp}_{unique_id}.txt"
        # os.makedirs("responses", exist_ok=True)

        # # 保存 response 内容到文件
        # with open(os.path.join("responses", filename), "w", encoding="utf-8") as f:
        #     f.write(response)
        llm_sections = response.strip().split('From the target sentences:')
        if len(llm_sections) <= 1:
            penalty -= 10
            return penalty
        
        tsv_data = []
        used_spans = set()  # 全局已占用区间，存储的是全局偏移量
        global_id_counter = 1
        annot_set_id = 1
        # print(len(llm_sections))
        for section_content in llm_sections[1:]:
            if not section_content.strip(): continue
            # 1. 从LLM的解释中，提取出它引用的原文“小段落”
            delimiter = "We can find the quantity with surface form"
            parts = section_content.split(delimiter, 1)
            context_paragraph = parts[0].strip() # 分隔符之前是上下文 

            # 使用全新的、健壮的函数来定位“小段落”
            section_start_offset, matched_paragraph = find_context_robustly(text, context_paragraph)
            
            if section_start_offset == -1:
                # 如果所有尝试都失败了，才抛出错误或跳过
                # print("没找到对应的小段落")
                penalty -= 1
                continue
            
            # 重要的更新：后续所有操作都必须基于实际匹配上的 matched_paragraph
            context_paragraph = matched_paragraph


            # 3. 在LLM的解释中，提取出实体、属性等的文本
            quantity_str = re.search(r'quantity with surface form \[(.*?)\]', section_content).group(1) if re.search(r'quantity with surface form \[(.*?)\]', section_content) else None
            if not quantity_str: continue # 每个段落必须有一个quantity作为核心

            entity_str = re.search(r'describe the entity \[(.*?)\]', section_content).group(1) if re.search(r'describe the entity \[(.*?)\]', section_content) else ""
            property_str = re.search(r'property \[(.*?)\]', section_content).group(1) if re.search(r'property \[(.*?)\]', section_content) else ""
            qualifier_str = re.search(r'has a qualifier \[(.*?)\]', section_content).group(1) if re.search(r'has a qualifier \[(.*?)\]', section_content) else ""
            unit_str = re.search(r'has unit \[(.*?)\]', section_content).group(1) if re.search(r'has unit \[(.*?)\]', section_content) else ""
            modifier_str = re.search(r'The modifier for the quantity are \[(.*?)\]', section_content).group(1) if re.search(r'The modifier for the quantity are \[(.*?)\]', section_content) else ""
            
            id_map = {}
            
            # 4. 在“小段落”内寻找Quantity，并计算其全局位置作为锚点
            local_q_indices = find_all_occurrences(context_paragraph, quantity_str)
            if not local_q_indices: 
                # print("没找到quantity")
                penalty -= 1
                continue

            # --- 全新的、智能选择Quantity位置的逻辑 ---
            found_valid_quantity = False
            global_q_start, global_q_end = -1, -1 # 先初始化

            for local_q_start in local_q_indices:
                # 遍历所有找到的可能位置
                global_q_start_candidate = section_start_offset + local_q_start
                global_q_end_candidate = global_q_start_candidate + len(quantity_str)

                is_occupied = any(global_q_start_candidate < used_end and used_start < global_q_end_candidate for used_start, used_end in used_spans)

                if not is_occupied:
                    # 太好了，找到了一个尚未被占用的位置！就用它了。
                    global_q_start = global_q_start_candidate
                    global_q_end = global_q_end_candidate
                    found_valid_quantity = True
                    break # 成功找到，退出这个小循环

            if not found_valid_quantity:
                # 如果把所有找到的位置都试了一遍，发现全都被占用了
                # print("quantity已被占用")
                penalty -= 1
                continue
            # --- 智能选择逻辑结束 ---
            
            # 检查这个全局位置是否已被占用 (这部分现在由上面的循环处理了，但保留原始的is_occupied检查以防万一)
            # is_occupied = any(global_q_start < used_end and used_start < global_q_end for used_start, used_end in used_spans)
            # if is_occupied:
            #     print(f"[信息] Quantity '{quantity_str}' 在位置 {global_q_start} 已被处理，跳过重复解释。")
            #     continue
            
            used_spans.add((global_q_start, global_q_end))
            quantity_id = f"T{global_id_counter}"; global_id_counter += 1
            id_map["quantity"] = quantity_id
        
            
            # 添加Quantity到tsv
            q_other = {}
            mods = [m.strip() for m in modifier_str.split(",") if m.strip() in valid_mods_keys]
            if mods: q_other["mods"] = mods
            if unit_str and unit_str != "None": q_other["unit"] = unit_str
            tsv_data.append({"docId": docId, "annotSet": annot_set_id, "annotType": "Quantity", "annotId": quantity_id, "startOffset": global_q_start, "endOffset": global_q_end, "text": quantity_str, "other": json.dumps(q_other) if q_other else ""})

            # 5. 对于其他元素，寻找段内所有匹配，换算成全局位置，再选择最近且可用的
            for role, text_to_find in [("property", property_str), ("entity", entity_str), ("qualifier", qualifier_str)]:
                if not text_to_find: continue
                
                local_indices = find_all_occurrences(context_paragraph, text_to_find)
                
                # 换算成全局位置并检查可用性
                valid_global_starts = []
                for local_start in local_indices:
                    global_start = section_start_offset + local_start
                    global_end = global_start + len(text_to_find)
                    # is_occ = any(global_start < used_end and used_start < global_end for used_start, used_end in used_spans)
                    # if not is_occ:
                    valid_global_starts.append(global_start)
                
                # if not valid_global_starts: continue

                # 从所有可用的全局位置中，选择离Quantity最近的
                if not valid_global_starts: 
                    # print("没找到其他元素")
                    penalty -= 1
                    continue
                    # 如果列表为空，直接跳到下一个role，不执行下面的min()
                    # raise ValueError(f"数量为空！")
                best_global_start = min(valid_global_starts, key=lambda s: abs(s - global_q_start))
                best_global_end = best_global_start + len(text_to_find)
                
                # used_spans.add((best_global_start, best_global_end)) # 占用找到的位置
                
                annot_id = f"T{global_id_counter}"; global_id_counter += 1
                
                if role == "property":
                    id_map["property"] = annot_id
                    tsv_data.append({"docId": docId, "annotSet": annot_set_id, "annotType": "MeasuredProperty", "annotId": annot_id, "startOffset": best_global_start, "endOffset": best_global_end, "text": text_to_find, "other": json.dumps({"HasQuantity": quantity_id})})
                elif role == "entity":
                    other = {}
                    if "property" in id_map: other["HasProperty"] = id_map["property"]
                    else:
                        other["HasQuantity"] = quantity_id
                    tsv_data.append({"docId": docId, "annotSet": annot_set_id, "annotType": "MeasuredEntity", "annotId": annot_id, "startOffset": best_global_start, "endOffset": best_global_end, "text": text_to_find, "other": json.dumps(other)})
                elif role == "qualifier":
                    tsv_data.append({"docId": docId, "annotSet": annot_set_id, "annotType": "Qualifier", "annotId": annot_id, "startOffset": best_global_start, "endOffset": best_global_end, "text": text_to_find, "other": json.dumps({"Qualifies": quantity_id})})
            
            annot_set_id += 1

        if tsv_data:
            df = pd.DataFrame(tsv_data, columns=["docId", "annotSet", "annotType", "annotId", "startOffset", "endOffset", "text", "other"])
        return penalty
    except:
        traceback.print_exc()
        return -10000