#!/usr/bin/env bash
# Waits for L3_TRAIN_DONE marker, then: ridgepass(8) -> ridgepick -> fullpass(8). Resumable.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"; NGPU="${NGPU:-8}"
echo "waiting for training to finish..."
until grep -q "L3_TRAIN_DONE" /tmp/l3train.log 2>/dev/null; do sleep 60; done
echo "train done ($(date +%H:%M)); starting eval"
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/eval_arms.py ridgepass --shard ${g}:${NGPU} > /tmp/l3ev_r_${g}.log 2>&1 &
done; wait
python3 loop3/eval_arms.py ridgepick || exit 1
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/eval_arms.py fullpass --shard ${g}:${NGPU} > /tmp/l3ev_f_${g}.log 2>&1 &
done; wait
echo "full files: $(ls loop3/eval/full_*.jsonl 2>/dev/null | wc -l)"
echo "L3_EVAL_DONE"
