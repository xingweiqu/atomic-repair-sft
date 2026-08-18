#!/bin/bash
# Base atomic profile for one model on one GPU: behavioral (vllm) + loss extraction (HF).
# Usage: base_profile.sh <model_path> <tag> <gpu_id>
set -u
MODEL=$1; TAG=$2; GPU=$3
source ~/atomic_env.sh
REPO=/opt/tiger/atomic-repair-sft-github
VX=$REPO/experiments/vnext_atomic_scaling_2026-08-18
EV=$REPO/prescription/gate1/eval500_proto.jsonl
OUT=/mnt/hdfs/xwqu/vnext0818/profiles/$TAG
mkdir -p $OUT
[ -f $OUT/DONE ] && { echo "skip $TAG"; exit 0; }
cd $REPO
export CUDA_VISIBLE_DEVICES=$GPU
export VLLM_WORKER_MULTIPROC_METHOD=spawn
if [ ! -f $OUT/pred.jsonl ]; then
  python3 $VX/code/gen_predict_vnext.py $EV $OUT/pred.jsonl $MODEL 8192 1 > $OUT/gen_log.txt 2>&1 || { echo "GEN_FAIL $TAG"; exit 1; }
fi
python3 prescription/lawv1_score.py --eval $EV --pred $OUT/pred.jsonl --out $OUT/score > $OUT/score_log.txt 2>&1 || { echo "SCORE_FAIL $TAG"; exit 1; }
if [ ! -f $OUT/loss.jsonl ]; then
  python3 $VX/code/loss_extract.py $EV $MODEL $OUT/loss.jsonl > $OUT/loss_log.txt 2>&1 || { echo "LOSS_FAIL $TAG"; exit 1; }
fi
touch $OUT/DONE
echo "PROFILE_DONE $TAG"
