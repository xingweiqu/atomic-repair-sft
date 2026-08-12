#!/usr/bin/env python3
"""if_scorer — behavior-level scorer for the C-31 General-IF pools (2026-08-10).

Scores a model RESPONSE against a pool row (dict from one of:
if_answerability_pool.jsonl, if_evidence_v2.1_proto.jsonl, if_format_pool.jsonl,
if_clean_replay_pool.jsonl). Behavioral judgements, not string-equality on the
training target (IF_SOURCES_PROPOSAL §3 risk 3 / C-30 #9):

  answerability
    answerable          — extraction match, SQuAD-style normalization (lowercase,
                          strip articles/punctuation); exact or contained in a
                          short response; any refusal marker => wrong;
    unanswerable        — refusal/insufficiency detected (marker list), no
                          answer-like span asserted;
    struct_found        — STATUS: OK + FINAL_ANSWER norm-matches gold;
    struct_insufficient — STATUS: INSUFFICIENT + FINAL_ANSWER NULL-ish (fallback:
                          explicit refusal wording);
  evidence_robustness   — answer correct AND evidence cited (a >=8-token run of
                          the evidence sentence, or the whole sentence if
                          shorter, appears in the response);
    suggestion_wrong    — additionally the FINAL answer segment must give gold,
                          not the wrong suggestion;
    distractor_passage  — additionally the correct passage index is named;
  format                — schema-validated: A1/A2/A3 strict JSON object with the
                          exact key set (first {...} block extracted), answer ==
                          gold (normalized) / evidence_span a passage substring
                          containing the answer / label == gold; A4 exact
                          "label: X" line;
  clean_replay          — plain_squad_qa: extraction match; plain_agnews_cls:
                          category keyword match; plain_eli5_qa: NOT scorable
                          (control without verifiable gold) -> correct=None.

Eval extensions (2026-08-12, for eval_if_proto.jsonl — C-30 #9 multi-task-form
formal IF eval; every extension covered by the selftest below):
  * gold aliases       — rows may carry meta.gold_aliases (SQuAD dev multi-
                         reference answers); extraction-type checks accept any;
  * format schema set B (generator-B eval schemas, disjoint from train set A):
      B1 {"final_answer"} / B2 {"final_answer","support_quote"} /
      B3 {"category"} / B4 line `category = <label>`;
  * candidate_contract — subtype candidate_keep/candidate_revise: response must
                         carry a DECISION: KEEP|REVISE line matching
                         meta.expected_decision AND a FINAL: line whose value is
                         correct (meta.final_kind: gold -> extraction match,
                         label -> label match, free -> non-empty >=4 words);
  * reading_qa         — rq_answerable: a real attempt (no refusal marker,
                         >=10 words); rq_insufficient: refusal detected;
  * constraint         — word_limit: <= meta.word_limit words AND answer right;
                         answer_prefix: single line "ANSWER: ..." AND right;
                         uppercase: no lowercase letters AND answer right;
  * classification     — cls_plain: category keyword match (same behavior rule
                         as replay plain_agnews_cls, eval-side identity).

API: score_row(row, response) -> {"correct": bool|None, "check": str, "why": str}
CLI: python3 if_scorer.py            -> run selftest (>=20 cases, exits non-zero on failure)
     python3 if_scorer.py POOL.jsonl RESP.jsonl  -> batch score (response file:
     {"family_id":..., "source_id":..., "response":...} per line, matched by
     (family_id, source_id, subtype) when present)
"""
import json
import re
import sys

ARTICLES = {"a", "an", "the"}

REFUSAL_MARKERS = [
    "does not contain", "doesn't contain", "not contained in the passage",
    "cannot be answered", "can't be answered", "cannot answer",
    "not enough information", "insufficient information", "insufficient",
    "no information", "not provided in the passage", "not stated",
    "not mentioned", "unanswerable", "cannot determine", "cannot be determined",
    "does not say", "doesn't say", "no answer",
]
NULLISH = {"null", "n/a", "none", "nil", "-", ""}


def norm_ans(s: str) -> str:
    s = str(s).lower()
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    toks = [t for t in s.split() if t not in ARTICLES]
    return " ".join(toks)


def has_refusal(resp: str) -> bool:
    r = " ".join(resp.lower().split())
    return any(m in r for m in REFUSAL_MARKERS)


def extraction_match(resp: str, gold: str, max_len=300) -> bool:
    nr, ng = norm_ans(resp), norm_ans(gold)
    if not ng:
        return False
    if nr == ng:
        return True
    # containment counts only for short answer-like responses (not passage dumps)
    return len(resp) <= max_len and f" {ng} " in f" {nr} "


def _status_lines(resp: str):
    status = final = None
    for line in resp.splitlines():
        m = re.match(r"\s*status\s*:\s*(.+?)\s*$", line, re.I)
        if m and status is None:
            status = m.group(1).strip()
        m = re.match(r"\s*final_answer\s*:\s*(.+?)\s*$", line, re.I)
        if m and final is None:
            final = m.group(1).strip()
    return status, final


def evidence_cited(resp: str, ev: str, n=8) -> bool:
    et = re.findall(r"[a-z0-9']+", ev.lower())
    rt = re.findall(r"[a-z0-9']+", resp.lower())
    if len(et) <= n:
        return " ".join(et) in " ".join(rt)
    rgrams = {" ".join(rt[i:i + n]) for i in range(len(rt) - n + 1)}
    return any(" ".join(et[i:i + n]) in rgrams for i in range(len(et) - n + 1))


def final_answer_segment(resp: str) -> str:
    """Text after the LAST 'answer is/answer:' cue; whole response if no cue."""
    m = list(re.finditer(r"answer\s*(?:is|:)\s*", resp, re.I))
    return resp[m[-1].end():] if m else resp


def first_json_block(resp: str):
    i = resp.find("{")
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(resp)):
        if resp[j] == "{":
            depth += 1
        elif resp[j] == "}":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(resp[i:j + 1])
                except Exception:
                    return None
    return None


def _res(correct, check, why=""):
    return {"correct": correct, "check": check, "why": why}


def _golds(row, fallback):
    """Accepted gold variants: meta.gold_aliases (SQuAD dev multi-reference)
    if present, else the single fallback string."""
    al = (row.get("meta") or {}).get("gold_aliases")
    return [a for a in al if a] if al else [fallback]


def _any_match(resp, golds):
    return any(extraction_match(resp, g) for g in golds)


# ---------------------------------------------------------------- per-component scoring
def score_answerability(row, resp):
    sub, gold = row["subtype"], row["target"]
    if sub == "answerable":
        if has_refusal(resp):
            return _res(False, "answerable_extraction", "refused an answerable question")
        return _res(_any_match(resp, _golds(row, gold)), "answerable_extraction")
    if sub == "unanswerable":
        status, final = _status_lines(resp)
        if final is not None and norm_ans(final) not in {norm_ans(x) for x in NULLISH}:
            return _res(False, "refusal", "asserted a FINAL_ANSWER value")
        return _res(has_refusal(resp) or (final is not None), "refusal",
                    "" if has_refusal(resp) else "no refusal marker")
    if sub == "struct_found":
        want = gold.split("FINAL_ANSWER:")[-1].strip()
        status, final = _status_lines(resp)
        ok = (status is not None and status.upper().startswith("OK")
              and final is not None and _any_match(final, _golds(row, want)))
        return _res(ok, "struct_found")
    if sub == "struct_insufficient":
        status, final = _status_lines(resp)
        if status is not None:
            ok = (status.upper().startswith("INSUFFICIENT")
                  and (final is None or final.lower().strip(".") in NULLISH))
        else:
            ok = has_refusal(resp)
        return _res(ok, "struct_insufficient")
    raise ValueError(f"unknown answerability subtype {sub}")


def score_evidence(row, resp):
    meta = row["meta"]
    gold, ev = meta["gold"], meta["evidence_sentence"]
    ok_ans = f" {norm_ans(gold)} " in f" {norm_ans(resp)} "
    ok_ev = evidence_cited(resp, ev)
    sub = row["subtype"]
    if not ok_ans:
        return _res(False, f"{sub}", "gold answer missing")
    if not ok_ev:
        return _res(False, f"{sub}", "evidence sentence not cited")
    if sub == "suggestion_wrong":
        seg = final_answer_segment(resp)
        wrong = meta["suggestion"]
        if f" {norm_ans(gold)} " not in f" {norm_ans(seg)} ":
            return _res(False, sub, "final answer segment does not give gold")
        if (f" {norm_ans(wrong)} " in f" {norm_ans(seg)} "
                and norm_ans(wrong) != norm_ans(gold)):
            return _res(False, sub, "final answer segment still carries the wrong suggestion")
    if sub == "distractor_passage":
        k = meta["evidence_passage"]
        if f"[{k}]" not in resp:
            return _res(False, sub, "correct passage index not named")
    return _res(True, sub)


def score_format(row, resp):
    sid = row["schema_id"]
    meta = row["meta"]
    if sid in ("A1", "A2", "B1", "B2"):
        akey = "answer" if sid.startswith("A") else "final_answer"
        skey = "evidence_span" if sid == "A2" else "support_quote"
        keys = [akey] if sid in ("A1", "B1") else [akey, skey]
        obj = first_json_block(resp)
        if obj is None or not isinstance(obj, dict):
            return _res(False, f"format_{sid}", "no parsable JSON object")
        if set(obj) != set(keys):
            return _res(False, f"format_{sid}", f"key set {sorted(obj)} != {sorted(keys)}")
        if not all(isinstance(obj[k], str) for k in keys):
            return _res(False, f"format_{sid}", "non-string field")
        golds = _golds(row, meta["gold"])
        if not any(norm_ans(obj[akey]) == norm_ans(g) for g in golds):
            return _res(False, f"format_{sid}", "answer != gold")
        if sid in ("A2", "B2"):
            evs = " ".join(obj[skey].split())
            if evs not in row["prompt"]:
                return _res(False, f"format_{sid}", f"{skey} not a passage substring")
            if not any(norm_ans(g) in norm_ans(evs) for g in golds):
                return _res(False, f"format_{sid}", f"{skey} does not contain the answer")
        return _res(True, f"format_{sid}")
    if sid in ("A3", "B3"):
        lkey = "label" if sid == "A3" else "category"
        obj = first_json_block(resp)
        if obj is None or set(obj) != {lkey} or not isinstance(obj.get(lkey), str):
            return _res(False, f"format_{sid}", "bad JSON / key set")
        return _res(obj[lkey].strip() == meta["label"], f"format_{sid}")
    if sid == "A4":
        for line in resp.splitlines():
            m = re.match(r"\s*label\s*:\s*(.+?)\s*$", line, re.I)
            if m:
                return _res(m.group(1) == meta["label"], "format_A4")
        return _res(False, "format_A4", "no 'label:' line")
    if sid == "B4":
        for line in resp.splitlines():
            m = re.match(r"\s*category\s*=\s*(.+?)\s*$", line, re.I)
            if m:
                return _res(m.group(1) == meta["label"], "format_B4")
        return _res(False, "format_B4", "no 'category =' line")
    raise ValueError(f"unknown schema_id {sid}")


# ---------------------------------------------------------------- eval components (C-30 #9)
def score_candidate(row, resp):
    """candidate_keep / candidate_revise: DECISION line must match
    meta.expected_decision; FINAL line must be a correct value."""
    meta = row["meta"]
    sub = row["subtype"]
    decision = final = None
    for line in resp.splitlines():
        m = re.match(r"\s*decision\s*:\s*(keep|revise)\b", line, re.I)
        if m and decision is None:
            decision = m.group(1).upper()
        m = re.match(r"\s*final\s*:\s*(.+?)\s*$", line, re.I)
        if m and final is None:
            final = m.group(1).strip()
    if decision is None:
        return _res(False, sub, "no DECISION: KEEP|REVISE line")
    if decision != meta["expected_decision"]:
        return _res(False, sub, f"decision {decision} != {meta['expected_decision']}")
    if final is None:
        return _res(False, sub, "no FINAL: line")
    kind = meta.get("final_kind", "gold")
    if kind == "gold":
        ok = _any_match(final, _golds(row, meta["gold"]))
        return _res(ok, sub, "" if ok else "FINAL value wrong")
    if kind == "label":
        ok = extraction_match(final, meta["label"])
        return _res(ok, sub, "" if ok else "FINAL label wrong")
    # free-text final (CREPE revision): substantive response required
    ok = len(final.split()) >= 4
    return _res(ok, sub, "" if ok else "FINAL not a substantive response")


def score_reading_qa(row, resp):
    sub = row["subtype"]
    if sub == "rq_answerable":
        if has_refusal(resp):
            return _res(False, sub, "refused an answerable question")
        if len(resp.split()) < 10:
            return _res(False, sub, "too short to be an answer attempt")
        return _res(True, sub)
    if sub == "rq_insufficient":
        return _res(has_refusal(resp), sub,
                    "" if has_refusal(resp) else "no refusal marker")
    raise ValueError(f"unknown reading_qa subtype {sub}")


def score_constraint(row, resp):
    meta = row["meta"]
    sub = row["subtype"]
    golds = _golds(row, meta["gold"])
    if sub == "word_limit":
        n = len(resp.split())
        if n > meta["word_limit"]:
            return _res(False, sub, f"{n} words > limit {meta['word_limit']}")
        return _res(_any_match(resp, golds), sub)
    if sub == "answer_prefix":
        lines = [l for l in resp.strip().splitlines() if l.strip()]
        if len(lines) != 1:
            return _res(False, sub, "not a single line")
        m = re.match(r"\s*ANSWER:\s*(.+?)\s*$", lines[0])
        if not m:
            return _res(False, sub, "line does not start with 'ANSWER:'")
        return _res(_any_match(m.group(1), golds), sub)
    if sub == "uppercase":
        if any(c.islower() for c in resp):
            return _res(False, sub, "contains lowercase letters")
        return _res(_any_match(resp, golds), sub)
    raise ValueError(f"unknown constraint subtype {sub}")


def score_classification(row, resp):
    label = row["meta"]["label"]
    r = resp.lower()
    hit = any(k in r for k in AG_KEYWORDS[label])
    other = any(k in r for lb, ks in AG_KEYWORDS.items() if lb != label
                for k in ks if k not in AG_KEYWORDS[label])
    return _res(hit and not other, "cls_plain")


AG_KEYWORDS = {"World": ["world", "international"], "Sports": ["sport"],
               "Business": ["business", "financ", "econom"],
               "Sci/Tech": ["sci/tech", "science", "technology", "tech"]}


def score_replay(row, resp):
    sub = row["subtype"]
    if sub == "plain_eli5_qa":
        return _res(None, "replay_unscored", "control row without verifiable gold")
    if sub == "plain_squad_qa":
        if has_refusal(resp):
            return _res(False, "replay_extraction", "refused")
        return _res(extraction_match(resp, row["target"]), "replay_extraction")
    if sub == "plain_agnews_cls":
        label = row["meta"]["label"]
        r = resp.lower()
        hit = any(k in r for k in AG_KEYWORDS[label])
        other = any(k in r for lb, ks in AG_KEYWORDS.items() if lb != label
                    for k in ks if k not in AG_KEYWORDS[label])
        return _res(hit and not other, "replay_classification")
    raise ValueError(f"unknown replay subtype {sub}")


def score_row(row, response):
    comp = row["component"]
    if comp == "answerability":
        return score_answerability(row, response)
    if comp == "evidence_robustness":
        return score_evidence(row, response)
    if comp == "format":
        return score_format(row, response)
    if comp == "clean_replay":
        return score_replay(row, response)
    if comp == "candidate_contract":
        return score_candidate(row, response)
    if comp == "reading_qa":
        return score_reading_qa(row, response)
    if comp == "constraint":
        return score_constraint(row, response)
    if comp == "classification":
        return score_classification(row, response)
    raise ValueError(f"unknown component {comp}")


# ---------------------------------------------------------------- selftest
def _row(component, subtype, target="", meta=None, schema_id=None, prompt=""):
    r = dict(component=component, subtype=subtype, target=target,
             meta=meta or {}, prompt=prompt, family_id="selftest", source_id="selftest")
    if schema_id:
        r["schema_id"] = schema_id
    return r


def selftest():
    EV = "The bridge was completed in 1937 by the district."
    cases = [
        # -------- answerability / answerable (1-4)
        (_row("answerability", "answerable", "Golden Gate Bridge"),
         "Golden Gate Bridge", True),
        (_row("answerability", "answerable", "Golden Gate Bridge"),
         "The answer is the Golden Gate Bridge.", True),      # containment + article norm
        (_row("answerability", "answerable", "Golden Gate Bridge"),
         "The passage does not contain the information needed.", False),
        (_row("answerability", "answerable", "Golden Gate Bridge"),
         "Bay Bridge", False),
        # -------- answerability / unanswerable (5-7)
        (_row("answerability", "unanswerable"),
         "The passage does not contain the information needed to answer this question.", True),
        (_row("answerability", "unanswerable"),
         "This question cannot be answered from the passage.", True),
        (_row("answerability", "unanswerable"), "It was built in 1937.", False),
        # -------- answerability / struct (8-12)
        (_row("answerability", "struct_found", "STATUS: OK\nFINAL_ANSWER: 1937"),
         "STATUS: OK\nFINAL_ANSWER: 1937", True),
        (_row("answerability", "struct_found", "STATUS: OK\nFINAL_ANSWER: 1937"),
         "STATUS: OK\nFINAL_ANSWER: 1938", False),
        (_row("answerability", "struct_insufficient", "STATUS: INSUFFICIENT\nFINAL_ANSWER: NULL"),
         "STATUS: INSUFFICIENT\nFINAL_ANSWER: NULL", True),
        (_row("answerability", "struct_insufficient", "STATUS: INSUFFICIENT\nFINAL_ANSWER: NULL"),
         "STATUS: OK\nFINAL_ANSWER: 1937", False),
        (_row("answerability", "struct_insufficient", "STATUS: INSUFFICIENT\nFINAL_ANSWER: NULL"),
         "The passage does not contain this field, so it cannot be answered.", True),  # fallback refusal
        # -------- evidence (13-19)
        (_row("evidence_robustness", "suggestion_wrong",
              meta={"gold": "1937", "evidence_sentence": EV, "suggestion": "1938"}),
         f'The suggestion is wrong. The passage states: "{EV}" So the answer is 1937.', True),
        (_row("evidence_robustness", "suggestion_wrong",
              meta={"gold": "1937", "evidence_sentence": EV, "suggestion": "1938"}),
         f'The passage states: "{EV}" So the answer is 1938.', False),   # endorsed the wrong span
        (_row("evidence_robustness", "suggestion_wrong",
              meta={"gold": "1937", "evidence_sentence": EV, "suggestion": "1938"}),
         "The answer is 1937.", False),                                   # no evidence cited
        (_row("evidence_robustness", "suggestion_correct",
              meta={"gold": "1937", "evidence_sentence": EV, "suggestion": "1937"}),
         f'The suggestion checks out: the passage states: "{EV}" So the answer is indeed 1937.', True),
        (_row("evidence_robustness", "note_conflicting",
              meta={"gold": "1937", "evidence_sentence": EV}),
         f'The note conflicts with the passage, which states: "{EV}" The answer is 1937.', True),
        (_row("evidence_robustness", "distractor_passage",
              meta={"gold": "1937", "evidence_sentence": EV, "evidence_passage": 2}),
         f'Passage [2] answers this — it states: "{EV}" Answer: 1937', True),
        (_row("evidence_robustness", "distractor_passage",
              meta={"gold": "1937", "evidence_sentence": EV, "evidence_passage": 2}),
         f'Passage [1] answers this — it states: "{EV}" Answer: 1937', False),  # wrong passage named
        # -------- format (20-26)
        (_row("format", "extract_A1", meta={"gold": "1937"}, schema_id="A1"),
         '{"answer": "1937"}', True),
        (_row("format", "extract_A1", meta={"gold": "1937"}, schema_id="A1"),
         'The answer is {"answer": "1937"}', True),           # JSON block extraction
        (_row("format", "extract_A1", meta={"gold": "1937"}, schema_id="A1"),
         '{"answer": "1937", "extra": "x"}', False),          # key set violation
        (_row("format", "extract_A2", meta={"gold": "1937"}, schema_id="A2",
              prompt=f"Passage:\n{EV}\n\nQuestion: when?\n\nschema"),
         json.dumps({"answer": "1937", "evidence_span": EV}), True),
        (_row("format", "extract_A2", meta={"gold": "1937"}, schema_id="A2",
              prompt=f"Passage:\n{EV}\n\nQuestion: when?\n\nschema"),
         json.dumps({"answer": "1937", "evidence_span": "A sentence not in the passage."}), False),
        (_row("format", "classify_A3", meta={"label": "Sports"}, schema_id="A3"),
         '{"label": "Sports"}', True),
        (_row("format", "classify_A3", meta={"label": "Sports"}, schema_id="A3"),
         'label: Sports', False),                             # wrong schema (line for A3)
        # -------- format A4 (27-28)
        (_row("format", "classify_A4", meta={"label": "Sci/Tech"}, schema_id="A4"),
         "label: Sci/Tech", True),
        (_row("format", "classify_A4", meta={"label": "Sci/Tech"}, schema_id="A4"),
         '{"label": "Sci/Tech"}', False),                     # wrong schema (JSON for A4)
        # -------- clean replay (29-32)
        (_row("clean_replay", "plain_squad_qa", "1937"), "It was completed in 1937.", True),
        (_row("clean_replay", "plain_squad_qa", "1937"), "It was completed in 1938.", False),
        (_row("clean_replay", "plain_agnews_cls", meta={"label": "Business"}),
         "This is a business news story.", True),
        (_row("clean_replay", "plain_eli5_qa", "free text"), "anything", None),
        # -------- gold aliases (33-34)
        (_row("answerability", "answerable", "Denver Broncos",
              meta={"gold_aliases": ["Denver Broncos", "Broncos"]}),
         "The Broncos.", True),                               # alias accepted
        (_row("answerability", "answerable", "Denver Broncos",
              meta={"gold_aliases": ["Denver Broncos", "Broncos"]}),
         "The Panthers.", False),
        # -------- format schema B (35-42)
        (_row("format", "extract_B1", meta={"gold": "1937"}, schema_id="B1"),
         '{"final_answer": "1937"}', True),
        (_row("format", "extract_B1", meta={"gold": "1937"}, schema_id="B1"),
         '{"answer": "1937"}', False),                        # train-A key set rejected
        (_row("format", "extract_B2", meta={"gold": "1937"}, schema_id="B2",
              prompt=f"Context:\n{EV}\n\nQ: when?\n\nschema"),
         json.dumps({"final_answer": "1937", "support_quote": EV}), True),
        (_row("format", "extract_B2", meta={"gold": "1937"}, schema_id="B2",
              prompt=f"Context:\n{EV}\n\nQ: when?\n\nschema"),
         json.dumps({"final_answer": "1937", "support_quote": "Not in the context."}), False),
        (_row("format", "classify_B3", meta={"label": "Sports"}, schema_id="B3"),
         '{"category": "Sports"}', True),
        (_row("format", "classify_B3", meta={"label": "Sports"}, schema_id="B3"),
         '{"label": "Sports"}', False),                       # A3 key rejected under B3
        (_row("format", "classify_B4", meta={"label": "Sci/Tech"}, schema_id="B4"),
         "category = Sci/Tech", True),
        (_row("format", "classify_B4", meta={"label": "Sci/Tech"}, schema_id="B4"),
         "label: Sci/Tech", False),                           # A4 line rejected under B4
        # -------- candidate contract (43-48)
        (_row("candidate_contract", "candidate_keep",
              meta={"expected_decision": "KEEP", "final_kind": "gold", "gold": "1937"}),
         "DECISION: KEEP\nFINAL: 1937", True),
        (_row("candidate_contract", "candidate_keep",
              meta={"expected_decision": "KEEP", "final_kind": "gold", "gold": "1937"}),
         "DECISION: REVISE\nFINAL: 1937", False),             # wrong decision
        (_row("candidate_contract", "candidate_revise",
              meta={"expected_decision": "REVISE", "final_kind": "gold", "gold": "1937",
                    "gold_aliases": ["1937", "in 1937"]}),
         "DECISION: REVISE\nFINAL: in 1937", True),           # alias accepted
        (_row("candidate_contract", "candidate_revise",
              meta={"expected_decision": "REVISE", "final_kind": "gold", "gold": "1937"}),
         "DECISION: REVISE\nFINAL: 1938", False),             # right decision, wrong value
        (_row("candidate_contract", "candidate_revise",
              meta={"expected_decision": "REVISE", "final_kind": "free"}),
         "DECISION: REVISE\nFINAL: The premise is false; files are recoverable.", True),
        (_row("candidate_contract", "candidate_keep",
              meta={"expected_decision": "KEEP", "final_kind": "label", "label": "Business"}),
         "FINAL: Business", False),                           # no DECISION line
        # -------- reading QA (49-52)
        (_row("reading_qa", "rq_answerable"),
         "Deleting only removes the index entry, so the underlying data blocks stay on disk until overwritten.", True),
        (_row("reading_qa", "rq_answerable"),
         "There is no information about this in the material.", False),   # refused
        (_row("reading_qa", "rq_insufficient"),
         "The material does not contain what this asks about, so it cannot be answered.", True),
        (_row("reading_qa", "rq_insufficient"), "It happened in 1937.", False),
        # -------- constraint (53-58)
        (_row("constraint", "word_limit", meta={"gold": "1937", "word_limit": 3}),
         "In 1937.", True),
        (_row("constraint", "word_limit", meta={"gold": "1937", "word_limit": 3}),
         "The bridge was completed in the year 1937.", False),  # over the limit
        (_row("constraint", "answer_prefix", meta={"gold": "1937"}),
         "ANSWER: 1937", True),
        (_row("constraint", "answer_prefix", meta={"gold": "1937"}),
         "The answer is 1937.", False),                       # missing prefix
        (_row("constraint", "uppercase", meta={"gold": "Golden Gate Bridge"}),
         "GOLDEN GATE BRIDGE", True),
        (_row("constraint", "uppercase", meta={"gold": "Golden Gate Bridge"}),
         "Golden Gate Bridge", False),                        # lowercase present
        # -------- classification plain (59-60)
        (_row("classification", "cls_plain", meta={"label": "Sci/Tech"}),
         "This one goes under the Sci/Tech desk.", True),
        (_row("classification", "cls_plain", meta={"label": "Sports"}),
         "Business, most likely.", False),
    ]
    fails = []
    for i, (row, resp, want) in enumerate(cases, 1):
        got = score_row(row, resp)
        if got["correct"] is not want:
            fails.append((i, row["component"], row["subtype"], want, got))
    print(f"selftest: {len(cases) - len(fails)}/{len(cases)} passed")
    for f in fails:
        print("  FAIL", f)
    return not fails


def batch(pool_path, resp_path):
    rows = {}
    for l in open(pool_path):
        r = json.loads(l)
        if "_header" in r:
            continue
        rows[(r["family_id"], r["source_id"], r["subtype"])] = r
        rows.setdefault((r["family_id"], r["source_id"]), r)
    n = c = u = 0
    by_check = {}
    for l in open(resp_path):
        rr = json.loads(l)
        key = (rr["family_id"], rr["source_id"], rr["subtype"]) if "subtype" in rr \
            else (rr["family_id"], rr["source_id"])
        row = rows.get(key)
        if row is None:
            continue
        res = score_row(row, rr["response"])
        n += 1
        if res["correct"] is None:
            u += 1
        elif res["correct"]:
            c += 1
        bc = by_check.setdefault(res["check"], [0, 0])
        if res["correct"] is not None:
            bc[1] += 1
            bc[0] += int(res["correct"])
    print(json.dumps({"n": n, "correct": c, "unscored": u,
                      "acc_scored": round(c / max(1, n - u), 4),
                      "by_check": {k: {"correct": v[0], "n": v[1]}
                                   for k, v in sorted(by_check.items())}}, indent=2))


if __name__ == "__main__":
    if len(sys.argv) == 3:
        batch(sys.argv[1], sys.argv[2])
    else:
        sys.exit(0 if selftest() else 1)
