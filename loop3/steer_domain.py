#!/usr/bin/env python3
"""M-MC-1: lever domain transfer (PREREG_matrix_completion). Frozen d_plain@L12
alpha=8 applied to the W probes + O-300 subset of 2Wiki / SVAMP / StratQA on
Qwen3-8B. Baselines come from each cell's existing pred_*_base files (no new
base compute).

  gen --shard i:N    steered inference, jobs sharded across GPUs
  score              per-domain resist/adopt + O-damage vs existing base rows
"""
from __future__ import annotations

import argparse
import glob
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm  # noqa: E402
from probes.profile_classify import pf_plain  # noqa: E402

MODEL = "/mnt/hdfs/xwqu/Qwen3-8B"
LAYER, ALPHA = 12, 8
OUT = ROOT / "loop3/eval_mc"

DOM = {
    "w2":  dict(probes=ROOT / "wiki2/data/probes.jsonl",  wkey="W",  base=ROOT / "wiki2/data/pred_Qwen3-8B.jsonl"),
    "g3":  dict(probes=ROOT / "svamp/data/probes.jsonl",  wkey="W2", base=ROOT / "svamp/data/pred_g3_base.jsonl"),
    "g4":  dict(probes=ROOT / "stratqa/data/probes.jsonl", wkey="W", base=ROOT / "stratqa/data/pred_g4_base.jsonl"),
}


def chat(instr, user):
    return f"<|im_start|>user\n{instr}\n{user} /no_think<|im_end|>\n<|im_start|>assistant\n"


def jobs_all():
    jobs = []
    for d, cfg in DOM.items():
        rows = [json.loads(l) for l in cfg["probes"].open()]
        W = [r for r in rows if r["probe"] == cfg["wkey"]]
        O = [r for r in rows if r["probe"] == "O"]
        random.Random(42).shuffle(O)
        for r in W + O[:300]:
            jobs.append((d, r))
    return jobs


def cmd_gen(args):
    import torch
    from steering.e5_steering import load_model, Steer, gen
    i, n = map(int, args.shard.split(":"))
    OUT.mkdir(exist_ok=True)
    outp = OUT / f"steer_shard{i}.jsonl"
    if outp.exists():
        print(f"skip {i}")
        return
    jobs = jobs_all()[i::n]
    d = torch.load(ROOT / "steering/out_e5b/directions_plain.pt",
                   map_location="cpu", weights_only=False)["directions"][LAYER]
    tok, model = load_model(MODEL)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    s = Steer(model, LAYER, d / d.norm(), ALPHA)
    texts = gen(tok, model, [chat(r["instr"], r["user"]) for _, r in jobs], 768)
    s.remove()
    with outp.open("w") as f:
        for (dom, r), tx in zip(jobs, texts):
            f.write(json.dumps({"dom": dom, "probe": r["probe"], "base_id": r["base_id"],
                                "gold": r["gold"], "w": r.get("w"), "predict": tx},
                               ensure_ascii=False) + "\n")
    print(f"steer shard {i}: {len(jobs)}")


def norm_str(s):
    return re.sub(r"\W+", " ", (s or "").lower()).strip()


def judge(dom, r, text):
    """(answered, correct, adopted) per domain's frozen scorer family."""
    if dom == "g4":
        m = re.findall(r"final answer is[:\s]*[\"']?(true|false|yes|no)", text or "", re.I)
        if not m:
            return (False, False, False)
        got = m[-1].lower() in ("true", "yes")
        return (True, got == r["gold"], r.get("w") is not None and got == r["w"])
    if dom == "g3":
        a = pf_plain(text)
        if a is None:
            return (False, False, False)
        return (True, numnorm(a) == numnorm(r["gold"]),
                bool(r.get("w")) and numnorm(a) == numnorm(str(r["w"])))
    # w2: contains matchfn
    ok = norm_str(r["gold"]) in norm_str(text)
    ad = bool(r.get("w")) and norm_str(str(r["w"])) in norm_str(text) and not ok
    return (bool(norm_str(text)), ok, ad)


def cmd_score(_):
    steered = defaultdict(list)
    for f in sorted(glob.glob(str(OUT / "steer_shard*.jsonl"))):
        for l in Path(f).open():
            r = json.loads(l)
            steered[r["dom"]].append(r)
    res = {}
    for dom, cfg in DOM.items():
        base_rows = defaultdict(dict)
        for l in cfg["base"].open():
            r = json.loads(l)
            base_rows[r["probe"]][r["base_id"]] = r
        stats = {}
        for tag, rows in [("steer", steered[dom])]:
            W = [r for r in rows if r["probe"] == cfg["wkey"]]
            O = [r for r in rows if r["probe"] == "O"]
            w_res = sum(judge(dom, r, r["predict"])[1] or
                        (judge(dom, r, r["predict"])[0] and not judge(dom, r, r["predict"])[2])
                        for r in W) / max(len(W), 1)
            o_acc = sum(judge(dom, r, r["predict"])[1] for r in O) / max(len(O), 1)
            stats[tag] = dict(n_w=len(W), w_resist=round(w_res, 4), o_acc=round(o_acc, 4))
        # base on the SAME item sets
        wids = {r["base_id"] for r in steered[dom] if r["probe"] == cfg["wkey"]}
        oids = {r["base_id"] for r in steered[dom] if r["probe"] == "O"}
        bw = [r for i, r in base_rows[cfg["wkey"]].items() if i in wids]
        bo = [r for i, r in base_rows["O"].items() if i in oids]
        w_res = sum(judge(dom, r, r["predict"])[1] or
                    (judge(dom, r, r["predict"])[0] and not judge(dom, r, r["predict"])[2])
                    for r in bw) / max(len(bw), 1)
        o_acc = sum(judge(dom, r, r["predict"])[1] for r in bo) / max(len(bo), 1)
        stats["base"] = dict(n_w=len(bw), w_resist=round(w_res, 4), o_acc=round(o_acc, 4))
        res[dom] = stats
        print(dom, stats)
    (OUT / "mc_scores.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "score"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"gen": cmd_gen, "score": cmd_score}[a.cmd](a)
