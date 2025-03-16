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


valid_mods_keys = ['IsCount', 'IsApproximate', 'IsMeanHasTolerance', 'IsMedian',
                   'IsList', 'IsRangeHasTolerance', 'IsMean', 'IsRange',
                   'HasTolerance', 'IsMeanIsRange', 'IsMeanHasSD']
class JsonValidator(Validator):
    """ Validates that a field contains valid JSON data """

    def __init__(self, **kwargs):
        super(JsonValidator, self).__init__(**kwargs)
        self.failures = set([])

    def validate(self, field, row={}):
        if ((not field) and (not self.empty_ok)):
            self.failures.add(field)
            logging.info("'{}' is empty".format(field))
            raise ValidationException(
                "'{}' is empty".format(field)
            )
        elif (field != ""):
            #print(field)
            try:
                data = json.loads(field)
                #print(list(data.keys()))
                if not all(k in ["HasQuantity", "HasProperty", "Qualifies", "mods", "unit"]
                           for k in list(data.keys())):
                    self.failures.add(field)
                    logging.info("'{}' has invalid key_100".format(field))
                    raise ValidationException(
                        "'{}' has invalid key".format(field)
                    )
                if row["annotType"] == "Quantity":
                    if not all(k in ["mods", "unit"] for k in list(data.keys())):
                        self.failures.add(field)
                        logging.info("'{}' has invalid key_Quantity".format(field))
                        raise ValidationException(
                            "'{}' has invalid key".format(field)
                        )
                    if "mods" in list(data.keys()):
                        if type(data["mods"]) != list:
                            self.failures.add(field)
                            logging.info("'{}' mods field is not a list".format(field))
                            raise ValidationException(
                                "'{}' mods field is not a list".format(field)
                            )
                        if not all(k in ['IsCount', 'IsApproximate', 'IsMeanHasTolerance', 'IsMedian',
                                          'IsList', 'IsRangeHasTolerance', 'IsMean', 'IsRange',
                                          'HasTolerance', 'IsMeanIsRange', 'IsMeanHasSD'] for k in data["mods"]):
                            self.failures.add(field)
                            logging.info("'{}' has invalid key in mods".format(field))
                            raise ValidationException(
                                "'{}' has invalid key in mods".format(field)
                            )
                if row["annotType"] == "MeasuredEntity":
                    if not all(k in ["HasProperty", "HasQuantity"] for k in list(data.keys())):
                        self.failures.add(field)
                        logging.info("'{}' has invalid key_MeasuredEntity".format(field))
                        raise ValidationException(
                            "'{}' has invalid key".format(field)
                        )
                if row["annotType"] == "MeasuredProperty":
                    if not all(k in ["HasQuantity"] for k in list(data.keys())):
                        self.failures.add(field)
                        logging.info("'{}' has invalid key_MeasuredProperty".format(field))
                        raise ValidationException(
                            "'{}' has invalid key".format(field)
                        )
                if row["annotType"] == "Qualifier":
                    if not all(k in ["Qualifies"] for k in list(data.keys())):
                        self.failures.add(field)
                        logging.info("'{}' has invalid key_Qualifier".format(field))
                        raise ValidationException(
                            "'{}' has invalid key".format(field)
                        )
            except json.decoder.JSONDecodeError:
                self.failures.add(field)
                raise ValidationException(
                    "'{}' is not valid json".format(field)
                )

    @property
    def bad(self):
        return self.failures
class LengthValidator(Validator):
    """ Validates that a text field's length is correct based on other fields """

    def __init__(self, **kwargs):
        super(LengthValidator, self).__init__(**kwargs)
        self.failures = set([])

    def validate(self, field, row={}):
        expectedLen = int(row["endOffset"]) - int(row["startOffset"])
        textLen = len(field)
        if expectedLen != textLen and (field or not self.empty_ok):
            self.failures.add(field)
            raise ValidationException(
                "'{}' length {} does not match extpected length /{}/".format(field, textLen, expectedLen)
            )

    @property
    def bad(self):
        return self.failures


def update_row(row, start_offset, end_offset):
    # 创建新的字典，将 'startOffset' 和 'endOffset' 插入到 'annotType' 后面
    return {
        'docId': row['docId'],
        'annotSet': row['annotSet'],
        'annotType': row['annotType'],
        'startOffset': start_offset,
        'endOffset': end_offset,
        'annotId': row['annotId'],
        'text': row['text'],
        'other': row['other']
    }

# 删除other中llm给出的不合法的多余字段
def filter_other_field(other_str,valid_key):
    try:
        # 解析 JSON 字符串
        other = json.loads(other_str)
        # 过滤掉不在有效键列表中的键
        filtered_other = {key: value for key, value in other.items() if key in valid_key}
        # 将过滤后的数据转换回 JSON 字符串
        if len(filtered_other) == 0:
            return ""
        return json.dumps(filtered_other)
    except json.JSONDecodeError:
        print(f"'other' 字段不是有效的 JSON 字符串: {other_str}")
        return other_str

def find_quantity_offsets(tsv_file, txt_file, output_file):
    # read
    annot_df = pd.read_csv(tsv_file, sep='\t')

    with open(txt_file, 'r') as f:
        text = f.read()

    updated_rows = []
    for annot_set_id, annot_set in annot_df.groupby('annotSet'):
        # print(annot_set)
        # print("---------------------------------------------------------------------------------------------------")
        quantity_start_offset = None
        quantity_end_offset = None



        for index, row in annot_set.iterrows():
            valid_keys = ["HasQuantity", "HasProperty", "Qualifies", "mods", "unit"]
            row['other'] = filter_other_field(row['other'],valid_keys)
            other = json.loads(row['other'])
            
            #处理mods字段
            if 'mods' in other:
                    # 过滤 mods 字段，只保留 valid_mods_keys 中的键
                other['mods'] = [mod for mod in other['mods'] if mod in valid_mods_keys]
                    # 将更新后的 other 转换回 JSON 字符串
                row['other'] = json.dumps(other)
      

            if row['annotType'] == 'Quantity':
                valid_keys = ["mods", "unit"]
                quantity_text = row.get('text', '')
                row['other'] = filter_other_field(row['other'],valid_keys)

                quantity_start_offset = text.find(quantity_text)
                if quantity_start_offset == -1:
                    print(f"Quantity '{quantity_text}' not found in the text.")
                    continue  # 如果没有找到该数量，跳过该行
                
                # 计算   end_offset
                quantity_end_offset = quantity_start_offset + len(quantity_text)
                
                updated_row = update_row(row, quantity_start_offset, quantity_end_offset)
                updated_rows.append(updated_row)

        # 如果找到了 Quantity，继续处理 MeasuredEntity, MeasuredProperty, 和 Qualifier
        if quantity_start_offset is not None:
            for index, row in annot_set.iterrows():
              
                valid_keys = ["HasQuantity", "HasProperty", "Qualifies", "mods", "unit"]
                row['other'] = filter_other_field(row['other'],valid_keys)
                other = json.loads(row['other'])
                
                if 'mods' in other:
                    # 过滤 mods 字段，只保留 valid_mods_keys 中的键
                    print(other['mods'])
                    print(valid_mods_keys)
                    other['mods'] = [mod for mod in other['mods'] if mod in valid_mods_keys]
                    # 将更新后的 other 转换回 JSON 字符串
                    row['other'] = json.dumps(other)

                if row['annotType'] == 'MeasuredEntity':
                    valid_keys = ["HasProperty", "HasQuantity"]
                    measured_entity_text = row.get('text', '')
                    row['other'] = filter_other_field(row['other'],valid_keys)
                    if row['other'] == "": continue
                    # 在 Quantity 的位置附近查找 MeasuredEntity
                    start_offset = text.find(measured_entity_text, max(0, quantity_start_offset - 100), quantity_start_offset + 100)  # 先往前后各查找 100 个字符
                    
                    if start_offset == -1:
                        print(f"MeasuredEntity '{measured_entity_text}' not found near Quantity.")
                        continue
                    
                    end_offset = start_offset + len(measured_entity_text)
                    

                    updated_row = update_row(row, start_offset, end_offset)
                    updated_rows.append(updated_row)
                
                # 检查当前行的 annotType 是否为 MeasuredProperty
                elif row['annotType'] == 'MeasuredProperty':

                    measured_property_text = row.get('text', '')
                    valid_keys = ['HasQuantity']
                    row['other'] = filter_other_field(row['other'],valid_keys)
                    if row['other'] == "" : continue
                    start_offset = text.find(measured_property_text, max(0, quantity_start_offset - 100), quantity_start_offset + 100)  # 先往前后各查找 100 个字符
                    
                    if start_offset == -1:
                        print(f"MeasuredProperty '{measured_property_text}' not found near Quantity.")
                        continue
                    
                    end_offset = start_offset + len(measured_property_text)
                    

                    updated_row = update_row(row, start_offset, end_offset)
                    updated_rows.append(updated_row)
                
                # 检查当前行的 annotType 是否为 Qualifier
                elif row['annotType'] == 'Qualifier':

                    qualifier_text = row.get('text', '')
                    valid_keys = ['Qualifies']
                    row['other'] = filter_other_field(row['other'],valid_keys)
                    if row['other'] == "":continue
                    start_offset = text.find(qualifier_text, max(0, quantity_start_offset - 100), quantity_start_offset + 100)  # 先往前后各查找 100 个字符
                    
                    if start_offset == -1:
                        print(f"Qualifier '{qualifier_text}' not found near Quantity.")
                        continue
                    
                    end_offset = start_offset + len(qualifier_text)
                    
                    # 使用 update_row 函数创建更新后的字典并加入到列表
                    updated_row = update_row(row, start_offset, end_offset)
                    updated_rows.append(updated_row)

    # 将更新后的数据写入新的 TSV 文件
    updated_df = pd.DataFrame(updated_rows)
    validators = {
            'docId': [
                UniqueValidator(unique_with=['annotSet', 'annotId']),
                #UniqueValidator(unique_with=['annotSet', 'startOffset'])
            ],
            'annotId': [
                RegexValidator(pattern=r'T?\d*-?\d+', full=True)
            ],
            'annotType': [
                SetValidator(['Quantity', 'Qualifier', 'MeasuredProperty', 'MeasuredEntity'])
            ],
            'annotSet': [
                IntValidator()
            ],
            'startOffset': [
                IntValidator()
            ],
            'endOffset': [
                IntValidator()
            ],
            'other': [
                JsonValidator(empty_ok=True)
            ],
            'text': [
                LengthValidator()
            ]
        }
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.tsv') as temp_file:
            # 将 DataFrame 保存为 TSV 文件
            updated_df.to_csv(temp_file.name, sep='\t',index=False)
    vlad = Vlad(source=LocalFile(temp_file.name), validators=validators, delimiter="\t")
    truth = vlad.validate()

    if truth == False:
        raise ValueError("数据验证失败")

    if updated_df.empty:
              updated_df = pd.DataFrame(columns=['docId', 'annotSet', 'annotType', 'startOffset', 'endOffset', 'annotId', 'text', 'other'])
    # print(updated_df)
    updated_df.to_csv(output_file, sep='\t', index=False)



message_template="""
Instruction:
You are an expert in extracting structured annotations from text. Your task is to identify and classify Quantities, MeasuredEntities, MeasuredProperties, and Qualifiers, along with their relationships. Please follow the step-by-step reasoning process below and provide the output strictly in the specified TSV format.

---
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
  - Mark any necessary Qualifier spans that provide context to interpret the Quantity.
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
  - HasQuantity: Connects MeasuredEntity to Quantity (e.g., "solution" -> "25°C")
  - HasProperty: Connects MeasuredEntity to MeasuredProperty (e.g., "solution" -> "temperature")
  - Qualifies: "approximately" qualifies the temperature.

---
Final Output (TSV Format):

annotSet    annotType           annotId    text                other
1           Quantity            T1         approximately 25°C  {"unit": "°C", "mods": ["IsApproximate"]}
1           MeasuredEntity      T2         solution            {"HasQuantity": "T1"}
1           MeasuredProperty    T3         temperature         {"HasQuantity": "T1", "HasProperty": "T2"}
2           Quantity            T4         500 milliliters     {"unit": "milliliters"}
2           MeasuredEntity      T5         solvent             {"HasQuantity": "T4"}
2           MeasuredProperty    T6         volume              {"HasQuantity": "T4", "HasProperty": "T5"}
3           Quantity            T7         10 grams            {"unit": "grams"}
3           MeasuredEntity      T8         salt                {"HasQuantity": "T7"}
3           MeasuredProperty    T9         amount              {"HasQuantity": "T7", "HasProperty": "T8"}


 Input：%s

"""





textpaths = [
            "data/train/text/"]
# textpaths = [
#             "data/eval/text/"]

client = OpenAI(api_key="sk-danqwpmat42akvfw",
                base_url="https://cloud.infini-ai.com/maas/v1")

typemap = {"Quantity": "QUANT",
           "MeasuredEntity": "ME", 
           "MeasuredProperty": "MP", 
           "Qualifier": "QUAL"}

docIds = []
textset = {}


for fileset in textpaths:
    for fn in os.listdir(fileset):
        with open(fileset + fn) as textfile:
            text = textfile.read() #.splitlines()
            #print(fn[:-4])
            textset[fn[:-4]] = text
            docIds.append(fn[:-4])
ents = {}


for docId in docIds:
    print(docId)
    
            
    cnt = 10
    while cnt >0:
        try:
          text = textset[docId]


          ents[docId] = {}



          response = client.chat.completions.create(
                  model="deepseek-v3",  # 填写需要调用的模型名称
                  messages=[{"role": "system", "content": "You are an expert in quantity relations extraction."},
                        {"role": "user", "content": message_template % (text)}])
          
          
          result=response.choices[0].message.content
      #     print(result)
          line_pattern = re.compile(
          r"(?P<annotSet>\d+)\s+"
          r"(?P<annotType>\w+)\s+"
          r"(?P<annotId>[a-zA-Z0-9-]+)\s+"
          r"(?P<text>.+?)\s+"
          r"(?P<other>{.+})" 
          )
          lines = []

          # print(result)




              
          for match in line_pattern.finditer(result):
              lines.append({
                  "docId": docId,
                  "annotSet": int(match.group("annotSet")),
                  "annotType": match.group("annotType"),
                  "annotId": match.group("annotId"),
                  "text": match.group("text").strip(),
                  "other": match.group("other"),
              })
          # 创建 DataFrame
          df = pd.DataFrame(lines)
          
          # 格式化输出
          formatted_output = df.to_string(index=False, justify="left")

          # 打印格式化的表格
          # print(formatted_output)

          # 如果需要保存为 TSV 文件
          df.to_csv(f"raw/{docId}.tsv", sep="\t", index=False)

          find_quantity_offsets(f"raw/{docId}.tsv", f"data/train/text/{docId}.txt", f"data/output_v3_train/{docId}.tsv")
        #   find_quantity_offsets(f"raw/{docId}.tsv", f"data/eval/text/{docId}.txt", f"data/output_v3/{docId}.tsv")


          break
        except Exception as e:
            cnt-=1
            print("解析出错，重试中----------------------------------------------------------")
            print(result)
            error_info = traceback.format_exc()
            print(e)
            print("完整错误信息:")
            print(error_info)
            print("----------------------------------------------------------------------")
        if cnt ==0:
              print(f"{docId}maybe no quantity,please check")
              df = pd.DataFrame(columns=['docId', 'annotSet', 'annotType', 'startOffset', 'endOffset', 'annotId', 'text', 'other'])
              df.to_csv(f"data/output_v3_train/{docId}.tsv",sep='\t',index=False)
            #   df.to_csv(f"data/output_v3/{docId}.tsv",sep='\t',index=False)

    # break 