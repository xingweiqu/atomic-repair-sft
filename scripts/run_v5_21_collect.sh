#!/usr/bin/env bash
# v5-clean: collect predictions HDFS -> data_v5/predict_outputs/predict_<name>/generated_predictions.jsonl
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
DEST="$REPO/data_v5/predict_outputs"; mkdir -p "$DEST"; ok=(); missing=()
for cfg in "$REPO"/configs/v5/*_predict.yaml; do
  out="$(grep -E '^output_dir:' "$cfg" | head -1 | awk '{print $2}')"; name="$(basename "$out")"
  src="$out/generated_predictions.jsonl"
  if [ -f "$src" ]; then mkdir -p "$DEST/$name"; cp "$src" "$DEST/$name/generated_predictions.jsonl"; ok+=("$name:$(wc -l < "$DEST/$name/generated_predictions.jsonl" | tr -d ' ')"); else missing+=("$name"); fi
done
echo "collected (${#ok[@]}):"; printf '  %s\n' "${ok[@]}"
[ "${#missing[@]}" -gt 0 ] && { echo "MISSING (${#missing[@]}):"; printf '  %s\n' "${missing[@]}"; }
