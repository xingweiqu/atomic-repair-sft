#!/usr/bin/env python3
"""Margin probe v2 (C-27 Fig7). Fixes v1 instrument faults:
  (a) continuation scored at token-id level (concat ids, score cont positions) --
      v1 re-tokenized the concatenated STRING, boundary merges zeroed T2/T3;
  (b) TRUE semantic label permutation: opaque letters A/B with both meaning
      assignments (perm=mapping swap, not scoring order);
  (c) genre variants: plain-label / natural-language / JSON.
Variants per probe kind (6): T1 plain labels; T2 NL sentence; T3 JSON field;
T4a/T4b opaque A/B with swapped mappings; T5 classification template.
Usage: margin_probe_v2.py <eval_proto.jsonl> <model_path> <out.jsonl>
"""
import json, sys
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

EVAL, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]

def variants(kind):
    if kind == "ans":
        pos, neg = "answerable", "unanswerable"
        return [
            ("T1", "\n\nSTATUS=", "ANSWERABLE", "INSUFFICIENT", None),
            ("T2", "\n\nIn short, with the information given this problem is ",
             "solvable", "not solvable", None),
            ("T3", '\n\nSummary JSON: {"status": "', "answerable", "insufficient", None),
            ("T4a", "\n\nLabel A means the problem can be answered; label B means required "
                    "information is missing. LABEL=", "A", "B", "A=pos"),
            ("T4b", "\n\nLabel A means required information is missing; label B means the "
                    "problem can be answered. LABEL=", "B", "A", "B=pos"),
            ("T5", "\n\nClassification (answerable / insufficient): ", "answerable", "insufficient", None),
        ]
    return [
        ("T1", "\nDECISION=", "KEEP", "REVISE", None),
        ("T2", "\nAll in all, the candidate's final answer should be ",
         "kept", "replaced", None),
        ("T3", '\nSummary JSON: {"verdict": "', "keep", "revise", None),
        ("T4a", "\nLabel A means the attempt is correct and its answer stands; label B "
                "means it must be corrected. LABEL=", "A", "B", "A=pos"),
        ("T4b", "\nLabel A means the attempt must be corrected; label B means it is "
                "correct and its answer stands. LABEL=", "B", "A", "B=pos"),
        ("T5", "\nClassification (correct / flawed): ", "correct", "flawed", None),
    ]

tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16, device_map="cuda:0")
model.eval()

@torch.no_grad()
def pair_margin(ctx_ids, a, b):
    """logp(a|ctx) - logp(b|ctx), token-id level."""
    out = []
    for cont in (a, b):
        cids = tok(cont, add_special_tokens=False).input_ids
        full = torch.tensor([ctx_ids + cids], device="cuda:0")
        logits = model(full).logits.log_softmax(-1)
        lp = sum(logits[0, len(ctx_ids) + i - 1, cids[i]].item() for i in range(len(cids)))
        out.append(lp)
    return out[0] - out[1], out[0], out[1]

rows = [json.loads(l) for l in open(EVAL)]
probes = []
for r in rows:
    if r["condition"] == "insuf_ctr":
        probes.append(("ans", False, r))     # gold = neg (unanswerable)
    elif r["condition"] == "suff_ctr":
        probes.append(("ans", True, r))
    elif r["condition"] == "wc_attempt":
        probes.append(("cand", False, r))    # gold = neg (revise)
    elif r["condition"] == "cc_attempt":
        probes.append(("cand", True, r))

with open(OUT, "w") as f:
    for kind, gold_pos, r in probes:
        ctx0 = tok.apply_chat_template([{"role": "user", "content": r["prompt"]}],
                                       tokenize=False, add_generation_prompt=True,
                                       enable_thinking=False)
        for tid, stem, lab_pos, lab_neg, mapping in variants(kind):
            ctx_ids = tok(ctx0 + stem, add_special_tokens=False).input_ids
            m_pos, lp_a, lp_b = pair_margin(ctx_ids, lab_pos, lab_neg)
            margin = m_pos if gold_pos else -m_pos
            f.write(json.dumps({"family_id": r["family_id"], "probe": kind,
                                "condition": r["condition"],
                                "gold": "pos" if gold_pos else "neg",
                                "template_id": tid, "mapping": mapping or "direct",
                                "margin": round(margin, 4)}) + "\n")
print("MARGIN_V2_DONE", len(probes))
