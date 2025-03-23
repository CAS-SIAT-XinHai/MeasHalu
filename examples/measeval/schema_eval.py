import os
import re

import pandas as pd

from meashalu.schemas.measeval_adapted import (  # 替换为你的模块路径
    MeasEvalAdaptedAnnotationMeasurement,
    MeasEvalAdaptedSetType,
    MeasEvalAdaptedAnnotationIdType,
    MeasEvalAdaptedOtherType,
    MeasEvalAdaptedTextType
)

docIds = []
textset = {}

textpaths = [
    "data/r1_reasoning_train/"]
for fileset in textpaths:
    for fn in os.listdir(fileset):
        with open(fileset + fn) as textfile:
            text = textfile.read()  # .splitlines()
            # print(fn[:-4])
            textset[fn[:-4]] = text
            docIds.append(fn[:-4])

for docId in docIds:
    # print(docId)

    text = textset[docId]

    line_pattern = re.compile(
        r"\n(?P<annotSet>\d+)\s+"
        r"(?P<annotType>\w+)\s+"
        r"(?P<annotId>[a-zA-Z0-9-]+)\s+"
        r"(?P<text>.+?)\s+"
        r"(?P<other>{.+})"
    )

    lines = []

    for match in line_pattern.finditer(text):
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
    df = df.drop_duplicates()
    # print(df)
    entries = []
    for index, row in df.iterrows():
        # print(MeasEvalOtherType(other = row['other']))
        # t = MeasEvalOtherType(other = row['other'])
        # print(t)
        try:
            instance = MeasEvalAdaptedAnnotationMeasurement(
                annotSet=MeasEvalAdaptedSetType(annotSet=row['annotSet']),
                annotType=row['annotType'],
                annotId=MeasEvalAdaptedAnnotationIdType(row['annotId']),
                text=MeasEvalAdaptedTextType(text=row['text']),
                other=MeasEvalAdaptedOtherType(other=row['other'])
            )
            entries.append(instance)
        except Exception as e:
            print(e)
            # print(df)    
            print(
                '---------------------------------------------------------------------------------------------------------------------------')
            # try:
    #     t  = MeasEvalAnnotationInstance.from_entries(entries=entries)
    # except Exception as e:
    #     print(e)  
    #     print(df)    
    #     print('---------------------------------------------------------------------------------------------------------------------------')
