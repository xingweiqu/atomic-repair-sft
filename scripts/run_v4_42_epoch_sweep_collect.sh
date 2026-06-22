#!/usr/bin/env bash
# Collect epoch-sweep predictions from HDFS output dirs into the repo for committing/analysis.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
HDFS="/mnt/hdfs/xwqu/gsm-repair-v4/output"
DST="$REPO/data_v4/epoch_sweep_predict"; mkdir -p "$DST"
n=0
for d in "$HDFS"/predict_*_e*; do
  [ -d "$d" ] || continue
  name="$(basename "$d")"
  src="$d/generated_predictions.jsonl"
  [ -f "$src" ] || { echo "MISSING $name/generated_predictions.jsonl"; continue; }
  mkdir -p "$DST/$name"; cp "$src" "$DST/$name/generated_predictions.jsonl"; n=$((n+1))
  echo "collected $name ($(wc -l < "$src") lines)"
done
echo "collected $n prediction dirs -> $DST"
