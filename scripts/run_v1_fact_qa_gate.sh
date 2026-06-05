#!/usr/bin/env bash
set -euo pipefail
LF_DIR="${LF_DIR:-$HOME/LLaMA-Factory}"
NPROC="${NPROC:-8}"
cd "$(dirname "${BASH_SOURCE[0]}")/.."
export PATH="$LF_DIR/src:$LF_DIR:$PATH"
python fact_qa_gate_v1.py build --raw data/repair_raw_eval.jsonl --out_dir data_v1
FORCE_TORCHRUN=1 NPROC_PER_NODE="$NPROC" llamafactory-cli train configs/qwen3_8b_repair_v1_fact_base_predict.yaml
FORCE_TORCHRUN=1 NPROC_PER_NODE="$NPROC" llamafactory-cli train configs/qwen3_8b_repair_v1_fact_B_predict.yaml
python fact_qa_gate_v1.py score
