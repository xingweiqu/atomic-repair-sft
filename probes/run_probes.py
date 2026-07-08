#!/usr/bin/env python3
"""Loop 2 profiling inference: pre-repair model over ALL probe rows, data-parallel shards.
Run: CUDA_VISIBLE_DEVICES=g python3 probes/run_probes.py --shard g:N [--model ...]
Writes probes/out/answers.shard{g}.jsonl  {base_id, probe, pool, predict}."""
from __future__ import annotations
import argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "probes/out"
TYPES = ["O", "P", "S", "R", "C", "W1", "W2", "F"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", default="0:1")
    ap.add_argument("--model", default="/mnt/hdfs/xwqu/Qwen3-8B")
    ap.add_argument("--types", default="", help="comma list; empty = all")
    ap.add_argument("--ids-file", default="", help="json list of base_ids to restrict to")
    ap.add_argument("--outdir", default="probes/out")
    a = ap.parse_args()
    i, n = map(int, a.shard.split(":"))
    want = set(a.types.split(",")) if a.types else set(TYPES)
    ids = set(__import__("json").loads(Path(a.ids_file).read_text())) if a.ids_file else None
    rows = []
    for t in [x for x in TYPES if x in want]:
        p = ROOT / f"probes/data/base_{t}.jsonl"
        if not p.exists():
            continue
        for l in p.open():
            r = json.loads(l)
            if ids is not None and r["base_id"] not in ids:
                continue
            rows.append((t, r))
    rows = rows[i::n]
    from vllm import LLM, SamplingParams
    llm = LLM(model=a.model, dtype="bfloat16")
    sp = SamplingParams(temperature=0.0, max_tokens=2048)
    msgs = [[{"role": "user", "content": f"{r['instr']}\n{r['user']} /no_think"}] for _, r in rows]
    outs = llm.chat(msgs, sp)
    outdir = ROOT / a.outdir
    outdir.mkdir(parents=True, exist_ok=True)
    with (outdir / f"answers.shard{i}.jsonl").open("w") as f:
        for (t, r), o in zip(rows, outs):
            f.write(json.dumps({"base_id": r["base_id"], "probe": t, "pool": r["pool"],
                                "gold": r["gold"], "w": r.get("w"),
                                "predict": o.outputs[0].text}, ensure_ascii=False) + "\n")
    print(f"shard {i}/{n}: {len(rows)} answered")

if __name__ == "__main__":
    main()
