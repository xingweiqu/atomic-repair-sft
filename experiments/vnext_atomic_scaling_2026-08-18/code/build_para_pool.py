#!/usr/bin/env python3
"""Paraphrase Repair pool (C-48 Phase C): surface rewrite of carrier questions,
gold answer/solution unchanged. Number-preservation gate: every number token of
the original question must appear in the paraphrase (digit-multiset check);
failures retried once at higher temperature then dropped (logged).

Usage: build_para_pool.py <carrier_formal.json> <out_pool.jsonl> <model_path> [tp]
"""
import json, re, sys
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer

CARRIER, OUT, MODEL = sys.argv[1], sys.argv[2], sys.argv[3]
TP = int(sys.argv[4]) if len(sys.argv) > 4 else 1

carrier = json.load(open(CARRIER))
tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)

INSTR = ("Rewrite the following math word problem with different surface wording "
         "(different sentence structure, synonyms, reordered phrasing) while keeping "
         "EVERY number, name, and the mathematical content EXACTLY the same. The rewritten "
         "problem must have the same answer. Output ONLY the rewritten problem text.\n\nProblem:\n")

def nums(s):
    return sorted(re.findall(r"\d+(?:\.\d+)?", s))

def build_prompts(items, temp_note=""):
    ps = []
    for it in items:
        msgs = [{"role": "user", "content": INSTR + it["instruction"] + temp_note}]
        for kw in ({"add_generation_prompt": True, "enable_thinking": False}, {"add_generation_prompt": True}, {}):
            try:
                p = tok.apply_chat_template(msgs, tokenize=False, **kw); break
            except (TypeError, ValueError):
                continue
        ps.append(p)
    return ps

llm = LLM(model=MODEL, tensor_parallel_size=TP, gpu_memory_utilization=0.9, max_model_len=4096)

def gen(items, temperature):
    outs = llm.generate(build_prompts(items), SamplingParams(temperature=temperature, top_p=0.95, max_tokens=512))
    return [o.outputs[0].text.strip() for o in outs]

kept, retry = [], []
texts = gen(carrier, 0.7)
for it, t in zip(carrier, texts):
    if t and nums(t) == nums(it["instruction"]) and t != it["instruction"]:
        kept.append((it, t))
    else:
        retry.append(it)
texts2 = gen(retry, 0.9) if retry else []
dropped = 0
for it, t in zip(retry, texts2):
    if t and nums(t) == nums(it["instruction"]) and t != it["instruction"]:
        kept.append((it, t))
    else:
        dropped += 1

with open(OUT, "w") as f:
    for it, t in kept:
        f.write(json.dumps({"family_id": it["family_id"], "source_split": "train",
                            "generator_id": "vnext-para-v1", "component": "paraphrase",
                            "subtype": "surface_rewrite", "prompt": t,
                            "target": it["output"]}, ensure_ascii=False) + "\n")
print(f"PARA_POOL_DONE kept={len(kept)} dropped={dropped}")
