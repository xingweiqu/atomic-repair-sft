#!/usr/bin/env python3
"""Compose Batch-2 dose arms (PREREG_batch2 frozen design).

Carrier = Batch-1 arm_cleanreplay.json (600 clean replay items, fixed set);
replacement-style dosing: total stays 600, N carrier items swapped for
component items drawn from the shared pools with rng(4242).
scafffmt = 300 scaffold + 300 format (no carrier).
Appends l3_* entries to loop3/dataset_info.json (Batch-1 entries untouched).
"""
from __future__ import annotations
import json, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
POOLS = ROOT / "loop3/pools"
OUT = ROOT / "loop3/arms"

ARMS = {  # name -> (component, n_component)
    "fmt10": ("format", 60), "fmt20": ("format", 120), "fmt36": ("format", 216),
    "drl10": ("drills", 60), "drl25": ("drills", 150),
}


def load_pool(name):
    return [json.loads(l) for l in (POOLS / f"{name}.jsonl").open()]


def chars(rows):
    return sum(len(r["instruction"]) + len(r["input"]) + len(r["output"]) for r in rows)


def main():
    rng = random.Random(4242)
    carrier = json.loads((OUT / "arm_cleanreplay.json").read_text())
    assert len(carrier) == 600, len(carrier)
    pools = {c: load_pool(c) for c in ("format", "drills", "scaffold")}
    for p in pools.values():
        rng.shuffle(p)
    arms = {}
    for name, (comp, n) in ARMS.items():
        rows = carrier[: 600 - n] + [
            {k: r[k] for k in ("instruction", "input", "output")} for r in pools[comp][:n]]
        rng.shuffle(rows)
        arms[name] = (rows, dict(component=comp, n_comp=n, item_share=n / 600))
    sf = ([{k: r[k] for k in ("instruction", "input", "output")} for r in pools["scaffold"][:300]]
          + [{k: r[k] for k in ("instruction", "input", "output")} for r in pools["format"][300:600]])
    rng.shuffle(sf)
    arms["scafffmt"] = (sf, dict(component="scaffold+format", n_comp=600, item_share=1.0))

    di = json.loads((ROOT / "loop3/dataset_info.json").read_text())
    stats = {}
    for name, (rows, meta) in arms.items():
        fn = f"arm_{name}.json"
        (OUT / fn).write_text(json.dumps(rows, ensure_ascii=False))
        di[f"l3_{name}"] = {"file_name": f"arms/{fn}",
                            "columns": {"prompt": "instruction", "query": "input", "response": "output"}}
        comp_chars = chars([r for r in rows if r not in carrier]) if name != "scafffmt" else chars(rows)
        stats[name] = dict(n=len(rows), chars=chars(rows), char_share_comp=None, **meta)
    # char share (dual disclosure, item share is the primary reading per prereg)
    for name, (rows, meta) in arms.items():
        if name == "scafffmt":
            continue
        comp = meta["component"]
        comp_rows = rows  # recompute precisely from pool membership
        pool_keys = {(r["instruction"], r["input"]) for r in pools[comp][: meta["n_comp"]]}
        cc = chars([r for r in rows if (r["instruction"], r["input"]) in pool_keys])
        stats[name]["char_share_comp"] = round(cc / chars(rows), 4)
    (ROOT / "loop3/dataset_info.json").write_text(json.dumps(di, indent=1))
    (OUT / "manifest_b2.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))


if __name__ == "__main__":
    main()
