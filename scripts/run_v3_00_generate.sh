#!/usr/bin/env bash
set -euo pipefail; cd "$(dirname "$0")/.."
# add --use-api to paraphrase scenario surfaces via the claude CLI (cached, optional)
python -m scenario_repair_v3.generate_v3 --out_dir data_v3 --seed 42 "$@"
