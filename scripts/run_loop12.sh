#!/usr/bin/env bash
# C-11 Loop1+2 driver, 8-GPU saturated end to end:
# genbase(CPU) -> P/R generation 8-shard -> assemble+gates(CPU, fail=stop) -> probe inference 8-shard.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"; NGPU="${NGPU:-8}"
MODEL="${1:-/mnt/hdfs/xwqu/Qwen3-8B}"
python3 probes/build_probes.py genbase || exit 1
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES="$g" python3 probes/build_probes.py genpr --model "$MODEL" --shard "${g}:${NGPU}" > "/tmp/probes_pr_${g}.log" 2>&1 &
done; wait
python3 probes/build_probes.py assemble || { echo "ASSEMBLE GATE FAIL"; exit 1; }
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES="$g" python3 probes/run_probes.py --model "$MODEL" --shard "${g}:${NGPU}" > "/tmp/probes_run_${g}.log" 2>&1 &
done; wait
echo "answers: $(cat probes/out/answers.shard*.jsonl | wc -l) rows"
echo "LOOP1+2 INFERENCE DONE (classification held until construct audit sign-off per prereg)"
