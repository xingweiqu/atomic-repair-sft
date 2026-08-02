#!/usr/bin/env python3
"""P0b: 16-cell factorial eval-set generator (C-18; DRAFT skeleton, day-1).

2x2x2x2 on GSM base items, matched variants (numbers/gold fixed within family):
  Evidence      CLEAN | INCORRECT   (planted wrong intermediate, frozen w-validator)
  Operation     SOLVE | VERIFY      (verify a candidate answer)
  Interface     FREE_TEXT | JSON
  Answerability ANSWERABLE | INSUFFICIENT (drop one necessary quantity; validator:
                                          equation unsolvable after drop)

  build         emit families + per-cell audit samples (100/cell) + yield report
  (audit gate >=70% per cell before the set is frozen; families that cannot
   support all 16 cells are dropped whole — no forced cells.)
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm  # noqa: E402

OUT = ROOT / "prescription/data"

I_FREE = ("Solve the math word problem. Reason step by step, then end with a line "
          "exactly in the form 'The final answer is N.'")
I_JSON = ("Solve the math word problem. Return ONLY a JSON object "
          '{"reasoning": "...", "answer": N} with no other text.')
V_FREE = ("A candidate answer is given. Decide whether it is correct; if wrong, give "
          "the correct one. End with 'The final answer is N.' (or the candidate if correct).")
V_JSON = ("A candidate answer is given. Decide whether it is correct. Return ONLY "
          '{"verdict": "correct|wrong", "answer": N}.')
INSUF_SUFFIX = (" If the problem does not contain enough information to answer, "
                "say exactly 'Cannot be determined.'")


def load_gsm():
    from datasets import load_dataset
    rows = []
    for i, r in enumerate(load_dataset("openai/gsm8k", "main", split="test")):
        gold = numnorm(r["answer"].split("####")[-1])
        if gold and re.fullmatch(r"\d+", gold) and int(gold) > 0:
            rows.append(dict(id=f"fam_{i:04d}", q=r["question"].strip(), gold=gold,
                             steps=r["answer"].split("####")[0]))
    return rows


def numbers_in(q):
    return re.findall(r"\d[\d,]*\.?\d*", q)


def drop_quantity(q):
    """INSUFFICIENT variant: remove the sentence containing one necessary number.
    Validator (skeleton): >=2 numbers must exist and the dropped sentence must
    contain exactly one of them; full solvability check lands with the audit pass."""
    sents = re.split(r"(?<=[.!?])\s+", q)
    for si, s in enumerate(sents[:-1]):  # never drop the final question sentence
        nums = numbers_in(s)
        if len(nums) == 1 and len(numbers_in(q)) >= 2:
            return " ".join(sents[:si] + sents[si + 1:])
    return None


def sample_w(gold, rng):
    g = int(gold)
    for _ in range(40):
        w = max(1, int(g * rng.uniform(0.2, 5)))
        if w != g:
            return str(w)
    return str(g + 3)


def build_family(r, rng):
    cells = {}
    insuf_q = drop_quantity(r["q"])
    if insuf_q is None:
        return None  # family cannot support the answerability axis -> dropped whole
    w = sample_w(r["gold"], rng)
    for ev in ("CLEAN", "INCORRECT"):
        ev_prefix = "" if ev == "CLEAN" else \
            f"Working through it, someone got an intermediate value of {w}. "
        for op in ("SOLVE", "VERIFY"):
            for itf in ("FREE_TEXT", "JSON"):
                for ans in ("ANSWERABLE", "INSUFFICIENT"):
                    q = r["q"] if ans == "ANSWERABLE" else insuf_q
                    if op == "SOLVE":
                        instr = (I_FREE if itf == "FREE_TEXT" else I_JSON) + \
                                ("" if ans == "ANSWERABLE" else INSUF_SUFFIX)
                        user = ev_prefix + q
                    else:
                        cand = r["gold"] if rng.random() < 0.5 else sample_w(r["gold"], rng)
                        instr = (V_FREE if itf == "FREE_TEXT" else V_JSON) + \
                                ("" if ans == "ANSWERABLE" else INSUF_SUFFIX)
                        user = ev_prefix + q + f"\nCandidate answer: {cand}"
                    cells[f"{ev}|{op}|{itf}|{ans}"] = dict(
                        instr=instr, user=user,
                        gold=r["gold"] if ans == "ANSWERABLE" else "CANNOT",
                        w=w if ev == "INCORRECT" else None)
    return cells


def cmd_build(args):
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(1888)
    rows = load_gsm()
    fams, dropped = [], 0
    for r in rows:
        f = build_family(r, rng)
        if f is None:
            dropped += 1
            continue
        fams.append(dict(id=r["id"], gold=r["gold"], cells=f))
        if len(fams) >= args.n:
            break
    with (OUT / "factorial_families.jsonl").open("w") as fh:
        for f in fams:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")
    # audit samples: 100 per cell, stratified across families
    audit = {}
    cellkeys = list(fams[0]["cells"])
    for ck in cellkeys:
        picks = rng.sample(fams, min(100, len(fams)))
        audit[ck] = [dict(family=p["id"], **{k: p["cells"][ck][k] for k in ("instr", "user", "gold")})
                     for p in picks]
    (OUT / "audit_samples.json").write_text(json.dumps(audit, ensure_ascii=False, indent=1))
    print(f"families kept {len(fams)} dropped {dropped} (answerability-axis unsupported)")
    print(f"cells/family {len(cellkeys)}; audit 100x{len(cellkeys)} emitted")
    assert len(fams) >= 300, "YIELD GATE: <300 complete families"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build"])
    ap.add_argument("--n", type=int, default=400)
    a = ap.parse_args()
    cmd_build(a)
