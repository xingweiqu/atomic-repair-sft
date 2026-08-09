#!/usr/bin/env python3
"""if_answerability FORMAL pool builder — C-31 line 1 (approved expansion; 2026-08-10).

Pool: if_answerability_pool.jsonl, n=2000 = 1000 same-context answerable/insufficient
pairs from SQuAD v2 train (paired family kept, per C-31):

  * 800 core pairs   — genre A extraction prompt; answerable target = gold span,
    insufficient target = fixed refusal genre (UNANS_TGT of build_if_v2.py);
  * 200 struct pairs — required-field structured record (STATUS/FINAL_ANSWER genre);
    insufficient target = STATUS: INSUFFICIENT / FINAL_ANSWER: NULL.

C-31 requirements implemented:
  * every insufficient row carries meta.subtype in {no_answer_in_passage,
    missing_field}; missing_field (structured required-field type) = 200/1000 = 20%
    of insufficient rows — keeps the false-premise-free sufficiency construct from
    being dominated by a single surface;
  * the 240 seed-20260818 proto rows (if_answerability_v2_proto.jsonl) are MERGED IN
    verbatim (same question ids / prompts / targets; only meta.subtype +
    meta.origin added) — proto ids join the pool once, never duplicated;
  * new families (seed 20260819) exclude every context already consumed by the v2
    protos (answerability families AND old evidence proto incl. donors) and by any
    other C-31 pool manifest on disk;
  * ALL consumed SQuAD context hashes / question ids / titles are registered in
    if_answerability_pool_manifest.json for future IF-eval isolation.

Auto-verification (hard asserts): n / pair structure / subtype counts; gold span in
normalized context; refusal + NULL targets exactly the fixed genres (no leaked
answer); meta.subtype present on every insufficient row with the 20% quota; proto
rows byte-identical on (prompt, target, source_id); no duplicate prompts or
question ids; naturalset isolation; cross-pool context disjointness; family-level
non-skeleton 8-gram target dup rate reported.

Deterministic: SEED=20260819. Output not committed (C-31 交付纪律 handled at review).
"""
import json
import random
from collections import Counter
from pathlib import Path

import if_build_lib as L
import build_if_v2 as v2

OUT = L.OUT
SEED = L.SEED
GEN_VER = "ifpool-v1.0"

N_CORE_PAIRS = 800     # includes the 100 proto core pairs
N_STRUCT_PAIRS = 200   # includes the 20 proto struct pairs -> missing_field = 20%

INSUFF_SUBTYPE = {"unanswerable": "no_answer_in_passage",
                  "struct_insufficient": "missing_field"}


def load_proto_rows():
    p = OUT / "if_answerability_v2_proto.jsonl"
    rows = [json.loads(l) for l in p.open()]
    assert len(rows) == 240, len(rows)
    for r in rows:
        r["meta"]["origin"] = "v2_proto_seed20260818"
        if r["subtype"] in INSUFF_SUBTYPE:
            r["meta"]["subtype"] = INSUFF_SUBTYPE[r["subtype"]]
    return rows


def build_new_pairs(by_ctx, exclude_ctx, n_core, n_struct):
    keys = [k for k, v in by_ctx.items()
            if k not in exclude_ctx and v["ans"] and v["una"]
            and v2.CTX_MIN <= len(v["ctx"]) <= v2.CTX_MAX]
    random.Random(SEED).shuffle(keys)
    rows, used, c_core, c_struct = [], set(), 0, 0
    for k in keys:
        if c_core >= n_core and c_struct >= n_struct:
            break
        v = by_ctx[k]
        a = min(v["ans"], key=lambda x: x["id"])
        u = min(v["una"], key=lambda x: x["id"])
        if L.norm(a["q"]).lower() == L.norm(u["q"]).lower():
            continue
        ctx = L.norm(v["ctx"])
        if a["gold"] not in ctx:
            continue
        common = dict(family_id=f"squadv2_ctx_{k}", source_split="train",
                      generator_id="A", generator_version=GEN_VER,
                      component="answerability", domain="general_if")
        meta = {"title": v["title"], "context_hash": k, "origin": "pool_seed20260819"}
        if c_core < n_core:
            rows.append(dict(common, subtype="answerable", source_id=a["id"],
                             prompt=v2.CORE_PROMPT.format(ctx=ctx, q=a["q"]),
                             target=a["gold"], meta=dict(meta)))
            rows.append(dict(common, subtype="unanswerable", source_id=u["id"],
                             prompt=v2.CORE_PROMPT.format(ctx=ctx, q=u["q"]),
                             target=v2.UNANS_TGT,
                             meta=dict(meta, subtype="no_answer_in_passage")))
            c_core += 1
        else:
            f_ok, f_null = v2.field_name(a["q"]), v2.field_name(u["q"])
            if not f_ok or not f_null or f_ok == f_null:
                continue
            rows.append(dict(common, subtype="struct_found", source_id=a["id"],
                             prompt=v2.STRUCT_PROMPT.format(ctx=ctx, field=f_ok, q=a["q"]),
                             target=v2.STRUCT_OK_TGT.format(span=a["gold"]),
                             meta=dict(meta)))
            rows.append(dict(common, subtype="struct_insufficient", source_id=u["id"],
                             prompt=v2.STRUCT_PROMPT.format(ctx=ctx, field=f_null, q=u["q"]),
                             target=v2.STRUCT_NULL_TGT,
                             meta=dict(meta, subtype="missing_field")))
            c_struct += 1
        used.add(k)
    assert c_core == n_core and c_struct == n_struct, (c_core, c_struct)
    return rows, used


def verify(rows, by_ctx, proto_rows, ns_txt, ns_ids, other_sq):
    errs = []
    if len(rows) != 2 * (N_CORE_PAIRS + N_STRUCT_PAIRS):
        errs.append(("bad_n", len(rows)))
    # pair structure: each family exactly 2 rows, one answerable-side + one insufficient-side
    fam = {}
    for r in rows:
        fam.setdefault(r["family_id"], []).append(r["subtype"])
    for fid, subs in fam.items():
        if sorted(subs) not in (["answerable", "unanswerable"],
                                ["struct_found", "struct_insufficient"]):
            errs.append(("broken_pair", fid, subs))
    sc = Counter(r["subtype"] for r in rows)
    if not (sc["answerable"] == sc["unanswerable"] == N_CORE_PAIRS
            and sc["struct_found"] == sc["struct_insufficient"] == N_STRUCT_PAIRS):
        errs.append(("bad_subtype_counts", dict(sc)))
    # meta.subtype quota on insufficient rows
    ms = Counter(r["meta"].get("subtype") for r in rows
                 if r["subtype"] in ("unanswerable", "struct_insufficient"))
    if ms != Counter({"no_answer_in_passage": N_CORE_PAIRS, "missing_field": N_STRUCT_PAIRS}):
        errs.append(("bad_meta_subtype", dict(ms)))
    if any("subtype" in r["meta"] for r in rows
           if r["subtype"] in ("answerable", "struct_found")):
        errs.append(("meta_subtype_on_answerable_row",))
    # uniqueness
    if len({r["prompt"] for r in rows}) != len(rows):
        errs.append(("dup_prompt",))
    ids = [r["source_id"] for r in rows]
    if len(set(ids)) != len(ids):
        errs.append(("dup_question_id",))
    # proto rows merged verbatim, exactly once
    by_id = {r["source_id"]: r for r in rows}
    for pr in proto_rows:
        r = by_id.get(pr["source_id"])
        if r is None or r["prompt"] != pr["prompt"] or r["target"] != pr["target"] \
                or r["family_id"] != pr["family_id"]:
            errs.append(("proto_row_not_merged_verbatim", pr["source_id"]))
    # per-row content checks
    for r in rows:
        for k in ("family_id", "component", "subtype", "prompt", "target",
                  "source_id", "source_split", "generator_id", "domain"):
            if not r.get(k):
                errs.append(("missing_field", k, r.get("family_id")))
        if L.norm(r["prompt"]) in ns_txt or r["source_id"] in ns_ids:
            errs.append(("naturalset_leak", r["family_id"]))
        ctx = L.norm(by_ctx[r["meta"]["context_hash"]]["ctx"])
        t = r["target"]
        if r["subtype"] in ("answerable", "struct_found"):
            span = t if r["subtype"] == "answerable" else t.split("FINAL_ANSWER:")[-1].strip()
            if span not in ctx:
                errs.append(("gold_span_not_in_context", r["family_id"]))
        elif r["subtype"] == "unanswerable":
            if t != v2.UNANS_TGT:
                errs.append(("refusal_genre_broken", r["family_id"]))
        else:
            if t != v2.STRUCT_NULL_TGT:
                errs.append(("insufficient_genre_broken", r["family_id"]))
    # cross-pool context disjointness (other C-31 pools already on disk)
    own_ctx = {r["meta"]["context_hash"] for r in rows}
    if own_ctx & other_sq:
        errs.append(("cross_pool_context_collision", len(own_ctx & other_sq)))
    return errs


def main():
    squad_rows, parquet_path = L.load_squad()
    ns_txt, ns_ids = L.load_ns()
    by_ctx, _ = L.index_squad(squad_rows)

    proto_rows = load_proto_rows()
    v2_all_ctx, v2_ans_ctx = L.v2_proto_registry()
    other_sq, _, _ = L.other_pool_registries("if_answerability_pool")

    # new families exclude: every v2-proto context (both pools, donors included),
    # and every context registered by other C-31 pools already built
    exclude = v2_all_ctx | other_sq
    n_core_new = N_CORE_PAIRS - sum(1 for r in proto_rows if r["subtype"] == "answerable")
    n_struct_new = N_STRUCT_PAIRS - sum(1 for r in proto_rows if r["subtype"] == "struct_found")
    new_rows, used_new = build_new_pairs(by_ctx, exclude, n_core_new, n_struct_new)

    rows = proto_rows + new_rows
    # stable order: core pairs first then struct, proto families first within each
    order = {"answerable": 0, "unanswerable": 1, "struct_found": 2, "struct_insufficient": 3}
    rows.sort(key=lambda r: (order[r["subtype"]] // 2, r["meta"]["origin"] != "v2_proto_seed20260818",
                             r["family_id"], order[r["subtype"]]))

    errs = verify(rows, by_ctx, proto_rows, ns_txt, ns_ids, other_sq)
    assert not errs, errs[:20]

    content_grams = L.make_content_grams([v2.CORE_PROMPT, v2.UNANS_TGT, v2.STRUCT_PROMPT,
                                          v2.STRUCT_OK_TGT, v2.STRUCT_NULL_TGT])
    dup_rate = L.family_dup_rate(rows, content_grams)

    manifest = {
        "pool": "if_answerability_pool", "status": "FORMAL (C-31 approved expansion)",
        "seed": SEED, "generator_version": GEN_VER, "instruction": "C-31 line 1 (C-30 #4 construct)",
        "source": {"dataset": "rajpurkar/squad_v2", "split": "train",
                   "parquet": Path(parquet_path).name, "license": "CC BY-SA 4.0"},
        "composition": {
            "pairs_core": N_CORE_PAIRS, "pairs_struct": N_STRUCT_PAIRS,
            "insufficient_meta_subtype": {"no_answer_in_passage": N_CORE_PAIRS,
                                          "missing_field": N_STRUCT_PAIRS},
            "missing_field_share_of_insufficient": N_STRUCT_PAIRS / (N_CORE_PAIRS + N_STRUCT_PAIRS),
            "merged_proto": {"file": "if_answerability_v2_proto.jsonl", "n_rows": len(proto_rows),
                             "note": "seed-20260818 proto rows merged verbatim (ids not duplicated); "
                                     "meta.origin/meta.subtype added"}},
        "verify_errors": [], "nonskeleton_8gram_dup_rate_family": dup_rate,
        "isolation_note": (
            "ALL SQuAD ids/titles/context hashes below are consumed for TRAINING; any "
            "future IF eval built on SQuAD (incl. format F-A eval carriers) must exclude "
            "them. SQuAD dev split remains untouched/reserved for eval. New families also "
            "exclude every old-v2-proto context (evidence donors included)."),
        "registry": {
            "context_hashes": sorted({r["meta"]["context_hash"] for r in rows}),
            "squad_question_ids": sorted({r["source_id"] for r in rows}),
            "squad_titles": sorted({r["meta"]["title"] for r in rows}),
        },
    }
    L.write_pool("if_answerability_pool", rows, manifest)
    L.write_sample("if_answerability_pool", rows, 3, 12)

    print(json.dumps({k: manifest[k] for k in
                      ("n", "sha256_16", "by_subtype", "n_families",
                       "nonskeleton_8gram_dup_rate_family", "target_length_buckets")}, indent=2))
    print("verify_errors: []")


if __name__ == "__main__":
    main()
