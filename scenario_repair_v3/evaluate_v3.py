"""Score one v3 prediction file against repair_eval. Per-policy metrics + abstain.

Final-answer scoring:
  - normal items: normalised exact match vs gold.
  - abstain items (policy retrieve_or_abstain): CORRECT iff the model abstained
    (final_answer null / says it cannot answer / asks for clarification). If the model
    produced a concrete answer (even by luck), it is WRONG — this measures calibration.

Outputs per-policy and per-scenario accuracy, false-keep, accept-rates, abstain
correctness, and stores per-policy hit vectors so compare_v3 can compute
Targeted Repair Gain and Selectivity.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_repair_v3 import policies as P


def load_pred(p):
    return [json.loads(l).get("predict", "") for l in p.open() if l.strip()]


def load_src(p):
    return [json.loads(l) for l in p.open() if l.strip()]


def parse(t):
    try:
        return json.loads(t)
    except Exception:
        m = re.search(r"\{.*\}", t or "", re.S)
        try:
            return json.loads(m.group(0)) if m else None
        except Exception:
            return None


def norm(s):
    if s is None:
        return ""
    return re.sub(r"[\s.]+$", "", str(s).strip()).lower()


def final(o, raw):
    if o and "final_answer" in o:
        return o["final_answer"]
    m = re.search(r"final answer\s*[:\-]\s*(.+)", raw or "", re.I)
    return m.group(1).splitlines()[0] if m else (raw or "").strip().splitlines()[-1] if raw else ""


ABSTAIN_MARKERS = ("clarif", "cannot", "can't", "not enough", "which ", "abstain",
                   "more information", "unclear", "don't know", "unable")


def is_abstain(o, raw):
    fa = o.get("final_answer") if o else None
    if fa is None or norm(fa) in ("", "null", "none"):
        return True
    if o and norm(o.get("update_decision")) == "retrieve_or_abstain":
        return True
    return any(m in (raw or "").lower() for m in ABSTAIN_MARKERS)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pred", type=Path, required=True)
    ap.add_argument("--eval-source", type=Path, default=Path("data_v3/repair_eval.jsonl"))
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    P_ = load_pred(a.pred)
    S = load_src(a.eval_source)
    n = min(len(P_), len(S))

    per_policy = defaultdict(list)        # policy -> 0/1 final correct
    per_scenario = defaultdict(list)
    policy_choice = defaultdict(list)     # policy -> chose correct update_policy?
    false_keep, tent_copy = [], []
    accept = defaultdict(list)            # failure_type Cor -> accepted planted wrong
    abstain_correct, overrepair_clean = [], []

    for i in range(n):
        r = S[i]
        o = parse(P_[i])
        pol = r["policy"]
        raw = P_[i]
        if pol == "retrieve_or_abstain":
            ok = int(is_abstain(o, raw))
            abstain_correct.append(ok)
            per_policy[pol].append(ok)
            per_scenario[r["scenario_family"]].append(ok)
            continue
        g = norm(r["gold_answer"])
        t = norm(r["tentative_answer"])
        fa = norm(final(o, raw))
        ok = int(fa == g)
        per_policy[pol].append(ok)
        per_scenario[r["scenario_family"]].append(ok)
        if o and "update_policy" in o:
            policy_choice[pol].append(int(o["update_policy"] == pol))
        # behavioural
        if pol == "keep_answer":
            overrepair_clean.append(int(fa != t))
        else:
            # false-keep: model kept the wrong tentative on an item that needed update
            kept = (fa == t) or (o and norm(o.get("update_decision")) == "keep")
            false_keep.append(int(bool(kept)))
            tent_copy.append(int(fa == t and fa != g))
        if r["failure_type"].endswith("Cor") and r.get("planted_wrong_answer") is not None:
            accept[r["failure_type"]].append(int(fa == norm(r["planted_wrong_answer"])))

    def acc(v):
        return round(sum(v) / len(v), 4) if v else None

    rep = {
        "pred": str(a.pred),
        "overall_final": acc([x for v in per_policy.values() for x in v]),
        "per_policy": {p: {"n": len(v), "acc": acc(v)} for p, v in sorted(per_policy.items())},
        "per_scenario": {s: {"n": len(v), "acc": acc(v)} for s, v in sorted(per_scenario.items())},
        "policy_choice_acc": {p: acc(v) for p, v in sorted(policy_choice.items())},
        "false_keep_rate": acc(false_keep),
        "tentative_copy_rate": acc(tent_copy),
        "clean_over_repair_rate": acc(overrepair_clean),
        "abstain_correct_rate": acc(abstain_correct),
        "accept_rate": {k: acc(v) for k, v in sorted(accept.items())},
        # per-policy hit vectors for Targeted Repair Gain / Selectivity in compare_v3
        "per_policy_vectors": {p: v for p, v in per_policy.items()},
    }
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(json.dumps(rep, indent=2, ensure_ascii=False))
    print(f"[{a.pred.parent.name or a.pred.stem}] overall={rep['overall_final']} "
          f"abstain={rep['abstain_correct_rate']} false_keep={rep['false_keep_rate']} -> {a.out}")


if __name__ == "__main__":
    main()
