import os
# Set pysqldf to keep global scope
docIds = []
textset = {}
textpaths = [
            "/home/huangruijun/MeasEval-main/data/eval/text/",
            "/home/huangruijun/MeasEval-main/data/train/text/",
            "/home/huangruijun/MeasEval-main/data/trial/txt/"]

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
