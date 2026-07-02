"""D-2 regression gate: the wrapper's HISTORICAL config (final=lenient chain,
abstain=strict) must reproduce numbers already published in the repo reports.
"Only re-packaged, nothing re-judged." Any mismatch beyond rounding (±1pp) -> exit 1.

Targets (all traceable):
  [scenario-repair-v4] data_v3_1/REPORT_v3_1_zh.md  §2/§3/§4  (v3.1 strict-judge tables)
  [scenario-repair-v4] data_v4/results/comparison_v4.md  Exp-1  (v4 overall)

Writes qc/LOOP1_JUDGE_REGRESSION.md.
"""
from __future__ import annotations

import subprocess
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ledger.judge import load_items, load_preds, score_run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def git_lines(branch, path):
    out = subprocess.run(["git", "show", f"{branch}:{path}"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [l for l in out.splitlines() if l.strip()]


def pct(x):
    return round(100 * x)


def acc(vs):
    return sum(vs) / len(vs) if vs else None


def per_policy_hist(items, verdicts):
    by = defaultdict(list)
    for it, v in zip(items, verdicts):
        by[it["policy"]].append(v["correct_hist"])
    return {p: pct(acc(vs)) for p, vs in by.items()}


def main():
    checks = []  # (name, got, expect)

    # ---------- v3.1 (domain v3_1, string match) ----------
    ev31 = load_items(ROOT / "data_v3_1/repair_eval.jsonl")

    def v31(run):
        return score_run(ev31, load_preds(
            ROOT / f"data_v3_1/predict_outputs/predict_{run}/generated_predictions.jsonl"), "v3_1")

    # REPORT_v3_1_zh.md §2: Fact-only overall strict = 39%; scaffold_only overall = 16%
    fo = v31("factonly")
    checks.append(("v3.1 factonly overall", pct(acc([v["correct_hist"] for v in fo])), 39))
    so = v31("scaffold_only")
    checks.append(("v3.1 scaffold_only overall", pct(acc([v["correct_hist"] for v in so])), 16))

    # §2 per-policy floors: scaffold_only override 22 / verify_bridge 3 / verify_step 0
    #                       / recompute 13 / use_support 30 / abstain 12
    pp = per_policy_hist(ev31, so)
    for pol, exp in [("override_wrong_claim", 22), ("verify_bridge", 3), ("verify_step", 0),
                     ("recompute", 13), ("use_provided_support", 30), ("retrieve_or_abstain", 12)]:
        checks.append((f"v3.1 scaffold_only {pol}", pp[pol], exp))

    # §4 targeted diagonal: 95 / 78 / 93 / 100 / 99 / 100
    for pol, exp in [("override_wrong_claim", 95), ("verify_bridge", 78), ("verify_step", 93),
                     ("recompute", 100), ("use_provided_support", 99), ("retrieve_or_abstain", 100)]:
        vd = per_policy_hist(ev31, v31(f"targeted_{pol}"))
        checks.append((f"v3.1 targeted_{pol} diagonal", vd[pol], exp))

    # ---------- v4 (numeric match) ----------
    ev4 = load_items(ROOT / "data_v4/repair_eval.jsonl")

    def v4(run):
        return score_run(ev4, load_preds(
            ROOT / f"data_v4/predict_outputs/predict_{run}/generated_predictions.jsonl"), "v4")

    # comparison_v4.md Exp-1: diagnosis_base 33 / scaffold_conv 56 / actionized_full 62
    for run, exp in [("diagnosis_base", 33), ("scaffold_conv", 56), ("actionized_full", 62)]:
        checks.append((f"v4 {run} overall", pct(acc([v["correct_hist"] for v in v4(run)])), exp))

    # ---------- report + gate ----------
    lines = ["# Loop 1 — judge wrapper regression (D-2 gate)", "",
             "Historical config = (final: lenient chain, abstain: strict). Tolerance ±1pp.",
             "Targets: `data_v3_1/REPORT_v3_1_zh.md` §2/§4, `data_v4/results/comparison_v4.md` Exp-1.", "",
             "| check | wrapper | historical | Δ | ok |", "|---|---|---|---|---|"]
    fails = 0
    for name, got, exp in checks:
        d = got - exp
        ok = abs(d) <= 1
        fails += 0 if ok else 1
        lines.append(f"| {name} | {got} | {exp} | {d:+d} | {'✅' if ok else '❌'} |")
    lines += ["", f"**{len(checks) - fails}/{len(checks)} PASS**"
              + ("" if fails == 0 else f" — {fails} FAIL → 停(D-2:不一致即停)")]
    out = ROOT / "qc/LOOP1_JUDGE_REGRESSION.md"
    out.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
