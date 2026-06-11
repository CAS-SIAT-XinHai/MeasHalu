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
url = 'http://localhost:3000/generate'
textpaths = ["/home/huangruijun/MeasEval-main/data/eval/text/"]
			#  "/home/huangruijun/MeasEval-main/data/trial/txt/"]
# textpaths=  ["/home/huangruijun/MeasEval-main/data/meashalu_all/"]
# textpaths = ["/home/huangruijun/MeasEval-main/data/meashalu_p2_txt/"]
# quantpahts = ["/home/huangruijun/MeasEval-main/data/eval/tsv/"]
quantpahts = ['/home/huangruijun/MeasEval-main/data/7bsft_only_grpo2_5500_3']
# quantpahts = ['/home/huangruijun/MeasEval-main/data/meashalu_all_quant/']
output_dir = "../MeasEval-main/data/7b_test/"
# output_dir = "../MeasEval-main/data/meashalu_all_everything/"

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
        start += 1 # 从下一个位置继续找，防止找到重复的开始位置

# --- 占位函数 (假设已实现 Longest Anchor Matching 逻辑) ---
def find_context_robustly(full_text, context_from_llm):
    """
    鲁棒地在原文中定位 LLM 引用的上下文段落，采用 Longest Anchor Matching 策略。
    """
    if not context_from_llm:
        return -1, None
        
    # 步骤 1: 精确匹配
    offset = full_text.find(context_from_llm)
    if offset != -1:
        return offset, context_from_llm

    # 步骤 2: 标准化 LLM 引用，用于后续正则匹配
    cleaned_context = re.sub(r'\s+', ' ', context_from_llm).strip()
    if not cleaned_context:
        return -1, None
        
    # 步骤 2.1: 标准化空白符，然后正则匹配 (这是最可靠的模糊匹配)
    pattern_escaped = re.escape(cleaned_context)
    pattern = re.sub(r'\s+', r'\\s+', pattern_escaped)
    
    match = re.search(pattern, full_text)
    if match:
        print("[信息] 通过空白符正则匹配成功定位上下文！")
        return match.start(), match.group(0) 

    # 步骤 2.2: 使用大小写不敏感的正则表达式，尝试完整匹配
    pattern_ignore_case = re.compile(pattern, re.IGNORECASE)
    match = pattern_ignore_case.search(full_text)
        
    if match:
        print("[信息] 通过大小写不敏感的正则匹配成功定位！")
        return match.start(), match.group(0)

    # --- 步骤 3: Longest Anchor Matching，保证边界正确 ---
    
    # 寻找最长匹配前缀和后缀，然后提取中间内容
    anchor_size = 10 # 最小锚点长度
    
    # 1. 寻找最长匹配前缀 (Start Anchor)
    anchor_start_offset = -1
    
    # 从 10 个字符开始，递增长度，找到最长的匹配前缀
    for length in range(anchor_size, len(cleaned_context) + 1):
        prefix = cleaned_context[:length]
        
        # 构建正则模式并搜索
        prefix_pattern_escaped = re.escape(prefix)
        prefix_pattern = re.sub(r'\s+', r'\\s+', prefix_pattern_escaped)
        match = re.search(prefix_pattern, full_text)
        
        if match:
            # 找到匹配，更新起始位置
            anchor_start_offset = match.start()
        else:
            # 一旦匹配失败，说明找到了最长前缀 (前一个循环是成功匹配的最长前缀)
            break
            
    if anchor_start_offset == -1:
        return -1, None
        
    # 2. 寻找最长匹配后缀 (End Anchor)
    anchor_end_offset = -1
    
    # 查找最长反向匹配 (在整个原文中进行搜索，并确保在起始锚点之后)
    for length in range(anchor_size, len(cleaned_context) + 1):
        suffix = cleaned_context[len(cleaned_context) - length:]
        
        # 构建正则模式并搜索
        suffix_pattern_escaped = re.escape(suffix)
        suffix_pattern = re.sub(r'\s+', r'\\s+', suffix_pattern_escaped)
        
        # 查找所有匹配，找到最接近起始锚点且在其之后的那个
        all_matches = list(re.finditer(suffix_pattern, full_text))
        
        best_match = None
        for match in reversed(all_matches): # 从后向前找，确保找到最远的
            if match.start() >= anchor_start_offset: # 必须在起始锚点之后
                best_match = match
                break
        
        if best_match:
            # 找到了匹配，更新结束位置 (匹配的起始位置 + 匹配到的后缀长度)
            anchor_end_offset = best_match.start() + len(best_match.group(0))
        else:
            break
            
    # 3. 提取原文中的整段内容
    if anchor_end_offset == -1 or anchor_end_offset <= anchor_start_offset:
        print("[信息] Longest Anchor 匹配失败：未找到可靠的结束锚点。")
        return -1, None
        
    final_matched_paragraph = full_text[anchor_start_offset:anchor_end_offset]
    
    print("[信息] 通过 Longest Anchor Matching 策略成功定位段落！")
    return anchor_start_offset, final_matched_paragraph



# --- 主处理流程 ---
for docId in docIds:
    # docId = "39"
    print(f"\n>>> 正在处理文档: {docId}")
    cnt = 10
    while(cnt):
        try:
            text = textset[docId]
            quant_df = pd.read_csv(StringIO(quantset[docId]), sep='\t')
            
            quant_df = quant_df[quant_df['annotType'] == 'Quantity'].drop(["other", "docId", "annotId", "annotSet", "startOffset", "endOffset"], axis=1)
            
            extracted_quantities_list = quant_df['text'].tolist()
            if not extracted_quantities_list: 
                print("no quantity")
                break
            quant_str_for_prompt = json.dumps(extracted_quantities_list, ensure_ascii=False)
            # quant_str_for_prompt = extracted_quantities_list
            
            print(f"Quantities Text List: {quant_str_for_prompt}")
            
            messages = [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": f"Please help me extract all the MeasuredEntities, MeasuredProperties, and Qualifiers, along with their relationships of the extracted quantities. \n\nExtracted quantities list:{quant_str_for_prompt}\n\nInput: {text}"}
            ]
            
            data = {"messages": messages}
            response = requests.post(url, json=data).json()['response']
            print(response)
            
            # --- 全新的、基于段落的解析流程 ---
            
            llm_sections = response.strip().split('From the target sentences:')
            if len(llm_sections) <= 1:
                raise ValueError("[警告] LLM响应格式不符合预期，无法按段落切分。")
                
            tsv_data = []
            used_spans = set()      # 仅用于 Quantity，防止 Quantity 重叠
            global_id_counter = 1
            annot_set_id = 1

            for section_content in llm_sections[1:]:
                if not section_content.strip(): continue
                # 1. 定位上下文段落
                delimiter = "We can find the quantity with surface form"
                parts = section_content.split(delimiter, 1)
                context_paragraph_llm = parts[0].strip() # LLM引用的上下文 

                section_start_offset, matched_paragraph = find_context_robustly(text, context_paragraph_llm)
                
                # --- 关键修改：引入容错机制 ---
                if section_start_offset == -1:
                    print(f"[警告] 无法在原文中定位上下文段落，切换至全局查找: {context_paragraph_llm[:50]}...")
                    # 如果段落定位失败，将上下文设为整个文本，起始偏移量设为 0
                    context_paragraph = text
                    section_start_offset = 0
                else:
                    context_paragraph = matched_paragraph # 使用实际匹配到的原文段落
                # --- 关键修改结束 ---


                # 3. 提取实体、属性等的文本 (重点修改 Qualifier 提取)
                quantity_match = re.search(r'quantity with surface form \[(.*?)\]', section_content)
                quantity_str = quantity_match.group(1) if quantity_match else None
                if not quantity_str: continue 

                entity_str = re.search(r'describe the entity \[(.*?)\]', section_content).group(1) if re.search(r'describe the entity \[(.*?)\]', section_content) else ""
                property_str = re.search(r'property \[(.*?)\]', section_content).group(1) if re.search(r'property \[(.*?)\]', section_content) else ""
                
                # --- 核心修正：多 Qualifier 提取 (使用 findall) ---
                # 匹配模式: 查找所有 'a qualifier [Qualifier 文本] [可选的 qualifies the [目标类型]]'
                # 结果是 [(Qualifier_text, Target_type), (Qualifier_text, Target_type), ...]
                qualifier_matches = re.findall(r'a qualifier \[(.*?)\](?: qualifies the \[(MeasuredProperty|MeasuredEntity|Quantity)\])?', section_content)
                
                # 构造 Qualifier 列表
                qualifier_list = []
                for q_text, q_target in qualifier_matches:
                    qualifier_list.append({
                        "text": q_text,
                        "target_type": q_target if q_target else "Quantity" # 默认指向 Quantity
                    })
                # --- 核心修正结束 ---
                
                unit_str = re.search(r'has unit \[(.*?)\]', section_content).group(1) if re.search(r'has unit \[(.*?)\]', section_content) else ""
                modifier_str = re.search(r'The modifier for the quantity are \[(.*?)\]', section_content).group(1) if re.search(r'The modifier for the quantity are \[(.*?)\]', section_content) else ""
                
                id_map = {}
                
                # --- 4. 定位 Quantity ---
                local_q_indices = find_all_occurrences(context_paragraph, quantity_str)
                if not local_q_indices: continue

                found_valid_quantity = False
                global_q_start, global_q_end = -1, -1

                for local_q_start in local_q_indices:
                    global_q_start_candidate = section_start_offset + local_q_start
                    global_q_end_candidate = global_q_start_candidate + len(quantity_str)

                    # 检查是否与已占用的 Quantity 重叠
                    is_occupied = any(global_q_start_candidate < used_end and used_start < global_q_end_candidate for used_start, used_end in used_spans)

                    if not is_occupied:
                        global_q_start = global_q_start_candidate
                        global_q_end = global_q_end_candidate
                        found_valid_quantity = True
                        break 

                if not found_valid_quantity:
                    print(f"[信息] Quantity '{quantity_str}' 的所有出现位置都已被占用，跳过。")
                    continue
                
                # 记录 Quantity 的占用
                used_spans.add((global_q_start, global_q_end))
                quantity_id = f"T{global_id_counter}"; global_id_counter += 1
                id_map["quantity"] = quantity_id
            
                # 添加 Quantity 到 tsv
                q_other = {}
                mods = [m.strip() for m in modifier_str.split(",") if m.strip() in valid_mods_keys]
                if mods: q_other["mods"] = mods
                if unit_str and unit_str != "None": q_other["unit"] = unit_str
                tsv_data.append({"docId": docId, "annotSet": annot_set_id, "annotType": "Quantity", "annotId": quantity_id, "startOffset": global_q_start, "endOffset": global_q_end, "text": quantity_str, "other": json.dumps(q_other) if q_other else ""})

                # --- 5. 定位 P/E/Q (调整为支持多 Qualifier) ---
                
                # 定义需要定位的元素列表
                elements_to_locate = []
                if property_str:
                    elements_to_locate.append({"role": "property", "text": property_str, "target_type": None})
                if entity_str:
                    elements_to_locate.append({"role": "entity", "text": entity_str, "target_type": None})
                
                # 添加所有 Qualifier
                for q_item in qualifier_list:
                    elements_to_locate.append({"role": "qualifier", "text": q_item["text"], "target_type": q_item["target_type"]})

                for item in elements_to_locate:
                    role = item["role"]
                    text_to_find = item["text"]
                    qualifies_target_type = item["target_type"]
                    
                    if not text_to_find: continue
                    
                    local_indices = find_all_occurrences(context_paragraph, text_to_find)
                    if not local_indices: continue
                    
                    # 换算成全局位置。所有匹配的位置都是 'valid' 的。
                    valid_global_starts = []
                    for local_start in local_indices:
                        global_start = section_start_offset + local_start
                        valid_global_starts.append(global_start)
                            
                    if not valid_global_starts: 
                        continue
                    
                    # 从所有可用的全局位置中，选择离 Quantity 最近的
                    best_global_start = min(valid_global_starts, key=lambda s: abs(s - global_q_start))
                    best_global_end = best_global_start + len(text_to_find)
                    
                    annot_id = f"T{global_id_counter}"; global_id_counter += 1
                    
                    if role == "property":
                        id_map["property"] = annot_id
                        tsv_data.append({"docId": docId, "annotSet": annot_set_id, "annotType": "MeasuredProperty", "annotId": annot_id, "startOffset": best_global_start, "endOffset": best_global_end, "text": text_to_find, "other": json.dumps({"HasQuantity": quantity_id})})
                    elif role == "entity":
                        id_map["entity"] = annot_id
                        other = {}
                        if "property" in id_map: other["HasProperty"] = id_map["property"]
                        else:
                            other["HasQuantity"] = quantity_id
                        tsv_data.append({"docId": docId, "annotSet": annot_set_id, "annotType": "MeasuredEntity", "annotId": annot_id, "startOffset": best_global_start, "endOffset": best_global_end, "text": text_to_find, "other": json.dumps(other)})
                    elif role == "qualifier":
                        
                        # --- 动态确定 Qualifies 目标 ID ---
                        target_id = quantity_id
                        if qualifies_target_type == "MeasuredProperty":
                            # 如果 LLM 说它修饰 Property，则查找 Property 的 ID
                            target_id = id_map.get("property", quantity_id)
                        elif qualifies_target_type == "MeasuredEntity":
                            # 如果 LLM 说它修饰 Entity，则查找 Entity 的 ID
                            target_id = id_map.get("entity", quantity_id)
                            
                        # 如果找不到对应的 ID (例如 property_str 为空，就没有 property ID)，则默认指向 quantity_id
                        if target_id == quantity_id and qualifies_target_type != "Quantity":
                            print(f"[警告] Qualifier '{text_to_find}' 目标为 {qualifies_target_type}，但找不到对应ID，默认指向 Quantity.")
                            
                        tsv_data.append({"docId": docId, "annotSet": annot_set_id, "annotType": "Qualifier", "annotId": annot_id, "startOffset": best_global_start, "endOffset": best_global_end, "text": text_to_find, "other": json.dumps({"Qualifies": target_id})})
                
                annot_set_id += 1

            if not tsv_data:
                raise ValueError(f"[警告] 未能为文档 {docId} 生成任何有效的标注行。")

            df = pd.DataFrame(tsv_data, columns=["docId", "annotSet", "annotType", "annotId", "startOffset", "endOffset", "text", "other"])
            print(df)
            print("correct length:" + str(len(extracted_quantities_list)))

            out_path = os.path.join(output_dir, f"{docId}.tsv")
            df.to_csv(out_path, sep='\t', index=False)
            print(f"成功保存TSV文件: {docId}.tsv")
            break
        except Exception as e:
            cnt-=1
            print(f"[错误] 处理文档 {docId} 时发生严重错误。")
            traceback.print_exc()
    if cnt==0 and tsv_data: # 确保在重试失败后，如果部分数据已生成，仍然保存
        out_path = os.path.join(output_dir, f"{docId}.tsv")
        df = pd.DataFrame(tsv_data, columns=["docId", "annotSet", "annotType", "annotId", "startOffset", "endOffset", "text", "other"])
        df.to_csv(out_path, sep='\t', index=False)
        print(f"在重试失败后，成功保存部分生成的TSV文件: {out_path}")
    elif cnt == 0 and not tsv_data:
        print(f"文档 {docId} 经过多次重试仍无法生成有效的TSV数据。")