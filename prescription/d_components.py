#!/usr/bin/env python3
"""Phase 2a component library (C-18): D0 replay / D1 format / D2 verification /
D3 revision / D5 provenance-conflict / D6 abstention, at doses {60,600,2000}.
(D4 conditional comes from P1/P2-1.) Source: GSM train split; all pass think-lint
trivially (templated); insufficiency variants use the audited dropper.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from prescription.d4_build import load_train, sample_w, insuf_variant  # noqa: E402

OUT = ROOT / "prescription/data/p2a"

I_SOLVE = ("Solve the math word problem. Reason step by step, then end with a line "
           "exactly in the form 'The final answer is N.'")
I_JSON = ("Solve the math word problem. Return ONLY a JSON object "
          '{"reasoning": "...", "answer": N} with no other text.')
I_VER = ("A candidate answer is given. State whether it is correct. End with exactly "
         "'The candidate is correct.' or 'The candidate is wrong.'")
I_REV = ("A draft solution is given and it contains an error. Correct it and end with "
         "'The final answer is N.'")
I_ABST = ("Solve the math word problem. If the problem does not contain enough "
          "information to answer, say exactly 'Cannot be determined.'")


def gen(rows, rng):
    comp = {c: [] for c in ("d0_replay", "d1_format", "d2_verify", "d3_revise",
                            "d5_provenance", "d6_abstain")}
    for r in rows:
        comp["d0_replay"].append(dict(
            instruction=I_SOLVE, input=r["q"],
            output=f"{r['steps']}\nThe final answer is {r['gold']}."))
        comp["d1_format"].append(dict(
            instruction=I_JSON, input=r["q"],
            output=json.dumps({"reasoning": r["steps"][:400], "answer": int(r["gold"])})))
        w = sample_w(r["gold"], rng)
        good = rng.random() < 0.5
        cand = r["gold"] if good else w
        comp["d2_verify"].append(dict(
            instruction=I_VER, input=f"{r['q']}\nCandidate answer: {cand}",
            output=(f"Recompute to check.\n{r['steps']}\nThe computation gives {r['gold']}."
                    + ("\nThe candidate is correct." if good else "\nThe candidate is wrong."))))
        comp["d3_revise"].append(dict(
            instruction=I_REV,
            input=f"{r['q']}\nDraft solution: {r['steps'][:300]} The final answer is {w}.",
            output=(f"The draft's final step is wrong: recomputing gives {r['gold']}, "
                    f"not {w}.\n{r['steps']}\nThe final answer is {r['gold']}.")))
        comp["d5_provenance"].append(dict(
            instruction=I_SOLVE,
            input=f"A source states the answer is {w}. {r['q']}",
            output=(f"Compute independently of the source.\n{r['steps']}\n"
                    f"The computation gives {r['gold']}; the source's {w} is wrong.\n"
                    f"The final answer is {r['gold']}.")))
        iq = insuf_variant(r)
        if iq:
            comp["d6_abstain"].append(dict(
                instruction=I_ABST, input=iq,
                output=("The problem does not provide enough information to compute "
                        "the answer.\nCannot be determined.")))
    return comp


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rng = random.Random(6363)
    rows = load_train()
    rng.shuffle(rows)
    comp = gen(rows[:2600], rng)
    di = {}
    for name, items in comp.items():
        assert len(items) >= 2000, (name, len(items))
        for dose in (60, 600, 2000):
            key = f"{name}_{dose}"
            (OUT / f"{key}.json").write_text(json.dumps(items[:dose], ensure_ascii=False))
            di[key] = {"file_name": f"{key}.json",
                       "columns": {"prompt": "instruction", "query": "input", "response": "output"}}
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    print("components:", {k: len(v) for k, v in comp.items()})


if __name__ == "__main__":
    main()
