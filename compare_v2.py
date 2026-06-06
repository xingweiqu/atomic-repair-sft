"""Build the v2 comparison report from per-condition eval JSONs.

Inputs (any subset):
  --inject-base   base model inject (cleanliness gate, should ~0)
  --inject-floor  injected model inject (learned gate, should ~100%)
  --zeroshot-direct --zeroshot-cot          (condition A)
  --factonly-repair                         (B = injected model on repair, no traj)
  --fact-then-cot                           (C)
  --fact-then-skillcot                      (D)

Emits comparison_v2.md/.json: two gates, per-cell B/C/D final-answer table,
the contrasts, and accept-rates per condition.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

CELLS = ["K-Aug", "K-Abl", "K-Cor", "R-Aug", "R-Abl", "R-Cor", "H-Aug", "H-Abl", "H-Cor", "Clean"]


def load(p):
    return json.loads(p.read_text()) if p and p.exists() else None


def cell_acc(rep, c):
    if not rep:
        return None
    return rep.get("per_cell", {}).get(c, {}).get("final_answer", {}).get("acc")


def overall(rep):
    return rep.get("overall_final", {}).get("acc") if rep else None


def fm(rep, k):
    return rep.get("failure_modes", {}).get(k, {}).get("acc") if rep else None


def pct(x):
    return "n/a" if x is None else f"{x*100:.1f}%"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data_v2/comparison_v2"))
    for n in ["inject-base", "inject-floor", "zeroshot-direct", "zeroshot-cot",
              "factonly-repair", "fact-then-cot", "fact-then-skillcot"]:
        ap.add_argument(f"--{n}", type=Path)
    ap.add_argument("--clean-thresh", type=float, default=0.05)
    ap.add_argument("--floor-thresh", type=float, default=0.90)
    a = ap.parse_args()

    ib = load(a.inject_base); ifl = load(a.inject_floor)
    zd = load(a.zeroshot_direct); zc = load(a.zeroshot_cot)
    fo = load(a.factonly_repair); fc = load(a.fact_then_cot); fs = load(a.fact_then_skillcot)

    base_acc = ib.get("overall", {}).get("acc") if ib else None
    floor_acc = ifl.get("overall", {}).get("acc") if ifl else None
    clean_pass = base_acc is not None and base_acc <= a.clean_thresh
    floor_pass = floor_acc is not None and floor_acc >= a.floor_thresh

    conds = [("A zero-shot direct", zd), ("A zero-shot CoT", zc),
             ("B Fact-only", fo), ("C Fact→CoT", fc), ("D Fact→Skill+CoT", fs)]

    L = ["# Atomic-repair v2 — comparison (9 atomic capacities)", "",
         "## Gates", "",
         f"- **Cleanliness** (base inject ≤ {pct(a.clean_thresh)}): {pct(base_acc)} → "
         f"{'PASS ✅' if clean_pass else ('FAIL ⚠️' if base_acc is not None else 'n/a')}",
         f"- **Learned floor** (injected inject ≥ {pct(a.floor_thresh)}): {pct(floor_acc)} → "
         f"{'PASS ✅' if floor_pass else ('FAIL ⚠️ do NOT interpret repair' if floor_acc is not None else 'n/a')}",
         "", "## Final-answer by condition (overall)", "", "| condition | overall |", "|---|---|"]
    for name, r in conds:
        L.append(f"| {name} | {pct(overall(r))} |")

    L += ["", "## Per-cell final-answer (the story: which capacities get repaired)", "",
          "| cell | B Fact-only | C Fact→CoT | D Fact→Skill+CoT |", "|---|---|---|---|"]
    for c in CELLS:
        L.append(f"| {c} | {pct(cell_acc(fo,c))} | {pct(cell_acc(fc,c))} | {pct(cell_acc(fs,c))} |")

    L += ["", "## Contrasts", "",
          f"- Does adding knowledge alone help? **B vs zero-shot**: {pct(overall(fo))} vs {pct(overall(zc))}",
          f"- Does CoT traj help use known facts? **C vs B**: {pct(overall(fc))} vs {pct(overall(fo))}",
          f"- Does the skill label add over CoT? **D vs C**: {pct(overall(fs))} vs {pct(overall(fc))}",
          "", "## Failure modes by condition", "",
          "| condition | Clean over-repair | K-Cor accept | R-Cor accept | H-Cor accept |",
          "|---|---|---|---|---|"]
    for name, r in conds:
        L.append(f"| {name} | {pct(fm(r,'over_repair_clean'))} | {pct(fm(r,'kcor_accept'))} | "
                 f"{pct(fm(r,'rcor_accept'))} | {pct(fm(r,'hcor_accept'))} |")

    a.out.with_suffix(".md").write_text("\n".join(L))
    a.out.with_suffix(".json").write_text(json.dumps({
        "gates": {"clean": {"acc": base_acc, "pass": clean_pass},
                  "floor": {"acc": floor_acc, "pass": floor_pass}},
        "overall": {name: overall(r) for name, r in conds},
        "per_cell": {c: {"B": cell_acc(fo, c), "C": cell_acc(fc, c), "D": cell_acc(fs, c)} for c in CELLS},
    }, indent=2, ensure_ascii=False))
    print("wrote", a.out.with_suffix(".md"))


if __name__ == "__main__":
    main()
