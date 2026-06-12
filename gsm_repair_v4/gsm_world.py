"""GSM8K loader + step parser for v4-real (Phase 2).

GSM8K answers carry inline calculator annotations `<<a op b=c>>` and a final `#### N`.
We parse each answer into an ordered list of computation steps, each with its operands,
operator, and result, so a corruption (verify_step) can target a SPECIFIC step and remain
traceable, and so we can verify solvability for the abstain (delete-a-quantity) injector.

Real arithmetic => intermediate-step correctness is COMPUTED, not memorized. The
entity-memory shortcut of the closed synthetic world does not exist here.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

CALC_RE = re.compile(r"<<\s*([^=]+?)\s*=\s*(-?\d+(?:\.\d+)?)\s*>>")
FINAL_RE = re.compile(r"####\s*(-?\d[\d,]*(?:\.\d+)?)")
NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

CACHE = Path("data_v4/gsm8k_cache.json")


def _clean_num(s: str) -> str:
    return s.replace(",", "").strip()


def parse_answer(answer: str) -> dict | None:
    """Return {final, steps:[{expr, result, nums}], clean_reasoning} or None if unparsable."""
    fm = FINAL_RE.search(answer)
    if not fm:
        return None
    final = _clean_num(fm.group(1))
    steps = []
    for m in CALC_RE.finditer(answer):
        expr, res = m.group(1).strip(), _clean_num(m.group(2))
        nums = NUM_RE.findall(expr)
        steps.append({"expr": expr, "result": res, "nums": nums})
    if not steps:
        return None
    # reasoning text with the <<...>> annotations stripped, #### line removed
    reasoning = CALC_RE.sub("", answer.split("####")[0]).strip()
    return {"final": final, "steps": steps, "reasoning": reasoning}


def question_numbers(question: str) -> list[str]:
    """The quantities stated in the question (for the abstain delete-a-quantity injector)."""
    return NUM_RE.findall(question)


def load_gsm(split: str, limit: int | None = None, use_cache: bool = True) -> list[dict]:
    """Load GSM8K split, parse, keep only cleanly-parsable items. Cached to disk.

    split: 'train' or 'test'. Returns list of {id, question, answer, final, steps, reasoning}.
    """
    cache = {}
    if use_cache and CACHE.exists():
        cache = json.loads(CACHE.read_text())
        if split in cache:
            rows = cache[split]
            return rows[:limit] if limit else rows
    from datasets import load_dataset
    ds = load_dataset("openai/gsm8k", "main", split=split)
    out = []
    for i, r in enumerate(ds):
        p = parse_answer(r["answer"])
        if not p:
            continue
        out.append({"id": f"gsm_{split}_{i:05d}", "question": r["question"],
                    "answer": r["answer"], "final": p["final"], "steps": p["steps"],
                    "reasoning": p["reasoning"]})
    if use_cache:
        cache[split] = out
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps(cache))
    return out[:limit] if limit else out


if __name__ == "__main__":
    for split in ("train", "test"):
        rows = load_gsm(split)
        ok = sum(1 for r in rows)
        print(f"{split}: {ok} parsable items")
        ex = rows[0]
        print(f"  e.g. final={ex['final']}, {len(ex['steps'])} steps, "
              f"step0={ex['steps'][0]}")
