#!/usr/bin/env python3
"""E5b — plain-genre probe direction (R-25 discriminator).

Goal: extract d_plain from PLAIN-GENRE corrupt behaviour — both classes answer in
plain prose (no repair schema), so the direction separates DECISION without the
genre-participation confound that contaminated E5's repair-mode d.

IMPLEMENTATION NOTE (flagged for advisor confirmation in PREREG_e5b): the ruling text
samples classes from the pre-repair model; we sample from the STEERED MODEL ITSELF
(floor e8) on the same plain-corrupt prompts — the v3 lesson (E5_INSTRUMENT_ARTIFACT)
is that directions must come from the model being steered. Both classes are still
genre-free (plain in, plain out), which is the ruling's operative requirement.
The registered dichotomy is unchanged.

Stages:
  probegen  (local)  : build plain-corrupt probe prompts from the 320 w-items — the
                       corruption already lives in `problem`; presentation is the
                       transfer-style plain instruction, NO tentative/schema.
  classify  (local)  : after the server generates floor answers on the probe, label
                       resist_plain = plain_final != w; report class sizes
                       (need >=100/100; if short, extend probe from GSM train).
  extract/sweep      : same machinery as e5_steering but with plain-probe prompts and
                       plain-behaviour classes; full four curves at best layer.

Usage:
  python3 steering/e5b.py probegen
  (server) llamafactory-cli 不适用——直接: python3 steering/e5b.py generate --model <floor>
  python3 steering/e5b.py classify
  (server) python3 steering/e5b.py extract --model <floor>
  (server) bash-style layer scan + curves: python3 steering/e5b.py sweep --model <floor>
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ledger.judge import load_items, match, wrong_value  # noqa: E402

OUT = ROOT / "steering/out_e5b"
PROBE = ROOT / "data_v4/e5b_plain_probe.jsonl"
INSTR = ("Solve the math word problem. Reason step by step, then end with a line exactly "
         "in the form 'The final answer is N.'")
FLOOR = "/mnt/hdfs/xwqu/gsm-repair-v4/output/scaffold_conv_e8"


def plain_final(t):
    m = re.findall(r"final answer is\s*(-?[\d,\.]+)", t or "", re.I)
    return m[-1].replace(",", "").rstrip(".") if m else None


def chatml(user):
    return (f"<|im_start|>user\n{user}<|im_end|>\n<|im_start|>assistant\n")


def cmd_probegen(_):
    items = load_items(ROOT / "data_v4/repair_eval.jsonl")
    rows = []
    for it in items:
        w, src = wrong_value(it, "v4")
        if w is None:
            continue
        rows.append({"id": it["id"], "w": str(w), "gold": str(it["gold_answer"]),
                     "prompt": chatml(f"{INSTR}\n{it['problem']}")})
    PROBE.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows))
    print(f"probe: {len(rows)} plain-corrupt prompts -> {PROBE}")


def cmd_generate(args):
    """Server: floor greedy answers on the probe (plain genre)."""
    import torch
    from steering.e5_steering import load_model, gen
    rows = [json.loads(l) for l in PROBE.open()]
    tok, model = load_model(args.model)
    texts = gen(tok, model, [r["prompt"] for r in rows], 1024)
    OUT.mkdir(exist_ok=True)
    with (OUT / "probe_answers.jsonl").open("w") as f:
        for r, t in zip(rows, texts):
            f.write(json.dumps({"id": r["id"], "predict": t}, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}/probe_answers.jsonl ({len(rows)})")


def cmd_classify(_):
    rows = {r["id"]: r for r in (json.loads(l) for l in PROBE.open())}
    ans = [json.loads(l) for l in (OUT / "probe_answers.jsonl").open()]
    pos, neg, mute = [], [], 0
    for a in ans:
        f = plain_final(a["predict"])
        if f is None:
            mute += 1
            continue
        (pos if not match("v4", f, rows[a["id"]]["w"]) else neg).append(a["id"])
    (OUT / "classes.json").write_text(json.dumps({"pos": pos, "neg": neg}, indent=1))
    print(f"plain classes: resist=1 {len(pos)}, resist=0 {len(neg)}, mute {mute}")
    if min(len(pos), len(neg)) < 100:
        print("UNDERPOWERED (<100): extend the probe from GSM train injections before extract "
              "(R-25: 补素题 corrupt 推理) — do NOT proceed to extract.")
        sys.exit(1)
    print("balance OK -> proceed to extract")


def cmd_extract(args):
    import torch
    from steering.e5_steering import load_model
    rows = {r["id"]: r for r in (json.loads(l) for l in PROBE.open())}
    cls = json.loads((OUT / "classes.json").read_text())
    tok, model = load_model(args.model)
    layers = model.model.layers
    sums = {c: {L: None for L in range(len(layers))} for c in ("pos", "neg")}
    counts = {"pos": 0, "neg": 0}
    for cname in ("pos", "neg"):
        for iid in cls[cname]:
            ids = tok(rows[iid]["prompt"], return_tensors="pt").to(model.device)
            with torch.no_grad():
                out = model(**ids, output_hidden_states=True)
            for L in range(len(layers)):
                h = out.hidden_states[L + 1][0, -1].float().cpu()
                sums[cname][L] = h if sums[cname][L] is None else sums[cname][L] + h
            counts[cname] += 1
    dirs = {L: sums["pos"][L] / counts["pos"] - sums["neg"][L] / counts["neg"]
            for L in range(len(layers))}
    torch.save({"directions": dirs, **counts}, OUT / "directions_plain.pt")
    print(f"saved directions_plain.pt (pos={counts['pos']} neg={counts['neg']})")


def cmd_sweep(args):
    """Layer/α scan + full curves with d_plain, steering the floor on the SAME repair
    eval + transfer eval as E5 v3 (so curves are directly comparable)."""
    import torch
    import random
    from steering.e5_steering import (load_model, gen, Steer, rows as rd,
                                      DIAG, TRANS, LAYER_SCAN, ALPHA_SCAN, ALPHA_FULL,
                                      SUBSET_N)
    from ledger.judge import score_run
    items = load_items(ROOT / "data_v4/repair_eval.jsonl")
    dpred = rd(DIAG)
    v0 = score_run(items, [r["predict"] for r in dpred], "v4")
    rprompts = [r["prompt"] for r in dpred]
    W = [i for i, x in enumerate(v0) if x["resist"] is not None]
    sub = sorted(random.Random(42).sample(W, min(SUBSET_N, len(W))))
    tprompts = [r["prompt"] for r in rd(TRANS)]
    d = torch.load(OUT / "directions_plain.pt")
    tok, model = load_model(args.model)
    res = []
    for L in LAYER_SCAN:
        vec = d["directions"][L] / d["directions"][L].norm()
        for a in ALPHA_SCAN:
            s = Steer(model, L, vec, a)
            texts = gen(tok, model, [rprompts[i] for i in sub], 384)
            s.remove()
            v = score_run([items[i] for i in sub], texts, "v4")
            R = [x["resist"] for x in v if x["resist"] is not None]
            parse = sum(x["parsed_strict"] for x in v) / len(v)
            res.append(dict(layer=L, alpha=a, resist=sum(R) / len(R) if R else None, parse=parse))
            print(f"[e5b] L={L} a={a}: resist={res[-1]['resist']} parse={parse:.2f}", flush=True)
    best = max(res, key=lambda x: (x["resist"] or 0) if x["parse"] >= 0.9 else -1)
    Lb = best["layer"]
    vec = d["directions"][Lb] / d["directions"][Lb].norm()
    for a in ALPHA_FULL:
        s = Steer(model, Lb, vec, a) if a > 0 else None
        rt = gen(tok, model, rprompts, 384)
        tt = gen(tok, model, tprompts, 2048)
        if s:
            s.remove()
        (OUT / f"gen_repair_L{Lb}_a{a}.jsonl").write_text(
            "\n".join(json.dumps({"predict": x}, ensure_ascii=False) for x in rt))
        (OUT / f"gen_transfer_L{Lb}_a{a}.jsonl").write_text(
            "\n".join(json.dumps({"predict": x}, ensure_ascii=False) for x in tt))
    (OUT / "sweep_meta.json").write_text(json.dumps({"stage1": res, "best_layer": Lb}, indent=1))
    print(f"e5b sweep done (best layer {Lb})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["probegen", "generate", "classify", "extract", "sweep"])
    ap.add_argument("--model", default=FLOOR)
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    {"probegen": cmd_probegen, "generate": cmd_generate, "classify": cmd_classify,
     "extract": cmd_extract, "sweep": cmd_sweep}[a.cmd](a)
