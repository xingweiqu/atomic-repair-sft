#!/bin/bash
# Batch-2 dose-curve training: 24 configs, each run exclusive on 8 GPUs (Batch-1 protocol).
# Then chains ridgepass(8-shard) -> ridgepick -> fullpass(8-shard) -> genre gen(8-shard).
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
for cfg in configs/loop3_b2/l3_*_sft.yaml; do
  tag=$(basename "$cfg" _sft.yaml)
  if [ -f "/mnt/hdfs/xwqu/loop3/output/$tag/config.json" ]; then echo "OK $tag (skip)"; continue; fi
  if llamafactory-cli train "$cfg" > "/tmp/b2_$tag.log" 2>&1; then
    echo "OK $tag"
  else
    echo "FAIL $tag"
  fi
done
echo "B2_TRAIN_DONE"
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/eval_arms.py ridgepass --shard $g:8 >> /tmp/b2eval_$g.log 2>&1 &
done
wait
python3 loop3/eval_arms.py ridgepick
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/eval_arms.py fullpass --shard $g:8 >> /tmp/b2eval_$g.log 2>&1 &
done
wait
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/genre_eval.py gen --shard $g:8 >> /tmp/b2genre_$g.log 2>&1 &
done
wait
echo "B2_EVAL_DONE"
