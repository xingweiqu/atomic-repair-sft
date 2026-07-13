#!/bin/bash
# M1 model downloads (xet disabled: incompatible with HDFS FUSE; local disk first).
source ~/atomic_env.sh
export HF_HUB_DISABLE_XET=1
huggingface-cli download NousResearch/Meta-Llama-3.1-8B-Instruct --local-dir /opt/tiger/models_mm/Llama-3.1-8B-Instruct --exclude "original/*" > /tmp/dl_llama.log 2>&1 && echo DL_LLAMA_OK >> /tmp/dl.log || echo DL_LLAMA_FAIL >> /tmp/dl.log
huggingface-cli download Qwen/Qwen3-4B-Instruct-2507 --local-dir /opt/tiger/models_mm/Qwen3-4B-Instruct > /tmp/dl_qwen4b.log 2>&1 && echo DL_QWEN4B_OK >> /tmp/dl.log || echo DL_QWEN4B_FAIL >> /tmp/dl.log
cp -r /opt/tiger/models_mm /mnt/hdfs/xwqu/ >> /tmp/dl.log 2>&1 && echo HDFS_COPY_OK >> /tmp/dl.log
