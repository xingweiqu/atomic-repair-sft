#!/usr/bin/env python3
"""P2a H1: freeze stage-1 (dose-60) per-cell component orderings as predictions
for dose-600/2000 orderings; score stage-2 against them (Spearman, per-cell,
median over 16 cells). Frozen rule (PREREG_p2a_dose):
  component score in a cell = mean over epochs {2,4} of R = S(arm,cell) - S(base,cell)
  ranking = descending; ties broken by component name (deterministic).

  freeze          write prescription/p2a_predictions_frozen.json from dose-60 scores
  score --dose N  Spearman(predicted ranking, observed dose-N ranking) per cell
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

COMPS = ["d0_replay", "d1_format", "d2_verify", "d3_revise", "d5_provenance", "d6_abstain"]
P1S = ROOT / "prescription/p1/p1_scores.json"
FROZEN = ROOT / "prescription/p2a_predictions_frozen.json"


def cell_scores(dose):
    P = json.loads(P1S.read_text())
    base = P["BASE"]["cell_table"]
    out = {}
    for cell in sorted(base):
        sc = {}
        for c in COMPS:
            rs = []
            for e in (2, 4):
                tag = f"p2a_{c}_{dose}_e{e}"
                if tag not in P:
                    return None
                rs.append(P[tag]["cell_table"][cell] - base[cell])
            sc[c] = sum(rs) / len(rs)
        out[cell] = sc
    return out


def ranking(sc):
    return sorted(COMPS, key=lambda c: (-sc[c], c))


def cmd_freeze(_):
    cs = cell_scores(60)
    assert cs, "dose-60 scores incomplete"
    pred = {cell: ranking(sc) for cell, sc in cs.items()}
    FROZEN.write_text(json.dumps(
        dict(rule="mean over epochs {2,4} of R vs base, descending, ties by name",
             source_dose=60, predicts_doses=[600, 2000], per_cell_ranking=pred,
             raw_scores={c: {k: round(v, 4) for k, v in sc.items()}
                         for c, sc in cs.items()}), indent=1))
    print(f"frozen {len(pred)} cell rankings -> {FROZEN.name}")


def spearman(a, b):
    n = len(a)
    ra = {c: i for i, c in enumerate(a)}
    rb = {c: i for i, c in enumerate(b)}
    d2 = sum((ra[c] - rb[c]) ** 2 for c in a)
    return 1 - 6 * d2 / (n * (n * n - 1))


def cmd_score(args):
    fr = json.loads(FROZEN.read_text())
    cs = cell_scores(args.dose)
    assert cs, f"dose-{args.dose} scores incomplete"
    rhos = {}
    for cell, sc in cs.items():
        rhos[cell] = round(spearman(fr["per_cell_ranking"][cell], ranking(sc)), 4)
    med = sorted(rhos.values())[len(rhos) // 2]
    print(json.dumps(dict(dose=args.dose, per_cell_rho=rhos, median_rho=med), indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["freeze", "score"])
    ap.add_argument("--dose", type=int, default=600)
    a = ap.parse_args()
    {"freeze": cmd_freeze, "score": cmd_score}[a.cmd](a)
