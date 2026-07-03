#!/usr/bin/env bash
# Parallel predict runner: shards configs/v4/epoch_sweep/*_predict.yaml across N GPUs
# (default 8), one sequential queue per GPU. RESUMABLE: skips any config whose
# output_dir already has a non-empty generated_predictions.jsonl.
# Usage:  bash scripts/run_v4_44_predict_parallel.sh            # all predict configs
#         ONLY=transfer bash scripts/run_v4_44_predict_parallel.sh   # transfer_* only
set -uo pipefail
unset FORCE_TORCHRUN NPROC_PER_NODE || true
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
NGPU="${NGPU:-8}"
PAT="${ONLY:+${ONLY}_}"
mapfile -t CFGS < <(ls "$REPO"/configs/v4/epoch_sweep/${PAT}*_predict.yaml 2>/dev/null)
[ "${#CFGS[@]}" -gt 0 ] || { echo "no configs matched"; exit 1; }
echo "sharding ${#CFGS[@]} configs across $NGPU GPUs"

run_queue() {  # $1 = gpu id
  local g="$1" i cfg out
  for i in "${!CFGS[@]}"; do
    [ $(( i % NGPU )) -eq "$g" ] || continue
    cfg="${CFGS[$i]}"
    out="$(grep -m1 '^output_dir:' "$cfg" | awk '{print $2}')"
    if [ -s "$out/generated_predictions.jsonl" ]; then
      echo "[gpu$g] skip (done): $(basename "$cfg")"; continue
    fi
    echo "[gpu$g] >>> $(basename "$cfg")"
    if CUDA_VISIBLE_DEVICES="$g" llamafactory-cli train "$cfg" > "/tmp/predict_gpu${g}_$(basename "$cfg" .yaml).log" 2>&1; then
      echo "[gpu$g] <<< OK   $(basename "$cfg")"
    else
      echo "[gpu$g] <<< FAIL $(basename "$cfg")  (log: /tmp/predict_gpu${g}_$(basename "$cfg" .yaml).log)"
    fi
  done
}

for g in $(seq 0 $((NGPU-1))); do run_queue "$g" & done
wait
echo "================ parallel predict done ================"
echo "missing outputs (if any):"
for cfg in "${CFGS[@]}"; do
  out="$(grep -m1 '^output_dir:' "$cfg" | awk '{print $2}')"
  [ -s "$out/generated_predictions.jsonl" ] || echo "  MISSING: $(basename "$cfg")"
done
