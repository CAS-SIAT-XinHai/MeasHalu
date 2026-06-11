
from unsloth import FastLanguageModel, PatchFastRL
import os
import json
PatchFastRL("GRPO", FastLanguageModel)

from unsloth import is_bfloat16_supported
import torch
from utils.rewards import strict_format_reward_func,quantities_reward_func,is_quantity_penalty_func,other_penalty_func
max_seq_length = 8196 # Can increase for longer reasoning traces
lora_rank = 32 # Larger rank = smarter, but slower
model, tokenizer = FastLanguageModel.from_pretrained(
    model_name = "/home/huangruijun/LLaMA-Factory/saves/qwen2-7b-instruct/lora_merge/6stage_meas_50step",
    max_seq_length = max_seq_length,
    load_in_4bit = True, # False for LoRA 16bit
    fast_inference = True, # Enable vLLM fast inference
    max_lora_rank = lora_rank,
    gpu_memory_utilization = 0.6, # Reduce if out of memory
)

model = FastLanguageModel.get_peft_model(
    model,
    r = lora_rank, # Choose any number > 0 ! Suggested 8, 16, 32, 64, 128
    target_modules = [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj",
    ], # Remove QKVO if out of memory
    lora_alpha = lora_rank,
    use_gradient_checkpointing = "unsloth", # Enable long context finetuning
    random_state = 3407,
)

import re
from datasets import load_dataset, Dataset

# Load and prep dataset
SYSTEM_PROMPT = """
You are a helpful assistant in quantity extraction.Please extract all the quantities,and follow the format below:
"""


# uncomment middle messages for 1-shot prompting
# uncomment middle messages for 1-shot prompting
def get_measdata(jsonl_path) -> Dataset:
    data = []
    with open(jsonl_path, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line.strip())
            data.append({
                "docId" : item["docId"],
                "prompt": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": item["query"]}
                ],
                "ans": item["ans"]
            })
    return Dataset.from_list(data)

dataset = get_measdata("/home/huangruijun/grpo_unsloth_2/data/quantity_grpo.jsonl")


from trl import GRPOConfig, GRPOTrainer
training_args = GRPOConfig(
    use_vllm = True, # use vLLM for fast inference!
    learning_rate = 5e-6,
    adam_beta1 = 0.9,
    adam_beta2 = 0.99,
    weight_decay = 0.1,
    warmup_ratio = 0.1,
    lr_scheduler_type = "cosine",
    optim = "paged_adamw_8bit",
    logging_steps = 1,
    bf16 = is_bfloat16_supported(),
    fp16 = not is_bfloat16_supported(),
    per_device_train_batch_size = 1,
    gradient_accumulation_steps = 1, # Increase to 4 for smoother training
    num_generations = 6, # Decrease if out of memory
    max_prompt_length = 2000,
    max_completion_length = 4096,
    num_train_epochs = 200, # Set to 1 for a full training run
    max_steps = 16000,
    save_steps = 500,
    max_grad_norm = 0.1,
    report_to = "none", # Can use Weights & Biases
    output_dir = "test_7b",
)

trainer = GRPOTrainer(
    model = model,
    processing_class = tokenizer,
    reward_funcs = [
        strict_format_reward_func,
        quantities_reward_func,
        is_quantity_penalty_func,
        other_penalty_func
    ],
    args = training_args,
    train_dataset = dataset,
)
trainer.train(resume_from_checkpoint=True)

model.save_lora("grpo_saved_lora")