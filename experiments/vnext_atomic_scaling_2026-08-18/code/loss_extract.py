#!/usr/bin/env python3
"""Teacher-forced atomic loss/margin extraction (C-48 Phase A/B).
Implements ATOMIC_LOSS_SCHEMA.json exactly; identical instrument for every model.

Usage: loss_extract.py <proto.jsonl> <model_path> <out.jsonl> [max_rows]
Single GPU (set CUDA_VISIBLE_DEVICES). Output: one JSON line per (family, condition)
with nll/margin fields; free-text conditions are skipped (loss_not_well_defined).
"""
import json, sys, math
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

PROTO, MODEL, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
MAXROWS = int(sys.argv[4]) if len(sys.argv) > 4 else 0
SCAFFOLD_PREFIX = "Final answer: "
SKIP = {"insufficient", "wc_nl", "cc_nl"}

tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
model = AutoModelForCausalLM.from_pretrained(MODEL, torch_dtype=torch.bfloat16,
                                             device_map="cuda", trust_remote_code=True)
model.eval()

def chat_ids(prompt):
    try:
        s = tok.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                    add_generation_prompt=True, enable_thinking=False)
    except TypeError:
        s = tok.apply_chat_template([{"role": "user", "content": prompt}], tokenize=False,
                                    add_generation_prompt=True)
    return tok(s, add_special_tokens=False)["input_ids"]

def piece_ids(s):
    return tok(s, add_special_tokens=False)["input_ids"]

# Build variants: each = (row_idx, variant_name, prompt_ids, [(piece_name, ids), ...])
rows = [json.loads(l) for l in open(PROTO)]
if MAXROWS: rows = rows[:MAXROWS]
variants = []
for i, r in enumerate(rows):
    c = r["condition"]
    if c in SKIP: continue
    p = chat_ids(r["prompt"]); g = str(r["gold"])
    if c in ("original", "paraphrase", "distractor"):
        variants.append((i, "gold", p, [("scaffold", piece_ids(SCAFFOLD_PREFIX)), ("gold", piece_ids(g))]))
    elif c in ("wc_light", "wc_attempt", "cc_light", "cc_attempt"):
        corr = "REVISE" if c.startswith("wc") else "KEEP"
        wrong = "KEEP" if corr == "REVISE" else "REVISE"
        variants.append((i, "dec_corr", p, [("dec", piece_ids(f"DECISION={corr}"))]))
        variants.append((i, "dec_wrong", p, [("dec", piece_ids(f"DECISION={wrong}"))]))
        variants.append((i, "final_gold", p, [("pre", piece_ids(f"DECISION={corr}\nFINAL_ANSWER=")), ("fin", piece_ids(g))]))
        if c.startswith("wc") and r["meta"].get("cand") is not None:
            variants.append((i, "final_cand", p, [("pre", piece_ids(f"DECISION={corr}\nFINAL_ANSWER=")), ("fin", piece_ids(str(r["meta"]["cand"])))]))
    elif c in ("insuf_ctr", "suff_ctr"):
        corr = "INSUFFICIENT" if c == "insuf_ctr" else "ANSWERABLE"
        wrong = "ANSWERABLE" if corr == "INSUFFICIENT" else "INSUFFICIENT"
        variants.append((i, "st_corr", p, [("st", piece_ids(f"STATUS={corr}"))]))
        variants.append((i, "st_wrong", p, [("st", piece_ids(f"STATUS={wrong}"))]))
    elif c == "format":
        variants.append((i, "fmt", p, [("contract", piece_ids("ANSWER=")), ("gold", piece_ids(g))]))

# Score in length-sorted batches
def score_batch(batch):
    seqs, masks = [], []
    for _, _, p, pieces in batch:
        t = [tid for _, ids in pieces for tid in ids]
        seqs.append(p + t)
        masks.append((len(p), [(n, len(ids)) for n, ids in pieces]))
    maxlen = max(len(s) for s in seqs)
    pad = tok.pad_token_id or tok.eos_token_id
    inp = torch.tensor([s + [pad] * (maxlen - len(s)) for s in seqs], device="cuda")
    att = torch.tensor([[1] * len(s) + [0] * (maxlen - len(s)) for s in seqs], device="cuda")
    with torch.no_grad():
        logits = model(input_ids=inp, attention_mask=att).logits.float()
    lp = torch.log_softmax(logits, dim=-1)
    out = []
    for bi, (s, (plen, pieces)) in enumerate(zip(seqs, masks)):
        pos = plen; res = {}
        for name, n in pieces:
            tot = 0.0
            for k in range(n):
                j = pos + k
                tot += lp[bi, j - 1, s[j]].item()
            res[name] = {"logp": tot, "ntok": n}
            pos += n
        out.append(res)
    return out

variants.sort(key=lambda v: len(v[2]))
results = {}
B = 8
for b0 in range(0, len(variants), B):
    batch = variants[b0:b0 + B]
    for (i, vname, _, _), res in zip(batch, score_batch(batch)):
        results.setdefault(i, {})[vname] = res
    if (b0 // B) % 50 == 0:
        print(f"{b0}/{len(variants)}", flush=True)

with open(OUT, "w") as f:
    for i, r in enumerate(rows):
        c = r["condition"]
        if c in SKIP or i not in results: continue
        v = results[i]; o = {"family_id": r["family_id"], "condition": c}
        if "gold" in v:
            o["nll_gold"] = -v["gold"]["gold"]["logp"]
            o["nll_gold_per_tok"] = o["nll_gold"] / max(1, v["gold"]["gold"]["ntok"])
        if "dec_corr" in v:
            o["nll_decision"] = -v["dec_corr"]["dec"]["logp"]
            o["margin_decision"] = v["dec_corr"]["dec"]["logp"] - v["dec_wrong"]["dec"]["logp"]
        if "final_gold" in v:
            o["nll_final_gold"] = -v["final_gold"]["fin"]["logp"]
            if "final_cand" in v:
                o["margin_candidate"] = v["final_gold"]["fin"]["logp"] - v["final_cand"]["fin"]["logp"]
        if "st_corr" in v:
            o["nll_status"] = -v["st_corr"]["st"]["logp"]
            o["margin_status"] = v["st_corr"]["st"]["logp"] - v["st_wrong"]["st"]["logp"]
        if "fmt" in v:
            o["nll_contract_tokens"] = -v["fmt"]["contract"]["logp"]
            o["nll_semantic_tokens"] = -v["fmt"]["gold"]["logp"]
        f.write(json.dumps(o) + "\n")
print("LOSS_EXTRACT_DONE", OUT, flush=True)
