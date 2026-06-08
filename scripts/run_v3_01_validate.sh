#!/usr/bin/env bash
set -euo pipefail; cd "$(dirname "$0")/.."
python -m scenario_repair_v3.validate_v3 --data_dir data_v3 --out data_v3/sanity_v3.json
