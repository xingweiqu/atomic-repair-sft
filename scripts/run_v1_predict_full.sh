#!/usr/bin/env bash
set -euo pipefail
COND="${COND:?set COND to A, B, C, or D}"
LF_DIR="${LF_DIR:-$HOME/LLaMA-Factory}"
NPROC="${NPROC:-8}"
cd "$(git rev-parse --show-toplevel)"
export PATH="$LF_DIR/src:$LF_DIR:$PATH"
CFG="configs/qwen3_8b_repair_v1_${COND}_full_predict.yaml"
FORCE_TORCHRUN=1 NPROC_PER_NODE="$NPROC" llamafactory-cli train "$CFG"
