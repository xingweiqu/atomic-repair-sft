#!/usr/bin/env bash
# All predictions. Prediction is single-GPU: explicitly disable distributed launch
# so a FORCE_TORCHRUN left in the environment from the training scripts does not
# spawn torchrun --nproc_per_node 8 (which then demands eval_dataset/val_size).
set -euo pipefail
unset FORCE_TORCHRUN NPROC_PER_NODE || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
for cfg in "$REPO"/configs/v3/*_predict.yaml; do
  echo ">>> predicting: $(basename "$cfg")"
  llamafactory-cli train "$cfg"
done
