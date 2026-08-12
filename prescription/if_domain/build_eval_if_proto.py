#!/usr/bin/env python3
"""IF formal-eval PROTOTYPE builder — C-30 #9 multi-task-form coverage (2026-08-12).

Output: eval_if_proto.jsonl (n=950), generator_id=B (ALL prompt wording is
generator-B, disjoint from the training generator-A templates — asserted two
ways below). Six task forms, 50 families each; per form only the SEMANTICALLY
applicable conditions are built (C-30 #9; no mechanical full cross product):

  form            source (split)         conditions (rows/family)
  --------------- ---------------------- ------------------------------------------
  extraction      SQuAD v2 DEV           original(1) format_contract:B2(1)
                                         candidate_keep/revise(2) insufficient(1)
                                         status_found/insufficient(2)   -> 7 = 350
  classification  AG-News TEST           original(1) format_contract:B4(1)
                                         candidate_keep/revise(2)       -> 4 = 200
  reading_qa      CREPE TEST (normal)    original(1)                    -> 50
                  + SQuAD v2 DEV unans   insufficient(1)                -> 50
                                         (C-30/#9 spec: the insufficient condition
                                          of extraction/readingQA comes from SQuAD
                                          v2 dev unanswerable; hence the readingQA
                                          insufficient families are SQuAD-dev)
  revision        CREPE TEST (fp)        candidate_keep/revise(2)       -> 100
                                         (the form IS the candidate contract:
                                          draft correct -> KEEP, draft repeats the
                                          false presupposition -> REVISE)
  constraint      SQuAD v2 DEV           word_limit(1) answer_prefix(1)
                                         uppercase(1)                   -> 3 = 150
  structured_resp SQuAD v2 DEV (25, B1)  format_contract(1)             -> 50
                  + AG-News TEST (25, B3)

Condition applicability rationale (per form semantics):
  * classification has no ground-truth-insufficient side -> no insufficient /
    STATUS pair; * reading_qa answers are free-form (not program-verifiable
    content) -> no format/STATUS/candidate contract (candidate-on-CREPE is the
    revision form); * revision is itself the candidate condition; * constraint
    variants are the form's own conditions; * structured_response is itself the
    format-contract condition (schema set B).

Schema set B (train/eval separation, C-30 #1 spirit): B1 {"final_answer"} /
B2 {"final_answer","support_quote"} / B3 {"category"} / B4 `category = <label>`
— keys AND instruction wording disjoint from train set A (A1/A2/A3/A4).
Within-form condition contrasts share ONE B template (candidate keep/revise
sides literally identical wording; original vs insufficient identical wording)
so no condition is cued by phrasing (asserted).

Isolation (hard-asserted):
  * SQuAD: dev split only; dev context hashes have ZERO intersection with every
    training-pool/proto registry (answerability, evidence v2.1 + formal pool,
    format, replay, both v2 protos incl. donors);
  * AG-News: test split; text-hash intersection with the train-side registries
    (format/replay pools) is ZERO;
  * CREPE: test split; id intersection with replay-pool train ids and the
    revision-proto train families is ZERO;
  * naturalset calibration set: eval source_ids (incl. CREPE test ids — the
    naturalset CREPE rows ARE test-split rows) and normalized prompt texts are
    disjoint;
  * within-eval: each SQuAD dev context / AG-News article / CREPE id belongs to
    exactly one form (no family reuse across forms).

Generator A/B separation (asserted): (i) no >=4-word literal chunk of ANY
training generator-A prompt template appears in ANY eval prompt; (ii) the A and
B template texts share zero word-level 6-grams; (iii) the training "Note:" /
"Unverified note" surfaces do not appear in any eval prompt.

Scoring: behavior-level via if_scorer.py (extended in-place for schema B,
candidate_contract, reading_qa, constraint, classification, gold aliases —
selftest 60/60). All 950 reference targets self-score correct (in-build assert).

Deterministic: SEED=20260822.
"""
import glob
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

import if_build_lib as L
import build_if_v2 as v2
import build_if_evidence_v2_1 as V21
import build_if_format_pool as FMT
import build_if_clean_replay_pool as RPL
import build_if_proto as PROTO
import if_scorer

OUT = L.OUT
SEED = 20260822
GEN_VER = "ifeval-v0.1"

N_FAM = 50
SQUAD_DEV_GLOB = str(Path.home() / ".cache/huggingface/hub/datasets--rajpurkar--squad_v2/snapshots/*/squad_v2/validation-*.parquet")
AGNEWS_TEST_GLOB = str(Path.home() / ".cache/huggingface/hub/datasets--fancyzhx--ag_news/snapshots/*/data/test-*.parquet")

# ------------------------------------------------------------ generator-B templates
EXT_B_PROMPT = ("Context:\n{ctx}\n\nQ: {q}\n\nWork strictly from the context above. "
                "Reply with the shortest snippet of the context that settles the "
                "question; if the context leaves it unsettled, state plainly that "
                "it cannot be settled from the context.")
REFUSE_B_TGT = ("The context does not contain what this question asks for, so it "
                "cannot be settled from the context.")

STAT_B_PROMPT = ("Context:\n{ctx}\n\nYou are auditing one entry of a records table. "
                 "Entry \"{field}\" is defined by the question: {q}\n\n"
                 "Report back in exactly two lines — first line 'STATUS: OK' when "
                 "the context supplies the value, otherwise 'STATUS: INSUFFICIENT'; "
                 "second line 'FINAL_ANSWER: <the value>', writing NULL when it is "
                 "missing.")
STAT_OK_TGT = "STATUS: OK\nFINAL_ANSWER: {span}"
STAT_NULL_TGT = "STATUS: INSUFFICIENT\nFINAL_ANSWER: NULL"

CAND_EXT_B = ("Context:\n{ctx}\n\nQ: {q}\n\nDrafted reply: \"{cand}\"\n\n"
              "Audit the drafted reply against the context. Give exactly two lines:\n"
              "DECISION: KEEP if the draft is right, REVISE if not\n"
              "FINAL: the answer you stand behind")
CAND_CLS_B = ("News brief:\n\n{text}\n\nDrafted desk assignment: {cand}\n\n"
              "Audit the draft. Give exactly two lines:\n"
              "DECISION: KEEP if the draft is right, REVISE if not\n"
              "FINAL: the desk you stand behind (World, Sports, Business, or Sci/Tech)")
CAND_REV_B = ("Reference material:\n{passages}\n\nQuestion: {q}\n\n"
              "Drafted response:\n{cand}\n\n"
              "Audit the drafted response against the material and the question. "
              "Give exactly two lines:\n"
              "DECISION: KEEP if the draft is sound, REVISE if it gets something wrong\n"
              "FINAL: the response you would send")
CAND_KEEP_TGT = "DECISION: KEEP\nFINAL: {final}"
CAND_REVISE_TGT = "DECISION: REVISE\nFINAL: {final}"

CLS_B_PROMPT = ("Here is a news brief:\n\n{text}\n\nWhich desk should this run "
                "under — World, Sports, Business, or Sci/Tech? Answer in one "
                "short sentence.")
CLS_B_TGT = "This one goes under the {label} desk."

READ_B_PROMPT = ("Reference material:\n{passages}\n\nUsing the material above, "
                 "write a brief explanation answering: {q}\nIf the material does "
                 "not cover what is asked, note that instead of speculating.")
READ_REFUSE_B_TGT = ("No part of the material covers this question, so it cannot "
                     "be answered from what is given.")

FMT_EXT_B = "Context:\n{ctx}\n\nQ: {q}\n\n{schema}"
FMT_CLS_B = ("Here is a news brief:\n\n{text}\n\nWhich desk should this run "
             "under — World, Sports, Business, or Sci/Tech?\n\n{schema}")
SCHEMA_B1 = ('Reply with a single JSON object shaped exactly like:\n'
             '{"final_answer": "<snippet copied from the context>"}\n'
             'Nothing before or after the object.')
SCHEMA_B2 = ('Reply with a single JSON object shaped exactly like:\n'
             '{"final_answer": "<snippet copied from the context>", '
             '"support_quote": "<the context sentence that backs it>"}\n'
             'Nothing before or after the object.')
SCHEMA_B3 = ('Reply with a single JSON object shaped exactly like:\n'
             '{"category": "<World, Sports, Business, or Sci/Tech>"}\n'
             'Nothing before or after the object.')
SCHEMA_B4 = ('Reply with a single line of the exact shape:\n'
             'category = <World, Sports, Business, or Sci/Tech>\n'
             'Nothing before or after that line.')

CON_B_PROMPT = "Context:\n{ctx}\n\nQ: {q}\n\n{constraint}"
CON_WORDS = "Reply in {n} words or fewer, giving just the answer."
CON_PREFIX = ("Your whole reply must be a single line that starts with 'ANSWER: ' "
              "followed by the answer, and nothing else.")
CON_UPPER = "Reply with just the answer, written entirely in capital letters."

B_TEMPLATES = [EXT_B_PROMPT, STAT_B_PROMPT, CAND_EXT_B, CAND_CLS_B, CAND_REV_B,
               CLS_B_PROMPT, READ_B_PROMPT, FMT_EXT_B, FMT_CLS_B, SCHEMA_B1,
               SCHEMA_B2, SCHEMA_B3, SCHEMA_B4, CON_B_PROMPT, CON_WORDS,
               CON_PREFIX, CON_UPPER]
# training generator-A prompt templates (every trained/proto line)
A_TEMPLATES = [v2.CORE_PROMPT, v2.STRUCT_PROMPT, v2.EV1_PROMPT, v2.EV2_PROMPT,
               v2.EV3_PROMPT, V21.NOTE_PROMPT, FMT.EXT_PROMPT, FMT.CLS_PROMPT,
               FMT.SCHEMA_A1, FMT.SCHEMA_A2, FMT.SCHEMA_A3, FMT.SCHEMA_A4,
               RPL.PLAIN_QA_PROMPT, RPL.PLAIN_CLS_PROMPT, PROTO.REV_PROMPT]


# ------------------------------------------------------------ loaders
def load_squad_dev():
    import pyarrow.parquet as pq
    paths = sorted(glob.glob(SQUAD_DEV_GLOB))
    assert paths, f"SQuAD v2 dev parquet not found: {SQUAD_DEV_GLOB}"
    rows = pq.read_table(paths[-1]).to_pylist()
    by_ctx, by_title = v2.index_squad(rows)
    aliases = {}
    for r in rows:
        if r["answers"]["text"]:
            al, seen = [], set()
            for t in r["answers"]["text"]:
                c = v2.clean_span(t)
                if c and c.lower() not in seen:
                    al.append(c)
                    seen.add(c.lower())
            aliases[r["id"]] = al
    return by_ctx, by_title, aliases, Path(paths[-1]).name


def load_agnews_test(min_len=120, max_len=1000):
    import pyarrow.parquet as pq
    paths = sorted(glob.glob(AGNEWS_TEST_GLOB))
    assert paths, f"AG-News test parquet not found: {AGNEWS_TEST_GLOB}"
    raw = pq.read_table(paths[-1]).to_pylist()
    seen, rows = set(), []
    for i, r in enumerate(raw):
        text = L.clean_agnews_text(r["text"])
        if not (min_len <= len(text) <= max_len) or not L.PRINTABLE.match(text):
            continue
        h = L.agnews_hash(text)
        if h in seen:
            continue
        seen.add(h)
        rows.append({"idx": i, "text": text, "label": int(r["label"]),
                     "label_name": L.AG_LABELS[int(r["label"])], "text_hash": h})
    return rows, Path(paths[-1]).name


def load_crepe_test():
    snap = sorted(glob.glob(L.CREPE_SNAP_GLOB))[-1]
    rows = [json.loads(l) for l in open(Path(snap) / "test.jsonl")]
    normal = [r for r in rows if set(r["labels"] or []) == {"normal"}]
    fp = [r for r in rows if set(r["labels"] or []) == {"false presupposition"}]
    return normal, fp


def crepe_passages(r):
    ps = PROTO.pick_passages(r)
    if len(ps) < 2:
        return None
    return "\n".join(f"[{i+1}] {PROTO.clip(p, 700)}" for i, p in enumerate(ps))


# ------------------------------------------------------------ common row factory
def mk(form, condition, family_id, source_id, split, component, subtype,
       prompt, target, meta, schema_id=None):
    r = dict(family_id=family_id, source_id=source_id, source_split=split,
             generator_id="B", generator_version=GEN_VER, domain="general_if",
             task_form=form, condition=condition, component=component,
             subtype=subtype, prompt=prompt, target=target, meta=meta)
    if schema_id:
        r["schema_id"] = schema_id
    return r


# ------------------------------------------------------------ SQuAD-dev form builders
def pick_dev_candidate(v, ctx, aliases, need_alpha=False):
    """First answerable question usable across all extraction-side conditions."""
    for a in sorted(v["ans"], key=lambda x: x["id"]):
        if a["gold"] not in ctx or len(a["gold"].split()) > v2.EVD_GOLD_MAX_TOKENS:
            continue
        if need_alpha and not re.search(r"[a-zA-Z]", a["gold"]):
            continue
        if not re.search(r"[a-zA-Z0-9]", a["gold"]):
            continue
        if not v2.evidence_sentence(v["ctx"], a["start"], a["gold"]):
            continue
        if a["id"] not in aliases:
            continue
        return a
    return None


def build_extraction(by_ctx, keys, aliases, used, skip):
    fams = []
    for k in keys:
        if len(fams) >= N_FAM:
            break
        if k in used:
            continue
        v = by_ctx[k]
        if not (v["ans"] and v["una"] and v2.CTX_MIN <= len(v["ctx"]) <= v2.CTX_MAX):
            skip["extraction_ctx_ineligible"] += 1
            continue
        ctx = L.norm(v["ctx"])
        a = pick_dev_candidate(v, ctx, aliases)
        if a is None:
            skip["extraction_no_candidate"] += 1
            continue
        al = aliases[a["id"]]
        wrong = v2.pick_wrong(a, v["ans"], ctx)
        if (not wrong or wrong.lower() in a["q"].lower()
                or any(wrong.lower() in g.lower() or g.lower() in wrong.lower()
                       for g in al)):
            skip["extraction_no_wrong_candidate"] += 1
            continue
        u = min(v["una"], key=lambda x: x["id"])
        f_ok, f_null = v2.field_name(a["q"]), v2.field_name(u["q"])
        if not f_ok or not f_null or f_ok == f_null:
            skip["extraction_bad_field_names"] += 1
            continue
        ev = v2.evidence_sentence(v["ctx"], a["start"], a["gold"])
        fams.append((k, v, ctx, a, al, wrong, u, f_ok, f_null, ev))
        used.add(k)
    assert len(fams) == N_FAM, len(fams)

    rows = []
    for k, v, ctx, a, al, wrong, u, f_ok, f_null, ev in fams:
        fid = f"squadv2dev_ctx_{k}"
        base_meta = {"title": v["title"], "context_hash": k}
        m_ans = dict(base_meta, question=a["q"], gold=a["gold"], gold_aliases=al)
        rows.append(mk("extraction", "original", fid, a["id"], "dev",
                       "answerability", "answerable",
                       EXT_B_PROMPT.format(ctx=ctx, q=a["q"]), a["gold"], dict(m_ans)))
        rows.append(mk("extraction", "insufficient", fid, u["id"], "dev",
                       "answerability", "unanswerable",
                       EXT_B_PROMPT.format(ctx=ctx, q=u["q"]), REFUSE_B_TGT,
                       dict(base_meta, question=u["q"])))
        rows.append(mk("extraction", "format_contract", fid, a["id"], "dev",
                       "format", "extract_B2",
                       FMT_EXT_B.format(ctx=ctx, q=a["q"], schema=SCHEMA_B2),
                       json.dumps({"final_answer": a["gold"], "support_quote": ev},
                                  ensure_ascii=False),
                       dict(m_ans, evidence_sentence=ev), schema_id="B2"))
        for cond, cand, exp in (("candidate_keep", a["gold"], "KEEP"),
                                ("candidate_revise", wrong, "REVISE")):
            rows.append(mk("extraction", cond, fid, a["id"], "dev",
                           "candidate_contract", cond,
                           CAND_EXT_B.format(ctx=ctx, q=a["q"], cand=cand),
                           (CAND_KEEP_TGT if exp == "KEEP" else CAND_REVISE_TGT)
                           .format(final=a["gold"]),
                           dict(m_ans, candidate=cand, expected_decision=exp,
                                final_kind="gold")))
        rows.append(mk("extraction", "status_found", fid, a["id"], "dev",
                       "answerability", "struct_found",
                       STAT_B_PROMPT.format(ctx=ctx, field=f_ok, q=a["q"]),
                       STAT_OK_TGT.format(span=a["gold"]), dict(m_ans, field=f_ok)))
        rows.append(mk("extraction", "status_insufficient", fid, u["id"], "dev",
                       "answerability", "struct_insufficient",
                       STAT_B_PROMPT.format(ctx=ctx, field=f_null, q=u["q"]),
                       STAT_NULL_TGT,
                       dict(base_meta, question=u["q"], field=f_null,
                            subtype="missing_field")))
    return rows


def build_readingqa_insufficient(by_ctx, keys, used, skip):
    rows = []
    for k in keys:
        if len(rows) >= N_FAM:
            break
        if k in used:
            continue
        v = by_ctx[k]
        if not (v["una"] and v2.CTX_MIN <= len(v["ctx"]) <= v2.CTX_MAX):
            skip["readingqa_ctx_ineligible"] += 1
            continue
        ctx = L.norm(v["ctx"])
        u = min(v["una"], key=lambda x: x["id"])
        rows.append(mk("reading_qa", "insufficient", f"squadv2dev_ctx_{k}",
                       u["id"], "dev", "reading_qa", "rq_insufficient",
                       READ_B_PROMPT.format(passages=f"[1] {ctx}", q=u["q"]),
                       READ_REFUSE_B_TGT,
                       {"title": v["title"], "context_hash": k, "question": u["q"]}))
        used.add(k)
    assert len(rows) == N_FAM, len(rows)
    return rows


def build_constraint(by_ctx, keys, aliases, used, skip):
    rows = []
    n_fam = 0
    for k in keys:
        if n_fam >= N_FAM:
            break
        if k in used:
            continue
        v = by_ctx[k]
        if not (v["ans"] and v2.CTX_MIN <= len(v["ctx"]) <= v2.CTX_MAX):
            skip["constraint_ctx_ineligible"] += 1
            continue
        ctx = L.norm(v["ctx"])
        a = pick_dev_candidate(v, ctx, aliases, need_alpha=True)
        if a is None:
            skip["constraint_no_candidate"] += 1
            continue
        al = aliases[a["id"]]
        fid = f"squadv2dev_ctx_{k}"
        meta = {"title": v["title"], "context_hash": k, "question": a["q"],
                "gold": a["gold"], "gold_aliases": al}
        n_words = max(3, len(a["gold"].split()) + 2)
        rows.append(mk("constraint", "word_limit", fid, a["id"], "dev",
                       "constraint", "word_limit",
                       CON_B_PROMPT.format(ctx=ctx, q=a["q"],
                                           constraint=CON_WORDS.format(n=n_words)),
                       a["gold"], dict(meta, word_limit=n_words)))
        rows.append(mk("constraint", "answer_prefix", fid, a["id"], "dev",
                       "constraint", "answer_prefix",
                       CON_B_PROMPT.format(ctx=ctx, q=a["q"], constraint=CON_PREFIX),
                       f"ANSWER: {a['gold']}", dict(meta)))
        rows.append(mk("constraint", "uppercase", fid, a["id"], "dev",
                       "constraint", "uppercase",
                       CON_B_PROMPT.format(ctx=ctx, q=a["q"], constraint=CON_UPPER),
                       a["gold"].upper(), dict(meta)))
        used.add(k)
        n_fam += 1
    assert n_fam == N_FAM
    return rows


def build_structured_squad(by_ctx, keys, aliases, used, skip, n=25):
    rows = []
    for k in keys:
        if len(rows) >= n:
            break
        if k in used:
            continue
        v = by_ctx[k]
        if not (v["ans"] and v2.CTX_MIN <= len(v["ctx"]) <= v2.CTX_MAX):
            skip["structured_ctx_ineligible"] += 1
            continue
        ctx = L.norm(v["ctx"])
        a = pick_dev_candidate(v, ctx, aliases)
        if a is None:
            skip["structured_no_candidate"] += 1
            continue
        rows.append(mk("structured_response", "format_contract",
                       f"squadv2dev_ctx_{k}", a["id"], "dev", "format", "extract_B1",
                       FMT_EXT_B.format(ctx=ctx, q=a["q"], schema=SCHEMA_B1),
                       json.dumps({"final_answer": a["gold"]}, ensure_ascii=False),
                       {"title": v["title"], "context_hash": k, "question": a["q"],
                        "gold": a["gold"], "gold_aliases": aliases[a["id"]]},
                       schema_id="B1"))
        used.add(k)
    assert len(rows) == n, len(rows)
    return rows


# ------------------------------------------------------------ AG-News form builders
def take_agnews(pool, quota_by_label, used):
    picked = []
    want = dict(quota_by_label)
    for r in pool:
        if not any(want.values()):
            break
        if r["text_hash"] in used or want[r["label_name"]] <= 0:
            continue
        picked.append(r)
        want[r["label_name"]] -= 1
        used.add(r["text_hash"])
    assert not any(want.values()), want
    return picked


def build_classification(pool, used, rng):
    quota = dict(zip(L.AG_LABELS, [13, 13, 12, 12]))
    picked = take_agnews(pool, quota, used)
    rows = []
    for r in picked:
        fid = f"agnews_test_{r['idx']}"
        sid = fid
        label = r["label_name"]
        meta = {"agnews_text_hash": r["text_hash"], "label": label}
        rows.append(mk("classification", "original", fid, sid, "test",
                       "classification", "cls_plain",
                       CLS_B_PROMPT.format(text=r["text"]),
                       CLS_B_TGT.format(label=label), dict(meta)))
        rows.append(mk("classification", "format_contract", fid, sid, "test",
                       "format", "classify_B4",
                       FMT_CLS_B.format(text=r["text"], schema=SCHEMA_B4),
                       f"category = {label}", dict(meta), schema_id="B4"))
        wrong = rng.choice([x for x in L.AG_LABELS if x != label])
        for cond, cand, exp in (("candidate_keep", label, "KEEP"),
                                ("candidate_revise", wrong, "REVISE")):
            rows.append(mk("classification", cond, fid, sid, "test",
                           "candidate_contract", cond,
                           CAND_CLS_B.format(text=r["text"], cand=cand),
                           (CAND_KEEP_TGT if exp == "KEEP" else CAND_REVISE_TGT)
                           .format(final=label),
                           dict(meta, candidate=cand, expected_decision=exp,
                                final_kind="label")))
    return rows


def build_structured_agnews(pool, used, n=25):
    quota = dict(zip(L.AG_LABELS, [7, 6, 6, 6]))
    picked = take_agnews(pool, quota, used)
    rows = []
    for r in picked:
        fid = f"agnews_test_{r['idx']}"
        rows.append(mk("structured_response", "format_contract", fid, fid, "test",
                       "format", "classify_B3",
                       FMT_CLS_B.format(text=r["text"], schema=SCHEMA_B3),
                       json.dumps({"category": r["label_name"]}, ensure_ascii=False),
                       {"agnews_text_hash": r["text_hash"], "label": r["label_name"]},
                       schema_id="B3"))
    assert len(rows) == n
    return rows


# ------------------------------------------------------------ CREPE form builders
def build_readingqa_original(normal_rows, ns_ids, ns_txt, skip):
    rows = []
    for r in normal_rows:
        if len(rows) >= N_FAM:
            break
        if r["id"] in ns_ids:
            skip["readingqa_naturalset_id"] += 1
            continue
        q = L.norm(r["question"])
        if not (20 <= len(q) <= 300) or not L.PRINTABLE.match(q) or q in ns_txt:
            skip["readingqa_bad_question"] += 1
            continue
        if RPL.URLISH.search(q):
            skip["readingqa_url"] += 1
            continue
        c = RPL.clip_comment(r["comment"])
        if c is None or len(c) < 80 or RPL.URLISH.search(c):
            skip["readingqa_bad_comment"] += 1
            continue
        if if_scorer.has_refusal(c) or len(c.split()) < 10:
            skip["readingqa_reference_not_attempt_like"] += 1
            continue
        passages = crepe_passages(r)
        if passages is None:
            skip["readingqa_lt2_passages"] += 1
            continue
        rows.append(mk("reading_qa", "original", f"crepe_test_{r['id']}", r["id"],
                       "test", "reading_qa", "rq_answerable",
                       READ_B_PROMPT.format(passages=passages, q=q), c,
                       {"crepe_id": r["id"], "question": q}))
    assert len(rows) == N_FAM, len(rows)
    return rows


def build_revision(fp_rows, ns_ids, ns_txt, skip):
    rows = []
    n_fam = 0
    for r in fp_rows:
        if n_fam >= N_FAM:
            break
        if r["id"] in ns_ids:
            skip["revision_naturalset_id"] += 1
            continue
        q = L.norm(r["question"])
        pres = L.norm((r["presuppositions"] or [""])[0])
        corr = L.norm((r["corrections"] or [""])[0])
        if not pres or not corr or len(corr) < 20 or len(corr.split()) < 4:
            skip["revision_bad_pres_or_corr"] += 1
            continue
        if not (20 <= len(q) <= 300) or not L.PRINTABLE.match(q) or q in ns_txt:
            skip["revision_bad_question"] += 1
            continue
        if RPL.URLISH.search(q) or RPL.URLISH.search(corr) or RPL.URLISH.search(pres):
            skip["revision_url"] += 1
            continue
        if L.norm(corr).lower() in L.norm(pres).lower():
            skip["revision_corr_inside_pres"] += 1
            continue
        passages = crepe_passages(r)
        if passages is None:
            skip["revision_lt2_passages"] += 1
            continue
        fid = f"crepe_test_{r['id']}"
        corr_s, pres_s = PROTO.sent(corr), PROTO.sent(pres)
        meta = {"crepe_id": r["id"], "question": q, "presupposition": pres,
                "correction": corr}
        for cond, cand, exp in (("candidate_keep", corr_s, "KEEP"),
                                ("candidate_revise", pres_s, "REVISE")):
            rows.append(mk("revision", cond, fid, r["id"], "test",
                           "candidate_contract", cond,
                           CAND_REV_B.format(passages=passages, q=q, cand=cand),
                           (CAND_KEEP_TGT if exp == "KEEP" else CAND_REVISE_TGT)
                           .format(final=corr),
                           dict(meta, candidate=cand, expected_decision=exp,
                                final_kind="free")))
        n_fam += 1
    assert n_fam == N_FAM, n_fam
    return rows


# ------------------------------------------------------------ A/B wording separation
def template_chunks(tpl, min_words=4):
    out = []
    for chunk in re.split(r"\{[a-z0-9_]+\}", tpl):
        c = L.norm(chunk).strip(" :—-\"'")
        if len(c.split()) >= min_words:
            out.append(c)
    return out


def word_grams(texts, n=6):
    toks = []
    for t in texts:
        toks += re.findall(r"[a-z0-9'_]+", re.sub(r"\{[a-z0-9_]+\}", " ", t.lower()))
        toks.append("\x00")
    out = set()
    for i in range(len(toks) - n + 1):
        window = toks[i:i + n]
        if "\x00" not in window:
            out.add(" ".join(window))
    return out


# ------------------------------------------------------------ verification
EXPECT = {
    ("extraction", "original"): 50, ("extraction", "insufficient"): 50,
    ("extraction", "format_contract"): 50, ("extraction", "candidate_keep"): 50,
    ("extraction", "candidate_revise"): 50, ("extraction", "status_found"): 50,
    ("extraction", "status_insufficient"): 50,
    ("classification", "original"): 50, ("classification", "format_contract"): 50,
    ("classification", "candidate_keep"): 50, ("classification", "candidate_revise"): 50,
    ("reading_qa", "original"): 50, ("reading_qa", "insufficient"): 50,
    ("revision", "candidate_keep"): 50, ("revision", "candidate_revise"): 50,
    ("constraint", "word_limit"): 50, ("constraint", "answer_prefix"): 50,
    ("constraint", "uppercase"): 50,
    ("structured_response", "format_contract"): 50,
}


def verify(rows, ns_txt, ns_ids, reg_sq, reg_ag, reg_cr):
    errs = []
    mat = Counter((r["task_form"], r["condition"]) for r in rows)
    if dict(mat) != EXPECT:
        errs.append(("bad_matrix", {f"{a}/{b}": n for (a, b), n in mat.items()}))
    if len(rows) != sum(EXPECT.values()):
        errs.append(("bad_n", len(rows)))
    if len({r["prompt"] for r in rows}) != len(rows):
        errs.append(("dup_prompt",))
    keyset = {(r["family_id"], r["source_id"], r["subtype"]) for r in rows}
    if len(keyset) != len(rows):
        errs.append(("dup_batch_key",))
    # required fields + generator identity
    for r in rows:
        for k in ("family_id", "source_id", "source_split", "generator_id",
                  "task_form", "condition", "component", "subtype", "prompt",
                  "target", "domain"):
            if not r.get(k):
                errs.append(("missing_field", k, r.get("family_id")))
        if r["generator_id"] != "B":
            errs.append(("not_generator_B", r["family_id"]))
        if r["source_split"] not in ("dev", "test"):
            errs.append(("train_split_leak", r["family_id"]))
    # family exclusivity across forms
    fam_form = defaultdict(set)
    for r in rows:
        fam_form[r["family_id"]].add(r["task_form"])
    for fid, forms in fam_form.items():
        if len(forms) > 1:
            errs.append(("family_shared_across_forms", fid, sorted(forms)))
    # per-family condition completeness
    fam_conds = defaultdict(set)
    for r in rows:
        fam_conds[(r["task_form"], r["family_id"])].add(r["condition"])
    want_conds = defaultdict(set)
    for f, c in EXPECT:
        want_conds[f].add(c)
    for (form, fid), conds in fam_conds.items():
        want = want_conds[form]
        if form == "reading_qa":     # split-sourced conditions (see docstring)
            if conds not in ({"original"}, {"insufficient"}):
                errs.append(("bad_readingqa_family", fid, sorted(conds)))
        elif form == "structured_response":
            if conds != {"format_contract"}:
                errs.append(("bad_structured_family", fid, sorted(conds)))
        elif conds != want:
            errs.append(("incomplete_family", form, fid, sorted(conds)))
    # candidate pairs share one template (wording carries no decision cue)
    by_fam = defaultdict(dict)
    for r in rows:
        if r["component"] == "candidate_contract":
            by_fam[(r["task_form"], r["family_id"])][r["condition"]] = r
    for (form, fid), pair in by_fam.items():
        if set(pair) != {"candidate_keep", "candidate_revise"}:
            errs.append(("broken_candidate_pair", form, fid))
            continue
        rk, rr = pair["candidate_keep"], pair["candidate_revise"]
        slot = {"extraction": 'Drafted reply: "{c}"',
                "classification": "Drafted desk assignment: {c}",
                "revision": "Drafted response:\n{c}"}[form]
        pk = rk["prompt"].replace(slot.format(c=rk["meta"]["candidate"]), "\x00", 1)
        pr = rr["prompt"].replace(slot.format(c=rr["meta"]["candidate"]), "\x00", 1)
        if pk != pr or "\x00" not in pk or "\x00" not in pr:
            errs.append(("candidate_pair_wording_cue", form, fid))
        if rk["meta"]["candidate"] == rr["meta"]["candidate"]:
            errs.append(("candidate_sides_identical", form, fid))
    # answer-bearing rows: gold present in the context shown
    for r in rows:
        m = r["meta"]
        if "gold" in m and "context_hash" in m:
            if m["gold"] not in r["prompt"]:
                errs.append(("gold_not_in_prompt_context", r["family_id"], r["condition"]))
        if r["condition"] == "word_limit" and len(r["target"].split()) > m["word_limit"]:
            errs.append(("word_limit_reference_overflow", r["family_id"]))
    # naturalset isolation (text + source_id; covers CREPE-test calibration rows)
    for r in rows:
        if L.norm(r["prompt"]) in ns_txt or str(r["source_id"]) in ns_ids:
            errs.append(("naturalset_leak", r["family_id"], r["condition"]))
    # zero intersection with every training pool / proto registry
    own_sq = {r["meta"]["context_hash"] for r in rows if "context_hash" in r["meta"]}
    own_ag = {r["meta"]["agnews_text_hash"] for r in rows if "agnews_text_hash" in r["meta"]}
    own_cr = {r["meta"]["crepe_id"] for r in rows if "crepe_id" in r["meta"]}
    if own_sq & reg_sq:
        errs.append(("train_squad_context_collision", len(own_sq & reg_sq)))
    if own_ag & reg_ag:
        errs.append(("train_agnews_collision", len(own_ag & reg_ag)))
    if own_cr & reg_cr:
        errs.append(("train_crepe_collision", len(own_cr & reg_cr)))
    # generator A/B wording separation
    a_chunks = [c for t in A_TEMPLATES for c in template_chunks(t)]
    for r in rows:
        p = L.norm(r["prompt"])
        if "Unverified" in p or "Note:" in p:
            errs.append(("train_note_surface_in_eval", r["family_id"], r["condition"]))
        for c in a_chunks:
            if c in p:
                errs.append(("A_template_chunk_in_eval_prompt", r["family_id"], c[:40]))
    shared = word_grams(A_TEMPLATES) & word_grams(B_TEMPLATES)
    if shared:
        errs.append(("A_B_template_6gram_overlap", sorted(shared)[:5]))
    # scorer self-regression on reference targets
    bad = [(r["family_id"], r["condition"], if_scorer.score_row(r, r["target"])["why"])
           for r in rows if if_scorer.score_row(r, r["target"])["correct"] is not True]
    if bad:
        errs.append(("scorer_reference_regression_failed", len(bad), bad[:5]))
    return errs, own_sq, own_ag, own_cr


# ------------------------------------------------------------ audit samples
def write_audit(rows):
    rng = random.Random(SEED)
    by_cell = defaultdict(list)
    for r in rows:
        by_cell[(r["task_form"], r["condition"])].append(r)
    md = ["# AUDIT_SAMPLES_IF — eval_if_proto.jsonl "
          f"(seed {SEED}; 3 random rows per task_form x condition, full text)", ""]
    for (form, cond) in sorted(by_cell):
        md.append(f"## {form} / {cond}  (n={len(by_cell[(form, cond)])})")
        md.append("")
        for r in rng.sample(by_cell[(form, cond)], 3):
            tag = f"{r['component']}/{r['subtype']}" + \
                  (f" schema={r['schema_id']}" if r.get("schema_id") else "")
            md += [f"### {r['family_id']}  [{tag}]", "",
                   "**prompt**", "```", r["prompt"], "```",
                   "**reference target**", "```", r["target"], "```", ""]
    (OUT / "AUDIT_SAMPLES_IF.md").write_text("\n".join(md))


# ------------------------------------------------------------ main
def main():
    by_ctx, by_title, aliases, dev_parquet = load_squad_dev()
    ag_pool, ag_parquet = load_agnews_test()
    crepe_normal, crepe_fp = load_crepe_test()
    ns_txt, ns_ids = L.load_ns()

    # union of every training-side registry on disk
    reg_sq, reg_ag, reg_cr = L.other_pool_registries("eval_if_proto")
    v2_all_ctx, _ = L.v2_proto_registry()
    reg_sq |= v2_all_ctx
    reg_cr |= L.revision_proto_crepe_ids()

    skip = Counter()
    # SQuAD dev: one shuffled key stream, forms consume disjoint contexts
    keys = [k for k in by_ctx if k not in reg_sq]
    assert len(keys) == len(by_ctx), "dev context collides with a train registry"
    random.Random(SEED).shuffle(keys)
    used_sq = set()
    ext_rows = build_extraction(by_ctx, keys, aliases, used_sq, skip)
    rq_ins_rows = build_readingqa_insufficient(by_ctx, keys, used_sq, skip)
    con_rows = build_constraint(by_ctx, keys, aliases, used_sq, skip)
    st_sq_rows = build_structured_squad(by_ctx, keys, aliases, used_sq, skip)

    # AG-News test
    ag_ok = [r for r in ag_pool if r["text_hash"] not in reg_ag]
    skip["agnews_test_hash_in_train_registry"] = len(ag_pool) - len(ag_ok)
    rng_ag = random.Random(SEED + 1)
    rng_ag.shuffle(ag_ok)
    used_ag = set()
    cls_rows = build_classification(ag_ok, used_ag, random.Random(SEED + 2))
    st_ag_rows = build_structured_agnews(ag_ok, used_ag)

    # CREPE test
    rng_cr = random.Random(SEED + 3)
    rng_cr.shuffle(crepe_normal)
    rng_cr.shuffle(crepe_fp)
    rq_rows = build_readingqa_original(crepe_normal, ns_ids, ns_txt, skip)
    rev_rows = build_revision(crepe_fp, ns_ids, ns_txt, skip)

    order = {f: i for i, f in enumerate(
        ["extraction", "classification", "reading_qa", "revision", "constraint",
         "structured_response"])}
    rows = (ext_rows + cls_rows + rq_rows + rq_ins_rows + rev_rows + con_rows
            + st_sq_rows + st_ag_rows)
    rows.sort(key=lambda r: (order[r["task_form"]], r["family_id"], r["condition"]))

    errs, own_sq, own_ag, own_cr = verify(rows, ns_txt, ns_ids, reg_sq, reg_ag, reg_cr)
    assert not errs, errs[:20]

    matrix = {}
    for (form, cond), n in sorted(Counter(
            (r["task_form"], r["condition"]) for r in rows).items()):
        matrix.setdefault(form, {})[cond] = n
    manifest = {
        "pool": "eval_if_proto",
        "status": "EVAL PROTOTYPE (C-30 #9 multi-task-form formal IF eval; "
                  "eval-only — never train on these rows)",
        "seed": SEED, "generator_version": GEN_VER, "generator_id": "B",
        "instruction": "C-30 #9 (+ C-31 交付纪律: proto JSONL + builder + scorer)",
        "sources": {
            "squad_dev": {"dataset": "rajpurkar/squad_v2", "split": "validation (dev)",
                          "parquet": dev_parquet, "license": "CC BY-SA 4.0"},
            "agnews_test": {"dataset": "fancyzhx/ag_news", "split": "test",
                            "parquet": ag_parquet,
                            "license": "research use (verify on freeze)"},
            "crepe_test": {"dataset": "tasksource/CREPE", "split": "test",
                           "license": "research release (no explicit LICENSE in "
                                      "mirror — flagged risk, recheck on freeze)"}},
        "task_form_condition_matrix": matrix,
        "families_per_form": {
            "extraction": 50, "classification": 50,
            "reading_qa": "50 CREPE-test (original) + 50 SQuAD-dev (insufficient; "
                          "spec fixes the insufficient condition to SQuAD-v2 dev "
                          "unanswerable)",
            "revision": 50, "constraint": 50,
            "structured_response": "25 SQuAD-dev (B1) + 25 AG-News-test (B3)"},
        "condition_applicability_note": (
            "Per-form semantics, no mechanical cross product: classification has "
            "no ground-truth-insufficient side (no insufficient/STATUS); "
            "reading_qa answers are free-form (no format/STATUS; its candidate "
            "condition IS the revision form); revision is itself the candidate "
            "contract; constraint variants are the form's own conditions; "
            "structured_response is itself the format contract (schema set B)."),
        "schema_set_B": {"B1": SCHEMA_B1, "B2": SCHEMA_B2, "B3": SCHEMA_B3,
                         "B4": SCHEMA_B4,
                         "note": "keys and wording disjoint from train schema set A; "
                                 "IFEval remains a separate eval-only holdout"},
        "generator_separation": (
            "All prompts generator-B: no >=4-word literal chunk of any training "
            "generator-A prompt template occurs in any eval prompt; A and B "
            "template texts share zero word-level 6-grams; the training 'Note:' / "
            "'Unverified note' surfaces are absent (all hard-asserted)."),
        "isolation": {
            "squad": "dev split only; 0 context-hash intersection with every "
                     "training pool/proto registry (asserted)",
            "agnews": "test split; 0 text-hash intersection with train-side "
                      "registries (asserted); cross-split duplicate articles "
                      "excluded at selection",
            "crepe": "test split; 0 id intersection with replay-pool train ids "
                     "and revision-proto train families (asserted)",
            "naturalset": "0 source_id and normalized-text intersection "
                          "(CREPE-test calibration rows excluded by id)",
            "within_eval": "each SQuAD dev context / AG-News article / CREPE id "
                           "belongs to exactly one task form (asserted)"},
        "scorer": {"file": "if_scorer.py",
                   "selftest": "60/60 (extended: schema B, candidate_contract, "
                               "reading_qa, constraint, classification, gold aliases)",
                   "reference_target_regression": f"{len(rows)}/{len(rows)}"},
        "reject_accounting": dict(skip),
        "verify_errors": [],
        "registry": {
            "context_hashes": sorted(own_sq),
            "squad_question_ids": sorted({r["source_id"] for r in rows
                                          if "context_hash" in r["meta"]}),
            "agnews_text_hashes": sorted(own_ag),
            "crepe_ids": sorted(own_cr),
        },
    }
    L.write_pool("eval_if_proto", rows, manifest)
    write_audit(rows)

    print(json.dumps({k: manifest[k] for k in
                      ("n", "sha256_16", "task_form_condition_matrix",
                       "n_families")}, indent=2))
    print("reject_accounting:", dict(skip))
    print("verify_errors: []")


if __name__ == "__main__":
    main()
