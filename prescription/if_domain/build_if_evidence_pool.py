#!/usr/bin/env python3
"""if_evidence FORMAL pool builder — C-31 line 2 expansion (2026-08-12).

Pool: if_evidence_pool.jsonl, n=2000, component=evidence_robustness, SQuAD v2
train ANSWERABLE subset. Expansion of the approved v2.1 fix pack: every v2.1
mechanism is carried over UNCHANGED (this build imports the v2.1 templates,
quality gate and selection logic from build_if_evidence_v2_1.py rather than
re-implementing them):

  * wrong_span PAIRED (C-31 ①): suggestion_correct / suggestion_wrong per
    family, prompt template IDENTICAL on both sides (no truth cue in wording;
    asserted per family). 500 families x 2 = 1000 rows.
  * note three classes (C-31 ②): neutral "Note:" label, one class per family,
    balanced note_correct 167 / note_irrelevant 167 / note_conflicting 166;
    conflicting notes must pass the v2.1 LANGUAGE QUALITY GATE (entity-type
    digit+capitalization match / printable-no-markup / word-length diff <= 3);
    families failing the gate are DISCARDED and accounted in the manifest.
  * distractor_passage: unchanged v2 behavior. 500 rows.

Composition keeps the exact v2.1 ratio (2:1:1 = pairs : notes : distractor).
The 240 v2.1 proto rows (seed 20260819) are MERGED IN VERBATIM (same pattern as
the approved if_answerability_pool merge): identical family_id/prompt/target/
source_id, only meta.origin added. New families (seed 20260821) fill the rest:
440 pair families, notes 147/147/146, distractor 440.

Isolation (hard-asserted):
  * NEW-row contexts (incl. distractor + irrelevant-note donors) exclude every
    SQuAD context registered by if_answerability_pool / if_format_pool /
    if_clean_replay_pool / the v2.1 proto / BOTH seed-20260818 v2 protos
    (old evidence proto donors included) — i.e. zero context intersection with
    every existing IF pool; aux pools (premise_validity / suggestion_pressure /
    revision proto) carry no SQuAD contexts (asserted trivially via manifests).
  * naturalset calibration set: normalized-text AND source_id disjoint.
  * merged proto contexts are exactly the v2.1 registry (asserted), so the
    pool registry is a superset of if_evidence_v2_1's; both remain excluded
    from all future IF eval construction.

Auto-verification: counts / pairing integrity / template-identity / evidence
chain (gold in ev in ctx in target) / per-subtype checks / note gate re-check /
proto rows verbatim / no dup prompts / family-level non-skeleton 8-gram dup
rate / if_scorer.py gold-target self-regression 2000/2000 (in-build assert).

Reject accounting (manifest): note-gate discards by reason + context-level
skip reasons for the new-row scan.

Deterministic: SEED=20260821 (new rows; proto rows keep their seed-20260819
content byte-identically).
"""
import json
import random
from collections import Counter
from pathlib import Path

import if_build_lib as L
import build_if_v2 as v2
import build_if_evidence_v2_1 as V21
import if_scorer

OUT = L.OUT
SEED = 20260821
GEN_VER = "ifpool-v1.0"

# totals (v2.1 ratio 2:1:1 kept)
T_PAIR_FAMS = 500                # -> 1000 rows
T_NOTE = {"note_correct": 167, "note_irrelevant": 167, "note_conflicting": 166}
T_DISTRACTOR = 500

SUG_PROMPT = V21.SUG_PROMPT
SUG_WRONG_TGT = V21.SUG_WRONG_TGT
SUG_CORRECT_TGT = V21.SUG_CORRECT_TGT
NOTE_PROMPT = V21.NOTE_PROMPT
NOTE_TGT = V21.NOTE_TGT
EV1_PROMPT, EV1_TGT = V21.EV1_PROMPT, V21.EV1_TGT
SKELETON = V21.SKELETON


def load_proto_rows():
    p = OUT / "if_evidence_v2.1_proto.jsonl"
    rows = [json.loads(l) for l in p.open()]
    assert len(rows) == 240, len(rows)
    for r in rows:
        r["meta"]["origin"] = "v2_1_proto_seed20260819"
    return rows


def build_new(by_ctx, by_title, exclude_ctx, quota):
    """Same selection algorithm as build_if_evidence_v2_1.build, own SEED and
    quotas, plus context-level reject accounting."""
    keys = [k for k, v in by_ctx.items()
            if k not in exclude_ctx and v["ans"]
            and v2.CTX_MIN <= len(v["ctx"]) <= v2.CTX_MAX]
    random.Random(SEED).shuffle(keys)
    coin = random.Random(SEED + 1)
    irr_rng = random.Random(SEED + 2)

    note_gate_fail = Counter()
    skip = Counter()
    rows, used = [], set()

    for k in keys:
        if not any(quota.values()):
            break
        if k in used:
            skip["already_used_as_donor"] += 1
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
            skip["no_candidate_answer_with_evidence_sentence"] += 1
            continue
        ev = v2.evidence_sentence(v["ctx"], cand["start"], cand["gold"])
        if ev not in ctx:
            skip["evidence_sentence_broken_by_normalization"] += 1
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

        can = {}
        can["pair"] = bool(wrong_sug)
        can["distractor_passage"] = bool(donor)
        can["note_correct"] = True
        can["note_conflicting"] = False
        note = None
        if wrong_note:
            note = ev.replace(cand["gold"], wrong_note, 1)
            ok, reason = V21.note_quality_gate(ev, note, cand["gold"], wrong_note)
            if ok:
                can["note_conflicting"] = True
            else:
                note_gate_fail[reason] += 1
        able = [(quota[s], s) for s in
                ("pair", "distractor_passage", "note_conflicting", "note_correct")
                if can[s] and quota[s] > 0]
        able.sort(key=lambda x: (-x[0], x[1]))
        sub = able[0][1] if able else "note_irrelevant"
        if sub == "note_irrelevant" and quota["note_irrelevant"] <= 0:
            skip["no_needed_subtype_serviceable"] += 1
            continue

        common = dict(family_id=f"squadv2_ctx_{k}", source_id=cand["id"],
                      source_split="train", generator_id="A",
                      generator_version=GEN_VER,
                      component="evidence_robustness", domain="general_if")
        meta = {"title": v["title"], "context_hash": k, "question": cand["q"],
                "gold": cand["gold"], "evidence_sentence": ev,
                "origin": "pool_seed20260821"}

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
            sent, dk = V21.pick_irrelevant_note(v, by_ctx, by_title_shuffled,
                                                cand["q"], cand["gold"],
                                                exclude_ctx | used | {k})
            if sent is None:
                skip["no_irrelevant_note_donor"] += 1
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
    return rows, used, dict(note_gate_fail), dict(skip)


def verify(rows, proto_rows, by_ctx, ns_txt, ns_ids, other_nonproto_sq, v21_reg):
    errs = []
    want_n = 2 * T_PAIR_FAMS + sum(T_NOTE.values()) + T_DISTRACTOR
    if len(rows) != want_n:
        errs.append(("bad_n", len(rows)))
    sc = Counter(r["subtype"] for r in rows)
    want_sc = {"suggestion_wrong": T_PAIR_FAMS, "suggestion_correct": T_PAIR_FAMS,
               "distractor_passage": T_DISTRACTOR, **T_NOTE}
    if dict(sc) != want_sc:
        errs.append(("bad_subtype_counts", dict(sc)))
    if len({r["prompt"] for r in rows}) != len(rows):
        errs.append(("dup_prompt",))
    # proto rows merged verbatim, exactly once each
    by_key = {(r["family_id"], r["subtype"]): r for r in rows}
    if len(by_key) != len(rows):
        errs.append(("dup_family_subtype",))
    for pr in proto_rows:
        r = by_key.get((pr["family_id"], pr["subtype"]))
        if (r is None or r["prompt"] != pr["prompt"] or r["target"] != pr["target"]
                or r["source_id"] != pr["source_id"]):
            errs.append(("proto_row_not_merged_verbatim", pr["family_id"], pr["subtype"]))
    # family structure: pair families both suggestion sides; others singleton
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
    # note prompts: one neutral template, no legacy label
    for r in rows:
        if r["subtype"].startswith("note_"):
            if "Unverified" in r["prompt"]:
                errs.append(("unverified_label_still_present", r["family_id"]))
            rebuilt = NOTE_PROMPT.format(
                ctx=L.norm(by_ctx[r["meta"]["context_hash"]]["ctx"]),
                note=r["meta"]["note"], q=r["meta"]["question"])
            if r["prompt"] != rebuilt:
                errs.append(("note_prompt_template_broken", r["family_id"]))
    # per-row evidence chain + subtype checks + naturalset isolation
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
            ok, reason = V21.note_quality_gate(ev, note, gold, w)
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
            if len(V21.content_words(r["meta"]["question"]) & V21.content_words(sent)) > 1:
                errs.append(("irrelevant_note_overlaps_question", r["family_id"]))
    # cross-pool context disjointness
    def ctxs(rs):
        s = {r["meta"]["context_hash"] for r in rs}
        s |= {r["meta"]["donor_context_hash"] for r in rs if "donor_context_hash" in r["meta"]}
        s |= {r["meta"]["note_donor_context_hash"] for r in rs if "note_donor_context_hash" in r["meta"]}
        return s
    own = ctxs(rows)
    proto_ctx = ctxs([r for r in rows if r["meta"]["origin"] == "v2_1_proto_seed20260819"])
    new_ctx = ctxs([r for r in rows if r["meta"]["origin"] == "pool_seed20260821"])
    if proto_ctx != v21_reg:
        errs.append(("proto_contexts_not_exactly_v21_registry",
                     len(proto_ctx - v21_reg), len(v21_reg - proto_ctx)))
    if own & other_nonproto_sq:
        errs.append(("cross_pool_context_collision", len(own & other_nonproto_sq)))
    if new_ctx & v21_reg:
        errs.append(("new_rows_reuse_proto_context", len(new_ctx & v21_reg)))
    # scorer gold-target self-regression
    bad = [r["family_id"] for r in rows
           if if_scorer.score_row(r, r["target"])["correct"] is not True]
    if bad:
        errs.append(("scorer_gold_regression_failed", len(bad), bad[:5]))
    return errs, own


def main():
    squad_rows, parquet_path = L.load_squad()
    ns_txt, ns_ids = L.load_ns()
    by_ctx, by_title = L.index_squad(squad_rows)

    proto_rows = load_proto_rows()
    v21_m = json.loads((OUT / "if_evidence_v2_1_manifest.json").read_text())
    v21_reg = set(v21_m["registry"]["context_hashes"])
    # every OTHER existing IF pool's SQuAD registry (answerability/format/replay
    # + eval proto if present); v2.1's own registry handled separately (merged in)
    other_sq, other_ag, other_cr = L.other_pool_registries("if_evidence_pool")
    other_nonproto_sq = other_sq - v21_reg
    # aux/proto lines: v2 protos (seed 20260818, old evidence donors included)
    v2_all_ctx, _ = L.v2_proto_registry()
    # new rows must avoid EVERYTHING already consumed anywhere
    exclude_new = other_sq | v21_reg | v2_all_ctx

    quota = {"pair": T_PAIR_FAMS - 60, "distractor_passage": T_DISTRACTOR - 60,
             "note_correct": T_NOTE["note_correct"] - 20,
             "note_irrelevant": T_NOTE["note_irrelevant"] - 20,
             "note_conflicting": T_NOTE["note_conflicting"] - 20}
    new_rows, used_new, gate_fail, skip = build_new(by_ctx, by_title, exclude_new, quota)

    rows = proto_rows + new_rows
    order = {"suggestion_wrong": 0, "suggestion_correct": 1, "note_correct": 2,
             "note_irrelevant": 3, "note_conflicting": 4, "distractor_passage": 5}
    rows.sort(key=lambda r: (min(order[r["subtype"]], 1) if r["subtype"].startswith("sugg") else order[r["subtype"]],
                             r["meta"]["origin"] != "v2_1_proto_seed20260819",
                             r["family_id"], order[r["subtype"]]))

    errs, own_ctx = verify(rows, proto_rows, by_ctx, ns_txt, ns_ids,
                           other_nonproto_sq, v21_reg)
    assert not errs, errs[:20]

    dup_rate = L.family_dup_rate(rows, L.make_content_grams(SKELETON))
    manifest = {
        "pool": "if_evidence_pool",
        "status": "FORMAL (C-31 line 2 expansion after the approved v2.1 fix pack)",
        "seed": SEED, "generator_version": GEN_VER,
        "instruction": "C-31 line 2 (fixes shipped in v2.1; expansion to 2000)",
        "source": {"dataset": "rajpurkar/squad_v2", "split": "train",
                   "parquet": Path(parquet_path).name, "license": "CC BY-SA 4.0"},
        "composition": {
            "pair_families": T_PAIR_FAMS, "pair_rows": 2 * T_PAIR_FAMS,
            "notes": T_NOTE, "distractor_passage": T_DISTRACTOR,
            "ratio_note": "v2.1 ratio 2:1:1 (pairs:notes:distractor) kept; "
                          "note classes balanced 167/167/166",
            "merged_proto": {"file": "if_evidence_v2.1_proto.jsonl", "n_rows": 240,
                             "note": "seed-20260819 v2.1 proto rows merged verbatim "
                                     "(same pattern as if_answerability_pool); only "
                                     "meta.origin added"}},
        "c31_compliance": {
            "wrong_span_paired_same_template": "asserted per family (both sides exact "
                                               "instances of one template, no wording cue)",
            "note_three_classes_neutral_label": "correct/irrelevant/conflicting, neutral "
                                                "'Note:'; no fixed 'Unverified=false' shortcut",
            "conflicting_language_quality_gate": "v2.1 gate re-used verbatim "
                                                 "(digit+cap entity match / printable-no-markup / "
                                                 "length diff <=3); failing families discarded",
            "distractor_passage": "unchanged v2 behavior",
            "eval_note": "no eval rows here; the formal IF eval (eval_if_proto) uses "
                         "generator-B wording and does not include a leaking "
                         "'exactly-one-passage-relevant' template"},
        "reject_accounting": {
            "note_gate_discarded_families": gate_fail,
            "context_scan_skips": skip},
        "verify_errors": [], "nonskeleton_8gram_dup_rate_family": dup_rate,
        "scorer_gold_regression": f"{len(rows)}/{len(rows)}",
        "isolation_note": (
            "Context hashes below (incl. distractor + irrelevant-note donors) are "
            "consumed for TRAINING; superset of the v2.1 proto registry (merged). "
            "New-row contexts exclude every SQuAD context of if_answerability_pool / "
            "if_format_pool / if_clean_replay_pool / v2.1 proto / both seed-20260818 "
            "v2 protos. Aux pools (premise_validity/suggestion_pressure/revision) "
            "carry no SQuAD contexts. Any future SQuAD-based IF eval must exclude "
            "this registry; SQuAD dev split stays reserved for eval."),
        "registry": {
            "context_hashes": sorted(own_ctx),
            "squad_question_ids": sorted({r["source_id"] for r in rows}),
            "squad_titles": sorted({r["meta"]["title"] for r in rows}),
        },
    }
    L.write_pool("if_evidence_pool", rows, manifest)
    L.write_sample("if_evidence_pool", rows, 2, 12, seed=SEED)

    print(json.dumps({k: manifest[k] for k in
                      ("n", "sha256_16", "by_subtype", "n_families",
                       "target_length_buckets", "nonskeleton_8gram_dup_rate_family",
                       "scorer_gold_regression")}, indent=2))
    print("note_gate_discarded:", gate_fail)
    print("context_scan_skips:", skip)
    print("verify_errors: []")


if __name__ == "__main__":
    main()
