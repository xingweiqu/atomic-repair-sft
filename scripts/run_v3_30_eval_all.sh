#!/usr/bin/env bash
# Local scoring after pulling predictions into data_v3/predict_outputs/predict_<name>/
set -euo pipefail; cd "$(dirname "$0")/.."
R=data_v3/reports; mkdir -p "$R"
score(){ python -m scenario_repair_v3.evaluate_v3 --pred "data_v3/predict_outputs/predict_$1/generated_predictions.jsonl" --eval-source data_v3/repair_eval.jsonl --out "$R/$2.json" || true; }
score factonly factonly; score actionized_full actionized_full; score cot cot
for p in override_wrong_claim verify_bridge verify_step recompute use_provided_support retrieve_or_abstain; do
  score targeted_${p} targeted_${p}; score random_${p} random_${p}; score wrongtarget_${p} wrongtarget_${p}
done
for m in M1 M2 M3 M4 M5 M6; do score cumulative_${m} cumulative_${m}; done
python -m scenario_repair_v3.compare_v3 --reports "$R" --out data_v3/results/comparison_v3
