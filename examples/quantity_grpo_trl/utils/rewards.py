from .strict_format_check import strict_check
from .F1Quantity import eval_quantity
from .is_quantity import is_quantity
def extract_conclusion(text: str) -> str:
    answer = text.split("<CONCLUSION>")[-1]
    answer = answer.split("</CONCLUSION>")[0]
    # print(answer)
    return answer.strip()


def strict_format_reward_func(completions, **kwargs) -> list[float]:
    """Reward function that checks if the completion has a specific format."""
    responses = [completion for completion in completions]
    reward_list = [strict_check(r) for r in responses]
    print(f"strict_format_reward_func = {reward_list}")
    # reward_list = reward_score_baseline(1.5, reward_list)
    # print(f"strict_format_reward_func substract baseline = {reward_list}")
    return reward_list


# Reward functions
def quantities_reward_func(docId, completions, ans, **kwargs) -> list[float]:
    responses = [completion for completion in completions]
    # q = prompts[0][-1]['content']
    extracted_responses = [extract_conclusion(r) for r in responses]
    # print('-'*20, f"Question:\n{q}", f"\nAnswer:\n{answer[0]}", f"\nResponse:\n{responses[0]}", f"\nExtracted:\n{extracted_responses[0]}")
    reward_list = [eval_quantity(d,r,a) for d,r, a in zip(docId,extracted_responses, ans)]
    print(f"quantities_reward_func={reward_list}")
    return reward_list

def is_quantity_penalty_func(docId,completions, **kwargs) -> list[float]:
    responses = [completion for completion in completions]
    # print(responses[0])
    extracted_responses = [extract_conclusion(r) for r in responses]
    reward_list =  [is_quantity(d,r) for d,r in zip(docId,extracted_responses)]
    print(f"is_quantity_penalty_func = {reward_list}")
    return reward_list
