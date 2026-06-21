#!/usr/bin/env bash
# A1 (B' debt #1): train a CONVERGENT v3 floor and predict it, so the B' modulation x-axis
# (v3 floor ability margin) is trustworthy. scaffold_only (3 epoch) was underfit (keep 0.22).
# After this, recollect the prediction and re-run bprime_audit with --v3_floor scaffold_conv.
set -uo pipefail
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"

echo ">>> TRAIN scaffold_conv (v3, 8-GPU, relay from inject ckpt)"
FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$REPO/configs/v3_1/scaffold_conv_sft.yaml"

echo ">>> PREDICT scaffold_conv (v3, single-GPU)"
unset FORCE_TORCHRUN NPROC_PER_NODE || true
export CUDA_VISIBLE_DEVICES="${CUDA_VISIBLE_DEVICES:-0}"
llamafactory-cli train "$REPO/configs/v3_1/scaffold_conv_predict.yaml"
echo "done. copy /mnt/hdfs/xwqu/scenario-repair-v3_1/output/predict_scaffold_conv/generated_predictions.jsonl"
echo "  -> data_v3_1/predict_outputs/predict_scaffold_conv/  then commit & push."
