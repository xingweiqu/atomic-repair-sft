#!/usr/bin/env bash
set -euo pipefail
unset FORCE_TORCHRUN NPROC_PER_NODE || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
for cfg in "$REPO"/configs/v4/*_predict.yaml; do
  echo ">>> $(basename "$cfg")"; llamafactory-cli train "$cfg"
done
