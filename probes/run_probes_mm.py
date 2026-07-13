#!/usr/bin/env python3
"""M1: multi-model probe inference (PREREG_multimodel; template-agnostic via
tokenizer chat template so Llama/Qwen prompts are each model's native format).

  gen --model PATH --tag NAME --shard i:N   full 8-type probe suite
  score --tag NAME                          frozen classifier profile + instrument gates
Outputs probes/out_mm/{tag}/answers.shard*.jsonl (same row schema as probes/out).
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm  # noqa: E402
from probes.profile_classify import pf_plain, pf_json, classify  # noqa: E402

TYPES = ["O", "P", "S", "R", "C", "W1", "W2", "F"]
OUT = ROOT / "probes/out_mm"


def rows_all():
    out = []
    for t in TYPES:
        for l in (ROOT / f"probes/data/base_{t}.jsonl").open():
            r = json.loads(l)
            out.append((t, r))
    return out


def cmd_gen(args):
    i, n = map(int, args.shard.split(":"))
    d = OUT / args.tag
    d.mkdir(parents=True, exist_ok=True)
    outp = d / f"answers.shard{i}.jsonl"
    if outp.exists():
        print(f"skip shard {i}")
        return
    jobs = rows_all()[i::n]
    from vllm import LLM, SamplingParams
    llm = LLM(model=args.model, dtype="bfloat16", max_model_len=8192)
    sp = SamplingParams(temperature=0.0, max_tokens=1024)
    msgs = [[{"role": "user", "content": f"{r['instr']}\n{r['user']}"}] for _, r in jobs]
    outs = llm.chat(msgs, sp, chat_template_kwargs={"enable_thinking": False})
    with outp.open("w") as f:
        for (t, r), o in zip(jobs, outs):
            f.write(json.dumps({"probe": t, "base_id": r["base_id"], "pool": r["pool"],
                                "gold": r["gold"], "w": r.get("w"),
                                "predict": o.outputs[0].text}, ensure_ascii=False) + "\n")
    print(f"{args.tag} shard {i}: {len(jobs)}")


def cmd_score(args):
    sig, meta = {}, {}
    raw = {}
    for f in sorted(glob.glob(str(OUT / args.tag / "answers.shard*.jsonl"))):
        for l in Path(f).open():
            r = json.loads(l)
            got = pf_json(r["predict"]) if r["probe"] == "F" else pf_plain(r["predict"])
            sig.setdefault(r["base_id"], {})[r["probe"]] = int(
                got is not None and numnorm(got) == numnorm(r["gold"]))
            meta[r["base_id"]] = r["pool"]
            raw.setdefault(r["probe"], []).append(got is not None)
    # instrument gates (PREREG_multimodel M1): O self-check + F schema validity
    o_answered = sum(raw.get("O", [])) / max(len(raw.get("O", [])), 1)
    f_valid = sum(raw.get("F", [])) / max(len(raw.get("F", [])), 1)
    prof = {}
    for pool in ("gsm", "hard"):
        c = Counter()
        n = 0
        for bid, s in sig.items():
            if meta.get(bid) != pool:
                continue
            n += 1
            for lab in classify(s):
                c[lab] += 1
        prof[pool] = {"n": n, "inclusive_pct": {k: round(100 * v / n, 1) for k, v in c.most_common()}}
    rep = {"tag": args.tag, "O_answered": round(o_answered, 4),
           "F_schema_valid": round(f_valid, 4),
           "gate_F": f_valid >= 0.5, "profile": prof}
    (OUT / f"profile_{args.tag}.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "score"])
    ap.add_argument("--model")
    ap.add_argument("--tag", required=True)
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"gen": cmd_gen, "score": cmd_score}[a.cmd](a)
