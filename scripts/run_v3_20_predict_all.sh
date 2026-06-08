#!/usr/bin/env bash
# All predictions (single GPU each)
set -euo pipefail
LF_DIR="${LLAMA_FACTORY_DIR:-$HOME/LLaMA-Factory}"; REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"
for cfg in "$REPO"/configs/v3/*_predict.yaml; do
  llamafactory-cli train "$cfg"
done
