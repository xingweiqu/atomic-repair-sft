#!/bin/bash
# M1: cross-model profiles, both models, 8-GPU sharded each, then score.
source ~/atomic_env.sh
cd /opt/tiger/atomic-repair-sft-github || exit 1
unset FORCE_TORCHRUN NPROC_PER_NODE
for pair in "llama31_8b:/opt/tiger/models_mm/Llama-3.1-8B-Instruct" "qwen3_4b:/opt/tiger/models_mm/Qwen3-4B-Instruct"; do
  tag="${pair%%:*}"; model="${pair#*:}"
  for g in 0 1 2 3 4 5 6 7; do
    CUDA_VISIBLE_DEVICES=$g python3 probes/run_probes_mm.py gen --model "$model" --tag "$tag" --shard $g:8 >> /tmp/m1_${tag}_$g.log 2>&1 &
  done
  wait
  python3 probes/run_probes_mm.py score --tag "$tag" >> /tmp/m1_score.log 2>&1
  echo "M1_${tag}_DONE"
done
echo "M1_ALL_DONE"
