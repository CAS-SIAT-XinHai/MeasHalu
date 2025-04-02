# coding=utf-8
# Copyright (c) CAS-SIAT-XinHai.
# Licensed under the CC0-1.0 license.
#
# XinHai stands for [Sea of Minds].
#
# Authors: Vimos Tan


import numpy as np

current_global_count = 0


# 从文本中提取 XML 格式的答案
def extract_xml_answer(text: str) -> str:
    answer = text.split("<answer>")[-1]
    if answer.strip().endswith("</answer>"):
        answer = answer.split("</answer>")[0]
        return answer.strip()
    return ''


def extract_xml_reasoning(text: str) -> str:
    reasoning = text.split("<reasoning>")[-1]
    if "</reasoning>" in reasoning:
        reasoning = reasoning.split("</reasoning>")[0].strip()
        return reasoning
    return ''


def extract_xml_template(text: str) -> str:
    template = text.split("<template>")[-1]
    if "</template>" in template:
        template = template.split("</template>")[0].strip()
        return template
    return ''


def standardized_data(data: list[float]) -> list[float]:
    # 计算均值和标准差
    mean_val = np.mean(data)
    std_val = np.std(data)
    # 使用标准化公式
    standardized_data = [(x - mean_val) / std_val for x in data]
    return standardized_data


def normalized_data(data: list[float]) -> list[float]:
    # 计算最小值和最大值
    min_val = np.min(data)
    max_val = np.max(data)
    # 使用 Min-Max 归一化
    if max_val - min_val == 0:
        return [0.0 for i in range(len(data))]
    normalized_data = [(x - min_val) / (max_val - min_val) for x in data]
    return normalized_data


def scaled_data(data: list[float], min_target, max_target) -> list[float]:
    print(f"unscaled data = {data}")
    # 原数据的最小值和最大值
    min_val = min(data)
    max_val = max(data)
    if max_val - min_val == 0:
        return [0.0 for i in range(len(data))]
    # 线性变换
    scaled_data = [(x - min_val) / (max_val - min_val) * (max_target - min_target) + min_target for x in data]
    return scaled_data


def reward_score_baseline(base_score: float, reward_list: list[float]) -> list[float]:
    return [num - base_score for num in reward_list]


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


# 从文本中提取哈希格式的答案
def extract_hash_answer(text: str):
    if "####" not in text:
        return None
    return text.split("####")[1].strip()


# 250317: 借鉴open-r1重复惩罚分
def get_repetition_penalty_reward(prompts, completions, answer, **kwargs) -> list[float]:
    ngram_size = 3
    max_penalty = -1.0

    if max_penalty > 0:
        raise ValueError(f"max_penalty {max_penalty} should not be positive")

    def zipngram(text: str, ngram_size: int):
        words = text.lower().split()
        return zip(*[words[i:] for i in range(ngram_size)])

    contents = [completion[0]["content"] for completion in completions]
    rewards = []
    for completion in contents:
        if completion == "":
            rewards.append(0.0)
            continue
        if len(completion.split()) < ngram_size:
            rewards.append(0.0)
            continue

        ngrams = set()
        total = 0
        for ng in zipngram(completion, ngram_size):
            ngrams.add(ng)
            total += 1

        scaling = 1 - len(ngrams) / total
        reward = scaling * max_penalty
        rewards.append(reward)
    return rewards
