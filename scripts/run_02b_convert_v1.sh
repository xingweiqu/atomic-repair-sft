#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
python convert_to_llamafactory_v1.py \
  --train data/repair_raw_train.jsonl \
  --eval data/repair_raw_eval.jsonl \
  --out_dir data_v1
