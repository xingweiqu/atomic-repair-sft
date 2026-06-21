#!/usr/bin/env bash
# v5-clean: train all 14 branches, EQUAL convergence (8 epoch), relay from BASE. 8-GPU. Continue-on-error.
set -uo pipefail
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
failed=()
for cfg in "$REPO"/configs/v5/*_sft.yaml; do
  name="$(basename "$cfg")"; echo ">>> $name"
  if FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$cfg"; then echo "<<< OK $name"; else echo "<<< FAIL $name"; failed+=("$name"); fi
done
echo "==== train summary ===="; [ "${#failed[@]}" -eq 0 ] && echo "all OK" || { printf 'FAILED: %s\n' "${failed[@]}"; exit 1; }
