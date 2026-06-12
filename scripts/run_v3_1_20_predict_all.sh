#!/usr/bin/env bash
# All predictions (single GPU; unset torchrun so a leftover env var can't spawn distributed)
set -euo pipefail
unset FORCE_TORCHRUN NPROC_PER_NODE || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
for cfg in "$REPO"/configs/v3_1/*_predict.yaml; do
  echo ">>> $(basename "$cfg")"; llamafactory-cli train "$cfg"
done
