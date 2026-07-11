#!/usr/bin/env python3
"""G/B race evaluation (PREREG_bendpoint frozen protocol).

Per (run, per-epoch checkpoint): eval-ID acc / eval-OOD acc (marker exact match,
Tier-2 frozen scorer) + json_bleed / mute on transfer300 plain items.
  gen --shard i:N   vllm over (run, epoch) jobs
  collect           G = first epoch OOD>=90%; B = first epoch bleed>5% or mute>12%;
                    teachable iff G < B. Writes race_summary.json.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

HDFS = "/mnt/hdfs/xwqu/bend/output"
OUT = ROOT / "data_bend/race"
RUNS = ["bend_e", "bend_e_poison10", "bend_f", "bend_g"]
MARK = re.compile(r"final answer is\s*(-?\d[\d,]*)", re.I)


def probe_rows(tier, split):
    return [json.loads(l) for l in (ROOT / f"data_bend/probe_{tier}_{split}.jsonl").open()]


def chat(instr, user):
    return f"<|im_start|>user\n{instr}\n{user} /no_think<|im_end|>\n<|im_start|>assistant\n"


def transfer_rows():
    return [json.loads(l) for l in
            (ROOT / "data_v4/predict_outputs/predict_transfer_base/generated_predictions.jsonl").open()]


def jobs():
    out = []
    for run in RUNS:
        cks = sorted(glob.glob(f"{HDFS}/{run}/checkpoint-*"),
                     key=lambda p: int(p.rsplit("-", 1)[1]))
        for ep, ck in enumerate(cks, 1):
            out.append((run, ep, ck))
    return out


def acc(rows, outs):
    ok = 0
    for r, t in zip(rows, outs):
        m = MARK.findall(t or "")
        ok += bool(m) and m[-1].replace(",", "") == str(r["gold"])
    return ok / len(rows)


def cmd_gen(args):
    i, n = map(int, args.shard.split(":"))
    OUT.mkdir(parents=True, exist_ok=True)
    from vllm import LLM, SamplingParams
    from ledger.genre import classify as genre
    sp = SamplingParams(temperature=0.0, max_tokens=768)
    T = transfer_rows()
    for run, ep, ck in jobs()[i::n]:
        tier = run.split("_")[1]
        outp = OUT / f"race_{run}_ep{ep}.json"
        if outp.exists():
            print(f"skip {run} ep{ep}")
            continue
        evid, ood = probe_rows(tier, "eval_id"), probe_rows(tier, "eval_ood")
        llm = LLM(model=ck, dtype="bfloat16")
        prompts = ([chat(r["instruction"], r["input"]) for r in evid + ood]
                   + [r["prompt"] for r in T])
        outs = [o.outputs[0].text for o in llm.generate(prompts, sp)]
        del llm
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()
        a, b = outs[:len(evid)], outs[len(evid):len(evid) + len(ood)]
        tt = outs[len(evid) + len(ood):]
        g = [genre(t) for t in tt]
        rec = dict(run=run, epoch=ep,
                   id_acc=acc(evid, a), ood_acc=acc(ood, b),
                   bleed=sum(x == "json_bleed" for x in g) / len(g),
                   mute=sum(x == "mute" for x in g) / len(g))
        outp.write_text(json.dumps(rec))
        print(json.dumps(rec))


def cmd_collect(_):
    summary = {}
    for run in RUNS:
        recs = sorted((json.loads(Path(f).read_text())
                       for f in glob.glob(str(OUT / f"race_{run}_ep*.json"))),
                      key=lambda r: r["epoch"])
        G = next((r["epoch"] for r in recs if r["ood_acc"] >= 0.90), None)
        B = next((r["epoch"] for r in recs if r["bleed"] > 0.05 or r["mute"] > 0.12), None)
        summary[run] = dict(G=G, B=B,
                            teachable=(G is not None and (B is None or G < B)),
                            final_id=recs[-1]["id_acc"] if recs else None,
                            final_ood=recs[-1]["ood_acc"] if recs else None,
                            curve=[{k: r[k] for k in ("epoch", "id_acc", "ood_acc", "bleed", "mute")}
                                   for r in recs])
    (OUT / "race_summary.json").write_text(json.dumps(summary, indent=1))
    for k, v in summary.items():
        print(k, "G:", v["G"], "B:", v["B"], "teachable:", v["teachable"],
              "final ID/OOD: %.3f/%.3f" % (v["final_id"] or 0, v["final_ood"] or 0))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "collect"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"gen": cmd_gen, "collect": cmd_collect}[a.cmd](a)
