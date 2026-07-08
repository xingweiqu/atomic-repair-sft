#!/usr/bin/env python3
"""Loop 3 Batch-1 component pools (PREREG_loop3 frozen first; GSM TRAIN split only).

Programmatic pools: conduct (verify-then-recompute on W1/W2-style corrupted items),
format ("compute correctly UNDER format constraint" — full reasoning then JSON line),
drills (bare arithmetic, falsification arm), replay (plain gold CoT; C-arm and
clean-replay draw from this same pool at different budgets — disclosed).
LLM pools (server, sharded, lint+validators): phrasing / scaffold / rule.

  genprog             : programmatic pools -> loop3/pools/*.jsonl
  prompts             : LLM prompts        -> loop3/gen/prompts.jsonl
  genllm --shard i:N  : vllm generation    -> loop3/gen/out.shard{i}.jsonl
  assemble            : validators + pools + 100-item audit samples per LLM pool
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import lint, has_residue, numnorm  # noqa: E402
from gsm_repair_v4.gsm_world import load_gsm  # noqa: E402
from gsm_repair_v4.generate_gsm import _wrong_num  # noqa: E402
from probes.fix_probes import q_entities  # noqa: E402

POOLS = ROOT / "loop3/pools"
GEN = ROOT / "loop3/gen"
PLAIN = ("Solve the math word problem. Reason step by step, then end with a line exactly "
         "in the form 'The final answer is N.'")
FJSON = ("Solve the math word problem. Reason step by step, then output ONLY a JSON object "
         "of the form {\"answer\": N} as the last line.")
W2_INTROS = ["Reportedly the answer is {w}.", "It says here that the answer is {w}.",
             "I read somewhere that the answer is {w}.", "Someone told me the answer is {w}."]
POOL_N = 2200  # per component pool (mixed arms draw up to 2000; single arms 600)


def reasoning_of(it):
    """Gold reasoning text: strip <<..>> calculator annotations and #### line."""
    body = it["answer"].split("####")[0].strip()
    return re.sub(r"<<[^>]*>>", "", body)


def base_items(rng):
    items = [it for it in load_gsm("train") if it.get("steps")]
    # coherence filter (same rule as the probe pool)
    items = [it for it in items if re.fullmatch(r"\d+", numnorm(it["final"]))]
    rng.shuffle(items)
    return items


def cmd_genprog(_):
    POOLS.mkdir(parents=True, exist_ok=True)
    rng = random.Random(42)
    items = base_items(rng)
    conduct, fmt, drills, replay = [], [], [], []
    for it in items:
        q, gold, steps = it["question"], numnorm(it["final"]), it["steps"]
        reason = reasoning_of(it)
        # --- conduct: verify-then-recompute, plain genre, W1/W2 style 50/50 ---
        if len(conduct) < POOL_N:
            if rng.random() < 0.5:
                w = numnorm(_wrong_num(rng, int(gold)))
                prob = f"{rng.choice(W2_INTROS).format(w=w)} {q}"
                trace = (f"The stated answer {w} needs checking, so I will solve it myself.\n"
                         f"{reason}\nThe claimed {w} is wrong.\nThe final answer is {gold}.")
            else:
                st = rng.choice(steps[:-1]) if len(steps) > 1 else steps[0]
                wm = numnorm(_wrong_num(rng, int(numnorm(st["result"])) if re.fullmatch(r"-?\d+", numnorm(st["result"])) else 0))
                prob = (f"Working through it, someone got an intermediate value of {wm} "
                        f"for the step '{st['expr']}'. {q}")
                trace = (f"The quoted intermediate value {wm} needs checking, so I will "
                         f"recompute every step myself.\n{reason}\nThe quoted {wm} does not "
                         f"hold up.\nThe final answer is {gold}.")
            conduct.append({"instruction": PLAIN, "input": prob, "output": trace, "_c": "conduct"})
        # --- format: compute correctly UNDER the constraint ---
        if len(fmt) < POOL_N:
            fmt.append({"instruction": FJSON, "input": q,
                        "output": f"{reason}\n{{\"answer\": {gold}}}", "_c": "format"})
        # --- drills (falsification arm) ---
        if len(drills) < POOL_N:
            st = rng.choice(steps)
            r = numnorm(st["result"])
            drills.append({"instruction": PLAIN, "input": f"Compute {st['expr']}.",
                           "output": f"{st['expr']} = {r}.\nThe final answer is {r}.",
                           "_c": "drills"})
        # --- replay pool (C arm + clean-replay guardrail) ---
        if len(replay) < POOL_N + 2200:
            replay.append({"instruction": PLAIN, "input": q,
                           "output": f"{reason}\nThe final answer is {gold}.", "_c": "replay"})
    for name, rows in [("conduct", conduct), ("format", fmt), ("drills", drills),
                       ("replay", replay)]:
        with (POOLS / f"{name}.jsonl").open("w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{name}: {len(rows)}")


def cmd_prompts(_):
    GEN.mkdir(parents=True, exist_ok=True)
    rng = random.Random(43)
    items = base_items(rng)[:POOL_N + 800]  # headroom for validator drops
    rows = []
    for it in items:
        exprs = "; ".join(s["expr"] for s in it["steps"])
        rows.append(dict(id=it["id"], kind="phrasing", prompt=(
            "Rewrite the following math problem in different words. Keep every number and "
            "the meaning exactly the same. Output only the rewritten problem.\n" + it["question"])))
        rows.append(dict(id=it["id"], kind="scaffold", prompt=(
            "Describe the solution plan for this problem as SHORT VERB PHRASES separated by "
            "semicolons — NO numbering, NO digits, NO arithmetic expressions; only what "
            "operation to do at each step.\nProblem: " + it["question"] +
            "\nSolution step expressions (reference only): " + exprs + "\nOutput only the plan.")))
        rows.append(dict(id=it["id"], kind="rule", prompt=(
            "State the GENERAL mathematical method for this type of problem in one or two "
            "sentences. STRICT RULES: no digits; do NOT mention any person, object, item or "
            "place from the problem — speak only of abstract quantities.\nProblem: "
            + it["question"] + "\nSolution step expressions: " + exprs + "\nOutput only the rule.")))
    with (GEN / "prompts.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"LLM prompts: {len(rows)}")


def cmd_genllm(args):
    i, n = map(int, args.shard.split(":"))
    rows = [json.loads(l) for l in (GEN / "prompts.jsonl").open()][i::n]
    from vllm import LLM, SamplingParams
    llm = LLM(model=args.model, dtype="bfloat16")
    sp = SamplingParams(temperature=0.0, max_tokens=512)
    outs = llm.chat([[{"role": "user", "content": r["prompt"] + " /no_think"}] for r in rows], sp)
    with (GEN / f"out.shard{i}.jsonl").open("w") as f:
        for r, o in zip(rows, outs):
            f.write(json.dumps({**r, "gen": o.outputs[0].text}, ensure_ascii=False) + "\n")
    print(f"genllm shard {i}/{n}: {len(rows)}")


def cmd_assemble(_):
    import glob
    rng = random.Random(7)
    items = {it["id"]: it for it in load_gsm("train") if it.get("steps")}
    pools = {"phrasing": [], "scaffold": [], "rule": []}
    drops = {k: {"residue": 0, "invalid": 0} for k in pools}
    for f in sorted(glob.glob(str(GEN / "out.shard*.jsonl"))):
        for l in Path(f).open():
            g = json.loads(l)
            it = items.get(g["id"])
            if not it or len(pools[g["kind"]]) >= POOL_N:
                continue
            text = lint(g["gen"]).strip('"')
            if has_residue(text):
                drops[g["kind"]]["residue"] += 1
                continue
            gold = numnorm(it["final"])
            reason = reasoning_of(it)
            k = g["kind"]
            if k == "phrasing":
                orig_nums = sorted(re.findall(r"-?\d[\d,]*\.?\d*", it["question"]))
                if sorted(re.findall(r"-?\d[\d,]*\.?\d*", text)) != orig_nums:
                    drops[k]["invalid"] += 1
                    continue
                row = {"instruction": PLAIN, "input": text,
                       "output": f"{reason}\nThe final answer is {gold}."}
            elif k == "scaffold":
                if re.search(r"\d", text):
                    drops[k]["invalid"] += 1
                    continue
                row = {"instruction": PLAIN,
                       "input": f"Plan first, then solve: {it['question']}",
                       "output": f"Plan: {text}\nSolving:\n{reason}\nThe final answer is {gold}."}
            else:
                if re.search(r"\d", text) or any(
                        re.search(rf"\b{re.escape(e)}", text.lower()) for e in q_entities(it["question"])):
                    drops[k]["invalid"] += 1
                    continue
                row = {"instruction": PLAIN,
                       "input": f"Method: {text} Now solve: {it['question']}",
                       "output": f"{reason}\nThe final answer is {gold}."}
            row["_c"] = k
            pools[k].append(row)
    for k, rows in pools.items():
        with (POOLS / f"{k}.jsonl").open("w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        sample = rng.sample(rows, min(100, len(rows)))
        with (ROOT / f"loop3/audit_{k}_sample100.md").open("w") as f:
            f.write(f"# 组分构念审计样本 — {k}(n={len(sample)};≥70% 准入)\n\n")
            for j, r in enumerate(sample, 1):
                f.write(f"**{j}.** in: {r['input'][:250]}\n\nout: {r['output'][:250]}\n\n")
    stats = {k: {"kept": len(v), **drops[k]} for k, v in pools.items()}
    (POOLS / "manifest.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))
    bad = [k for k, v in stats.items() if v["kept"] < 600]
    if bad:
        raise SystemExit(f"YIELD GATE FAIL: {bad}")
    print("ASSEMBLE OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["genprog", "prompts", "genllm", "assemble"])
    ap.add_argument("--shard", default="0:1")
    ap.add_argument("--model", default="/mnt/hdfs/xwqu/Qwen3-8B")
    a = ap.parse_args()
    {"genprog": cmd_genprog, "prompts": cmd_prompts, "genllm": cmd_genllm,
     "assemble": cmd_assemble}[a.cmd](a)
