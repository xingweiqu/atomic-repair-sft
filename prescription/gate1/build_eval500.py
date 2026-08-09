#!/usr/bin/env python3
"""eval-500 builder (C-28 P0): expand the Reasoning eval from 50 to 500 families.

Does NOT modify build_gate1.py; imports and reuses its functions/constants.

Contract (C-28):
  * main pool = 500 families randomly sampled (SEED_500=20260816) from the
    base_filter'ed GSM8K TEST split, UNION the frozen v1.2 50-family pool
    (prescription/gate1/main_pool.json); the old 50 MUST all be included so the
    old 518-row readings remain a comparable subset.
  * pool ordering = old-50 first (frozen order), then new sampled families in
    sample order.  wc_nl / cc_nl are built on the FIRST 100 families of that
    order, so the old 20-family NL subset is preserved verbatim.
  * conditions = full v1.2 set: original / distractor / format / wc_light /
    wc_attempt / cc_light / cc_attempt (KEEP-REVISE contract) / wc_nl / cc_nl
    (first 100 families) / insufficient + insuf_ctr + suff_ctr (typed_delete
    surviving subset, all mechanical gates).
  * paraphrase: ONLY the 50 hand-written rewrites from paraphrase_overrides.json
    (rule-based rewriting is banned); all other families are flagged missing.
  * outputs: eval500_proto.jsonl / build_stats_500.json / AUDIT_SAMPLES_500.md.
    main_pool.json is NOT touched; the frozen 550-family list goes to
    main_pool_500.json.

Built-in hard checks (assertions, build fails loudly):
  1. zero family overlap with the FULL training pool: lawv1/*_pool_formal.jsonl
     + lawv1/carrier_formal.json (text-matched back to GSM8K ids) +
     gate1/train_proto.jsonl;
  2. every insufficient row re-passes word_leak / RESIDUE / derivable using
     build_gate1's own functions (recomputed from the DELETED prompt's numbers,
     i.e. independent of typed_delete's internal bookkeeping);
  3. wc_* candidate != gold on every row;
  4. union accounting: all old eval rows OUTSIDE the insufficient trio reappear
     with identical condition/prompt/gold/gold_behavior; per-condition counts
     reconcile.  The insufficient / insuf_ctr / suff_ctr trio is NOT required
     to be verbatim: the checked-in eval_proto.jsonl (518 rows) predates the
     later typed_delete hardening in build_gate1.py (comparative/comma-compound
     guards, commit c78552d) and was never regenerated, so a few old
     insufficient rows are legitimately dropped or re-derived by the current
     generator.  The delta is fully accounted in build_stats_500.json.
"""
import json, random, sys, re
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))
import build_gate1 as G

ROOT = G.ROOT
SEED_500 = 20260816
N_NEW = 500
N_NL = 100
GEN_VER_500 = G.GEN_VER + "-eval500"
AUDIT_SEED = 20260816

# ------------------------------------------------------------------ pool
def build_pool():
    cache = json.load(open(ROOT / "data_v4/gsm8k_cache.json"))
    cands = [it for it in cache["test"] if G.base_filter(it)]
    by_id = {it["id"]: it for it in cands}
    old = json.load(open(OUT / "main_pool.json"))["families"]
    assert len(old) == 50, f"frozen pool expected 50, got {len(old)}"
    missing_old = [f for f in old if f not in by_id]
    assert not missing_old, f"old families fail base_filter now: {missing_old}"
    sampled = random.Random(SEED_500).sample(cands, N_NEW)
    sampled_ids = [it["id"] for it in sampled]
    overlap = [f for f in sampled_ids if f in set(old)]
    order = list(old) + [f for f in sampled_ids if f not in set(old)]
    pool = [by_id[f] for f in order]
    acct = {
        "base_filtered_test_n": len(cands),
        "sampled_n": N_NEW,
        "old_pool_n": len(old),
        "sample_old_overlap_n": len(overlap),
        "sample_old_overlap": overlap,
        "union_pool_n": len(order),
    }
    return pool, order, acct, cache

# ------------------------------------------------------- typed_delete diagnosis
def diagnose_typed_delete(it):
    """Mirror of G.typed_delete control flow, returning per-candidate rejection
    reasons instead of bailing silently.  Consistency with G.typed_delete is
    asserted by the caller."""
    if it["id"] in G.INSUF_BLOCKLIST:
        return None, ["blocklist"]
    q = it["question"]
    all_vals = [G.numval(t) for t in G.NUM_TOKEN.findall(q)]
    reasons = []
    for n_raw in it["steps"][0]["nums"]:
        val = G.numval(n_raw.lstrip("-"))
        if val in (None, 0, 1):
            reasons.append("val_trivial"); continue
        toks = G.find_tokens_for_value(q, val)
        if len(toks) != 1 or all_vals.count(val) != 1:
            reasons.append("not_unique_mention"); continue
        if G.word_leak(q, val):
            reasons.append("number_word_leak"); continue
        others = [v for v in all_vals if v != val]
        if G.derivable(others, val):
            reasons.append("derivable_from_rest"); continue
        s, e, tok = toks[0]
        vtype, repl, ds, de = G.classify_token(q, s, e, tok)
        if repl is None:
            reasons.append(f"unsafe_context:{vtype}"); continue
        head = q[:ds]
        if re.search(r"(?:^|[\.!?]\s+)$", head):
            repl = repl[0].upper() + repl[1:]
        new_q = head + repl + q[de:]
        if G.RESIDUE.search(new_q):
            reasons.append("grammar_residue"); continue
        return (new_q, val), reasons
    if not reasons:
        reasons = ["no_numeric_first_step_input"]
    return None, reasons

# ------------------------------------------------------------------ eval rows
def build_rows(pool, overrides, nl_fams):
    """Per-family condition build, replicated verbatim from
    build_gate1.build_eval (v1.2) — all randomness is rng_for(fid, tag), so
    rows for the old 50 families reproduce byte-identically (checked later)."""
    rows, insuf_fams, taxo = [], [], {}
    insuf_reject = {}
    for it in pool:
        fid, gold = it["id"], str(int(float(it["final"])))
        q = it["question"].strip()
        base = dict(family_id=fid, source_id=fid, source_split="test", generator_id="B",
                    generator_version=G.GEN_VER, gold=gold, domain="reasoning")
        rng = G.rng_for(fid, "wc")
        etype, wv, wsteps = G.wrong_process(it, rng)
        taxo[etype] = taxo.get(etype, 0) + 1
        chain = [f"{s['expr']} = {s['result']}" for s in it["steps"]]
        dis, dmeta = G.pick_distractor(q, fid, G.GEN_B_DIS, "dis")
        parts = re.split(r"(?<=[.!?])\s+", q)
        q_dis = " ".join(parts[:-1] + [dis, parts[-1]]) if len(parts) >= 2 else q + " " + dis
        sch = G.GEN_B_FMT[G.h(fid) % 2]
        conds = {
            "original": dict(prompt=q),
            "distractor": dict(prompt=q_dis, meta=dmeta),
            "format": dict(prompt=q + "\n\n" + sch["instr"], meta={"schema": sch["id"], "check": sch["check"]}),
            "wc_light": dict(prompt=f"{q}\n\nCandidate attempt:\nThey state the answer is {wv}, without showing their work.\n\n{G.CONTRACT_B}",
                             meta={"cand": wv, "error_type": etype, "layer": "light"}),
            "wc_attempt": dict(prompt=f"{q}\n\nCandidate attempt:\n{G.render_attempt_B(wsteps, wv)}\n\n{G.CONTRACT_B}",
                               meta={"cand": wv, "error_type": etype, "layer": "attempt"}),
            "cc_light": dict(prompt=f"{q}\n\nCandidate attempt:\nThey state the answer is {gold}, without showing their work.\n\n{G.CONTRACT_B}",
                             meta={"cand": int(gold), "layer": "light"}),
            "cc_attempt": dict(prompt=f"{q}\n\nCandidate attempt:\n{G.render_attempt_B(chain, gold)}\n\n{G.CONTRACT_B}",
                               meta={"cand": int(gold), "layer": "attempt"}),
        }
        if fid in overrides:
            conds["paraphrase"] = dict(prompt=overrides[fid], meta={"source": "cc_rewrite_v1"})
        if fid in nl_fams:
            conds["wc_nl"] = dict(prompt=q + "\n\n" + G.NL_PROBE_B.format(cand=wv),
                                  meta={"cand": wv, "error_type": etype})
            conds["cc_nl"] = dict(prompt=q + "\n\n" + G.NL_PROBE_B.format(cand=gold),
                                  meta={"cand": int(gold)})
        td = G.typed_delete(it)
        diag, reasons = diagnose_typed_delete(it)
        assert (td is None) == (diag is None), f"diagnose/typed_delete disagree on {fid}"
        if td is not None:
            assert diag[0] == td[0], f"diagnose prompt mismatch on {fid}"
            conds["insufficient"] = dict(prompt=td[0], meta=td[1], gold_behavior="abstain")
            conds["insuf_ctr"] = dict(prompt=td[0] + "\n\n" + G.CONTRACT_STATUS, meta=td[1], gold_behavior="abstain")
            conds["suff_ctr"] = dict(prompt=q + "\n\n" + G.CONTRACT_STATUS, meta={})
            insuf_fams.append(fid)
        else:
            insuf_reject[fid] = reasons
        for cname, c in conds.items():
            r = dict(base)
            r.update(condition=cname, prompt=c["prompt"], meta=c.get("meta", {}),
                     gold_behavior=c.get("gold_behavior", "answer"),
                     template_id=c.get("meta", {}).get("schema", "-"))
            rows.append(r)
    return rows, insuf_fams, insuf_reject, taxo

# ------------------------------------------------------------------ hard checks
def norm_text(s):
    return " ".join(s.split())

def load_train_families(cache):
    fams = set()
    lawv1 = ROOT / "prescription/lawv1"
    pool_files = sorted(lawv1.glob("*_pool_formal.jsonl"))
    assert len(pool_files) == 4, f"expected 4 formal pools, found {pool_files}"
    for f in pool_files:
        for line in f.open():
            fams.add(json.loads(line)["family_id"])
    for line in (OUT / "train_proto.jsonl").open():
        fams.add(json.loads(line)["family_id"])
    # carrier_formal.json rows carry no family_id -> map back by exact text.
    txt2id = {}
    for split in ("train", "test"):
        for it in cache[split]:
            txt2id[norm_text(it["question"])] = it["id"]
    carrier = json.load(open(lawv1 / "carrier_formal.json"))
    unmatched = 0
    for row in carrier:
        fid = txt2id.get(norm_text(row["instruction"]))
        if fid is None:
            unmatched += 1
        else:
            fams.add(fid)
    return fams, len(carrier), unmatched

def verify_500(rows, pool_ids, cache):
    errs = list(G.verify([], rows))                       # reuse v1.2 eval-side checks

    # (1) zero family overlap with the full training pool
    train_fams, carrier_n, carrier_unmatched = load_train_families(cache)
    inter = train_fams & set(pool_ids)
    assert not inter, f"train/eval family leak: {sorted(inter)[:10]}"
    # belt-and-braces: no eval prompt text equals a carrier instruction
    pool_txt = {norm_text(r["prompt"]) for r in rows if r["condition"] == "original"}
    carrier_txt = {norm_text(c["instruction"]) for c in json.load(
        open(ROOT / "prescription/lawv1/carrier_formal.json"))}
    assert not (pool_txt & carrier_txt), "carrier text overlaps eval originals"

    # (2) insufficient rows: independent re-check from the deleted prompt itself
    for r in rows:
        if r["condition"] != "insufficient":
            continue
        p, fid = r["prompt"], r["family_id"]
        assert not G.RESIDUE.search(p), f"residue {fid}"
        v = G.numval(r["meta"]["removed_variable"])
        assert v is not None, f"insuf meta removed_variable unparsable {fid}"
        assert not G.word_leak(p, v), f"word leak {fid}"
        remaining = [G.numval(t) for t in G.NUM_TOKEN.findall(p)]
        assert v not in remaining, f"removed value still stated {fid}"
        assert not G.derivable(remaining, v), f"derivable {fid}"
        for k in ("removed_variable", "variable_type", "dependency_path", "why_unanswerable"):
            assert k in r["meta"], f"insuf meta missing {k} {fid}"

    # (3) wc candidate != gold
    for r in rows:
        if r["condition"].startswith("wc"):
            assert str(r["meta"]["cand"]) != r["gold"], f"wc cand==gold {r['family_id']}"
        if r["condition"].startswith("cc"):
            assert str(r["meta"]["cand"]) == r["gold"], f"cc cand!=gold {r['family_id']}"

    # (4) union accounting vs the frozen 518-row eval.
    # Strict verbatim outside the insufficient trio; the trio may differ because
    # eval_proto.jsonl predates the later typed_delete hardening (see docstring).
    INSUF_TRIO = {"insufficient", "insuf_ctr", "suff_ctr"}
    old_rows = [json.loads(l) for l in (OUT / "eval_proto.jsonl").open()]
    new_key = {(r["family_id"], r["condition"]): r for r in rows}
    assert len(new_key) == len(rows), "duplicate (family, condition) rows"
    mismatch, trio_delta = [], {"reproduced": 0, "changed": [], "dropped": []}
    for o in old_rows:
        k = (o["family_id"], o["condition"])
        nr = new_key.get(k)
        same = nr is not None and (nr["prompt"], nr["gold"], nr["gold_behavior"]) == \
            (o["prompt"], o["gold"], o["gold_behavior"])
        if o["condition"] in INSUF_TRIO:
            if same:
                trio_delta["reproduced"] += 1
            elif nr is None:
                trio_delta["dropped"].append(list(k))
            else:
                trio_delta["changed"].append(list(k))
        elif nr is None:
            mismatch.append(("missing", k))
        elif not same:
            mismatch.append(("changed", k))
    assert not mismatch, f"old non-insufficient rows not a verbatim subset: {mismatch[:5]}"
    n_strict = sum(1 for o in old_rows if o["condition"] not in INSUF_TRIO)
    return errs, {"old_rows": len(old_rows),
                  "old_rows_outside_insuf_trio": n_strict,
                  "old_rows_outside_insuf_trio_reproduced_verbatim": n_strict,
                  "old_insuf_trio_rows": len(old_rows) - n_strict,
                  "old_insuf_trio_delta": trio_delta,
                  "insuf_trio_delta_reason": "eval_proto.jsonl predates typed_delete hardening (c78552d); current generator is authoritative",
                  "new_rows_added": len(rows) - len(old_rows),
                  "carrier_rows": carrier_n, "carrier_text_unmatched": carrier_unmatched,
                  "train_family_pool_n": len(train_fams)}

# ------------------------------------------------------- suspect pre-screen
# Mechanical pre-screen of insufficient rows for the human adjudicator.
# FLAG ONLY — nothing is dropped here; blocklisting is an adjudication call
# (established mechanism: INSUF_BLOCKLIST in build_gate1.py).
# Known generator bug behind class (a): classify_token reads only a 16-char
# lookahead window (after = q[e:e+16]), which truncates the second word of long
# noun compounds ("chocolate cupca..."), so the plural-compound guard
# (w2.endswith("s")) misfires and the MODIFIER gets pluralized
# ("chocolates cupcakes", "seasonals workers", "nows", "hows").
SUSPECT_DOUBLE_PLURAL = re.compile(r"unspecified number of ([A-Za-z&]+s) ([a-z]+s)\b")
SUSPECT_FUNCWORD_HEAD = re.compile(r"unspecified number of (nows|hows|thens|Ms|ones|sames)\b")
SUSPECT_MOD_PLURAL_3 = re.compile(r"unspecified number of ([a-z]+s) ([a-z]+) ([a-z]+s)\b")
# words that legitimately follow a real plural head noun -> not a suspect
_OK_AFTER_PLURAL = {"this", "his", "its", "is", "was", "has", "as", "does", "plus",
                    "across", "thus", "less"}
_OK_MIDDLE = {"of", "on", "and", "or", "for", "in", "at", "to", "with", "per", "by",
              "from", "before", "after", "than", "the", "a", "an", "every", "each",
              "his", "her", "their", "this", "that"}
SUSPECT_WORLD_KNOWLEDGE = re.compile(
    r"unspecified number of (days|weeks|months) in (January|February|March|April|May|June|July|"
    r"August|September|October|November|December|a week|a month|a year)", re.I)

def suspect_scan(rows):
    out = []
    for r in rows:
        if r["condition"] != "insufficient":
            continue
        p = r["prompt"]
        hit = None
        if m := SUSPECT_FUNCWORD_HEAD.search(p):
            hit = ("pluralized_modifier_or_funcword", m.group(0))
        elif (m := SUSPECT_DOUBLE_PLURAL.search(p)) and m.group(2) not in _OK_AFTER_PLURAL:
            hit = ("double_plural_compound", m.group(0))
        elif (m := SUSPECT_MOD_PLURAL_3.search(p)) and m.group(2) not in _OK_MIDDLE:
            hit = ("modifier_plural_3gram", m.group(0))
        elif m := SUSPECT_WORLD_KNOWLEDGE.search(p):
            hit = ("world_knowledge_recoverable", m.group(0))
        elif "Ms&Ms" in p:
            hit = ("mangled_token", "Ms&Ms")
        if hit:
            out.append({"family_id": r["family_id"], "class": hit[0], "surface": hit[1]})
    return out

# ------------------------------------------------------------------ audit file
def write_audit(rows, path, suspects):
    rng = random.Random(AUDIT_SEED)
    by_cond = defaultdict(list)
    for r in rows:
        by_cond[r["condition"]].append(r)
    lines = ["# AUDIT_SAMPLES_500 — eval-500 human-audit draw",
             f"\nSeeded draw (seed={AUDIT_SEED}): 5 rows per condition, plus 30 "
             "insufficient rows listed separately for full manual review.\n"]
    def render(r, i):
        out = [f"### {i}. `{r['family_id']}` / {r['condition']} (gold={r['gold']}, behavior={r['gold_behavior']})"]
        m = r.get("meta") or {}
        keep = {k: m[k] for k in ("cand", "error_type", "layer", "schema", "removed_variable",
                                  "variable_type", "replacement", "source", "k", "item") if k in m}
        if keep:
            out.append(f"meta: `{json.dumps(keep, ensure_ascii=False)}`")
        out.append("```text\n" + r["prompt"] + "\n```")
        return "\n".join(out) + "\n"
    for cond in sorted(by_cond):
        pick = rng.sample(by_cond[cond], min(5, len(by_cond[cond])))
        lines.append(f"\n## condition: {cond} (n={len(by_cond[cond])}, showing {len(pick)})\n")
        for i, r in enumerate(pick, 1):
            lines.append(render(r, i))
    lines.append("\n## INSUFFICIENT mechanical pre-screen suspects (FLAGS, not drops — adjudicate)\n")
    lines.append("Known generator bug for the plural classes: classify_token's 16-char lookahead "
                 "truncates long compounds, so the plural-compound guard misfires and the modifier "
                 "gets pluralized. World-knowledge class: deleted value recoverable from common "
                 "knowledge, so the row is still answerable despite passing all text-level gates.\n")
    for s in suspects:
        lines.append(f"- `{s['family_id']}` [{s['class']}] \"{s['surface']}\"")
    lines.append("")
    insuf = by_cond.get("insufficient", [])
    pick30 = rng.sample(insuf, min(30, len(insuf)))
    lines.append(f"\n## INSUFFICIENT manual-audit draw (n={len(insuf)}, showing {len(pick30)})\n")
    for i, r in enumerate(pick30, 1):
        m = r["meta"]
        lines.append(f"### I{i:02d}. `{r['family_id']}` removed=`{m['removed_variable']}` "
                     f"type={m['variable_type']}")
        lines.append(f"why_unanswerable: {m['why_unanswerable']}")
        lines.append("```text\n" + r["prompt"] + "\n```\n")
    path.write_text("\n".join(lines) + "\n")
    return [r["family_id"] for r in pick30]

# ------------------------------------------------------------------ main
def main():
    pool, order, acct, cache = build_pool()
    overrides = json.load(open(OUT / "paraphrase_overrides.json"))
    assert set(overrides) == set(order[:50]), "overrides must be exactly the old 50 (hand-written only)"
    nl_fams = set(order[:N_NL])
    rows, insuf_fams, insuf_reject, taxo = build_rows(pool, overrides, nl_fams)
    errs, union_acct = verify_500(rows, order, cache)
    assert not errs, f"verify errors: {errs}"

    by_cond = Counter(r["condition"] for r in rows)
    n = len(order)
    assert by_cond["original"] == by_cond["distractor"] == by_cond["format"] == n
    assert by_cond["wc_light"] == by_cond["wc_attempt"] == by_cond["cc_light"] == by_cond["cc_attempt"] == n
    assert by_cond["paraphrase"] == 50
    assert by_cond["wc_nl"] == by_cond["cc_nl"] == N_NL
    assert by_cond["insufficient"] == by_cond["insuf_ctr"] == by_cond["suff_ctr"] == len(insuf_fams)
    assert len(rows) == sum(by_cond.values())

    reject_primary = Counter(v[0] for v in insuf_reject.values())
    reject_all = Counter(x for v in insuf_reject.values() for x in v)

    (OUT / "eval500_proto.jsonl").write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    (OUT / "main_pool_500.json").write_text(json.dumps(
        {"seed_new": SEED_500, "seed_old": G.SEED, "note": "old-50 first (frozen order), then new sample order",
         "families": order}, indent=2))
    suspects = suspect_scan(rows)
    audit_insuf_ids = write_audit(rows, OUT / "AUDIT_SAMPLES_500.md", suspects)

    stats = {
        "generator_version": GEN_VER_500,
        "pool_accounting": acct,
        "nl_subset_n": N_NL,
        "eval_rows": len(rows),
        "eval_by_condition": dict(by_cond),
        "eval_wrong_candidate_taxonomy": dict(taxo),
        "paraphrase": {"present_n": by_cond["paraphrase"],
                       "missing_n": n - by_cond["paraphrase"],
                       "policy": "hand-written old-50 only; rule-based rewriting banned; others flagged missing"},
        "insufficient": {
            "survivors_n": len(insuf_fams),
            "survival_rate": round(len(insuf_fams) / n, 4),
            "rejected_n": len(insuf_reject),
            "reject_primary_reason": dict(reject_primary.most_common()),
            "reject_all_reasons_candidate_level": dict(reject_all.most_common()),
            "variable_types": dict(Counter(
                r["meta"]["variable_type"] for r in rows if r["condition"] == "insufficient")),
            "prescreen_suspects_flagged_not_dropped": suspects,
        },
        "union_accounting_vs_old_518": union_acct,
        "audit_insufficient_draw": audit_insuf_ids,
        "verify_errors": [],
    }
    (OUT / "build_stats_500.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
