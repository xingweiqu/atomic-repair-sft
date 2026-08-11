#!/usr/bin/env python3
"""K-eval-500: formal 500-family Knowledge (2Wiki) eval builder (C-31/C-32 spec).

Extends build_knowledge_eval.py (v1 prototype, 50 families) via import. Changes
mandated by qc/INSTRUCTION_C30.md pts 7/8 and qc/INSTRUCTION_C31.md pt "K eval v1
not frozen":

  1. Main pool: 500 families from 2Wiki validation, same hard filters as v1
     (short entity answers, passages complete, answer in supporting passage, zero
     overlap with old wiki2 ids). The v1 50 families are force-included as the
     comparable subset.
  2. Distractor donor pool: 300 additional validation families, disjoint from the
     main pool, donor-only (never evaluated). Registered in main_pool_k500.json.
  3. Hard distractors replace v1's same-type random donor. Tiers (per-family
     first-hit, donors scanned in family-deterministic random order):
       same_entity   a bridge entity of the main family (supporting title or
                     evidence subject/object, not the gold answer) appears in a
                     donor supporting passage under a different relation
                     (match_kind=title: donor passage is ABOUT the entity;
                      match_kind=text: entity mentioned in donor passage text)
     The 300 donors are NOT sampled at random: donor candidates (validation
     minus main pool) are scored for same_entity coverage of main families and
     picked by greedy set cover, so the same_entity tier reaches its natural
     ceiling under the 300-donor budget; leftover slots are filled at random.
       same_relation donor family of the same 2wiki type sharing >=1 evidence
                     relation with the main family (same expected answer class
                     preferred)
       soft          same-type donor (else any donor); counted separately
     Every distractor row's meta records hardness + match details + donor family.
  4. wrong_candidate_citation donor answers ("other_family_answer" source) are
     also drawn from the donor pool, never from other main-pool families.
  5. paraphrase: still PENDING (no rule-based rewrite) -> no rows, flagged.

All other conditions/contracts are v1-identical (grounded instruction, answer
line, KEEP-REVISE contract, STATUS contract, insufficient leak check). Built-in
assertions: main∩donor=0, main∩old-wiki2=0, v1⊆main, insufficient alias leak,
cand!=gold, hardness counts reconcile, per-condition row accounting.

Outputs (same dir): eval_k500_proto.jsonl, build_stats_k500.json,
AUDIT_SAMPLES_K500.md, main_pool_k500.json. Deterministic under SEED500.
"""
import json, random, re
from collections import Counter
from pathlib import Path

import build_knowledge_eval as bke
from build_knowledge_eval import (
    h, rng_for, norm, contains, aliases, passage_text, render_context,
    grounded_prompt, answer_kind, expected_answer_class, pick_wrong_candidate,
    build_insufficient, fid_of, base_passages, load_rows, verify,
    ANSWER_LINE, CONTRACT_B_K, CONTRACT_STATUS_K, FMT_SCHEMAS)

OUT = Path(__file__).resolve().parent
GEN_VER = "k-eval-v2-500"
SEED500 = 20260810
N_MAIN, N_DONOR = 500, 300
V1_POOL_FILE = OUT / "main_pool_k.json"

# ------------------------------ relation / entity structure ------------------------
def strip_paren(t):
    return re.sub(r"\([^)]*\)", "", t).strip()

def relations(r):
    """(all relation labels, normalized-entity -> relation labels) from evidences."""
    rels, ent_rels = set(), {}
    for e in r["evidences"]:
        if len(e) < 3:
            continue
        s, rel, o = str(e[0]).strip(), str(e[1]).strip().lower(), str(e[2]).strip()
        if not rel:
            continue
        rels.add(rel)
        for x in (s, o):
            nx = norm(x)
            if nx:
                ent_rels.setdefault(nx, set()).add(rel)
    return rels, ent_rels

def bridge_entities(r):
    """Non-answer entities of the family: supporting titles + evidence subj/obj.
    Returns [(surface, normalized)] sorted longest-normalized-first (specific
    entities matched before generic ones)."""
    als = {norm(a) for a in aliases(r["answer"])}
    ents = {strip_paren(t) for t in r["sf_titles"]}
    for e in r["evidences"]:
        if len(e) >= 3:
            ents.update((str(e[0]).strip(), str(e[2]).strip()))
    out = []
    for e in ents:
        ne = norm(e)
        if len(ne) < 4 or answer_kind(e) != "entity":
            continue
        if any(ne == a or (a and (a in ne or ne in a)) for a in als):
            continue
        out.append((e, ne))
    return sorted(out, key=lambda x: -len(x[1]))

def donor_index(donors):
    """Precomputed donor structures for the hard-distractor scan."""
    idx = []
    for d in donors:
        rels, ent_rels = relations(d)
        sup = []
        for t in dict.fromkeys(d["sf_titles"]):
            ss = d["sents"][d["titles"].index(t)]
            txt = passage_text(t, ss)
            if any(b in txt.lower() for b in bke.BANNED_MARKERS):
                continue   # natural text with a marker word would trip the cue check
            sup.append((t, ss, norm(txt), norm(strip_paren(t))))
        idx.append(dict(d=d, fid=fid_of(d), rels=rels, ent_rels=ent_rels, sup=sup,
                        cls=expected_answer_class(d), n_ans=norm(d["answer"])))
    return idx

# ------------------------------ targeted donor selection ---------------------------
def main_entity_structs(main):
    """Per main family: precomputed pieces the same_entity check needs."""
    out = {}
    for r in main:
        out[fid_of(r)] = dict(
            r=r, ents=bridge_entities(r),
            n_gold=norm(r["answer"]),
            n_gold_als={norm(a) for a in aliases(r["answer"])},
            titles=set(r["titles"]), ent_rels=relations(r)[1])
    return out

def same_entity_cover(dd, ms):
    """Does donor struct dd give main-family struct ms a valid same_entity passage?
    Mirrors pick_hard_distractor tier-a checks exactly."""
    if dd["n_ans"] == ms["n_gold"]:
        return False
    for t, ss, ntxt, ntitle in dd["sup"]:
        if t in ms["titles"] or any(a and a in ntxt for a in ms["n_gold_als"]):
            continue
        for e, ne in ms["ents"]:
            if ne not in ntxt:
                continue
            d_rels = dd["ent_rels"].get(ne, set())
            m_rels = ms["ent_rels"].get(ne, set())
            if d_rels and m_rels and d_rels <= m_rels:
                continue
            return True
    return False

def select_donors(main, rest, rng):
    """Greedy set cover: pick up to N_DONOR donor families maximizing the number
    of main families that get a same_entity distractor; fill remaining slots at
    random. Returns (donor_pool, coverage_stats)."""
    mstructs = main_entity_structs(main)
    # inverted entity index: entity-norm -> [main fid]
    ent2fids = {}
    for fid, ms in mstructs.items():
        for e, ne in ms["ents"]:
            ent2fids.setdefault(ne, []).append(fid)
    all_d = donor_index(rest)
    cover = []   # (cover_set, donor_struct)
    for dd in all_d:
        hits = set()
        for t, ss, ntxt, ntitle in dd["sup"]:
            for ne, fids in ent2fids.items():
                if ne in ntxt:
                    hits.update(fids)
        cov = {fid for fid in hits if same_entity_cover(dd, mstructs[fid])}
        cover.append((cov, dd))
    coverable = set().union(*[c for c, _ in cover]) if cover else set()
    nonempty = sorted([i for i in range(len(cover)) if cover[i][0]],
                      key=lambda i: cover[i][1]["d"]["idx"])
    chosen, covered = [], set()
    while len(chosen) < N_DONOR and nonempty:
        best_i, best_gain = None, 0
        for i in nonempty:   # idx-sorted -> deterministic tie-break (first best wins)
            gain = len(cover[i][0] - covered)
            if gain > best_gain:
                best_i, best_gain = i, gain
        if best_gain == 0:
            break
        chosen.append(best_i)
        covered |= cover[best_i][0]
        nonempty.remove(best_i)
    remaining = [i for i in range(len(cover)) if i not in set(chosen)]
    fill = rng.sample(remaining, N_DONOR - len(chosen)) if len(chosen) < N_DONOR else []
    donor_pool = [cover[i][1]["d"] for i in chosen] + [cover[i][1]["d"] for i in fill]
    stats = dict(
        donor_candidates_scanned=len(rest),
        main_families_coverable_by_any_candidate=len(coverable),
        main_families_covered_by_chosen_300=len(covered),
        donors_chosen_by_cover=len(chosen),
        donors_filled_random=len(fill))
    return donor_pool, stats

# ------------------------------ hard distractor ------------------------------------
def pick_hard_distractor(r, dindex):
    """Donor-pool-only hard distractor. Tier order: same_entity (title match, then
    text match) -> same_relation (same type + shared relation; same answer class
    preferred) -> soft (same type, else any). Returns (donor_row, (title, sents),
    hard_meta) or (None, None, None)."""
    rng = rng_for(fid_of(r), "dis500")
    n_gold_als = {norm(a) for a in aliases(r["answer"])}
    n_gold = norm(r["answer"])
    main_titles = set(r["titles"])
    main_rels, main_ent_rels = relations(r)
    ents = bridge_entities(r)
    order = list(range(len(dindex)))
    rng.shuffle(order)

    def safe(dd, t, ntxt):
        return (dd["n_ans"] != n_gold and t not in main_titles
                and not any(a and a in ntxt for a in n_gold_als))

    # tier a: same_entity, different relation
    for match_kind in ("title", "text"):
        for i in order:
            dd = dindex[i]
            for t, ss, ntxt, ntitle in dd["sup"]:
                if not safe(dd, t, ntxt):
                    continue
                for e, ne in ents:
                    hit = (ne == ntitle) if match_kind == "title" else (ne in ntxt)
                    if not hit:
                        continue
                    d_rels = dd["ent_rels"].get(ne, set())
                    m_rels = main_ent_rels.get(ne, set())
                    if d_rels and m_rels and d_rels <= m_rels:
                        continue   # donor relates this entity only via the same relation(s)
                    return dd["d"], (t, ss), dict(
                        hardness="same_entity", match_kind=match_kind,
                        matched_entity=e,
                        donor_entity_relations=sorted(d_rels),
                        main_entity_relations=sorted(m_rels))
    # tier b: same type + shared relation (same expected answer class preferred)
    for want_cls in (True, False):
        for i in order:
            dd = dindex[i]
            if dd["d"]["type"] != r["type"]:
                continue
            shared = dd["rels"] & main_rels
            if not shared or (want_cls and dd["cls"] != expected_answer_class(r)):
                continue
            for t, ss, ntxt, _ in dd["sup"]:
                if safe(dd, t, ntxt):
                    return dd["d"], (t, ss), dict(
                        hardness="same_relation", shared_relations=sorted(shared),
                        same_answer_class=want_cls)
    # tier c: soft
    for same_type in (True, False):
        for i in order:
            dd = dindex[i]
            if same_type and dd["d"]["type"] != r["type"]:
                continue
            for t, ss, ntxt, _ in dd["sup"]:
                if safe(dd, t, ntxt):
                    return dd["d"], (t, ss), dict(hardness="soft", same_type=same_type)
    return None, None, None

# ------------------------------ build (v1 conditions + hard distractor) ------------
def build(main, dindex, donor_pool):
    rows, insuf_n = [], 0
    insuf_drop, hard_ct, donor_use = Counter(), Counter(), Counter()
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
        d_donor, d_pass, hard = pick_hard_distractor(r, dindex)
        if d_pass:
            pos = rng_for(fid, "dpos").randrange(1, len(passages))
            meta = {"donor_family": fid_of(d_donor), "donor_title": d_pass[0],
                    "donor_pool": "disjoint_donor_only", "insert_pos": pos + 1}
            meta.update(hard)
            conds["distractor"] = dict(
                prompt=grounded_prompt(passages[:pos] + [d_pass] + passages[pos:], q) + ANSWER_LINE,
                meta=meta)
            hard_ct[hard["hardness"]] += 1
            donor_use[fid_of(d_donor)] += 1
        cand, csrc = pick_wrong_candidate(r, donor_pool)   # donor answers from donor pool only
        if cand:
            cite_wc = cand if csrc in ("same_context_title", "comparison_option") else sup_cited
            att_w = (f'After reading the passages, they concluded that the answer is '
                     f'{cand}, citing the passage titled "{cite_wc}".')
            conds["wrong_candidate_citation"] = dict(
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
    return rows, insuf_n, dict(insuf_drop), dict(hard_ct), donor_use

# ------------------------------ k500-specific assertions ---------------------------
def verify_k500(rows, main, donor_pool, old_idx, v1_fids, hard_ct):
    errs = []
    main_ids, donor_ids = {r["idx"] for r in main}, {d["idx"] for d in donor_pool}
    main_fids, donor_fids = {fid_of(r) for r in main}, {fid_of(d) for d in donor_pool}
    if main_ids & donor_ids:
        errs.append(("main_donor_overlap", sorted(main_ids & donor_ids)[:5]))
    if donor_ids & set(old_idx):
        errs.append(("donor_old_wiki2_overlap", len(donor_ids & set(old_idx))))
    missing_v1 = set(v1_fids) - main_fids
    if missing_v1:
        errs.append(("v1_families_missing_from_main", sorted(missing_v1)))
    if len(main) != N_MAIN or len(donor_pool) != N_DONOR:
        errs.append(("pool_size_mismatch", len(main), len(donor_pool)))
    by_cond = Counter(r["condition"] for r in rows)
    for r in rows:
        if r["family_id"] in donor_fids:
            errs.append(("donor_family_in_eval", r["family_id"]))
        if r["condition"] == "distractor":
            if r["meta"].get("hardness") not in ("same_entity", "same_relation", "soft"):
                errs.append(("distractor_missing_hardness", r["family_id"]))
            if r["meta"]["donor_family"] not in donor_fids:
                errs.append(("distractor_donor_not_in_donor_pool", r["family_id"]))
        if (r["condition"] == "wrong_candidate_citation"
                and r["meta"]["cand_source"] == "other_family_answer"):
            if not any(norm(d["answer"]) == norm(str(r["meta"]["cand"])) for d in donor_pool):
                errs.append(("wc_donor_answer_not_from_donor_pool", r["family_id"]))
    if sum(hard_ct.values()) != by_cond.get("distractor", 0):
        errs.append(("hardness_count_mismatch", dict(hard_ct), by_cond.get("distractor", 0)))
    for cond in ("original", "cc_attempt", "format"):
        if by_cond.get(cond, 0) != N_MAIN:
            errs.append(("condition_count_short", cond, by_cond.get(cond, 0)))
    for a, b in (("insufficient", "insuf_ctr"), ("insufficient", "suff_ctr")):
        if by_cond.get(a, 0) != by_cond.get(b, 0):
            errs.append(("insuf_triplet_count_mismatch", a, b))
    expect = sum(by_cond.values())
    if len(rows) != expect:
        errs.append(("row_total_mismatch", len(rows), expect))
    return errs

# ------------------------------ audit samples --------------------------------------
def sample_block(lines, r, with_meta=True):
    lines.append(f"### {r['family_id']}  (gold: {r['gold']}, gold_behavior: {r['gold_behavior']})\n")
    lines.append("```text\n" + r["prompt"] + "\n```\n")
    if with_meta and r["meta"]:
        lines.append("meta: `" + json.dumps(r["meta"], ensure_ascii=False) + "`\n")

def write_audit(rows):
    rng = random.Random(SEED500)
    by_cond = {}
    for r in rows:
        by_cond.setdefault(r["condition"], []).append(r)
    lines = ["# AUDIT_SAMPLES_K500 — Knowledge (2Wiki) formal 500-family eval",
             f"\nGenerator: {GEN_VER}, seed {SEED500}. Paraphrase: PENDING (no rows).",
             "\nSections: 5 random samples per condition, then 15 insufficient and "
             "15 hard-distractor samples listed separately.\n"]
    for cond in sorted(by_cond):
        picks = rng.sample(by_cond[cond], min(5, len(by_cond[cond])))
        lines.append(f"\n## condition: {cond} (n={len(by_cond[cond])})\n")
        for r in picks:
            sample_block(lines, r)
    # 15 extra insufficient
    ins = rng.sample(by_cond["insufficient"], min(15, len(by_cond["insufficient"])))
    lines.append(f"\n## EXTRA: insufficient x{len(ins)} (leak-checked context removal)\n")
    for r in ins:
        sample_block(lines, r)
    # 15 hard distractors, stratified by hardness
    dis = by_cond["distractor"]
    by_h = {}
    for r in dis:
        by_h.setdefault(r["meta"]["hardness"], []).append(r)
    picks, quota = [], {"same_entity": 7, "same_relation": 5, "soft": 3}
    for k, n in quota.items():
        picks += rng.sample(by_h.get(k, []), min(n, len(by_h.get(k, []))))
    if len(picks) < 15:
        rest = [r for r in dis if r not in picks]
        picks += rng.sample(rest, min(15 - len(picks), len(rest)))
    lines.append(f"\n## EXTRA: hard-distractor x{len(picks)} (stratified by hardness)\n")
    for r in picks:
        lines.append(f"**hardness={r['meta']['hardness']}**\n")
        sample_block(lines, r)
    (OUT / "AUDIT_SAMPLES_K500.md").write_text("\n".join(lines))

# ------------------------------ main -----------------------------------------------
def main():
    v1 = json.loads(V1_POOL_FILE.read_text())
    v1_fids = list(v1["families"])
    assert len(v1_fids) == 50, "v1 pool file malformed"
    cands, old_idx, acct = load_rows()
    by_fid = {fid_of(r): r for r in cands}
    missing = [f for f in v1_fids if f not in by_fid]
    assert not missing, f"v1 families missing from filtered candidates: {missing}"
    v1_rows = [by_fid[f] for f in v1_fids]
    v1_set = set(v1_fids)
    rest = [r for r in cands if fid_of(r) not in v1_set]
    rng = random.Random(SEED500)
    extra = rng.sample(rest, N_MAIN - len(v1_rows))
    main_pool = v1_rows + extra
    main_ids = {r["idx"] for r in main_pool}
    rest2 = [r for r in rest if r["idx"] not in main_ids]
    donor_pool, cover_stats = select_donors(main_pool, rest2, rng)

    dindex = donor_index(donor_pool)
    rows, insuf_n, insuf_drop, hard_ct, donor_use = build(main_pool, dindex, donor_pool)
    errs = verify(rows, main_pool, old_idx)
    errs += verify_k500(rows, main_pool, donor_pool, old_idx, v1_fids, hard_ct)

    (OUT / "eval_k500_proto.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    (OUT / "main_pool_k500.json").write_text(json.dumps(
        {"seed": SEED500, "generator_version": GEN_VER,
         "n_main": len(main_pool), "n_donor": len(donor_pool),
         "v1_comparable_subset": v1_fids,
         "main_families": [fid_of(r) for r in main_pool],
         "main_hf_ids": [r["hf_id"] for r in main_pool],
         "donor_families": [fid_of(d) for d in donor_pool],
         "donor_hf_ids": [d["hf_id"] for d in donor_pool],
         "donor_role": "distractor+wrong-candidate donors only; never evaluated",
         "donor_selection": "greedy same_entity set cover over validation-minus-main, "
                            "random fill for leftover slots"},
        indent=2))
    n_dis = sum(hard_ct.values())
    stats = {
        "generator_version": GEN_VER, "seed": SEED500,
        "dataset": "framolfese/2wikimultihopqa", "split": "validation",
        "main_pool_families": len(main_pool),
        "v1_subset_included": len(v1_set & {fid_of(r) for r in main_pool}),
        "donor_pool_families": len(donor_pool),
        "main_donor_overlap": len(main_ids & {d["idx"] for d in donor_pool}),
        "old_wiki2_excluded_ids": len(old_idx),
        "filter_accounting": acct,
        "candidate_pool_after_filters": len(cands),
        "insufficient_survivors": insuf_n,
        "insufficient_survival_rate": round(insuf_n / len(main_pool), 4),
        "insufficient_drop_reasons": insuf_drop,
        "paraphrase": "PENDING — no rule-based rewrite; overrides file to come",
        "eval_rows": len(rows),
        "eval_by_condition": dict(Counter(r["condition"] for r in rows)),
        "distractor_hardness": hard_ct,
        "distractor_hardness_share": {k: round(v / n_dis, 4) for k, v in hard_ct.items()},
        "donor_selection_coverage": cover_stats,
        "distractor_same_entity_match_kind": dict(Counter(
            r["meta"].get("match_kind") for r in rows
            if r["condition"] == "distractor" and r["meta"]["hardness"] == "same_entity")),
        "donor_accounting": {
            "distinct_donors_used": len(donor_use),
            "max_reuse_of_one_donor": max(donor_use.values()) if donor_use else 0,
            "donor_uses_total": sum(donor_use.values())},
        "wc_candidate_sources": dict(Counter(
            r["meta"]["cand_source"] for r in rows if r["condition"] == "wrong_candidate_citation")),
        "wc_answer_classes": dict(Counter(
            r["meta"]["answer_class"] for r in rows if r["condition"] == "wrong_candidate_citation")),
        "question_types_in_pool": dict(Counter(r["type"] for r in main_pool)),
        "verify_errors": errs,
    }
    (OUT / "build_stats_k500.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    write_audit(rows)
    print(json.dumps(stats, indent=2, ensure_ascii=False))
    if errs:
        raise SystemExit(f"VERIFY FAILED: {len(errs)} errors")

if __name__ == "__main__":
    main()
