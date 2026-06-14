#!/usr/bin/env bash
# Collect every v4 prediction from HDFS back into the repo, mirroring the v3 layout
# (data_v4/predict_outputs/predict_<name>/generated_predictions.jsonl). Reads each predict
# config's output_dir so the mapping always matches what run_v4_20 actually wrote. Missing
# outputs are reported, not fatal. Prints a line-count summary at the end.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
DEST="$REPO/data_v4/predict_outputs"; mkdir -p "$DEST"
ok=(); missing=()
for cfg in "$REPO"/configs/v4/*_predict.yaml; do
  out="$(grep -E '^output_dir:' "$cfg" | head -1 | awk '{print $2}')"
  name="$(basename "$out")"
  src="$out/generated_predictions.jsonl"
  if [ -f "$src" ]; then
    mkdir -p "$DEST/$name"
    cp "$src" "$DEST/$name/generated_predictions.jsonl"
    ok+=("$name:$(wc -l < "$DEST/$name/generated_predictions.jsonl" | tr -d ' ')")
  else
    missing+=("$name")
  fi
done
echo "================ collected (${#ok[@]}) ================"
printf '  %s\n' "${ok[@]}"
if [ "${#missing[@]}" -gt 0 ]; then
  echo "================ MISSING (${#missing[@]}) — predict not generated ================"
  printf '  %s\n' "${missing[@]}"
fi
