#!/usr/bin/env bash
set -euo pipefail; cd "$(dirname "$0")/.."
python -m scenario_repair_v3.convert_v3 --data_dir data_v3
