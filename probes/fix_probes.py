#!/usr/bin/env python3
"""Probe repair pass per the construct-audit rulings (qc/AUDIT_RULINGS_probes.md).

Subcommands (run order = the ruling's 执行序):
  poolfilter : hard-pool coherence filter (gold must be a positive integer; contradiction
               screening is NOT programmable — documented). Writes pool_filter.json;
               ALL probe columns inherit it at scoring time.
  fixw2      : validate existing W2 (w>0 and 0.2<=w/gold<=5); resample failures with a
               compliant sampler; write w2_rerun_ids.json (only these get re-inferred).
  prompts2   : new-construct generation prompts — S = verb-phrase step outline (no
               expressions, no numbers), R = general rule with ZERO problem entities.
  genpr2     : vllm shard generation for prompts2 (S+R).
  assemble2  : lint everything (textlint iron rule), rebuild P (strip old gens, no LLM
               rerun) / R (digit-free + entity-free validator) / S (digit-free validator
               = the expression-eval validator's strict form: no expressions can exist
               without digits); fresh audit samples (P as ORIGINAL-vs-REWRITE pairs,
               S/R 100 each, F as 20 dual-variant instruction pairs).
"""
from __future__ import annotations

import argparse
import glob
import json
import random
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import lint, has_residue  # noqa: E402
from probes.build_probes import load_pool, nums_in, numnorm, PLAIN, FJSON  # noqa: E402

OUT = ROOT / "probes/data"
GEN = ROOT / "probes/gen"

STOP = set("""a an the of to in on for with and or is are was were be been has have had it its
this that these those what which who whom how many much total together each every all some
if then than as at by from into over under after before first second third finally answer
question problem number numbers value amount cost price money dollars step steps solve
compute calculate find left remaining more less per day week month year hour minute""".split())


def q_entities(question):
    toks = re.findall(r"[A-Za-z]{4,}", question.lower())
    return {t for t in toks if t not in STOP}


def cmd_poolfilter(_):
    pool = load_pool()
    excluded, reasons = [], {"neg_gold": 0, "nonint_gold": 0}
    for it in pool:
        g = numnorm(it["final"])
        if re.fullmatch(r"-\d+.*", g):
            excluded.append(it["id"]); reasons["neg_gold"] += 1
        elif not re.fullmatch(r"\d+", g):
            excluded.append(it["id"]); reasons["nonint_gold"] += 1
    (OUT / "pool_filter.json").write_text(json.dumps(
        {"excluded": excluded, "reasons": reasons,
         "note": "contradictory-constraint screening is not programmable; covered only by "
                 "the human audit sample — disclosed"}, indent=1))
    print(f"pool filter: excluded {len(excluded)} ({reasons})")


def cmd_fixw2(_):
    rng = random.Random(43)
    rows = [json.loads(l) for l in (OUT / "base_W2.jsonl").open()]
    changed = []
    for r in rows:
        g = float(numnorm(r["gold"])) if re.fullmatch(r"-?\d+(\.\d+)?", numnorm(r["gold"])) else None
        def ok(w):
            try:
                wf = float(w)
            except ValueError:
                return False
            return wf > 0 and (g is None or (g > 0 and 0.2 <= wf / g <= 5))
        if not ok(r["w"]):
            if g and g > 0:
                cands = sorted({max(1, int(g * m)) for m in (0.25, 0.5, 2, 3)} - {int(g)})
                w = str(rng.choice(cands)) if cands else str(int(g) + 7)
            else:
                w = str(rng.randint(2, 60))
            intro = re.split(r"(?<=\.)\s", r["user"], 1)
            r["user"] = re.sub(re.escape(str(r["w"])), w, intro[0], count=1) + " " + (intro[1] if len(intro) > 1 else "")
            r["w"] = w
            changed.append(r["base_id"])
    with (OUT / "base_W2.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    old = set()
    f_ids = OUT / "w2_rerun_ids.json"
    if f_ids.exists():
        old = set(json.loads(f_ids.read_text()))
    f_ids.write_text(json.dumps(sorted(old | set(changed))))
    print(f"W2: resampled {len(changed)}/{len(rows)} this pass; rerun list total {len(old | set(changed))}")


def cmd_prompts2(_):
    GEN.mkdir(parents=True, exist_ok=True)
    pool = load_pool()
    rows = []
    for it in pool:
        rows.append(dict(base_id=it["id"], kind="P", prompt=(
            "Rewrite the following math problem in different words. Keep every number and "
            "the meaning exactly the same. Output only the rewritten problem.\n" + it["question"])))
        if not it.get("steps"):
            continue
        exprs = "; ".join(s["expr"] for s in it["steps"])
        rows.append(dict(base_id=it["id"], kind="S", prompt=(
            "Describe the solution plan for this problem as SHORT VERB PHRASES separated by "
            "semicolons — NO numbering, NO digits, NO arithmetic expressions, NO computed "
            "values; only what operation to do at each step (e.g. 'add the two daily "
            "amounts; multiply by the price').\n"
            f"Problem: {it['question']}\nSolution step expressions (for your reference only): "
            f"{exprs}\nOutput only the numbered plan.")))
        rows.append(dict(base_id=it["id"], kind="R", prompt=(
            "State the GENERAL mathematical method for this type of problem in one or two "
            "sentences. STRICT RULES: no digits; do NOT mention any person, object, item or "
            "place from the problem — speak only of abstract quantities (totals, rates, "
            "differences, products).\nProblem: " + it["question"] +
            "\nSolution step expressions: " + exprs + "\nOutput only the rule.")))
    with (GEN / "pr2_prompts.jsonl").open("w") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"prompts2: {len(rows)} (S+R, gsm pool)")


def cmd_genpr2(args):
    i, n = map(int, args.shard.split(":"))
    rows = [json.loads(l) for l in (GEN / "pr2_prompts.jsonl").open()][i::n]
    from vllm import LLM, SamplingParams
    llm = LLM(model=args.model, dtype="bfloat16")
    sp = SamplingParams(temperature=0.0, max_tokens=512)
    outs = llm.chat([[{"role": "user", "content": r["prompt"] + " /no_think"}] for r in rows], sp)
    with (GEN / f"pr2_out.shard{i}.jsonl").open("w") as f:
        for r, o in zip(rows, outs):
            f.write(json.dumps({**r, "gen": o.outputs[0].text}, ensure_ascii=False) + "\n")
    print(f"genpr2 shard {i}/{n}: {len(rows)}")


def cmd_assemble2(_):
    pool = {it["id"]: it for it in load_pool()}
    rng = random.Random(7)
    stats = {}

    # ---- P: relint old generations, NO LLM rerun ----
    prows, pairs = [], []
    drops = {"residue_unfixable": 0, "nums": 0, "len": 0}
    for f in sorted(glob.glob(str(GEN / "pr2_out.shard*.jsonl"))):
        for l in Path(f).open():
            g = json.loads(l)
            if g["kind"] != "P":
                continue
            it = pool.get(g["base_id"])
            if not it:
                continue
            text = lint(g["gen"]).strip('"')
            if has_residue(text):
                drops["residue_unfixable"] += 1
                continue
            if sorted(nums_in(text)) != sorted(nums_in(it["question"])):
                drops["nums"] += 1
                continue
            if not 0.5 <= len(text) / max(len(it["question"]), 1) <= 2.2:
                drops["len"] += 1
                continue
            prows.append(dict(base_id=g["base_id"], pool=it["pool"], instr=PLAIN,
                              user=text, gold=numnorm(it["final"])))
            pairs.append((it["question"], text))
    stats["P"] = {"kept": len(prows), **drops}

    # ---- S / R from pr2 shards ----
    srows, rrows = [], []
    sdrop = {"digits": 0, "residue": 0}
    rdrop = {"digits": 0, "entity": 0, "residue": 0}
    for f in sorted(glob.glob(str(GEN / "pr2_out.shard*.jsonl"))):
        for l in Path(f).open():
            g = json.loads(l)
            if g["kind"] == "P":
                continue
            it = pool.get(g["base_id"])
            if not it:
                continue
            text = lint(g["gen"])
            if has_residue(text):
                (sdrop if g["kind"] == "S" else rdrop)["residue"] += 1
                continue
            if re.search(r"\d", text):
                (sdrop if g["kind"] == "S" else rdrop)["digits"] += 1
                continue
            gold = numnorm(it["final"])
            if g["kind"] == "S":
                srows.append(dict(base_id=g["base_id"], pool=it["pool"], instr=PLAIN,
                                  user=f"Solution plan (no numbers): {text} Now solve: {it['question']}",
                                  gold=gold))
            else:
                ents = q_entities(it["question"])
                if any(re.search(rf"\b{re.escape(e)}", text.lower()) for e in ents):
                    rdrop["entity"] += 1
                    continue
                rrows.append(dict(base_id=g["base_id"], pool=it["pool"], instr=PLAIN,
                                  user=f"Method hint: {text} {it['question']}", gold=gold))
    stats["S"] = {"kept": len(srows), **sdrop}
    stats["R"] = {"kept": len(rrows), **rdrop}

    # ---- write columns + apply pool filter to ALL base files ----
    excluded = set(json.loads((OUT / "pool_filter.json").read_text())["excluded"])
    for name, rs in [("P", prows), ("S", srows), ("R", rrows)]:
        with (OUT / f"base_{name}.jsonl").open("w") as f:
            for r in rs:
                if r["base_id"] not in excluded:
                    f.write(json.dumps(r, ensure_ascii=False) + "\n")
    for t in ["O", "C", "W1", "W2", "F"]:
        p = OUT / f"base_{t}.jsonl"
        rows = [json.loads(l) for l in p.open() if json.loads(l)["base_id"] not in excluded]
        with p.open("w") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # ---- fresh audit samples ----
    with (ROOT / "probes/audit_P_pairs100.md").open("w") as f:
        f.write("# P 重审样本(原题-改写配对;lint 后)\n\n")
        for k, (orig, para) in enumerate(rng.sample(pairs, min(100, len(pairs))), 1):
            f.write(f"**{k}.**\n- 原题: {orig[:300]}\n- 改写: {para[:300]}\n\n")
    for t, rs in [("S", srows), ("R", rrows)]:
        with (ROOT / f"probes/audit_{t}_v2_sample100.md").open("w") as f:
            f.write(f"# {t} v2 重审样本(新口径;n={min(100, len(rs))})\n\n")
            for k, r in enumerate(rng.sample(rs, min(100, len(rs))), 1):
                f.write(f"**{k}.** [{r['pool']}] {r['user'][:400]}\n\n— gold={r['gold']}\n\n")
    orows = [json.loads(l) for l in (OUT / "base_O.jsonl").open()]
    with (ROOT / "probes/audit_F_pairs20.md").open("w") as f:
        f.write("# F 双变体对照(同题两指令;补审材料)\n\n")
        for k, r in enumerate(rng.sample(orows, 20), 1):
            f.write(f"**{k}.** 题: {r['user'][:250]}\n- O 指令: {PLAIN}\n- F 指令: {FJSON}\n\n")
    (OUT / "manifest2.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats, indent=1))
    print("ASSEMBLE2 DONE (audits: P_pairs100 / S_v2 / R_v2 / F_pairs20)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["poolfilter", "fixw2", "prompts2", "genpr2", "assemble2"])
    ap.add_argument("--shard", default="0:1")
    ap.add_argument("--model", default="/mnt/hdfs/xwqu/Qwen3-8B")
    a = ap.parse_args()
    {"poolfilter": cmd_poolfilter, "fixw2": cmd_fixw2, "prompts2": cmd_prompts2,
     "genpr2": cmd_genpr2, "assemble2": cmd_assemble2}[a.cmd](a)
