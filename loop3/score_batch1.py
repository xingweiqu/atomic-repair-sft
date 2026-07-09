#!/usr/bin/env python3
"""Batch-1 scorer (PREREG_loop3 frozen metrics).

Per arm@ridge: recompute the 8-probe signature on the same items; report
  - RescueEffect_k = fraction of pre-repair bucket-k items whose signature is now "ok"
    (O correct AND no failure label) — primary; per-probe accuracies secondary;
  - clean GSM (O acc), W adopt/derail/mute, bleed/mute (from ridge json), gain/1k tokens.
Prediction-table scoring (6 cells, hit = within ±0.15 per prereg grey rule).
CC does NOT adjudicate arm outcomes (i/ii/iii) — numbers only (C-11 §5).
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

EVAL = ROOT / "loop3/eval"


def load_pre_signatures():
    sig = defaultdict(dict)
    meta = {}
    excluded = set(json.loads((ROOT / "probes/data/pool_filter.json").read_text())["excluded"])
    for f in sorted(glob.glob(str(ROOT / "probes/out/answers.shard*.jsonl"))) + \
             sorted(glob.glob(str(ROOT / "probes/out2/**/answers.shard*.jsonl"), recursive=True)):
        for l in Path(f).open():
            r = json.loads(l)
            if r["base_id"] in excluded:
                continue
            got = pf_json(r["predict"]) if r["probe"] == "F" else pf_plain(r["predict"])
            sig[r["base_id"]][r["probe"]] = int(got is not None and numnorm(got) == numnorm(r["gold"]))
            meta[r["base_id"]] = r["pool"]
    return sig, meta


def arm_signatures(path):
    sig = defaultdict(dict)
    extra = defaultdict(dict)
    for l in Path(path).open():
        r = json.loads(l)
        got = pf_json(r["predict"]) if r["probe"] == "F" else pf_plain(r["predict"])
        ok = int(got is not None and numnorm(got) == numnorm(r["gold"]))
        sig[r["base_id"]][r["probe"]] = ok
        if r["probe"] in ("W1", "W2") and r.get("w"):
            extra[r["base_id"]][r["probe"]] = (
                "mute" if got is None else
                "adopt" if numnorm(got) == numnorm(r["w"]) else
                "derail" if not ok else "resist_ok")
    return sig, extra


# defining probes per bucket (frozen classifier's decision surface); for RE we only
# require the probes that FAILED pre-repair to now pass (loose reading of prereg
# "桶 k 失败题…答对比例"). Strict reading (full signature -> ok) reported alongside.
DEFPROBE = {"conduct": ["W1", "W2"], "format": ["F"], "phrasing": ["O", "P"],
            "scaffold": ["O"], "rule": ["O"], "local_exec": ["O"], "unresolved": ["O"]}


def re_defining(pre, sig, buckets):
    out = {}
    for lab, ids in buckets.items():
        if lab not in DEFPROBE:
            continue
        fixed = tot = 0
        for bid in ids:
            s = sig.get(bid)
            if not s:
                continue
            probes = [p for p in DEFPROBE[lab] if pre[bid].get(p) == 0]
            if not probes:
                continue
            tot += 1
            if all(s.get(p) == 1 for p in probes):
                fixed += 1
        out[lab] = fixed / tot if tot else None
    return out


def main():
    pre_sig, meta = load_pre_signatures()
    buckets = defaultdict(list)   # label -> [base_id] (gsm pool only for RE)
    for bid, s in pre_sig.items():
        if meta.get(bid) != "gsm":
            continue
        for lab in classify(s):
            buckets[lab].append(bid)

    manifest = json.loads((ROOT / "loop3/arms/manifest.json").read_text())
    rows = []
    for f in sorted(glob.glob(str(EVAL / "full_l3_*.jsonl"))):
        tag = Path(f).stem.replace("full_l3_", "")          # e.g. A1_s42_e4
        arm = "_".join(tag.split("_")[:-2])
        sig, extra = arm_signatures(f)
        rec = {"arm": tag}
        # clean GSM + W behaviour
        o = [(b, s.get("O")) for b, s in sig.items() if meta.get(b) == "gsm" and s.get("O") is not None]
        rec["O_acc"] = sum(v for _, v in o) / max(len(o), 1)
        wstat = defaultdict(int)
        for b, d in extra.items():
            for _, kind in d.items():
                wstat[kind] += 1
        wn = sum(wstat.values()) or 1
        rec.update({f"W_{k}": v / wn for k, v in wstat.items()})
        # RescueEffect per bucket
        for lab, ids in sorted(buckets.items()):
            if lab in ("ok",):
                continue
            fixed = 0
            tot = 0
            for bid in ids:
                s = sig.get(bid)
                if not s or s.get("O") is None:
                    continue
                tot += 1
                labs = classify(s)
                if labs == ["ok"]:
                    fixed += 1
            rec[f"RE_{lab}"] = fixed / tot if tot else None
            rec[f"n_{lab}"] = tot
        for lab, v in re_defining(pre_sig, sig, buckets).items():
            rec[f"REd_{lab}"] = v
        # tokens (chars proxy) for gain-per-1k
        m = manifest.get(arm) or manifest.get(arm.replace("single_", "single_"))
        rec["chars"] = (m or {}).get("chars")
        rows.append(rec)

    (EVAL / "batch1_scores.json").write_text(json.dumps(rows, indent=1))
    # ---- report ----
    def pc(x):
        return f"{100*x:.0f}%" if isinstance(x, float) else "—"
    labs = ["conduct", "format", "phrasing", "scaffold", "rule", "local_exec", "unresolved"]
    print(f"{'arm':26}{'O_acc':>7}" + "".join(f"{('RE_'+l)[:10]:>11}" for l in labs)
          + f"{'W_adopt':>9}{'W_mute':>8}")
    for r in sorted(rows, key=lambda x: x["arm"]):
        print(f"{r['arm']:26}{pc(r['O_acc']):>7}"
              + "".join(f"{pc(r.get('RE_'+l)):>11}" for l in labs)
              + f"{pc(r.get('W_adopt', 0.0)):>9}{pc(r.get('W_mute', 0.0)):>8}")
    print("\nbucket sizes:", {l: len(buckets[l]) for l in labs if buckets.get(l)})


if __name__ == "__main__":
    main()
