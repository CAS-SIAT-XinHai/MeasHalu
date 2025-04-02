# coding=utf-8
# Copyright (c) CAS-SIAT-XinHai.
# Licensed under the CC0-1.0 license.
#
# XinHai stands for [Sea of Minds].
#
# Authors: Vimos Tan


import re

import numpy as np

from .utils import extract_xml_answer, extract_xml_reasoning, extract_xml_template, sigmoid, scaled_data


def is_independent_number(any_str: str, ground_truth: str) -> bool:
    # 检查是否为纯数字字符串
    if not ground_truth.isdigit():
        return False
    # 构造正则表达式模式
    pattern = r'(?<!\d)' + re.escape(ground_truth) + r'(?!\d)'
    # 使用正则表达式查找
    match = re.search(pattern, any_str)
    return match is not None


def correctness_reward_func(prompts, completions, answer, **kwargs) -> list[float]:
    responses = [completion[0]['content'] for completion in completions]
    q = prompts[0][-1]['content']
    extracted_responses = [extract_xml_answer(r) for r in responses]
    print('-' * 20, f"Question:\n{q}", f"\nAnswer:\n{answer[0]}", f"\nResponse:\n{responses[0]}",
          f"\nExtracted:\n{extracted_responses[0]}")
    reward_list = [5 if is_independent_number(r, a) else 0.0 for r, a in zip(extracted_responses, answer)]
    print(f"correctness_reward_func = {reward_list}")
    # reward_list = reward_score_baseline(1.5, reward_list)
    # print(f"correctness_reward_func substract baseline = {reward_list}")
    return reward_list


def int_reward_func(completions, **kwargs) -> list[float]:
    responses = [completion[0]['content'] for completion in completions]
    extracted_responses = [extract_xml_answer(r) for r in responses]
    reward_list = [3 if r.isdigit() else 0.0 for r in extracted_responses]
    print(f"int_reward_func = {reward_list}")
    # reward_list = reward_score_baseline(1.5, reward_list)
    # print(f"int_reward_func substract baseline = {reward_list}")
    return reward_list


def strict_format_reward_func(completions, **kwargs) -> list[float]:
    """Reward function that checks if the completion has a specific format."""
    responses = [completion[0]["content"] for completion in completions]
    pattern = r"^<template>\n[\s\S]*\n</template>\n<reasoning>\n[\s\S]*?\n</reasoning>\n<answer>\n[\s\S]*?\n</answer>$"
    matches = [re.match(pattern, r) for r in responses]
    reward_list = [1 if match else 0.0 for match in matches]
    print(f"strict_format_reward_func = {reward_list}")
    # reward_list = reward_score_baseline(1.5, reward_list)
    # print(f"strict_format_reward_func substract baseline = {reward_list}")
    return reward_list


def soft_format_reward_func(completions, **kwargs) -> list[float]:
    """Reward function that checks if the completion has a specific format."""
    responses = [completion[0]["content"] for completion in completions]
    pattern = r"<template>[\s\S]*?</template>\s*<reasoning>[\s\S]*?</reasoning>\s*<answer>[\s\S]*?</answer>"
    matches = [re.match(pattern, r) for r in responses]
    reward_list = [3 if match else 0.0 for match in matches]
    print(f"soft_format_reward_func = {reward_list}")
    # reward_list = reward_score_baseline(1.5, reward_list)
    # print(f"soft_format_reward_func substract baseline = {reward_list}")
    return reward_list


def count_xml(text) -> float:
    count = 0.0
    if text.count("<template>\n") == 1:
        count += 0.1667
    if text.count("\n</template>\n") == 1:
        count += 0.16666
    if text.count("<reasoning>\n") == 1:
        count += 0.16666
    if text.count("\n</reasoning>\n") == 1:
        count += 0.16666
    if text.count("\n<answer>\n") == 1:
        count += 0.16666
        count -= len(text.split("\n</answer>\n")[-1]) * 0.001
    if text.count("\n</answer>") == 1:
        count += 0.16666
        count -= (len(text.split("\n</answer>")[-1]) - 1) * 0.001
    return count


def xmlcount_reward_func(completions, **kwargs) -> list[float]:
    contents = [completion[0]["content"] for completion in completions]
    reward_list = [count_xml(c) for c in contents]
    print(f"xmlcount_reward_func = {reward_list}")
    # reward_list = reward_score_baseline(1.5, reward_list)
    # print(f"xmlcount_reward_func substract baseline = {reward_list}")
    return reward_list


# 我自己写的奖励函数, 线性变化不使用sigmoid, 但过于简单,且效果不咋地
def template_and_answer_reward_func_v4(prompts, completions, answer, **kwargs) -> list[float]:
    global current_global_count
    current_global_count += 1
    # 正确性分数
    responses = [completion[0]['content'] for completion in completions]
    extracted_responses = [extract_xml_answer(r) for r in responses]
    correct_reward_list = [1.5 if is_independent_number(r, a) else 0.0 for r, a in zip(extracted_responses, answer)]

    # reasoning长度分数
    extracted_reasonings = [extract_xml_reasoning(r) for r in responses]
    reasoning_length_reward_list = [len(reasoning_item) for reasoning_item in extracted_reasonings]
    max_val = np.max(reasoning_length_reward_list)
    new_arr = []
    # 每一值都减去数组的最大值，然后取绝对值，如此一来原本越大的就越小，越小的就越大
    for num in reasoning_length_reward_list:
        num -= max_val
        num = abs(num)
        new_arr.append(num)
    scaled_reasoning_length_reward_list = scaled_data(new_arr, 0.0, 1.5)

    # 答案正确的前提下越短分越高, 答案一错直接 0 分
    reward_list = [a + b if a > 0.0 else 0 for a, b in zip(correct_reward_list, scaled_reasoning_length_reward_list)]
    print(
        f"correct_reward_list = {correct_reward_list}, reasoning_length_reward_list = {reasoning_length_reward_list}， new_arr={new_arr}, scaled_reasoning_length_reward_list = {scaled_reasoning_length_reward_list}, template_reward_func = {reward_list}")
    # reward_list = reward_score_baseline(1.5, template_reward_func_reward)
    # print(f"template_reward_func substract baseline = {reward_list}")
    print(f"当前已经到了第{current_global_count}条")
    return reward_list


# 250301: 借鉴https://arxiv.org/abs/2502.04463的实现方式, 引入 sigmoid,先做非线性变化,再通过线性变化映射到 0~3 区间
def template_and_answer_reward_func(prompts, completions, answer, **kwargs) -> list[float]:
    global current_global_count
    # 正确性分数
    responses = [completion[0]['content'] for completion in completions]
    extracted_responses = [extract_xml_answer(r) for r in responses]
    correct_reward_list = [1 if is_independent_number(r, a) else 0.0 for r, a in zip(extracted_responses, answer)]

    # reasoning长度分数
    extracted_reasonings = [extract_xml_reasoning(r) for r in responses]
    response_len = [len(reasoning_item) for reasoning_item in extracted_reasonings]

    alpha = 0.1
    unscaled_reward_list = []
    for accuracy, response_i in zip(correct_reward_list, response_len):
        # 为了避免除零错误。如果有某个问题的长度标准差非常小（比如接近零），那么直接除以 np.std(lens) 可能会导致分母为零的情况，或者分母非常小而导致数值不稳定的巨大值。通过加上一个很小的数（1e-7，也就是 10−7），可以避免这种情况，同时在数学上对结果的影响几乎可以忽略不计。
        new_length = (response_i - np.mean(response_len)) / (np.std(response_len) + 1e-7)
        len_reward = accuracy * (1 - alpha * (sigmoid(new_length)))
        unscaled_reward_list.append(len_reward)
    # 待改成乘以 3
    # reward_list = scaled_data(unscaled_reward_list, 0.0, 3.0)
    # reward_list = [x * 3 for x in unscaled_reward_list]

    print(
        f"correct_reward_list = {correct_reward_list}, reasoning_length_reward_list = {response_len}, unscaled_reward_list = {unscaled_reward_list}")
    # reward_list = reward_score_baseline(1.5, template_reward_func_reward)
    # print(f"template_reward_func substract baseline = {reward_list}")
    print(f"当前已经到了第{current_global_count}条")
    return unscaled_reward_list


# 250310: 借鉴https://arxiv.org/abs/2503.04697,引入 alpha 参数和目标长度,目标长度=len(template)*alpha从而训练一个 template 长度和 reasoning 长度之间有某种对应关系的 rl 模型
def template_and_reasoning_reward_func(prompts, completions, answer, **kwargs) -> list[float]:
    global current_global_count
    current_global_count += 1

    def reverse_data_private(reward_list: list):
        max_val = np.max(reward_list)
        new_reward_list = [abs(i - max_val) for i in reward_list]
        return new_reward_list

    responses = [completion[0]['content'] for completion in completions]

    # reasoning长度分数
    extracted_reasonings = [extract_xml_reasoning(r) for r in responses]
    reasoning_len = [len(reasoning_item) for reasoning_item in extracted_reasonings]

    # template长度分数
    extracted_templates = [extract_xml_template(r) for r in responses]
    template_len = [len(template_item) for template_item in extracted_templates]

    alpha = 0.9
    beta = 1
    unscaled_reward_list = []

    epos_length = 0.1 * np.mean(template_len)
    for reasoning_i, template_i in zip(reasoning_len, template_len):
        target_length = alpha * reasoning_i + (1 - alpha) * (np.mean(template_len) + beta * template_i)
        len_reward = abs(reasoning_i - target_length)
        unscaled_reward_list.append(len_reward)

    epos_length_pos = []
    for index, value in enumerate(unscaled_reward_list):
        if value <= epos_length:
            epos_length_pos.append(index)

    reward_list = scaled_data(reverse_data_private(unscaled_reward_list), 0.0, 0.5)
    for index, value in enumerate(reward_list):
        if index in epos_length_pos:
            reward_list[index] = 1

    print(f"unscaled_reward_list = {unscaled_reward_list}, template_and_reasoning_reward_func = {reward_list}")
    # reward_list = reward_score_baseline(1.5, template_reward_func_reward)
    # print(f"template_reward_func substract baseline = {reward_list}")
    print(f"当前已经到了第{current_global_count}条")
    return reward_list


# 250314: 借鉴open-r1分点步骤分
def reasoning_steps_reward(prompts, completions, answer, **kwargs) -> list[float]:
    pattern = r"(步骤 \d+:|^\d+\.|\n-|\n\*|首先|其次|接着|然后|最后)"
    completion_contents = [completion[0]["content"] for completion in completions]
    matches = [len(re.findall(pattern, content)) for content in completion_contents]
    return [min(1.0, count / 3) for count in matches]
