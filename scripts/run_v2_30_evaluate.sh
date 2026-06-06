#!/usr/bin/env bash
set -euo pipefail; cd "$(dirname "$0")/.."
P=output_v2; R=data_v2/reports; mkdir -p "$R"
pr(){ echo "$P/$1/generated_predictions.jsonl"; }
python evaluate_v2.py --mode inject --pred "$(pr predict_inject_base)"  --eval-source data_v2/inject.jsonl --out "$R/inject_base.json" --sanity || true
python evaluate_v2.py --mode inject --pred "$(pr predict_inject_floor)" --eval-source data_v2/inject.jsonl --out "$R/inject_floor.json" --sanity || true
for c in zs_direct:zeroshot_direct zs_cot:zeroshot_cot factonly:factonly fc:fact_then_cot fs:fact_then_skillcot; do
  d="${c%%:*}"; n="${c##*:}"
  python evaluate_v2.py --mode repair --pred "$(pr predict_$d)" --eval-source data_v2/repair_eval.jsonl --out "$R/$n.json" --report "$R/$n.md" || true
done
echo "reports -> $R"
