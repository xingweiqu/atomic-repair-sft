#!/usr/bin/env python3
"""P1 eval: D4 arms x 16-cell factorial with VERIFY cells split by candidate
correctness (keep-rate vs override-rate, PREREG_phase1_D4 main readouts) +
abstention-retention column (INSUFFICIENT cells).

  gen --shard i:N   inference over P1 ckpts (glob env P0C_EXTRA) on the frozen
                    200-family subset
  score             per-arm: override_rate / keep_rate / insuf_retention / cell table
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm  # noqa: E402
from prescription.p0c_eval import fams200, chat, score_one  # noqa: E402

OUT = ROOT / "prescription/p1"


def roster():
    out = []
    for d in sorted(glob.glob(os.environ.get("P0C_EXTRA", "/mnt/hdfs/xwqu/p1/output/*"))):
        if Path(d, "config.json").exists():
            out.append((Path(d).name, d))
    return out


def cmd_gen(args):
    i, n = map(int, args.shard.split(":"))
    OUT.mkdir(parents=True, exist_ok=True)
    fams = fams200()
    from vllm import LLM, SamplingParams
    sp = SamplingParams(temperature=0.0, max_tokens=1024)
    for tag, path in roster()[i::n]:
        outp = OUT / f"pred_{tag}.jsonl"
        if outp.exists():
            print(f"skip {tag}")
            continue
        jobs = [(f["id"], ck, c) for f in fams for ck, c in f["cells"].items()]
        llm = LLM(model=path, dtype="bfloat16")
        outs = [o.outputs[0].text for o in llm.generate(
            [chat(c["instr"], c["user"]) for _, _, c in jobs], sp)]
        del llm
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()
        with outp.open("w") as f:
            for (fid, ck, c), t in zip(jobs, outs):
                f.write(json.dumps({"fam": fid, "cell": ck, "gold": c["gold"],
                                    "user": c["user"], "predict": t}, ensure_ascii=False) + "\n")
        print(f"done {tag}")


def cand_of(user):
    m = re.search(r"Candidate answer:\s*(-?[\d,\.]+)", user or "")
    return numnorm(m.group(1)) if m else None


def cmd_score(_):
    res = {}
    files = sorted(glob.glob(str(OUT / "pred_*.jsonl"))) + \
        [str(ROOT / "prescription/p0c/pred_BASE.jsonl"),
         str(ROOT / "prescription/p0c/pred_l3_cleanreplay_s42_e4.jsonl")]
    for f in files:
        if not Path(f).exists():
            continue
        tag = Path(f).stem.replace("pred_", "")
        cells = defaultdict(list)
        keep_ok = keep_n = ovr_ok = ovr_n = 0
        for l in Path(f).open():
            r = json.loads(l)
            s = score_one(r)
            cells[r["cell"]].append(s)
            if "VERIFY" in r["cell"] and "ANSWERABLE" in r["cell"] and "user" in r:
                cand = cand_of(r["user"])
                if cand is None:
                    continue
                if cand == numnorm(r["gold"]):
                    keep_n += 1
                    keep_ok += s
                else:
                    ovr_n += 1
                    ovr_ok += s
        insuf = [v for c, vs in cells.items() if "INSUFFICIENT" in c for v in vs]
        res[tag] = dict(
            keep_rate=round(keep_ok / keep_n, 4) if keep_n else None,
            override_rate=round(ovr_ok / ovr_n, 4) if ovr_n else None,
            insuf_retention=round(sum(insuf) / len(insuf), 4) if insuf else None,
            cell_table={c: round(sum(v) / len(v), 4) for c, v in cells.items()})
    (OUT / "p1_scores.json").write_text(json.dumps(res, indent=1))
    for tag, v in sorted(res.items()):
        print(f"{tag:34} keep {v['keep_rate']} override {v['override_rate']} insuf {v['insuf_retention']}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "score"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"gen": cmd_gen, "score": cmd_score}[a.cmd](a)
