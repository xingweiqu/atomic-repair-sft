#!/usr/bin/env bash
# Probe repair pass per qc/AUDIT_RULINGS_probes.md. 8-GPU saturated.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"; cd "$REPO"; NGPU="${NGPU:-8}"
MODEL="${1:-/mnt/hdfs/xwqu/Qwen3-8B}"
python3 probes/fix_probes.py poolfilter || exit 1
python3 probes/fix_probes.py fixw2 || exit 1
python3 probes/fix_probes.py prompts2 || exit 1
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES="$g" python3 probes/fix_probes.py genpr2 --model "$MODEL" --shard "${g}:${NGPU}" > "/tmp/fix_pr2_${g}.log" 2>&1 &
done; wait
python3 probes/fix_probes.py assemble2 || { echo "ASSEMBLE2 GATE FAIL"; exit 1; }
# yield sanity: no probe column may be empty or absurdly small
python3 - << 'PY' || { echo "YIELD GATE FAIL"; exit 1; }
import json
m = json.load(open("probes/data/manifest2.json"))
bad = [k for k, v in m.items() if v.get("kept", 0) < 200]
print("yield check:", {k: v.get("kept") for k, v in m.items()}, "bad:", bad)
raise SystemExit(1 if bad else 0)
PY
# re-inference: P/R/S full columns + W2 changed ids only -> probes/out2/
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES="$g" python3 probes/run_probes.py --model "$MODEL" --types P,R,S --outdir probes/out2/prs --shard "${g}:${NGPU}" > "/tmp/fix_prs_${g}.log" 2>&1 &
done; wait
for g in $(seq 0 $((NGPU-1))); do
  CUDA_VISIBLE_DEVICES="$g" python3 probes/run_probes.py --model "$MODEL" --types W2 --ids-file probes/data/w2_rerun_ids.json --outdir probes/out2/w2 --shard "${g}:${NGPU}" > "/tmp/fix_w2_${g}.log" 2>&1 &
done; wait
echo "rerun rows: $(cat probes/out2/*/answers.shard*.jsonl 2>/dev/null | wc -l)"
echo "PROBE FIX PASS DONE (audits: P_pairs100 / S_v2 / R_v2 / F_pairs20 -> Xingwei)"
