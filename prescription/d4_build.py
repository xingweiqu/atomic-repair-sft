#!/usr/bin/env python3
"""Phase-1 D4: balanced conditional-policy pairs (PREREG_phase1_D4, frozen).

Source: GSM8K TRAIN split (strict separation from the factorial eval on test).
Each base item yields a PAIR:
  PRESERVE exemplar : candidate == gold  -> verify, confirm, keep
  OVERRIDE exemplar : candidate == w     -> verify, refute, recompute to gold
Balanced 50/50 by construction. Arms: bal_{300,600,2000}, pure_override_600,
pure_keep_600. Writes prescription/data/d4/ + dataset_info.
"""
from __future__ import annotations

import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm  # noqa: E402

OUT = ROOT / "prescription/data/d4"

INSTR = ("A candidate answer is given. Decide whether it is correct; if wrong, give "
         "the correct one. End with 'The final answer is N.'")


def load_train():
    from datasets import load_dataset
    rows = []
    for i, r in enumerate(load_dataset("openai/gsm8k", "main", split="train")):
        gold = numnorm(r["answer"].split("####")[-1])
        steps = re.sub(r"<<.*?>>", "", r["answer"].split("####")[0]).strip()
        if gold and re.fullmatch(r"\d+", gold) and int(gold) > 0 and steps:
            rows.append(dict(q=r["question"].strip(), gold=gold, steps=steps))
    return rows


def sample_w(gold, rng):
    g = int(gold)
    for _ in range(40):
        w = max(1, int(g * rng.uniform(0.2, 5)))
        if w != g:
            return str(w)
    return str(g + 3)


def pair(r, rng):
    keep = dict(
        instruction=INSTR,
        input=f"{r['q']}\nCandidate answer: {r['gold']}",
        output=(f"Check the candidate by recomputing.\n{r['steps']}\n"
                f"The computation gives {r['gold']}, which matches the candidate. "
                f"The candidate is correct; keep it.\nThe final answer is {r['gold']}."))
    w = sample_w(r["gold"], rng)
    override = dict(
        instruction=INSTR,
        input=f"{r['q']}\nCandidate answer: {w}",
        output=(f"Check the candidate by recomputing.\n{r['steps']}\n"
                f"The computation gives {r['gold']}, not {w}. "
                f"The candidate is wrong; override it.\nThe final answer is {r['gold']}."))
    return keep, override


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(4242)
    rows = load_train()
    rng.shuffle(rows)
    pairs = [pair(r, rng) for r in rows[:1000]]
    di = {}

    def write(name, items):
        assert len(items) in (300, 600, 2000), (name, len(items))
        rng.shuffle(items)
        (OUT / f"{name}.json").write_text(json.dumps(items, ensure_ascii=False))
        di[name] = {"file_name": f"{name}.json",
                    "columns": {"prompt": "instruction", "query": "input", "response": "output"}}

    write("d4_bal_300", [x for p in pairs[:150] for x in p])
    write("d4_bal_600", [x for p in pairs[:300] for x in p])
    write("d4_bal_2000", [x for p in pairs[:1000] for x in p])
    write("d4_pure_override_600", [p[1] for p in pairs[:600]])
    write("d4_pure_keep_600", [p[0] for p in pairs[:600]])
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    print(f"pairs {len(pairs)}; arms 5 written")


if __name__ == "__main__":
    main()
