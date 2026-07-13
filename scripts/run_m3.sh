#!/bin/bash
# M3: Llama steering — extract(8-shard) -> scan(1 GPU) -> full(8-shard) -> score.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/m3_steer.py extract --shard $g:8 >> /tmp/m3_ext_$g.log 2>&1 &
done
wait
CUDA_VISIBLE_DEVICES=0 python3 loop3/m3_steer.py scan > /tmp/m3_scan.log 2>&1 || { echo "M3_SCAN_FAIL"; exit 1; }
tail -2 /tmp/m3_scan.log
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/m3_steer.py full --shard $g:8 >> /tmp/m3_full_$g.log 2>&1 &
done
wait
python3 loop3/m3_steer.py score > /tmp/m3_score.log 2>&1
echo "M3_DONE"
