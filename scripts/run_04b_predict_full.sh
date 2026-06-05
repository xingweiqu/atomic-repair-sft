#!/usr/bin/env bash
# Prediction on the held-out eval set with the fully fine-tuned model from run_03b.
# Full fine-tuning produces a complete checkpoint, so we load it directly
# (no adapter). Single GPU is enough for 550 eval rows.
set -euo pipefail

LF_DIR="${LF_DIR:-$HOME/LLaMA-Factory}"
NPROC="${NPROC:-1}"   # prediction only needs one GPU by default
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CFG="$REPO_DIR/configs/qwen3_8b_repair_full_predict.yaml"

if [ ! -d "$LF_DIR" ]; then
  echo "LLaMA-Factory not found at $LF_DIR; set LF_DIR or clone first" >&2
  exit 1
fi

cd "$REPO_DIR"
FORCE_TORCHRUN=1 NPROC_PER_NODE="$NPROC" llamafactory-cli train "$CFG"
