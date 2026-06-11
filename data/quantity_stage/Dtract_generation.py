import random
import os
import json
from openai import OpenAI
import re
import pandas as pd
import traceback
from vladiate.validators import UniqueValidator, SetValidator, IntValidator, Validator, ValidationException, RegexValidator
import logging
from vladiate import Vlad, logs
import tempfile
from vladiate.inputs import LocalFile
import threading
from concurrent.futures import ThreadPoolExecutor
from schema_eval import check_reasoning_measeval
from io import StringIO
import traceback
message_template_quantity = '''
Instruction:
You are an expert in extracting structured annotations from text.
I have an text input and you need to extract all the quantities within it. I need you to strictly follow the format with six specific sections: ARABIC-QUANTITY,ALPHABETIC-QUANTITY, CHANGE-QUANTITY,TIME-QUANTITY,FORMULA-QUANTITY,CONCLUSION. It is crucial that you adhere to this structure exactly as outlined and that the final answer in the ANSWER matches the standard correct answer precisely. To explain further:In ARABIC-QUANTITY, outline a step-by-step thought process you would use to extract the arabic quantities in the text such as the 2 in '2 apples'. In ALPHABETIC-QUANTITY,  outline a step-by-step thought process you would use to extract all the alphabetic quantities in the text, such as the two in 'two apples'. In CHANGE-QUANTITY,outline a step-by-step thought process that you extract the quantity describes changes,such as the 20 in 'a rise of 20'.In TIME-QUANTITY,you need to outline a step-by-step process that how you extract all the time related quantity like 'June 2001'.In FORMULA-QUANTITY, you need to outline a step-by-step process that how you extract all the quantity in formula.For example: the 2 in 'q=2'(q is the measured entity) In ANSWER,give the final answer in a tsv format explained below, and it must match the correct answer exactly. Here's how the format should look:<ARABIC-QUANTITY> [Provide a chain-of-thought, logical explanation of how you extract all arabic quantities in the text. This should outline step-by-step reasoning.] </ARABIC-QUANTITY> <ALPHABETIC-QUANTITY> [Provide a chain-of-thought, logical explanation of how you extract all alphabetic quantities in the text,like two in 'two stages' This should outline step-by-step reasoning.] </ALPHABETIC-QUANTITY> <CHANGE-QUANTITY> [Provide a chain-of-thought, logical explanation of how you extract all the quantity describes changes,such as the 2.12 in 'fall dwon to 2.12'. This should outline step-by-step reasoning.] </CHANGE-QUANTITY> <TIME-QUANTITY> [Provide a chain-of-thought, logical explanation of how you extract the time related quantities like 'before the summer of 2015' for each previously identified quantity. This should outline step-by-step reasoning.] </TIME-QUANTITY><FORMULA-QUANTITY> [Provide a chain-of-thought, logical explanation of how you extract all the quantities in formula, like 3 in 't=3',where t is the measured entity. for each previously identified quantity. This should outline step-by-step reasoning.] </FORMULA-QUANTITY> <CONCLUSION> [State the final answer in a tsv format explained below format. It must match the correct answer exactly.] </CONCLUSION> (Do not forget </CONCLUSION>!) Please apply this format meticulously to analyze the text and extract all of the quantities, ensuring that the answer matches the standard one perfectly.
---
Output Format (TSV Fields):
- annotType: As you're extracting quantities, this field should be Quantity
- text: The exact text of the annotation from the input.
---

Standard Answer:%s

Input: %s
'''

# message_template_everything = '''
# You are an expert in extracting structured annotations from text.
# Instruction:
# You are an expert in extracting structured annotations from text.
# In the previous step, you have already extracted the "quantity" from the text file. Now, you need to extract all the Measured Entities, Measured Properties, and Qualifiers corresponding to the quantity, along with their relationships.I have an text input and you need to extract all the quantities within it. I need you to strictly follow the format with two specific sections: EVERYTHING-REASONING, CONCLUSION. It is crucial that you adhere to this structure exactly as outlined and that the final answer in the CONCLUSION matches the standard correct answer precisely. To explain further: In EVERYTHING-REASONING, outline a step-by-step thought process you utilize the quantity information you have already extracted to extract all the Measured Entities, Measured Properties, and Qualifiers corresponding to the quantity. In CONCLUSION, give the final answer in a tsv format explained below,summarizing all of the information,including Quantities,Measured Entities, Measured Properties, and Qualifiers along with relationships corresponding to the quantity, and it must match the correct answer exactly. Here's how the format should look: <EVERYTHING-REASONING> [Provide a chain-of-thought, logical explanation of how you extract MeasuredEntities, MeasuredProperties, and Qualifiers, along with their relationships in the text. This should outline step-by-step reasoning.] </EVERYTHING-REASONING> <CONCLUSION> [Combine the information of quantities with the information extracted from EVERYTHING-REASONING to generate the answers in TSV format. It must match the correct answer exactly.] </CONCLUSION> (Do not forget </CONCLUSION>!) Please apply this format meticulously to analyze the text and extract all of the MeasuredEntities, MeasuredProperties, and Qualifiers, along with their relationships corresponding to the quantities,and put the extracted information together with the quantities into a TSV file, ensuring that the answer matches the standard one perfectly.
# ---
# Output Format (TSV Fields):
# - annotSet: The annotation set ID (starting from 1 for each logical grouping of related annotations).
# - annotType: One of the following types: Quantity, MeasuredEntity, MeasuredProperty, or Qualifier.
# - annotId: A unique identifier for the annotation (e.g., T1, T2), numbered sequentially within each annotSet.
# - text: The exact text of the annotation from the input.
# - other: If annotType is Quantities: Extract all phrases involving quantities, specifying their unit and modifiers (if any). Include unit (e.g., "kg", "ppm"), ensure that all modifiers are placed inside "mods" (e.g., "mods": ["IsCount"]), and si (SI equivalent of the unit, if applicable). Optional modifiers include IsApproximate (indicating approximate values, e.g., "around 1300 m/s"), IsCount (indicating a count, e.g., "four samples"), IsRange (indicating a range, e.g., "1.5-2.6m"), IsList (indicating a list of quantities, e.g., "4.5kg, 6kg, 13kg"), IsMedian (indicating a median value, e.g., "10ppq"), IsMean (indicating a mean value, e.g., "9 ± 6"), and IsMeanHasSD (indicating a mean value with standard deviation, e.g., "1.23 ± 0.25").
# Example: {"mods": ["IsMean"], "unit": "years"}
# else if annotType is Other types (e.g., MeasuredEntities, MeasuredProperties, Qualifier,etc.):You must annotate relationships between entities using the format {relationType: targetAnnotation}.
# Examples: if annotType is MeasuredEntities:{"HasProperty": "T21-4"},MeasyredProperties:{"HasQuantity":"T3-2"},Qualifier:{"Qualifies": "T4-5"}
# ---
# Quantities have extracted:%s

# Standard Answer:%s

# Input: %s
# '''

textpaths = [
        "data/train/text/","data/trial/txt/"]
tsvpaths = ["data/train/tsv/","data/trial/tsv/"]
client = OpenAI()

typemap = {"Quantity": "QUANT",
        "MeasuredEntity": "ME",
        "MeasuredProperty": "MP",
        "Qualifier": "QUAL"}

docIds = []
textset = {}
tsvset = {}
for fileset in textpaths:
    for fn in os.listdir(fileset):
        with open(fileset + fn) as textfile:
            text = textfile.read()  # .splitlines()
            textset[fn[:-4]] = text
for fileset in tsvpaths:
    for fn in os.listdir(fileset):
        with open(fileset + fn) as textfile:
            text = textfile.read()  # .splitlines()
            tsvset[fn[:-4]] = text
            docIds.append(fn[:-4])
ents = {}

# 创建线程锁
file_lock = threading.Lock()


def process_doc(docId):
    cnt =60
    while cnt:
        try:
            print(docId)
            text = textset[docId]
            ans = pd.read_csv(StringIO(tsvset[docId]), sep='\t')
            old_to_new = {}
            for idx, row in ans.iterrows():
                old_id = row['annotId']  # 例如 "T1-1"
                new_id = f"T{idx + 1}"   # 新的 ID "T1", "T2", ...
                old_to_new[old_id] = new_id

            # 2. 更新 other 字段里的引用
            def update_other_refs(other_str):
                if pd.isna(other_str) or other_str == "{}":
                    return other_str
                
                # 解析 JSON（注意：原数据可能使用单引号，需替换为双引号）
                try:
                    other_dict = json.loads(other_str.replace("'", '"'))
                except json.JSONDecodeError:
                    return other_str  # 如果解析失败，保持原样
                
                # 遍历字典，替换所有 T* 的引用
                for key, value in other_dict.items():
                    if isinstance(value, str) and value.startswith('T'):
                        # 检查是否在映射表中
                        if value in old_to_new:
                            other_dict[key] = old_to_new[value]
                    # 如果值是列表（如 "mods": ["IsCount"]），也检查是否需要替换
                    # elif isinstance(value, list):
                    #     other_dict[key] = [old_to_new[v] if isinstance(v, str) and v.startswith('T') else v for v in value]
                
                return json.dumps(other_dict)  # 重新转为字符串

            # 3. 应用更新
            # print(ans['other'])
            ans['other'] = ans['other'].apply(update_other_refs)

            # 4. 最后，更新 annotId 列
            ans['annotId'] = [f"T{i+1}" for i in range(len(ans))]
            ans = ans.drop('docId', axis=1).drop('startOffset',axis=1).drop('endOffset',axis=1).drop('other',axis=1)
            quantity_ans = ans[ans['annotType'] == 'Quantity'].drop('annotId', axis=1).drop('annotSet',axis=1)
            # print(quantity_ans)
            response = client.chat.completions.create(
                model="deepseek-v3",  # 填写需要调用的模型名称
                messages=[{"role": "system", "content": "You are an expert in quantity relations extraction."},
                        {"role": "user", "content": message_template_quantity % (quantity_ans.to_string(index=False), text)}])
    
            result_quantity = response.choices[0].message.content
            # print(result_quantity)
            # print(result_quantity)
            # if not ("<QUANTITY-REASONING>" in result_quantity and "</QUANTITY-REASONING>" in result_quantity 
            #                     and "<QUANTITY-ANSWER>" in result_quantity and "</QUANTITY-ANSWER>" in result_quantity):
            #     raise ValueError("The quantity result does not contain the necessary tags")
            # response = client.chat.completions.create(
            #     model="deepseek-v3",  # 填写需要调用的模型名称
            #     messages=[{"role": "system", "content": "You are an expert in quantity relations extraction."},
            #             {"role": "user", "content": message_template_everything % (
            #                 quantity_ans.to_string(), ans.to_string(), text)}])
            # result_everything = response.choices[0].message.content
            if not ("<ARABIC-QUANTITY>" in result_quantity and "</ARABIC-QUANTITY>" in result_quantity 
                        and "<ALPHABETIC-QUANTITY>" in result_quantity and "</ALPHABETIC-QUANTITY>" in result_quantity 
                        and "<CHANGE-QUANTITY>" in result_quantity and "</CHANGE-QUANTITY>" in result_quantity
                        and "<TIME-QUANTITY>" in result_quantity and "</TIME-QUANTITY>" in result_quantity
                        and "<FORMULA-QUANTITY>" in result_quantity and "</FORMULA-QUANTITY>" in result_quantity
                        and "<CONCLUSION>" in result_quantity and "</CONCLUSION>" in result_quantity):
                raise ValueError("The everything result does not contain the necessary tags")
            pattern = r'<CONCLUSION>(.*?)</CONCLUSION>'
            match = re.search(pattern, result_quantity, re.DOTALL).group(1)
            # quantity_result_content = match.group(1)
            # check_reasoning_measeval(quantity_result_content)
            # print(match)
            df = pd.read_csv(StringIO(match) ,sep='\t').reset_index(drop=True)
            quantity_ans = quantity_ans.reset_index(drop=True)
            # print(df)
            # print(quantity_ans)
            # print("----------------------------------------------------------------------")
            if not df.equals(quantity_ans):
                raise ValueError("不完全相同")
            # # df['other'] = df['other'].apply(lambda x: None if x == '{}' else x)
            # # 如果没找到匹配项，检查是否有表头
            # pattern = r'(<EVERYTHING-REASONING>.*?</EVERYTHING-REASONING>)'
            # match = re.search(pattern, result_everything, re.DOTALL).group(1)
            # result_everything = match + '\n<CONCLUSION>\n'+ df.to_string(index=False) +'\n</CONCLUSION>'

            # print(reasoning_process)
            # print(reasoning_process)
            output_data = {
                "docId": docId,
                "query": 'Please help me extract all of the Quantities along with their modifiers and units. And think according to the following six stages:ARABIC-QUANTITY,ALPHABETIC-QUANTITY,CHANGE-QUANTITY,TIME-QUANTITY,FORMULA-QUANTITY and CONCLUSION. \n\nInput: '+text,
                "original_text": text,
                "quantity_reasoning_process": result_quantity
            }
            # 每次处理数据时打开文件并追加写入
            output_file = 'quantity_6stage_meas.jsonl'
            # 获取锁
            with file_lock:
                with open(output_file, 'a', encoding='utf-8') as outfile:
                    json_line = json.dumps(output_data, ensure_ascii=False)
                    outfile.write(json_line + '\n')
            break
        except Exception as e:
            cnt -=1
            traceback.print_exc()

        if cnt==0:
            while True:
                try:
                    response = client.chat.completions.create(
                    model="deepseek-v3",  # 填写需要调用的模型名称
                    messages=[{"role": "system", "content": "You are an expert in quantity relations extraction."},
                            {"role": "user", "content": message_template_quantity % (quantity_ans.to_string(index=False), text)}])
        
                    result_quantity = response.choices[0].message.content

                    reasoning_process = result_quantity
                    # print(reasoning_process)
                    # print(reasoning_process)

                    if not ("<ARABIC-QUANTITY>" in result_quantity and "</ARABIC-QUANTITY>" in result_quantity 
                                and "<ALPHABETIC-QUANTITY>" in result_quantity and "</ALPHABETIC-QUANTITY>" in result_quantity 
                                and "<CHANGE-QUANTITY>" in result_quantity and "</CHANGE-QUANTITY>" in result_quantity
                                and "<TIME-QUANTITY>" in result_quantity and "</TIME-QUANTITY>" in result_quantity
                                and "<FORMULA-QUANTITY>" in result_quantity and "</FORMULA-QUANTITY>" in result_quantity
                                and "<CONCLUSION>" in result_quantity and "</CONCLUSION>" in result_quantity):
                        raise ValueError("The everything result does not contain the necessary tags")
                    output_data = {
                        "docId": docId,
                        "query": 'Please help me extract all of the Quantities along with their modifiers and units. And think according to the following six stages:ARABIC-QUANTITY,ALPHABETIC-QUANTITY,CHANGE-QUANTITY,TIME-QUANTITY,FORMULA-QUANTITY and CONCLUSION. \n\nInput: '+text,
                        "original_text": text,
                        "quantity_reasoning_process": reasoning_process
                    }
                    # 每次处理数据时打开文件并追加写入
                    output_file = 'quantity_6stage_meas.jsonl'
                    # 获取锁
                    with file_lock:
                        with open(output_file, 'a', encoding='utf-8') as outfile:
                            json_line = json.dumps(output_data, ensure_ascii=False)
                            outfile.write(json_line + '\n')
                    break
                except Exception as e:
                    print("出错了")
                    print(e)

# 使用 ThreadPoolExecutor 进行并发处理
with ThreadPoolExecutor(max_workers=290) as executor:
    executor.map(process_doc, docIds)