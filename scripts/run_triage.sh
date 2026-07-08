#!/usr/bin/env bash
# Steering triage: extract(8) -> merge -> scan(8) -> scanmerge -> triage(8). 8-GPU.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"; NGPU="${NGPU:-8}"
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES=$g python3 probes/steer_triage.py extract --shard ${g}:${NGPU} > /tmp/tri_ext_${g}.log 2>&1 &
done; wait
python3 probes/steer_triage.py merge || exit 1
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES=$g python3 probes/steer_triage.py scan --shard ${g}:${NGPU} > /tmp/tri_scan_${g}.log 2>&1 &
done; wait
python3 probes/steer_triage.py scanmerge || exit 1
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES=$g python3 probes/steer_triage.py triage --shard ${g}:${NGPU} > /tmp/tri_tri_${g}.log 2>&1 &
done; wait
echo "triage rows: $(cat probes/out_triage/triage_shard*.jsonl | wc -l)"
echo "TRIAGE DONE"
