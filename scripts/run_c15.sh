#!/bin/bash
# C-15: E-15a 24 seed-replication trains -> eval chain; then E-15c alpha scan; then E-15b scan2.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
export FORCE_TORCHRUN=1 NPROC_PER_NODE=8
for cfg in configs/loop3_c15/l3_*_sft.yaml; do
  tag=$(basename "$cfg" _sft.yaml)
  if [ -f "/mnt/hdfs/xwqu/loop3/output/$tag/config.json" ]; then echo "OK $tag (skip)"; continue; fi
  if llamafactory-cli train "$cfg" > "/tmp/c15_$tag.log" 2>&1; then echo "OK $tag"; else echo "FAIL $tag"; fi
done
echo "C15A_TRAIN_DONE"
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/eval_arms.py ridgepass --shard $g:8 >> /tmp/c15eval_$g.log 2>&1 &
done
wait
python3 loop3/eval_arms.py ridgepick
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/eval_arms.py fullpass --shard $g:8 >> /tmp/c15eval_$g.log 2>&1 &
done
wait
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/genre_eval.py gen --shard $g:8 >> /tmp/c15genre_$g.log 2>&1 &
done
wait
echo "C15A_EVAL_DONE"
for a in 4 6; do
  for g in 0 1 2 3 4 5 6 7; do
    CUDA_VISIBLE_DEVICES=$g python3 loop3/e_arm_alpha.py gen --alpha $a --shard $g:8 >> /tmp/c15c_a${a}_$g.log 2>&1 &
  done
  wait
done
echo "C15C_DONE"
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/m3_steer.py scan2 --shard $g:8 >> /tmp/c15b_$g.log 2>&1 &
done
wait
python3 loop3/m3_steer.py merge2 > /tmp/c15b_verdict.log 2>&1
cat /tmp/c15b_verdict.log
echo "C15_ALL_DONE"
