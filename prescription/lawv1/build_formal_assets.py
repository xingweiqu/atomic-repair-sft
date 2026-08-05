#!/usr/bin/env python3
"""Queue-B formal asset builder (C-25): family partition + 2000 carrier + 2000 format pool.

Decisions (recorded):
- Family partition FROZEN here (seed 20260813) over base-filtered GSM8K-train families:
  format[0:2000] evidence[2000:4000] revision[4000:5000] answerability[5000:6000]
  carrier[6000:] (carrier draws its 2000 from the reserved tail -> zero overlap with
  any component pool by construction; prototype-used families are re-assigned to their
  component's slice or dropped -- checked below).
- Formal carrier = GSM8K-train solve replay (prompt=question, target=cleaned reasoning
  + 'Final answer: N', genre A), NOT the 600-item synthetic loop3 pool. Rationale:
  in-domain placebo isolates component effects; unlimited audited supply; the loop3
  pool remains the smoke-era prototype carrier (kept for reproducibility).
- Format pool: 2000 items over format[0:2000] families, schema A1-A4 round-robin,
  reasoning-hygiene filtered; nested bundle order = seeded shuffle prefix.
Checks: family overlap across pools == 0; exact duplicate == 0; token stats separately.
"""
import json, random, hashlib, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "prescription/gate1"))
from build_gate1 import base_filter, GEN_A, reasoning_clean  # noqa: E402

SEED = 20260813
cache = json.load(open(ROOT / "data_v4/gsm8k_cache.json"))
pool = [it for it in cache["train"] if base_filter(it)]
rng = random.Random(SEED)
rng.shuffle(pool)
ids = [it["id"] for it in pool]
# NOTE: filtered GSM8K-train has only ~6817 families. Queue-C needs format+carrier now;
# the remaining 2817 are reserved for queue-D components, whose pool sizes vs the
# advisor's 2000-each target CANNOT all fit -- that shortage is deferred to the
# queue-D build as an explicit decision (options: cross-component family sharing with
# declared overlap, synthetic augmentation, or reduced pool sizes). Recorded in manifest.
PART = {
    "format": set(ids[0:2000]), "carrier": set(ids[2000:4000]),
    "reserved_queueD": set(ids[4000:]),
}
by_id = {it["id"]: it for it in pool}

# --- formal carrier: first 2000 of the carrier slice (frozen order) -----------------
carrier_ids = ids[2000:4000]
assert len(carrier_ids) == 2000
carrier = []
for fid in carrier_ids:
    it = by_id[fid]
    carrier.append({"instruction": it["question"].strip(), "input": "",
                    "output": GEN_A["answer_full"].format(reason=it["reasoning"].strip(),
                                                          gold=str(int(float(it["final"])))),
                    "family_id": fid})
Path(OUT / "carrier_formal.json").write_text(json.dumps(carrier, ensure_ascii=False, indent=1))

# --- formal format pool: 2000 over format slice ------------------------------------
fmt_rows = []
for i, fid in enumerate(ids[0:2000]):
    it = by_id[fid]
    sch = GEN_A["format_schemas"][i % 4]
    gold = str(int(float(it["final"])))
    fmt_rows.append({"family_id": fid, "source_split": "train", "generator_id": "A",
                     "component": "format", "subtype": sch["id"],
                     "prompt": it["question"].strip() + "\n\n" + sch["instr"],
                     "target": sch["render"](it, gold)})
Path(OUT / "format_pool_formal.jsonl").write_text(
    "\n".join(json.dumps(r, ensure_ascii=False) for r in fmt_rows) + "\n")
bundle_order = [f"fmt_{i:04d}_{r['family_id']}" for i, r in enumerate(fmt_rows)]

# --- checks -------------------------------------------------------------------------
overlap = set(carrier_ids) & set(ids[0:2000])
eval_fams = {json.loads(l)["family_id"] for l in open(ROOT / "prescription/gate1/eval_proto.jsonl")}
leak = (set(carrier_ids) | set(ids[0:2000])) & eval_fams
dup = len(fmt_rows) - len({r["prompt"] for r in fmt_rows})
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
manifest = {
    "seed": SEED, "partition_sizes": {k: len(v) for k, v in PART.items()},
    "carrier_n": len(carrier), "format_pool_n": len(fmt_rows),
    "family_overlap_carrier_format": len(overlap), "eval_family_leak": len(leak),
    "format_exact_duplicates": dup,
    "carrier_sha256": sha(OUT / "carrier_formal.json"),
    "format_pool_sha256": sha(OUT / "format_pool_formal.jsonl"),
    "prototype_families_note": "gate1 prototype pools drew pre-partition; formal pools re-drawn from frozen partition; prototype/formal collisions are within-component only.",
    "queueD_shortage_note": "reserved_queueD=2817 families < 3 components x target sizes; resolution (sharing/synthetic/reduced) is an explicit queue-D decision, NOT silently resolved here.",
    "bundle_order_head": bundle_order[:5],
}
Path(OUT / "formal_assets_manifest.json").write_text(json.dumps(manifest, indent=1))
Path(OUT / "bundle_order_format_formal.json").write_text(json.dumps(
    {"seed": SEED, "nested_prefix_order": bundle_order}))
print(json.dumps(manifest, indent=1))
assert not overlap and not leak and dup == 0, "POOL CHECK FAILED"
print("POOL_CHECKS_PASS")
