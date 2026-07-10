#!/usr/bin/env python3
"""B2-0(b) genre reconciliation (Batch-1 ruling ②b, no retraining).

Run the 14 Batch-1 ridge ckpts on the REPAIR-GENRE corrupt eval
(data_v4/repair_eval.jsonl, 480 items) with the exact v4 prompt template,
then score with the frozen v4 scorer (gsm_repair_v4.evaluate_gsm.score_repair).

Question: do A1/B/D separate in the repair genre (E1b predicts yes) while
being indistinguishable on plain items? If so: "whether ratios matter
depends on genre".

  gen --shard i:N   vllm generation, ckpts sharded across GPUs
  score             local scoring incl. pre-repair base reference
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

EVAL = ROOT / "loop3/eval"
GENRE = EVAL / "genre"
HDFS = "/mnt/hdfs/xwqu/loop3/output"

INSTR = ("You are given a math word problem and a tentative answer that may be wrong. "
         "Decide whether to keep it, update it, or abstain, commit to the repair action, "
         "then give the final answer (or null if you must abstain). Return only valid JSON.")


def prompt(r):
    # exact v4 template (system Qwen + instruction; no /no_think) for comparability
    return ("<|im_start|>system\nYou are Qwen, created by Alibaba Cloud. "
            "You are a helpful assistant.<|im_end|>\n<|im_start|>user\n"
            f"{INSTR}\nProblem:\n{r['problem']}\n\nTentative answer:\n{r['tentative_answer']}"
            "<|im_end|>\n<|im_start|>assistant\n")


def ridge_ckpts():
    picks = json.loads((EVAL / "ridge_picks.json").read_text())
    return [f"l3_{k}_e{v['epoch']}" for k, v in sorted(picks.items()) if "epoch" in v]


def cmd_gen(args):
    i, n = map(int, args.shard.split(":"))
    src = [json.loads(l) for l in (ROOT / "data_v4/repair_eval.jsonl").open()]
    prompts = [prompt(r) for r in src]
    GENRE.mkdir(parents=True, exist_ok=True)
    from vllm import LLM, SamplingParams
    sp = SamplingParams(temperature=0.0, max_tokens=1024)
    for tag in ridge_ckpts()[i::n]:
        outp = GENRE / f"pred_{tag}.jsonl"
        if outp.exists():
            print(f"skip {tag}")
            continue
        llm = LLM(model=f"{HDFS}/{tag}", dtype="bfloat16")
        outs = llm.generate(prompts, sp)
        with outp.open("w") as f:
            for o in outs:
                f.write(json.dumps({"predict": o.outputs[0].text}, ensure_ascii=False) + "\n")
        del llm
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()
        print(f"done {tag}: {len(outs)}")


def cmd_score(_):
    from gsm_repair_v4.evaluate_gsm import score_repair, load_jsonl, numkey
    src = load_jsonl(ROOT / "data_v4/repair_eval.jsonl")
    rows = {}
    base = ROOT / "data_v4/predict_outputs/predict_diagnosis_base/generated_predictions.jsonl"
    if base.exists():
        rows["pre-repair(base)"] = score_repair(base, src, numkey)
    for f in sorted(glob.glob(str(GENRE / "pred_l3_*.jsonl"))):
        rows[Path(f).stem.replace("pred_l3_", "")] = score_repair(f, src, numkey)
    (EVAL / "genre_scores.json").write_text(json.dumps(rows, indent=1))
    print(f"{'ckpt':26}{'overall':>8}{'false_keep':>11}{'clean_over':>11}  per-policy")
    for k, v in rows.items():
        pp = " ".join(f"{p}:{d['acc']}" for p, d in sorted(v["per_policy"].items()))
        print(f"{k:26}{v['overall']:>8}{str(v['false_keep']):>11}{str(v['clean_over_repair']):>11}  {pp}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["gen", "score"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"gen": cmd_gen, "score": cmd_score}[a.cmd](a)
