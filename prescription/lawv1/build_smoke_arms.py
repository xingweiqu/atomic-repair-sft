#!/usr/bin/env python3
"""Assemble smoke-run training arms per DOSE_DEFINITION 4b (C-24 #4/#5/#6).

Runs where the Qwen tokenizer lives (server). Inputs: carrier json (LF alpaca),
train_proto.jsonl. Outputs (out_dir): arm data files (LF alpaca), dataset_info.json,
carrier_manifest.json, bundle_manifest.json, dose_manifest_smoke.json.

Arms: SMK-PLAC-0000 (pure carrier), SMK-FMT-0060, SMK-FMT-0200
(format component substituted into carrier by equal-target-token, same-bucket removal).
Deterministic: seed 20260812. Carrier = loop3 cleanreplay prototype pool (n=600);
formal 2000-carrier is a later, separately-audited build (declared deviation).
"""
import json, sys, random, hashlib
from pathlib import Path
from transformers import AutoTokenizer

CARRIER, PROTO, OUT_DIR, MODEL = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
SEED = 20260812
BUCKETS = [(0, 50), (50, 100), (100, 200), (200, 400), (400, 10**9)]

tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
ntok = lambda s: len(tok(s, add_special_tokens=False)["input_ids"])
CUTOFF = 2048
SEQ_PER_STEP = 16          # per_device 1 x grad_accum 2 x 8 GPU (packed mode)
EPOCHS = 2

def seqtok(prompt, target):
    """chat-template-rendered sequence length (prompt+target), matching training."""
    rendered = tok.apply_chat_template([{"role": "user", "content": prompt}],
                                       tokenize=False, add_generation_prompt=True,
                                       enable_thinking=False)
    return ntok(rendered) + ntok(target)
sha = lambda b: hashlib.sha256(b).hexdigest()
out = Path(OUT_DIR); out.mkdir(parents=True, exist_ok=True)

carrier = json.load(open(CARRIER))
for i, c in enumerate(carrier):
    c["_id"] = f"carrier_{i:04d}"
    c["_tgt"] = ntok(c["output"])
    c["_bucket"] = next(bi for bi, (lo, hi) in enumerate(BUCKETS) if lo <= c["_tgt"] < hi)

rng = random.Random(SEED)
removal_order = {bi: [c["_id"] for c in sorted((x for x in carrier if x["_bucket"] == bi),
                 key=lambda x: x["_id"])] for bi in range(5)}
for bi in removal_order:
    rng.shuffle(removal_order[bi])

fmt = [json.loads(l) for l in open(PROTO) if '"component": "format"' in l]
assert len(fmt) == 200
rng2 = random.Random(SEED)
rng2.shuffle(fmt)                      # frozen nested order; bundle = single item
for i, f in enumerate(fmt):
    f["_id"] = f"fmt_{i:04d}_{f['family_id']}"
    f["_tgt"] = ntok(f["target"])
    f["_bucket"] = next(bi for bi, (lo, hi) in enumerate(BUCKETS) if lo <= f["_tgt"] < hi)

def lf(row):
    return {"instruction": row["prompt"], "input": "", "output": row["target"]}

def make_arm(name, n_fmt):
    ins = fmt[:n_fmt]
    ins_tok = sum(f["_tgt"] for f in ins)
    need = {bi: sum(f["_tgt"] for f in ins if f["_bucket"] == bi) for bi in range(5)}
    removed, rem_tok = [], 0
    for bi in range(5):
        want = need[bi]
        got = 0
        for cid in removal_order[bi]:
            if got >= want or cid in removed:
                continue
            c = next(x for x in carrier if x["_id"] == cid)
            removed.append(cid); got += c["_tgt"]
        rem_tok += got
    keep = [c for c in carrier if c["_id"] not in removed]
    in_tok = sum(ntok(c["instruction"] + "\n" + c["input"]) for c in keep) + sum(ntok(f["prompt"]) for f in ins)
    sq_tok = (sum(seqtok(c["instruction"] + "\n" + c["input"], c["output"]) for c in keep)
              + sum(seqtok(f["prompt"], f["target"]) for f in ins))
    data = [dict(lf_row, ) for lf_row in ([{k: c[k] for k in ("instruction", "input", "output")} for c in keep]
                                          + [lf(f) for f in ins])]
    fname = out / f"data_{name}.json"
    fname.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    tot_tgt = sum(c["_tgt"] for c in keep) + ins_tok
    return {
        "arm": name, "examples": len(data),
        "component_examples": n_fmt, "carrier_examples": len(keep),
        "inserted_ids": [f["_id"] for f in ins], "removed_carrier_ids": removed,
        "component_target_tokens": ins_tok, "removed_target_tokens": rem_tok,
        "total_target_tokens": tot_tgt,
        "total_input_tokens": in_tok,
        "total_sequence_tokens": sq_tok,
        "packed_sequences_est": -(-sq_tok // CUTOFF),
        "q_d": round(ins_tok / tot_tgt, 5) if tot_tgt else 0.0,
        "data_sha256": sha(fname.read_bytes()),
    }

arms = [make_arm("SMK-PLAC-0000", 0), make_arm("SMK-FMT-0060", 60), make_arm("SMK-FMT-0200", 200)]
base_T = arms[0]["total_target_tokens"]
base_S = arms[0]["total_sequence_tokens"]
max_packed = max(a["packed_sequences_est"] for a in arms)
fixed_steps = -(-max_packed // SEQ_PER_STEP) * EPOCHS
for a in arms:
    a["T_dev_pct"] = round(100 * (a["total_target_tokens"] - base_T) / base_T, 3)
    a["S_dev_pct"] = round(100 * (a["total_sequence_tokens"] - base_S) / base_S, 3)
    a["optimizer_updates_fixed"] = fixed_steps
    a["budget_violation"] = abs(a["T_dev_pct"]) > 1.0 or abs(a["S_dev_pct"]) > 1.0

json.dump({"seed": SEED, "buckets": BUCKETS,
           "carrier_n": len(carrier),
           "carrier_note": "loop3 cleanreplay prototype pool n=600; formal 2000-carrier is a later separately-audited build",
           "carrier_sha256": sha(Path(CARRIER).read_bytes()),
           "per_bucket_counts": {bi: len(v) for bi, v in removal_order.items()},
           "removal_order": removal_order},
          open(out / "carrier_manifest.json", "w"), indent=1)
json.dump({"seed": SEED, "component": "format", "bundle": "single-item",
           "nested_prefix_order": [f["_id"] for f in fmt]},
          open(out / "bundle_manifest.json", "w"), indent=1)
json.dump(arms, open(out / "dose_manifest_smoke.json", "w"), indent=1)
json.dump({f"lawv1_{a['arm']}": {"file_name": f"data_{a['arm']}.json"} for a in arms},
          open(out / "dataset_info.json", "w"), indent=1)
print(json.dumps([{k: a[k] for k in ("arm", "examples", "component_examples", "q_d",
                                     "total_target_tokens", "T_dev_pct", "budget_violation")}
                  for a in arms], indent=1))
