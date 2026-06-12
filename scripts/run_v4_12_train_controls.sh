#!/usr/bin/env bash
set -euo pipefail
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
for p in verify_step override_wrong_claim recompute retrieve_or_abstain; do
  FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$REPO/configs/v4/random_${p}_sft.yaml"
  FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$REPO/configs/v4/wrongtarget_${p}_sft.yaml"
done
