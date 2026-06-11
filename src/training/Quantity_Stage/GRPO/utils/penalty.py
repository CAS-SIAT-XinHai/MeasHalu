from .utils import is_overlapping,update_row,textset
import pandas as pd
from io import StringIO
import re
from CQE import CQE
from quantulum3 import parser
cqe_parser = CQE.CQE()
import re
from datetime import datetime
import traceback
def is_year_reference(text, start, end, window=15):
    current_year = datetime.now().year
    number_str = text[start:end]
    
    # 1. 判断是否是年份格式（4位数字且合理）
    if not (number_str.isdigit() and 1800 <= int(number_str) <= current_year + 2):
        return False
    # 2. 获取上下文
    left_context = text[max(0, start - window):start]
    right_context = text[end:min(len(text), end + window)]
    context = (left_context + number_str + right_context)
    # 3. 是否是括号中仅包含年份
    bracket_only_pattern = r"\(\s*{}\s*\)".format(number_str)
    if re.search(bracket_only_pattern, context):
        print(context)
        return -100.0

    reference_pattern = r"\(\s*[^()]+?,\s*{}\s*\).format(number_str)"
    if re.search(reference_pattern,context):
        print(context)
        return -100.0
    
    return 0.0

def check_structure_reference(text, start, end, number_str, window=15):
    context_start = max(0, start - window)
    context_end = min(len(text), end + window)
    context = text[context_start:context_end].lower()

    patterns = [
        (r"\bfig(?:ure)?\.?\s*{}\b".format(number_str), "figure"),
        (r"\bsec(?:tion)?\.?\s*{}\b".format(number_str), "section"),
        (r"\bline\s*{}\b".format(number_str), "line"),
        (r"\btab(?:le)?\.?\s*{}\b".format(number_str), "table"),
        (r"\bapp(?:endix)?\.?\s*{}\b".format(number_str), "appendix"),
        (r"\balg(?:orithm)?\.?\s*{}\b".format(number_str), "algorithm"),
        (r"\bpara(?:graph)?\.?\s*{}\b".format(number_str), "paragraph"),
        (r"\bp(?:age)?\.?\s*{}\b".format(number_str), "page"),
        (r"\b(item|step)\s*{}\b".format(number_str), "item_or_step"),
    ]

    for pattern, label in patterns:
        for match in re.finditer(pattern, context):
            match_start = context_start + match.start()
            match_end = context_start + match.end()
            if match_start <= start and match_end >= end:
                print(f"{label} match:", match.group())
                return -100.0

    return 0.0


def penalty(docId,input):
    '''
        判断是否为年份以及figure. 2 这种的惩罚
    '''
    try:
        annot_df = pd.read_csv(StringIO(input),sep = '\t')
        text = textset[docId]
        used_ranges = []  # 保存所有已标记的区间
        quantity_counter = 1
        updated_rows = []
        found=False
        quantity_text = ""
        for index, row in annot_df.iterrows():
            quantity_text = str(row.get('text', ''))
            found=False

            if row['annotType'] != 'Quantity':
                raise ValueError(f"Invalid annotType: {row['annotType']} (Only 'Quantity' allowed)")

            if re.fullmatch(r'T\d+', str(row.get('text', ''))):
                raise ValueError(f"Invalid text label: {row['text']} (T-labels like T1, T2 not allowed)")
            
            if re.fullmatch(r'\d+S',str(row.get('text',''))):
                penalty -= 100

            for match in re.finditer(re.escape(quantity_text), text):
                start = match.start()
                end = match.end()
                if not is_overlapping(start, end, used_ranges):
                    used_ranges.append((start, end))
                    updated_row = update_row(row, start, end, quantity_counter, docId)
                    updated_rows.append(updated_row)
                    quantity_counter += 1
                    found = True
                    break
            if not found:
                print(f"Quantity '{quantity_text}' not found without overlap in the text.")
        # 将更新后的数据写入新的 TSV 文件
        updated_df = pd.DataFrame(updated_rows)
        penalty = 0
        for index,row in updated_df.iterrows():
            penalty += is_year_reference(text,row["startOffset"],row["endOffset"])
            penalty += check_structure_reference(text,row["startOffset"],row["endOffset"],row["text"])
        return penalty
    except:
        traceback.print_exc()
        return -100