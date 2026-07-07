"""Loop 1 ledger builder — four-layer gain accounting (frozen protocol:
qc/INSTRUCTION_v1.md §1 + qc/LOOP0_RULINGS.md C-1/C-2/C-3, R-1/R-2/R-3).

Per row = (ckpt, eval cell)  [R-3]:
  L0  d_raw    = lenient acc(run) - lenient acc(floor)          (full items)
  L1  d_strict ; F_judge = d_raw - d_strict                      (C-2 F_judge)
  L2  d_clean  = strict on leak_any==0 items ; M = d_strict - d_clean
      (n_clean==0 -> M = d_strict recorded as UPPER BOUND, L3 skipped)
  L3  scope = clean AND strict-parsed-by-both (C-1, symmetric) AND has-w (R-1):
      per endpoint  final = resist × ability|resist  (own denominators -> exact identity)
      D = Δresist·(a0+a1)/2 ;  A = Δability·(r0+r1)/2            (Shapley)
      F_parse = d_clean - d_cleanP                                (C-1: unparsed -> F)
      ND      = strict delta of clean∩P items WITHOUT a (g,w) pair (keep/abstain cells;
                named per R-1 instead of faking a pseudo-resist)
  residual = d_raw - (F_judge + F_parse + M + D + A + ND)  -> ~0 by construction;
             non-zero flags a pipeline bug, not a story.
  F_floor (C-2 memo) = d_strict(vs underfit floor) - d_strict(vs convergent floor).
  A-claim gate (C-3): pairwise-matched Δability + n_matched; n_matched<50 -> lowpower.

Outputs: ledger/master_ledger.csv, ledger/inventory.md, ledger/fig_ledger.png.
"""
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ledger.judge import load_items, score_run  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
BP = "scenario-repair-b-prime"


# ---------------- loading ----------------

def git_text(branch, path):
    r = subprocess.run(["git", "show", f"{branch}:{path}"], cwd=ROOT,
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def load_eval(branch, path):
    if branch is None:
        return load_items(ROOT / path)
    return [json.loads(l) for l in git_text(branch, path).splitlines() if l.strip()]


def load_pred(branch, path):
    t = git_text(branch, path) if branch else None
    if branch is None:
        p = ROOT / path
        if not p.exists():
            return None
        t = p.read_text()
    if t is None:
        return None
    return [json.loads(l).get("predict", "") for l in t.splitlines() if l.strip()]


def read_epochs(branch, cfg_candidates):
    for c in cfg_candidates:
        t = git_text(branch or "HEAD", c)
        if t:
            m = re.search(r"num_train_epochs:\s*([\d.]+)", t)
            if m:
                return int(float(m.group(1)))
    return ""


# ---------------- registry (A2 inventory made executable) ----------------

OPS6 = ["override_wrong_claim", "verify_bridge", "verify_step", "recompute",
        "use_provided_support", "retrieve_or_abstain"]
OPS4_V4 = ["verify_step", "override_wrong_claim", "recompute", "retrieve_or_abstain"]
OPS4_V5 = ["override_wrong_claim", "verify_bridge", "use_provided_support", "retrieve_or_abstain"]


def dom_registry():
    """domain -> dict(eval, cellfield, floor, underfit, runs{name:(branch,path)}, cfg)"""
    def pd(base, run, branch=None):
        return (branch, f"{base}/predict_{run}/generated_predictions.jsonl")

    reg = {}
    reg["v2"] = dict(
        eval=(None, "data_v2/repair_eval.jsonl"), cellfield="cell",
        floor="factonly", underfit=None,
        runs={r: pd("data_v2/predict_outputs", r) for r in
              ["factonly", "fc", "fs", "zs_direct", "zs_cot"]},
        refs=["zs_direct", "zs_cot"],
        cfg={"fc": ["configs/v2/fact_then_cot_sft.yaml"],
             "fs": ["configs/v2/fact_then_skillcot_sft.yaml"],
             "factonly": ["configs/v2/factonly_sft.yaml", "configs/v2/inject_sft.yaml"]})
    reg["v2_1"] = dict(
        eval=(None, "data_v2_1/repair_eval.jsonl"), cellfield="cell",
        # R-8 (LOOP1_RULINGS): knowledge-floor predict on the v2.1 eval landed 2026-07-03
        # (server batch-1) -> the seven v2.1 rows move from absolute-only to fine ledger.
        floor="factonly_on_v21", underfit=None,
        runs={r: pd("data_v2_1/predict_outputs", r) for r in
              ["factonly_on_v21", "actionized", "cot_fixed", "decision", "randomskill",
               "skillcot_fixed", "prefix_gold", "prefix_wrong"]},
        refs=[], cfg={})
    reg["v3"] = dict(
        eval=(None, "data_v3/repair_eval.jsonl"), cellfield="policy",
        floor="factonly", underfit=None,
        runs={**{r: pd("data_v3/predict_outputs", r) for r in
                 ["factonly", "actionized_full", "cot"]
                 + [f"targeted_{o}" for o in OPS6] + [f"random_{o}" for o in OPS6]
                 + [f"wrongtarget_{o}" for o in OPS6]
                 + [f"cumulative_M{i}" for i in range(1, 7)]}},
        refs=[],
        cfg={r: [f"configs/v3/{r}_sft.yaml"] for r in
             ["actionized_full", "cot"] + [f"targeted_{o}" for o in OPS6]})
    reg["v3_1"] = dict(
        eval=(None, "data_v3_1/repair_eval.jsonl"), cellfield="policy",
        floor="scaffold_conv", underfit="scaffold_only",
        runs={**{r: pd("data_v3_1/predict_outputs", r) for r in
                 ["factonly", "scaffold_only", "actionized_full"]
                 + [f"targeted_{o}" for o in OPS6] + [f"random_{o}" for o in OPS6]
                 + [f"wrongtarget_{o}" for o in OPS6]},
              "scaffold_conv": pd("data_v3_1/predict_outputs", "scaffold_conv", BP)},
        refs=[],
        cfg={"scaffold_conv": [f"configs/v3_1/scaffold_conv_sft.yaml"],
             "scaffold_only": ["configs/v3_1/scaffold_only_sft.yaml"],
             **{f"targeted_{o}": [f"configs/v3_1/targeted_{o}_sft.yaml"] for o in OPS6}})
    reg["v4"] = dict(
        eval=(None, "data_v4/repair_eval.jsonl"), cellfield="policy",
        # R-17 (LOOP1_5_RULINGS_BATCH2): canonical floor = scaffold_conv e8 (the ridge
        # point: parse 1.00, json_bleed 0%, plain-genre acc == pre-repair). The round-1
        # 30-epoch floor is PAST the ridge (31% bleed, plain acc 49%) and becomes a
        # measured run; the pre-R-17 ledger is archived as archive_master_ledger_v4floor_e30.csv.
        floor="scaffold_conv_e8", underfit="scaffold_only",
        runs={**{r: pd("data_v4/predict_outputs", r) for r in
                 ["scaffold_only", "scaffold_conv", "actionized_full", "diagnosis_base"]
                 + [f"targeted_{o}" for o in OPS4_V4] + [f"random_{o}" for o in OPS4_V4]
                 + [f"wrongtarget_{o}" for o in OPS4_V4]},
              "scaffold_conv_e8": pd("data_v4/epoch_sweep_predict", "scaffold_conv_e8")},
        refs=["diagnosis_base"],
        cfg={"scaffold_conv": ["configs/v4/scaffold_conv_sft.yaml"],
             "scaffold_conv_e8": ["configs/v4/epoch_sweep/scaffold_conv_e8_sft.yaml"],
             "scaffold_only": ["configs/v4/scaffold_only_sft.yaml"],
             **{f"targeted_{o}": [f"configs/v4/targeted_{o}_sft.yaml"] for o in OPS4_V4}})
    reg["v5"] = dict(
        eval=(BP, "data_v5/repair_eval.jsonl"), cellfield="policy",
        floor="scaffold_conv", underfit=None,
        runs={r: pd("data_v5/predict_outputs", r, BP) for r in
              ["scaffold_conv", "actionized_full", "diagnosis_base"]
              + [f"targeted_{o}" for o in OPS4_V5] + [f"random_{o}" for o in OPS4_V5]
              + [f"wrongtarget_{o}" for o in OPS4_V5]},
        refs=["diagnosis_base"],
        cfg={r: [f"configs/v5/{r}_sft.yaml"] for r in
             ["scaffold_conv", "actionized_full"] + [f"targeted_{o}" for o in OPS4_V5]},
        cfg_branch=BP)
    return reg


# ---------------- accounting ----------------

def acc(vs):
    return sum(vs) / len(vs) if vs else None


def cell_account(items, vf, vt, leaks, idx):
    """One ledger row body for item subset idx: floor verdicts vf, target verdicts vt."""
    n = len(idx)
    raw_f = acc([vf[i]["correct_lenient"] for i in idx])
    raw_t = acc([vt[i]["correct_lenient"] for i in idx])
    st_f = acc([vf[i]["correct_strict"] for i in idx])
    st_t = acc([vt[i]["correct_strict"] for i in idx])
    d_raw, d_strict = raw_t - raw_f, st_t - st_f
    F_judge = d_raw - d_strict

    clean = [i for i in idx if leaks[i] == 0]
    n_clean = len(clean)
    out = dict(n=n, n_clean=n_clean, d_raw=d_raw, F_judge=F_judge,
               parse_rate_t=acc([vt[i]["parsed_strict"] for i in idx]),
               abs_strict_t=st_t, abs_strict_f=st_f,
               M=None, F_parse=None, D=None, A=None, ND=None, residual=None,
               n_P=None, n_w=None, r0=None, r1=None, a0=None, a1=None,
               d_a_matched=None, n_matched=None, lowpower="", w_source="", note="")
    if n_clean == 0:
        out["M"] = d_strict
        out["note"] = "M=UPPER BOUND (no clean items); D/A undefined here"
        out["residual"] = round(d_raw - F_judge - d_strict, 6)
        return out
    dc_f = acc([vf[i]["correct_strict"] for i in clean])
    dc_t = acc([vt[i]["correct_strict"] for i in clean])
    d_clean = dc_t - dc_f
    out["M"] = d_strict - d_clean

    P = [i for i in clean if vf[i]["parsed_strict"] and vt[i]["parsed_strict"]]
    out["n_P"] = len(P)
    if not P:
        out["F_parse"] = d_clean
        out["note"] = "no both-parsed clean items; F_parse=d_clean"
        out["residual"] = round(d_raw - F_judge - out["M"] - out["F_parse"], 6)
        return out
    dP_f = acc([vf[i]["correct_strict"] for i in P])
    dP_t = acc([vt[i]["correct_strict"] for i in P])
    out["F_parse"] = (d_clean - (dP_t - dP_f) * len(P) / n_clean
                      - (0 if len(P) == n_clean else 0))
    # exact: d_clean = (sum over P + sum over clean\P)/n_clean ; charge clean\P wholly to F
    sP_f = sum(vf[i]["correct_strict"] for i in P)
    sP_t = sum(vt[i]["correct_strict"] for i in P)
    sNP_f = sum(vf[i]["correct_strict"] for i in clean if i not in set(P))
    sNP_t = sum(vt[i]["correct_strict"] for i in clean if i not in set(P))
    out["F_parse"] = (sNP_t - sNP_f) / n_clean

    W = [i for i in P if vf[i]["resist"] is not None and vt[i]["resist"] is not None]
    NW = [i for i in P if i not in set(W)]
    out["n_w"] = len(W)
    ws = {items[i].get("__wsrc") for i in W}
    out["w_source"] = "/".join(sorted(x for x in ws if x)) if ws else ""
    D = A = 0.0
    if W:
        r0 = acc([vf[i]["resist"] for i in W])
        r1 = acc([vt[i]["resist"] for i in W])
        a0 = acc([vf[i]["ability"] for i in W if vf[i]["resist"] == 1]) or 0.0
        a1 = acc([vt[i]["ability"] for i in W if vt[i]["resist"] == 1]) or 0.0
        D = (r1 - r0) * (a0 + a1) / 2 * len(W) / n_clean
        A = (a1 - a0) * (r0 + r1) / 2 * len(W) / n_clean
        out.update(r0=r0, r1=r1, a0=a0, a1=a1)
        matched = [i for i in W if vf[i]["resist"] == 1 and vt[i]["resist"] == 1]
        out["n_matched"] = len(matched)
        if matched:
            am_f = acc([vf[i]["ability"] for i in matched])
            am_t = acc([vt[i]["ability"] for i in matched])
            out["d_a_matched"] = am_t - am_f
        out["lowpower"] = "LOWPOWER" if len(matched) < 50 else ""
    out["D"], out["A"] = D, A
    out["ND"] = (sum(vt[i]["correct_strict"] for i in NW)
                 - sum(vf[i]["correct_strict"] for i in NW)) / n_clean
    out["residual"] = round(out["d_raw"] - out["F_judge"] - out["M"] - out["F_parse"]
                            - out["D"] - out["A"] - out["ND"], 6)
    return out


# R-4 (C-4a, frozen by qc/LOOP1_RULINGS.md): per-domain pre-repair reference run.
# Any paper claim about ability injected/spent may ONLY cite the pre-repair columns.
PREREPAIR = {"v4": "diagnosis_base", "v5": "diagnosis_base",
             "v3": "factonly", "v3_1": "factonly", "v2": "factonly",
             "v2_1": "factonly_on_v21"}


def prerepair_matched(vp, vt, idx):
    """Pairwise matched Δability vs the pre-repair reference (R-4)."""
    m = [i for i in idx if vp[i]["resist"] == 1 and vt[i]["resist"] == 1
         and vp[i]["parsed_strict"] and vt[i]["parsed_strict"]]
    if not m:
        return None, 0
    ap = sum(vp[i]["ability"] for i in m) / len(m)
    at = sum(vt[i]["ability"] for i in m) / len(m)
    return at - ap, len(m)


def main():
    reg = dom_registry()
    rows, inventory = [], []

    for dom, R in reg.items():
        ev_branch, ev_path = R["eval"]
        items = load_eval(ev_branch, ev_path)
        # leak flags
        lf = {r["id"]: r["leak_any"] for r in
              (json.loads(l) for l in (ROOT / f"ledger/leak_flags_{dom}.jsonl").open())}
        leaks = [lf[it["id"]] for it in items]
        # annotate w_source once
        from ledger.judge import wrong_value
        for it in items:
            it["__wsrc"] = wrong_value(it, dom)[1]

        cellf = R["cellfield"]
        cells = sorted({it[cellf] for it in items})
        # score all runs
        scored = {}
        for run, (br, path) in R["runs"].items():
            preds = load_pred(br, path)
            if preds is None or len(preds) != len(items):
                inventory.append((dom, run, br or "gain-accounting-v1", path,
                                  0 if preds is None else len(preds), "MISSING/MISALIGNED"))
                continue
            scored[run] = score_run(items, preds, dom)
            inventory.append((dom, run, br or "gain-accounting-v1", path, len(preds), "ok"))

        floor = R["floor"]
        if floor not in scored:
            floor = None
        for run, vt in scored.items():
            if run == floor:
                continue
            ep = read_epochs(R.get("cfg_branch"), R["cfg"].get(run, []))
            is_ref = run in R.get("refs", [])
            for cell, idx in [("ALL", list(range(len(items))))] + [
                    (c, [i for i, it in enumerate(items) if it[cellf] == c]) for c in cells]:
                base = dict(run_id=f"{dom}:{run}:{cell}", domain=dom, ckpt=run, cell=cell,
                            floor=floor or "NA", epochs=ep,
                            grey="REF" if is_ref else "", F_floor="")
                if floor is None or is_ref:
                    vf = scored.get(floor) if floor else None
                    st = acc([vt[i]["correct_strict"] for i in idx])
                    ln = acc([vt[i]["correct_lenient"] for i in idx])
                    base.update(n=len(idx), abs_strict_t=st, d_raw="",
                                note="no floor on this eval; absolute only" if floor is None
                                else "pre-repair reference; absolute only",
                                parse_rate_t=acc([vt[i]["parsed_strict"] for i in idx]))
                    rows.append(base)
                    continue
                body = cell_account(items, scored[floor], vt, leaks, idx)
                # R-4: ability-claim column vs pre-repair reference
                pr = PREREPAIR.get(dom)
                if pr and pr in scored and pr != run:
                    d_pre, n_pre = prerepair_matched(scored[pr], vt, idx)
                    base["d_a_prerepair"] = d_pre
                    base["n_matched_pre"] = n_pre
                    base["lowpower_pre"] = "LOWPOWER" if n_pre < 50 else ""
                # C-2 memo: underfit-floor baseline difference
                uf = R.get("underfit")
                if uf and uf in scored and uf != run:
                    st_u = acc([scored[uf][i]["correct_strict"] for i in idx])
                    base["F_floor"] = (body["abs_strict_t"] - st_u) - \
                                      (body["abs_strict_t"] - body["abs_strict_f"])
                base.update(body)
                rows.append(base)

    # ---------------- C-5.1: construct column + the K row ----------------
    # All repair evals claim to measure PROCEDURE (answer-update behaviour), so their
    # exposure-driven gain stays M. The v2 fact-injection eval claims RECALL of trained
    # content -> its gain books to K (legitimate), not M. See qc/LOOP1_5_RULINGS_C5.md.
    for r in rows:
        r.setdefault("construct", "procedure")
        r.setdefault("K", "")

    def inj_score(path):
        recs = [json.loads(l) for l in (ROOT / path).open() if l.strip()]
        def norm(s):
            return re.sub(r"\s+", " ", (s or "").strip().lower())
        return [int(norm(r["label"]) in norm(r["predict"])) for r in recs]

    ib = inj_score("data_v2/predict_outputs/predict_inject_base/generated_predictions.jsonl")
    if_ = inj_score("data_v2/predict_outputs/predict_inject_floor/generated_predictions.jsonl")
    d = sum(if_) / len(if_) - sum(ib) / len(ib)
    rows.append(dict(
        run_id="v2_inject:inject_floor:ALL", domain="v2_inject", ckpt="inject_floor",
        cell="ALL", n=len(if_), floor="inject_base(zero-shot pre-repair)",
        epochs=read_epochs(None, ["configs/v2/inject_sft.yaml"]),
        d_raw=d, F_judge=0.0, M=0.0, K=d, construct="recall",
        abs_strict_t=sum(if_) / len(if_), abs_strict_f=sum(ib) / len(ib),
        grey="", F_floor="",
        note="C-5.1 canonical K row: construct=recall (fact-QA on the injected corpus); "
             "exposure IS the claim -> gain books to K, not M. Judge: normalised label "
             "containment (plain-text QA, not JSON)."))
    inventory.append(("v2_inject", "inject_base/floor", "gain-accounting-v1",
                      "data_v2/predict_outputs/predict_inject_{base,floor}", len(if_),
                      "ok (K row, construct=recall)"))

    # ---------------- write csv ----------------
    cols = ["run_id", "domain", "ckpt", "cell", "n", "floor", "epochs", "d_raw",
            "F_judge", "K", "M", "F_parse", "D", "A_delivered", "A_latent", "ND", "residual", "F_floor",
            "n_clean", "n_P", "n_w", "r0", "r1", "a0", "a1",
            "d_a_matched", "n_matched", "lowpower",
            "d_a_prerepair", "n_matched_pre", "lowpower_pre", "w_source", "construct",
            "abs_strict_t", "abs_strict_f", "parse_rate_t", "grey", "note"]
    with (ROOT / "ledger/master_ledger.csv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            # R-10 (LOOP1_5_RULINGS): A_delivered = Shapley A in the repair genre vs the
            # convergent floor (deployment readout). A_latent (plain-genre, vs pre-repair,
            # the ability-claim column) is populated only where dual-genre evals exist
            # (R-7); T4 supplies the v4 floor-level evidence — see LEDGER_REPORT.
            r["A_delivered"] = r.pop("A", None)
            r.setdefault("A_latent", "")
            for k in cols:
                v = r.get(k)
                if isinstance(v, float):
                    r[k] = round(v, 4)
            w.writerow(r)

    # ---------------- inventory ----------------
    inv = ["# ledger/inventory.md — run inventory (Loop 1)", "",
           "| domain | run | branch | predictions | rows | status |", "|---|---|---|---|---|---|"]
    for dom, run, br, path, n, st in inventory:
        inv.append(f"| {dom} | {run} | {br} | {path} | {n} | {st} |")
    inv += ["", "## 粗账/灰名单(不入主图)",
            "- v0 `output/qwen3_8b_repair_full_predict` (550): no floor predict on its eval -> absolute only.",
            "- v1 `output/qwen3_8b_repair_v1_{A,B,C,D}_predict` (550): **misfired, lineage unverified**"
            " (D-1 ruling; Provenance artifact). Excluded from all aggregates.",
            "- v2 `predict_inject_base/floor`: fact-QA gates (different eval), not repair runs.",
            "- v4 `predict_transfer_*`: separate un-perturbed eval; enters §6 evidence, not this ledger.",
            "- epoch-sweep `_e{N}` points: configs ready, server not yet run (pending)."]
    (ROOT / "ledger/inventory.md").write_text("\n".join(inv) + "\n")

    # ---------------- fig ----------------
    make_fig(rows)
    n_rows = len([r for r in rows if r.get("d_raw") != ""])
    print(f"ledger rows: {len(rows)} (decomposed: {n_rows}); csv + inventory + fig written")
    bad = [r for r in rows if isinstance(r.get("residual"), float) and abs(r["residual"]) > 0.03]
    print("residual>3pp rows:", len(bad))
    for r in bad[:10]:
        print("  ", r["run_id"], r["residual"], r.get("note"))


def make_fig(rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    sel = [r for r in rows if r["cell"] == "ALL" and r.get("d_raw") != ""
           and not r.get("grey") and not r["ckpt"].startswith(("random_", "wrongtarget_",
                                                               "cumulative_"))]
    sel.sort(key=lambda r: (r["domain"], r["ckpt"]))
    labels = [f"{r['domain']}:{r['ckpt']}" for r in sel]
    chans = ["F_judge", "F_parse", "K", "M", "D", "A", "ND"]  # C-10: K/M split colours; A -> A_delivered
    colors = {"F_judge": "#f4a261", "F_parse": "#e9c46a", "K": "#4c9f70", "M": "#e76f51",
              "D": "#2a9d8f", "A": "#264653", "ND": "#bdbdbd"}
    legend_names = {"A": "A_delivered (in-genre)", "K": "K (legit content, construct=recall)",
                    "M": "M (contamination, construct=procedure)"}
    fig, ax = plt.subplots(figsize=(13, 0.42 * len(sel) + 2))
    y = np.arange(len(sel))
    for r_i, r in enumerate(sel):
        pos = neg = 0.0
        for c in chans:
            v = r.get(c)
            v = 0.0 if not isinstance(v, float) else v
            if v >= 0:
                ax.barh(r_i, v, left=pos, color=colors[c], height=0.72)
                pos += v
            else:
                ax.barh(r_i, v, left=neg, color=colors[c], height=0.72)
                neg += v
        ax.plot([r["d_raw"]], [r_i], "k|", markersize=14)
    ax.set_yticks(y, labels, fontsize=8)
    ax.invert_yaxis()
    ax.axvline(0, color="k", lw=0.6)
    ax.set_xlabel("gain vs canonical floor (fraction; black tick = Δfinal_raw)")
    ax.set_title("Gain accounting — F(judge/parse) + M + D + A + ND per run (cell=ALL)")
    handles = [plt.Rectangle((0, 0), 1, 1, color=colors[c]) for c in chans]
    ax.legend(handles, [legend_names.get(c, c) for c in chans], loc="lower right", fontsize=8, ncol=3)
    fig.tight_layout()
    fig.savefig(ROOT / "ledger/fig_ledger.png", dpi=150)


if __name__ == "__main__":
    main()
