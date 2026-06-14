#!/usr/bin/env bash
# Re-run ONLY the two transfer predicts (max_new_tokens bumped to 2048 so the Qwen3 <think>
# block is no longer truncated before the answer line). Single-GPU, ~300 items each. After
# this, run scripts/run_v4_21_collect_predictions.sh to pull the refreshed outputs back.
set -uo pipefail
unset FORCE_TORCHRUN NPROC_PER_NODE || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
failed=()
for cfg in transfer_base_predict transfer_verify_step_predict; do
  echo ">>> $cfg"
  if llamafactory-cli train "$REPO/configs/v4/${cfg}.yaml"; then echo "<<< OK $cfg"; else echo "<<< FAIL $cfg"; failed+=("$cfg"); fi
done
[ "${#failed[@]}" -eq 0 ] && echo "both transfer predicts OK" || { echo "FAILED: ${failed[*]}"; exit 1; }
