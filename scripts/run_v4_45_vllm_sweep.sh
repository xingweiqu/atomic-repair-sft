#!/usr/bin/env bash
# vllm predict for ALL epoch-sweep ckpts, sharded across N GPUs (one model per GPU slot,
# each ckpt does repair(480)+transfer(300) in one load). RESUMABLE (skips done outputs).
# PRECONDITION: gate must have PASSED:
#   CUDA_VISIBLE_DEVICES=0 python3 scripts/vllm_predict_one.py --gate
#   python3 scripts/vllm_gate_check.py --vllm /mnt/hdfs/xwqu/gsm-repair-v4/output/predict_vllm_gate_scaffold_conv/generated_predictions.jsonl
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
NGPU="${NGPU:-8}"
TAGS=()
for b in scaffold_conv targeted_override_wrong_claim targeted_recompute random_override_wrong_claim; do
  for e in 1 2 3 8 30; do TAGS+=("${b}_e${e}"); done
done
for e in 1 3 30; do TAGS+=("targeted_verify_step_e${e}"); done
echo "sharding ${#TAGS[@]} ckpts across $NGPU GPUs"

run_queue() {
  local g="$1" i
  for i in "${!TAGS[@]}"; do
    [ $(( i % NGPU )) -eq "$g" ] || continue
    echo "[gpu$g] >>> ${TAGS[$i]}"
    if CUDA_VISIBLE_DEVICES="$g" python3 scripts/vllm_predict_one.py --tag "${TAGS[$i]}" \
         > "/tmp/vllm_gpu${g}_${TAGS[$i]}.log" 2>&1; then
      echo "[gpu$g] <<< OK   ${TAGS[$i]}"
    else
      echo "[gpu$g] <<< FAIL ${TAGS[$i]}  (log: /tmp/vllm_gpu${g}_${TAGS[$i]}.log)"
    fi
  done
}
for g in $(seq 0 $((NGPU-1))); do run_queue "$g" & done
wait
echo "================ vllm sweep done ================"
echo "missing outputs (if any):"
for t in "${TAGS[@]}"; do
  for d in "predict_${t}" "predict_transfer_${t}"; do
    [ -s "/mnt/hdfs/xwqu/gsm-repair-v4/output/${d}/generated_predictions.jsonl" ] || echo "  MISSING: $d"
  done
done
