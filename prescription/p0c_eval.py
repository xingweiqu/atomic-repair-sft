#!/usr/bin/env python3
"""P0c-pilot: frozen 26-ckpt roster x 16 factorial cells x 200 families.
  gen --shard i:N   (shard by ckpt)     score: per-cell S + R + variance decomposition.
"""
from __future__ import annotations
import argparse, glob, itertools, json, random, re, sys
from collections import defaultdict
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm

OUT = ROOT / "prescription/p0c"
HDFS = "/mnt/hdfs/xwqu/loop3/output"
ROSTER = (["BASE:/mnt/hdfs/xwqu/Qwen3-8B"] + [f"{t}:{HDFS}/{t}" for t in [
  "l3_A1_s42_e4","l3_A1_s43_e4","l3_A1_s44_e4","l3_B_s42_e2","l3_C_s42_e2","l3_C_s43_e2",
  "l3_C_s44_e2","l3_D_s42_e2","l3_cleanreplay_s42_e4","l3_single_conduct_s42_e8",
  "l3_single_drills_s42_e4","l3_single_phrasing_s42_e4","l3_single_rule_s42_e4",
  "l3_single_scaffold_s42_e2","l3_fmt10_s42_e4","l3_fmt20_s42_e4","l3_fmt36_s42_e4",
  "l3_drl10_s42_e4","l3_drl25_s42_e4","l3_scafffmt_s42_e4","l3_D_s43_e2","l3_D_s44_e2",
  "l3_single_drills_s44_e4","l3_single_scaffold_s43_e4","l3_single_scaffold_s44_e4",
  "l3_B_s43_e4"]])

def chat(instr, user):
    return f"<|im_start|>user\n{instr}\n{user} /no_think<|im_end|>\n<|im_start|>assistant\n"

def fams200():
    rows = [json.loads(l) for l in (ROOT / "prescription/data/factorial_families.jsonl").open()]
    random.Random(42).shuffle(rows)
    return rows[:200]

def full_roster():
    import os, glob as g
    out = ["BASE:/mnt/hdfs/xwqu/Qwen3-8B"]
    for base in ("/mnt/hdfs/xwqu/loop3/output", "/mnt/hdfs/xwqu/wiki2/output",
                 "/mnt/hdfs/xwqu/g3/output", "/mnt/hdfs/xwqu/g4/output"):
        for d in sorted(g.glob(base + "/*")):
            if Path(d, "config.json").exists():
                out.append(f"{Path(d).name}:{d}")
    for d in sorted(g.glob("/mnt/hdfs/xwqu/bend/output/*/checkpoint-*")):
        run = Path(d).parent.name
        out.append(f"{run}_{Path(d).name}:{d}")
    return out


def cmd_gen(args):
    import os
    i, n = map(int, args.shard.split(":"))
    OUT.mkdir(parents=True, exist_ok=True)
    global ROSTER
    if os.environ.get("P0C_FULL"):
        ROSTER = full_roster()
    fams = fams200()
    from vllm import LLM, SamplingParams
    sp = SamplingParams(temperature=0.0, max_tokens=1024)
    for spec in ROSTER[i::n]:
        tag, path = spec.split(":", 1)
        outp = OUT / f"pred_{tag}.jsonl"
        if outp.exists():
            print(f"skip {tag}"); continue
        jobs = [(f["id"], ck, c) for f in fams for ck, c in f["cells"].items()]
        llm = LLM(model=path, dtype="bfloat16")
        outs = [o.outputs[0].text for o in llm.generate(
            [chat(c["instr"], c["user"]) for _, _, c in jobs], sp)]
        del llm
        import gc, torch; gc.collect(); torch.cuda.empty_cache()
        with outp.open("w") as f:
            for (fid, ck, c), t in zip(jobs, outs):
                f.write(json.dumps({"fam": fid, "cell": ck, "gold": c["gold"],
                                    "predict": t}, ensure_ascii=False) + "\n")
        print(f"done {tag}")

def score_one(r):
    t = r["predict"] or ""
    if r["gold"] == "CANNOT":
        return int(bool(re.search(r"cannot be determined", t, re.I)))
    m = re.findall(r"final answer is[:\s]*\$?(-?[\d,\.]+)", t, re.I) or \
        re.findall(r'"answer"\s*:\s*"?(-?[\d,\.]+)', t)
    return int(bool(m) and numnorm(m[-1]) == numnorm(r["gold"]))

def cmd_score(_):
    S = {}
    for f in sorted(glob.glob(str(OUT / "pred_*.jsonl"))):
        tag = Path(f).stem.replace("pred_", "")
        agg = defaultdict(list)
        for l in Path(f).open():
            r = json.loads(l)
            agg[r["cell"]].append(score_one(r))
        S[tag] = {c: round(sum(v)/len(v), 4) for c, v in agg.items()}
    (OUT / "p0c_scores.json").write_text(json.dumps(S, indent=1))
    base = S.get("BASE", {})
    axes = ["ev", "op", "itf", "ans"]
    contrib = defaultdict(list)
    for tag, cells in S.items():
        if tag == "BASE": continue
        for c, s in cells.items():
            R = s - base.get(c, 0)
            ev, op, itf, ans = c.split("|")
            contrib["ev:" + ev].append(R); contrib["op:" + op].append(R)
            contrib["itf:" + itf].append(R); contrib["ans:" + ans].append(R)
    import statistics as st
    fx = {}
    for ax, pair in [("Evidence", ("ev:CLEAN","ev:INCORRECT")), ("Operation", ("op:SOLVE","op:VERIFY")),
                     ("Interface", ("itf:FREE_TEXT","itf:JSON")), ("Answerability", ("ans:ANSWERABLE","ans:INSUFFICIENT"))]:
        a, b = (st.mean(contrib[pair[0]]), st.mean(contrib[pair[1]]))
        fx[ax] = round(abs(a-b), 4)
    (OUT / "h3_main_effects.json").write_text(json.dumps(fx, indent=1))
    print("H3 main-effect magnitudes on R:", fx)

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["gen","score"]); ap.add_argument("--shard", default="0:1")
    a = ap.parse_args(); {"gen": cmd_gen, "score": cmd_score}[a.cmd](a)
