#!/usr/bin/env bash
# Epoch-sweep prediction: decode every _e{N} ckpt on v4_actionized_eval (480). Single GPU, resilient.
set -uo pipefail
unset FORCE_TORCHRUN NPROC_PER_NODE || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
failed=()
for cfg in "$REPO"/configs/v4/epoch_sweep/*_predict.yaml; do
  name="$(basename "$cfg")"
  echo ">>> $name"
  if llamafactory-cli train "$cfg"; then echo "<<< OK   $name"; else echo "<<< FAIL $name"; failed+=("$name"); fi
done
echo "================ predict summary ================"
[ "${#failed[@]}" -eq 0 ] && { echo "all predict configs succeeded"; exit 0; }
echo "FAILED (${#failed[@]}):"; printf '  - %s\n' "${failed[@]}"; exit 1
