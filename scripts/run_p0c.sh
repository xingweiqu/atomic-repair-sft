#!/bin/bash
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
git fetch -q origin prescription-v1 && git checkout -q prescription-v1 && git reset --hard -q origin/prescription-v1
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 prescription/p0c_eval.py gen --shard $g:8 >> /tmp/p0c_$g.log 2>&1 &
done
wait
python3 prescription/p0c_eval.py score > /tmp/p0c_score.log 2>&1
tail -2 /tmp/p0c_score.log
echo "P0C_DONE"
