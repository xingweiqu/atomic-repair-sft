#!/usr/bin/env python3
"""E arm: steering-only zero-data anchor (PREREG_e_arm; figpack ruling fig4-(ii)).

pre-repair Qwen3-8B + frozen plain-genre direction (E5b: directions_plain L12, alpha=8),
NO training. Runs the Batch-1 full probe suite + repair-genre 480 so the existing
scorers (loop3/score_batch1.py, loop3/genre_eval.py score) pick the arm up unchanged
under the tag l3_E_steer_e0.

  gen --shard i:N    HF + activation hook, sharded across GPUs
  merge              combine shards into loop3/eval/full_l3_E_steer_e0.jsonl and
                     loop3/eval/genre/pred_l3_E_steer_e0.jsonl
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

MODEL = "/mnt/hdfs/xwqu/Qwen3-8B"
LAYER, ALPHA = 12, 8
TYPES_FULL = ["O", "P", "S", "R", "C", "W1", "W2", "F"]
TMP = ROOT / "loop3/eval/e_arm_shards"


def probe_jobs():
    from loop3.eval_arms import probe_rows, chat
    jobs = []
    for t in TYPES_FULL:
        for r in probe_rows(t):
            jobs.append(("probe", {"probe": t, "base_id": r["base_id"], "pool": r["pool"],
                                   "gold": r["gold"], "w": r.get("w")},
                         chat(r["instr"], r["user"])))
    from loop3.genre_eval import prompt as gprompt
    src = [json.loads(l) for l in (ROOT / "data_v4/repair_eval.jsonl").open()]
    for idx, r in enumerate(src):
        jobs.append(("genre", {"idx": idx}, gprompt(r)))
    return jobs


def cmd_gen(args):
    import torch
    from steering.e5_steering import load_model, Steer, gen
    i, n = map(int, args.shard.split(":"))
    TMP.mkdir(parents=True, exist_ok=True)
    outp = TMP / f"shard{i}.jsonl"
    if outp.exists():
        print(f"skip shard {i}")
        return
    jobs = probe_jobs()[i::n]
    d = torch.load(ROOT / "steering/out_e5b/directions_plain.pt",
                   map_location="cpu", weights_only=False)["directions"][LAYER]
    vec = d / d.norm()
    tok, model = load_model(MODEL)
    s = Steer(model, LAYER, vec, ALPHA)
    texts = gen(tok, model, [p for _, _, p in jobs], 1024)
    s.remove()
    with outp.open("w") as f:
        for (kind, meta, _), tx in zip(jobs, texts):
            f.write(json.dumps({"kind": kind, **meta, "predict": tx},
                               ensure_ascii=False) + "\n")
    print(f"e_arm shard {i}: {len(jobs)}")


def cmd_merge(_):
    rows = []
    for f in sorted(glob.glob(str(TMP / "shard*.jsonl"))):
        rows += [json.loads(l) for l in Path(f).open()]
    probes = [r for r in rows if r["kind"] == "probe"]
    genre = sorted((r for r in rows if r["kind"] == "genre"), key=lambda r: r["idx"])
    with (ROOT / "loop3/eval/full_l3_E_steer_e0.jsonl").open("w") as f:
        for r in probes:
            f.write(json.dumps({k: r[k] for k in ("probe", "base_id", "pool", "gold", "w", "predict")},
                               ensure_ascii=False) + "\n")
    (ROOT / "loop3/eval/genre").mkdir(exist_ok=True)
    with (ROOT / "loop3/eval/genre/pred_l3_E_steer_e0.jsonl").open("w") as f:
        for r in genre:
            f.write(json.dumps({"predict": r["predict"]}, ensure_ascii=False) + "\n")
    print(f"merged: probes {len(probes)}, genre {len(genre)}")
    assert len(genre) == 480, "genre yield gate"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "merge"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"gen": cmd_gen, "merge": cmd_merge}[a.cmd](a)
