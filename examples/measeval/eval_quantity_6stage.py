import requests
import re
import pandas as pd
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
from vladiate.validators import UniqueValidator, SetValidator, IntValidator, Validator, ValidationException, RegexValidator
import traceback
from io import StringIO
url = 'http://localhost:5000/generate'
docIds = []
textset = {}
textpaths = [
            "/home/huangruijun/MeasEval-main/data/eval/text/"]
valid_mods_keys = ['IsCount', 'IsApproximate', 'IsMeanHasTolerance', 'IsMedian',
                   'IsList', 'IsRangeHasTolerance', 'IsMean', 'IsRange',
                   'HasTolerance', 'IsMeanIsRange', 'IsMeanHasSD']

for fileset in textpaths:
    for fn in os.listdir(fileset):
        with open(fileset + fn) as textfile:
            text = textfile.read() #.splitlines()
            #print(fn[:-4])
            textset[fn[:-4]] = text
            docIds.append(fn[:-4])

def update_row(row, start_offset, end_offset,quantityCount,docId):
    # 创建新的字典，将 'startOffset' 和 'endOffset' 插入到 'annotType' 后面
    return {
        'docId': docId,
        'annotSet': quantityCount,
        'annotType': row['annotType'],
        'startOffset': start_offset,
        'endOffset': end_offset,
        'annotId': 'T'+str(quantityCount),
        'text': row['text'],
        'other': None
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

def is_overlapping(start, end, ranges):
    """检查 (start, end) 是否与已有 ranges 有重叠"""
    return any(not (end <= r_start or start >= r_end) for r_start, r_end in ranges)
def fetch_annotations(docId,text: str, max_retries: int = 3) -> pd.DataFrame:
    """
    向 LLM 服务发一次请求，解析返回内容，生成 DataFrame
    """
    cnt = 5
    while cnt>0:
        try:
            for _ in range(max_retries):
                data = {
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user",   "content": f"please help me extract all of the Quantities.\n\nInput:\n{text}"}
                    ]
                }
                resp = requests.post(url, json=data).json().get('response', '')
                m = re.search(r'<CONCLUSION>(.*?)</CONCLUSION>', resp, re.DOTALL).group(1)
                if not m:
                    continue
                
                annot_df = pd.read_csv(StringIO(m),sep='\t')
                # print(annot_df)
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
                print(updated_df)
                return updated_df
        except Exception as e:
            traceback.print_exc()
            print(cnt)
            print("--------------------")
            cnt -=1
    # 如果多次都没拿到结果，返回空表
    return pd.DataFrame(columns=['docId','annotSet',	'annotType',	'startOffset'	,'endOffset',	'annotId'	,'text',	'other'])


def merge_and_dedupe(dfs: list[pd.DataFrame], text: str) -> pd.DataFrame:
    """
    1) 合并所有 df，去重（不考虑 other 字段，只按 annotType, text, startOffset, endOffset）；
    2) 按 startOffset 排序，任意两段只要有重叠就合并；
    3) 按 startOffset 排序，重新生成 annotSet 和 annotId。
    """
    # Step 1: 重新定位所有 span 的 startOffset 和 endOffset
    full = pd.concat(dfs, ignore_index=True)
    print(type(full))
    # full = dfs
    if full.empty:
        return pd.DataFrame(columns=['docId','annotSet',	'annotType',	'startOffset'	,'endOffset',	'annotId'	,'text',	'other'])

    # Step 2: 去重（忽略 other 字段）
    full = full.sort_values(["startOffset", "endOffset"]).reset_index(drop=True)

    full = full.drop_duplicates(
        subset=["annotType", "text", "startOffset", "endOffset"],
        keep="first"
    ).reset_index(drop=True)
    # Step 3: 合并所有有重叠的区间
    merged = []
    cur = full.iloc[0].to_dict()
    for row in full.iloc[1:].to_dict(orient="records"):
        # 判断两个区间是否有重叠
        if not (cur["endOffset"] < row["startOffset"] or row["endOffset"] < cur["startOffset"]):
            # 有重叠，合并
            cur["startOffset"] = min(cur["startOffset"], row["startOffset"])
            cur["endOffset"] = max(cur["endOffset"], row["endOffset"])
            cur["text"] = text[cur["startOffset"]:cur["endOffset"]]
        else:
            # 没重叠，推入 merged 列表
            merged.append(cur)
            cur = row
    merged.append(cur)

    # Step 4: 重新生成 annotSet 和 annotId
    out = pd.DataFrame(merged)
    out = out.sort_values("startOffset").reset_index(drop=True)
    out["annotSet"] = out.index + 1
    out["annotId"] = out["annotSet"].apply(lambda i: f"T{i}")

    return out[['docId','annotSet',	'annotType',	'startOffset'	,'endOffset',	'annotId'	,'text',	'other']]

# —— 主循环 —— #
for docId, text in textset.items():
    # 并发调用 6 次
    # docId="S0022000014000026-12523"
    print(docId)
    with ThreadPoolExecutor(max_workers=6) as exe:
        futures = [exe.submit(fetch_annotations, docId,text) for _ in range(6)]
        dfs = [f.result() for f in as_completed(futures)]

    # 合并、去重、合并重叠，重排编号
    merged_df = merge_and_dedupe(dfs, text)

    merged_df.to_csv(f"../MeasEval-main/data/qwen_6stage_grpo/{docId}.tsv",sep='\t',index=False)
