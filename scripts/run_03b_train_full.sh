#!/usr/bin/env bash
# FULL-parameter SFT for atomic-repair on an 8x80G box via DeepSpeed ZeRO-3.
# This is the full fine-tuning path (NOT LoRA). Run after cloning LLaMA-Factory
# and installing its deps (incl. deepspeed). See README.
set -euo pipefail

LF_DIR="${LF_DIR:-$HOME/LLaMA-Factory}"
NPROC="${NPROC:-8}"   # number of GPUs; override if not 8
REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CFG="$REPO_DIR/configs/qwen3_8b_repair_full_sft.yaml"

if [ ! -d "$LF_DIR" ]; then
  echo "LLaMA-Factory not found at $LF_DIR; set LF_DIR or clone first" >&2
  exit 1
fi

# Run from the repo dir so dataset_dir: ./data and the relative deepspeed path resolve.
cd "$REPO_DIR"

# FORCE_TORCHRUN tells llamafactory-cli to launch a distributed run across NPROC GPUs.
FORCE_TORCHRUN=1 NPROC_PER_NODE="$NPROC" llamafactory-cli train "$CFG"
