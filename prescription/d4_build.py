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


def insuf_variant(r):
    import re as _re
    sents = _re.split(r"(?<=[.!?])\s+", r["q"])
    if len(sents) < 3:
        return None
    for si in range(1, len(sents) - 1):
        nums = _re.findall(r"\d[\d,]*\.?\d*", sents[si])
        if len(nums) == 1 and len(_re.findall(r"\d[\d,]*\.?\d*", r["q"])) >= 2:
            return " ".join(sents[:si] + sents[si + 1:])
    return None


INSTR3 = (INSTR + " If the problem does not contain enough information to answer, "
          "say exactly 'Cannot be determined.'")


def triplet(r, rng):
    k, o = pair(r, rng)
    k = dict(k, instruction=INSTR3)
    o = dict(o, instruction=INSTR3)
    iq = insuf_variant(r)
    if iq is None:
        return None
    cand = sample_w(r["gold"], rng)
    a = dict(instruction=INSTR3,
             input=f"{iq}\nCandidate answer: {cand}",
             output=("Check the candidate by recomputing. The problem does not provide "
                     "enough information to compute the answer, so the candidate cannot "
                     "be verified.\nCannot be determined."))
    return k, o, a


def main3():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(5252)
    rows = load_train()
    rng.shuffle(rows)
    trips = []
    for r in rows:
        t3 = triplet(r, rng)
        if t3:
            trips.append(t3)
        if len(trips) >= 666:
            break
    assert len(trips) >= 666, len(trips)
    di = json.loads((OUT / "dataset_info.json").read_text())

    def write(name, items):
        rng.shuffle(items)
        (OUT / f"{name}.json").write_text(json.dumps(items, ensure_ascii=False))
        di[name] = {"file_name": f"{name}.json",
                    "columns": {"prompt": "instruction", "query": "input", "response": "output"}}

    write("d4_3way_600", [x for t3 in trips[:200] for x in t3])
    write("d4_3way_1998", [x for t3 in trips[:666] for x in t3])
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    print(f"triplets {len(trips)}; 3way arms written")


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
    import sys as _s
    (main3 if "--3way" in _s.argv else main)()
