"""Genre classifier for plain-mode (素题) outputs — the R-11 bleed-curve instrument.

Three-way rule frozen from the T4 autopsy (qc/LOOP1_5_T4_VERDICT.md §1):
  plain      : output carries the plain-genre marker "The final answer is N."
  json_bleed : no plain marker, but the output contains a JSON object (the repair genre
               invading a plain question, e.g. self-invented {"solve_decision": ...}).
  mute       : neither — no committed answer in any genre.

Self-test: `python3 -m ledger.genre` must reproduce the T4 scaffold_conv split 13/11/4.
Used by the epoch-sweep bleed curve (R-11) and any R-7 dual-genre eval.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

PLAIN_RE = re.compile(r"final answer is\s*(-?[\d,\.]+)", re.I)
JSON_RE = re.compile(r"\{.*\}", re.S)
FA_RE = re.compile(r'"final_answer"\s*:\s*"?(-?[\d,\.]+)')


def _json_final(text: str):
    m = JSON_RE.search(text or "")
    if not m:
        return None
    try:
        return json.loads(m.group(0)).get("final_answer")
    except Exception:
        m2 = FA_RE.search(text or "")
        return m2.group(1) if m2 else None


def classify(text: str) -> str:
    """T4-verdict convention: json_bleed = repair-genre JSON WITH an extractable
    final_answer; brace-noise without a committed answer counts as mute."""
    if PLAIN_RE.search(text or ""):
        return "plain"
    if _json_final(text) is not None:
        return "json_bleed"
    return "mute"


def bleed_rate(texts) -> dict:
    """Aggregate for one ckpt on a plain eval set: fractions per genre + bleed rate
    (= json_bleed + mute; the R-11 canonical-floor gate quantity)."""
    n = len(texts) or 1
    counts = {"plain": 0, "json_bleed": 0, "mute": 0}
    for t in texts:
        counts[classify(t)] += 1
    return {**{k: v / n for k, v in counts.items()},
            "bleed_rate": (counts["json_bleed"] + counts["mute"]) / n, "n": n}


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    p = root / "data_v4/predict_outputs/predict_t4_plain_scaffold_conv/generated_predictions.jsonl"
    texts = [json.loads(l).get("predict", "") for l in p.open() if l.strip()]
    from collections import Counter
    got = Counter(classify(t) for t in texts)
    exp = {"plain": 13, "json_bleed": 11, "mute": 4}
    print("T4 scaffold_conv genre split:", dict(got), "expected:", exp)
    sys.exit(0 if dict(got) == exp else 1)
