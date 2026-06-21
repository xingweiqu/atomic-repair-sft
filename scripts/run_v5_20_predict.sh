#!/usr/bin/env bash
# v5-clean: run all predicts (single-GPU), continue-on-error + summary.
set -uo pipefail
unset FORCE_TORCHRUN NPROC_PER_NODE || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
failed=()
for cfg in "$REPO"/configs/v5/*_predict.yaml; do
  name="$(basename "$cfg")"; echo ">>> $name"
  if llamafactory-cli train "$cfg"; then echo "<<< OK $name"; else echo "<<< FAIL $name"; failed+=("$name"); fi
done
echo "==== predict summary ===="; [ "${#failed[@]}" -eq 0 ] && echo "all OK" || { printf 'FAILED: %s\n' "${failed[@]}"; exit 1; }
