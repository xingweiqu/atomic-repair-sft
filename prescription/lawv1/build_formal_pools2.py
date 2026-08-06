#!/usr/bin/env python3
"""Formal Reasoning evidence/revision pools (C-26 GPU queue #1-2).

Families from the frozen reserved slice (build_formal_assets partition, seed 20260813):
  evidence  = reserved[0:2000]
  revision  = reserved[1817:2817] (1000 fams -> 2000 paired examples)
  DECLARED overlap evidence∩revision = reserved[1817:2000] = 183 families (intra-domain,
  cross-component sharing; forced by GSM8K-train supply of 6817 filtered families.
  Advisor-flagged decision: recorded here, surfaced in manifest, NOT silent).
Generators = gate1 v1.2 machinery (approved for smoke prep by C-24). Hygiene verified.
"""
import json, hashlib, sys, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "prescription/gate1"))
import build_gate1 as G  # noqa: E402

SEED = 20260813
cache = json.load(open(ROOT / "data_v4/gsm8k_cache.json"))
pool = [it for it in cache["train"] if G.base_filter(it)]
random.Random(SEED).shuffle(pool)
ids = [it["id"] for it in pool]
reserved = ids[4000:]
by_id = {it["id"]: it for it in pool}
ev_f, rev_f = reserved[0:2000], reserved[1817:2817]
assert len(ev_f) == 2000 and len(rev_f) == 1000

def evid_item(it, sub):
    st = next((s for s in it["steps"] if G.re.search(r"\d\s*[\+\-\*\/x]\s*\d", s["expr"])), None)
    if st is None:
        return None
    gold = str(int(float(it["final"])))
    q = it["question"].strip()
    bad = str(int(float(st["result"])) + (1 + G.h(it["id"]) % 3)) if G.intish(st["result"]) else "99"
    if sub == 0:
        inj, dm = G.pick_distractor(q, it["id"], G.GEN_A["evid_irrelevant"], "evd")
        tgt = G.GEN_A["evid_target_ignore"].format(item=dm["item"], reason=it["reasoning"].strip(), gold=gold)
        s = "irrelevant"
    elif sub == 1:
        inj = G.GEN_A["evid_wrong_step"].format(expr=st["expr"], bad=bad)
        tgt = G.GEN_A["evid_target_refute"].format(expr=st["expr"], good=st["result"], bad=bad,
                                                  reason=it["reasoning"].strip(), gold=gold)
        s = "wrong_step"
    else:
        inj = G.GEN_A["evid_conflict"].format(expr=st["expr"], good=st["result"], bad=bad)
        tgt = G.GEN_A["evid_target_conflict"].format(expr=st["expr"], good=st["result"],
                                                    reason=it["reasoning"].strip(), gold=gold)
        s = "conflict"
    if not G.reasoning_clean(tgt):
        return None
    return dict(family_id=it["id"], component="evidence_robustness", subtype=s,
                prompt=q + "\n\n" + inj, target=tgt)

ev_rows, i = [], 0
for fid in ev_f:
    r = evid_item(by_id[fid], i % 3)
    if r:
        ev_rows.append(r); i += 1
print("evidence rows:", len(ev_rows))

rev_rows = []
for fid in rev_f:
    it = by_id[fid]
    gold = str(int(float(it["final"])))
    q = it["question"].strip()
    chain = [f"{s['expr']} = {s['result']}" for s in it["steps"]]
    rng = G.rng_for(fid, "rev")
    et, wv, ws = G.wrong_process(it, rng)
    rev_rows.append(dict(family_id=fid, component="selective_revision", subtype="keep",
                         prompt=G.GEN_A["revise_prompt"].format(q=q, attempt=G.render_attempt_A(chain, gold)),
                         target=G.GEN_A["revise_keep"].format(gold=gold)))
    wrong_i = next((k for k, (a, b) in enumerate(zip(chain, ws)) if a != b), len(ws) - 1) \
        if len(ws) == len(chain) else len(ws)
    if et == "dropped_step":
        tgt = G.GEN_A["revise_fix_missing"].format(laststep=chain[-1], gold=gold)
    else:
        i0 = min(wrong_i, len(chain) - 1)
        tgt = G.GEN_A["revise_fix"].format(i=i0 + 1, expr_good=chain[i0],
                                           fixtail="\n".join(chain[i0:]), gold=gold)
    rev_rows.append(dict(family_id=fid, component="selective_revision", subtype="fix",
                         meta={"error_type": et},
                         prompt=G.GEN_A["revise_prompt"].format(q=q, attempt=G.render_attempt_A(ws, wv)),
                         target=tgt))
print("revision rows:", len(rev_rows))

bad = [r for r in ev_rows + rev_rows if not G.reasoning_clean(r["target"])]
eval_fams = {json.loads(l)["family_id"] for l in open(ROOT / "prescription/gate1/eval_proto.jsonl")}
leak = ({r["family_id"] for r in ev_rows} | {r["family_id"] for r in rev_rows}) & eval_fams
Path(OUT / "evidence_pool_formal.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in ev_rows) + "\n")
Path(OUT / "revision_pool_formal.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rev_rows) + "\n")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]
man = dict(seed=SEED, evidence_n=len(ev_rows), revision_n=len(rev_rows),
           declared_overlap_families=len(set(ev_f) & set(rev_f)),
           target_hygiene_bad=len(bad), eval_leak=len(leak),
           evidence_sha=sha(OUT / "evidence_pool_formal.jsonl"),
           revision_sha=sha(OUT / "revision_pool_formal.jsonl"))
Path(OUT / "pools2_manifest.json").write_text(json.dumps(man, indent=1))
print(json.dumps(man, indent=1))
assert not bad and not leak
print("POOLS2_CHECKS_PASS")
