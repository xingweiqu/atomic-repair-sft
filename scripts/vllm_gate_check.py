#!/usr/bin/env python3
"""Instrument-change gate for the vllm engine swap (runs ON THE SERVER, pure CPU).

Scores the SAME ckpt (round-1 scaffold_conv) decoded by both engines with the frozen
strict judge and requires |Δ overall strict acc| <= 1pp. Fails -> exit 1 -> per the red
lines the server agent must STOP and report; vllm sweep outputs are then untrusted.

Usage:
  python3 scripts/vllm_gate_check.py \
      --vllm /mnt/hdfs/xwqu/gsm-repair-v4/output/predict_vllm_gate_scaffold_conv/generated_predictions.jsonl
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ledger.judge import load_items, load_preds, score_run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LF_PRED = ROOT / "data_v4/predict_outputs/predict_scaffold_conv/generated_predictions.jsonl"


def overall_strict(preds, items):
    v = score_run(items, preds, "v4")
    return sum(x["correct_strict"] for x in v) / len(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--vllm", required=True, type=Path)
    ap.add_argument("--tol", type=float, default=0.01)
    args = ap.parse_args()

    items = load_items(ROOT / "data_v4/repair_eval.jsonl")
    lf = overall_strict(load_preds(LF_PRED), items)
    vl = overall_strict(load_preds(args.vllm), items)
    d = vl - lf
    print(f"strict overall  LF={lf:.4f}  vllm={vl:.4f}  diff={d:+.4f}  tol=±{args.tol}")
    if abs(d) > args.tol:
        print("GATE FAIL — engines are not equivalent; STOP and report (do not run the sweep).")
        sys.exit(1)
    print("GATE PASS — vllm outputs are ledger-equivalent.")


if __name__ == "__main__":
    main()
