import os
# Set pysqldf to keep global scope
docIds = []
textset = {}
textpaths = [
            "/home/huangruijun/MeasEval-main/data/eval/text/",
            "/home/huangruijun/MeasEval-main/data/train/text/",
            "/home/huangruijun/MeasEval-main/data/trial/txt/"]
valid_mods_keys = [
    'IsCount', 'IsApproximate', 'IsMeanHasTolerance', 'IsMedian',
    'IsList', 'IsRangeHasTolerance', 'IsMean', 'IsRange',
    'HasTolerance', 'IsMeanIsRange', 'IsMeanHasSD'
]
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
def is_overlapping(start, end, ranges):
    """检查 (start, end) 是否与已有 ranges 有重叠"""
    return any(not (end <= r_start or start >= r_end) for r_start, r_end in ranges)

# --- 辅助函数 ---
def find_all_occurrences(text, sub):
    """在一个给定的文本（比如小段落）中，找到一个子串所有出现的起始位置。"""
    if not sub: return []
    start = 0
    indices = []
    while True:
        start = text.find(sub, start)
        if start == -1: return indices
        indices.append(start)
        start += 1

def find_context_robustly(full_text, context_from_llm, min_words=5):
    """
    一个健壮的、分三步尝试寻找上下文的函数。
    """
    # 尝试 1: 精确匹配
    offset = full_text.find(context_from_llm)
    if offset != -1:
        # print("[信息] 通过精确匹配成功定位上下文！")
        return offset, context_from_llm

    # 尝试 2: 标准化所有空白符（包括换行符）后再次匹配
    cleaned_context = " ".join(context_from_llm.split())
    offset = full_text.find(cleaned_context)
    if offset != -1:
        print("[信息] 通过空白符标准化成功定位上下文！")
        return offset, cleaned_context
    
    # # 尝试 3: 逐步缩短标准化的上下文，应对LLM引用不完整句子的情况
    # words = cleaned_context.split()
    # for i in range(1, len(words)):
    #     # 每次尝试都从末尾去掉一个词
    #     num_words_to_use = len(words) - i
    #     if num_words_to_use < min_words:
    #         # 如果段落变得太短，就没有查找的意义了，停止尝试
    #         break
        
    #     shorter_context = " ".join(words[:num_words_to_use])
    #     offset = full_text.find(shorter_context)
    #     if offset != -1:
    #         print(f"[信息] 通过缩短至 {num_words_to_use} 个词成功定位上下文！")
    #         return offset, shorter_context

    # 如果所有尝试都失败了
    return -1, None