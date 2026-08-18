#!/usr/bin/env python3
"""Queue-C formal grid arm assembly (C-25). Run on server (tokenizer).

Inputs: carrier_formal.json, format_pool_formal.jsonl, bundle_order_format_formal.json.
Doses n in {0,30,60,120,240,480,960,2000}; substitution per DOSE_DEFINITION 4b
(same-bucket equal-target-token removal, nested prefixes); packed budget accounting;
ONE global fixed max_steps for every arm (computed from the max packed estimate).
Outputs to out_dir: data_FMT-<n>.json x8, dataset_info.json, dose_manifest_format.json.
"""
import json, sys, random, hashlib
from pathlib import Path
from transformers import AutoTokenizer

CARRIER, POOL, OUT_DIR, MODEL = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
PREFIX = sys.argv[5] if len(sys.argv) > 5 else "FMT"
CAP_MODE = len(sys.argv) > 6 and sys.argv[6] == "cap"
CUSTOM_DOSES = [int(x) for x in sys.argv[7].split(",")] if len(sys.argv) > 7 else None
SEED = 20260813
DOSES = [0, 30, 60, 120, 240, 480, 960, 2000]
if CUSTOM_DOSES: DOSES = CUSTOM_DOSES
BUCKETS = [(0, 50), (50, 100), (100, 200), (200, 400), (400, 10**9)]
CUTOFF, SEQ_PER_STEP, EPOCHS = 2048, 16, 2

tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
ntok = lambda s: len(tok(s, add_special_tokens=False)["input_ids"])

def _chat(msgs):
    for kw in ({"add_generation_prompt": True, "enable_thinking": False},
               {"add_generation_prompt": True}, {}):
        try:
            return tok.apply_chat_template(msgs, tokenize=False, **kw)
        except (TypeError, ValueError):
            continue
    raise RuntimeError("no chat template variant worked")

def seqtok(prompt, target):
    r = _chat([{"role": "user", "content": prompt}])
    return (len(r) if isinstance(r, list) else ntok(r)) + ntok(target)

sha = lambda b: hashlib.sha256(b).hexdigest()
out = Path(OUT_DIR); out.mkdir(parents=True, exist_ok=True)

carrier = json.load(open(CARRIER))
for i, c in enumerate(carrier):
    c["_id"] = c.get("family_id", f"carrier_{i:04d}")
    c["_tgt"] = ntok(c["output"])
    c["_seq"] = seqtok(c["instruction"], c["output"])
    c["_bucket"] = next(bi for bi, (lo, hi) in enumerate(BUCKETS) if lo <= c["_tgt"] < hi)
rng = random.Random(SEED)
removal_order = {bi: sorted(x["_id"] for x in carrier if x["_bucket"] == bi) for bi in range(5)}
for bi in removal_order:
    rng.shuffle(removal_order[bi])
by_id = {c["_id"]: c for c in carrier}

pool = [json.loads(l) for l in open(POOL)]
order = json.load(open(Path(OUT_DIR).parent / "bundle_order_format_formal.json"))["nested_prefix_order"] \
    if (Path(OUT_DIR).parent / "bundle_order_format_formal.json").exists() else None
# pool is already in frozen build order; nested prefix = as-listed (bundle_order file authoritative)
for i, f in enumerate(pool):
    f["_tgt"] = ntok(f["target"])
    f["_seq"] = seqtok(f["prompt"], f["target"])
    f["_bucket"] = next(bi for bi, (lo, hi) in enumerate(BUCKETS) if lo <= f["_tgt"] < hi)

carrier_tgt_total = sum(c["_tgt"] for c in carrier)
if CAP_MODE:
    cum, cap = 0, 0
    for f in pool:
        if cum + f["_tgt"] > carrier_tgt_total:
            break
        cum += f["_tgt"]; cap += 1
    DOSES = [d for d in DOSES if d < cap] + [cap]   # top arm = token-capped pure-component corner (declared)
arms = []
for n in DOSES:
    n_eff = min(n, len(pool))
    ins = pool[:n_eff]
    need = {bi: sum(f["_tgt"] for f in ins if f["_bucket"] == bi) for bi in range(5)}
    removed = set(); rem_tok = 0
    for bi in range(5):
        got = 0
        for cid in removal_order[bi]:
            if got >= need[bi]:
                break
            removed.add(cid); got += by_id[cid]["_tgt"]
        rem_tok += got
    # bucket-spill (declared): if a bucket ran dry, keep removing from the next
    # buckets in ascending order until the total inserted-token budget is met.
    total_need = sum(need.values())
    spill = 0
    if rem_tok < total_need:
        for bi in range(5):
            for cid in removal_order[bi]:
                if rem_tok >= total_need:
                    break
                if cid in removed:
                    continue
                removed.add(cid); rem_tok += by_id[cid]["_tgt"]; spill += 1
    keep = [c for c in carrier if c["_id"] not in removed]
    data = ([{"instruction": c["instruction"], "input": "", "output": c["output"]} for c in keep]
            + [{"instruction": f["prompt"], "input": "", "output": f["target"]} for f in ins])
    name = f"{PREFIX}-{n:04d}"
    fp = out / f"data_{name}.json"
    fp.write_text(json.dumps(data, ensure_ascii=False))
    tgt = sum(c["_tgt"] for c in keep) + sum(f["_tgt"] for f in ins)
    seq = sum(c["_seq"] for c in keep) + sum(f["_seq"] for f in ins)
    arms.append(dict(arm=name, dose=n, examples=len(data), component_examples=n_eff,
                     carrier_examples=len(keep), removed_carrier=len(removed),
                     component_target_tokens=sum(f["_tgt"] for f in ins),
                     bucket_spill_removals=spill,
                     total_target_tokens=tgt, total_sequence_tokens=seq,
                     packed_sequences_est=-(-seq // CUTOFF),
                     q_d=round(sum(f["_tgt"] for f in ins) / tgt, 5),
                     data_sha256=sha(fp.read_bytes())[:16]))
base = arms[0]
max_packed = max(a["packed_sequences_est"] for a in arms)
fixed_steps = -(-max_packed // SEQ_PER_STEP) * EPOCHS
for a in arms:
    a["T_dev_pct"] = round(100 * (a["total_target_tokens"] - base["total_target_tokens"]) / base["total_target_tokens"], 3)
    a["S_dev_pct_declared"] = round(100 * (a["total_sequence_tokens"] - base["total_sequence_tokens"]) / base["total_sequence_tokens"], 3)
    a["optimizer_updates_fixed"] = fixed_steps
    a["budget_violation"] = abs(a["T_dev_pct"]) > 1.0
json.dump(arms, open(out / f"dose_manifest_{PREFIX}.json", "w"), indent=1)
json.dump({f"lawv1_{a['arm']}": {"file_name": f"data_{a['arm']}.json"} for a in arms},
          open(out / "dataset_info.json", "w"), indent=1)
print(json.dumps([{k: a[k] for k in ("arm", "examples", "q_d", "total_target_tokens",
                                     "T_dev_pct", "S_dev_pct_declared", "optimizer_updates_fixed",
                                     "budget_violation")} for a in arms], indent=1))
