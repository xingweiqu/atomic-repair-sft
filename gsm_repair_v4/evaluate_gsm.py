"""Score all v4 (GSM) predictions and build the v3-vs-v4 selective matrix + transfer check.

Reuses v3's actionized parsing / strict-abstain judge (scenario_repair_v3.evaluate_v3) so the
two domains are scored by the SAME logic; only the final-answer normaliser differs (numeric for
GSM vs string for the synthetic world), which is passed in as `matchfn`.

Conditions (from data_v4/predict_outputs/predict_<name>/generated_predictions.jsonl):
  diagnosis_base   base instruct, no repair training (lower anchor; mostly non-JSON)
  scaffold_only    format-only SFT (FLOOR baseline for gains)
  actionized_full  trained on all policies (upper anchor)
  targeted_<op>    trained on ONLY that operator's data  -> matrix rows
  random_<op>      same-size random repair data          -> control (volume)
  wrongtarget_<op> mislabeled-target data                -> control (label signal)
  transfer_base / transfer_verify_step  un-perturbed GSM test (repair must not hurt base task)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_repair_v3.evaluate_v3 import parse, is_abstain_strict, final as final_field, norm

OPS = ["verify_step", "override_wrong_claim", "recompute", "retrieve_or_abstain"]
FINAL_RE = re.compile(r"final answer is\s*\$?(-?\d[\d,]*\.?\d*)", re.I)
NUM_RE = re.compile(r"-?\d[\d,]*\.?\d*")


def numkey(s):
    """Normalise a numeric answer: strip $/commas, parse, collapse 18.0->18."""
    if s is None:
        return None
    m = NUM_RE.search(str(s).replace(",", "").replace("$", ""))
    if not m:
        return None
    try:
        f = float(m.group(0))
        return int(f) if f == int(f) else round(f, 4)
    except Exception:
        return None


def strkey(s):
    return norm(s)


def load_jsonl(p):
    return [json.loads(l) for l in Path(p).open() if l.strip()]


def acc(v):
    return round(sum(v) / len(v), 4) if v else None


def score_repair(pred_path, src, matchfn):
    preds = [r.get("predict", "") for r in load_jsonl(pred_path)]
    n = min(len(preds), len(src))
    per_policy = defaultdict(list)
    false_keep, clean_over = [], []
    for i in range(n):
        r, raw = src[i], preds[i]
        o, pol = parse(raw), r["policy"]
        if pol == "retrieve_or_abstain":
            per_policy[pol].append(int(is_abstain_strict(o, raw)))
            continue
        g = matchfn(r["gold_answer"])
        t = matchfn(r["tentative_answer"])
        fa = matchfn(final_field(o, raw))
        per_policy[pol].append(int(fa is not None and fa == g))
        if pol == "keep_answer":
            clean_over.append(int(fa is not None and fa != t))
        else:
            kept = (fa is not None and fa == t) or (o and norm(o.get("update_decision")) == "keep")
            false_keep.append(int(bool(kept)))
    return {"overall": acc([x for v in per_policy.values() for x in v]),
            "per_policy": {p: {"n": len(v), "acc": acc(v)} for p, v in per_policy.items()},
            "false_keep": acc(false_keep), "clean_over_repair": acc(clean_over)}


def score_transfer(pred_path, src):
    preds = [r.get("predict", "") for r in load_jsonl(pred_path)]
    n = min(len(preds), len(src))
    hit, no_final = [], 0
    for i in range(n):
        raw = preds[i] or ""
        gold = numkey(src[i]["output"])
        m = FINAL_RE.search(raw)
        if m:
            pa = numkey(m.group(1))
        else:
            no_final += 1
            nums = NUM_RE.findall(raw.replace(",", ""))
            pa = numkey(nums[-1]) if nums else None
        hit.append(int(pa is not None and pa == gold))
    return {"acc": acc(hit), "n": n, "no_final_line": no_final}


def pol_acc(rep, pol):
    d = (rep or {}).get("per_policy", {}).get(pol)
    return d["acc"] if d else None


def pct(x):
    return "n/a" if x is None else f"{x*100:.0f}"


def gain(x, b):
    return None if (x is None or b is None) else round(x - b, 4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--v4_pred", type=Path, default=Path("data_v4/predict_outputs"))
    ap.add_argument("--v4_eval", type=Path, default=Path("data_v4/repair_eval.jsonl"))
    ap.add_argument("--v4_transfer", type=Path, default=Path("data_v4/transfer_eval.json"))
    ap.add_argument("--v3_pred", type=Path, default=Path("data_v3_1/predict_outputs"))
    ap.add_argument("--v3_eval", type=Path, default=Path("data_v3_1/repair_eval.jsonl"))
    ap.add_argument("--out", type=Path, default=Path("data_v4/results/comparison_v4"))
    a = ap.parse_args()

    src4 = load_jsonl(a.v4_eval)

    def v4(name):
        p = a.v4_pred / f"predict_{name}" / "generated_predictions.jsonl"
        return score_repair(p, src4, numkey) if p.exists() else None

    base = v4("diagnosis_base")
    floor = v4("scaffold_only")
    full = v4("actionized_full")
    targeted = {op: v4(f"targeted_{op}") for op in OPS}
    random_ = {op: v4(f"random_{op}") for op in OPS}
    wrong = {op: v4(f"wrongtarget_{op}") for op in OPS}

    transfer = {}
    tsrc = json.loads(a.v4_transfer.read_text())
    for cond in ("base", "verify_step"):
        p = a.v4_pred / f"predict_transfer_{cond}" / "generated_predictions.jsonl"
        transfer[cond] = score_transfer(p, tsrc) if p.exists() else None

    # v3.1 side-by-side (same scorer, string match)
    v3 = {}
    if a.v3_eval.exists():
        src3 = load_jsonl(a.v3_eval)

        def v3f(name):
            p = a.v3_pred / f"predict_{name}" / "generated_predictions.jsonl"
            return score_repair(p, src3, strkey) if p.exists() else None
        v3 = {"floor": v3f("scaffold_only"), **{op: v3f(f"targeted_{op}") for op in OPS}}

    L = ["# Scenario-Repair v4 (GSM8K) — Comparison & v3↔v4 Selective Matrix", ""]
    L += ["## Exp 1: Repair conditions (final-answer accuracy)", "",
          "| condition | overall | false-keep | clean over-repair |", "|---|---|---|---|"]
    for nm, rep in [("diagnosis_base (base, no repair)", base),
                    ("scaffold_only (FLOOR)", floor),
                    ("actionized_full (all policies)", full)]:
        if rep:
            L.append(f"| {nm} | {pct(rep['overall'])}% | {pct(rep['false_keep'])}% | "
                     f"{pct(rep['clean_over_repair'])}% |")

    L += ["", "## Exp 2: Selective Repair Matrix — gain over scaffold_only FLOOR (%)", "",
          "Rows = trained on ONLY this operator. Cols = eval on this operator. Diagonal = Targeted Gain.", "",
          "| trained \\ eval | " + " | ".join(o[:10] for o in OPS) + " |",
          "|" + "---|" * (len(OPS) + 1)]
    sel = {}
    for tp in OPS:
        rep, cells, diag, off = targeted[tp], [], None, []
        for ep in OPS:
            g = gain(pol_acc(rep, ep), pol_acc(floor, ep))
            cells.append("n/a" if g is None else f"{g*100:+.0f}")
            if ep == tp:
                diag = g
            elif g is not None:
                off.append(g)
        if diag is not None:
            sel[tp] = {"gain": diag, "sel": round(diag - (sum(off) / len(off) if off else 0), 4)}
        L.append(f"| {tp[:16]} | " + " | ".join(cells) + " |")
    L += ["", "| operator | targeted gain | selectivity |", "|---|---|---|"]
    for tp in OPS:
        s = sel.get(tp, {})
        L.append(f"| {tp} | {pct(s.get('gain'))}% | {pct(s.get('sel'))}% |")

    L += ["", "## Controls (accuracy on the operator's own eval cell)", "",
          "| operator | targeted | same-size random | wrong-target | floor |", "|---|---|---|---|---|"]
    for tp in OPS:
        L.append(f"| {tp} | {pct(pol_acc(targeted[tp], tp))}% | {pct(pol_acc(random_[tp], tp))}% | "
                 f"{pct(pol_acc(wrong[tp], tp))}% | {pct(pol_acc(floor, tp))}% |")

    L += ["", "## Transfer check — un-perturbed GSM8K test (repair must not hurt base task)", "",
          "| model | GSM acc | n | no-final-line (trunc.) |", "|---|---|---|---|"]
    for cond in ("base", "verify_step"):
        t = transfer[cond]
        if t:
            L.append(f"| {cond} | {pct(t['acc'])}% | {t['n']} | {t['no_final_line']} |")

    if v3 and v3.get("floor"):
        L += ["", "## v3 (synthetic) ↔ v4 (GSM) — Targeted Gain on shared operators", "",
              "Same scorer; gain = targeted − scaffold_only floor, on the operator's own eval cell.", "",
              "| operator | v3 floor→targeted | v3 gain | v4 floor→targeted | v4 gain |",
              "|---|---|---|---|---|"]
        for op in OPS:
            v3t, v3f_ = pol_acc(v3.get(op), op), pol_acc(v3["floor"], op)
            v4t, v4f_ = pol_acc(targeted[op], op), pol_acc(floor, op)
            L.append(f"| {op} | {pct(v3f_)}→{pct(v3t)} | {pct(gain(v3t, v3f_))} | "
                     f"{pct(v4f_)}→{pct(v4t)} | {pct(gain(v4t, v4f_))} |")
        L += ["", "_Both diagonals lighting up across two domains = the repair-induction "
              "framework transfers, not a synthetic-world artifact._"]

    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.with_suffix(".md").write_text("\n".join(L))
    dump = {"v4": {"base": base, "floor": floor, "full": full, "targeted": targeted,
                   "random": random_, "wrongtarget": wrong, "transfer": transfer, "selectivity": sel},
            "v3": v3}
    a.out.with_suffix(".json").write_text(json.dumps(dump, indent=2, ensure_ascii=False))
    print("wrote", a.out.with_suffix(".md"))
    print("\n".join(L))


if __name__ == "__main__":
    main()
