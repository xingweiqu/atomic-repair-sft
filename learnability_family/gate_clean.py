#!/usr/bin/env python3
"""Tier-2 clean gate (server-side, CPU): pre-repair zero-shot acc must be <=5% on every
eval set (invented ops not in pretraining). Exit 1 -> STOP, do not train."""
import json, re, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
OUT = Path("/mnt/hdfs/xwqu/tier2/output")
def pf(t):
    m = re.findall(r"final answer is\s*(-?[\d,\.]+)", t or "", re.I)
    return m[-1].replace(",", "").rstrip(".") if m else None
bad = 0
for tier in "abcd":
    for ev in ["eval_id", "eval_ood"]:
        gold = [re.findall(r"final answer is (-?\d+)", r["output"])[-1]
                for r in json.loads((ROOT / f"data_tier2/tier_{tier}_{ev}.json").read_text())]
        p = OUT / f"predict_zeroshot_{tier}_{ev}/generated_predictions.jsonl"
        preds = [json.loads(l)["predict"] for l in p.open()]
        acc = sum(1 for t, g in zip(preds, gold) if pf(t) == g) / len(gold)
        ok = acc <= 0.05
        bad += 0 if ok else 1
        print(f"zeroshot {tier}/{ev}: acc={acc:.1%} {'OK' if ok else 'LEAK? >5% — STOP'}")
sys.exit(1 if bad else 0)
