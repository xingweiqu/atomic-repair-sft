#!/usr/bin/env bash
# Controls: same-size random + wrong-target
set -euo pipefail
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
for p in override_wrong_claim verify_bridge verify_step recompute use_provided_support retrieve_or_abstain; do
  FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$REPO/configs/v3/random_${p}_sft.yaml"
  FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$REPO/configs/v3/wrongtarget_${p}_sft.yaml"
done
