#!/usr/bin/env python3
"""if_format FORMAL pool builder — C-31 line 3 (route F-A approved in C-30 #1).

Pool: if_format_pool.jsonl, n=2000, component=format. Carrier tasks (半/半):

  * 1000 SQuAD v2 train ANSWERABLE extraction rows (one question per context;
    contexts disjoint from every other C-31 pool), train schema set A:
      A1 (500): {"answer": str}
      A2 (500): {"answer": str, "evidence_span": str}   (evidence_span = the
                context sentence containing the gold span)
  * 1000 AG-News train classification rows (cleaned, deduplicated), labels
    World / Sports / Business / Sci/Tech:
      A3 (500): {"label": str}
      A4 (500): line format  label: <label>

Schema rotation: within each carrier the two schemas alternate row-by-row in
build order (四式轮转 A1,A2,... / A3,A4,...); eval will use a DISJOINT schema set
B (TRAIN_EVAL_SEPARATION; not built here). Every target is program-verifiable —
the build re-parses each target with the same schema validators used by
if_scorer.py-style logic and asserts: JSON parse + exact key set + answer ==
gold span present in context / evidence_span in context and containing the
answer / label == gold label; A4 exact line form.

Auto-verification also: counts (500 per schema), no duplicate prompts, no
naturalset overlap, zero SQuAD-context / AG-News-article intersection with the
other C-31 pools, family-level non-skeleton 8-gram dup rate. Registry: all
SQuAD context hashes / question ids / titles and AG-News row indices + text
hashes (for replay-pool disjointness and future IF-eval isolation).

Deterministic: SEED=20260819. IFEval remains eval-only holdout (never built here).
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

N_EXTRACT = 1000   # A1/A2 500 each
N_CLASSIFY = 1000  # A3/A4 500 each

EXT_PROMPT = ("Passage:\n{ctx}\n\nQuestion: {q}\n\n{schema}")
SCHEMA_A1 = ('Return your answer as a JSON object with exactly this form:\n'
             '{"answer": "<exact answer span from the passage>"}\n'
             'Output the JSON object only.')
SCHEMA_A2 = ('Return your answer as a JSON object with exactly this form:\n'
             '{"answer": "<exact answer span from the passage>", '
             '"evidence_span": "<the passage sentence that contains the answer>"}\n'
             'Output the JSON object only.')

CLS_PROMPT = ("News article:\n{text}\n\nClassify the article into exactly one "
              "category out of: World, Sports, Business, Sci/Tech.\n\n{schema}")
SCHEMA_A3 = ('Return your answer as a JSON object with exactly this form:\n'
             '{"label": "<one of World, Sports, Business, Sci/Tech>"}\n'
             'Output the JSON object only.')
SCHEMA_A4 = ('Return your answer as exactly one line of the form:\n'
             'label: <one of World, Sports, Business, Sci/Tech>\n'
             'Output that single line only.')

SKELETON = [EXT_PROMPT, SCHEMA_A1, SCHEMA_A2, CLS_PROMPT, SCHEMA_A3, SCHEMA_A4]


# ---- schema validators (mirrored by if_scorer.py; used here on gold targets)
def parse_json_obj(text, keys):
    try:
        obj = json.loads(text.strip())
    except Exception:
        return None
    if not isinstance(obj, dict) or set(obj) != set(keys):
        return None
    if not all(isinstance(obj[k], str) and obj[k] for k in keys):
        return None
    return obj


def validate_target(schema_id, target, ctx=None, gold=None, ev=None, label=None):
    if schema_id == "A1":
        o = parse_json_obj(target, ["answer"])
        return o and o["answer"] == gold and gold in ctx
    if schema_id == "A2":
        o = parse_json_obj(target, ["answer", "evidence_span"])
        return (o and o["answer"] == gold and gold in ctx
                and o["evidence_span"] == ev and ev in ctx and gold in ev)
    if schema_id == "A3":
        o = parse_json_obj(target, ["label"])
        return o and o["label"] == label and label in L.AG_LABELS
    if schema_id == "A4":
        return target == f"label: {label}" and label in L.AG_LABELS
    return False


def build_extract(by_ctx, exclude_ctx):
    keys = [k for k, v in by_ctx.items()
            if k not in exclude_ctx and v["ans"]
            and v2.CTX_MIN <= len(v["ctx"]) <= v2.CTX_MAX]
    random.Random(SEED).shuffle(keys)
    rows = []
    for k in keys:
        if len(rows) >= N_EXTRACT:
            break
        v = by_ctx[k]
        ctx = L.norm(v["ctx"])
        cand, ev = None, None
        for a in sorted(v["ans"], key=lambda x: x["id"]):
            if a["gold"] not in ctx:
                continue
            e = v2.evidence_sentence(v["ctx"], a["start"], a["gold"])
            if e and e in ctx:
                cand, ev = a, e
                break
        if cand is None:
            continue
        schema_id = "A1" if len(rows) % 2 == 0 else "A2"
        schema = SCHEMA_A1 if schema_id == "A1" else SCHEMA_A2
        if schema_id == "A1":
            target = json.dumps({"answer": cand["gold"]}, ensure_ascii=False)
        else:
            target = json.dumps({"answer": cand["gold"], "evidence_span": ev},
                                ensure_ascii=False)
        assert validate_target(schema_id, target, ctx=ctx, gold=cand["gold"], ev=ev)
        rows.append(dict(
            family_id=f"squadv2_ctx_{k}", source_id=cand["id"], source_split="train",
            generator_id="A", generator_version=GEN_VER, component="format",
            domain="general_if", subtype=f"extract_{schema_id}", schema_id=schema_id,
            prompt=EXT_PROMPT.format(ctx=ctx, q=cand["q"], schema=schema),
            target=target,
            meta={"title": v["title"], "context_hash": k, "question": cand["q"],
                  "gold": cand["gold"], "evidence_sentence": ev, "carrier": "squad_v2"}))
    assert len(rows) == N_EXTRACT, len(rows)
    return rows


def build_classify(ag_rows, exclude_ag):
    pool = [r for r in ag_rows if r["text_hash"] not in exclude_ag]
    random.Random(SEED + 1).shuffle(pool)
    # balance labels 250 per class per schema
    per_label = N_CLASSIFY // len(L.AG_LABELS)
    picked, cnt = [], Counter()
    for r in pool:
        if cnt[r["label_name"]] >= per_label:
            continue
        picked.append(r)
        cnt[r["label_name"]] += 1
        if len(picked) >= N_CLASSIFY:
            break
    assert len(picked) == N_CLASSIFY, len(picked)
    rows = []
    for i, r in enumerate(picked):
        schema_id = "A3" if i % 2 == 0 else "A4"
        schema = SCHEMA_A3 if schema_id == "A3" else SCHEMA_A4
        target = (json.dumps({"label": r["label_name"]}, ensure_ascii=False)
                  if schema_id == "A3" else f"label: {r['label_name']}")
        assert validate_target(schema_id, target, label=r["label_name"])
        rows.append(dict(
            family_id=f"agnews_train_{r['idx']}", source_id=f"agnews_train_{r['idx']}",
            source_split="train", generator_id="A", generator_version=GEN_VER,
            component="format", domain="general_if",
            subtype=f"classify_{schema_id}", schema_id=schema_id,
            prompt=CLS_PROMPT.format(text=r["text"], schema=schema), target=target,
            meta={"agnews_text_hash": r["text_hash"], "label": r["label_name"],
                  "carrier": "ag_news"}))
    return rows


def verify(rows, by_ctx, ns_txt, other_sq, other_ag):
    errs = []
    if len(rows) != N_EXTRACT + N_CLASSIFY:
        errs.append(("bad_n", len(rows)))
    sc = Counter(r["schema_id"] for r in rows)
    if dict(sc) != {"A1": 500, "A2": 500, "A3": 500, "A4": 500}:
        errs.append(("bad_schema_rotation", dict(sc)))
    if len({r["prompt"] for r in rows}) != len(rows):
        errs.append(("dup_prompt",))
    fams = [r["family_id"] for r in rows]
    if len(set(fams)) != len(fams):
        errs.append(("dup_family",))
    for r in rows:
        for k in ("family_id", "component", "subtype", "prompt", "target",
                  "source_id", "source_split", "generator_id", "domain", "schema_id"):
            if not r.get(k):
                errs.append(("missing_field", k, r.get("family_id")))
        if L.norm(r["prompt"]) in ns_txt:
            errs.append(("naturalset_leak", r["family_id"]))
        if r["schema_id"] in ("A1", "A2"):
            ctx = L.norm(by_ctx[r["meta"]["context_hash"]]["ctx"])
            ok = validate_target(r["schema_id"], r["target"], ctx=ctx,
                                 gold=r["meta"]["gold"],
                                 ev=r["meta"]["evidence_sentence"])
        else:
            ok = validate_target(r["schema_id"], r["target"], label=r["meta"]["label"])
        if not ok:
            errs.append(("target_not_program_verifiable", r["family_id"]))
    own_sq = {r["meta"]["context_hash"] for r in rows if "context_hash" in r["meta"]}
    own_ag = {r["meta"]["agnews_text_hash"] for r in rows if "agnews_text_hash" in r["meta"]}
    if own_sq & other_sq:
        errs.append(("cross_pool_squad_collision", len(own_sq & other_sq)))
    if own_ag & other_ag:
        errs.append(("cross_pool_agnews_collision", len(own_ag & other_ag)))
    return errs, own_sq, own_ag


def main():
    squad_rows, parquet_path = L.load_squad()
    ns_txt, _ = L.load_ns()
    by_ctx, _ = L.index_squad(squad_rows)
    ag_rows, ag_parquet = L.load_agnews()

    other_sq, other_ag, _ = L.other_pool_registries("if_format_pool")
    v2_all_ctx, _ = L.v2_proto_registry()
    exclude_ctx = other_sq | v2_all_ctx

    ext = build_extract(by_ctx, exclude_ctx)
    cls = build_classify(ag_rows, other_ag)
    # 四式轮转 assembly: interleave carriers so file order cycles A1,A3,A2,A4,...
    rows = []
    for a, b in zip(ext, cls):
        rows += [a, b]

    errs, own_sq, own_ag = verify(rows, by_ctx, ns_txt, other_sq, other_ag)
    assert not errs, errs[:20]

    dup_rate = L.family_dup_rate(rows, L.make_content_grams(SKELETON))
    label_dist = Counter(r["meta"]["label"] for r in rows if "label" in r["meta"])
    manifest = {
        "pool": "if_format_pool", "status": "FORMAL (route F-A, C-30 #1 approved)",
        "seed": SEED, "generator_version": GEN_VER, "instruction": "C-31 line 3",
        "source": {
            "squad": {"dataset": "rajpurkar/squad_v2", "split": "train",
                      "parquet": Path(parquet_path).name, "license": "CC BY-SA 4.0"},
            "agnews": {"dataset": "fancyzhx/ag_news", "split": "train",
                       "parquet": ag_parquet,
                       "license": "custom research use (announced free for research; "
                                  "verify on freeze)"}},
        "schemas": {"A1": SCHEMA_A1, "A2": SCHEMA_A2, "A3": SCHEMA_A3, "A4": SCHEMA_A4,
                    "note": "train set A only; eval uses disjoint schema set B "
                            "(not built here); IFEval = eval-only holdout, never trained"},
        "classify_label_dist": dict(label_dist),
        "verify_errors": [], "nonskeleton_8gram_dup_rate_family": dup_rate,
        "isolation_note": (
            "SQuAD contexts and AG-News articles below are consumed for training; "
            "disjoint from every other C-31 pool and from all v2 proto contexts. "
            "Future IF evals on SQuAD/AG-News must exclude these registries."),
        "registry": {
            "context_hashes": sorted(own_sq),
            "squad_question_ids": sorted({r["source_id"] for r in rows
                                          if r["meta"].get("carrier") == "squad_v2"}),
            "squad_titles": sorted({r["meta"]["title"] for r in rows
                                    if "title" in r["meta"]}),
            "agnews_text_hashes": sorted(own_ag),
            "agnews_row_indices": sorted(int(r["family_id"].split("_")[-1]) for r in rows
                                         if r["family_id"].startswith("agnews_")),
        },
    }
    L.write_pool("if_format_pool", rows, manifest)
    L.write_sample("if_format_pool", rows, 3, 12)

    print(json.dumps({k: manifest[k] for k in
                      ("n", "sha256_16", "by_subtype", "n_families",
                       "classify_label_dist", "nonskeleton_8gram_dup_rate_family")}, indent=2))
    print("verify_errors: []")


if __name__ == "__main__":
    main()
