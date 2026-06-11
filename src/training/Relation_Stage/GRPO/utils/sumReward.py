import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from .utils import is_overlapping,update_row,textset,find_context_robustly,find_all_occurrences,valid_mods_keys
import re
import json
from io import StringIO

def _overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    """半开区间 [start, end) 的重叠判断"""
    return not (a_end <= b_start or b_end <= a_start)

def _best_overlap_match(
    pred_span: Tuple[int,int],
    cand_df: pd.DataFrame,
    used_answer_ids: set
) -> Optional[str]:
    """
    在 cand_df 中（按行）找与 pred_span 重叠且尚未被使用的答案项，
    返回其 annotId（字符串），若无匹配返回 None。
    选择重叠长度最大的那一项（优先最大重叠）。
    """
    ps, pe = pred_span
    best_aid = None
    best_len = -1
    for _, row in cand_df.iterrows():
        aid = row["annotId"]
        if aid in used_answer_ids:
            continue
        s, e = int(row["startOffset"]), int(row["endOffset"])
        if _overlap(ps, pe, s, e):
            ov = min(pe, e) - max(ps, s)
            if ov > best_len:
                best_len = ov
                best_aid = aid
    return best_aid

def SumReward(docId,input,answer):
    """
    以“提交为主导”的奖励函数（逐行对比）：
      - 先遍历提交的每个 Quantity：
          * 若未命中任何答案 Quantity -> 记一次 penalty_no_quantity_hit
          * 若命中 -> 锁定该答案的 annotSet（答案组），奖励 Quantity，并
                    在该答案组内对预测组的 ME/MP/Qualifier 逐条比对：
                        - 命中答案（未被占用） -> +weights[type]
                        - 未命中（找不到重叠或对应答案已被占用） -> +penalty_nonmatch_inside_group
      - 每个答案项（通过 annotId 标识）全局只被匹配一次（used_answer_ids）
    返回字典包含 score / reward_sum / penalties / hits / details
    """
    try:
        # print(answer)
        text = textset[docId]
        response = input
        # --- 全新的、基于段落的解析流程 ---
        empty_st = False
        llm_sections = response.strip().split('From the target sentences:')
        if len(llm_sections) <= 1:
            df = ""
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
            empty_st = True

        df = pd.DataFrame(tsv_data, columns=["docId", "annotSet", "annotType", "annotId", "startOffset", "endOffset", "text", "other"])

        pred_df = df.copy()
        answer_df = pd.read_csv(StringIO(answer),sep = '\t')

        weights = {"Quantity": 1.0, "MeasuredEntity": 1.0, "MeasuredProperty": 1.0, "Qualifier": 1.0}

        # 强制为整数
        for df in (answer_df, pred_df):
            df["startOffset"] = df["startOffset"].astype(int)
            df["endOffset"] = df["endOffset"].astype(int)

        reward_sum = 0.0
        penalties = 0.0
        hits = 0
        details: List[Dict[str, Any]] = []
        bonus_full_match = 5
        used_answer_ids: set = set()  # 存放 annotId（字符串）

        # 按 docId 分文档处理
        for doc_id, pred_doc in pred_df.groupby("docId"):
            ans_doc = answer_df[answer_df["docId"] == doc_id]

            # 仅遍历提交里的 Quantity（作为预测组入口）
            pred_qty = pred_doc[pred_doc["annotType"] == "Quantity"]
            for _, pq in pred_qty.iterrows():
                pq_span = (int(pq["startOffset"]), int(pq["endOffset"]))
                pq_set = pq["annotSet"]

                # 答案里所有 Quantity 候选
                ans_qty_cand = ans_doc[ans_doc["annotType"] == "Quantity"]

                # 找到最佳（未被占用的）答案 Quantity（返回 annotId）
                best_ans_q_aid = _best_overlap_match(pq_span, ans_qty_cand, used_answer_ids)

                if best_ans_q_aid is None:
                    # 未命中答案 Quantity -> 惩罚并跳过后续判定
                    penalties += 1
                    continue

                # 命中答案 Quantity：标记为已用并奖励
                used_answer_ids.add(best_ans_q_aid)
                reward_sum += weights.get("Quantity", 1.0)
                hits += 1

                # 获取该答案 Quantity 的整行以确定它的 annotSet（锁定答案组）
                ans_q_row = ans_qty_cand[ans_qty_cand["annotId"] == best_ans_q_aid].iloc[0]

                # 锁定的答案组（以该答案 Quantity 所在 annotSet 为准）
                ans_group_set = ans_doc[ans_doc["annotSet"] == ans_q_row["annotSet"]]
                # 对应的预测组（以预测里该 Quantity 的 annotSet 为准）
                pred_group_set = pred_doc[pred_doc["annotSet"] == pq_set]


            # 在进入对 ans_group_set / pred_group_set 的逐条比对前，放在原来对应位置
            types = ("MeasuredEntity", "MeasuredProperty", "Qualifier")
            group_matched_ans_ids = set()
            used_before_group = used_answer_ids.copy()  # snapshot：记录在当前组匹配前已经被占用的答案项

            # 逐条对预测项进行匹配（与原逻辑类似），但同时记录匹配到的答案 annotId
            for atype in types:
                pred_items = pred_group_set[pred_group_set["annotType"] == atype]
                # 逐条预测项对比：命中奖励 / 未命中惩罚
                for _, pi in pred_items.iterrows():
                    p_span = (int(pi["startOffset"]), int(pi["endOffset"]))
                    ans_items = ans_group_set[ans_group_set["annotType"] == atype]
                    best_ans_aid = _best_overlap_match(p_span, ans_items, used_answer_ids)

                    if best_ans_aid is not None:
                        # 命中（且答案项未被占用）
                        used_answer_ids.add(best_ans_aid)
                        group_matched_ans_ids.add(best_ans_aid)   # 记录：本次匹配到的答案ID
                        reward_sum += weights.get(atype, 1.0)
                        hits += 1
                    else:
                        # 未命中：在已锁定的答案组内找不到匹配 -> 惩罚
                        penalties += 1
                        # 这里不要立刻把 all_matched 设为 False，改为后面基于 ans_ids 比较决定

            # --- 新增：检查答案组是否被完整覆盖 ---
            ans_ids_in_group = set(ans_group_set[ans_group_set["annotType"].isin(types)]["annotId"].astype(str))

            # 选项 A（严格）：要求本次预测匹配到答案组里的所有项
            if ans_ids_in_group and ans_ids_in_group.issubset(group_matched_ans_ids):
                reward_sum += bonus_full_match

            # 选项 B（宽松）：允许此前别的预测已匹配过的答案项也算（不推荐，视场景）
            # elif ans_ids_in_group and ans_ids_in_group.issubset(group_matched_ans_ids.union(used_before_group)):
            #     reward_sum += bonus_full_match

            # 可以记录/输出未被本次预测覆盖的答案项（用于分析/调试）
            missing_ans_ids = ans_ids_in_group - group_matched_ans_ids - used_before_group
            if missing_ans_ids:
                # 这些是“真正漏掉且此前也没人匹配”的答案项
                # 可选：对每个漏掉的答案项施加额外惩罚
                # penalties += len(missing_ans_ids) * penalty_missing_answer_in_group
                pass




        return reward_sum
    except:
        return -1000