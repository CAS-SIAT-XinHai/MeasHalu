import os

import re
import json
from schemas.grobid_quantities_adapted import GrobidQuantitiesAnnotationMeasurementValue,GrobidQuantitiesAnnotationMeasurementInterval,GrobidQuantitiesAnnotationMeasurementList,GrobidQuantitiesAnnotationInstance
docIds = []
textset = {}

textpaths = [
            "data/grobid_r1_reasoning/"]
for fileset in textpaths:
    for fn in os.listdir(fileset):
        with open(fileset + fn) as textfile:
            text = textfile.read() #.splitlines()
            #print(fn[:-4])
            textset[fn[:-4]] = text
            docIds.append(fn[:-4])
def check_reasoning_grobid(text):
    if re.search(r'[\u4e00-\u9fff]', text):
        raise ValueError("chinese exists")
    json_blocks = re.findall(r'\'\'\'([\s\S]*?)\'\'\'', text)
    # 依次输出每个JSON块
    for i, block in enumerate(json_blocks, 1):
        if '...' in block:
            continue
        # print(f"JSON Block {i}:")
        # print(block)
        # print('-'*100)
        try:
            json_obj = json.loads(block)
            # print(json_obj.keys())
        except:
            raise ValueError("json format is incorret")
        # print(json_obj)
        # print(json_obj.keys())
        # print("-" * 50)  # 分隔符
        quantityMost,quantityLeast,quantity = None,None,None
        try:
            if 'quantity' in json_obj.keys():
                # print(json_obj)
                # quantity = json_obj.get('quantity')
                # print(json_obj)
                obj = GrobidQuantitiesAnnotationMeasurementValue(**json_obj)
                # print(obj)
                break
            elif ('quantityLeast' or 'quantityMost') in json_obj.keys():
                obj = GrobidQuantitiesAnnotationMeasurementInterval(**json_obj)
            elif 'quantities' in json_obj.keys():
                obj = GrobidQuantitiesAnnotationMeasurementList(**json_obj)                    

            if 'measurements' in json_obj.keys():
                # print("yes!!!")
                obj = GrobidQuantitiesAnnotationInstance(**json_obj)
        except Exception as e:
            raise ValueError(e)


