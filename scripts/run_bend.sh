#!/bin/bash
# Bendpoint G/B race: 4 x 16-epoch trains (per-epoch ckpts) then race eval 8-shard.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
for cfg in configs/bend/*_sft.yaml; do
  tag=$(basename "$cfg" _sft.yaml)
  if ls /mnt/hdfs/xwqu/bend/output/$tag/checkpoint-* >/dev/null 2>&1; then echo "OK $tag (skip)"; continue; fi
  if llamafactory-cli train "$cfg" > "/tmp/bend_$tag.log" 2>&1; then echo "OK $tag"; else echo "FAIL $tag"; fi
done
echo "BEND_TRAIN_DONE"
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 learnability_family/race_eval.py gen --shard $g:8 >> /tmp/bendrace_$g.log 2>&1 &
done
wait
python3 learnability_family/race_eval.py collect
echo "BEND_EVAL_DONE"
