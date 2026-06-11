from .strict_format_check import strict_check
from .F1Reward import eval_F1
from .penalty import penalty
from .sumReward import SumReward
import re
import json
import pandas as pd

# 读取文本数据
import os
valid_mods_keys = [
    'IsCount', 'IsApproximate', 'IsMeanHasTolerance', 'IsMedian',
    'IsList', 'IsRangeHasTolerance', 'IsMean', 'IsRange',
    'HasTolerance', 'IsMeanIsRange', 'IsMeanHasSD'
]
textpaths = [
    "/home/huangruijun/MeasEval-main/data/train/text/",
    "/home/huangruijun/MeasEval-main/data/trial/txt/"
]
textset = {}
docIds = []


# def strict_format_reward_func(completions, **kwargs) -> list[float]:
#     """Reward function that checks if the completion has a specific format."""
#     responses = [completion[0]["content"] for completion in completions]
#     reward_list = [strict_check(r) for r in responses]
#     print(f"strict_format_reward_func = {reward_list}")
#     # reward_list = reward_score_baseline(1.5, reward_list)
#     # print(f"strict_format_reward_func substract baseline = {reward_list}")
#     return reward_list


# Reward functions
def F1_reward_func(docId, completions, ans, **kwargs) -> list[float]:
    responses = [completion[0]['content'] for completion in completions]
    reward_list = [eval_F1(d,r,a) for d,r,a in zip(docId,responses, ans)]
    # print(responses[0])
    print(f"{docId[0]} quantities_reward_func={reward_list}")
    return reward_list


def get_penalty_func(docId,completions, **kwargs) -> list[float]:
    responses = [completion[0]["content"] for completion in completions]
    reward_list =  [penalty(d,r) for d,r in zip(docId,responses)]

    print(f"get_penalty_func = {reward_list}")
    return reward_list

def sum_reward_func(docId, completions, ans, **kwargs) -> list[float]:
    responses = [completion[0]['content'] for completion in completions]
    reward_list = [SumReward(d,r,a) for d,r,a in zip(docId,responses, ans)]
    print(f"{docId[0]} sum_reward_func={reward_list}")
    return reward_list