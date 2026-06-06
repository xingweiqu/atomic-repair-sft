#!/usr/bin/env bash
set -euo pipefail; cd "$(dirname "$0")/.."
python validate_v2.py --data_dir data_v2 --out data_v2/sanity_v2.json
