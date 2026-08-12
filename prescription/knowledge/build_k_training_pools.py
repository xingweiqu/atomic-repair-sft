#!/usr/bin/env python3
"""K-domain component TRAINING pool builder (K_TRAINING_SPEC.md, frozen).

Builds the five C-26 §3 knowledge training pools from the 2Wiki **train** split
(evals live entirely on validation -> natural split isolation):

  k_clean_replay_2000   plain grounded QA, answer + citation sentence
  k_format_2000         schema set KA (4 rotations), real citation fields
  k_evidence_2000       false_fact / irrelevant_passage / confusable_passage
  k_revision_2000       1000 families x keep/fix pairs (hop-localized fix)
  k_answerability_2000  1000 families x sufficient/insufficient pairs

Generator A surface (train) is disjoint from generator B (eval, build_k500.py):
different grounded instruction, "Sources:\n(n) title — text" rendering, "Q:",
prose answer skeleton; targets never contain FINAL_ANSWER=/DECISION=/STATUS=.

Isolation (hard gates, see K_TRAINING_SPEC.md §0/§2):
  * hf_id and norm(question) disjoint from the 800 validation families already
    consumed by K-eval-500 (main 500 + donor 300, main_pool_k500.json);
  * supporting-title guard: any train family whose supporting title appears in
    ANY context title of those 800 eval families is dropped entirely;
  * five main pools pairwise family-disjoint; evidence/revision donors are a
    separately carved train-split pool, disjoint from all mains; everything is
    registered in pools/K_FAMILY_LEDGER.json;
  * quoted citation sentences: normalized sentence-level substring leak into
    any eval prompt = 0 (hard);
  * non-skeleton 8-gram collisions train-target x eval-prompt+gold are listed
    (title guard makes same-article collisions impossible; residue = generic
    phrasing, reported for advisor adjudication);
  * per-pool: n=2000 exact, no duplicate prompts, family-level non-skeleton
    8-gram dup rate <= 5%, content checks per pool (spec §1), nested bundle
    shuffle order (seed 20260820) in the manifest.

Outputs -> prescription/knowledge/pools/ (NOT committed):
  <pool>.jsonl, <pool>_manifest.json, sample10_<pool>.md,
  K_FAMILY_LEDGER.json, build_stats_kpools.json

Deterministic under SEED=20260820. Any failed gate -> nonzero exit, no pools.
"""
import json
import random
import re
import hashlib
import sys
from collections import Counter
from pathlib import Path

OUT_DIR = Path(__file__).resolve().parent
POOLS = OUT_DIR / "pools"
sys.path.insert(0, str(OUT_DIR))

import build_knowledge_eval as bke                     # noqa: E402
from build_knowledge_eval import (                     # noqa: E402
    h, rng_for, norm, contains, aliases, passage_text, answer_kind,
    expected_answer_class, pick_wrong_candidate, build_insufficient, fid_of)
from build_k500 import bridge_entities, strip_paren    # noqa: E402

SEED = 20260820
GEN_VER = "kpool-v1.0"
N_POOL = 2000
N_PAIR_FAM = 1000
N_DONOR = 1500
EVAL_POOL_FILE = OUT_DIR / "main_pool_k500.json"
EVAL_PROTO_FILE = OUT_DIR / "eval_k500_proto.jsonl"

# ------------------------- generator A surface (train-only) ------------------------
INSTR_A = ("Use only the information given in the sources below; do not draw on "
           "outside knowledge. If the sources do not provide what is needed, say "
           "so instead of guessing.")

def render_sources(passages):
    return "\n".join(f"({i+1}) {t} — {' '.join(s.strip() for s in ss)}"
                     for i, (t, ss) in enumerate(passages))

def prompt_a(passages, q, extra=""):
    body = f"{INSTR_A}\n\nSources:\n{render_sources(passages)}"
    if extra:
        body += f"\n\n{extra}"
    return f"{body}\n\nQ: {q}"

def support_citation(r):
    """(title, sentence) of the first supporting passage sentence holding gold."""
    for t in dict.fromkeys(r["sf_titles"]):
        ss = r["sents"][r["titles"].index(t)]
        if contains(passage_text(t, ss), r["answer"]):
            for s in ss:
                if contains(s, r["answer"]):
                    return t, s.strip()
            return t, " ".join(x.strip() for x in ss)
    return None, None

def answer_skeleton(r, title, sent):
    return f'Based on the source "{title}": "{sent}" The answer is {r["answer"]}.'

ABSTAIN_TARGET = ("The sources given here do not contain the information needed "
                  "to answer this question. Based only on these sources, the "
                  "answer cannot be determined.")

KA_SCHEMAS = [
    {"id": "KA1",
     "instr": ('Return your answer as a JSON object with exactly this form:\n'
               '{"answer": "<string>", "evidence_title": "<title of the source '
               'that establishes it>"}\nOutput the JSON object only.')},
    {"id": "KA2",
     "instr": ('Return your answer as a JSON object with exactly this form:\n'
               '{"entity": "<string>", "quote": "<the source sentence that '
               'establishes it>"}\nOutput the JSON object only.')},
    {"id": "KA3",
     "instr": ('Return your answer as exactly one line of the form:\n'
               'entity: <string> | source: <title of the source that '
               'establishes it>\nOutput that single line only.')},
    {"id": "KA4",
     "instr": ('Return your answer as exactly one XML tag of the form:\n'
               '<result answer="<string>" source="<title of the source that '
               'establishes it>"/>\nOutput that single tag only.')},
]

FALSE_FACT_NOTE = 'An attached note claims: the answer to this question is "{w}".'
REFUTE_FALSE = 'The attached note is wrong: the sources do not support "{w}".'
REFUTE_IRREL = 'The source about "{t}" is unrelated to this question.'
REFUTE_CONF = 'The source "{t}" mentions {e} but does not answer this question.'
CAND_LINE = 'A previous reader answered: "{c}", citing the source "{t}".'
KEEP_HEAD = "The previous answer is correct — keep it."
FIX_HEAD = "The previous answer is wrong."
HOP1 = ('It picks the wrong entity: the cited source "{t}" is not where this '
        "question's answer is established.")
HOP2 = ('The cited source "{t}" does not state that answer; the citation does '
        "not support it.")
FIX_TAIL = "The correct answer is {g}."

SKELETON_TEXTS = [
    INSTR_A, bke.INSTR_GROUNDED, bke.CONTRACT_B_K, bke.CONTRACT_STATUS_K,
    bke.ANSWER_LINE, ABSTAIN_TARGET, FALSE_FACT_NOTE, REFUTE_FALSE,
    REFUTE_IRREL, REFUTE_CONF, CAND_LINE, KEEP_HEAD, FIX_HEAD, HOP1, HOP2,
    FIX_TAIL, 'Based on the source "": "" The answer is .',
    'Based on the source "": "" The correct answer is .',
    "Is the previous answer right? If it is, keep it; if not, correct it.",
    "After reading the passages, they concluded that the answer is , citing "
    'the passage titled "".',
    "Return your answer as a JSON object with exactly this form: Output the "
    "JSON object only.",
] + [s["instr"] for s in KA_SCHEMAS] + [s["instr"] for s in bke.FMT_SCHEMAS]

BANNED_IN_TARGET = ("FINAL_ANSWER=", "DECISION=", "STATUS=")

# ------------------------- n-gram utilities ---------------------------------------
def grams8(text):
    toks = norm(text).split()
    return {" ".join(toks[i:i + 8]) for i in range(len(toks) - 7)}

def skeleton_whitelist():
    wl = set()
    for t in SKELETON_TEXTS:
        wl |= grams8(t)
        # template lines with format slots removed still need coverage
        wl |= grams8(re.sub(r"[{}<>\[\]]", " ", t))
    return wl

# ------------------------- load train split ---------------------------------------
def load_train_rows():
    from datasets import load_dataset
    ds = load_dataset("framolfese/2wikimultihopqa", split="train")
    rows, acct = [], Counter()
    for i, r in enumerate(ds):
        rows.append(dict(idx=i, hf_id=r["id"], question=(r["question"] or "").strip(),
                         answer=str(r["answer"]).strip(), type=r.get("type", ""),
                         evidences=[list(e) for e in (r.get("evidences") or [])],
                         sf_titles=list(r["supporting_facts"]["title"]),
                         sf_sent=list(r["supporting_facts"]["sent_id"]),
                         titles=list(r["context"]["title"]),
                         sents=[list(s) for s in r["context"]["sentences"]]))
    cands = []
    for r in rows:
        a, q = r["answer"], r["question"]
        if not a or a.lower() in ("yes", "no"):
            acct["drop_yesno_or_empty_answer"] += 1; continue
        if len(a) > 60 or "\n" in a:
            acct["drop_long_answer"] += 1; continue
        if not q.endswith("?") or not (6 <= len(q.split()) <= 60):
            acct["drop_question_shape"] += 1; continue
        if len(r["evidences"]) < 2:
            acct["drop_few_evidences"] += 1; continue
        if len(r["titles"]) < 4 or len(r["titles"]) != len(r["sents"]):
            acct["drop_context_shape"] += 1; continue
        tset = set(r["titles"])
        if any(t not in tset for t in r["sf_titles"]) or not all(
                si < len(r["sents"][r["titles"].index(t)])
                for t, si in zip(r["sf_titles"], r["sf_sent"])):
            acct["drop_supporting_incomplete"] += 1; continue
        sup = [(t, r["sents"][r["titles"].index(t)]) for t in dict.fromkeys(r["sf_titles"])]
        if not any(contains(passage_text(t, ss), a) for t, ss in sup):
            acct["drop_answer_not_in_supporting"] += 1; continue
        acct["pass_all_filters"] += 1
        cands.append(r)
    return cands, dict(acct), len(rows)

def load_eval_guard():
    """(800 eval hf_ids, their norm(question) set, their ALL context titles,
    eval prompt norm-texts, eval 8-gram set)."""
    from datasets import load_dataset
    pool = json.loads(EVAL_POOL_FILE.read_text())
    used_ids = set(pool["main_hf_ids"]) | set(pool["donor_hf_ids"])
    assert len(used_ids) == 800, f"expected 800 used eval families, got {len(used_ids)}"
    ds = load_dataset("framolfese/2wikimultihopqa", split="validation")
    q_norms, ctx_titles = set(), set()
    found = 0
    for r in ds:
        if r["id"] in used_ids:
            found += 1
            q_norms.add(norm(r["question"]))
            ctx_titles.update(r["context"]["title"])
    assert found == 800, f"only {found}/800 eval families found in validation"
    eval_prompt_parts, eval_gram_hashes = [], set()
    with EVAL_PROTO_FILE.open() as f:
        for line in f:
            row = json.loads(line)
            txt = row["prompt"] + " " + str(row["gold"])
            eval_prompt_parts.append(norm(txt))
            eval_gram_hashes |= {hash(g) for g in grams8(txt)}
    # word-boundary-safe haystack: parts are normalized token streams, joined
    # and padded with spaces so " <ns> " membership == contiguous-token match
    # (and therefore consistent with the 8-gram prefilter)
    eval_prompt_blob = " " + " @@ ".join(eval_prompt_parts) + " "
    return used_ids, q_norms, ctx_titles, eval_prompt_blob, eval_gram_hashes

def fid_tr(r):
    return f"w2ktr_{r['idx']:07d}"

# ------------------------- donors ---------------------------------------------------
def donor_structs(donors):
    out = []
    for d in donors:
        sup = []
        for t in dict.fromkeys(d["sf_titles"]):
            ss = d["sents"][d["titles"].index(t)]
            txt = passage_text(t, ss)
            if any(b in txt.lower() for b in bke.BANNED_MARKERS):
                continue
            sup.append((t, ss, norm(txt)))
        out.append(dict(d=d, fid=fid_tr(d), sup=sup, n_ans=norm(d["answer"])))
    return out

def pick_irrelevant(r, dindex):
    """Donor supporting passage sharing no bridge entity with r, no gold alias."""
    rng = rng_for(fid_tr(r), "irr")
    als = {norm(a) for a in aliases(r["answer"])}
    ents = [ne for _, ne in bridge_entities(r)]
    order = list(range(len(dindex)))
    rng.shuffle(order)
    for i in order:
        dd = dindex[i]
        if dd["n_ans"] == norm(r["answer"]):
            continue
        for t, ss, ntxt in dd["sup"]:
            if t in set(r["titles"]):
                continue
            if any(a and a in ntxt for a in als):
                continue
            if any(ne in ntxt for ne in ents):
                continue
            return dd, (t, ss)
    return None, None

def pick_confusable(r, dindex):
    """Donor supporting passage that DOES mention a bridge entity of r."""
    rng = rng_for(fid_tr(r), "conf")
    als = {norm(a) for a in aliases(r["answer"])}
    ents = bridge_entities(r)
    order = list(range(len(dindex)))
    rng.shuffle(order)
    for i in order:
        dd = dindex[i]
        if dd["n_ans"] == norm(r["answer"]):
            continue
        for t, ss, ntxt in dd["sup"]:
            if t in set(r["titles"]):
                continue
            if any(a and a in ntxt for a in als):
                continue
            for e, ne in ents:
                if ne in ntxt:
                    return dd, (t, ss), e
    return None, None, None

# ------------------------- per-pool builders ---------------------------------------
def base_passages(r):
    return list(zip(r["titles"], r["sents"]))

def base_row(r, component, subtype, template_id="-"):
    return dict(family_id=fid_tr(r), source_id=r["hf_id"], source_split="train",
                generator_id="A", generator_version=GEN_VER, domain="knowledge",
                component=component, subtype=subtype, template_id=template_id)

def build_clean_replay(fams):
    rows = []
    for r in fams:
        t, s = support_citation(r)
        row = base_row(r, "clean_replay", "plain")
        row.update(prompt=prompt_a(base_passages(r), r["question"]),
                   target=answer_skeleton(r, t, s),
                   meta={"cite_title": t, "cite_sentence": s})
        rows.append(row)
    return rows

def format_target(r, sch, t, s):
    g = r["answer"]
    if sch["id"] == "KA1":
        return json.dumps({"answer": g, "evidence_title": t}, ensure_ascii=False)
    if sch["id"] == "KA2":
        return json.dumps({"entity": g, "quote": s}, ensure_ascii=False)
    if sch["id"] == "KA3":
        return f"entity: {g} | source: {t}"
    return f'<result answer="{g}" source="{t}"/>'

def format_target_valid(r, sch, target, t, s):
    g = r["answer"]
    if sch["id"] in ("KA1", "KA2"):
        try:
            obj = json.loads(target)
        except Exception:
            return False
        if sch["id"] == "KA1":
            return set(obj) == {"answer", "evidence_title"} and obj["answer"] == g \
                and obj["evidence_title"] == t
        return set(obj) == {"entity", "quote"} and obj["entity"] == g and obj["quote"] == s
    if sch["id"] == "KA3":
        m = re.fullmatch(r"entity: (.+) \| source: (.+)", target)
        return bool(m) and m.group(1) == g and m.group(2) == t
    m = re.fullmatch(r'<result answer="(.+)" source="(.+)"/>', target)
    return bool(m) and m.group(1) == g and m.group(2) == t

def build_format(fams):
    rows, errs = [], []
    for i, r in enumerate(fams):
        sch = KA_SCHEMAS[i % 4]
        t, s = support_citation(r)
        target = format_target(r, sch, t, s)
        if not format_target_valid(r, sch, target, t, s):
            errs.append(("format_target_invalid", fid_tr(r)))
        row = base_row(r, "format", f"schema_{sch['id']}", sch["id"])
        row.update(prompt=prompt_a(base_passages(r), r["question"]) + "\n\n" + sch["instr"],
                   target=target,
                   meta={"cite_title": t, "schema": sch["id"],
                         "cite_sentence": s if sch["id"] == "KA2" else ""})
        rows.append(row)
    return rows, errs

def build_evidence(fams, dindex, donor_pool):
    quota = {"false_fact": 667, "irrelevant_passage": 667, "confusable_passage": 666}
    got = Counter()
    rows, errs, used = [], [], set()
    donor_reg = Counter()
    for r in fams:
        if sum(got.values()) == N_POOL:
            break
        fid = fid_tr(r)
        t_sup, s_sup = support_citation(r)
        skel = answer_skeleton(r, t_sup, s_sup)
        placed = False
        # try subtypes in order of remaining need (deterministic tie-break by name)
        for st in sorted(quota, key=lambda k: (got[k] - quota[k], k)):
            if got[st] >= quota[st]:
                continue
            if st == "false_fact":
                cand, csrc = pick_wrong_candidate(r, donor_pool)
                if not cand:
                    continue
                extra = FALSE_FACT_NOTE.format(w=cand)
                row = base_row(r, "evidence", st)
                row.update(prompt=prompt_a(base_passages(r), r["question"], extra=extra),
                           target=f"{REFUTE_FALSE.format(w=cand)} {skel}",
                           meta={"wrong": cand, "wrong_source": csrc,
                                 "cite_title": t_sup, "cite_sentence": s_sup})
            elif st == "irrelevant_passage":
                dd, dp = pick_irrelevant(r, dindex)
                if not dp:
                    continue
                row = base_row(r, "evidence", st)
                row.update(prompt=prompt_a(base_passages(r) + [dp], r["question"]),
                           target=f"{REFUTE_IRREL.format(t=dp[0])} {skel}",
                           meta={"donor_family": dd["fid"], "donor_title": dp[0],
                                 "insert_pos": "last", "cite_title": t_sup,
                                 "cite_sentence": s_sup})
                donor_reg[dd["fid"]] += 1
            else:
                dd, dp, ent = pick_confusable(r, dindex)
                if not dp:
                    continue
                row = base_row(r, "evidence", st)
                row.update(prompt=prompt_a(base_passages(r) + [dp], r["question"]),
                           target=f"{REFUTE_CONF.format(t=dp[0], e=ent)} {skel}",
                           meta={"donor_family": dd["fid"], "donor_title": dp[0],
                                 "matched_entity": ent, "insert_pos": "last",
                                 "cite_title": t_sup, "cite_sentence": s_sup})
                donor_reg[dd["fid"]] += 1
            got[st] += 1
            used.add(fid)
            rows.append(row)
            placed = True
            break
        if not placed:
            errs.append(("evidence_family_unusable", fid))
    if sum(got.values()) != N_POOL:
        errs.append(("evidence_quota_unfilled", dict(got)))
    return rows, dict(got), donor_reg, [e for e in errs if e[0] != "evidence_family_unusable"]

def donor_meta_of(donors):
    return [(d["answer"], expected_answer_class(d), answer_kind(d["answer"]))
            for d in donors]

def pick_donor_answer(r, donor_meta):
    """Class-matched (else kind-matched) donor-pool answer != gold."""
    rng = rng_for(fid_tr(r), "fixwc")
    gold, cls, kind = r["answer"], expected_answer_class(r), answer_kind(r["answer"])

    def ok(c):
        return norm(c) != norm(gold) and not contains(c, gold) and not contains(gold, c)

    for match in (lambda a, c, k: c == cls, lambda a, c, k: k == kind):
        cands = sorted({a for a, c, k in donor_meta if match(a, c, k) and ok(a)})
        rng.shuffle(cands)
        if cands:
            return cands[0]
    return None

def pick_fix_candidate(r, donor_meta, want):
    """Return (cand, cited_title, hop, source) for the fix side.
    similar_entity -> non-supporting context title, cited to its own passage (hop 1)
    wrong_citation -> donor-pool class-matched answer cited to a supporting title
                      whose text does NOT contain it (hop 2)."""
    gold = r["answer"]

    def ok(c):
        return norm(c) != norm(gold) and not contains(c, gold) and not contains(gold, c)

    order = (("similar_entity", "wrong_citation") if want == "similar_entity"
             else ("wrong_citation", "similar_entity"))
    for kind in order:
        if kind == "similar_entity":
            titles = [t for t in r["titles"] if t not in set(r["sf_titles"]) and ok(t)]
            rng = rng_for(fid_tr(r), "fixse")
            rng.shuffle(titles)
            if titles:
                return titles[0], titles[0], "similar_entity", "same_context_title"
        else:
            cand = pick_donor_answer(r, donor_meta)
            if cand:
                for t in dict.fromkeys(r["sf_titles"]):
                    ss = r["sents"][r["titles"].index(t)]
                    if not contains(passage_text(t, ss), cand):
                        return cand, t, "wrong_citation", "donor_answer"
    return None, None, None, None

def build_revision(fams, donor_meta):
    rows, errs = [], []
    kinds = Counter()
    want_cycle = ["similar_entity", "wrong_citation"]
    n_fam = 0
    for i, r in enumerate(fams):
        if n_fam == N_PAIR_FAM:
            break
        t_sup, s_sup = support_citation(r)
        cand, cited, hop, csrc = pick_fix_candidate(r, donor_meta, want_cycle[i % 2])
        if not cand:
            continue
        p = prompt_a(base_passages(r), r["question"])
        keep_line = CAND_LINE.format(c=r["answer"], t=t_sup)
        keep = base_row(r, "revision", "keep")
        keep.update(prompt=f"{p}\n\n{keep_line}\n\nIs the previous answer right? "
                           "If it is, keep it; if not, correct it.",
                    target=f"{KEEP_HEAD} {answer_skeleton(r, t_sup, s_sup)}",
                    meta={"cand": r["answer"], "cited_title": t_sup,
                          "cite_sentence": s_sup})
        hop_reason = (HOP1 if hop == "similar_entity" else HOP2).format(t=cited)
        fix_line = CAND_LINE.format(c=cand, t=cited)
        fix = base_row(r, "revision", f"fix_{hop}")
        fix.update(prompt=f"{p}\n\n{fix_line}\n\nIs the previous answer right? "
                          "If it is, keep it; if not, correct it.",
                   target=(f"{FIX_HEAD} {hop_reason} "
                           f'Based on the source "{t_sup}": "{s_sup}" '
                           + FIX_TAIL.format(g=r["answer"])),
                   meta={"cand": cand, "cited_title": cited, "hop": hop,
                         "cand_source": csrc, "cite_sentence": s_sup})
        rows += [keep, fix]
        kinds[hop] += 1
        n_fam += 1
    if n_fam != N_PAIR_FAM:
        errs.append(("revision_family_shortfall", n_fam))
    return rows, dict(kinds), errs

def build_answerability(fams):
    rows, errs = [], []
    n_fam = 0
    for r in fams:
        if n_fam == N_PAIR_FAM:
            break
        ins, _why = build_insufficient(r)
        if ins is None:
            continue
        kept, removed = ins
        t_sup, s_sup = support_citation(r)
        suff = base_row(r, "answerability", "sufficient")
        suff.update(prompt=prompt_a(base_passages(r), r["question"]),
                    target=answer_skeleton(r, t_sup, s_sup),
                    meta={"cite_title": t_sup, "cite_sentence": s_sup})
        insuf = base_row(r, "answerability", "insufficient")
        insuf.update(prompt=prompt_a(kept, r["question"]),
                     target=ABSTAIN_TARGET,
                     meta={"removed_titles": removed, "n_kept": len(kept)})
        rows += [suff, insuf]
        n_fam += 1
    if n_fam != N_PAIR_FAM:
        errs.append(("answerability_family_shortfall", n_fam))
    return rows, errs

# ------------------------- verification --------------------------------------------
QUOTE_RE = re.compile(r'"([^"]+)"')

def strip_quotes(text):
    """Remove quoted spans (verbatim source citations) for the dup-rate check."""
    return QUOTE_RE.sub(" ", text)

# Constant fragments of the declared target templates (K_TRAINING_SPEC §1).
# Every target is program-rendered from a declared template and re-validated,
# so the 8-gram dup gate runs on the CONTENT layer: quotes stripped, then
# these constants removed; what remains is slot values (answers/titles/
# entities). Raw and quote-stripped rates are reported as diagnostics.
TEMPLATE_FRAGMENTS = [
    ABSTAIN_TARGET, KEEP_HEAD, FIX_HEAD,
    "Based on the source", "The correct answer is", "The answer is",
    "The attached note is wrong: the sources do not support",
    "The source about", "is unrelated to this question.",
    "but does not answer this question.", "The source", "mentions",
    "It picks the wrong entity: the cited source",
    "is not where this question's answer is established.",
    "The cited source",
    "does not state that answer; the citation does not support it.",
    "entity:", "| source:", "<result answer=", "source=", "/>",
]

def content_view(target):
    t = strip_quotes(target)
    for frag in TEMPLATE_FRAGMENTS:
        t = t.replace(frag, " ")
    return t

def verify_pool(name, rows, expected_n, whitelist, eval_gram_hashes, eval_prompt_blob):
    errs, report = [], {}
    if len(rows) != expected_n:
        errs.append((name, "pool_size", len(rows)))
    prompts = [r["prompt"] for r in rows]
    if len(set(prompts)) != len(prompts):
        errs.append((name, "duplicate_prompts", len(prompts) - len(set(prompts))))
    for r in rows:
        if any(b in r["target"] for b in BANNED_IN_TARGET):
            errs.append((name, "eval_readout_token_in_target", r["family_id"]))
        if r["source_split"] != "train":
            errs.append((name, "wrong_split", r["family_id"]))
    # content checks
    for r in rows:
        g = norm_gold(r)
        st = r["subtype"]
        tgt = r["target"]
        if st == "insufficient":
            # sources section only: the fixed instruction text can spuriously
            # contain aliases of stopword-like answers ("The Information")
            body = r["prompt"].split("Sources:\n", 1)[1].split("\n\nQ:")[0]
            for al in aliases(g):
                if contains(body, al):
                    errs.append((name, "insufficient_context_leak", r["family_id"]))
                # target alias check only for non-constant targets: the fixed
                # refusal formula is family-independent text and cannot convey
                # the answer (stopword-like golds such as "The Answer" would
                # false-positive on it)
                if tgt != ABSTAIN_TARGET and contains(tgt, al):
                    errs.append((name, "insufficient_target_leak", r["family_id"]))
            if tgt != ABSTAIN_TARGET:
                errs.append((name, "abstain_not_formulaic", r["family_id"]))
        else:
            if not contains(tgt, g):
                errs.append((name, "gold_missing_from_target", r["family_id"]))
        if st.startswith("fix_") and norm(str(r["meta"]["cand"])) == norm(g):
            errs.append((name, "fix_cand_eq_gold", r["family_id"]))
        if st == "keep" and norm(str(r["meta"]["cand"])) != norm(g):
            errs.append((name, "keep_cand_neq_gold", r["family_id"]))
        if st == "false_fact" and norm(str(r["meta"]["wrong"])) == norm(g):
            errs.append((name, "false_fact_eq_gold", r["family_id"]))
        if st in ("irrelevant_passage", "confusable_passage"):
            # injected donor passage must not contain a gold alias
            last_src = r["prompt"].split("\n\nQ:")[0].strip().split("\n")[-1]
            if any(contains(last_src, al) for al in aliases(g)):
                errs.append((name, "injected_passage_gold_leak", r["family_id"]))
    # 8-gram: family-level dup rate within pool. Gate on the content layer
    # (quotes + declared template constants removed); quote-stripped and raw
    # rates are reported alongside as diagnostics.
    fam_grams_gate, fam_grams_qs, fam_grams_raw = {}, {}, {}
    for r in rows:
        fid = r["family_id"]
        fam_grams_gate.setdefault(fid, set()).update(
            grams8(content_view(r["target"])) - whitelist)
        fam_grams_qs.setdefault(fid, set()).update(
            grams8(strip_quotes(r["target"])) - whitelist)
        fam_grams_raw.setdefault(fid, set()).update(grams8(r["target"]) - whitelist)

    def dup_rate_of(fam_grams):
        seen, dup = set(), 0
        for f in fam_grams:
            if fam_grams[f] & seen:
                dup += 1
            seen |= fam_grams[f]
        return dup / max(len(fam_grams), 1)

    gate_rate = dup_rate_of(fam_grams_gate)
    report["nonskeleton_8gram_dup_rate_family_contentlayer_GATE"] = round(gate_rate, 4)
    report["nonskeleton_8gram_dup_rate_family_quotestripped"] = round(
        dup_rate_of(fam_grams_qs), 4)
    report["nonskeleton_8gram_dup_rate_family_raw"] = round(dup_rate_of(fam_grams_raw), 4)
    if gate_rate > 0.05:
        errs.append((name, "family_8gram_dup_rate_gt_5pct", gate_rate))
    # target x eval-prompt 8-gram scan (report; same-article collisions are
    # impossible by the supporting-title guard, residue = generic phrasing)
    coll = set()
    for f in fam_grams_raw:
        coll |= {g for g in fam_grams_raw[f] if hash(g) in eval_gram_hashes}
    report["target_x_eval_8gram_collisions"] = sorted(coll)[:50]
    report["target_x_eval_8gram_collision_count"] = len(coll)
    # sentence-level quote leak into any eval prompt (hard gate; sentences of
    # >=8 normalized tokens — below the preregistered n-gram granularity a
    # "leak" is just generic phrasing)
    quote_leaks = 0
    for r in rows:
        # the quoted citation sentence is carried in meta by the builders, so
        # the gate checks exactly the string the load-time guard screened
        # (regex re-extraction truncates at internal double quotes and would
        # gate on tail fragments the guard never saw); regex kept as fallback
        s = r["meta"].get("cite_sentence", "")
        if not s:
            m = re.search(r'"([^"]{20,})" The (?:correct )?answer is', r["target"])
            s = m.group(1) if m else (json.loads(r["target"]).get("quote", "")
                                      if r["subtype"] == "schema_KA2" else "")
        if s:
            ns = norm(s)
            if len(ns.split()) >= 8 and f" {ns} " in eval_prompt_blob:
                quote_leaks += 1
    report["quoted_sentence_in_eval_prompt"] = quote_leaks
    if quote_leaks:
        errs.append((name, "quoted_sentence_leaks_into_eval_prompt", quote_leaks))
    return errs, report

def norm_gold(row):
    return row["meta"].get("gold", row.get("gold", "")) or row["_gold"]

# ------------------------- manifests / samples -------------------------------------
def target_len_buckets(rows):
    b = Counter()
    for r in rows:
        n = len(r["target"].split())
        b["<50" if n < 50 else "50-100" if n < 100 else "100-200" if n < 200
          else "200-400" if n < 400 else ">=400"] += 1
    return {k: b.get(k, 0) for k in ("<50", "50-100", "100-200", "200-400", ">=400")}

def bundles_of(name, rows):
    if name in ("k_revision_2000", "k_answerability_2000"):
        order = list(dict.fromkeys(r["family_id"] for r in rows))
        return order, "pair"
    return [r["family_id"] for r in rows], "single"

def write_pool(name, rows, extra_manifest, report):
    f = POOLS / f"{name}.jsonl"
    f.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    sha = hashlib.sha256(f.read_bytes()).hexdigest()[:16]
    bundle_ids, bkind = bundles_of(name, rows)
    random.Random(SEED).shuffle(bundle_ids)
    man = {"pool": name, "seed": SEED, "generator_version": GEN_VER,
           "spec": "prescription/knowledge/K_TRAINING_SPEC.md",
           "source": {"dataset": "framolfese/2wikimultihopqa", "split": "train"},
           "n": len(rows), "sha256_16": sha,
           "by_subtype": dict(Counter(r["subtype"] for r in rows)),
           "n_families": len({r["family_id"] for r in rows}),
           "target_length_buckets_wordcount": target_len_buckets(rows),
           "bundle_kind": bkind,
           "nested_bundle_order_seed": SEED,
           "nested_bundle_order": bundle_ids,
           "scan_report": report}
    man.update(extra_manifest)
    (POOLS / f"{name}_manifest.json").write_text(
        json.dumps(man, indent=2, ensure_ascii=False))
    # sample10
    rng = random.Random(SEED)
    by_st = {}
    for r in rows:
        by_st.setdefault(r["subtype"], []).append(r)
    picks = []
    while len(picks) < 10:
        for st in sorted(by_st):
            pool = [r for r in by_st[st] if r not in picks]
            if pool and len(picks) < 10:
                picks.append(rng.choice(pool))
    lines = [f"# sample10 — {name} (seed {SEED}, generator A, 2Wiki train)\n"]
    for r in picks:
        lines.append(f"## {r['family_id']}  [{r['subtype']}]\n")
        lines.append("```text\n" + r["prompt"] + "\n```\n")
        lines.append("**target**\n\n```text\n" + r["target"] + "\n```\n")
        if r["meta"]:
            lines.append("meta: `" + json.dumps(r["meta"], ensure_ascii=False) + "`\n")
    (POOLS / f"sample10_{name}.md").write_text("\n".join(lines))
    return man

# ------------------------- main -----------------------------------------------------
def main():
    POOLS.mkdir(exist_ok=True)
    (used_ids, eval_qnorms, eval_ctx_titles,
     eval_prompt_blob, eval_gram_hashes) = load_eval_guard()
    cands, acct, n_total = load_train_rows()
    acct2 = Counter()
    guarded = []
    for r in cands:
        if r["hf_id"] in used_ids:
            acct2["drop_eval_used_hf_id"] += 1; continue
        if norm(r["question"]) in eval_qnorms:
            acct2["drop_eval_question_dup"] += 1; continue
        if any(t in eval_ctx_titles for t in r["sf_titles"]):
            acct2["drop_supporting_title_in_eval_context"] += 1; continue
        # citation-sentence guard: the sentence every target would quote must
        # not appear verbatim in any eval prompt (duplicate passages can recur
        # under different titles, so the title guard alone is not enough).
        # 8-gram hash prefilter keeps this cheap; sentences <8 norm tokens are
        # below the preregistered granularity and exempt (gate matches).
        _t, s_cit = support_citation(r)
        ns = norm(s_cit or "")
        if len(ns.split()) >= 8:
            gs = grams8(s_cit)
            if (not gs or any(hash(g) in eval_gram_hashes for g in gs)) \
                    and f" {ns} " in eval_prompt_blob:
                acct2["drop_citation_sentence_in_eval_prompt"] += 1; continue
        guarded.append(r)
    rng = random.Random(SEED)
    rng.shuffle(guarded)

    # allocation: donors first, then ANS (needs insufficient survivors),
    # REV (needs fix candidate), EVD, FMT, replay
    donors = guarded[:N_DONOR]
    rest = guarded[N_DONOR:]
    dindex = donor_structs(donors)
    donor_meta = donor_meta_of(donors)

    it = iter(rest)
    taken = set()

    def take(n, pred):
        out = []
        for r in it:
            if pred(r):
                out.append(r)
                taken.add(fid_tr(r))
                if len(out) == n:
                    break
        return out

    # over-allocate candidate families; builders stop at their quota
    ans_f = take(int(N_PAIR_FAM * 1.6), lambda r: build_insufficient(r)[0] is not None)
    rev_f = take(int(N_PAIR_FAM * 1.3),
                 lambda r: pick_fix_candidate(r, donor_meta, "similar_entity")[0] is not None)
    evd_f = take(int(N_POOL * 1.25), lambda r: True)
    fmt_f = take(N_POOL, lambda r: True)
    rep_f = take(N_POOL, lambda r: True)

    whitelist = skeleton_whitelist()

    ans_rows, e1 = build_answerability(ans_f)
    rev_rows, rev_kinds, e2 = build_revision(rev_f, donor_meta)
    evd_rows, evd_got, evd_donor_reg, e3 = build_evidence(evd_f, dindex, donors)
    fmt_rows, e4 = build_format(fmt_f)
    rep_rows = build_clean_replay(rep_f)
    hard_errs = e1 + e2 + e3 + e4

    pools = {"k_answerability_2000": ans_rows, "k_revision_2000": rev_rows,
             "k_evidence_2000": evd_rows, "k_format_2000": fmt_rows,
             "k_clean_replay_2000": rep_rows}

    # attach gold for verification convenience (not serialized twice)
    fam_gold = {fid_tr(r): r["answer"] for r in guarded}
    for rows in pools.values():
        for r in rows:
            r["_gold"] = fam_gold[r["family_id"]]

    # cross-pool disjointness + donor isolation
    fam_sets = {k: {r["family_id"] for r in v} for k, v in pools.items()}
    names = sorted(fam_sets)
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            inter = fam_sets[a] & fam_sets[b]
            if inter:
                hard_errs.append(("cross_pool_family_overlap", a, b, len(inter)))
    donor_fids = {fid_tr(d) for d in donors}
    for k, s in fam_sets.items():
        if s & donor_fids:
            hard_errs.append(("donor_in_main_pool", k, len(s & donor_fids)))

    manifests, reports = {}, {}
    for name, rows in pools.items():
        errs, report = verify_pool(name, rows, N_POOL, whitelist,
                                   eval_gram_hashes, eval_prompt_blob)
        hard_errs += [e for e in errs
                      if e[1] != "target_x_eval_8gram_collision_count"]
        reports[name] = report

    stats = {"generator_version": GEN_VER, "seed": SEED,
             "dataset": "framolfese/2wikimultihopqa", "split": "train",
             "train_rows_total": n_total, "filter_accounting": acct,
             "eval_guard_accounting": dict(acct2),
             "candidates_after_guards": len(guarded),
             "donor_pool_families": len(donors),
             "evidence_subtypes": evd_got, "revision_fix_kinds": rev_kinds,
             "evidence_donor_reuse_max": max(evd_donor_reg.values()) if evd_donor_reg else 0,
             "hard_errors": [list(map(str, e)) for e in hard_errs]}

    if hard_errs:
        (POOLS / "build_stats_kpools.json").write_text(json.dumps(stats, indent=2))
        print(json.dumps(stats, indent=2)[:4000])
        raise SystemExit(f"HARD FAIL: {len(hard_errs)} gate errors — no pools written")

    for name, rows in pools.items():
        for r in rows:
            r.pop("_gold", None)
        extra = {}
        if name == "k_evidence_2000":
            extra = {"donor_families_used": sorted({r["meta"]["donor_family"]
                                                    for r in rows if "donor_family" in r["meta"]}),
                     "donor_pool_size": len(donors)}
        manifests[name] = write_pool(name, rows, extra, reports[name])

    ledger = {"seed": SEED, "spec": "K_TRAINING_SPEC.md",
              "eval_families_excluded": {"count": 800,
                                         "source": "main_pool_k500.json (main 500 + donor 300, validation)"},
              "cross_pool_sharing": "none — five main pools pairwise disjoint",
              "pools": {k: sorted(v) for k, v in fam_sets.items()},
              "donor_pool_train_split": sorted(donor_fids),
              "donor_rule": ("evidence/revision donors only; never a main family in any K "
                             "training or eval pool (C-30 #7 discipline, train side)")}
    (POOLS / "K_FAMILY_LEDGER.json").write_text(json.dumps(ledger, indent=2))
    stats["pools"] = {k: {kk: m[kk] for kk in ("n", "n_families", "sha256_16",
                                               "by_subtype", "target_length_buckets_wordcount")}
                      for k, m in manifests.items()}
    stats["scan_reports"] = {k: {kk: vv for kk, vv in v.items()
                                 if kk != "target_x_eval_8gram_collisions"}
                             for k, v in reports.items()}
    (POOLS / "build_stats_kpools.json").write_text(
        json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
