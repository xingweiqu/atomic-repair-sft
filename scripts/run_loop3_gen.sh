#!/usr/bin/env bash
# Loop3 Batch-1 数据线 + 2b(opsonly ckpt 素题探针)。8-GPU。
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"; NGPU="${NGPU:-8}"
# --- 2b first (small): opsonly ckpt on O/W1/W2 probes ---
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES=$g python3 probes/run_probes.py \
    --model /mnt/hdfs/xwqu/gsm-repair-v4/output/e1b_opsonly_n300_s42_e8 \
    --types O,W1,W2 --outdir probes/out_opsonly --shard ${g}:${NGPU} > /tmp/l3_2b_${g}.log 2>&1 &
done; wait
echo "2b rows: $(cat probes/out_opsonly/answers.shard*.jsonl | wc -l)"
# --- component pools ---
python3 loop3/gen_components.py genprog || exit 1
python3 loop3/gen_components.py prompts || exit 1
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES=$g python3 loop3/gen_components.py genllm --shard ${g}:${NGPU} > /tmp/l3_gen_${g}.log 2>&1 &
done; wait
python3 loop3/gen_components.py assemble || { echo "ASSEMBLE/YIELD FAIL"; exit 1; }
echo "LOOP3 GEN DONE"
