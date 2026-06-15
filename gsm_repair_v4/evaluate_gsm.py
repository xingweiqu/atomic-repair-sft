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
    hit, answered_hit, no_answer = [], [], 0
    for i in range(n):
        raw = preds[i] or ""
        # gold: the reference's final-answer LINE (not the first number in the reasoning)
        gm = FINAL_RE.search(src[i]["output"])
        gold = numkey(gm.group(1)) if gm else numkey(src[i]["output"])
        # pred: the LAST "final answer is N" if present (avoid an in-think mention), else a
        # final_answer JSON field (repair-trained ckpts drift to actionized JSON on plain
        # tasks). Either of those = the model actually committed to an answer.
        answered = True
        pm = FINAL_RE.findall(raw)
        if pm:
            pa = numkey(pm[-1])
        else:
            o = parse(raw)
            if o and o.get("final_answer") is not None:
                pa = numkey(o["final_answer"])
            else:
                answered, no_answer = False, no_answer + 1
                nums = NUM_RE.findall(raw.replace(",", ""))
                pa = numkey(nums[-1]) if nums else None
        h = int(pa is not None and pa == gold)
        hit.append(h)
        if answered:
            answered_hit.append(h)
    # acc = accuracy over ALL items; answered_acc = accuracy when the model committed to an
    # answer (isolates ARITHMETIC ability from BEHAVIOURAL DRIFT into repair mode).
    return {"acc": acc(hit), "answered_acc": acc(answered_hit),
            "answered_n": len(answered_hit), "n": n, "no_answer": no_answer}


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
    ap.add_argument("--floor", default="scaffold_conv",
                    help="floor run name (scaffold_conv = convergent; scaffold_only = underfit/legacy)")
    ap.add_argument("--out", type=Path, default=Path("data_v4/results/comparison_v4"))
    a = ap.parse_args()

    src4 = load_jsonl(a.v4_eval)

    def v4(name):
        p = a.v4_pred / f"predict_{name}" / "generated_predictions.jsonl"
        return score_repair(p, src4, numkey) if p.exists() else None

    base = v4("diagnosis_base")
    floor = v4(a.floor)
    full = v4("actionized_full")
    targeted = {op: v4(f"targeted_{op}") for op in OPS}
    random_ = {op: v4(f"random_{op}") for op in OPS}
    wrong = {op: v4(f"wrongtarget_{op}") for op in OPS}

    transfer = {}
    tsrc = json.loads(a.v4_transfer.read_text())
    for cond in ("base", "verify_step", "actionized_full"):
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
                    (f"{a.floor} (FLOOR)", floor),
                    ("actionized_full (all policies)", full)]:
        if rep:
            L.append(f"| {nm} | {pct(rep['overall'])}% | {pct(rep['false_keep'])}% | "
                     f"{pct(rep['clean_over_repair'])}% |")

    L += ["", f"## Exp 2: Selective Repair Matrix — gain over {a.floor} FLOOR (%)", "",
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
          "`acc` = over all 300 items; `answered acc` = when the model committed to an answer "
          "(isolates arithmetic ability from drift into repair mode); `no-answer` = items where "
          "the repair-trained ckpt produced a diagnosis/JSON with no committed answer.", "",
          "| model | acc | answered acc | answered n | no-answer |", "|---|---|---|---|---|"]
    for cond in ("base", "verify_step", "actionized_full"):
        t = transfer[cond]
        if t:
            L.append(f"| {cond} | {pct(t['acc'])}% | {pct(t['answered_acc'])}% | "
                     f"{t['answered_n']} | {t['no_answer']} |")

    if v3 and v3.get("floor"):
        L += ["", "## v3 (synthetic) ↔ v4 (GSM) — Targeted Gain on shared operators", "",
              "Same scorer; gain = targeted − floor (v3: scaffold_only; v4: convergent scaffold_conv), "
              "on the operator's own eval cell.", "",
              "| operator | v3 floor→targeted | v3 gain | v4 floor→targeted | v4 gain |",
              "|---|---|---|---|---|"]
        for op in OPS:
            v3t, v3f_ = pol_acc(v3.get(op), op), pol_acc(v3["floor"], op)
            v4t, v4f_ = pol_acc(targeted[op], op), pol_acc(floor, op)
            L.append(f"| {op} | {pct(v3f_)}→{pct(v3t)} | {pct(gain(v3t, v3f_))} | "
                     f"{pct(v4f_)}→{pct(v4t)} | {pct(gain(v4t, v4f_))} |")
        L += ["", "_v3 (synthetic) is operator-SELECTIVE (diagonal spikes). v4 (GSM), on a CONVERGENT "
              "floor, shows small positive compute-cell gains and ZERO abstain gain — the real "
              "structure is at the decision level (see decision_analysis_conv.md)._"]

    L += ["", f"## 结论解读 — 收敛 floor 下的三层真相 (FLOOR = {a.floor})", "",
          "> 本表 FLOOR = scaffold_conv（收敛, parse 100%）。旧 scaffold_only（欠拟合, loss 2.53, "
          "parse 0.68–0.80）评分是格式崩溃产物, 会系统性反转结论符号, 已弃用为基线。", "",
          "- **final-acc 层（本表）**: 收敛 floor 下计算类对角线全部转正（verify +4 / override +10 / "
          "recompute +8）, abstain gain 归零（floor 也 100%）。selectivity 接近 0 → v4 非 operator-selective。",
          "- **decision 层（decision_analysis_conv.md）**: 真正结构在此 —— targeted 把 recompute/override 的"
          "「抵抗错误值」从 floor 0.60/0.64 拉到 0.98; 但任一 targeted 都泛化拉高（非 operator-specific）。",
          "- **arithmetic 层**: 所有 run 决策对之后的重算正确率恒为 ~0.30–0.46, 谁训都不提升。",
          "",
          "**论点**: repair / operator-induction 在真实算术域注入的是一个**通用的「抵抗错误值」修复决策**, "
          "**不注入底层算术**。final-acc 只小幅正且 selectivity 低, 因为决策增益被 base 算术上限压住。"
          "abstain 在收敛 floor 下 gain 归零, 确认是「见过格式即会」的格式技能（降为正对照）。",
          "**v3↔v4**: v3（合成, base 全不会）operator-selective; v4（GSM, base 已会算术）泛化决策诱导 + 算术上限。"
          "共同点 = repair 注入决策/轨迹而非底层能力。",
          "**Transfer**: 单 operator(verify_step) 30% 普通题漂移进修复模式不作答; 混合(actionized_full)漂移降到 17%; "
          "两者作答时算术 ≈ base（未损害底层计算）。"]

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
