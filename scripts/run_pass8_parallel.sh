#!/usr/bin/env bash
# pass@8 data-parallel across N GPUs: 8 independent single-GPU vllm engines, each
# taking items[i::N]; merge stitches shards back into pool order. Resumable per shard.
# Usage: bash scripts/run_pass8_parallel.sh /mnt/hdfs/xwqu/Qwen3-8B data_v4/pass8_merged.jsonl
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
MODEL="${1:?model path}"; OUT="${2:?out path}"; NGPU="${NGPU:-8}"
for g in $(seq 0 $((NGPU-1))); do
  if [ -s "${OUT}.shard${g}" ]; then echo "skip shard $g (done)"; continue; fi
  CUDA_VISIBLE_DEVICES="$g" python3 scripts/pass8_gsm.py --model "$MODEL" --pool merged \
    --out "$OUT" --shard "${g}:${NGPU}" > "/tmp/pass8_shard${g}.log" 2>&1 &
done
wait
echo "shards done; merging..."
python3 scripts/pass8_gsm.py --model "$MODEL" --pool merged --out "$OUT" --merge "$NGPU"
