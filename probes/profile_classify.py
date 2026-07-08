#!/usr/bin/env python3
"""Loop 2 profile classifier — frozen rules from prereg/PREREG_profile.md §2, verbatim.
HELD until construct-audit sign-off (>=70%/type); running it earlier prints signatures
only if --pre-audit is passed explicitly (provisional, not for the profile table).

Signature per base item: dict probe->0/1/None(no probe). Classification (frozen):
  scaffold  = !O and S==1
  rule      = !O and R==1 and S!=1
  phrasing  = O xor P  (inconsistency)
  conduct   = O==1 and (W1==0 or W2==0)
  local_exec= !O and S==0 and R==0 and C==1
  format    = only F differs from O
  unresolved= all available probes 0
  mixed     = signature matches none of the above (explicit bucket, per prereg grey rule)
Outputs profile/GSM_profile.md: prevalence per pool with Wilson CI, overlap matrix,
answered rates; steering-triage column filled by a later d_plain@α8 pass (separate job).
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TYPES = ["O", "P", "S", "R", "C", "W1", "W2", "F"]


def pf_plain(t):
    m = re.findall(r"final answer is\s*(-?[\d,\.]+)", t or "", re.I)
    return m[-1].replace(",", "").rstrip(".") if m else None


def pf_json(t):
    m = re.findall(r'"answer"\s*:\s*"?(-?[\d,\.]+)', t or "")
    return m[-1].replace(",", "").rstrip(".") if m else None


import sys as _sys
_sys.path.insert(0, str(ROOT))
from textlint import numnorm  # shared guarded normaliser (9e999 family, 3rd strike)


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (p, max(0, c - h), min(1, c + h))


def load_answers():
    sig = defaultdict(dict)   # base_id -> probe -> 0/1
    meta = {}
    excluded = set()
    pfj = ROOT / "probes/data/pool_filter.json"
    if pfj.exists():
        excluded = set(json.loads(pfj.read_text())["excluded"])
    # out2 (repair-pass reruns) OVERRIDES out per (base_id, probe)
    for f in sorted(glob.glob(str(ROOT / "probes/out/answers.shard*.jsonl"))) +              sorted(glob.glob(str(ROOT / "probes/out2/**/answers.shard*.jsonl"), recursive=True)):
        for l in Path(f).open():
            r = json.loads(l)
            if r["base_id"] in excluded:
                continue
            got = pf_json(r["predict"]) if r["probe"] == "F" else pf_plain(r["predict"])
            ok = int(got is not None and numnorm(got) == numnorm(r["gold"]))
            sig[r["base_id"]][r["probe"]] = ok
            meta[r["base_id"]] = r["pool"]
    return sig, meta


def classify(s):
    O = s.get("O")
    have = lambda k: s.get(k) is not None
    labels = []
    if O == 0 and s.get("S") == 1:
        labels.append("scaffold")
    if O == 0 and s.get("R") == 1 and s.get("S") != 1:
        labels.append("rule")
    if have("P") and O is not None and O != s.get("P"):
        labels.append("phrasing")
    if O == 1 and ((have("W1") and s["W1"] == 0) or (have("W2") and s["W2"] == 0)):
        labels.append("conduct")
    if O == 0 and s.get("S") == 0 and s.get("R") == 0 and s.get("C") == 1:
        labels.append("local_exec")
    if have("F") and O is not None and O != s.get("F") and not labels:
        labels.append("format")
    if not labels:
        avail = [v for v in s.values() if v is not None]
        labels.append("unresolved" if avail and not any(avail) else
                      ("ok" if O == 1 else "mixed"))
    return labels


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pre-audit", action="store_true",
                    help="explicit provisional run before construct audit sign-off")
    ap.add_argument("--audited", default="",
                    help="comma list of probe types that PASSED the >=70% audit")
    a = ap.parse_args()
    if not a.pre_audit and not a.audited:
        raise SystemExit("HELD: pass --audited O,P,... after construct-audit sign-off, "
                         "or --pre-audit for an explicitly provisional look.")
    admitted = set(a.audited.split(",")) if a.audited else set(TYPES)
    sig, meta = load_answers()
    lab_by_pool = defaultdict(lambda: defaultdict(int))
    n_pool = defaultdict(int)
    co = defaultdict(int)
    for bid, s in sig.items():
        s = {k: v for k, v in s.items() if k in admitted}
        pool = meta[bid]
        n_pool[pool] += 1
        labels = classify(s)
        for L in labels:
            lab_by_pool[pool][L] += 1
        for i in range(len(labels)):
            for j in range(i + 1, len(labels)):
                co[tuple(sorted((labels[i], labels[j])))] += 1
    tag = "PROVISIONAL (pre-audit)" if a.pre_audit else f"admitted={sorted(admitted)}"
    L = [f"# GSM Diagnostic Profile — {tag}", "",
         "| pool | n | " + " | ".join(sorted({k for p in lab_by_pool for k in lab_by_pool[p]})) + " |"]
    cats = sorted({k for p in lab_by_pool for k in lab_by_pool[p]})
    L.append("|" + "---|" * (len(cats) + 2))
    for pool in sorted(n_pool):
        row = [pool, str(n_pool[pool])]
        for c in cats:
            k = lab_by_pool[pool].get(c, 0)
            p, lo, hi = wilson(k, n_pool[pool])
            row.append(f"{p:.1%} [{lo:.0%},{hi:.0%}]")
        L.append("| " + " | ".join(row) + " |")
    L += ["", "## overlap(共现计数 top)", ""]
    for k, v in sorted(co.items(), key=lambda x: -x[1])[:10]:
        L.append(f"- {k[0]} ∧ {k[1]}: {v}")
    out = ROOT / "profile"
    out.mkdir(exist_ok=True)
    (out / "GSM_profile.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
