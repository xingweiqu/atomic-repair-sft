#!/bin/bash
# E arm: steering-only anchor, pure inference, 8-GPU sharded.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
unset FORCE_TORCHRUN NPROC_PER_NODE
for g in 0 1 2 3 4 5 6 7; do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/e_arm.py gen --shard $g:8 >> /tmp/e_arm_$g.log 2>&1 &
done
wait
python3 loop3/e_arm.py merge && echo "E_ARM_DONE"
