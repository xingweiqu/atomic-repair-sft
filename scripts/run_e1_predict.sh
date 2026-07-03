#!/usr/bin/env bash
# E1+E3 predicts, sharded across 8 GPUs, resumable (same pattern as run_v4_44).
set -uo pipefail
unset FORCE_TORCHRUN NPROC_PER_NODE || true
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
NGPU="${NGPU:-8}"
ONLY="${ONLY:-}"   # regex filter for two-machine split
mapfile -t CFGS < <(ls "$REPO"/configs/v4/e1/*_predict.yaml "$REPO"/configs/v4/e3/*_predict.yaml)
if [ -n "$ONLY" ]; then
  mapfile -t CFGS < <(printf '%s\n' "${CFGS[@]}" | grep -E "$ONLY")
fi
echo "sharding ${#CFGS[@]} predicts across $NGPU GPUs"
run_queue() {
  local g="$1" i cfg out
  for i in "${!CFGS[@]}"; do
    [ $(( i % NGPU )) -eq "$g" ] || continue
    cfg="${CFGS[$i]}"; out="$(grep -m1 '^output_dir:' "$cfg" | awk '{print $2}')"
    if [ -s "$out/generated_predictions.jsonl" ]; then echo "[gpu$g] skip $(basename "$cfg")"; continue; fi
    if CUDA_VISIBLE_DEVICES="$g" llamafactory-cli train "$cfg" > "/tmp/e1_gpu${g}_$(basename "$cfg" .yaml).log" 2>&1; then
      echo "[gpu$g] OK   $(basename "$cfg")"
    else
      echo "[gpu$g] FAIL $(basename "$cfg")"
    fi
  done
}
for g in $(seq 0 $((NGPU-1))); do run_queue "$g" & done
wait
echo "missing:"; for cfg in "${CFGS[@]}"; do out="$(grep -m1 '^output_dir:' "$cfg" | awk '{print $2}')"; [ -s "$out/generated_predictions.jsonl" ] || echo "  $(basename "$cfg")"; done
