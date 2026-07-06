#!/usr/bin/env bash
# batch-5 Tier-2 一键(全并行):token 闸门 -> zero-shot 8卡并行 -> 干净闸门(CPU,不过即停)
# -> 6 训练(每个吃满 8 卡,逐个) -> 12 predicts 8卡并行。断点续跑。
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
NGPU="${NGPU:-8}"
python3 learnability_family/gate_token_audit.py --model /mnt/hdfs/xwqu/Qwen3-8B || exit 1
run_predicts() {  # $1 = glob pattern
  mapfile -t CFGS < <(ls $1)
  for g in $(seq 0 $((NGPU-1))); do
    ( for i in "${!CFGS[@]}"; do
        [ $(( i % NGPU )) -eq "$g" ] || continue
        cfg="${CFGS[$i]}"; out="$(grep -m1 '^output_dir:' "$cfg" | awk '{print $2}')"
        [ -s "$out/generated_predictions.jsonl" ] && { echo "[gpu$g] skip $(basename "$cfg")"; continue; }
        unset FORCE_TORCHRUN NPROC_PER_NODE
        CUDA_VISIBLE_DEVICES="$g" llamafactory-cli train "$cfg" > "/tmp/t2_$(basename "$cfg" .yaml).log" 2>&1 \
          && echo "[gpu$g] OK $(basename "$cfg")" || echo "[gpu$g] FAIL $(basename "$cfg")"
      done ) &
  done
  wait
}
echo "== zero-shot (8 parallel) =="; run_predicts "$REPO/configs/tier2/tier2_zeroshot_*_predict.yaml"
echo "== clean gate =="; python3 learnability_family/gate_clean.py || { echo "CLEAN GATE FAIL — STOP"; exit 1; }
echo "== 6 trains (8-GPU each, sequential) =="
for cfg in "$REPO"/configs/tier2/tier2_*_e8_sft.yaml; do
  out="$(grep -m1 '^output_dir:' "$cfg" | awk '{print $2}')"
  [ -f "$out/config.json" ] && { echo "skip $(basename "$cfg") (done)"; continue; }
  FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train "$cfg" && echo "OK $(basename "$cfg")" || echo "FAIL $(basename "$cfg")"
done
echo "== 12 predicts (8 parallel) =="; run_predicts "$REPO/configs/tier2/tier2_*_e8_predict_*.yaml"
echo "== collect =="
DST="$REPO/data_tier2/predict_outputs"; mkdir -p "$DST"; n=0
for d in /mnt/hdfs/xwqu/tier2/output/predict_*; do
  [ -s "$d/generated_predictions.jsonl" ] || continue
  mkdir -p "$DST/$(basename "$d")"; cp "$d/generated_predictions.jsonl" "$DST/$(basename "$d")/"; n=$((n+1))
done
echo "collected $n predict dirs -> data_tier2/predict_outputs"
