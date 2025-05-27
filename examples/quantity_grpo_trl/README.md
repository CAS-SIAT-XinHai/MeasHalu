```shell
CUDA_VISIBLE_DEVICES=1,2,4,5 accelerate launch --num_processes 3 --config_file /home/huangruijun/grpo_trl/deepspeed_zero3.yaml run_grpo.py --config /home/huangruijun/grpo_trl/grpo.yaml
```

第一版代码写的有点乱，数据是写死在py文件里的