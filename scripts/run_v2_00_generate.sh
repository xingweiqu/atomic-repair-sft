#!/usr/bin/env bash
set -euo pipefail; cd "$(dirname "$0")/.."
python generate_v2.py --out_dir data_v2 --seed 42
