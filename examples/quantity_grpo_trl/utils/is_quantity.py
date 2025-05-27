from .utils import is_overlapping,update_row,textset
import pandas as pd
from io import StringIO
import re
from CQE import CQE
from quantulum3 import parser
cqe_parser = CQE.CQE()

def is_quantity(docId,input):
    '''
        无数字直接减一百，希望能惩罚非数字预测
    '''
    try:
        annot_df = pd.read_csv(StringIO(input),sep = '\t')
        text = textset[docId]
        used_ranges = []  # 保存所有已标记的区间
        quantity_counter = 1
        updated_rows = []
        found=False
        quantity_text = ""
        penalty=0.0
        for index, row in annot_df.iterrows():
            quantity_text = str(row.get('text', ''))
            found=False
            if row['annotType'] != 'Quantity':
                penalty-=5.0
            if re.fullmatch(r'T\d+', str(row.get('text', ''))):
                penalty-=5.0
            result_cqe = cqe_parser.parse(quantity_text)
            result_quantulum = parser.parse(quantity_text)
            if len(result_cqe) ==0 and len(result_quantulum) ==0:
                print(quantity_text)
                penalty-=100.0
            for match in re.finditer(re.escape(quantity_text), text):
                start = match.start()
                end = match.end()

                if not is_overlapping(start, end, used_ranges):
                    used_ranges.append((start, end))
                    updated_row = update_row(row, start, end, quantity_counter, docId)
                    updated_rows.append(updated_row)
                    quantity_counter += 1.0
                    found = True
                    break
            if not found:
                print(f"Quantity '{quantity_text}' not found without overlap in the text.")
                penalty-=1.0
        return penalty
    except:
        return -100