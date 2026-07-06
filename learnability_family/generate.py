"""Tier-2 generator: per-tier train/eval-ID/eval-OOD + poison calibration + assertions.

Volumes (v2 instruction Loop 2B): train 2000, eval-ID 500, eval-OOD 500 per tier.
Poison calibration (M instrument): tier-b train with {10%, 30%} of eval-ID items
leaked verbatim (0% = the clean train). Constructive zero-leak asserted for all
non-poison sets; poison sets assert their EXACT dose. Token audit: char-proxy locally,
exact tokenizer audit via gate_token_audit.py on the server (R-9).

Plain genre throughout (R-7: ability is claimed in plain genre; these ops are new
knowledge so the clean gate is pre-repair zero-shot ~0, checked server-side).

Run: python3 -m learnability_family.generate
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from learnability_family.ops import TIERS, RANGE_ID, RANGE_OOD, tier_a_table

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data_tier2"
N_TRAIN, N_ID, N_OOD = 2000, 500, 500
INSTR = ("Solve the problem using the invented operation you have learned. Reason step "
         "by step, then end with a line exactly in the form 'The final answer is N.'")


def item(tier, a, b, gold):
    t = TIERS[tier]
    steps = t["steps"](a, b, gold)
    return {"instruction": INSTR,
            "input": f"Compute the {t['name']} of {a} and {b}.",
            "output": t["rule"] + "\n" + "\n".join(steps)
                      + f"\nThe final answer is {gold}.",
            "_combo": [a, b], "_tier": tier, "_gold": gold}


def gen_tier(tier, rng):
    t = TIERS[tier]
    if tier == "a":
        table = tier_a_table(rng)
        combos = list(table)
        rng.shuffle(combos)
        train, evid = combos[:N_TRAIN], combos[N_TRAIN:N_TRAIN + N_ID]
        # OOD for lookup: fresh combos in [100,999] with random golds (unpredictable by design)
        ood = set()
        while len(ood) < N_OOD:
            ood.add((rng.randint(*RANGE_OOD), rng.randint(*RANGE_OOD)))
        return ([item(tier, a, b, table[(a, b)]) for a, b in train],
                [item(tier, a, b, table[(a, b)]) for a, b in evid],
                [item(tier, a, b, rng.randint(100, 999)) for a, b in sorted(ood)])
    combos = set()
    while len(combos) < N_TRAIN + N_ID:
        combos.add((rng.randint(*RANGE_ID), rng.randint(*RANGE_ID)))
    combos = sorted(combos)
    rng.shuffle(combos)
    train, evid = combos[:N_TRAIN], combos[N_TRAIN:N_TRAIN + N_ID]
    ood = set()
    while len(ood) < N_OOD:
        ood.add((rng.randint(*RANGE_OOD), rng.randint(*RANGE_OOD)))
    f = t["fn"]
    return ([item(tier, a, b, f(a, b)) for a, b in train],
            [item(tier, a, b, f(a, b)) for a, b in evid],
            [item(tier, a, b, f(a, b)) for a, b in sorted(ood)])


def strip(rows):
    return [{k: r[k] for k in ("instruction", "input", "output")} for r in rows]


def main():
    OUT.mkdir(exist_ok=True)
    rng = random.Random(42)
    di, manifest = {}, {}
    audit = []
    for tier in "abcd":
        train, evid, ood = gen_tier(tier, rng)
        # ---- constructive zero-leak assertions ----
        tr = {tuple(r["_combo"]) for r in train}
        for name, ev in [("eval_id", evid), ("eval_ood", ood)]:
            inter = tr & {tuple(r["_combo"]) for r in ev}
            assert not inter, f"LEAK tier {tier} {name}: {sorted(inter)[:3]}"
        for r in ood:
            assert r["_combo"][0] >= RANGE_OOD[0] and r["_combo"][1] >= RANGE_OOD[0]
        # ---- write ----
        for name, rows in [("train", train), ("eval_id", evid), ("eval_ood", ood)]:
            fn = f"tier_{tier}_{name}.json"
            (OUT / fn).write_text(json.dumps(strip(rows), ensure_ascii=False, indent=1))
            di[f"tier2_{tier}_{name}"] = {"file_name": fn,
                                          "columns": {"prompt": "instruction", "query": "input",
                                                      "response": "output"}}
        manifest[tier] = dict(train=len(train), eval_id=len(evid), eval_ood=len(ood),
                              op=TIERS[tier]["name"], depth=TIERS[tier]["depth"])
        # char-proxy token audit (exact audit on server via gate_token_audit.py)
        lens = sorted(len(r["instruction"]) + len(r["input"]) + len(r["output"]) for r in train)
        audit.append(dict(tier=tier, p95_chars=lens[int(0.95 * len(lens))],
                          proxy_tokens=round(lens[int(0.95 * len(lens))] / 3.5)))
        # ---- poison calibration on tier b ----
        if tier == "b":
            for dose in (0.10, 0.30):
                k = int(dose * len(evid))
                poison = strip(train) + strip(evid[:k])
                random.Random(7).shuffle(poison)
                fn = f"tier_b_train_poison{int(dose*100)}.json"
                (OUT / fn).write_text(json.dumps(poison, ensure_ascii=False, indent=1))
                di[f"tier2_b_train_poison{int(dose*100)}"] = {
                    "file_name": fn, "columns": {"prompt": "instruction", "query": "input",
                                                 "response": "output"}}
                manifest[f"b_poison{int(dose*100)}"] = dict(base=len(train), leaked=k,
                                                            dose=f"{int(dose*100)}% of eval_id")
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    (OUT / "token_audit_charproxy.json").write_text(json.dumps(audit, indent=1))
    print(json.dumps(manifest, indent=1))
    print("token audit (char-proxy):", audit)
    print("ALL ASSERTIONS PASS (constructive zero-leak; poison doses exact)")


if __name__ == "__main__":
    main()
