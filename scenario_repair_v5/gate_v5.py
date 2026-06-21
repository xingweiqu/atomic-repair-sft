"""v5 HARD GATE (STEP 2.1). Must PASS before any training. Read-only.

Checks:
  - oracle triple overlap eval∈train  (target 0)
  - world size
  - entity balance: false-share spread across tails
  - shortcut gate: TF-IDF predicting update_decision from the ENTITY-MASKED problem,
    5-fold balanced accuracy < 0.65 (the decision must not be a surface marker)
Exit 1 if any fails.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gsm_repair_v4.validate_gsm import _bow


def load(p):
    return [json.loads(l) for l in Path(p).open() if l.strip()]


def triples(it):
    return [tuple(str(x).lower() for x in t) for t in it["gold_symbolic_facts"]]


def mask(it):
    t = it["problem"]
    ents = set()
    for tri in it["gold_symbolic_facts"]:
        ents.update(str(x) for x in tri)
    for k in ("planted_wrong_answer", "tentative_answer", "gold_answer"):
        if it.get(k):
            ents.add(str(it[k]))
    for e in sorted(ents, key=len, reverse=True):
        t = re.sub(re.escape(e), "ENT", t)
    return t


def main():
    d = Path("data_v5")
    tr, ev = load(d / "repair_train.jsonl"), load(d / "repair_eval.jsonl")
    fails = []

    TR = set(x for it in tr for x in triples(it))
    EV = [x for it in ev for x in triples(it)]
    ov = sum(1 for x in EV if x in TR)
    if ov > 0:
        fails.append(f"triple overlap eval∈train = {ov} (must be 0)")

    # entity balance
    gold_ct, false_ct = Counter(), Counter()
    for r in tr:
        if r["gold_answer"]:
            gold_ct[r["gold_answer"]] += 1
        if r["planted_wrong_answer"]:
            false_ct[r["planted_wrong_answer"]] += 1
    shares = [false_ct[t] / (gold_ct[t] + false_ct[t]) for t in (set(gold_ct) | set(false_ct))
              if gold_ct[t] + false_ct[t] >= 4]
    import statistics
    bal_med = statistics.median(shares) if shares else None

    # shortcut gate
    X = [mask(it) for it in tr + ev]
    y = [it["update_decision"] for it in tr + ev]
    masked = _bow(X, y, (1, 1))
    raw = _bow([it["problem"] for it in tr + ev], y, (1, 1))
    gate_pass = masked is not None and masked < 0.65
    if not gate_pass:
        fails.append(f"shortcut gate masked balanced-acc = {masked} (must be <0.65)")

    status = "PASS" if not fails else "FAIL"
    rep = {
        "status": status, "failures": fails,
        "world": {"train_items": len(tr), "eval_items": len(ev),
                  "unique_triples_train": len(TR), "eval_triples": len(EV)},
        "triple_overlap_eval_in_train": ov,
        "entity_balance_false_share_median": round(bal_med, 3) if bal_med else None,
        "shortcut": {"masked_balanced_acc": round(masked, 4) if masked else None,
                     "raw_balanced_acc": round(raw, 4) if raw else None,
                     "gate_pass_<0.65": gate_pass},
    }
    (d / "gate_v5.json").write_text(json.dumps(rep, indent=2))
    print(json.dumps(rep, indent=2))
    if status != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
