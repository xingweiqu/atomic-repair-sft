#!/usr/bin/env bash
# E5b 全并行一键:generate 8分片 -> classify(CPU闸门,不过即停) -> extract 8分片+merge
# -> stage1 8分片+merge -> stage2 6α并行 -> 投影仪器(CPU)。
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
MODEL="${1:-/mnt/hdfs/xwqu/gsm-repair-v4/output/scaffold_conv_e8}"; NGPU="${NGPU:-8}"
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES="$g" python3 steering/e5b.py generate --model "$MODEL" --shard "${g}:${NGPU}" > "/tmp/e5b_gen_${g}.log" 2>&1 &
done; wait
python3 steering/e5b.py classify || { echo "CLASS GATE FAIL — 停,贴 classify 输出"; exit 1; }
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES="$g" python3 steering/e5b.py extract --model "$MODEL" --shard "${g}:${NGPU}" > "/tmp/e5b_ext_${g}.log" 2>&1 &
done; wait
python3 steering/e5b.py extractmerge
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES="$g" python3 steering/e5b.py sweep1 --model "$MODEL" --shard "${g}:${NGPU}" > "/tmp/e5b_s1_${g}.log" 2>&1 &
done; wait
python3 steering/e5b.py sweep1merge
ALPHAS=(0.0 2.0 4.0 8.0 16.0 32.0)
for k in "${!ALPHAS[@]}"; do
  CUDA_VISIBLE_DEVICES="$k" python3 steering/e5b.py sweep2 --model "$MODEL" --alpha "${ALPHAS[$k]}" > "/tmp/e5b_s2_${ALPHAS[$k]}.log" 2>&1 &
done; wait
python3 steering/w_projection.py
echo "E5b all done"; ls steering/out_e5b/
