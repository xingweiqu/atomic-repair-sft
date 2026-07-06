#!/usr/bin/env python3
"""R-9 token-length gate (exact, server-side): p95(prompt+target tokens) vs cutoff 1024.
Exit 1 if p95 > 0.9*cutoff. Usage: python3 learnability_family/gate_token_audit.py --model <path>"""
import argparse, json, sys
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument("--model", required=True); ap.add_argument("--cutoff", type=int, default=1024)
a = ap.parse_args()
from transformers import AutoTokenizer
tok = AutoTokenizer.from_pretrained(a.model)
bad = 0
for f in sorted(Path("data_tier2").glob("tier_*_train*.json")):
    rows = json.loads(f.read_text())
    L = sorted(len(tok(r["instruction"] + "\n" + r["input"] + r["output"]).input_ids) for r in rows)
    p95 = L[int(0.95 * len(L))]
    ok = p95 <= 0.9 * a.cutoff
    bad += 0 if ok else 1
    print(f"{f.name}: p95={p95} cutoff={a.cutoff} {'OK' if ok else 'OVER'}")
sys.exit(1 if bad else 0)
