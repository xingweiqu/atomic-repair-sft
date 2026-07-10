#!/usr/bin/env python3
"""B2-0(a) flip-overlap audit (Batch-1 ruling ②a, zero-compute).

Question: are the items rescued (defining-probe flips fail->pass) the SAME set
across arms/seeds, or does each run rescue a different random subset?
  same set   -> shallow deterministic repair (bucket has a fixable core)
  different  -> the bucket is measuring dice; Fig-1 prevalence needs an
                instability-discount footnote.

Per bucket: rescued-set Jaccard (i) within-arm across seeds (A1, C),
(ii) across arms at s42 (incl. placebo), each vs the chance baseline for
independent random rescue at the observed rates: J_rand = ab/(a+b-ab).
Also: stable core = items rescued by every mixed arm AND the placebo.
"""
from __future__ import annotations

import glob
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from loop3.score_batch1 import load_pre_signatures, arm_signatures, DEFPROBE  # noqa: E402
from probes.profile_classify import classify  # noqa: E402

EVAL = ROOT / "loop3/eval"


def rescued_sets():
    pre, meta = load_pre_signatures()
    buckets = defaultdict(list)
    for bid, s in pre.items():
        if meta.get(bid) != "gsm":
            continue
        for lab in classify(s):
            if lab in DEFPROBE:
                buckets[lab].append(bid)
    runs = {}
    for f in sorted(glob.glob(str(EVAL / "full_l3_*.jsonl"))):
        tag = Path(f).stem.replace("full_l3_", "")
        sig, _ = arm_signatures(f)
        per = {}
        for lab, ids in buckets.items():
            resc, denom = set(), set()
            for bid in ids:
                s = sig.get(bid)
                if not s:
                    continue
                probes = [p for p in DEFPROBE[lab] if pre[bid].get(p) == 0]
                if not probes:
                    continue
                denom.add(bid)
                if all(s.get(p) == 1 for p in probes):
                    resc.add(bid)
            per[lab] = (resc, denom)
        runs[tag] = per
    return runs, buckets


def jac(a, b):
    return len(a & b) / len(a | b) if (a | b) else float("nan")


def jrand(a, b, denom):
    ra, rb = len(a) / len(denom), len(b) / len(denom)
    return ra * rb / (ra + rb - ra * rb) if (ra + rb - ra * rb) else float("nan")


def main():
    runs, buckets = rescued_sets()
    labs = ["conduct", "format", "phrasing", "scaffold"]
    report = {}
    print("=== within-arm, across seeds (J_obs / J_rand) ===")
    for arm in ("A1", "C"):
        seeds = [t for t in runs if t.startswith(arm + "_s")]
        for lab in labs:
            js, jr = [], []
            for t1, t2 in itertools.combinations(seeds, 2):
                a, da = runs[t1][lab]
                b, db = runs[t2][lab]
                d = da & db
                js.append(jac(a & d, b & d))
                jr.append(jrand(a & d, b & d, d))
            if js:
                report[f"within_{arm}_{lab}"] = (sum(js) / len(js), sum(jr) / len(jr))
                print(f"{arm:3} {lab:9} J_obs {sum(js)/len(js):.2f}  J_rand {sum(jr)/len(jr):.2f}")
    print("\n=== across arms @ s42 (J_obs / J_rand) ===")
    arms42 = ["A1_s42_e4", "B_s42_e2", "D_s42_e2", "C_s42_e2", "cleanreplay_s42_e4"]
    for lab in labs:
        for t1, t2 in itertools.combinations(arms42, 2):
            a, da = runs[t1][lab]
            b, db = runs[t2][lab]
            d = da & db
            jo, jr_ = jac(a & d, b & d), jrand(a & d, b & d, d)
            report[f"cross_{t1.split('_')[0]}x{t2.split('_')[0]}_{lab}"] = (jo, jr_)
            print(f"{lab:9} {t1.split('_')[0]:>11} x {t2.split('_')[0]:11} J_obs {jo:.2f}  J_rand {jr_:.2f}")
    print("\n=== stable core (rescued by ALL of A1/B/D/C + placebo, s42) ===")
    core = {}
    for lab in labs:
        sets = [runs[t][lab][0] for t in arms42]
        denoms = [runs[t][lab][1] for t in arms42]
        d = set.intersection(*denoms)
        c = set.intersection(*[s & d for s in sets])
        u = set.union(*[s & d for s in sets])
        core[lab] = dict(core=len(c), union=len(u), denom=len(d))
        print(f"{lab:9} core {len(c):3}/{len(d)} ({len(c)/len(d):.0%})  union {len(u)}/{len(d)} ({len(u)/len(d):.0%})")
    (EVAL / "flip_overlap.json").write_text(json.dumps(
        {"pairs": {k: v for k, v in report.items()}, "stable_core": core}, indent=1))


if __name__ == "__main__":
    main()
