#!/bin/bash
# B2-0(b) genre reconciliation: 14 ridge ckpts x repair_eval 480, 8-GPU sharded.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/genre_eval.py gen --shard $g:8 \
    >> /tmp/b20b_$g.log 2>&1 &
done
wait
n=$(ls loop3/eval/genre/pred_l3_*.jsonl 2>/dev/null | wc -l)
echo "B20B_GEN_DONE preds=$n"
if [ "$n" -lt 14 ]; then echo "B20B_FAIL yield $n/14"; exit 1; fi
