#!/usr/bin/env bash
# R-11 bleed curve: plain-genre transfer predicts for all epoch-sweep ckpts.
# Run AFTER run_v4_40 (sweep training). Continue-on-error like run_v4_20.
set -uo pipefail
unset FORCE_TORCHRUN NPROC_PER_NODE || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
failed=()
for cfg in "$REPO"/configs/v4/epoch_sweep/transfer_*_predict.yaml; do
  name="$(basename "$cfg")"
  echo ">>> $name"
  if llamafactory-cli train "$cfg"; then echo "<<< OK   $name"; else echo "<<< FAIL $name (continuing)"; failed+=("$name"); fi
done
echo "FAILED: ${failed[*]:-none}"
