#!/usr/bin/env python3
"""Compose Batch-1 arms from pools (PREREG_loop3 ratios; char-proxy token alignment
within 2%, exact token counts reported server-side at card time)."""
from __future__ import annotations
import json, random
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
POOLS = ROOT / "loop3/pools"
OUT = ROOT / "loop3/arms"
COMP = ["conduct", "format", "phrasing", "scaffold", "rule"]
A1 = dict(conduct=.40, format=.36, phrasing=.16, scaffold=.05, rule=.02)  # sums .99->renorm
D_ = dict(conduct=.02, format=.05, phrasing=.16, scaffold=.36, rule=.40)  # frozen permutation
MIX_N, SINGLE_N = 2000, 600

def load(name):
    return [json.loads(l) for l in (POOLS / f"{name}.jsonl").open()]

def take(pool, n, rng, used):
    out = []
    for r in pool:
        k = (r["_c"], r["input"][:80])
        if k in used:
            continue
        out.append(r); used.add(k)
        if len(out) == n:
            break
    assert len(out) == n, f"pool short: {n} wanted, {len(out)} got"
    return out

def chars(rows):
    return sum(len(r["instruction"]) + len(r["input"]) + len(r["output"]) for r in rows)

def main():
    OUT.mkdir(exist_ok=True)
    rng = random.Random(42)
    pools = {c: load(c) for c in COMP + ["drills", "replay"]}
    for p in pools.values():
        rng.shuffle(p)
    arms, di = {}, {}
    used = set()
    for c in COMP + ["drills"]:
        arms[f"single_{c}"] = take(pools[c], SINGLE_N, rng, set())
    def mix(name, ratios):
        rows, u = [], set()
        norm = sum(ratios.values())
        for c, w in ratios.items():
            rows += take(pools[c], round(MIX_N * w / norm), rng, u)
        rng.shuffle(rows)
        return rows
    arms["A1"] = mix("A1", A1)
    arms["B"] = mix("B", {c: .2 for c in COMP})
    arms["D"] = mix("D", D_)
    arms["C"] = take(pools["replay"], MIX_N, rng, used)
    arms["cleanreplay"] = take(pools["replay"], SINGLE_N, rng, used)
    # char-proxy alignment (ruling: 600 items/arm is PRIMARY; alignment within comparable
    # groups only — drills items are ~10x shorter, aligning them would gut the others;
    # drills & cleanreplay stay at fixed 600 items with token totals DISCLOSED)
    for group in [["A1", "B", "C", "D"], [f"single_{c}" for c in COMP]]:
        tgt = min(chars(arms[g]) for g in group)
        for g in group:
            rows = arms[g]
            while chars(rows) > tgt * 1.02:
                rows.pop()
            arms[g] = rows
    stats = {}
    for name, rows in arms.items():
        fn = f"arm_{name}.json"
        (OUT / fn).write_text(json.dumps(
            [{k: r[k] for k in ("instruction", "input", "output")} for r in rows],
            ensure_ascii=False))
        di[f"l3_{name}"] = {"file_name": f"arms/{fn}",
                            "columns": {"prompt": "instruction", "query": "input", "response": "output"}}
        stats[name] = dict(n=len(rows), chars=chars(rows))
    (ROOT / "loop3/dataset_info.json").write_text(json.dumps(di, indent=1))
    (OUT / "manifest.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))

if __name__ == "__main__":
    main()
