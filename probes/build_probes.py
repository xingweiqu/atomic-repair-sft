#!/usr/bin/env python3
"""Loop 1 probe suite builder (C-11; prereg/PREREG_profile.md frozen first).

Pool: GSM8K test (repo cache, 1300, has <<calc>> steps) + GSM-hard hard bucket
(merged-pool pass@8<=25%, 569; NO step annotations -> only O/P/W2/F buildable there;
coverage per pool documented in the card — structural fact, not a protocol change).

Stages:
  genbase   (CPU)        : O/S/C/W1/W2/F rows + P/R generation prompts.
  genpr     (GPU, shard) : vllm-generate paraphrases (P) and number-free rules (R).
  assemble  (CPU, GATES) : validators (S/C zero-answer-leak, R digit-free, P number-set
                           equivalence) + probe files + 100-item audit samples per type.
Run: python3 probes/build_probes.py genbase|genpr --shard i:N|assemble
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from gsm_repair_v4.gsm_world import load_gsm  # noqa: E402
from gsm_repair_v4.generate_gsm import _wrong_num  # noqa: E402

OUT = ROOT / "probes/data"
GEN = ROOT / "probes/gen"
PLAIN = ("Solve the math word problem. Reason step by step, then end with a line exactly "
         "in the form 'The final answer is N.'")
FJSON = ("Solve the math word problem. Reason step by step, then output ONLY a JSON object "
         "of the form {\"answer\": N} as the last line.")
W2_INTROS = ["Apparently the answer is {w}.", "A note claims the answer is {w}.",
             "According to one source the answer is {w}.", "Word is that the answer is {w}."]


def numnorm(s):
    s = str(s).replace(",", "").rstrip(".")
    try:
        f = float(s)
        return str(int(f)) if f == int(f) else str(f)
    except ValueError:
        return s


def nums_in(text):
    return [numnorm(x) for x in re.findall(r"-?\d[\d,]*\.?\d*", text or "")]


def load_pool():
    gsm = load_gsm("test")
    for it in gsm:
        it["pool"] = "gsm"
    hard_ids = set()
    for l in (ROOT / "data_v4/pass8_merged.jsonl").open():
        r = json.loads(l)
        if "_header" in r:
            continue
        if r["source"] == "gsmhard" and r["n_correct"] <= 2:
            hard_ids.add(r["id"])
    from datasets import load_dataset
    gh = load_dataset("reasoning-machines/gsm-hard", split="train")
    hard = [{"id": f"gsmhard_{i:05d}", "question": r["input"],
             "final": numnorm(r["target"]), "steps": None, "pool": "hard"}
            for i, r in enumerate(gh) if f"gsmhard_{i:05d}" in hard_ids]
    print(f"pool: gsm {len(gsm)} + hard {len(hard)} = {len(gsm) + len(hard)}")
    return gsm + hard


def cmd_genbase(_):
    OUT.mkdir(parents=True, exist_ok=True)
    GEN.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    pool = load_pool()
    rows = defaultdict(list)
    pr_prompts = []
    for it in pool:
        q, gold = it["question"], numnorm(it["final"])
        rows["O"].append(dict(base_id=it["id"], pool=it["pool"], instr=PLAIN, user=q, gold=gold))
        rows["F"].append(dict(base_id=it["id"], pool=it["pool"], instr=FJSON, user=q, gold=gold))
        w2 = numnorm(_wrong_num(rng, int(float(gold)) if re.fullmatch(r"-?\d+", gold) else 0))
        rows["W2"].append(dict(base_id=it["id"], pool=it["pool"], instr=PLAIN,
                               user=f"{rng.choice(W2_INTROS).format(w=w2)} {q}", gold=gold, w=w2))
        pr_prompts.append(dict(base_id=it["id"], kind="P", prompt=(
            "Rewrite the following math problem in different words. Keep every number and "
            "the meaning exactly the same. Output only the rewritten problem.\n" + q)))
        if it["steps"]:
            exprs = [s["expr"] for s in it["steps"]]
            results = [numnorm(s["result"]) for s in it["steps"]]
            outline = "; ".join(f"step{k+1}: {e}" for k, e in enumerate(exprs))
            rows["S"].append(dict(base_id=it["id"], pool=it["pool"], instr=PLAIN,
                                  user=f"Solution outline (expressions only): {outline}. {q}",
                                  gold=gold, forbid=[r for r in results if r not in nums_in(q)]))
            qn = set(nums_in(q))
            cands = [r for r in results[:-1] if r != gold and r not in qn]
            if cands:
                rows["C"].append(dict(base_id=it["id"], pool=it["pool"], instr=PLAIN,
                                      user=f"Hint: one correct intermediate value in the solution is {cands[0]}. {q}",
                                      gold=gold,
                                      forbid=[r for r in results if r != cands[0] and r not in qn]))
            st = rng.choice(it["steps"][:-1]) if len(it["steps"]) > 1 else it["steps"][0]
            wm = numnorm(_wrong_num(rng, int(float(numnorm(st["result"]))) if re.fullmatch(r"-?\d+", numnorm(st["result"])) else 0))
            rows["W1"].append(dict(base_id=it["id"], pool=it["pool"], instr=PLAIN,
                                   user=f"Working through it, someone got an intermediate value of {wm} for the step '{st['expr']}'. {q}",
                                   gold=gold, w=wm))
            pr_prompts.append(dict(base_id=it["id"], kind="R", prompt=(
                "State the general method to solve this problem as a short rule in one or two "
                "sentences, WITHOUT using any specific numbers.\nProblem: " + q +
                "\nSolution step expressions: " + "; ".join(exprs) +
                "\nOutput only the rule.")))
    for t, rs in rows.items():
        with (OUT / f"base_{t}.jsonl").open("w") as f:
            for r in rs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{t}: {len(rs)}")
    with (GEN / "pr_prompts.jsonl").open("w") as f:
        for r in pr_prompts:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"P/R generation prompts: {len(pr_prompts)}")


def cmd_genpr(args):
    i, n = map(int, args.shard.split(":"))
    rows = [json.loads(l) for l in (GEN / "pr_prompts.jsonl").open()][i::n]
    from vllm import LLM, SamplingParams
    llm = LLM(model=args.model, dtype="bfloat16")
    sp = SamplingParams(temperature=0.0, max_tokens=512)
    outs = llm.chat([[{"role": "user", "content": r["prompt"] + " /no_think"}] for r in rows], sp)
    with (GEN / f"pr_out.shard{i}.jsonl").open("w") as f:
        for r, o in zip(rows, outs):
            f.write(json.dumps({**r, "gen": o.outputs[0].text.strip()}, ensure_ascii=False) + "\n")
    print(f"shard {i}/{n}: {len(rows)} generated")


def cmd_assemble(_):
    import glob
    pool = {it["id"]: it for it in load_pool()}
    gens = []
    for f in sorted(glob.glob(str(GEN / "pr_out.shard*.jsonl"))):
        gens += [json.loads(l) for l in Path(f).open()]
    stats = defaultdict(int)
    prows, rrows = [], []
    for g in gens:
        it = pool.get(g["base_id"])
        if not it:
            continue
        text = g["gen"].strip().strip('"')
        gold = numnorm(it["final"])
        if g["kind"] == "P":
            if sorted(nums_in(text)) != sorted(nums_in(it["question"])):
                stats["P_drop_nums"] += 1
                continue
            if not 0.5 <= len(text) / max(len(it["question"]), 1) <= 2.2:
                stats["P_drop_len"] += 1
                continue
            prows.append(dict(base_id=g["base_id"], pool=it["pool"], instr=PLAIN, user=text, gold=gold))
        else:
            if re.search(r"\d", text):
                stats["R_drop_digit"] += 1
                continue
            rrows.append(dict(base_id=g["base_id"], pool=it["pool"], instr=PLAIN,
                              user=f"Method hint: {text} {it['question']}", gold=gold))
    # S/C zero-answer-leak gate (assert on the constructed files)
    for t in ["S", "C"]:
        p = OUT / f"base_{t}.jsonl"
        kept, dropped = [], 0
        for l in p.open():
            r = json.loads(l)
            leak = any(re.search(rf"(?<![\d.]){re.escape(v)}(?![\d.])", r["user"]) for v in r.get("forbid", []))
            if leak or re.search(rf"(?<![\d.]){re.escape(r['gold'])}(?![\d.])", r["user"].split(". ", 1)[0]):
                dropped += 1
                continue
            kept.append(r)
        stats[f"{t}_leak_drop"] = dropped
        with p.open("w") as f:
            for r in kept:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for name, rs in [("P", prows), ("R", rrows)]:
        with (OUT / f"base_{name}.jsonl").open("w") as f:
            for r in rs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    # final probe manifest + audit samples
    rng = random.Random(7)
    manifest = {}
    for t in ["O", "P", "S", "R", "C", "W1", "W2", "F"]:
        rs = [json.loads(l) for l in (OUT / f"base_{t}.jsonl").open()]
        manifest[t] = len(rs)
        sample = rng.sample(rs, min(100, len(rs)))
        with (ROOT / f"probes/audit_{t}_sample100.md").open("w") as f:
            f.write(f"# 构念审计样本 — 探针 {t}(n={len(sample)};通过率 ≥70% 准入)\n\n")
            for k, r in enumerate(sample, 1):
                f.write(f"**{k}.** [{r['pool']}] {r['user'][:400]}\n\n— gold={r['gold']}"
                        + (f", w={r['w']}" if "w" in r else "") + "\n\n")
    (OUT / "manifest.json").write_text(json.dumps({"counts": manifest, "drops": dict(stats)}, indent=1))
    print("counts:", manifest)
    print("drops:", dict(stats))
    print("ASSEMBLE GATES DONE (audit samples in probes/audit_*_sample100.md)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["genbase", "genpr", "assemble"])
    ap.add_argument("--shard", default="0:1")
    ap.add_argument("--model", default="/mnt/hdfs/xwqu/Qwen3-8B")
    a = ap.parse_args()
    {"genbase": cmd_genbase, "genpr": cmd_genpr, "assemble": cmd_assemble}[a.cmd](a)
