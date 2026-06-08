#!/usr/bin/env bash
# Exp3: cumulative curriculum
set -euo pipefail
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
for m in M1 M2 M3 M4 M5 M6; do
  FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$REPO/configs/v3/cumulative_${m}_sft.yaml"
done
