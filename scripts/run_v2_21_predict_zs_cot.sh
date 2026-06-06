#!/usr/bin/env bash
# A zero-shot CoT
set -euo pipefail
LF_DIR="${LF_DIR:-$HOME/LLaMA-Factory}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
[ -d "$LF_DIR" ] || { echo "set LF_DIR"; exit 1; }
llamafactory-cli train "$REPO/configs/v2/zeroshot_cot_predict.yaml"
