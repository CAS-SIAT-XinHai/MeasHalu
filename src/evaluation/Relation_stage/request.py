import unsloth
from vllm import SamplingParams
from unsloth import FastLanguageModel, PatchFastRL
from flask import Flask, request, jsonify
app = Flask(__name__)

max_seq_length = 8196 # Can increase for longer reasoning traces
lora_rank = 32 # Larger rank = smarter, but slower
model, tokenizer = FastLanguageModel.from_pretrained(
    # model_name = "/home/huangruijun/LLaMA-Factory/saves/qwen2-3b-instruct/full/sentence_quantBase_quant/checkpoint-100",
    # model_name="/home/huangruijun/LLaMA-Factory/saves/qwen2-7b-instruct/full/test_grpo_2_3/checkpoint-100",
    # model_name="/home/huangruijun/LLaMA-Factory/saves/qwen2-7b-instruct/full/reasoning_test",
    model_name="/home/huangruijun/grpo_onlygrpo2_agent2_lowcalcpenalty/outputs_quantity_penalty/lora_merge/5500step",
    max_seq_length = max_seq_length,
    load_in_4bit = True, # False for LoRA 16bit
    fast_inference = True, # Enable vLLM fast inference
    max_lora_rank = lora_rank,
    gpu_memory_utilization = 0.98, # Reduce if out of memory
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
SYSTEM_PROMPT = """
You are a helpful assistant.
"""

@app.route('/generate',methods=['POST'])
def generate():
    data = request.get_json()
    messages = data.get('messages')
    text = tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

    sampling_params = SamplingParams(
        temperature = 0.8,
        top_p = 0.95,
        max_tokens = 4096,
    )
    output = model.fast_generate(
        text,
        sampling_params = sampling_params,
        # lora_request = model.load_lora("/home/huangruijun/grpo_onlygrpo2_agent2_lowcalcpenalty/outputs_quantity_penalty/checkpoint-3750"),
    )[0].outputs[0].text
    return jsonify({"response":output})
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, threaded=False)