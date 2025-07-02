# sft训练（使用llamafactory，配置数据集info中的columns，prompt为'query',response为quantity_reasoning_process）：
```shell
CUDA_VISIBLE_DEVICES=2,3 FORCE_TORCHRUN=1 llamafactory-cli train /home/huangruijun/everything_curriculum/mp_sft.yaml
```
# grpo训练
```shell
python run_grpo.py
```


# 评测（生成tsv到MeasEval-main的data目录下,-s为submission目录，-g为答案目录）
```shell
python measeval-eval.py -i /home/huangruijun/MeasEval-main/data/ -s everything_many_grpo/ -g eval/tsv/
```