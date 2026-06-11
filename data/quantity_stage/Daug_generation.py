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
import concurrent
from schema_eval import check_reasoning_measeval
from modelscope import AutoTokenizer
from io import StringIO
tokenizer = AutoTokenizer.from_pretrained('Qwen/Qwen2.5-7B-Instruct')
message_template_quantity = '''
Instruction:
You are an expert in extracting structured annotations from text.
I have an text input and you need to extract all the quantities within it. I need you to strictly follow the format with six specific sections: ARABIC-QUANTITY,ALPHABETIC-QUANTITY, CHANGE-QUANTITY,TIME-QUANTITY,FORMULA-QUANTITY,CONCLUSION. The Quantulum information may be incorrect or incomplete, so it is crucial that you have to get the quantity from the text on your own,and you are not allowed to mention obtaining it from the Quantulum library. To explain further:In ARABIC-QUANTITY, outline a step-by-step thought process you would use to extract the arabic quantities in the text such as the 2 in '2 apples'. In ALPHABETIC-QUANTITY,  outline a step-by-step thought process you would use to extract all the alphabetic quantities in the text, such as the two in 'two apples'. In CHANGE-QUANTITY,outline a step-by-step thought process that you extract the quantity describes changes,such as the 20 in 'a rise of 20'.In TIME-QUANTITY,you need to outline a step-by-step process that how you extract all the time related quantity like 'June 2001'.In FORMULA-QUANTITY, you need to outline a step-by-step process that how you extract all the quantity in formula.For example: the 2 in 'q=2'(q is the measured entity) In ANSWER,give the final answer in a tsv format explained below, and it must match the correct answer exactly. Here's how the format should look:<ARABIC-QUANTITY> [Provide a chain-of-thought, logical explanation of how you extract all arabic quantities in the text. This should outline step-by-step reasoning.] </ARABIC-QUANTITY> <ALPHABETIC-QUANTITY> [Provide a chain-of-thought, logical explanation of how you extract all alphabetic quantities in the text,like two in 'two stages' This should outline step-by-step reasoning.] </ALPHABETIC-QUANTITY> <CHANGE-QUANTITY> [Provide a chain-of-thought, logical explanation of how you extract all the quantity describes changes,such as the 2.12 in 'fall dwon to 2.12'. This should outline step-by-step reasoning.] </CHANGE-QUANTITY> <TIME-QUANTITY> [Provide a chain-of-thought, logical explanation of how you extract the time related quantities like 'before the summer of 2015' for each previously identified quantity. This should outline step-by-step reasoning.] </TIME-QUANTITY><FORMULA-QUANTITY> [Provide a chain-of-thought, logical explanation of how you extract all the quantities in formula, like 3 in 't=3',where t is the measured entity. for each previously identified quantity. This should outline step-by-step reasoning.] </FORMULA-QUANTITY> <CONCLUSION> [State the final answer in a tsv format explained below format. Please extract all of the quantities based on the information I provide to you. But you have to find all the quantities in the text,you can't only based on the quantulum information.] </CONCLUSION> (Do not forget </CONCLUSION>!) Please apply this format meticulously to analyze the text and extract all of the quantities.

---
Task Definition: Extract Quantities
1. Annotation of Quantities: 
  - Identify and annotate all Quantities in the paragraph.
  - Quantities may include values and units (measurements), or just values (counts).
  - If a quantity involves a modifier such as "approximately" or symbols like ">", include it if adjacent to the quantity span.
  - Counts of entities (e.g., "five samples") should also be annotated as Quantities.
2. Example Process: 
  - Extract all the quantity in arabic form.(e.g.,'5','approximately 25°C')
  - Extract all the quantity in alphabetic form.(e.g.,'two','nine')
  - Extract all the quantity describes changes.(e.g., 'a rise of 5', 'fall 5%%')
  - Extract all the quantity related to time.(e.g. 'before December 2001')
  - Extract all the quantity in the formula. (e.g. 'p = 5','where g = 10*5+4+1/2')
  - Annotate any numbers or phrases that represent quantities, including both measurements and counts, and answer in tsv form.
---
Output Format (TSV Fields):
- annotType: As you're extracting quantities, this field should be Quantity
- text: The exact text of the annotation from the input.Please only extract text of quantity with its modifiers and unit.
---
Final Output Example (TSV Format):
annotType   text
Quantity    approximately 25°C
Quantity    500 milliliters
Quantity    10 grams
if there is no quantity, just output:
annotType       text
---



The reference answer from quantulum:%s
The quantity in Quantulum is standardized. In the output, you should present it according to the original text content, and not according to the information from Quantulum!
Input: %s
'''

textpaths = [
        "data/train/text/"]
tsvpath = "data/train/tsv/"
client = OpenAI()

typemap = {"Quantity": "QUANT",
        "MeasuredEntity": "ME",
        "MeasuredProperty": "MP",
        "Qualifier": "QUAL"}

docIds = []
textset = {}
file_lock = threading.Lock()

file_path = 'datas.jsonl'

def process_line(line):
    try:
        data = json.loads(line)
        article_id = data["article_id"]
        abstract_text = data["abstract_text"]
        parsed_result = data["parsed_result"]
        print(article_id)
        filled_template = message_template_quantity % (parsed_result, abstract_text)
        
        cnt = 10
        while cnt > 0:
            try:
                response = client.chat.completions.create(
                    model="deepseek-v3",
                    messages=[
                        {"role": "system", "content": "You are an expert in quantity relations extraction."},
                        {"role": "user", "content": filled_template}
                    ]
                )
                result_quantity = response.choices[0].message.content
                pattern = r"^<ARABIC-QUANTITY>.*</ARABIC-QUANTITY>\n+<ALPHABETIC-QUANTITY>.*</ALPHABETIC-QUANTITY>\n+<CHANGE-QUANTITY>.*</CHANGE-QUANTITY>\n+<TIME-QUANTITY>.*</TIME-QUANTITY>\n+<FORMULA-QUANTITY>.*</FORMULA-QUANTITY>\n+<CONCLUSION>.*</CONCLUSION>$"
                match = re.search(pattern, result_quantity, re.DOTALL)
                if (match != None):
                    
                    pattern = r'<CONCLUSION>(.*?)</CONCLUSION>'
                    match = re.search(pattern, result_quantity, re.DOTALL)
                    quantity_result_content = match.group(1)

                    df = pd.read_csv(StringIO(quantity_result_content) ,sep='\t').reset_index(drop=True)
                    def is_column_all_quantity(df):
                        return (df['annotType'] == 'Quantity').all()

                    result = is_column_all_quantity(df)
                    if not result:
                        raise ValueError("annotType标注错误")
                    t = df['text']
                    output_data = {
                        "docId": article_id,
                        "query": 'Please help me extract all of the Quantities along with their modifiers and units. And think according to the following six stages:ARABIC-QUANTITY,ALPHABETIC-QUANTITY,CHANGE-QUANTITY,TIME-QUANTITY,FORMULA-QUANTITY and CONCLUSION. \n\nInput: '+abstract_text,
                        "original_text": abstract_text,
                        "quantity_reasoning_process": result_quantity
                    }
                        
                        # 写入文件时加锁
                    with file_lock:
                        with open('quantity_6stage_100k.jsonl', 'a', encoding='utf-8') as outfile:
                            json_line = json.dumps(output_data, ensure_ascii=False)
                            outfile.write(json_line + '\n')
                    break
                else:
                    raise ValueError("The quantity result does not contain the necessary tags")
                    
            except Exception as e:
                print(f"Error processing article {article_id}: {str(e)}")
                cnt -= 1
                if cnt == 0:
                    print(f"Failed to process article {article_id} after 5 attempts")
    except Exception as e:
        print(f"Error parsing line: {str(e)}")

def process_file_with_threads(file_path, num_threads):
    with open(file_path, 'r') as file:
        # 使用ThreadPoolExecutor创建线程池
        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            # 提交所有行处理任务
            futures = [executor.submit(process_line, line) for line in file]
            
            # 等待所有任务完成
            for future in concurrent.futures.as_completed(futures):
                try:
                    future.result()  # 获取结果，如果有异常会在这里抛出
                except Exception as e:
                    print(f"Thread error: {str(e)}")

# 使用示例
process_file_with_threads("datas.jsonl", num_threads=256)
                # break
        # break

# # 创建线程锁
# file_lock = threading.Lock()


# def process_doc(docId):
#     try:
#         print(docId)
#         text = textset[docId]
#         standard_ans_path = tsvpath + str(docId) + '.tsv'

#         ans = pd.read_csv(standard_ans_path, sep='\t')
#         ans = ans.drop('docId', axis=1)
#         quantity_ans = ans[ans['annotType'] == 'Quantity'].drop('annotId', axis=1)
        # response = client.chat.completions.create(
        #     model="deepseek-v3",  # 填写需要调用的模型名称
        #     messages=[{"role": "system", "content": "You are an expert in quantity relations extraction."},
        #               {"role": "user", "content": message_template_quantity % (quantity_ans.to_string(), text)}])
        # result_quantity = response.choices[0].message.content

        # response = client.chat.completions.create(
        #     model="deepseek-v3",  # 填写需要调用的模型名称
        #     messages=[{"role": "system", "content": "You are an expert in quantity relations extraction."},
        #               {"role": "user", "content": message_template_everything % (
        #                   quantity_ans.to_string(), ans.to_string(), text)}])
        # result_everything = response.choices[0].message.content
        # reasoning_process = result_quantity + '\n' + result_everything
        # # print(reasoning_process)
#         output_data = {
#             "docId": docId,
#             "text": text,
#             "reasoning_process": reasoning_process
#         }
#         # 每次处理数据时打开文件并追加写入
#         output_file = 'step_reasoning.jsonl'
#         # 获取锁
#         with file_lock:
#             with open(output_file, 'a', encoding='utf-8') as outfile:
#                 json_line = json.dumps(output_data, ensure_ascii=False)
#                 outfile.write(json_line + '\n')
#     except Exception as e:
#         print(f"处理 docId {docId} 时出错: {e}")

# # 使用 ThreadPoolExecutor 进行并发处理
# with ThreadPoolExecutor(max_workers=200) as executor:
#     executor.map(process_doc, docIds)