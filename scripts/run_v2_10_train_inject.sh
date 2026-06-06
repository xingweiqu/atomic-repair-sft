#!/usr/bin/env bash
# stage1 knowledge injection -> output_v2/inject
set -euo pipefail
LF_DIR="${LF_DIR:-$HOME/LLaMA-Factory}"; NPROC="${NPROC:-8}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
[ -d "$LF_DIR" ] || { echo "set LF_DIR"; exit 1; }
FORCE_TORCHRUN=1 NPROC_PER_NODE="$NPROC" llamafactory-cli train "$REPO/configs/v2/inject_sft.yaml"
