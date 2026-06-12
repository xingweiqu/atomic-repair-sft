#!/usr/bin/env bash
# actionized_full + scaffold_only (the two endpoints / baselines)
set -euo pipefail
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
for c in actionized_full scaffold_only; do
  FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$REPO/configs/v3_1/${c}_sft.yaml"
done
