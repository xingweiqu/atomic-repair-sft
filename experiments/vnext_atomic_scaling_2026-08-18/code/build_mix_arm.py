#!/usr/bin/env python3
"""Build ONE mixture arm dataset (C-48 Phase I). Simplified substitution (declared):
remove sum(n_i) carrier items in a fixed seeded shuffle order, append n_i prefix items
from each repair pool (frozen pool order). Same 2000-example budget; max_steps taken
from this model's FMT dose manifest (fixed updates).
Usage: build_mix_arm.py <carrier.json> <out_dir> <arm_name> <spec_json_str> <para_pool_path>
Writes data_<arm_name>.json + dataset_info.json (merging if exists).
"""
import json, sys, random, pathlib

CARRIER, OUT, NAME, SPEC, PARA = sys.argv[1], pathlib.Path(sys.argv[2]), sys.argv[3], json.loads(sys.argv[4]), sys.argv[5]
REPO = pathlib.Path("/opt/tiger/atomic-repair-sft-github")
POOLS = {
    "FMT": REPO / "prescription/lawv1/format_pool_formal.jsonl",
    "EVD": REPO / "prescription/lawv1/evidence_pool_formal.jsonl",
    "REV": REPO / "prescription/lawv1/revision_pool_formal.jsonl",
    "ANS": REPO / "prescription/lawv1/answerability_pool_audited.jsonl",
    "PARA": pathlib.Path(PARA),
}
carrier = json.load(open(CARRIER))
total = sum(SPEC.values())
rng = random.Random(20260818)
order = list(range(len(carrier)))
rng.shuffle(order)
keep = set(order[total:])
examples = [ {"instruction": c["instruction"], "input": c.get("input", ""), "output": c["output"]}
             for i, c in enumerate(carrier) if i in keep ]
for rep, n in SPEC.items():
    if n <= 0: continue
    rows = [json.loads(l) for l in open(POOLS[rep])][:n]
    if len(rows) < n: raise SystemExit(f"pool {rep} too small: {len(rows)}<{n}")
    for r in rows:
        examples.append({"instruction": r["prompt"], "input": "", "output": r["target"]})
rng.shuffle(examples)
OUT.mkdir(parents=True, exist_ok=True)
fn = f"data_{NAME}.json"
json.dump(examples, open(OUT / fn, "w"), ensure_ascii=False)
di_p = OUT / "dataset_info.json"
di = json.load(open(di_p)) if di_p.exists() else {}
di[f"lawv1_{NAME}"] = {"file_name": fn, "columns": {"prompt": "instruction", "query": "input", "response": "output"}}
json.dump(di, open(di_p, "w"), indent=1)
print(f"MIX_BUILD_OK {NAME} n_examples={len(examples)} total_repair={total}")
