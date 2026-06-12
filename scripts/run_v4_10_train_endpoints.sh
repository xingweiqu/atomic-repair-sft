#!/usr/bin/env bash
set -euo pipefail
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
for c in actionized_full scaffold_only; do
  FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$REPO/configs/v4/${c}_sft.yaml"
done
