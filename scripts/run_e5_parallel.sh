#!/usr/bin/env bash
# E5 multi-GPU: extract(1卡) -> stage1 8分片 -> merge -> stage2 6α各占一卡 -> align(1卡)
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
MODEL="${1:-/mnt/hdfs/xwqu/gsm-repair-v4/output/scaffold_conv_e8}"; NGPU="${NGPU:-8}"
CUDA_VISIBLE_DEVICES=0 python3 steering/e5_steering.py extract --model "$MODEL" || exit 1
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES="$g" python3 steering/e5_steering.py sweep1 --model "$MODEL" \
    --shard "${g}:${NGPU}" > "/tmp/e5_s1_${g}.log" 2>&1 &
done
wait
python3 steering/e5_steering.py sweep1merge || exit 1
ALPHAS=(0.0 2.0 4.0 8.0 16.0 32.0)
for k in "${!ALPHAS[@]}"; do
  CUDA_VISIBLE_DEVICES="$k" python3 steering/e5_steering.py sweep2 --model "$MODEL" \
    --alpha "${ALPHAS[$k]}" > "/tmp/e5_s2_${ALPHAS[$k]}.log" 2>&1 &
done
wait
CUDA_VISIBLE_DEVICES=0 python3 steering/e5_steering.py align --model "$MODEL"
echo "E5 parallel done; outputs in steering/out/"
ls steering/out/
