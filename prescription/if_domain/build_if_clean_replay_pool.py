#!/usr/bin/env python3
"""if_clean_replay FORMAL pool builder — C-31 line 4 (route R-A approved, C-30 #2).

Pool: if_clean_replay_pool.jsonl, n=2000, component=clean_replay (control /
carrier: same distribution family as the IF component pools, NO component
structure, plain natural-language targets, no schema instruction):

  * 800 CREPE-normal rows  — plain ELI5-style QA: prompt = the question, target =
    the reference comment, cleaned + clipped at a sentence boundary (control need
    not be program-verifiable per IF_SOURCES_PROPOSAL R-A note);
  * 700 SQuAD v2 plain QA  — passage + question, plain instruction wording
    (distinct from the answerability genre-A prompt), target = the gold span;
  * 500 AG-News plain classification — plain "what kind of news" question,
    target = a plain sentence naming the category (no schema).

C-31 requirements: zero family/context intersection with the other three C-31
pools (SQuAD contexts, AG-News articles, CREPE families — hard-asserted against
their manifests; CREPE-normal rows are additionally label-disjoint from the
fp-only if_revision proto and split-disjoint from naturalset CREPE-test);
5-length-bucket target distribution reported in the manifest (carrier spec,
CONTRACT_DATA §3.5).

Auto-verification: counts per source; no duplicate prompts/families; no schema
tokens in prompts (JSON braces / "label:" line forms); refusal-genre and
component-genre skeletons absent (replay must carry no component surface);
naturalset isolation; cross-pool disjointness; family-level 8-gram dup rate
(no skeleton subtraction needed beyond the three short plain templates).

Deterministic: SEED=20260819.
"""
import json
import random
import re
from collections import Counter
from pathlib import Path

import if_build_lib as L
import build_if_v2 as v2

OUT = L.OUT
SEED = L.SEED
GEN_VER = "ifpool-v1.0"

N_CREPE, N_SQUAD, N_AG = 800, 700, 500

PLAIN_QA_PROMPT = ("Read the passage and answer the question briefly.\n\n"
                   "Passage:\n{ctx}\n\nQuestion: {q}")
PLAIN_CLS_PROMPT = "{text}\n\nWhat kind of news story is this?"
PLAIN_CLS_TGT = "This is a {desc} news story."
AG_DESC = {"World": "world", "Sports": "sports", "Business": "business",
           "Sci/Tech": "science and technology"}

SKELETON = [PLAIN_QA_PROMPT, PLAIN_CLS_PROMPT, PLAIN_CLS_TGT]

# component-genre skeleton phrases that must NOT appear in replay rows
COMPONENT_MARKERS = [
    "if the passage does not contain", "STATUS:", "FINAL_ANSWER:",
    "Return exactly two lines", "JSON object", "label: <", "Note:",
    "Someone believes the answer is", "Exactly one of the passages",
    "Check the candidate response",
]

URLISH = re.compile(r"https?://|www\.")


def clip_comment(text, max_chars=600, min_chars=80):
    """Normalized comment clipped at the last sentence end <= max_chars."""
    t = L.norm(text)
    if len(t) <= max_chars:
        return t
    cut = t[:max_chars]
    best = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
    if best >= min_chars:
        return cut[:best + 1]
    return None


def build_crepe(exclude_crepe, ns_txt):
    rows_src = L.load_crepe_normal()
    rng = random.Random(SEED)
    rng.shuffle(rows_src)
    rows = []
    for r in rows_src:
        if len(rows) >= N_CREPE:
            break
        if r["id"] in exclude_crepe:
            continue
        q = L.norm(r["question"])
        if not (20 <= len(q) <= 300) or L.norm(q) in ns_txt:
            continue
        c = clip_comment(r["comment"])
        if c is None or len(c) < 80 or URLISH.search(c) or URLISH.search(q):
            continue
        if not L.PRINTABLE.match(q):
            continue
        rows.append(dict(
            family_id=f"crepe_train_{r['id']}", source_id=r["id"], source_split="train",
            generator_id="A", generator_version=GEN_VER, component="clean_replay",
            domain="general_if", subtype="plain_eli5_qa", prompt=q, target=c,
            meta={"carrier": "crepe_normal"}))
    assert len(rows) == N_CREPE, len(rows)
    return rows


def build_squad(by_ctx, exclude_ctx):
    keys = [k for k, v in by_ctx.items()
            if k not in exclude_ctx and v["ans"]
            and v2.CTX_MIN <= len(v["ctx"]) <= v2.CTX_MAX]
    random.Random(SEED + 1).shuffle(keys)
    rows = []
    for k in keys:
        if len(rows) >= N_SQUAD:
            break
        v = by_ctx[k]
        ctx = L.norm(v["ctx"])
        cand = next((a for a in sorted(v["ans"], key=lambda x: x["id"])
                     if a["gold"] in ctx
                     and re.search(r"[a-z0-9]", a["gold"].lower())), None)
        if cand is None:
            continue
        rows.append(dict(
            family_id=f"squadv2_ctx_{k}", source_id=cand["id"], source_split="train",
            generator_id="A", generator_version=GEN_VER, component="clean_replay",
            domain="general_if", subtype="plain_squad_qa",
            prompt=PLAIN_QA_PROMPT.format(ctx=ctx, q=cand["q"]), target=cand["gold"],
            meta={"title": v["title"], "context_hash": k, "carrier": "squad_v2"}))
    assert len(rows) == N_SQUAD, len(rows)
    return rows


def build_agnews(ag_rows, exclude_ag):
    pool = [r for r in ag_rows if r["text_hash"] not in exclude_ag]
    random.Random(SEED + 2).shuffle(pool)
    per_label = N_AG // len(L.AG_LABELS)
    rows, cnt = [], Counter()
    for r in pool:
        if cnt[r["label_name"]] >= per_label:
            continue
        rows.append(dict(
            family_id=f"agnews_train_{r['idx']}", source_id=f"agnews_train_{r['idx']}",
            source_split="train", generator_id="A", generator_version=GEN_VER,
            component="clean_replay", domain="general_if", subtype="plain_agnews_cls",
            prompt=PLAIN_CLS_PROMPT.format(text=r["text"]),
            target=PLAIN_CLS_TGT.format(desc=AG_DESC[r["label_name"]]),
            meta={"agnews_text_hash": r["text_hash"], "label": r["label_name"],
                  "carrier": "ag_news"}))
        cnt[r["label_name"]] += 1
        if len(rows) >= N_AG:
            break
    assert len(rows) == N_AG, len(rows)
    return rows


def verify(rows, by_ctx, ns_txt, other_sq, other_ag, other_crepe):
    errs = []
    if len(rows) != N_CREPE + N_SQUAD + N_AG:
        errs.append(("bad_n", len(rows)))
    sc = Counter(r["subtype"] for r in rows)
    if dict(sc) != {"plain_eli5_qa": N_CREPE, "plain_squad_qa": N_SQUAD,
                    "plain_agnews_cls": N_AG}:
        errs.append(("bad_source_mix", dict(sc)))
    fams = [r["family_id"] for r in rows]
    if len(set(fams)) != len(fams):
        errs.append(("dup_family",))
    if len({r["prompt"] for r in rows}) != len(rows):
        errs.append(("dup_prompt",))
    for r in rows:
        for k in ("family_id", "component", "subtype", "prompt", "target",
                  "source_id", "source_split", "generator_id", "domain"):
            if not r.get(k):
                errs.append(("missing_field", k, r.get("family_id")))
        if L.norm(r["prompt"]) in ns_txt:
            errs.append(("naturalset_leak", r["family_id"]))
        # replay must carry no component surface / schema instruction
        for m in COMPONENT_MARKERS:
            if m in r["prompt"] or m in r["target"]:
                errs.append(("component_marker_in_replay", m, r["family_id"]))
        if r["subtype"] == "plain_squad_qa":
            ctx = L.norm(by_ctx[r["meta"]["context_hash"]]["ctx"])
            if r["target"] not in ctx:
                errs.append(("gold_span_not_in_context", r["family_id"]))
            if not re.search(r"[a-z0-9]", r["target"].lower()):
                errs.append(("gold_span_not_scorable", r["family_id"]))
        if r["subtype"] == "plain_agnews_cls":
            if r["target"] != PLAIN_CLS_TGT.format(desc=AG_DESC[r["meta"]["label"]]):
                errs.append(("bad_plain_label_target", r["family_id"]))
    own_sq = {r["meta"]["context_hash"] for r in rows if "context_hash" in r["meta"]}
    own_ag = {r["meta"]["agnews_text_hash"] for r in rows if "agnews_text_hash" in r["meta"]}
    own_cr = {r["source_id"] for r in rows if r["subtype"] == "plain_eli5_qa"}
    if own_sq & other_sq:
        errs.append(("cross_pool_squad_collision", len(own_sq & other_sq)))
    if own_ag & other_ag:
        errs.append(("cross_pool_agnews_collision", len(own_ag & other_ag)))
    if own_cr & other_crepe:
        errs.append(("cross_pool_crepe_collision", len(own_cr & other_crepe)))
    return errs, own_sq, own_ag, own_cr


def main():
    squad_rows, parquet_path = L.load_squad()
    ns_txt, _ = L.load_ns()
    by_ctx, _ = L.index_squad(squad_rows)
    ag_rows, ag_parquet = L.load_agnews()

    other_sq, other_ag, other_cr = L.other_pool_registries("if_clean_replay_pool")
    v2_all_ctx, _ = L.v2_proto_registry()
    rev_crepe = L.revision_proto_crepe_ids()   # fp-only families; label-disjoint anyway
    exclude_ctx = other_sq | v2_all_ctx
    exclude_crepe = other_cr | rev_crepe

    crepe = build_crepe(exclude_crepe, ns_txt)
    squad = build_squad(by_ctx, exclude_ctx)
    ag = build_agnews(ag_rows, other_ag)
    rows = crepe + squad + ag

    errs, own_sq, own_ag, own_cr = verify(rows, by_ctx, ns_txt,
                                          other_sq, other_ag, other_cr | rev_crepe)
    assert not errs, errs[:20]

    dup_rate = L.family_dup_rate(rows, L.make_content_grams(SKELETON))
    manifest = {
        "pool": "if_clean_replay_pool", "status": "FORMAL (route R-A, C-30 #2 approved)",
        "seed": SEED, "generator_version": GEN_VER, "instruction": "C-31 line 4",
        "source": {
            "crepe": {"dataset": "tasksource/CREPE", "split": "train (pure normal rows)",
                      "license": "research release (no explicit LICENSE in mirror — "
                                 "flagged risk, recheck on freeze)"},
            "squad": {"dataset": "rajpurkar/squad_v2", "split": "train",
                      "parquet": Path(parquet_path).name, "license": "CC BY-SA 4.0"},
            "agnews": {"dataset": "fancyzhx/ag_news", "split": "train",
                       "parquet": ag_parquet, "license": "research use (verify on freeze)"}},
        "composition": {"crepe_normal": N_CREPE, "squad_plain": N_SQUAD,
                        "agnews_plain": N_AG,
                        "note": "plain natural-language targets, no schema; CREPE "
                                "comments clipped <=600 chars at sentence boundary"},
        "verify_errors": [], "nonskeleton_8gram_dup_rate_family": dup_rate,
        "isolation_note": (
            "Zero family/context intersection with if_answerability_pool, "
            "if_evidence_v2.1_proto, if_format_pool (hard-asserted against their "
            "manifests) and with all v2/v0.1 proto contexts (evidence donors and "
            "revision-proto CREPE families included). CREPE-normal rows are "
            "label-disjoint from the fp-only revision proto and split-disjoint "
            "from naturalset CREPE-test."),
        "registry": {
            "context_hashes": sorted(own_sq),
            "squad_question_ids": sorted({r["source_id"] for r in rows
                                          if r["subtype"] == "plain_squad_qa"}),
            "agnews_text_hashes": sorted(own_ag),
            "crepe_ids": sorted(own_cr),
        },
    }
    L.write_pool("if_clean_replay_pool", rows, manifest)
    L.write_sample("if_clean_replay_pool", rows, 4, 12)

    print(json.dumps({k: manifest[k] for k in
                      ("n", "sha256_16", "by_subtype", "n_families",
                       "target_length_buckets", "nonskeleton_8gram_dup_rate_family")},
                     indent=2))
    print("verify_errors: []")


if __name__ == "__main__":
    main()
