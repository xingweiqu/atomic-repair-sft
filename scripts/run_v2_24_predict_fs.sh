#!/usr/bin/env bash
# D repair
set -euo pipefail
LF_DIR="${LF_DIR:-$HOME/LLaMA-Factory}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
[ -d "$LF_DIR" ] || { echo "set LF_DIR"; exit 1; }
llamafactory-cli train "$REPO/configs/v2/fact_then_skillcot_predict.yaml"
