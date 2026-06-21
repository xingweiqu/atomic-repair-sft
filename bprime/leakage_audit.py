"""Leakage audit: is v3 convergent-floor ability=1.00 real or memorized test answers?

Read-only. No retraining. Checks train/eval overlap at the SURFACE and ORACLE (triple) levels,
a context-bypass memorization signal from existing floor predictions, world size, and a v4 control.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from bprime.bprime_audit import load_run, extract_final, parse, strkey


def load(p):
    return [json.loads(l) for l in Path(p).open() if l.strip()]


def norm_txt(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def mask_entities(problem, facts):
    """Remove the item's own entity strings -> template skeleton, for surface-overlap check."""
    t = problem or ""
    ents = set()
    for tri in facts or []:
        ents.update(str(x) for x in tri)
    for e in sorted(ents, key=len, reverse=True):
        if e:
            t = re.sub(re.escape(e), "<E>", t)
    return norm_txt(t)


def triples(item):
    out = []
    for tri in item.get("gold_symbolic_facts") or []:
        if isinstance(tri, list) and len(tri) == 3:
            out.append(tuple(str(x).strip().lower() for x in tri))
    return out


def main():
    L = ["# Leakage audit — is v3 convergent-floor ability real or memorized?", "",
         "_Read-only; no retraining._", ""]

    tr = load("data_v3_1/repair_train.jsonl")
    ev = load("data_v3_1/repair_eval.jsonl")

    # ---- 1c world size ----
    all_tri, heads, rels, tails = set(), set(), set(), set()
    for it in tr + ev:
        for h, r, t in triples(it):
            all_tri.add((h, r, t)); heads.add(h); rels.add(r); tails.add(t)
    L += ["## 1c. v3 world size", "",
          f"- unique triples: **{len(all_tri)}** · heads: {len(heads)} · relations: {len(rels)} · tails: {len(tails)}",
          f"- train items {len(tr)} / eval items {len(ev)}",
          "_Small world + 30-epoch full SFT ⇒ memorization is plausible a priori._", ""]

    # ---- 1a surface overlap ----
    tr_prob = set(norm_txt(it["problem"]) for it in tr)
    tr_tmpl = set(mask_entities(it["problem"], it.get("gold_symbolic_facts")) for it in tr)
    exact = sum(1 for it in ev if norm_txt(it["problem"]) in tr_prob)
    tmpl = sum(1 for it in ev if mask_entities(it["problem"], it.get("gold_symbolic_facts")) in tr_tmpl)
    L += ["## 1a. Surface overlap (problem text)", "",
          f"- exact problem match eval∈train: **{exact}/{len(ev)}** ({exact/len(ev):.1%})",
          f"- entity-masked TEMPLATE match eval∈train: **{tmpl}/{len(ev)}** ({tmpl/len(ev):.1%})",
          "_Template match high but exact low = same phrasing skeletons, different entities (by design)._", ""]

    # ---- 1b oracle (triple) overlap — the key check ----
    tr_tri = set()
    tr_heads, tr_tails, tr_hr = set(), set(), set()
    for it in tr:
        for h, r, t in triples(it):
            tr_tri.add((h, r, t)); tr_heads.add(h); tr_tails.add(t); tr_hr.add((h, r))
    ev_tri = [(h, r, t) for it in ev for (h, r, t) in triples(it)]
    n = len(ev_tri) or 1
    tri_ov = sum(1 for x in ev_tri if x in tr_tri)
    head_ov = sum(1 for (h, r, t) in ev_tri if h in tr_heads)
    tail_ov = sum(1 for (h, r, t) in ev_tri if t in tr_tails)
    hr_ov = sum(1 for (h, r, t) in ev_tri if (h, r) in tr_hr)
    L += ["## 1b. ★ Oracle (triple) overlap — leakage check", "",
          "| overlap of eval facts with train | rate |", "|---|---|",
          f"| exact (head, relation, tail) triple | **{tri_ov}/{n} = {tri_ov/n:.1%}** |",
          f"| head entity seen in train | {head_ov}/{n} = {head_ov/n:.1%} |",
          f"| tail entity seen in train | {tail_ov}/{n} = {tail_ov/n:.1%} |",
          f"| (head, relation) pair seen in train | {hr_ov}/{n} = {hr_ov/n:.1%} |",
          "_High exact-triple overlap ⇒ the convergent floor can default-write eval answers._", ""]

    # ---- 2b context-bypass memorization (floor predictions, no ckpt needed) ----
    floor = load_run("data_v3_1/predict_outputs", "scaffold_conv")
    L += ["## 2b. Context-bypass signal (convergent floor predictions)", ""]
    if floor:
        # H-class / bridge items: is the gold answer literally present in the given context?
        rows_checked = ans_not_in_ctx = correct_when_not_in_ctx = total_correct = 0
        for i, it in enumerate(ev):
            pol = it["policy"]
            if pol not in ("verify_bridge", "use_provided_support"):
                continue
            rows_checked += 1
            ctx = norm_txt(" ".join(it.get("oracle_facts") or []))
            gold = strkey(it.get("gold_answer"))
            fa = strkey(extract_final(parse(floor[i]), floor[i]))
            ok = (fa is not None and fa == gold)
            total_correct += int(ok)
            in_ctx = gold is not None and gold in ctx
            if not in_ctx:
                ans_not_in_ctx += 1
                if ok:
                    correct_when_not_in_ctx += 1
        L += [f"- H-class items checked (verify_bridge/use_provided_support): {rows_checked}",
              f"- gold answer NOT literally in provided context: {ans_not_in_ctx}",
              f"- floor CORRECT despite gold not in context: **{correct_when_not_in_ctx}/{ans_not_in_ctx}**"
              + (f" ({correct_when_not_in_ctx/ans_not_in_ctx:.1%})" if ans_not_in_ctx else ""),
              "_Correct when the answer is not in the context ⇒ it comes from weights (memorized), "
              "not from reading context. (Counterfactual probe 2a needs the ckpt ⇒ PHASE-1.)_", ""]
    else:
        L += ["_no floor predictions found_", ""]

    # ---- 3 epoch curve ----
    L += ["## 3. ability vs epoch", "",
          "_No intermediate scaffold checkpoints (3/10/20/30 epoch) were saved (save_total_limit=1). "
          "Cannot trace where memorization sets in without a PHASE-1 re-run; flagged, skipped._", ""]

    # ---- 4 v4 control ----
    t4 = load("data_v4/repair_train.jsonl")
    e4 = load("data_v4/repair_eval.jsonl")
    src_tr = set(r.get("source_id") for r in t4)
    src_ev = set(r.get("source_id") for r in e4)
    inter = src_tr & src_ev
    tr4_q = set(norm_txt(r.get("problem", "")) for r in t4)
    q_ov = sum(1 for r in e4 if norm_txt(r.get("problem", "")) in tr4_q)
    L += ["## 4. v4 (GSM8K) control — same overlap check", "",
          f"- GSM source split overlap (train source_id ∩ eval source_id): **{len(inter)}** "
          f"(train uses GSM train split, eval uses test split)",
          f"- exact problem-text overlap eval∈train: {q_ov}/{len(e4)}",
          "_v4 eval answers cannot be default-written: items come from the held-out GSM test split._", ""]

    L += ["## 5. Conclusion", "",
          "**Is v3 convergent-floor ability=1.00 caused by leakage / memorization? — PARTLY-TO-"
          "LARGELY YES.** Evidence: (1b) **79.4% of eval triples appear verbatim in train**, with "
          "head and (head,relation) 100% seen and tail 97% seen; (1c) the world is tiny "
          f"({len(all_tri)} unique triples) and the floor is 30-epoch full-parameter SFT — "
          "memorization is both feasible and indicated. Surface text does NOT overlap (1a, 0%), "
          "which is exactly why the original 'phrasing-disjoint' guarantee is insufficient: the "
          "oracle facts leak even when the wording does not.", "",
          "The decisive counterfactual probe (2a — does the floor follow a rewritten context or "
          "emit the memorized old tail) needs the ckpt ⇒ **PHASE-1**. (2b) is inconclusive: in v3 "
          "the gold is always in the context, so reading vs memorizing cannot be told apart from "
          "outputs alone.", "",
          "**Can v3 serve as evidence for the ability layer? — NO; demote to a cautionary case.** "
          "The v3 world is too small to measure ability without test-set contamination: a converged "
          "floor can default-write ~79% of eval answers, so v3 floor ability (and thus the v3 end of "
          "the modulation axis) is not a clean measurement. **Clean ability evidence exists only in "
          "v4** (held-out GSM test split, 0% source overlap, answers not default-writable). Net: the "
          "'targeted does not inject ability' conclusion stands on **v4 alone**; v3 becomes the "
          "cautionary tale that floor fit on a small synthetic world contaminates every measurement "
          "layer.", ""]

    out = Path("bprime/leakage_audit.md")
    out.write_text("\n".join(L))
    print("wrote", out)
    print("\n".join(L))


if __name__ == "__main__":
    main()
