#!/usr/bin/env python3
"""Batch-2 verdict debts, zero-compute (qc/BATCH2_RULINGS_verdict.md).

  0c       discrimination recomputed on the stable-failure core: bucket items the
           PLACEBO (cleanreplay@ridge) does NOT rescue — does any arm separate there?
  adopt    plain-genre adopt subset: pre-repair W probes answered with the planted
           value; rescored per arm ridge (correct/adopt/derail/mute) — mechanism routing.
  abstain  component shares vs repair-genre retrieve_or_abstain acc (register only).
"""
from __future__ import annotations

import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm  # noqa: E402
from probes.profile_classify import pf_plain, pf_json, classify  # noqa: E402
from loop3.score_batch1 import load_pre_signatures, arm_signatures, DEFPROBE  # noqa: E402

EVAL = ROOT / "loop3/eval"


def pre_raw_w():
    """pre-repair W1/W2 raw rows (need w field for adopt classification)."""
    excluded = set(json.loads((ROOT / "probes/data/pool_filter.json").read_text())["excluded"])
    rows = defaultdict(dict)
    for f in sorted(glob.glob(str(ROOT / "probes/out/answers.shard*.jsonl"))) + \
             sorted(glob.glob(str(ROOT / "probes/out2/**/answers.shard*.jsonl"), recursive=True)):
        for l in Path(f).open():
            r = json.loads(l)
            if r["probe"] not in ("W1", "W2") or r["base_id"] in excluded or r["pool"] != "gsm":
                continue
            got = pf_plain(r["predict"])
            kind = ("mute" if got is None else
                    "adopt" if r.get("w") and numnorm(got) == numnorm(r["w"]) else
                    "ok" if numnorm(got) == numnorm(r["gold"]) else "derail")
            rows[r["base_id"]][r["probe"]] = dict(kind=kind, w=r.get("w"), gold=r["gold"])
    return rows


def arm_files():
    return sorted(glob.glob(str(EVAL / "full_l3_*.jsonl")))


def main():
    pre, meta = load_pre_signatures()
    buckets = defaultdict(list)
    for bid, s in pre.items():
        if meta.get(bid) != "gsm":
            continue
        for lab in classify(s):
            if lab in DEFPROBE:
                buckets[lab].append(bid)
    arm_sigs = {Path(f).stem.replace("full_l3_", ""): arm_signatures(f)[0] for f in arm_files()}

    # ---- 0c: stable-failure core = defining probes still failed under placebo ----
    def rescued(sig, bid, lab):
        probes = [p for p in DEFPROBE[lab] if pre[bid].get(p) == 0]
        return bool(probes) and all(sig.get(bid, {}).get(p) == 1 for p in probes)

    placebo = arm_sigs["cleanreplay_s42_e4"]
    print("=== 0c: REd on placebo-UNFIXABLE remainder (stable failure core) ===")
    labs = ["conduct", "format", "phrasing", "scaffold"]
    hard = {lab: [b for b in buckets[lab]
                  if any(pre[b].get(p) == 0 for p in DEFPROBE[lab]) and not rescued(placebo, b, lab)]
            for lab in labs}
    print("core sizes:", {k: len(v) for k, v in hard.items()})
    out0c = {}
    print(f"{'arm':22}" + "".join(f"{l[:8]:>10}" for l in labs))
    for tag, sig in sorted(arm_sigs.items()):
        row = {}
        for lab in labs:
            ids = hard[lab]
            got = [rescued(sig, b, lab) for b in ids if sig.get(b)]
            row[lab] = round(sum(got) / len(got), 3) if got else None
        out0c[tag] = row
        print(f"{tag:22}" + "".join(f"{row[l]:>10.0%}" if row[l] is not None else f"{'—':>10}" for l in labs))

    # ---- adopt subset ----
    print("\n=== adopt subset: pre-repair W probes that ADOPTED the planted value ===")
    praw = pre_raw_w()
    adopt_items = [(bid, p) for bid, d in praw.items() for p, v in d.items() if v["kind"] == "adopt"]
    print(f"n adopt probe-instances = {len(adopt_items)} (items: {len({b for b,_ in adopt_items})})")
    outad = {}
    print(f"{'arm':22}{'correct':>9}{'adopt':>7}{'derail':>8}{'mute':>6}")
    for f in arm_files():
        tag = Path(f).stem.replace("full_l3_", "")
        byid = defaultdict(dict)
        for l in Path(f).open():
            r = json.loads(l)
            if r["probe"] in ("W1", "W2"):
                byid[r["base_id"]][r["probe"]] = r
        cnt = defaultdict(int)
        for bid, p in adopt_items:
            r = byid.get(bid, {}).get(p)
            if not r:
                continue
            got = pf_plain(r["predict"])
            k = ("mute" if got is None else
                 "adopt" if r.get("w") and numnorm(got) == numnorm(r["w"]) else
                 "correct" if numnorm(got) == numnorm(r["gold"]) else "derail")
            cnt[k] += 1
        n = sum(cnt.values()) or 1
        outad[tag] = {k: round(v / n, 3) for k, v in cnt.items()}
        print(f"{tag:22}" + "".join(f"{cnt[k]/n:>{w}.0%}" for k, w in
                                    [("correct", 9), ("adopt", 7), ("derail", 8), ("mute", 6)]))

    # ---- abstain vs composition (register only) ----
    print("\n=== abstain: component share vs retrieve_or_abstain acc (Pearson; register only) ===")
    comp = {  # item-share composition per arm family
        "A1": dict(conduct=.40, format=.36, phrasing=.16, scaffold=.05, rule=.02),
        "B": dict(conduct=.2, format=.2, phrasing=.2, scaffold=.2, rule=.2),
        "D": dict(conduct=.02, format=.05, phrasing=.16, scaffold=.36, rule=.40),
        "C": {}, "cleanreplay": {},
        "single_conduct": dict(conduct=1), "single_phrasing": dict(phrasing=1),
        "single_rule": dict(rule=1), "single_scaffold": dict(scaffold=1),
        "single_drills": dict(drills=1),
        "fmt10": dict(format=.10), "fmt20": dict(format=.20), "fmt36": dict(format=.36),
        "drl10": dict(drills=.10), "drl25": dict(drills=.25),
        "scafffmt": dict(scaffold=.5, format=.5),
    }
    gs = json.loads((EVAL / "genre_scores.json").read_text())
    pts = []
    for k, v in gs.items():
        fam = k.split("_s4")[0]
        if fam in comp:
            pts.append((fam, comp[fam], v["per_policy"]["retrieve_or_abstain"]["acc"]))
    comps = ["conduct", "format", "phrasing", "scaffold", "rule", "drills"]
    import statistics
    corr = {}
    ys = [y for _, _, y in pts]
    for c in comps:
        xs = [cc.get(c, 0.0) for _, cc, _ in pts]
        if statistics.pstdev(xs) == 0:
            continue
        mx, my = statistics.mean(xs), statistics.mean(ys)
        cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(xs)
        corr[c] = round(cov / (statistics.pstdev(xs) * statistics.pstdev(ys)), 3)
    # n_components as a crude diversity axis
    xs = [len(cc) for _, cc, _ in pts]
    mx, my = statistics.mean(xs), statistics.mean(ys)
    cov = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / len(xs)
    corr["n_components"] = round(cov / (statistics.pstdev(xs) * statistics.pstdev(ys)), 3)
    print("points:", [(f, y) for f, _, y in sorted(pts, key=lambda t: -t[2])])
    print("pearson r:", corr)

    (EVAL / "debts_b2.json").write_text(json.dumps(
        {"core0c": out0c, "core_sizes": {k: len(v) for k, v in hard.items()},
         "adopt": outad, "n_adopt": len(adopt_items), "abstain_corr": corr}, indent=1))


if __name__ == "__main__":
    main()
