#!/usr/bin/env bash
set -euo pipefail; cd "$(dirname "$0")/.."
python generate_v2.py --out_dir data_v2_1 --seed 42
python validate_v2.py --data_dir data_v2_1 --out data_v2_1/sanity_v2_1.json
python convert_v2_1.py --data_dir data_v2_1
