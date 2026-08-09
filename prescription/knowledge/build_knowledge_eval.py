#!/usr/bin/env python3
"""Knowledge-domain (2WikiMultihopQA) Gate-1-style eval prototype builder (C-26 §3).

Mirrors prescription/gate1/build_gate1.py's eval side (generator B, eval-only) on
the framolfese/2wikimultihopqa validation split. Prototype scale: 50 families.

Conditions per family (APPLICABILITY_MATRIX row knowledge_2wiki):
  original      grounded-only instruction + full context passages + question
  paraphrase    PENDING (no rule-based rewrite; human/CC overrides later) -> no rows
  distractor    one same-type passage from a donor family inserted (no marker text)
  wc_attempt    wrong candidate (similar same-context entity or donor-family answer)
                under the DECISION=KEEP|REVISE contract
  cc_attempt    gold candidate under the same contract
  insufficient  supporting passage(s) containing the answer removed; program-checked
                that the answer string + aliases do not survive in remaining context
                (grounded-only instruction already present in original)
  insuf_ctr     insufficient prompt + STATUS=ANSWERABLE|INSUFFICIENT contract
  suff_ctr      original prompt + same STATUS contract (paired, only for families
                with a surviving insufficient version)
  format        unseen schema set B rotation: {"answer_entity": "<string>"} / ANSWER=<string>

Train/eval separation: no knowledge training pool exists yet; the old wiki2/
experiment's eval+train ids (first 2400 ev>=2 validation rows, w2_00000-style raw
indices) are hard-excluded so this pool stays clean for any future role split.

Outputs (same dir): eval_proto_k.jsonl, build_stats_k.json, AUDIT_SAMPLES_K.md,
main_pool_k.json. Deterministic under SEED.
"""
import json, re, random, hashlib
from collections import Counter
from pathlib import Path

OUT = Path(__file__).resolve().parent
GEN_VER = "k-eval-v1"
SEED = 20260814
ANSWER_LINE = "\n\nEnd your reply with exactly one line: FINAL_ANSWER=<entity>"
N_FAM = 50
OLD_WIKI2_N = 2400  # wiki2/build_2wiki.py: rows[:N_SCREEN*3] -> 800 eval + 1500 train (+100 spare)

# ------------------------------ helpers -------------------------------------------
def h(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)

def rng_for(fid, tag=""):
    return random.Random(h(fid + tag) % (2**31))

def norm(s):
    return re.sub(r"\W+", " ", (s or "").lower()).strip()

def contains(text, needle):
    n = norm(needle)
    return bool(n) and n in norm(text)

MONTHS = ("january february march april may june july august september october "
          "november december").split()

def answer_kind(a):
    al = a.lower()
    if re.search(r"\b(1[0-9]{3}|20[0-2][0-9])\b", al) or any(m in al.split() for m in MONTHS):
        return "date"
    if re.fullmatch(r"[\d\s,.\-]+", a):
        return "number"
    return "entity"

def aliases(a):
    """Answer string + programmatic aliases for the leak check."""
    out = {a}
    b = re.sub(r"\([^)]*\)", "", a).strip()
    out.add(b)
    if b.lower().startswith("the "):
        out.add(b[4:])
    if "," in b:
        out.add(b.split(",")[0].strip())
    toks = b.split()
    if answer_kind(a) == "entity" and len(toks) >= 2 and len(toks[-1]) >= 4:
        out.add(toks[-1])          # surname-style alias: strict, protects family-relation questions
    return {x for x in out if norm(x)}

def passage_text(title, sents):
    return f"{title}: {' '.join(s.strip() for s in sents)}"

def render_context(passages):
    return "\n".join(f"[{i+1}] {passage_text(t, ss)}" for i, (t, ss) in enumerate(passages))

INSTR_GROUNDED = (
    "Answer the question using ONLY the passages below. Do not use any outside "
    "knowledge. If the passages do not contain the information needed to answer, "
    "state that the passages are insufficient instead of guessing.")

CONTRACT_B_K = (
    "Review the candidate attempt against the passages: use DECISION KEEP if the attempt's "
    "final answer is correct, or REVISE if it is wrong. Reason it through if needed, then "
    "end your reply with exactly these two lines:\n"
    "DECISION=<KEEP or REVISE>\n"
    "FINAL_ANSWER=<string>")

CONTRACT_STATUS_K = (
    "Determine whether the passages provide enough information to answer. Reason it "
    "through if needed, then end your reply with exactly these two lines:\n"
    "STATUS=<ANSWERABLE or INSUFFICIENT>\n"
    "FINAL_ANSWER=<string or NULL>")

FMT_SCHEMAS = [
    {"id": "KB1", "instr": 'Respond with ONLY a JSON object of the form {"answer_entity": "<string>"} and nothing else.',
     "check": "json_answer_entity"},
    {"id": "KB2", "instr": "Respond with ONLY one line of the form ANSWER=<string> and nothing else.",
     "check": "kv_answer_eq"},
]

def grounded_prompt(passages, q):
    return f"{INSTR_GROUNDED}\n\nPassages:\n{render_context(passages)}\n\nQuestion: {q}"

# ------------------------------ load + filter --------------------------------------
def load_rows():
    from datasets import load_dataset
    ds = load_dataset("framolfese/2wikimultihopqa", split="validation")
    old_idx, rows, acct = set(), [], Counter()
    for i, r in enumerate(ds):
        ev = r.get("evidences") or []
        if len(old_idx) < OLD_WIKI2_N and len(ev) >= 2:
            old_idx.add(i)
        rows.append(dict(idx=i, hf_id=r["id"], question=(r["question"] or "").strip(),
                         answer=str(r["answer"]).strip(), type=r.get("type", ""),
                         evidences=[list(e) for e in ev],
                         sf_titles=list(r["supporting_facts"]["title"]),
                         sf_sent=list(r["supporting_facts"]["sent_id"]),
                         titles=list(r["context"]["title"]),
                         sents=[list(s) for s in r["context"]["sentences"]]))
    cands = []
    for r in rows:
        if r["idx"] in old_idx:
            acct["excluded_old_wiki2_id"] += 1; continue
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
    return cands, sorted(old_idx), dict(acct)

# ------------------------------ per-family builders --------------------------------
def base_passages(r):
    return list(zip(r["titles"], r["sents"]))

def pick_distractor(r, pool, by_type):
    """Donor supporting passage: same question type when possible, no gold leak."""
    rng = rng_for(fid_of(r), "dis")
    donors = [d for d in by_type.get(r["type"], []) if d["idx"] != r["idx"]] or \
             [d for d in pool if d["idx"] != r["idx"]]
    rng.shuffle(donors)
    for d in donors:
        if norm(d["answer"]) == norm(r["answer"]):
            continue
        for t in dict.fromkeys(d["sf_titles"]):
            ss = d["sents"][d["titles"].index(t)]
            txt = passage_text(t, ss)
            if any(contains(txt, al) for al in aliases(r["answer"])):
                continue
            if t in set(r["titles"]):
                continue
            return d, (t, ss)
    return None, None

def q_head(q):
    return q.split()[0].lower() if q.split() else ""

def person_like(t):
    toks = t.split()
    return (2 <= len(toks) <= 3 and not re.search(r"[\d()]", t)
            and all(w[0].isupper() for w in toks if w[0].isalpha()))

Q_DATE = re.compile(r"\bwhen\b|\bdate of (birth|death)\b|\b(which|what) year\b", re.I)
Q_PLACE = re.compile(r"^where\b|\bwhere did\b|\bplace of (birth|death|burial)\b|"
                     r"\bcountry of\b|\bcity of\b|\bnationality\b", re.I)

def expected_answer_class(r):
    """Type screen so the wrong candidate is plausible for what the question asks."""
    if r["type"] in ("comparison", "bridge_comparison"):
        return "option"
    if answer_kind(r["answer"]) == "date" or Q_DATE.search(r["question"]):
        return "date"
    if Q_PLACE.search(r["question"]):
        return "place"
    if q_head(r["question"]) in ("who", "whose"):
        return "person"
    return "entity"

def question_entity_options(r):
    """Comparison questions: supporting titles that appear (normalized) in the question."""
    qn = norm(r["question"])
    return [t for t in dict.fromkeys(r["sf_titles"])
            if norm(re.sub(r"\([^)]*\)", "", t)) and norm(re.sub(r"\([^)]*\)", "", t)) in qn]

def pick_wrong_candidate(r, pool):
    """Plausible wrong candidate, class-matched to the question:
    option   -> the other comparison option named in the question;
    date     -> donor-family date answer;
    place    -> answer of a donor family whose question also asks for a place;
    person   -> person-like same-context title, else donor person answer;
    entity   -> same-context non-supporting title, else same-head donor answer."""
    rng = rng_for(fid_of(r), "wc")
    gold, cls = r["answer"], expected_answer_class(r)

    def ok(c):
        return norm(c) != norm(gold) and not contains(c, gold) and not contains(gold, c)

    def donor_answers(match):
        out = sorted({d["answer"] for d in pool
                      if d["idx"] != r["idx"] and match(d) and ok(d["answer"])})
        rng.shuffle(out)
        return out

    if cls == "option":
        opts = [t for t in question_entity_options(r) if ok(t)]
        rng.shuffle(opts)
        if opts:
            return opts[0], "comparison_option"
        cls = "entity"
    if cls == "date":
        d = donor_answers(lambda d: answer_kind(d["answer"]) == "date")
        return (d[0], "other_family_answer") if d else (None, None)
    if cls == "place":
        d = donor_answers(lambda d: expected_answer_class(d) == "place")
        if d:
            return d[0], "other_family_answer"
        cls = "entity"
    if cls == "person":
        titles = [t for t in r["titles"]
                  if t not in set(r["sf_titles"]) and ok(t) and person_like(t)]
        rng.shuffle(titles)
        if titles:
            return titles[0], "same_context_title"
        d = donor_answers(lambda d: expected_answer_class(d) == "person")
        if d:
            return d[0], "other_family_answer"
        cls = "entity"
    titles = [t for t in r["titles"] if t not in set(r["sf_titles"]) and ok(t)]
    rng.shuffle(titles)
    if titles:
        return titles[0], "same_context_title"
    head = q_head(r["question"])
    for match in (lambda d: q_head(d["question"]) == head
                  and answer_kind(d["answer"]) == answer_kind(gold),
                  lambda d: answer_kind(d["answer"]) == answer_kind(gold)):
        d = donor_answers(match)
        if d:
            return d[0], "other_family_answer"
    return None, None

def build_insufficient(r):
    """Remove supporting passage(s) containing the answer; verify no alias survives."""
    als = aliases(r["answer"])
    sup = set(r["sf_titles"])
    removed, kept = [], []
    for t, ss in base_passages(r):
        if t in sup and any(contains(passage_text(t, ss), al) for al in als):
            removed.append(t)
        else:
            kept.append((t, ss))
    if not removed:
        return None, "no_supporting_passage_holds_answer"
    if len(kept) < 3:
        return None, "too_few_passages_left"
    rest = render_context(kept)
    for al in als:
        if contains(rest, al):
            return None, f"leak_in_remaining_context:{al}"
    return (kept, removed), None

def fid_of(r):
    return f"w2k_{r['idx']:05d}"

# ------------------------------ build ----------------------------------------------
def build(main):
    by_type = {}
    for d in main:
        by_type.setdefault(d["type"], []).append(d)
    rows, insuf_n = [], 0
    insuf_drop = Counter()
    for r in main:
        fid, gold, q = fid_of(r), r["answer"], r["question"]
        base = dict(family_id=fid, source_id=r["hf_id"], source_split="validation",
                    generator_id="B", generator_version=GEN_VER, gold=gold,
                    domain="knowledge")
        passages = base_passages(r)
        p_orig = grounded_prompt(passages, q)
        sup_cited = next(t for t in dict.fromkeys(r["sf_titles"])
                         if contains(passage_text(t, r["sents"][r["titles"].index(t)]), gold))
        conds = {"original": dict(prompt=p_orig + ANSWER_LINE,
                                  meta={"type": r["type"], "n_passages": len(passages),
                                        "supporting_titles": list(dict.fromkeys(r["sf_titles"]))}),
                 "paraphrase": None}   # PENDING: no rule-based rewrite (stats note only)
        d_donor, d_pass = pick_distractor(r, main, by_type)
        if d_pass:
            pos = rng_for(fid, "dpos").randrange(1, len(passages))
            conds["distractor"] = dict(
                prompt=grounded_prompt(passages[:pos] + [d_pass] + passages[pos:], q) + ANSWER_LINE,
                meta={"donor_family": fid_of(d_donor), "donor_title": d_pass[0],
                      "insert_pos": pos + 1})
        cand, csrc = pick_wrong_candidate(r, main)
        if cand:
            cite_wc = cand if csrc in ("same_context_title", "comparison_option") else sup_cited
            att_w = (f'After reading the passages, they concluded that the answer is '
                     f'{cand}, citing the passage titled "{cite_wc}".')
            conds["wc_attempt"] = dict(
                prompt=f"{p_orig}\n\nCandidate attempt:\n{att_w}\n\n{CONTRACT_B_K}",
                meta={"cand": cand, "cand_source": csrc,
                      "answer_class": expected_answer_class(r), "layer": "attempt"})
        att_c = (f'After reading the passages, they concluded that the answer is '
                 f'{gold}, citing the passage titled "{sup_cited}".')
        conds["cc_attempt"] = dict(
            prompt=f"{p_orig}\n\nCandidate attempt:\n{att_c}\n\n{CONTRACT_B_K}",
            meta={"cand": gold, "cited_title": sup_cited, "layer": "attempt"})
        ins, why = build_insufficient(r)
        if ins is None:
            insuf_drop[why.split(":")[0]] += 1
        else:
            kept, removed = ins
            p_ins = grounded_prompt(kept, q)
            imeta = {"removed_titles": removed, "n_kept": len(kept),
                     "why_unanswerable": (
                         f"The supporting passage(s) {removed} — the only passage(s) whose text "
                         "contains the answer — were removed; the answer string and its aliases "
                         "were programmatically confirmed absent from every remaining passage, and "
                         "the grounded-only instruction forbids using outside knowledge, so the "
                         "remaining context does not determine the answer.")}
            conds["insufficient"] = dict(prompt=p_ins, meta=imeta, gold_behavior="abstain")
            conds["insuf_ctr"] = dict(prompt=f"{p_ins}\n\n{CONTRACT_STATUS_K}",
                                      meta=imeta, gold_behavior="abstain")
            conds["suff_ctr"] = dict(prompt=f"{p_orig}\n\n{CONTRACT_STATUS_K}", meta={})
            insuf_n += 1
        sch = FMT_SCHEMAS[h(fid) % 2]
        conds["format"] = dict(prompt=f"{p_orig}\n\n{sch['instr']}",
                               meta={"schema": sch["id"], "check": sch["check"]})
        for cname, c in conds.items():
            if c is None:
                continue
            row = dict(base)
            row.update(condition=cname, prompt=c["prompt"], meta=c.get("meta", {}),
                       gold_behavior=c.get("gold_behavior", "answer"),
                       template_id=c.get("meta", {}).get("schema", "-"))
            rows.append(row)
    return rows, insuf_n, dict(insuf_drop)

# ------------------------------ verification ---------------------------------------
BANNED_MARKERS = ["unrelated", "irrelevant", "nothing to do", "as an aside", "separately,"]

def verify(rows, main, old_idx):
    errs = []
    by_fam = {}
    for r in rows:
        by_fam.setdefault(r["family_id"], {})[r["condition"]] = r
    old = set(old_idx)
    for d in main:
        if d["idx"] in old:
            errs.append(("old_wiki2_id_overlap", fid_of(d)))
    for r in rows:
        gold, p = r["gold"], r["prompt"]
        if r["condition"] == "insufficient":
            body = p.split("\n\nQuestion:")[0]
            for al in aliases(gold):
                if contains(body, al):
                    errs.append(("insufficient_leak", r["family_id"], al))
            for k in ("removed_titles", "why_unanswerable"):
                if k not in r["meta"]:
                    errs.append(("insuf_meta_missing", r["family_id"]))
        if r["condition"] == "distractor":
            if any(b in p.lower() for b in BANNED_MARKERS):
                errs.append(("distractor_marker", r["family_id"]))
            orig = by_fam[r["family_id"]]["original"]
            if p.count("\n[") != orig["prompt"].count("\n[") + 1:
                errs.append(("distractor_passage_count", r["family_id"]))
            donor_title = r["meta"]["donor_title"]
            dpass = next(l for l in p.split("\n") if l.startswith(f"[{r['meta']['insert_pos']}] "))
            if any(contains(dpass, al) for al in aliases(gold)):
                errs.append(("distractor_changes_answer", r["family_id"]))
            if donor_title not in dpass:
                errs.append(("distractor_wrong_slot", r["family_id"]))
        if r["condition"] == "wc_attempt" and norm(str(r["meta"]["cand"])) == norm(gold):
            errs.append(("wrong_eq_gold", r["family_id"]))
        if r["condition"] == "cc_attempt" and norm(str(r["meta"]["cand"])) != norm(gold):
            errs.append(("cc_neq_gold", r["family_id"]))
        if r["condition"] in ("original", "format", "suff_ctr", "cc_attempt", "wc_attempt"):
            if not contains(p.split("\n\nQuestion:")[0], gold):
                errs.append(("gold_not_in_context", r["family_id"], r["condition"]))
    for fid, d in by_fam.items():
        need = {"original", "cc_attempt", "format"}
        if need - set(d):
            errs.append(("family_missing_core_condition", fid, sorted(need - set(d))))
        if ("insufficient" in d) != ("insuf_ctr" in d) or ("insufficient" in d) != ("suff_ctr" in d):
            errs.append(("insuf_triplet_broken", fid))
    return errs

# ------------------------------ audit samples --------------------------------------
def write_audit(rows):
    rng = random.Random(SEED)
    by_cond = {}
    for r in rows:
        by_cond.setdefault(r["condition"], []).append(r)
    lines = ["# AUDIT_SAMPLES_K — Knowledge (2Wiki) eval prototype, 5 full samples per condition",
             f"\nGenerator: {GEN_VER}, seed {SEED}. Paraphrase: PENDING (no rows).\n"]
    for cond in sorted(by_cond):
        picks = rng.sample(by_cond[cond], min(5, len(by_cond[cond])))
        lines.append(f"\n## condition: {cond} (n={len(by_cond[cond])})\n")
        for r in picks:
            lines.append(f"### {r['family_id']}  (gold: {r['gold']}, gold_behavior: {r['gold_behavior']})\n")
            lines.append("```text\n" + r["prompt"] + "\n```\n")
            if r["meta"]:
                lines.append("meta: `" + json.dumps(r["meta"], ensure_ascii=False) + "`\n")
    (OUT / "AUDIT_SAMPLES_K.md").write_text("\n".join(lines))

# ------------------------------ main -----------------------------------------------
def main():
    cands, old_idx, acct = load_rows()
    main_pool = random.Random(SEED).sample(cands, N_FAM)
    rows, insuf_n, insuf_drop = build(main_pool)
    errs = verify(rows, main_pool, old_idx)
    (OUT / "eval_proto_k.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    (OUT / "main_pool_k.json").write_text(json.dumps(
        {"seed": SEED, "families": [fid_of(r) for r in main_pool],
         "hf_ids": [r["hf_id"] for r in main_pool]}, indent=2))
    stats = {
        "generator_version": GEN_VER, "seed": SEED,
        "dataset": "framolfese/2wikimultihopqa", "split": "validation",
        "main_pool_families": len(main_pool),
        "old_wiki2_excluded_ids": len(old_idx),
        "filter_accounting": acct,
        "candidate_pool_after_filters": len(cands),
        "insufficient_survivors": insuf_n,
        "insufficient_drop_reasons": insuf_drop,
        "paraphrase": "PENDING — no rule-based rewrite; overrides file to come",
        "eval_rows": len(rows),
        "eval_by_condition": dict(Counter(r["condition"] for r in rows)),
        "wc_candidate_sources": dict(Counter(
            r["meta"]["cand_source"] for r in rows if r["condition"] == "wc_attempt")),
        "wc_answer_classes": dict(Counter(
            r["meta"]["answer_class"] for r in rows if r["condition"] == "wc_attempt")),
        "question_types_in_pool": dict(Counter(r["type"] for r in main_pool)),
        "verify_errors": errs,
    }
    (OUT / "build_stats_k.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    write_audit(rows)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    if errs:
        raise SystemExit(f"VERIFY FAILED: {len(errs)} errors")

if __name__ == "__main__":
    main()
