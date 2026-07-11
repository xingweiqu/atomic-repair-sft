#!/usr/bin/env python3
"""B3 natural set: sample 200 real-world messy prompts from 6 existing datasets
(PREREG_naturalset quotas, seed 42) and emit the frozen annotation schema.

CC pre-annotation fills mapped_probe + a one-line item-grounded reason where the
source's own labels license it (e.g. CREPE's labelled false presupposition);
Xingwei double-annotates a 50-item overlap (agreement reported as Cohen kappa).
Deviation from prereg recorded inline: CREPE via tasksource/CREPE HF mirror
(original Google Drive file 404s); sycophancy via meg-tong/sycophancy-eval
answer split (user asserts an answer; Anthropic evals philpapers is opinion-only).
"""
from __future__ import annotations

import csv
import json
import random
from pathlib import Path

RAW = Path(__file__).parent / "raw"
OUT = Path(__file__).parent / "natural_set_v1.jsonl"
rng = random.Random(42)


def clip(s, n=1200):
    s = " ".join(str(s).split())
    return s[:n]


def sample(rows, k):
    rows = list(rows)
    rng.shuffle(rows)
    return rows[:k]


def main():
    items = []

    # CREPE (50) - false-presupposition real questions -> W2
    from datasets import load_dataset
    crepe = [r for r in load_dataset("tasksource/CREPE", split="test")
             if "false presupposition" in (r["labels"] or [])]
    for r in sample(crepe, 50):
        items.append(dict(
            source="CREPE", source_id=r["id"], text=clip(r["question"]),
            error_info_type="false presupposition embedded in a genuine user question",
            mapped_probe="W2",
            mapping_reason=f"question presupposes: '{clip(r['presuppositions'][0], 120)}' "
                           f"(labelled false) — a wrong claim planted in the prompt, "
                           f"the W2 construct in the wild."))

    # GSM-IC (30) - irrelevant context injection -> W1 (neighbour, noise not wrong value)
    gsmic = json.loads((RAW / "GSM-IC_2step.json").read_text())
    for i, r in enumerate(sample(gsmic, 30)):
        items.append(dict(
            source="GSM-IC", source_id=f"gsmic_{i}", text=clip(r["new_question"]),
            error_info_type="irrelevant in-context sentence inserted into a math problem",
            mapped_probe="W1",
            mapping_reason="inserted sentence adds a distracting quantity to the "
                           "context; neighbour of W1 (planted intermediate) with "
                           "noise instead of a wrong value — differential line, not first."))

    # FalseQA (30) - unanswerable false-premise questions -> abstain
    with (RAW / "test.csv").open() as f:
        fq = [r for r in csv.DictReader(f) if r.get("label") == "1"]
    for i, r in enumerate(sample(fq, 30)):
        items.append(dict(
            source="FalseQA", source_id=f"falseqa_{i}", text=clip(r["question"]),
            error_info_type="question built on a false premise; correct behaviour is to refuse/correct",
            mapped_probe="abstain",
            mapping_reason="no true answer exists; maps to the retrieve_or_abstain "
                           "policy class (the abstain instrument)."))

    # sycophancy answer split (30) - user asserts an answer -> W2/keep
    syc = [json.loads(l) for l in (RAW / "syco_answer.jsonl").open()]
    syc = [r for r in syc if "I think the answer is" in r["prompt"][0]["content"]]
    for i, r in enumerate(sample(syc, 30)):
        items.append(dict(
            source="sycophancy-eval/answer", source_id=f"syco_{i}",
            text=clip(r["prompt"][0]["content"]),
            error_info_type="user asserts a (possibly wrong) answer inside the question",
            mapped_probe="W2",
            mapping_reason="user-asserted answer is a planted final claim under "
                           "social pressure; the keep/adopt failure class."))

    # NQ-Swap (30) - substituted context contradicts parametric knowledge -> K-conflict
    from datasets import load_dataset as ld
    nq = ld("pminervini/NQ-Swap", split="dev")
    for i, r in enumerate(sample(list(nq), 30)):
        items.append(dict(
            source="NQ-Swap", source_id=f"nqswap_{i}",
            text=clip(f"{r['sub_context']} Question: {r['question']}"),
            error_info_type="retrieved context entity swapped against model knowledge",
            mapped_probe="K-conflict(W2)",
            mapping_reason="context contradicts parametric fact; wrong-claim-in-context "
                           "family with knowledge (K) rather than computation as target."))

    # RGB noise (30) - noisy retrieved docs -> noise robustness (blind-spot candidate)
    rgb = json.loads((RAW / "en.json").read_text()) if (RAW / "en.json").read_text().lstrip().startswith("[") \
        else [json.loads(l) for l in (RAW / "en.json").open()]
    for i, r in enumerate(sample(rgb, 30)):
        docs = (r.get("negative") or r.get("positive") or [""])[:1]
        items.append(dict(
            source="RGB", source_id=f"rgb_{i}",
            text=clip(f"{docs[0]} Question: {r['query']}"),
            error_info_type="noisy/irrelevant retrieved document in context",
            mapped_probe="none",
            mapping_reason="retrieval noise robustness; no dedicated probe in our "
                           "suite — honest blind-spot column (P-NS-2)."))

    assert len(items) == 200, len(items)
    with OUT.open("w") as f:
        for i, r in enumerate(items):
            f.write(json.dumps({"id": f"ns_{i:03d}", **r}, ensure_ascii=False) + "\n")
    # 50-item overlap for double annotation (stratified: ~8-9 per source)
    overlap = []
    for src in ("CREPE", "GSM-IC", "FalseQA", "sycophancy-eval/answer", "NQ-Swap", "RGB"):
        overlap += sample([r for r in items if r["source"] == src], 9)
    with (Path(__file__).parent / "overlap50_for_xingwei.jsonl").open("w") as f:
        for r in overlap[:50]:
            f.write(json.dumps({**r, "mapped_probe": "", "mapping_reason": ""},
                               ensure_ascii=False) + "\n")
    from collections import Counter
    print(Counter(r["source"] for r in items))
    print(Counter(r["mapped_probe"] for r in items))
    print(f"wrote {OUT} + overlap50_for_xingwei.jsonl")


if __name__ == "__main__":
    main()
