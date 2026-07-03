#!/usr/bin/env python3
"""D-7 (approved): per-item pass@8 on GSM8K test for the PRE-REPAIR model — the Loop 2A
bucketing variable. Sampling regime is used ONLY for bucketing; repair evaluation stays
greedy single-shot (two inference regimes never mixed — LOOP0_RULINGS D-7(iii)).

Spec (LOOP0_RULINGS D-7):
  (i)  first 500 items to calibrate bucket edges, then the full 1319 (--limit controls);
  (ii) temperature fixed to the Qwen3 official recommendation (0.7 / top_p 0.8 / top_k 20,
       non-thinking mode), recorded in the output header and later in the dataset_card;
  (iii) k=8 samples per item, seed 42.

Runs with vllm if available (fast), else transformers (slow but same sampling params).
Output: data_v4/pass8_results.jsonl  {id, question, gold, n_correct, pass_at_8, samples[]}

Usage (server):
  python3 scripts/pass8_gsm.py --model /mnt/hdfs/xwqu/Qwen3-8B --limit 500
  python3 scripts/pass8_gsm.py --model /mnt/hdfs/xwqu/Qwen3-8B            # full 1319
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gsm_repair_v4.gsm_world import load_gsm  # noqa: E402

K = 8
TEMP, TOP_P, TOP_K = 0.7, 0.8, 20  # Qwen3 official non-thinking recommendation
VERSION = 2  # v2 (2026-07-04): force non-thinking via /no_think + max_tokens 2048 + sample dump.
# v1 CAVEAT: chat template may default to Qwen3 THINKING mode; <think> can eat the 1024-token
# budget -> truncation scored as wrong -> inflates the [0-25%] bucket. v1 calib500 numbers are
# therefore SUSPECT until re-run with v2 (repair evals all use non-thinking `template: qwen`).
INSTR = ("Solve the math word problem. Reason step by step, then end with a line exactly "
         "in the form 'The final answer is N.'")


def gold_of(ans: str) -> str:
    return ans.split("####")[-1].strip().replace(",", "")


def extract(text: str):
    m = re.findall(r"final answer is\s*(-?[\d,\.]+)", text or "", re.I)
    return m[-1].replace(",", "").rstrip(".") if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--limit", type=int, default=None, help="500 for calibration run")
    ap.add_argument("--out", default="data_v4/pass8_results.jsonl")
    args = ap.parse_args()

    items = load_gsm("test", limit=args.limit)
    prompts = [f"{INSTR}\n{it['question']} /no_think" for it in items]  # soft-switch: non-thinking

    try:
        from vllm import LLM, SamplingParams
        llm = LLM(model=args.model, dtype="bfloat16")
        sp = SamplingParams(n=K, temperature=TEMP, top_p=TOP_P, top_k=TOP_K,
                            max_tokens=2048, seed=42)
        # chat template = qwen (align with LF `template: qwen`)
        outs = llm.chat([[{"role": "user", "content": p}] for p in prompts], sp)
        samples = [[o.text for o in out.outputs] for out in outs]
    except ImportError:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(args.model)
        model = AutoModelForCausalLM.from_pretrained(args.model, torch_dtype=torch.bfloat16,
                                                     device_map="auto")
        torch.manual_seed(42)
        samples = []
        for p in prompts:
            text = tok.apply_chat_template([{"role": "user", "content": p}],
                                           tokenize=False, add_generation_prompt=True)
            ids = tok(text, return_tensors="pt").to(model.device)
            out = model.generate(**ids, do_sample=True, temperature=TEMP, top_p=TOP_P,
                                 top_k=TOP_K, num_return_sequences=K, max_new_tokens=2048)
            samples.append([tok.decode(o[ids["input_ids"].shape[1]:],
                                       skip_special_tokens=True) for o in out])

    with Path(args.out).open("w") as f:
        f.write(json.dumps({"_header": {"model": args.model, "k": K, "temperature": TEMP,
                                        "top_p": TOP_P, "top_k": TOP_K, "seed": 42,
                                        "n_items": len(items), "version": VERSION,
                                        "no_think": True, "max_tokens": 2048}}) + "\n")
        for it, ss in zip(items, samples):
            g = gold_of(it["answer"])
            nc = sum(1 for s in ss if extract(s) == g)
            f.write(json.dumps({"id": it["id"], "gold": g, "n_correct": nc,
                                "pass_at_8": int(nc > 0)}) + "\n")
    # audit sidecar: raw samples of the first 20 items (validity check for extraction/truncation)
    side = Path(args.out).with_suffix(".samples20.json")
    side.write_text(json.dumps([{"id": it["id"], "samples": ss[:2]}
                                for it, ss in list(zip(items, samples))[:20]], ensure_ascii=False))
    print(f"wrote {args.out} ({len(items)} items)")


if __name__ == "__main__":
    main()
