#!/usr/bin/env bash
# Review follow-up (round 1): (1) train a CONVERGENT floor and predict it; (3) transfer check for
# the mixed model. After this, run scripts/run_v4_21_collect_predictions.sh to pull all three back.
#   - scaffold_conv: convergent floor (replaces the underfit scaffold_only as the baseline)
#   - predict_scaffold_conv: that floor on repair eval
#   - predict_transfer_actionized_full: mixed model on un-perturbed GSM (drift comparison)
set -uo pipefail
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"

echo ">>> TRAIN scaffold_conv (8-GPU)"
FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$REPO/configs/v4/scaffold_conv_sft.yaml"

echo ">>> PREDICT (single-GPU)"
unset FORCE_TORCHRUN NPROC_PER_NODE || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
failed=()
for cfg in scaffold_conv_predict transfer_actionized_full_predict; do
  echo ">>> $cfg"
  if llamafactory-cli train "$REPO/configs/v4/${cfg}.yaml"; then echo "<<< OK $cfg"; else echo "<<< FAIL $cfg"; failed+=("$cfg"); fi
done
[ "${#failed[@]}" -eq 0 ] && echo "all OK" || { echo "FAILED: ${failed[*]}"; exit 1; }
