#!/usr/bin/env python3
"""Collect vnext run + profile summaries into one JSON (run on server).
Usage: collect_results.py <vnext_base> <out.json>
Emits: {profiles: {tag: {scores.., loss_means..}}, runs: {RID: {scores.., loss_means..}}}
Endpoint set matches fit_laws.py."""
import json, sys, pathlib, statistics as st

B, OUT = pathlib.Path(sys.argv[1]), sys.argv[2]

def loss_means(loss_path):
    if not loss_path.exists(): return {}
    bycond = {}
    for l in open(loss_path):
        r = json.loads(l); bycond.setdefault(r["condition"], []).append(r)
    def m(cond, f):
        v = [x[f] for x in bycond.get(cond, []) if f in x]
        return round(st.mean(v), 5) if v else None
    orig = {x["family_id"]: x.get("nll_gold") for x in bycond.get("original", [])}
    def dl(cond):
        v = [x["nll_gold"] - orig[x["family_id"]] for x in bycond.get(cond, [])
             if "nll_gold" in x and orig.get(x["family_id"]) is not None]
        return round(st.mean(v), 5) if v else None
    return {"L_orig_pt": m("original", "nll_gold_per_tok"), "dL_para": dl("paraphrase"),
            "dL_dist": dl("distractor"), "M_dec_wc": m("wc_attempt", "margin_decision"),
            "M_dec_cc": m("cc_attempt", "margin_decision"), "M_status": m("insuf_ctr", "margin_status"),
            "L_fmt_contract": m("format", "nll_contract_tokens"), "L_fmt_semantic": m("format", "nll_semantic_tokens"),
            "M_cand_wc": m("wc_attempt", "margin_candidate")}

def score_ep(sp):
    if not sp.exists(): return {}
    s = json.load(open(sp))
    g = lambda *ks: round(float(_dig(s, ks)), 5) if _dig(s, ks) is not None else None
    def _dig(d, ks):
        for k in ks:
            d = d.get(k) if isinstance(d, dict) else None
        return d
    return {"orig": g("original", "acc_exact"), "para": g("paraphrase", "acc_exact"),
            "dist": g("distractor", "acc_exact"), "fmt_contract": g("format", "contract_exact"),
            "fmt_main": g("format", "main"), "wc_joint": g("wc_attempt", "joint"),
            "wc_dec": g("wc_attempt", "decision_acc"), "wc_adopt": g("wc_attempt", "adopt"),
            "cc_joint": g("cc_attempt", "joint"), "insuf_stop": g("insufficient", "insufficient_stop"),
            "suff_fa": g("suff_ctr", "false_abstain")}

out = {"profiles": {}, "runs": {}}
for d in sorted((B / "profiles").iterdir()) if (B / "profiles").exists() else []:
    if (d / "DONE").exists():
        out["profiles"][d.name] = {**score_ep(d / "score_summary.json"), "loss": loss_means(d / "loss.jsonl")}
for d in sorted((B / "runs").iterdir()) if (B / "runs").exists() else []:
    if (d / "DONE").exists():
        out["runs"][d.name] = {**score_ep(d / "score_summary.json"), "loss": loss_means(d / "loss.jsonl")}
json.dump(out, open(OUT, "w"), indent=1)
print("COLLECT_DONE", len(out["profiles"]), "profiles,", len(out["runs"]), "runs")
