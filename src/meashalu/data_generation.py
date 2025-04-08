import pandas as pd
import json
import pandas as pd
from quantulum3 import parser
from tqdm.auto import tqdm
import swifter
from pandarallel import pandarallel

def read_jsonlines_to_df(file_path):
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            for line in file:
                try:
                    json_obj = json.loads(line.strip())
                    data.append(json_obj)
                except json.JSONDecodeError:
                    print(f"Failed to decode line: {line}")
        df = pd.DataFrame(data)
        return df
    except FileNotFoundError:
        print("错误: 文件未找到!")
    except Exception as e:
        print(f"错误: 发生了一个未知错误: {e}")

file_path = 'dataset_todo/arxiv-dataset/train.txt'
df = read_jsonlines_to_df(file_path)
if df is not None:
    print("数据已成功读取到 DataFrame:")
def clean_and_merge(sentences):
    return ''.join([sentence.replace('<S>', '').replace('</S>', '').strip() for sentence in sentences])

tmp = clean_and_merge(df.iloc[0]['abstract_text'])


# 为 pandas 的 apply 方法添加进度条
tqdm.pandas()

def clean_and_merge(sentences):
    return ''.join([sentence.replace('<S>', '').replace('</S>', '').strip() for sentence in sentences])

# 指定分区数量，通常可以设置为 CPU 核心数

# 对 abstract_text 列应用 clean_and_merge 函数并显示进度条
df['abstract_text'] = df['abstract_text'].progress_apply(clean_and_merge)


# 初始化并行处理（会自动显示进度条）
pandarallel.initialize(progress_bar=True, nb_workers=64)

# 筛选出 abstract_text 中不包含 @ 的行
df = df[~df['abstract_text'].parallel_apply(lambda x: '@' in x)]
df['parsed_result'] = df['abstract_text'].parallel_apply(parser.parse)
df = df[df['parsed_result'].parallel_apply(lambda x: len(x) >= 1)]

file_path = 'datas.jsonl'
try:
    with open(file_path, 'w', encoding='utf-8') as f:
        for _, row in df.iterrows():
            data = {
                'article_id': row['article_id'],
                'abstract_text': row['abstract_text'],
                'parsed_result': str(row['parsed_result'])
            }
            json_line = json.dumps(data, ensure_ascii=False)
            f.write(json_line + '\n')
    print(f"数据已成功保存到 {file_path}")
except Exception as e:
    print(f"保存数据时出现错误: {e}")
