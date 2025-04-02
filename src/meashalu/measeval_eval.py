import re

import os
import re
import pandas as pd
from schemas.measeval_adapted import (  # 替换为你的模块路径
    MeasEvalAnnotationMeasurement,
    MeasEvalSetType,
    MeasEvalAnnotationIdType,
    MeasEvalOtherType,
    MeasEvalTextType,
    MeasEvalAnnotationInstance

)
def check_reasoning_measeval(text):          
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
    for index,row in df.iterrows():
    # print(MeasEvalOtherType(other = row['other']))
    # t = MeasEvalOtherType(other = row['other'])
    # print(t)
        try:
            instance = MeasEvalAnnotationMeasurement(
                    annotSet=MeasEvalSetType(annotSet = row['annotSet']),
                    annotType=row['annotType'],
                    annotId=MeasEvalAnnotationIdType(row['annotId']),
                    text=MeasEvalTextType(text=row['text']),
                    other=MeasEvalOtherType(other = row['other'])
                )            
            entries.append(instance)
        except Exception as e:
            raise ValueError(e)
    # try:
    #     t  = MeasEvalAnnotationInstance.from_entries(entries=entries)
    # except Exception as e:
    #     print(e)  
    #     print(df)    
    #     print('---------------------------------------------------------------------------------------------------------------------------')       


