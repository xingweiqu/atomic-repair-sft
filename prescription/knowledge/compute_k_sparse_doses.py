#!/usr/bin/env python3
"""K sparse-dose table (C-26 §五: Knowledge 每组件只跑 {0, n_onset, n_high}).

Mechanically applies the FROZEN onset algorithm of CONTRACT_ANALYSIS §4 to the
Reasoning discovery curves and writes K_SPARSE_DOSES.json. No plotting, no
judgment calls at run time; every rule is written down here and in the output.

Inputs (read-only):
  prescription/lawv1/curves_e500_all.json   EVD/FMT/REV runs + base, rescored on
                                            the 529-item e500 eval (insufficient
                                            conditions: 249 paired families)
  prescription/lawv1/curves_ans_e500.json   ANS runs; NOTE: despite the filename
                                            these are 50-family scores
                                            (insufficient n=26) — the ANS grid
                                            was not rescored on e500. Flagged in
                                            the output as small-n.

Frozen rules applied (CONTRACT_ANALYSIS §4 + PLAN_lawv1 §5):
  G_e(n)  = seed-mean s_e(component, n) − seed-mean s_e(dose-0 placebo of the
            same component grid)          [dose-0 = pure carrier replay]
  tau_e   = max( max over anchor doses of 3-seed half-range,
                 95% CI halfwidth at the placebo mean )
  onset_e = smallest grid dose n with |G_e(n)| > tau_e and
            sign(G_e(n)) == sign(G_e(n_next))   (top dose alone cannot qualify)
  no qualifying dose -> literal "no detected onset within tested range"

Documented deviations (goal-mode self-certified, advisor may veto):
  D1  CONTRACT_ANALYSIS §3 defines the CI term as an item-family bootstrap
      (B=2000) halfwidth. Per-item score files are not in the repo (only
      *_summary.json), so the CI term is the analytic binomial halfwidth
      1.96*sqrt(p(1-p)/n_items) at the placebo mean. For family-level
      endpoints this is a close stand-in; flagged per endpoint.
  D2  A component needs ONE dose, but onset is endpoint-specific. Rule used:
      onset_component = min over the component's frozen endpoint set
      (CONTRACT_EVAL §2 metric list of the targeted eval condition) of the
      endpoints' onsets. All per-endpoint onsets are listed in the output.
  D3  PLAN_lawv1 §5 "无 onset → {0, mid, high}" does not define mid.
      mid := median of the positive preregistered grid {30,60,120,240,480,
      960,2000} = 240.

Component -> targeted condition/endpoints (CONTRACT_EVAL §2):
  format        format: semantic_correct, json_valid, schema_compliant,
                        contract_exact, main
  evidence      distractor: acc_exact (primary), acc_loose, paired_family
  revision      wc_attempt + cc_attempt: final_acc (primary=correct),
                        decision_acc, joint, adopt, contract_followed
  answerability insufficient: paired_answerability (primary),
                        insufficient_stop; insuf_ctr/suff_ctr: status_acc, joint
  clean_replay  carrier component: dose-0 of every grid IS the 2000-replay
                arm, so a component-vs-placebo contrast does not exist by
                construction -> no onset defined; doses {0, high} only.

Output: K_SPARSE_DOSES.json (same dir). Deterministic, no RNG.
"""
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAW = HERE.parent / "lawv1"
OUT = HERE / "K_SPARSE_DOSES.json"

GRID_TOP = {"FMT": 2000, "REV": 2000, "EVD": 1620, "ANS": 1822}
BASE_GRID = [0, 30, 60, 120, 240, 480, 960]
ANCHORS = {"FMT": [0, 120, 960, 2000], "REV": [0, 120, 960, 2000],
           "EVD": [0, 120, 960, 1620], "ANS": [0, 120, 960, 1822]}
MID_NULL = 240      # D3: median of {30,60,120,240,480,960,2000}
HIGH_K = 2000       # high = max preregistered dose (CONTRACT_ANALYSIS §4)

ENDPOINT_SETS = {
    "FMT": [("format", f) for f in
            ("semantic_correct", "json_valid", "schema_compliant",
             "contract_exact", "main")],
    "EVD": [("distractor", f) for f in ("acc_exact", "acc_loose", "paired_family")],
    "REV": [(c, f) for c in ("wc_attempt", "cc_attempt")
            for f in ("final_acc", "decision_acc", "joint", "adopt",
                      "contract_followed")],
    "ANS": [("insufficient", "paired_answerability"),
            ("insufficient", "insufficient_stop"),
            ("insuf_ctr", "status_acc"), ("insuf_ctr", "joint"),
            ("suff_ctr", "status_acc"), ("suff_ctr", "joint")],
}
PRIMARY = {"FMT": ("format", "main"),
           "EVD": ("distractor", "acc_exact"),
           "REV": ("wc_attempt", "final_acc"),
           "ANS": ("insufficient", "paired_answerability")}

NO_ONSET = "no detected onset within tested range"


def seed_runs(curves, comp, dose):
    return [v for k, v in curves.items() if k.startswith(f"{comp}-{dose:04d}-")]


def endpoint_onset(curves, comp, cond, field):
    grid = BASE_GRID + [GRID_TOP[comp]]
    means, half_ranges, n_items = {}, {}, None
    for n in grid:
        runs = seed_runs(curves, comp, n)
        vals = [r[cond][field] for r in runs]
        means[n] = sum(vals) / len(vals)
        if n_items is None:
            n_items = runs[0][cond].get("n")
        if len(vals) >= 3:
            half_ranges[n] = (max(vals) - min(vals)) / 2
    placebo = means[0]
    ci_half = 1.96 * math.sqrt(max(placebo * (1 - placebo), 0.0) / n_items)
    tau = max(max(half_ranges.values()), ci_half)
    G = {n: means[n] - placebo for n in grid if n > 0}
    doses = [n for n in grid if n > 0]
    onset = None
    for i, n in enumerate(doses[:-1]):
        g, g_next = G[n], G[doses[i + 1]]
        if abs(g) > tau and (g > 0) == (g_next > 0):
            onset = n
            break
    return {
        "condition": cond, "metric": field, "n_items": n_items,
        "placebo_mean_3seed": round(placebo, 4),
        "anchor_seed_half_ranges": {str(k): round(v, 4) for k, v in half_ranges.items()},
        "ci_halfwidth_analytic_binomial": round(ci_half, 4),
        "tau": round(tau, 4),
        "G_vs_placebo": {str(n): round(g, 4) for n, g in G.items()},
        "onset": onset if onset is not None else NO_ONSET,
        "onset_direction": (None if onset is None
                            else ("+" if G[onset] > 0 else "-")),
    }


def main():
    curves = json.loads((LAW / "curves_e500_all.json").read_text())
    curves.update(json.loads((LAW / "curves_ans_e500.json").read_text()))

    per_comp = {}
    for comp, eps in ENDPOINT_SETS.items():
        rows = [endpoint_onset(curves, comp, c, f) for c, f in eps]
        onsets = [r["onset"] for r in rows if isinstance(r["onset"], int)]
        comp_onset = min(onsets) if onsets else None
        per_comp[comp] = {"endpoints": rows,
                          "component_onset": comp_onset,
                          "primary_endpoint": "%s.%s" % PRIMARY[comp]}

    def dose_entry(comp_key, k_component):
        pc = per_comp[comp_key]
        onset = pc["component_onset"]
        if onset is None:
            doses = {"placebo": 0, "mid": MID_NULL, "high": HIGH_K}
            rule = ("no endpoint reached onset -> null check {0, mid, high}, "
                    f"mid={MID_NULL} per D3")
        else:
            doses = {"placebo": 0, "onset": onset, "high": HIGH_K}
            rule = "onset = min over endpoint-set onsets (D2)"
        return {"k_pool": k_component, "reasoning_grid": comp_key,
                "doses": doses, "rule": rule,
                "primary_endpoint": pc["primary_endpoint"],
                "component_onset": onset if onset is not None else NO_ONSET,
                "endpoint_detail": pc["endpoints"]}

    table = {
        "_spec": "C-26 §五 Knowledge sparse doses {0, onset, high}; "
                 "onset per CONTRACT_ANALYSIS §4 frozen algorithm from the "
                 "Reasoning discovery curves",
        "_inputs": ["prescription/lawv1/curves_e500_all.json",
                    "prescription/lawv1/curves_ans_e500.json"],
        "_algorithm": {
            "G": "seed-mean s_e(component,n) - seed-mean s_e(dose-0 placebo, "
                 "same component grid, 3 seeds)",
            "tau": "max(max anchor-dose 3-seed half-range, 95% CI halfwidth at "
                   "placebo mean)",
            "onset": "smallest grid dose with |G(n)|>tau and sign(G(n))=="
                     "sign(G(n_next)); none -> literal no-onset",
            "high": HIGH_K, "mid_if_no_onset": MID_NULL,
        },
        "_deviations_self_certified": {
            "D1": "CI term is analytic binomial halfwidth, not item-family "
                  "bootstrap (per-item files absent from repo); advisor may "
                  "veto and demand the bootstrap recomputation",
            "D2": "component onset = min over its frozen endpoint set "
                  "(per-endpoint onsets all listed)",
            "D3": "mid for null-check = 240 (median of positive grid)",
            "D4": "ANS curves are 50-family scores (insufficient n=26) despite "
                  "the e500 filename; small-n flagged",
        },
        "components": {
            "k_clean_replay": {
                "k_pool": "k_clean_replay_2000", "reasoning_grid": None,
                "doses": {"placebo_arm": 2000},
                "rule": "carrier component: the 2000-row pure-replay arm IS "
                        "the shared dose-0 placebo of every K component grid; "
                        "no component-vs-placebo contrast exists, so no onset "
                        "is defined",
                "component_onset": None, "endpoint_detail": []},
            "k_format": dose_entry("FMT", "k_format_2000"),
            "k_evidence": dose_entry("EVD", "k_evidence_2000"),
            "k_revision": dose_entry("REV", "k_revision_2000"),
            "k_answerability": dose_entry("ANS", "k_answerability_2000"),
        },
    }
    OUT.write_text(json.dumps(table, indent=2, ensure_ascii=False) + "\n")
    brief = {k: v["doses"] for k, v in table["components"].items()}
    print(json.dumps(brief, indent=2))


if __name__ == "__main__":
    main()
