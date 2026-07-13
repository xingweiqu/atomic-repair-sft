#!/usr/bin/env python3
"""M2 dual-genre eval for Llama miniature repair (PREREG_multimodel M2).

Same items and instructions as the Qwen pipeline; prompts rendered with each
model's NATIVE chat template (llm.chat) — cross-model comparability is at the
item/instruction level, disclosed. Plain genre: O(300)/W1+W2(400)/F(300)
subsets; repair genre: the frozen 480-item corrupt eval, scored by the frozen
score_repair. Gates as in C-9 (answered/bleed/mute) with the pre-repair
Llama baseline row for reference (its marker compliance is lower; disclosed).

  gen --shard i:N     all (ckpt x prompt) jobs sharded by ckpt
  score               table per ckpt
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm  # noqa: E402
from probes.profile_classify import pf_plain, pf_json  # noqa: E402
from loop3.eval_arms import probe_rows  # noqa: E402
from loop3.genre_eval import INSTR as REPAIR_INSTR  # noqa: E402

HDFS = "/mnt/hdfs/xwqu/m2/output"
BASE = "/opt/tiger/models_mm/Llama-3.1-8B-Instruct"
OUT = ROOT / "loop3/eval_m2"


def ckpts():
    out = [("m2_base", BASE)]
    for d in sorted(glob.glob(f"{HDFS}/m2_*")):
        if Path(d, "config.json").exists():
            out.append((Path(d).name, d))
    return out


def jobs_prompts():
    jobs = []
    for t, lim in (("O", 300), ("W1", 200), ("W2", 200), ("F", 300)):
        for r in probe_rows(t, lim):
            jobs.append((t, {"base_id": r["base_id"], "gold": r["gold"], "w": r.get("w")},
                         f"{r['instr']}\n{r['user']}"))
    src = [json.loads(l) for l in (ROOT / "data_v4/repair_eval.jsonl").open()]
    for i, r in enumerate(src):
        jobs.append(("REPAIR", {"idx": i},
                     f"{REPAIR_INSTR}\nProblem:\n{r['problem']}\n\nTentative answer:\n{r['tentative_answer']}"))
    return jobs


def cmd_gen(args):
    i, n = map(int, args.shard.split(":"))
    OUT.mkdir(exist_ok=True)
    from vllm import LLM, SamplingParams
    sp = SamplingParams(temperature=0.0, max_tokens=1024)
    jobs = jobs_prompts()
    for tag, path in ckpts()[i::n]:
        outp = OUT / f"pred_{tag}.jsonl"
        if outp.exists():
            print(f"skip {tag}")
            continue
        llm = LLM(model=path, dtype="bfloat16", max_model_len=8192)
        msgs = [[{"role": "user", "content": p}] for _, _, p in jobs]
        outs = llm.chat(msgs, sp)
        del llm
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()
        with outp.open("w") as f:
            for (t, meta, _), o in zip(jobs, outs):
                f.write(json.dumps({"probe": t, **meta, "predict": o.outputs[0].text},
                                   ensure_ascii=False) + "\n")
        print(f"done {tag}")


def cmd_score(_):
    from gsm_repair_v4.evaluate_gsm import score_repair, load_jsonl, numkey
    from ledger.genre import classify as genre
    src = load_jsonl(ROOT / "data_v4/repair_eval.jsonl")
    print(f"{'ckpt':22}{'answered':>9}{'O_acc':>7}{'bleed':>7}{'mute':>6}"
          f"{'W_res':>7}{'W_adopt':>8}{'F_ok':>6}{'repair':>8}")
    res = {}
    for f in sorted(glob.glob(str(OUT / "pred_*.jsonl"))):
        tag = Path(f).stem.replace("pred_", "")
        rows = [json.loads(l) for l in Path(f).open()]
        O = [r for r in rows if r["probe"] == "O"]
        W = [r for r in rows if r["probe"] in ("W1", "W2")]
        F = [r for r in rows if r["probe"] == "F"]
        R = [r for r in rows if r["probe"] == "REPAIR"]
        ans = [pf_plain(r["predict"]) for r in O]
        answered = sum(a is not None for a in ans) / len(O)
        o_acc = sum(a is not None and numnorm(a) == numnorm(r["gold"]) for a, r in zip(ans, O)) / len(O)
        g = [genre(r["predict"]) for r in O]
        bleed = sum(x == "json_bleed" for x in g) / len(g)
        mute = sum(x == "mute" for x in g) / len(g)
        res_c = ad = 0
        for r in W:
            a = pf_plain(r["predict"])
            if a is None:
                continue
            if r.get("w") and numnorm(a) == numnorm(r["w"]):
                ad += 1
            elif numnorm(a) == numnorm(r["gold"]):
                res_c += 1
        f_ok = sum(1 for r in F if (v := pf_json(r["predict"])) is not None
                   and numnorm(v) == numnorm(r["gold"])) / len(F)
        tmp = OUT / f"_rg_{tag}.jsonl"
        with tmp.open("w") as fh:
            for r in R:
                fh.write(json.dumps({"predict": r["predict"]}, ensure_ascii=False) + "\n")
        rep = score_repair(tmp, src, numkey)
        res[tag] = dict(answered=answered, o_acc=o_acc, bleed=bleed, mute=mute,
                        w_correct=res_c / len(W), w_adopt=ad / len(W), f_ok=f_ok,
                        repair=rep["overall"], per_policy=rep["per_policy"],
                        false_keep=rep["false_keep"])
        r0 = res[tag]
        print(f"{tag:22}{r0['answered']:>9.2f}{r0['o_acc']:>7.2f}{r0['bleed']:>7.3f}"
              f"{r0['mute']:>6.2f}{r0['w_correct']:>7.2f}{r0['w_adopt']:>8.3f}"
              f"{r0['f_ok']:>6.2f}{r0['repair']:>8.3f}")
    (OUT / "m2_scores.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "score"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"gen": cmd_gen, "score": cmd_score}[a.cmd](a)
