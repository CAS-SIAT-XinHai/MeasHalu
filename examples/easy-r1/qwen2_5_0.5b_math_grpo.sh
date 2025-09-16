#!/bin/bash
FILE_DIR=$(dirname $(readlink -f $0))
WORK_DIR=$(dirname $(dirname $FILE_DIR))
echo "${WORK_DIR}"
UUID=$(uuidgen)
echo "${UUID}"

set -x

export PYTHONUNBUFFERED=1

MODEL_PATH=Qwen/Qwen2.5-0.5B-Instruct  # replace it with your local file path

PYTHONPATH=${WORK_DIR}/src python3 -m verl.trainer.main \
    config=${FILE_DIR}/config.yaml \
    worker.actor.model.model_path=${MODEL_PATH} \
    trainer.experiment_name=qwen2_5_0.5b_math_grpo \
    trainer.n_gpus_per_node=1
