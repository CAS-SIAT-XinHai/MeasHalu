import requests
import os
import re
import pandas as pd
import traceback
import json
from io import StringIO
# S0016236113008041-3257
# 
# --- 全局配置 ---
url = 'http://localhost:4399/generate'
textpaths = ["/home/huangruijun/MeasEval-main/data/eval/text/"]
# quantpahts = ["/home/huangruijun/MeasEval-main/data/eval/tsv/"]
quantpahts = ["/home/huangruijun/MeasEval-main/data/qwen_6stage_grpo_4/"]

output_dir = "../MeasEval-main/data/sentence_sft/"

if not os.path.exists(output_dir):
    os.makedirs(output_dir)

# --- 数据加载 ---
quantset = {}
for fileset in quantpahts:
    for fn in os.listdir(fileset):
        with open(os.path.join(fileset, fn)) as textfile:
            text = textfile.read()
            quantset[fn[:-4]] = text

docIds = []
textset = {}
for fileset in textpaths:
    for fn in os.listdir(fileset):
        with open(os.path.join(fileset, fn), encoding='utf-8') as textfile:
            text = textfile.read()
            textset[fn[:-4]] = text
            if fn[:-4] in quantset:
                docIds.append(fn[:-4])

valid_mods_keys = [
    'IsCount', 'IsApproximate', 'IsMeanHasTolerance', 'IsMedian',
    'IsList', 'IsRangeHasTolerance', 'IsMean', 'IsRange',
    'HasTolerance', 'IsMeanIsRange', 'IsMeanHasSD'
]

# --- 辅助函数 ---
def find_all_occurrences(text, sub):
    """在一个给定的文本（比如小段落）中，找到一个子串所有出现的起始位置。"""
    if not sub: return []
    start = 0
    indices = []
    while True:
        start = text.find(sub, start)
        if start == -1: return indices
        indices.append(start)
        start += 1

def find_context_robustly(full_text, context_from_llm, min_words=5):
    """
    一个健壮的、分三步尝试寻找上下文的函数。
    """
    # 尝试 1: 精确匹配
    offset = full_text.find(context_from_llm)
    if offset != -1:
        # print("[信息] 通过精确匹配成功定位上下文！")
        return offset, context_from_llm

    # 尝试 2: 标准化所有空白符（包括换行符）后再次匹配
    cleaned_context = " ".join(context_from_llm.split())
    offset = full_text.find(cleaned_context)
    if offset != -1:
        print("[信息] 通过空白符标准化成功定位上下文！")
        return offset, cleaned_context
        # 步骤1：先对LLM的上下文进行空白符标准化，这是基础
    cleaned_context = " ".join(context_from_llm.split())
    if not cleaned_context:
        return -1, None

    # 步骤2：使用大小写不敏感的正则表达式，尝试完整匹配
        # 使用re.escape来保证上下文中的特殊字符被当作普通文本对待
    pattern = re.escape(cleaned_context)
    match = re.search(pattern, full_text, re.IGNORECASE)
        
    if match:
        print("[信息] 通过大小写不敏感的正则匹配成功定位！")
        # match.group(0) 返回的是在full_text中实际匹配上的那段文本
        # match.start() 返回的是它在full_text中的起始偏移量
        return match.start(), match.group(0)
    # # 尝试 3: 逐步缩短标准化的上下文，应对LLM引用不完整句子的情况
    # words = cleaned_context.split()
    # for i in range(1, len(words)):
    #     # 每次尝试都从末尾去掉一个词
    #     num_words_to_use = len(words) - i
    #     if num_words_to_use < min_words:
    #         # 如果段落变得太短，就没有查找的意义了，停止尝试
    #         break
        
    #     shorter_context = " ".join(words[:num_words_to_use])
    #     offset = full_text.find(shorter_context)
    #     if offset != -1:
    #         print(f"[信息] 通过缩短至 {num_words_to_use} 个词成功定位上下文！")
    #         return offset, shorter_context

    # 如果所有尝试都失败了
    return -1, None
# --- 主处理流程 ---
for docId in docIds:
    # docId = "S0019103512002801-2075"
    print(f"\n>>> 正在处理文档: {docId}")
    cnt = 10
    while(cnt):
        try:
            text = textset[docId]
            quant_df = pd.read_csv(StringIO(quantset[docId]), sep='\t')
            quant_df = quant_df[quant_df['annotType'] == 'Quantity'].drop(["other", "docId", "annotId", "annotSet", "startOffset", "endOffset"], axis=1)
            quant_str_for_prompt = quant_df.to_csv(index=False, sep='\t')
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Please help me extract all the MeasuredEntities, MeasuredProperties, and Qualifiers, along with their relationships of the extracted quantities. \nextracted quantities:{quant_str_for_prompt}\n\nInput: {text}"}
            ]
            
            data = {"messages": messages}
            response = requests.post(url, json=data).json()['response']
            print(response)
            # --- 全新的、基于段落的解析流程 ---
            
            llm_sections = response.strip().split('From the target sentences:')
            if len(llm_sections) <= 1:
                raise ValueError("[警告] LLM响应格式不符合预期，无法按段落切分。")
                
            tsv_data = []
            used_spans = set()  # 全局已占用区间，存储的是全局偏移量
            global_id_counter = 1
            annot_set_id = 1

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
                    if cnt ==1: continue
                    else:
                        raise ValueError(f"[警告] 无法在原文中定位上下文段落: {context_paragraph}")
                
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
                if not local_q_indices: continue

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
                    print(f"[信息] Quantity '{quantity_str}' 的所有出现位置都已被占用，跳过。")
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

            if not tsv_data:
                raise ValueError(f"[警告] 未能为文档 {docId} 生成任何有效的标注行。")

            df = pd.DataFrame(tsv_data, columns=["docId", "annotSet", "annotType", "annotId", "startOffset", "endOffset", "text", "other"])
            print(df)
            out_path = os.path.join(output_dir, f"{docId}.tsv")
            df.to_csv(out_path, sep='\t', index=False)
            print(f"成功保存TSV文件: {out_path}")
            break
        except Exception as e:
            cnt-=1
            print(f"[错误] 处理文档 {docId} 时发生严重错误。")
            traceback.print_exc()
    if cnt==0:
        out_path = os.path.join(output_dir, f"{docId}.tsv")
        df = pd.DataFrame(tsv_data, columns=["docId", "annotSet", "annotType", "annotId", "startOffset", "endOffset", "text", "other"])
        df.to_csv(out_path, sep='\t', index=False)
