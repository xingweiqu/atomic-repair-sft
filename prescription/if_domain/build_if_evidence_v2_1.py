#!/usr/bin/env python3
"""if_evidence v2.1 PROTO builder — C-31 line 2 (fix before expansion; 2026-08-10).

Supersedes if_evidence_v2_proto.jsonl (seed 20260818, kept on disk as archive).
Pool: if_evidence_v2.1_proto.jsonl, n=240, SQuAD v2 train answerable subset,
construct: answer FROM in-context evidence under interference (evidence always
present). Three subtype groups per the C-30 orange fixes as concretized by C-31:

  1. wrong_span -> PAIRED (C-31 ①): each family emits BOTH
       suggestion_correct  (suggestion = gold; target confirms it and cites the
                            evidence sentence)
       suggestion_wrong    (suggestion = plausible wrong span from the same
                            paragraph; target refutes against the evidence, v2
                            behavior)
     The suggestion prompt template is IDENTICAL for both sides — the wording
     carries no truth cue; only the suggested span differs (asserted).
     60 families x 2 = 120 rows.
  2. note (was conflicting_statement, C-31 ②): fixed "Unverified note appended
     by a reader:" label REMOVED -> neutral "Note:"; three note classes, one per
     family, 1/3 each (20/20/20 = 60 rows):
       note_correct     — note = the evidence sentence itself (agrees with passage)
       note_irrelevant  — note = an off-topic sentence from a different-title
                          paragraph (<=1 content-word overlap with the question,
                          gold absent)
       note_conflicting — note = evidence sentence with gold replaced by a
                          plausible wrong span; the substituted sentence must pass
                          a LANGUAGE QUALITY GATE: entity-type match (digit-ness +
                          capitalization of the replacement matches gold), no
                          garbage (printable ASCII, no braces/backslash/markup),
                          word-length difference vs the original sentence <= 3;
                          families failing the gate are DISCARDED (counted).
     Prompt template identical across the three classes (no class cue in wording).
  3. distractor_passage — unchanged v2 behavior (C-31 ③). 60 rows.

Auto-verification (hard asserts): counts; pairing integrity (wrong_span families
have exactly both sides, prompts differ ONLY in the suggested span); gold/evidence
containment chain (gold in ev, ev in ctx, ev quoted in target); suggestion sides
carry no extra wording cue; note class balance; conflicting-note quality gate
re-checked; distractor passage free of gold; cross-pool context disjointness
(answerability formal pool + other C-31 manifests); naturalset isolation;
family-level non-skeleton 8-gram dup rate.

Deterministic: SEED=20260819. STATUS: proto (n=240) — expansion to 2000 only
after this fix pack is approved (C-31: 修完才能扩).
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
GEN_VER = "ifv2.1-v1.0"

N_PAIR_FAMS = 60                 # wrong_span paired families -> 120 rows
N_NOTE = {"note_correct": 20, "note_irrelevant": 20, "note_conflicting": 20}
N_DISTRACTOR = 60

# ---- genre templates (suggestion prompt identical to v2's EV2; note prompt neutral)
SUG_PROMPT = v2.EV2_PROMPT       # "Someone believes the answer is "{wrong}". Check that suggestion ..."
SUG_WRONG_TGT = v2.EV2_TGT
SUG_CORRECT_TGT = ("The suggestion checks out: the passage states: \"{ev}\" "
                   "So the answer is indeed {gold}.")

NOTE_PROMPT = ("Passage:\n{ctx}\n\nNote: {note}\n\nQuestion: {q}\n\n"
               "Answer the question based on the passage evidence, with a brief "
               "justification.")
NOTE_TGT = {
    "note_correct": ("The note agrees with the passage, which states: \"{ev}\" "
                     "So the answer is {gold}."),
    "note_irrelevant": ("The note does not bear on this question. The passage "
                        "states: \"{ev}\" So the answer is {gold}."),
    "note_conflicting": ("The note conflicts with the passage, which states: \"{ev}\" "
                         "The passage evidence governs, so the answer is {gold}."),
}
EV1_PROMPT, EV1_TGT = v2.EV1_PROMPT, v2.EV1_TGT

SKELETON = [SUG_PROMPT, SUG_WRONG_TGT, SUG_CORRECT_TGT, NOTE_PROMPT,
            *NOTE_TGT.values(), EV1_PROMPT, EV1_TGT]

STOP = v2.STOP


def content_words(s):
    return {w for w in re.findall(r"[a-z0-9']+", s.lower())
            if w not in STOP and len(w) > 2}


def cap_type(s: str) -> bool:
    for c in s:
        if c.isalpha():
            return c.isupper()
    return False


def note_quality_gate(ev: str, note: str, gold: str, wrong: str):
    """C-31 ② language quality check for the substituted (conflicting) sentence.
    Returns (ok, reason)."""
    if v2.has_digit(wrong) != v2.has_digit(gold):
        return False, "entity_type_digit_mismatch"
    if cap_type(wrong) != cap_type(gold):
        return False, "entity_type_cap_mismatch"
    if not L.PRINTABLE.match(note) or any(c in note for c in "{}\\|<>"):
        return False, "garbage_chars"
    if abs(len(note.split()) - len(ev.split())) > 3:
        return False, "length_diff_gt3"
    if note == ev or gold in note or wrong not in note:
        return False, "substitution_failed"
    return True, ""


def pick_irrelevant_note(v_ctx, by_ctx, by_title, question, gold, exclude_ctx):
    """A clean off-topic sentence from a DIFFERENT-title paragraph: <=1
    content-word overlap with the question, gold absent, printable, 8..40 words.
    Returns (sentence, donor_key) or (None, None)."""
    qw = content_words(question)
    for title in sorted(by_title):
        if title == v_ctx["title"]:
            continue
        for dk in by_title[title]:
            if dk in exclude_ctx:
                continue
            dctx = by_ctx[dk]["ctx"]
            for s, e in v2.sentence_spans(dctx):
                sent = L.norm(dctx[s:e])
                if not (8 <= len(sent.split()) <= 40) or len(sent) > v2.EVSENT_MAX:
                    continue
                if not L.PRINTABLE.match(sent) or any(c in sent for c in "{}\\|<>"):
                    continue
                if gold.lower() in sent.lower():
                    continue
                if len(qw & content_words(sent)) > 1:
                    continue
                return sent, dk
    return None, None


def build(by_ctx, by_title, exclude_ctx):
    keys = [k for k, v in by_ctx.items()
            if k not in exclude_ctx and v["ans"]
            and v2.CTX_MIN <= len(v["ctx"]) <= v2.CTX_MAX]
    random.Random(SEED).shuffle(keys)
    coin = random.Random(SEED + 1)
    irr_rng = random.Random(SEED + 2)

    quota = {"pair": N_PAIR_FAMS, "distractor_passage": N_DISTRACTOR, **N_NOTE}
    note_gate_fail = Counter()
    rows, used = [], set()

    # pre-shuffled donor titles for irrelevant notes come from the same key stream
    for k in keys:
        if not any(quota.values()):
            break
        if k in used:
            continue
        v = by_ctx[k]
        ctx = L.norm(v["ctx"])
        cand = None
        for a in sorted(v["ans"], key=lambda x: x["id"]):
            if (len(a["gold"].split()) <= v2.EVD_GOLD_MAX_TOKENS and a["gold"] in ctx
                    and v2.evidence_sentence(v["ctx"], a["start"], a["gold"])):
                cand = a
                break
        if cand is None:
            continue
        ev = v2.evidence_sentence(v["ctx"], cand["start"], cand["gold"])
        if ev not in ctx:
            continue
        wrong = v2.pick_wrong(cand, v["ans"], ctx)
        wrong_sug = wrong if wrong and wrong.lower() not in cand["q"].lower() else None
        wrong_note = wrong if wrong and wrong.lower() not in ev.lower() else None

        donor = None
        for dk in by_title[v["title"]]:
            dv = by_ctx[dk]
            if (dk != k and dk not in used and dk not in exclude_ctx
                    and v2.CTX_MIN <= len(dv["ctx"]) <= v2.CTX_MAX
                    and cand["gold"].lower() not in L.norm(dv["ctx"]).lower()):
                donor = dk
                break

        # capability flags per subtype group
        can = {}
        can["pair"] = bool(wrong_sug)
        can["distractor_passage"] = bool(donor)
        can["note_correct"] = True
        can["note_conflicting"] = False
        note = None
        if wrong_note:
            note = ev.replace(cand["gold"], wrong_note, 1)
            ok, reason = note_quality_gate(ev, note, cand["gold"], wrong_note)
            if ok:
                can["note_conflicting"] = True
            else:
                note_gate_fail[reason] += 1
        # irrelevant note found lazily only if needed (expensive scan)
        able = [(quota[s], s) for s in
                ("pair", "distractor_passage", "note_conflicting", "note_correct")
                if can[s] and quota[s] > 0]
        if quota["note_irrelevant"] > 0 and not able:
            pass  # fall through to irrelevant attempt below
        able.sort(key=lambda x: (-x[0], x[1]))
        sub = able[0][1] if able else "note_irrelevant"
        if sub == "note_irrelevant" and quota["note_irrelevant"] <= 0:
            continue

        common = dict(family_id=f"squadv2_ctx_{k}", source_id=cand["id"],
                      source_split="train", generator_id="A",
                      generator_version=GEN_VER,
                      component="evidence_robustness", domain="general_if")
        meta = {"title": v["title"], "context_hash": k, "question": cand["q"],
                "gold": cand["gold"], "evidence_sentence": ev}

        if sub == "pair":
            rows.append(dict(common, subtype="suggestion_wrong",
                             prompt=SUG_PROMPT.format(ctx=ctx, q=cand["q"], wrong=wrong_sug),
                             target=SUG_WRONG_TGT.format(wrong=wrong_sug, ev=ev, gold=cand["gold"]),
                             meta=dict(meta, suggestion=wrong_sug, suggestion_is_gold=False)))
            rows.append(dict(common, subtype="suggestion_correct",
                             prompt=SUG_PROMPT.format(ctx=ctx, q=cand["q"], wrong=cand["gold"]),
                             target=SUG_CORRECT_TGT.format(ev=ev, gold=cand["gold"]),
                             meta=dict(meta, suggestion=cand["gold"], suggestion_is_gold=True)))
        elif sub == "distractor_passage":
            dctx = L.norm(by_ctx[donor]["ctx"])
            k_ev = coin.choice([1, 2])
            p1, p2 = (ctx, dctx) if k_ev == 1 else (dctx, ctx)
            rows.append(dict(common, subtype=sub,
                             prompt=EV1_PROMPT.format(p1=p1, p2=p2, q=cand["q"]),
                             target=EV1_TGT.format(k=k_ev, ev=ev, gold=cand["gold"]),
                             meta=dict(meta, donor_context_hash=donor, evidence_passage=k_ev)))
            used.add(donor)
        elif sub == "note_conflicting":
            rows.append(dict(common, subtype=sub,
                             prompt=NOTE_PROMPT.format(ctx=ctx, note=note, q=cand["q"]),
                             target=NOTE_TGT[sub].format(ev=ev, gold=cand["gold"]),
                             meta=dict(meta, note=note, note_class="conflicting",
                                       wrong_span=wrong_note)))
        elif sub == "note_correct":
            rows.append(dict(common, subtype=sub,
                             prompt=NOTE_PROMPT.format(ctx=ctx, note=ev, q=cand["q"]),
                             target=NOTE_TGT[sub].format(ev=ev, gold=cand["gold"]),
                             meta=dict(meta, note=ev, note_class="correct")))
        else:  # note_irrelevant
            titles = sorted(by_title)
            irr_rng.shuffle(titles)
            by_title_shuffled = {t: by_title[t] for t in titles}
            sent, dk = pick_irrelevant_note(v, by_ctx, by_title_shuffled,
                                            cand["q"], cand["gold"],
                                            exclude_ctx | used | {k})
            if sent is None:
                continue
            rows.append(dict(common, subtype=sub,
                             prompt=NOTE_PROMPT.format(ctx=ctx, note=sent, q=cand["q"]),
                             target=NOTE_TGT[sub].format(ev=ev, gold=cand["gold"]),
                             meta=dict(meta, note=sent, note_class="irrelevant",
                                       note_donor_context_hash=dk)))
            used.add(dk)
        quota["pair" if sub == "pair" else sub] -= 1
        used.add(k)
    assert not any(quota.values()), f"unfilled quota: {quota}"
    return rows, used, dict(note_gate_fail)


def verify(rows, by_ctx, ns_txt, ns_ids, other_sq):
    errs = []
    want_n = 2 * N_PAIR_FAMS + sum(N_NOTE.values()) + N_DISTRACTOR
    if len(rows) != want_n:
        errs.append(("bad_n", len(rows)))
    sc = Counter(r["subtype"] for r in rows)
    want_sc = {"suggestion_wrong": N_PAIR_FAMS, "suggestion_correct": N_PAIR_FAMS,
               "distractor_passage": N_DISTRACTOR, **N_NOTE}
    if dict(sc) != want_sc:
        errs.append(("bad_subtype_counts", dict(sc)))
    if len({r["prompt"] for r in rows}) != len(rows):
        errs.append(("dup_prompt",))
    # family structure: paired families = both suggestion sides; others singleton
    fam = {}
    for r in rows:
        fam.setdefault(r["family_id"], []).append(r)
    for fid, rs in fam.items():
        subs = sorted(r["subtype"] for r in rs)
        if len(rs) == 2:
            if subs != ["suggestion_correct", "suggestion_wrong"]:
                errs.append(("broken_pair", fid, subs))
                continue
            rw = next(r for r in rs if r["subtype"] == "suggestion_wrong")
            rc = next(r for r in rs if r["subtype"] == "suggestion_correct")
            # both prompts must be exact instances of ONE template, differing only
            # in the suggested span (no wording cue)
            ctx_p = L.norm(by_ctx[rw["meta"]["context_hash"]]["ctx"])
            for r_side in (rw, rc):
                if r_side["prompt"] != SUG_PROMPT.format(
                        ctx=ctx_p, q=r_side["meta"]["question"],
                        wrong=r_side["meta"]["suggestion"]):
                    errs.append(("suggestion_prompt_wording_cue", fid, r_side["subtype"]))
            if rw["meta"]["suggestion"].lower() == rw["meta"]["gold"].lower():
                errs.append(("wrong_suggestion_equals_gold", fid))
            if rc["meta"]["suggestion"] != rc["meta"]["gold"]:
                errs.append(("correct_suggestion_not_gold", fid))
            if rw["source_id"] != rc["source_id"]:
                errs.append(("pair_question_mismatch", fid))
        elif len(rs) != 1 or subs[0] in ("suggestion_wrong", "suggestion_correct"):
            errs.append(("bad_family_size", fid, subs))
    # note prompts share one template across classes (neutral "Note:" label)
    for r in rows:
        if r["subtype"].startswith("note_"):
            if "Unverified" in r["prompt"]:
                errs.append(("unverified_label_still_present", r["family_id"]))
            rebuilt = NOTE_PROMPT.format(
                ctx=L.norm(by_ctx[r["meta"]["context_hash"]]["ctx"]),
                note=r["meta"]["note"], q=r["meta"]["question"])
            if r["prompt"] != rebuilt:
                errs.append(("note_prompt_template_broken", r["family_id"]))
    # per-row evidence chain + subtype-specific checks
    for r in rows:
        for k in ("family_id", "component", "subtype", "prompt", "target",
                  "source_id", "source_split", "generator_id", "domain"):
            if not r.get(k):
                errs.append(("missing_field", k, r.get("family_id")))
        if L.norm(r["prompt"]) in ns_txt or r["source_id"] in ns_ids:
            errs.append(("naturalset_leak", r["family_id"]))
        ctx = L.norm(by_ctx[r["meta"]["context_hash"]]["ctx"])
        gold, ev, t = r["meta"]["gold"], r["meta"]["evidence_sentence"], r["target"]
        if gold not in ev or ev not in ctx or ev not in t or gold not in t:
            errs.append(("evidence_chain_broken", r["family_id"]))
        sub = r["subtype"]
        if sub == "distractor_passage":
            dctx = L.norm(by_ctx[r["meta"]["donor_context_hash"]]["ctx"])
            if dctx not in r["prompt"] or ctx not in r["prompt"]:
                errs.append(("passage_missing_in_prompt", r["family_id"]))
            if gold.lower() in dctx.lower():
                errs.append(("gold_in_distractor", r["family_id"]))
            if f"Passage [{r['meta']['evidence_passage']}]" not in t:
                errs.append(("wrong_passage_named", r["family_id"]))
        elif sub == "suggestion_wrong":
            w = r["meta"]["suggestion"]
            if w not in ctx:
                errs.append(("wrong_span_not_plausible", r["family_id"]))
            if w.lower() in gold.lower() or gold.lower() in w.lower():
                errs.append(("wrong_span_gold_substring", r["family_id"]))
            if w.lower() in r["meta"]["question"].lower():
                errs.append(("wrong_span_in_question", r["family_id"]))
        elif sub == "note_conflicting":
            note, w = r["meta"]["note"], r["meta"]["wrong_span"]
            ok, reason = note_quality_gate(ev, note, gold, w)
            if not ok:
                errs.append(("note_quality_gate_failed", r["family_id"], reason))
            if note not in r["prompt"]:
                errs.append(("note_missing_in_prompt", r["family_id"]))
        elif sub == "note_correct":
            if r["meta"]["note"] != ev:
                errs.append(("correct_note_not_evidence", r["family_id"]))
        elif sub == "note_irrelevant":
            sent = r["meta"]["note"]
            if gold.lower() in sent.lower():
                errs.append(("gold_in_irrelevant_note", r["family_id"]))
            if len(content_words(r["meta"]["question"]) & content_words(sent)) > 1:
                errs.append(("irrelevant_note_overlaps_question", r["family_id"]))
    # cross-pool context disjointness (incl. note/distractor donors)
    own = {r["meta"]["context_hash"] for r in rows}
    own |= {r["meta"]["donor_context_hash"] for r in rows if "donor_context_hash" in r["meta"]}
    own |= {r["meta"]["note_donor_context_hash"] for r in rows if "note_donor_context_hash" in r["meta"]}
    if own & other_sq:
        errs.append(("cross_pool_context_collision", len(own & other_sq)))
    return errs, own


def main():
    squad_rows, parquet_path = L.load_squad()
    ns_txt, ns_ids = L.load_ns()
    by_ctx, by_title = L.index_squad(squad_rows)

    other_sq, _, _ = L.other_pool_registries("if_evidence_v2_1")
    # also exclude the v2 ANSWERABILITY proto contexts (merged into pool 1;
    # old v2 EVIDENCE proto contexts may be reused — that file is superseded)
    _, v2_ans_ctx = L.v2_proto_registry()
    exclude = other_sq | v2_ans_ctx

    rows, used, gate_fail = build(by_ctx, by_title, exclude)
    errs, own_ctx = verify(rows, by_ctx, ns_txt, ns_ids, other_sq)
    assert not errs, errs[:20]

    dup_rate = L.family_dup_rate(rows, L.make_content_grams(SKELETON))
    manifest = {
        "pool": "if_evidence_v2_1", "status": "PROTO v2.1 (C-31 fix pack; expansion gated on approval)",
        "seed": SEED, "generator_version": GEN_VER, "instruction": "C-31 line 2 (C-30 #5 fixes)",
        "supersedes": "if_evidence_v2_proto.jsonl (seed 20260818; kept as archive)",
        "source": {"dataset": "rajpurkar/squad_v2", "split": "train",
                   "parquet": Path(parquet_path).name, "license": "CC BY-SA 4.0"},
        "fixes": {
            "wrong_span_paired": "suggestion_correct/suggestion_wrong per family, identical prompt wording",
            "note_three_classes": "correct/irrelevant/conflicting 20/20/20, neutral 'Note:' label",
            "conflicting_quality_gate": "entity-type match (digit+cap) / printable-no-markup / length diff <=3 words",
            "note_gate_discarded_families": gate_fail,
            "distractor_passage": "unchanged v2 behavior"},
        "verify_errors": [], "nonskeleton_8gram_dup_rate_family": dup_rate,
        "isolation_note": (
            "Context hashes below (incl. distractor + irrelevant-note donors) are "
            "consumed for training protos; future SQuAD-based IF evals must exclude "
            "them. Disjoint from if_answerability_pool / if_format_pool / "
            "if_clean_replay_pool and from the v2 answerability proto contexts."),
        "registry": {
            "context_hashes": sorted(own_ctx),
            "squad_question_ids": sorted({r["source_id"] for r in rows}),
            "squad_titles": sorted({r["meta"]["title"] for r in rows}),
        },
    }
    L.write_pool("if_evidence_v2_1", rows, manifest)
    L.write_sample("if_evidence_v2.1", rows, 2, 12)

    print(json.dumps({k: manifest[k] for k in
                      ("n", "sha256_16", "by_subtype", "n_families",
                       "nonskeleton_8gram_dup_rate_family")}, indent=2))
    print("note_gate_discarded:", gate_fail)
    print("verify_errors: []")


if __name__ == "__main__":
    main()
