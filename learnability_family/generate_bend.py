"""Bendpoint tiers e/f/g generator (PREREG_bendpoint; frozen a-d generator untouched).

Reuses generate.py machinery; differences, all preregistered:
  - tier g inputs are story templates (rotated) and outputs contain steps ONLY
    (the rule is never stated -- that is the tier's construct);
  - e-poison10 arm: tier-e train with 10% of eval-ID leaked verbatim (calibration bed);
  - writes to data_bend/ with its own dataset_info.

Run: python3 -m learnability_family.generate_bend
"""
from __future__ import annotations

import json
import random
from pathlib import Path

from learnability_family.ops import TIERS, STORY_TEMPLATES
from learnability_family.generate import gen_tier, strip, INSTR, N_ID

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data_bend"

INSTR_G = ("Solve the word problem. Reason step by step, then end with a line exactly "
           "in the form 'The final answer is N.'")


def wrap_g(rows, rng):
    out = []
    for r in rows:
        a, b = r["_combo"]
        tpl = STORY_TEMPLATES[rng.randrange(len(STORY_TEMPLATES))]
        gold = r["_gold"]
        steps = TIERS["g"]["steps"](a, b, gold)
        out.append({"instruction": INSTR_G, "input": tpl.format(a=a, b=b),
                    "output": "\n".join(steps) + f"\nThe final answer is {gold}.",
                    "_combo": r["_combo"], "_tier": "g", "_gold": gold})
    return out


def main():
    OUT.mkdir(exist_ok=True)
    rng = random.Random(1234)
    di, manifest = {}, {}
    for tier in "efg":
        if tier == "g":
            TIERS["g"]["rule"] = ""  # placeholder for the shared builder; wrap_g rebuilds outputs
        train, evid, ood = gen_tier(tier, rng)
        if tier == "g":
            train, evid, ood = (wrap_g(x, random.Random(99 + i))
                                for i, x in enumerate((train, evid, ood)))
            train, evid, ood = list(train), list(evid), list(ood)
        tr = {tuple(r["_combo"]) for r in train}
        for name, ev in [("eval_id", evid), ("eval_ood", ood)]:
            inter = tr & {tuple(r["_combo"]) for r in ev}
            assert not inter, f"LEAK {tier} {name}"
        for name, rows in [("train", train), ("eval_id", evid), ("eval_ood", ood)]:
            fn = f"bend_{tier}_{name}.json"
            (OUT / fn).write_text(json.dumps(strip(rows), ensure_ascii=False, indent=1))
            di[f"bend_{tier}_{name}"] = {"file_name": fn,
                                         "columns": {"prompt": "instruction", "query": "input",
                                                     "response": "output"}}
        manifest[tier] = dict(train=len(train), eval_id=len(evid), eval_ood=len(ood),
                              op=TIERS[tier]["name"], depth=TIERS[tier]["depth"])
        if tier == "e":
            k = int(0.10 * len(evid))
            poison = strip(train) + strip(evid[:k])
            random.Random(7).shuffle(poison)
            (OUT / "bend_e_train_poison10.json").write_text(
                json.dumps(poison, ensure_ascii=False, indent=1))
            di["bend_e_train_poison10"] = {"file_name": "bend_e_train_poison10.json",
                                           "columns": {"prompt": "instruction", "query": "input",
                                                       "response": "output"}}
            manifest["e_poison10"] = dict(base=len(train), leaked=k)
        # eval prompt sidecars for race_eval (gold kept)
        for name, rows in [("eval_id", evid), ("eval_ood", ood)]:
            (OUT / f"probe_{tier}_{name}.jsonl").write_text(
                "\n".join(json.dumps({"instruction": r["instruction"], "input": r["input"],
                                      "gold": r["_gold"]}, ensure_ascii=False)
                          for r in rows))
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1))
    print(json.dumps(manifest, indent=1))
    print("ASSERTIONS PASS")


if __name__ == "__main__":
    main()
