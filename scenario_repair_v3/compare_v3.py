"""Build the v3 comparison report: selective repair matrix + curriculum + controls.

Inputs: a directory of per-condition eval JSONs produced by evaluate_v3.py, named:
  factonly.json, actionized_full.json, cot.json,
  targeted_<policy>.json  (Exp 2: trained on only that policy's data)
  cumulative_M<k>.json    (Exp 3)
  random_<policy>.json, wrongtarget_<policy>.json  (controls)

Outputs results/comparison_v3.md + .json with:
  - Selective Repair Matrix: rows = trained-on policy, cols = eval policy,
    value = gain over Fact-only on that eval policy.
  - Targeted Repair Gain (diagonal) and Selectivity per policy.
  - Cumulative curve (per-policy acc as stages accumulate).
  - Controls: targeted vs random (same size), targeted vs wrong-target.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_repair_v3 import policies as P

OPS = P.OPERATOR_POLICIES  # the inducible policies (matrix axes)


def load(p):
    return json.loads(p.read_text()) if p and Path(p).exists() else None


def pol_acc(rep, pol):
    if not rep:
        return None
    d = rep.get("per_policy", {}).get(pol)
    return d["acc"] if d else None


def pct(x):
    return "n/a" if x is None else f"{x*100:.0f}"


def gain(x, base):
    return None if (x is None or base is None) else round(x - base, 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reports", type=Path, default=Path("data_v3/reports"))
    ap.add_argument("--out", type=Path, default=Path("data_v3/results/comparison_v3"))
    a = ap.parse_args()
    R = a.reports
    base = load(R / "factonly.json")
    full = load(R / "actionized_full.json")
    cot = load(R / "cot.json")

    L = ["# Scenario-Repair v3 — Comparison & Selective Operator Induction", ""]

    # Exp 1 headline
    L += ["## Experiment 1: Scenario-based Actionized Repair", "",
          "| condition | overall | abstain-correct | false-keep | clean over-repair |",
          "|---|---|---|---|---|"]
    for name, rep in [("Fact-only", base), ("Fact→CoT", cot), ("Fact→Actionized (full)", full)]:
        if rep:
            L.append(f"| {name} | {pct(rep['overall_final'])}% | {pct(rep.get('abstain_correct_rate'))}% | "
                     f"{pct(rep.get('false_keep_rate'))}% | {pct(rep.get('clean_over_repair_rate'))}% |")

    # Exp 2: selective repair matrix
    targeted = {pol: load(R / f"targeted_{pol}.json") for pol in OPS}
    L += ["", "## Experiment 2: Selective Repair Matrix (gain over Fact-only, %)", "",
          "Rows = trained on ONLY this policy's data. Columns = eval on this policy. "
          "Diagonal = Targeted Repair Gain.", "",
          "| trained \\ eval | " + " | ".join(p[:10] for p in OPS) + " |",
          "|" + "---|" * (len(OPS) + 1)]
    selectivity = {}
    for tp in OPS:
        rep = targeted[tp]
        cells = []
        diag = None
        offdiag = []
        for ep in OPS:
            g = gain(pol_acc(rep, ep), pol_acc(base, ep))
            cells.append("n/a" if g is None else f"{g*100:+.0f}")
            if ep == tp:
                diag = g
            elif g is not None:
                offdiag.append(g)
        if diag is not None:
            sel = round(diag - (sum(offdiag) / len(offdiag) if offdiag else 0), 4)
            selectivity[tp] = {"targeted_gain": diag, "selectivity": sel}
        L.append(f"| {tp[:14]} | " + " | ".join(cells) + " |")

    L += ["", "### Targeted Repair Gain & Selectivity", "",
          "| policy | targeted gain | selectivity |", "|---|---|---|"]
    for tp in OPS:
        s = selectivity.get(tp, {})
        tg = s.get("targeted_gain"); se = s.get("selectivity")
        L.append(f"| {tp} | {'n/a' if tg is None else f'{tg*100:+.0f}%'} | "
                 f"{'n/a' if se is None else f'{se*100:+.0f}%'} |")
    L += ["", "_Diagonal-dominant matrix + high selectivity ⇒ targeted data is on-target. "
          "If off-diagonal gains are as large (everything rises together), the gain is generic "
          "action-commitment, not selective induction — reported honestly either way._"]

    # Exp 3: cumulative curriculum
    L += ["", "## Experiment 3: Cumulative Curriculum", "",
          "| stage | overall | " + " | ".join(p[:8] for p in P.POLICY_NAMES) + " |",
          "|" + "---|" * (len(P.POLICY_NAMES) + 2)]
    for tag in ["M0"] + [t for t, _ in __import__("scenario_repair_v3.convert_v3",
                                                   fromlist=["CURRICULUM"]).CURRICULUM]:
        rep = base if tag == "M0" else load(R / f"cumulative_{tag}.json")
        if not rep:
            continue
        row = [pct(rep["overall_final"]) + "%"] + [pct(pol_acc(rep, p)) for p in P.POLICY_NAMES]
        L.append(f"| {tag} | " + " | ".join(row) + " |")

    # Controls
    L += ["", "## Controls", "",
          "| policy | targeted | same-size random | wrong-target |", "|---|---|---|---|"]
    for tp in OPS:
        t = pol_acc(targeted[tp], tp)
        r = pol_acc(load(R / f"random_{tp}.json"), tp)
        w = pol_acc(load(R / f"wrongtarget_{tp}.json"), tp)
        L.append(f"| {tp} | {pct(t)}% | {pct(r)}% | {pct(w)}% |")
    L += ["", "_Targeted > random ⇒ on-target data beats mere volume. "
          "Targeted > wrong-target ⇒ the policy label/action carries real signal._"]

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".md").write_text("\n".join(L))
    a.out.with_suffix(".json").write_text(json.dumps(
        {"selectivity": selectivity, "exp1": {
            "factonly": base and base["overall_final"],
            "cot": cot and cot["overall_final"],
            "actionized_full": full and full["overall_final"]}}, indent=2))
    print("wrote", a.out.with_suffix(".md"))


if __name__ == "__main__":
    main()
