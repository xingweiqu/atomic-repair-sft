#!/usr/bin/env python3
"""E-15c: E-arm alpha scan (PREREG_c15). Subset jobs (O300 + W400 + repair480)
at a given alpha; the alpha=8 reference point is re-read from the existing full
E-arm files on the SAME subsets at score time.

  gen --alpha A --shard i:N
  score
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm  # noqa: E402
from probes.profile_classify import pf_plain  # noqa: E402
from loop3.eval_arms import probe_rows, chat  # noqa: E402
from loop3.genre_eval import prompt as gprompt  # noqa: E402

MODEL = "/mnt/hdfs/xwqu/Qwen3-8B"
LAYER = 12
OUT = ROOT / "loop3/eval_e15c"


def jobs():
    out = []
    for t, lim in (("O", 300), ("W1", 200), ("W2", 200)):
        for r in probe_rows(t, lim):
            out.append((t, {"base_id": r["base_id"], "gold": r["gold"], "w": r.get("w")},
                        chat(r["instr"], r["user"])))
    src = [json.loads(l) for l in (ROOT / "data_v4/repair_eval.jsonl").open()]
    for i, r in enumerate(src):
        out.append(("REPAIR", {"idx": i}, gprompt(r)))
    return out


def cmd_gen(args):
    import torch
    from steering.e5_steering import load_model, Steer, gen
    i, n = map(int, args.shard.split(":"))
    OUT.mkdir(exist_ok=True)
    outp = OUT / f"pred_a{args.alpha}_shard{i}.jsonl"
    if outp.exists():
        print(f"skip a{args.alpha} shard {i}")
        return
    jj = jobs()[i::n]
    d = torch.load(ROOT / "steering/out_e5b/directions_plain.pt",
                   map_location="cpu", weights_only=False)["directions"][LAYER]
    vec = d / d.norm()
    tok, model = load_model(MODEL)
    s = Steer(model, LAYER, vec, args.alpha)
    texts = gen(tok, model, [p for _, _, p in jj], 1024)
    s.remove()
    with outp.open("w") as f:
        for (t, meta, _), tx in zip(jj, texts):
            f.write(json.dumps({"probe": t, **meta, "predict": tx}, ensure_ascii=False) + "\n")
    print(f"a{args.alpha} shard {i}: {len(jj)}")


def read_rows(alpha):
    """alpha 4/6 from shards; alpha 8 re-read from the existing full E-arm files."""
    if alpha != 8:
        rows = []
        for f in sorted(glob.glob(str(OUT / f"pred_a{alpha}_shard*.jsonl"))):
            rows += [json.loads(l) for l in Path(f).open()]
        return rows
    keep = {(t, r["base_id"]) for t, lim in (("O", 300), ("W1", 200), ("W2", 200))
            for r in probe_rows(t, lim)}
    rows = []
    for l in (ROOT / "loop3/eval/full_l3_E_steer_e0.jsonl").open():
        r = json.loads(l)
        if (r["probe"], r["base_id"]) in keep:
            rows.append(r)
    for i, l in enumerate((ROOT / "loop3/eval/genre/pred_l3_E_steer_e0.jsonl").open()):
        rows.append({"probe": "REPAIR", "idx": i, "predict": json.loads(l)["predict"]})
    return rows


def cmd_score(_):
    from gsm_repair_v4.evaluate_gsm import score_repair, load_jsonl, numkey
    from ledger.genre import classify as genre
    src = load_jsonl(ROOT / "data_v4/repair_eval.jsonl")
    table = {}
    for alpha in (4, 6, 8):
        rows = read_rows(alpha)
        if not rows:
            continue
        O = [r for r in rows if r["probe"] == "O"]
        W = [r for r in rows if r["probe"] in ("W1", "W2")]
        R = sorted((r for r in rows if r["probe"] == "REPAIR"), key=lambda r: r["idx"])
        ans = [pf_plain(r["predict"]) for r in O]
        o_acc = sum(a is not None and numnorm(a) == numnorm(r["gold"]) for a, r in zip(ans, O)) / len(O)
        g = [genre(r["predict"]) for r in O]
        res = ad = 0
        for r in W:
            a = pf_plain(r["predict"])
            if a is None:
                continue
            if r.get("w") and numnorm(a) == numnorm(r["w"]):
                ad += 1
            else:
                res += 1
        tmp = OUT / f"_rg_a{alpha}.jsonl"
        with tmp.open("w") as f:
            for r in R:
                f.write(json.dumps({"predict": r["predict"]}, ensure_ascii=False) + "\n")
        rep = score_repair(tmp, src, numkey)
        table[alpha] = dict(
            O_acc=round(o_acc, 4),
            answered=round(sum(a is not None for a in ans) / len(O), 4),
            mute=round(sum(x == "mute" for x in g) / len(g), 4),
            bleed=round(sum(x == "json_bleed" for x in g) / len(g), 4),
            resist=round(res / len(W), 4), adopt=round(ad / len(W), 4),
            repair=rep["overall"], false_keep=rep["false_keep"])
        print(alpha, table[alpha])
    (OUT / "alpha_scan.json").write_text(json.dumps(table, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "score"])
    ap.add_argument("--alpha", type=int, default=4)
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"gen": cmd_gen, "score": cmd_score}[a.cmd](a)
