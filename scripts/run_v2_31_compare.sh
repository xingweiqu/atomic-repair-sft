#!/usr/bin/env bash
set -euo pipefail; cd "$(dirname "$0")/.."
R=data_v2/reports
python compare_v2.py --out data_v2/comparison_v2 \
  --inject-base "$R/inject_base.json" --inject-floor "$R/inject_floor.json" \
  --zeroshot-direct "$R/zeroshot_direct.json" --zeroshot-cot "$R/zeroshot_cot.json" \
  --factonly-repair "$R/factonly.json" --fact-then-cot "$R/fact_then_cot.json" \
  --fact-then-skillcot "$R/fact_then_skillcot.json"
echo "-> data_v2/comparison_v2.md"
