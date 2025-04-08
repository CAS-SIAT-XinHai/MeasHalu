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
message_template_quantity = '''
Instruction:
You are an expert in extracting structured annotations from text.
I have an text input and you need to extract all the quantities within it. I need you to strictly follow the format with two specific sections: QUANTITY-REASONING, QUANTITY-RESULT. It is crucial that you adhere to this structure exactly as outlined, the quantulum information maybe incorrect, so you have to get the quantity along with units and modifiers from the text on your own. To explain further: In QUANTITY-REASONING, outline a step-by-step thought process you would use to extract all the quantities in the text.You should demonstrate the process of how you found the quantity within the text, and you are not allowed to mention obtaining it from the Quantulum library. In QUANTITY-ANSWER, give the final answer in a tsv format explained below, I will provide you with the quantities extracted using the quantulum library for your reference, the information provided by Quantulum is standardized. You need to find the original text in the passage and fill in the tsv form.Also, the quantulum information maybe incorrect, You can't follow it completely. Here's how the format should look: <QUANTITY-REASONING> [Provide a chain-of-thought, logical explanation of how you extract all quantities in the text. This should outline step-by-step reasoning.And you are not allowed to mention obtaining it from the Quantulum library.] </QUANTITY-REASONING> <QUANTITY-ANSWER> [State the final answer in a tsv format explained below format. Please extract all of the quantities based on the information I provide to you. But you have to find all the quantities in the text,you can't only based on the quantulum information.] </QUANTITY-ANSWER> (Do not forget </QUANTITY-ANSWER>!) Please apply this format meticulously to analyze the text and extract all of the quantities, ensuring that the answer matches the standard one perfectly.
---
Task Definition: Extract Quantities
1. Annotation of Quantities: 
  - Identify and annotate all Quantities in the paragraph.
  - Quantities may include values and units (measurements), or just values (counts).
  - If a quantity involves a modifier such as "approximately" or symbols like ">", include it if adjacent to the quantity span.
  - Counts of entities (e.g., "five samples") should also be annotated as Quantities.
2. Example Process: 
  - Read through the paragraph and identify each quantity, whether numeric (e.g., "5", "355") or descriptive (e.g., "room temperature", "sea level").
  - Annotate any numbers or phrases that represent quantities, including both measurements and counts.
---
Output Format (TSV Fields):
- annotSet: The annotation set ID (starting from 1 for each logical grouping of related annotations).
- annotType: As you're extracting quantities, this field should be Quantity
- text: The exact text of the annotation from the input.Please only extract text of quantity with its modifiers and unit.
- other: If annotType is Quantities: Extract all phrases involving quantities, specifying their unit and modifiers (if any). Include unit (e.g., "kg", "ppm"), ensure that all modifiers are placed inside "mods" (e.g., "mods": ["IsCount"]), and si (SI equivalent of the unit, if applicable). Optional modifiers include IsApproximate (indicating approximate values, e.g., "around 1300 m/s"), IsCount (indicating a count, e.g., "four samples"), IsRange (indicating a range, e.g., "1.5-2.6m"), IsList (indicating a list of quantities, e.g., "4.5kg, 6kg, 13kg"), IsMedian (indicating a median value, e.g., "10ppq"), IsMean (indicating a mean value, e.g., "9 ± 6"), and IsMeanHasSD (indicating a mean value with standard deviation, e.g., "1.23 ± 0.25").
Example: {"mods": ["IsMean"], "unit": "years"}
else if annotType is Other types (e.g., MeasuredEntities, MeasuredProperties, Qualifier,etc.):You must annotate relationships between entities using the format {relationType: targetAnnotation}.
Examples: if annotType is MeasuredEntities:{"HasProperty": "T21-4"},MeasyredProperties:{"HasQuantity":"T3-2"},Qualifier:{"Qualifies": "T4-5"}
---
Final Output Example (TSV Format):
annotSet    annotType   text                other
1   Quantity    approximately 25°C  {"unit": "°C", "mods": ["IsApproximate"]}
2   Quantity    500 milliliters {"unit": "milliliters"}
3   Quantity    10 grams    {"unit": "grams"}
if there is no quantity, just output:
annotSet        annotType       text    other
---



The reference answer from quantulum:%s
if the unit is dimensionless, it means this quantity don't have unit, you don't have to fill the unit field.
The quantity in Quantulum is standardized. In the output, you should present it according to the original text content, and not according to the information from Quantulum!
Input: %s
'''

message_template_everything = '''
You are an expert in extracting structured annotations from text.
Instruction:
You are an expert in extracting structured annotations from text.
In the previous step, you have already extracted the "quantity" from the text file. Now, you need to extract all the Measured Entities, Measured Properties, and Qualifiers corresponding to the quantity, along with their relationships.I have an text input and you need to extract all the quantities within it. I need you to strictly follow the format with two specific sections: EVERYTHING-REASONING, CONCLUSION. It is crucial that you adhere to this structure exactly as outlined and extract all the Measured Entities, Measured Properties, and Qualifiers corresponding to the quantity, along with their relationships. To explain further: In EVERYTHING-REASONING, outline a step-by-step thought process you utilize the quantity information you have already extracted to extract all the Measured Entities, Measured Properties, and Qualifiers corresponding to the quantity. In CONCLUSION, give the final answer in a tsv format explained below,summarizing all of the information,including Quantities,Measured Entities, Measured Properties, and Qualifiers along with relationships corresponding to the quantity. Here's how the format should look: <EVERYTHING-REASONING> [Provide a chain-of-thought, logical explanation of how you extract MeasuredEntities, MeasuredProperties, and Qualifiers, along with their relationships in the text. This should outline step-by-step reasoning.] </EVERYTHING-REASONING> <CONCLUSION> [Combine the information of quantities with the information extracted from EVERYTHING-REASONING to generate the answers in TSV format.] </CONCLUSION> (Do not forget </CONCLUSION>!) Please apply this format meticulously to analyze the text and extract all of the MeasuredEntities, MeasuredProperties, and Qualifiers, along with their relationships corresponding to the quantities,and put the extracted information together with the quantities into a TSV file.
---
Task Definition:
Annotation Type Definitions:
1. Quantity: A value that can represent a Count (e.g., "5 apples") or a Measurement (e.g., "355 ml"). It may include optional Modifiers such as tolerances and must ideally relate to a MeasuredEntity or MeasuredProperty using the "HasQuantity" relationship. If no such entity exists, the Quantity can remain standalone. 
  - Example: "355 ml" in "The soda can's volume was 355 ml."
2. MeasuredEntity: The object or entity associated with a Quantity. It must relate to the Quantity via "HasQuantity". If applicable, it can also relate to a MeasuredProperty using "HasProperty". 
  - Example: "soda can" in "The soda can's volume was 355 ml."
3. MeasuredProperty: A descriptive property linked to both a MeasuredEntity (via "HasProperty") and a Quantity (via "HasQuantity"). It is optional. 
  - Example: "volume" in "The soda can's volume was 355 ml."
4. Qualifier: An optional span describing conditions or attributes that affect a Quantity, MeasuredEntity, or MeasuredProperty. It is related using the "Qualifies" relationship. 
  - Example: "after I drank half the can" in "The can contained 175 ml of soda after I drank half the can."
5. Unit: The unit of a Quantity, typically included within the Quantity span (e.g., "ml").
---
Relationships Definitions:
1. HasQuantity: Links a MeasuredEntity or MeasuredProperty to a Quantity.
2. HasProperty: Links a MeasuredEntity to a MeasuredProperty.
3. Qualifies: Links a Qualifier to a Quantity, MeasuredEntity, or MeasuredProperty.
---
Output Format (TSV Fields):
- annotSet: The annotation set ID (starting from 1 for each logical grouping of related annotations).
- annotType: One of the following types: Quantity, MeasuredEntity, MeasuredProperty, or Qualifier.
- startOffset: character offset of the start of the annotation in the text.
- endOffset: character offset pointing to the character after the last character in the annotation.
- annotId: A unique identifier for the annotation (e.g., T1, T2), numbered sequentially within each annotSet.
- text: The exact text of the annotation from the input.
- other: If annotType is Quantities: Extract all phrases involving quantities, specifying their unit and modifiers (if any). Include unit (e.g., "kg", "ppm"), ensure that all modifiers are placed inside "mods" (e.g., "mods": ["IsCount"]), and si (SI equivalent of the unit, if applicable). Optional modifiers include IsApproximate (indicating approximate values, e.g., "around 1300 m/s"), IsCount (indicating a count, e.g., "four samples"), IsRange (indicating a range, e.g., "1.5-2.6m"), IsList (indicating a list of quantities, e.g., "4.5kg, 6kg, 13kg"), IsMedian (indicating a median value, e.g., "10ppq"), IsMean (indicating a mean value, e.g., "9 ± 6"), and IsMeanHasSD (indicating a mean value with standard deviation, e.g., "1.23 ± 0.25").
Example: {"mods": ["IsMean"], "unit": "years"}
else if annotType is Other types (e.g., MeasuredEntities, MeasuredProperties, Qualifier,etc.):You must annotate relationships between entities using the format {relationType: targetAnnotation}.
Examples: if annotType is MeasuredEntities:{"HasProperty": "T21-4"},MeasyredProperties:{"HasQuantity":"T3-2"},Qualifier:{"Qualifies": "T4-5"}
---

Annotation Steps:
Step 1: Extract Quantities
1. Annotation of Quantities: 
  - Identify and annotate all Quantities in the paragraph.
  - Quantities may include values and units (measurements), or just values (counts).
  - If a quantity involves a modifier such as "approximately" or symbols like ">", include it if adjacent to the quantity span.
  - Counts of entities (e.g., "five samples") should also be annotated as Quantities.
2. Example Process: 
  - Read through the paragraph and identify each quantity, whether numeric (e.g., "5", "355") or descriptive (e.g., "room temperature", "sea level").
  - Annotate any numbers or phrases that represent quantities, including both measurements and counts.
In this step, you can refer to the quantity information that you have previously extracted, which is mentioned later.

---
Step 2: For Each Quanties，Extract Quantity Modifiers, Units, and Additional Spans and Relations
1. Quantity Modifiers and Units:
  - Correct the Quantity if necessary, then annotate any relevant Modifiers and Units for the Quantity.
  - Add a "Unit" span for the relevant unit if applicable.
  - If the Quantity is approximate, include the text indicating this in the span and tick the "IsApproximate" box.
  - If the Quantity represents a count and lacks a corresponding unit, tick the "IsCount" box.
2. Special Quantity Modifiers:
  - IsApproximate: Indicates the Quantity is an approximation (e.g., "around 1300 m/s").
  - IsCount: Indicates a count of entities (e.g., "four transits").
  - IsRange: Denotes a range of values (e.g., "1.5–2.6 m").
  - IsList: Denotes a list of quantities (e.g., "4.5 kg, 6 kg, and 13 kg").
  - IsMean: Indicates an average value (e.g., "490 K").
  - IsMedian: Indicates a median value (e.g., "10 ppq").
  - IsMeanHasSD: Indicates a mean with standard deviation (e.g., "1.23±0.25‰").
  - HasTolerance: Indicates tolerance (e.g., "93.90±0.15 Ma").
3. Additional Spans and Relations:
  - Mark the MeasuredEntity associated with the Quantity.
  - Mark the MeasuredProperty, if present.
  - Mark any necessary Qualifier spans, which could include elements like temporal (e.g., 'in the last month'), spatial (e.g., 'in the downtown area'), or conditional (e.g., 'if the product is on sale') qualifiers, that provide context to accurately interpret the Quantity.
  - Be sure to include modifying adjectives or nouns that describe the MeasuredEntity (e.g., "Venera-I spacecraft" instead of just "spacecraft").
4. Create Relationships:
  - HasQuantity: Connect the MeasuredEntity (or MeasuredProperty) to the Quantity.
  - HasProperty: Connect the MeasuredEntity to the MeasuredProperty if applicable.
  - Qualifies: If a modifier is not adjacent to the Quantity, link it to the relevant span using a "Qualifies" relationship.


Example Paragraph:
"The temperature of the solution was approximately 25°C, and the volume of the solvent was 500 milliliters. We also added 10 grams of salt to the solution."


Step 1: Extract Quantities
- Quantities: 
  - "approximately 25°C" (Temperature)
  - "500 milliliters" (Volume of solvent)
  - "10 grams" (Amount of salt)
Step 2: For Each Quanties，Extract Quantity Modifiers, Units, and Additional Spans and Relations
- Modifiers: 
  - "approximately" is a modifier for "25°C", marking it as IsApproximate.
- Units: 
  - "°C" for the temperature (25°C)
  - "milliliters" for the volume (500 milliliters)
  - "grams" for the amount of salt (10 grams)
- MeasuredEntities: 
  - "solution" (for temperature)
  - "solvent" (for volume)
  - "salt" (for amount)
- MeasuredProperties: 
  - "temperature" (for solution)
  - "volume" (for solvent)
  - "amount" (for salt)
- Relationships: 
  - These spans are related using three types of Relationships:
  - HasQuantity, which relates a MeasuredEntity or MeasuredProperty to a Qauntity;
  - HasProperty, which relates a MeasuredEntity to a MeasuredProperty; and
  - Qualifies, which relates a Qualifier to any MeasuredEntity, MeasuredProperty, or Quantity.

---

Final Output (TSV Format):

annotSet    annotType           annotId    text                other
1           Quantity            T1         approximately 25°C  {"unit": "°C", "mods": ["IsApproximate"]}
1           MeasuredProperty    T2         temperature         {"HasQuantity": "T1"}
1           MeasuredEntity      T3         solution            {"HasQuantity": "T1", "HasProperty":"T2"}
2           Quantity            T4         500 milliliters     {"unit": "milliliters"}
2           MeasuredProperty    T5         volume              {"HasQuantity": "T4"}
2           MeasuredEntity      T6         solvent             {"HasQuantity": "T4", "HasProperty": "T5"}
3           Quantity            T7         10 grams            {"unit": "grams"}
3           MeasuredProperty    T9         amount              {"HasQuantity": "T7"}
3           MeasuredEntity      T8         salt                {"HasQuantity": "T7", "HasProperty": "T8"}

Quantities have extracted:%s

Input: %s
'''

textpaths = [
        "data/train/text/"]
tsvpath = "data/train/tsv/"
client = OpenAI(api_key="sk-danqwpmat42akvfw",
                base_url="https://cloud.infini-ai.com/maas/v1")

typemap = {"Quantity": "QUANT",
        "MeasuredEntity": "ME",
        "MeasuredProperty": "MP",
        "Qualifier": "QUAL"}

docIds = []
textset = {}
file_lock = threading.Lock()

# 假设JSONL文件名为 data.jsonl ，根据实际情况修改文件名
file_path = 'datas.jsonl'

def process_line(line):
    try:
        data = json.loads(line)
        article_id = data["article_id"]
        abstract_text = data["abstract_text"]
        parsed_result = data["parsed_result"]
        print(article_id)
        filled_template = message_template_quantity % (parsed_result, abstract_text)
        
        cnt = 3
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
                result_everything = ''
                
                if ("<QUANTITY-REASONING>" in result_quantity and "</QUANTITY-REASONING>" in result_quantity 
                    and "<QUANTITY-ANSWER>" in result_quantity and "</QUANTITY-ANSWER>" in result_quantity):
                    
                    pattern = r'<QUANTITY-ANSWER>(.*?)</QUANTITY-ANSWER>'
                    match = re.search(pattern, result_quantity, re.DOTALL)
                    quantity_result_content = match.group(1)
                    
                    response = client.chat.completions.create(
                        model="deepseek-v3",
                        messages=[
                            {"role": "system", "content": "You are an expert in quantity relations extraction."},
                            {"role": "user", "content": message_template_everything % (quantity_result_content, abstract_text)}
                        ]
                    )
                    result_everything = response.choices[0].message.content
                    
                    if ("<EVERYTHING-REASONING>" in result_everything and "</EVERYTHING-REASONING>" in result_everything 
                        and "<CONCLUSION>" in result_everything and "</CONCLUSION>" in result_everything):
                        
                        pattern = r'<CONCLUSION>(.*?)</CONCLUSION>'
                        match = re.search(pattern, result_everything, re.DOTALL)
                        everything_result_content = match.group(1)
                        
                        if not ('MeasuredEntity' in everything_result_content or 'MeasuredProperty' in everything_result_content 
                                or 'Qualifiers' in everything_result_content):
                            print("only quantity exist!")
                            break
                            
                        reasoning_process = result_quantity + '\n' + result_everything
                        output_data = {
                            "docId": article_id,
                            "text": abstract_text,
                            "reasoning_process": reasoning_process
                        }
                        
                        # 写入文件时加锁
                        with file_lock:
                            with open('step_reasoning.jsonl', 'a', encoding='utf-8') as outfile:
                                json_line = json.dumps(output_data, ensure_ascii=False)
                                outfile.write(json_line + '\n')
                        break
                    else:
                        raise ValueError("The everything result does not contain the necessary tags")
                else:
                    raise ValueError("The quantity result does not contain the necessary tags")
                    
            except Exception as e:
                print(f"Error processing article {article_id}: {str(e)}")
                cnt -= 1
                if cnt == 0:
                    print(f"Failed to process article {article_id} after 3 attempts")
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
process_file_with_threads("datas.jsonl", num_threads=512)
