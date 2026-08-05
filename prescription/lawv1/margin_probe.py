#!/usr/bin/env python3
"""Template-audit margin probe (CONTRACT_EVAL 4-5; C-25 queue B). HF forward only.

For each probe item, computes logprob margin between the two action continuations
under K template variants (3 wordings x label permutation where applicable).
Probes: answerability (suff/insuf paired, gold ANSWERABLE|INSUFFICIENT) and
candidate verdict (wc/cc attempt, gold KEEP|REVISE).

Usage: margin_probe.py <eval_proto.jsonl> <model_path> <out.jsonl>
Writes one row per (family, probe, template): {family_id, probe, gold, template_id,
perm_id, margin, lp_gold, lp_other}. Audit stats computed downstream.
"""
import json, sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

EVAL, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

TEMPLATES = {
    "ans": [
        ("T1", "\n\nSTATUS=", {"pos": "ANSWERABLE", "neg": "INSUFFICIENT"}),
        ("T2", "\n\nVerdict: the problem is ", {"pos": "answerable", "neg": "missing required information"}),
        ("T3", "\n\nCan the answer be determined from the given information? ", {"pos": "Yes", "neg": "No"}),
    ],
    "cand": [
        ("T1", "\nDECISION=", {"pos": "KEEP", "neg": "REVISE"}),
        ("T2", "\nThe candidate answer is ", {"pos": "correct", "neg": "wrong"}),
        ("T3", "\nShould the attempt's answer be kept or replaced? ", {"pos": "Kept", "neg": "Replaced"}),
    ],
}

tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16, device_map="cuda:0")
model.eval()

@torch.no_grad()
def contlp(context, cont):
    ids_c = tok(context, return_tensors="pt").input_ids.to("cuda:0")
    ids_f = tok(context + cont, return_tensors="pt").input_ids.to("cuda:0")
    out = model(ids_f).logits.log_softmax(-1)
    lp = 0.0
    for pos in range(ids_c.shape[1], ids_f.shape[1]):
        lp += out[0, pos - 1, ids_f[0, pos]].item()
    return lp

rows = [json.loads(l) for l in open(EVAL)]
probes = []
for r in rows:
    if r["condition"] == "insuf_ctr":
        probes.append(("ans", "INSUFFICIENT", r))
    elif r["condition"] == "suff_ctr":
        probes.append(("ans", "ANSWERABLE", r))
    elif r["condition"] in ("wc_attempt", "cc_attempt"):
        probes.append(("cand", "REVISE" if r["condition"] == "wc_attempt" else "KEEP", r))

def render(prompt):
    return tok.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                   add_generation_prompt=True, enable_thinking=False)

with open(OUT, "w") as f:
    for kind, gold, r in probes:
        base_ctx = render(r["prompt"])
        gold_is_pos = gold in ("ANSWERABLE", "KEEP")
        for tid, stem, labels in TEMPLATES[kind]:
            for perm in (0, 1):     # label order permutation in scoring (order-free margin,
                                    # perm swaps which label is scored first -> detects position/format bias
                a, b = (labels["pos"], labels["neg"]) if perm == 0 else (labels["neg"], labels["pos"])
                lpa, lpb = contlp(base_ctx + stem, a), contlp(base_ctx + stem, b)
                lp_pos, lp_neg = (lpa, lpb) if perm == 0 else (lpb, lpa)
                margin = (lp_pos - lp_neg) if gold_is_pos else (lp_neg - lp_pos)
                f.write(json.dumps({"family_id": r["family_id"], "probe": kind,
                                    "condition": r["condition"], "gold": gold,
                                    "template_id": tid, "perm_id": perm,
                                    "margin": round(margin, 4),
                                    "lp_gold": round(lp_pos if gold_is_pos else lp_neg, 4),
                                    "lp_other": round(lp_neg if gold_is_pos else lp_pos, 4)}) + "\n")
print("MARGIN_PROBE_DONE", len(probes))
