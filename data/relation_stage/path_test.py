import os
import json
import pandas as pd
from io import StringIO
import traceback

from measeval_test import MeasEvalAnnotationInstance, MeasEvalAnnotationMeasurement

# 原文路径和结构化标注路径
textpaths = [
    "MeasEval/data/train/text/",
    "MeasEval/data/trial/txt/"
]

anspaths = [
    "MeasEval/data/train/tsv/",
    "MeasEval/data/trial/tsv/"
]

typemap = {
    "Quantity": "QUANT",
    "MeasuredEntity": "ME",
    "MeasuredProperty": "MP",
    "Qualifier": "QUAL"
}

docIds = []
textset = {}
ansset = {}

# 读取原始文本
for fileset in textpaths:
    for fn in os.listdir(fileset):
        with open(os.path.join(fileset, fn), encoding='utf-8') as textfile:
            text = textfile.read()
            textset[fn[:-4]] = text
            docIds.append(fn[:-4])

# 读取标注文件（TSV形式）
for fileset in anspaths:
    for fn in os.listdir(fileset):
        with open(os.path.join(fileset, fn), encoding='utf-8') as textfile:
            text = textfile.read()
            ansset[fn[:-4]] = text

# 输出文件路径
output_file = 'test.jsonl'

# 清空之前的输出文件（如有）
with open(output_file, 'w', encoding='utf-8') as f:
    pass

# 遍历每个文档
for docId in docIds:
    print(docId)
    try:
        text = textset[docId]
        ans = pd.read_csv(StringIO(ansset[docId]), sep='\t')
        
        # --- START OF MODIFICATION ---
        # 筛选 Quantity 并提取其文本
        quantity_ans = ans[ans['annotType'] == 'Quantity']
        # 提取 'text' 列，并转换为 Python 列表
        extracted_quantities_list = quantity_ans['text'].tolist()
        # 将列表转换为 JSON 字符串格式，以便在 query 中清晰展示
        quantities_str = json.dumps(extracted_quantities_list, ensure_ascii=False)
        # --- END OF MODIFICATION ---

        # 构造 annotation measurement 对象列表
        validated_data = []
        for item in ans.to_dict(orient='records'):
            try:
                # 确保 'other' 字段是有效的 JSON 或空字典
                item['other'] = json.loads(item['other']) if pd.notna(item['other']) and item['other'].strip() not in ['', '{}'] else {}
            except Exception as e:
                print(f"[warning] JSON parsing failed for other: {item.get('other')}, error: {e}")
                item['other'] = {}
            # 确保其他字段的 NaN 处理
            for key in item:
                if pd.isna(item[key]):
                    item[key] = None

            validated_data.append(MeasEvalAnnotationMeasurement(**item))

        # 构建推理实例并生成 instruction
        instance = MeasEvalAnnotationInstance.from_entries(validated_data, text)
        instruction = instance.to_instruction()

        # 输出为 JSONL 格式
        output_data = {
            "docId": docId,
            # --- START OF MODIFICATION ---
            # 使用列表字符串 quantities_str 替换原始的 tsv 格式
            "query": 'Please help me extract all the MeasuredEntities, MeasuredProperties, and Qualifiers, along with their relationships of the extracted quantities. \n\nExtracted quantities list:' + quantities_str + '\n\nInput: ' + text,
            # --- END OF MODIFICATION ---
            "path": instruction,
            "ans": ans.to_csv(sep='\t', index=False)
        }
        print(output_data)
        with open(output_file, 'a', encoding='utf-8') as outfile:
            json_line = json.dumps(output_data, ensure_ascii=False)
            outfile.write(json_line + '\n')
    except Exception:
        traceback.print_exc()
        continue