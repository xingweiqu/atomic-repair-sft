#!/usr/bin/env python3
"""D-7 (approved): per-item pass@8 for the PRE-REPAIR model — the Loop 2A bucketing
variable. Sampling regime is used ONLY for bucketing; repair evaluation stays greedy
single-shot (two inference regimes never mixed — LOOP0_RULINGS D-7(iii)).

Spec (LOOP0_RULINGS D-7 + R-15):
  (i)   --limit 500 calibration first, then full pool;
  (ii)  temperature fixed to the Qwen3 non-thinking recommendation (0.7/0.8/20),
        recorded in the output header;
  (iii) k=8, seed 42; --pool merged = GSM8K test + GSM-hard (bucket on the merged
        pool, per-item `source` recorded as a covariate).

Version history (kept honest for the taxonomy):
  v2  /no_think + max_tokens 2048 + samples20 sidecar (v1 thinking-truncation artifact).
  v3  merged pool (GSM-hard) + float-gold normalisation.
  v4  (2026-07-06) crash-proofing after a real loss of ~21k generations:
      - numnorm guards inf/nan/1e15+ ("9e999"-style outputs overflowed int(inf));
      - ALL raw samples are dumped to <out>.samples_raw.jsonl.gz BEFORE scoring;
      - --rescore re-scores from the dump without regenerating.

Output: <out> jsonl  {id, gold, n_correct, pass_at_8, source} (+ header line)
        <out>.samples_raw.jsonl.gz (full generations)  + <out>.samples20.json (audit)
"""
from __future__ import annotations

import argparse
import gzip
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from gsm_repair_v4.gsm_world import load_gsm  # noqa: E402

K = 8
TEMP, TOP_P, TOP_K = 0.7, 0.8, 20
VERSION = 4
INSTR = ("Solve the math word problem. Reason step by step, then end with a line exactly "
         "in the form 'The final answer is N.'")


def numnorm(s: str) -> str:
    s = s.replace(",", "").rstrip(".")
    try:
        f = float(s)
    except (ValueError, OverflowError):
        return s
    # v4: outputs like "9e999" float to inf; int(inf) overflows. Non-finite or
    # astronomically large values are never GSM golds -> keep the raw string.
    if f != f or f in (float("inf"), float("-inf")) or abs(f) > 1e15:
        return s
    return str(int(f)) if f == int(f) else str(f)


def gold_of(ans: str) -> str:
    return numnorm(ans.split("####")[-1].strip())


def extract(text: str):
    m = re.findall(r"final answer is\s*(-?[\d,\.eE+]+)", text or "", re.I)
    return numnorm(m[-1]) if m else None


def build_pool(pool: str, limit):
    items = load_gsm("test", limit=limit)
    n_gsm = len(items)
    if pool == "merged":
        from datasets import load_dataset
        gh = load_dataset("reasoning-machines/gsm-hard", split="train")
        hard = [{"id": f"gsmhard_{i:05d}", "question": r["input"],
                 "answer": f"#### {r['target']}"} for i, r in enumerate(gh)]
        if limit:
            hard = hard[:limit]
        items = items + hard
        print(f"pool breakdown: gsm={n_gsm} gsmhard={len(hard)} total={len(items)}", flush=True)
    return items


def generate(model, prompts):
    try:
        from vllm import LLM, SamplingParams
        llm = LLM(model=model, dtype="bfloat16")
        sp = SamplingParams(n=K, temperature=TEMP, top_p=TOP_P, top_k=TOP_K,
                            max_tokens=2048, seed=42)
        outs = llm.chat([[{"role": "user", "content": p}] for p in prompts], sp)
        return [[o.text for o in out.outputs] for out in outs]
    except ImportError:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        tok = AutoTokenizer.from_pretrained(model)
        mdl = AutoModelForCausalLM.from_pretrained(model, torch_dtype=torch.bfloat16,
                                                   device_map="auto")
        torch.manual_seed(42)
        samples = []
        for p in prompts:
            text = tok.apply_chat_template([{"role": "user", "content": p}],
                                           tokenize=False, add_generation_prompt=True)
            ids = tok(text, return_tensors="pt").to(mdl.device)
            out = mdl.generate(**ids, do_sample=True, temperature=TEMP, top_p=TOP_P,
                               top_k=TOP_K, num_return_sequences=K, max_new_tokens=2048)
            samples.append([tok.decode(o[ids["input_ids"].shape[1]:],
                                       skip_special_tokens=True) for o in out])
        return samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--pool", choices=["gsm", "merged"], default="gsm")
    ap.add_argument("--out", default="data_v4/pass8_results.jsonl")
    ap.add_argument("--rescore", action="store_true",
                    help="skip generation; re-score from <out>.samples_raw.jsonl.gz")
    ap.add_argument("--shard", default=None, metavar="i:N",
                    help="data-parallel shard: process items[i::N], write <out>.shard{i}")
    ap.add_argument("--merge", type=int, default=None, metavar="N",
                    help="merge N shard outputs into <out> (no GPU)")
    args = ap.parse_args()

    items = build_pool(args.pool, args.limit)

    if args.merge:
        # stitch shards back into pool order (items[i::N] round-robin)
        rows = {}
        for i in range(args.merge):
            for l in Path(f"{args.out}.shard{i}").open():
                r = json.loads(l)
                if "_header" not in r:
                    rows[r["id"]] = l
        assert len(rows) == len(items), f"merge mismatch: {len(rows)} vs {len(items)}"
        with gzip.open(args.out + ".samples_raw.jsonl.gz", "wt") as fo:
            for i in range(args.merge):
                with gzip.open(f"{args.out}.shard{i}.samples_raw.jsonl.gz", "rt") as fi:
                    for l in fi:
                        fo.write(l)
        with Path(args.out).open("w") as f:
            f.write(json.dumps({"_header": {"model": args.model, "k": K, "temperature": TEMP,
                                            "top_p": TOP_P, "top_k": TOP_K, "seed": 42,
                                            "n_items": len(items), "version": VERSION,
                                            "no_think": True, "max_tokens": 2048,
                                            "pool": args.pool, "shards": args.merge}}) + "\n")
            for it in items:
                f.write(rows[it["id"]])
        print(f"merged {args.merge} shards -> {args.out} ({len(items)} items)")
        return

    if args.shard:
        i, n = map(int, args.shard.split(":"))
        items = items[i::n]
        args.out = f"{args.out}.shard{i}"
        print(f"shard {i}/{n}: {len(items)} items -> {args.out}", flush=True)
    raw_path = Path(args.out + ".samples_raw.jsonl.gz")

    if args.rescore:
        with gzip.open(raw_path, "rt") as f:
            dump = {r["id"]: r["samples"] for r in (json.loads(l) for l in f)}
        samples = [dump[it["id"]] for it in items]
        print(f"rescore: loaded {len(samples)} items from {raw_path}", flush=True)
    else:
        prompts = [f"{INSTR}\n{it['question']} /no_think" for it in items]
        samples = generate(args.model, prompts)
        # v4: persist generations BEFORE any scoring — scoring bugs must never cost GPU time.
        with gzip.open(raw_path, "wt") as f:
            for it, ss in zip(items, samples):
                f.write(json.dumps({"id": it["id"], "samples": ss}, ensure_ascii=False) + "\n")
        print(f"raw samples persisted -> {raw_path}", flush=True)

    with Path(args.out).open("w") as f:
        f.write(json.dumps({"_header": {"model": args.model, "k": K, "temperature": TEMP,
                                        "top_p": TOP_P, "top_k": TOP_K, "seed": 42,
                                        "n_items": len(items), "version": VERSION,
                                        "no_think": True, "max_tokens": 2048,
                                        "pool": args.pool}}) + "\n")
        for it, ss in zip(items, samples):
            g = gold_of(it["answer"])
            nc = sum(1 for s in ss if extract(s) == g)
            f.write(json.dumps({"id": it["id"], "gold": g, "n_correct": nc,
                                "pass_at_8": int(nc > 0),
                                "source": "gsmhard" if it["id"].startswith("gsmhard") else "gsm"})
                    + "\n")
    side = Path(args.out).with_suffix(".samples20.json")
    side.write_text(json.dumps([{"id": it["id"], "samples": ss[:2]}
                                for it, ss in list(zip(items, samples))[:20]], ensure_ascii=False))
    print(f"wrote {args.out} ({len(items)} items)")


if __name__ == "__main__":
    main()
