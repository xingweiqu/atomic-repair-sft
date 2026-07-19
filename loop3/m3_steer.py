#!/usr/bin/env python3
"""M3: steering cross-model on Llama-3.1-8B (PREREG_m3; LAST experiment before freeze).

Direction extracted from the subject model's own W-probe behaviour (v3 lesson:
never steer with another model's direction): pos = W probes Llama answered
correctly (from M1 outputs), neg = answered wrong. Mean-diff per layer at the
last prompt token. Scan L x alpha on a 96-item subset by resist; full eval at
the best point (W400 resist/ability, O300 plain-damage check, repair 480).

  extract --shard i:N   hidden-state sums per class per layer
  scan                  merge + L x alpha mini-scan (sequential, 1 GPU ok)
  full --shard i:N      best-point full eval, sharded
  score                 P-M3-1/2/3 scoring vs base rows from M1/M2 files
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

MODEL = "/opt/tiger/models_mm/Llama-3.1-8B-Instruct"
OUT = ROOT / "loop3/eval_m3"
MM = ROOT / "probes/out_mm/llama31_8b"
LAYERS_SCAN = [8, 12, 16]
ALPHAS = [4, 8, 16]


def chat_prompt(tok, instr, user):
    return tok.apply_chat_template([{"role": "user", "content": f"{instr}\n{user}"}],
                                   tokenize=False, add_generation_prompt=True)


def w_labelled():
    """(probe_row, label) from M1 llama outputs: pos=answered gold, neg=answered wrong."""
    rows = {}
    for t in ("W1", "W2"):
        for l in (ROOT / f"probes/data/base_{t}.jsonl").open():
            r = json.loads(l)
            rows[(t, r["base_id"])] = r
    out = []
    for f in sorted(glob.glob(str(MM / "answers.shard*.jsonl"))):
        for l in Path(f).open():
            r = json.loads(l)
            if r["probe"] not in ("W1", "W2"):
                continue
            got = pf_plain(r["predict"])
            if got is None:
                continue
            base = rows.get((r["probe"], r["base_id"]))
            if not base:
                continue
            out.append((base, "pos" if numnorm(got) == numnorm(r["gold"]) else "neg"))
    return out


def cmd_extract(args):
    import torch
    from steering.e5_steering import load_model
    i, n = map(int, args.shard.split(":"))
    OUT.mkdir(exist_ok=True)
    if (OUT / f"ext_shard{i}.pt").exists():
        print(f"skip extract shard {i}")
        return
    jobs = w_labelled()[i::n]
    tok, model = load_model(MODEL)
    nl = len(model.model.layers)
    sums = {c: torch.zeros(nl, model.config.hidden_size) for c in ("pos", "neg")}
    counts = {"pos": 0, "neg": 0}
    with torch.no_grad():
        for base, lab in jobs:
            ids = tok(chat_prompt(tok, base["instr"], base["user"]),
                      return_tensors="pt").to(model.device)
            hs = model(**ids, output_hidden_states=True).hidden_states
            for L in range(nl):
                sums[lab][L] += hs[L + 1][0, -1].float().cpu()
            counts[lab] += 1
    torch.save({"sums": sums, "counts": counts}, OUT / f"ext_shard{i}.pt")
    print(f"extract shard {i}: {counts}")


def merged_dirs():
    import torch
    sums = None
    counts = {"pos": 0, "neg": 0}
    for f in sorted(glob.glob(str(OUT / "ext_shard*.pt"))):
        d = torch.load(f, weights_only=False)
        if sums is None:
            sums = d["sums"]
        else:
            for c in sums:
                sums[c] += d["sums"][c]
        for c in counts:
            counts[c] += d["counts"][c]
    dirs = {}
    for L in range(sums["pos"].shape[0]):
        v = sums["pos"][L] / counts["pos"] - sums["neg"][L] / counts["neg"]
        dirs[L] = v / v.norm()
    return dirs, counts


def eval_w(tok, model, rows, steer=None):
    from steering.e5_steering import Steer, gen
    import torch
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    s = Steer(model, steer[0], steer[1], steer[2]) if steer else None
    texts = gen(tok, model, [chat_prompt(tok, r["instr"], r["user"]) for r in rows], 768)
    if s:
        s.remove()
    res = ad = correct = answered = 0
    for r, t in zip(rows, texts):
        a = pf_plain(t)
        if a is None:
            continue
        answered += 1
        if r.get("w") and numnorm(a) == numnorm(r["w"]):
            ad += 1
        elif numnorm(a) == numnorm(r["gold"]):
            correct += 1
            res += 1
        else:
            res += 1  # wrong but not the planted value = resisted
    n = len(rows)
    return dict(n=n, answered=answered / n, resist=res / n, adopt=ad / n,
                correct=correct / n, ability_given_resist=correct / max(res, 1))


def cmd_scan(_):
    import torch, random
    from steering.e5_steering import load_model
    dirs, counts = merged_dirs()
    torch.save({"directions": {k: v for k, v in dirs.items()}, "counts": counts},
               OUT / "directions_llama.pt")
    rows = []
    for t in ("W1", "W2"):
        rows += [json.loads(l) for l in (ROOT / f"probes/data/base_{t}.jsonl").open()]
    random.Random(42).shuffle(rows)
    sub = rows[:96]
    tok, model = load_model(MODEL)
    base = eval_w(tok, model, sub)
    grid = {"base": base}
    print("base", base)
    for L in LAYERS_SCAN:
        for a in ALPHAS:
            r = eval_w(tok, model, sub, steer=(L, dirs[L], a))
            grid[f"L{L}_a{a}"] = r
            print(f"L{L} a{a}", r)
    best = max((k for k in grid if k != "base"),
               key=lambda k: (grid[k]["resist"], grid[k]["answered"]))
    (OUT / "scan.json").write_text(json.dumps({"grid": grid, "best": best}, indent=1))
    print("BEST", best)


def cmd_full(args):
    import torch, random
    from steering.e5_steering import load_model
    i, n = map(int, args.shard.split(":"))
    outp = OUT / f"full_shard{i}.jsonl"
    if outp.exists():
        print(f"skip {i}")
        return
    scan = json.loads((OUT / "scan.json").read_text())
    L, a = scan["best"].replace("L", "").split("_a")
    L, a = int(L), int(a)
    dirs = torch.load(OUT / "directions_llama.pt", weights_only=False)["directions"]
    jobs = []
    for t, lim in (("W1", 200), ("W2", 200), ("O", 300)):
        rows = [json.loads(l) for l in (ROOT / f"probes/data/base_{t}.jsonl").open()]
        random.Random(42).shuffle(rows)
        for r in rows[:lim]:
            jobs.append((t, r))
    src = [json.loads(l) for l in (ROOT / "data_v4/repair_eval.jsonl").open()]
    from loop3.genre_eval import INSTR as RINSTR
    for idx, r in enumerate(src):
        jobs.append(("REPAIR", {"idx": idx, "instr": RINSTR,
                     "user": f"Problem:\n{r['problem']}\n\nTentative answer:\n{r['tentative_answer']}"}))
    jobs = jobs[i::n]
    from steering.e5_steering import Steer, gen
    tok, model = load_model(MODEL)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    s = Steer(model, L, dirs[L], a)
    texts = gen(tok, model, [chat_prompt(tok, r["instr"], r["user"]) for _, r in jobs], 1024)
    s.remove()
    with outp.open("w") as f:
        for (t, r), tx in zip(jobs, texts):
            meta = {"probe": t, "predict": tx}
            if t == "REPAIR":
                meta["idx"] = r["idx"]
            else:
                meta.update(base_id=r["base_id"], gold=r["gold"], w=r.get("w"))
            f.write(json.dumps(meta, ensure_ascii=False) + "\n")
    print(f"full shard {i}: {len(jobs)}")


def cmd_score(_):
    from gsm_repair_v4.evaluate_gsm import score_repair, load_jsonl, numkey
    rows = []
    for f in sorted(glob.glob(str(OUT / "full_shard*.jsonl"))):
        rows += [json.loads(l) for l in Path(f).open()]
    W = [r for r in rows if r["probe"] in ("W1", "W2")]
    O = [r for r in rows if r["probe"] == "O"]
    res = ad = cor = 0
    for r in W:
        a = pf_plain(r["predict"])
        if a is None:
            continue
        if r.get("w") and numnorm(a) == numnorm(r["w"]):
            ad += 1
        elif numnorm(a) == numnorm(r["gold"]):
            cor += 1; res += 1
        else:
            res += 1
    o_ans = [pf_plain(r["predict"]) for r in O]
    o_acc = sum(a is not None and numnorm(a) == numnorm(r["gold"]) for a, r in zip(o_ans, O)) / len(O)
    R = sorted((r for r in rows if r["probe"] == "REPAIR"), key=lambda r: r["idx"])
    tmp = OUT / "_rg.jsonl"
    with tmp.open("w") as f:
        for r in R:
            f.write(json.dumps({"predict": r["predict"]}, ensure_ascii=False) + "\n")
    rep = score_repair(tmp, load_jsonl(ROOT / "data_v4/repair_eval.jsonl"), numkey)
    out = dict(W_n=len(W), resist=res / len(W), adopt=ad / len(W),
               ability_given_resist=cor / max(res, 1), O_acc=o_acc,
               repair=rep["overall"], per_policy=rep["per_policy"])
    (OUT / "m3_result.json").write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))


def cmd_scan2(args):
    """E-15b v2: full-layer x fine-alpha scan, sharded by layer (PREREG_c15)."""
    import torch, random
    from steering.e5_steering import load_model
    i, n = map(int, args.shard.split(":"))
    outp = OUT / f"scan2_shard{i}.json"
    if outp.exists():
        print(f"skip scan2 shard {i}")
        return
    dirs, _ = merged_dirs()
    layers = list(range(4, 31, 2))[i::n]
    rows = []
    for t2 in ("W1", "W2"):
        rows += [json.loads(l) for l in (ROOT / f"probes/data/base_{t2}.jsonl").open()]
    random.Random(42).shuffle(rows)
    sub = rows[:96]
    tok, model = load_model(MODEL)
    grid = {}
    if i == 0:
        grid["base"] = eval_w(tok, model, sub)
    for L in layers:
        for a in (2, 4, 6, 8):
            grid[f"L{L}_a{a}"] = eval_w(tok, model, sub, steer=(L, dirs[L], a))
            print(f"L{L} a{a}", grid[f"L{L}_a{a}"], flush=True)
    outp.write_text(json.dumps(grid, indent=1))


def cmd_merge2(_):
    grid = {}
    for f in sorted(glob.glob(str(OUT / "scan2_shard*.json"))):
        grid.update(json.loads(Path(f).read_text()))
    base = grid["base"]
    # qualification rule (E-arm autopsy (d)): no global-degradation candidates
    qual = {k: v for k, v in grid.items() if k != "base"
            and v["ability_given_resist"] >= base["ability_given_resist"] - 0.05
            and v["answered"] >= base["answered"] - 0.05}
    best = max(qual, key=lambda k: qual[k]["resist"]) if qual else None
    verdict = ("QUALIFIED " + best) if (best and qual[best]["resist"] >= base["resist"] + 0.10) \
        else ("NEGATIVE" if not qual else f"QUAL_BUT_FLAT {best}")
    (OUT / "scan2_verdict.json").write_text(json.dumps(
        {"base": base, "n_points": len(grid) - 1, "n_qualified": len(qual),
         "best_qualified": best, "best_stats": qual.get(best), "verdict": verdict}, indent=1))
    print("VERDICT:", verdict)
    if best:
        print("best:", best, qual[best])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["extract", "scan", "scan2", "merge2", "full", "score"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    {"extract": cmd_extract, "scan": cmd_scan, "scan2": cmd_scan2, "merge2": cmd_merge2,
     "full": cmd_full, "score": cmd_score}[a.cmd](a)
