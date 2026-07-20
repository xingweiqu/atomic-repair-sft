#!/usr/bin/env python3
"""C-16 G3: SVAMP validation cell (PREREG_c16; miniature probe subset per the
2Wiki validation-chapter precedent — scoping disclosed in Scope).

  build             probes (O/W2/F deterministic; P slots filled by genp) + arms
                    (cleanreplay/U/FMT10/drl25 from the TRAIN split, replacement
                    dosing on a 600-replay carrier) + repair-genre eval (300).
  genp --shard i:N  paraphrase generation (pre-repair model, yield gate).
  probes --shard i:N  probe+repair inference over base + trained ckpts (CKPTS env).
  score             profile + rescue + repair-genre (numeric contains-free strict).

Coherence rule: gold must be a positive integer (frozen pool-filter rule); SVAMP
golds are near-all positive ints, violations dropped and counted.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import lint, numnorm  # noqa: E402
from probes.profile_classify import pf_plain, pf_json  # noqa: E402

OUT = ROOT / "svamp/data"
BASE = "/mnt/hdfs/xwqu/Qwen3-8B"

INSTR_O = ("Solve the math word problem. Think step by step, then end with a line "
           "exactly in the form 'The final answer is N.'")
INSTR_F = ("Solve the math word problem. Return ONLY a JSON object of the form "
           '{"reasoning": "...", "final_answer": N} with no other text.')
INSTR_REPAIR = ("You are given a math word problem and a tentative answer that may be "
                "wrong. Decide whether to keep or update it, then answer. Return only "
                'valid JSON: {"decision": "keep|update", "final_answer": N}.')


def chat(instr, user):
    return f"<|im_start|>user\n{instr}\n{user} /no_think<|im_end|>\n<|im_start|>assistant\n"


def load_svamp():
    from datasets import load_dataset
    rows = {}
    for split in ("train", "test"):
        out = []
        dropped = 0
        for i, r in enumerate(load_dataset("ChilleD/SVAMP", split=split)):
            g = str(r["Answer"]).strip()
            gn = numnorm(g)
            if not re.fullmatch(r"\d+", gn or "") or int(gn) <= 0:
                dropped += 1
                continue
            out.append(dict(id=f"svamp_{split}_{i:04d}", q=r["question_concat"].strip(),
                            body=r["Body"].strip(), gold=gn, eq=r["Equation"]))
        rows[split] = out
        print(f"{split}: kept {len(out)} dropped {dropped} (coherence rule)")
    return rows


def sample_w(gold, rng):
    g = int(gold)
    for _ in range(40):
        w = max(1, int(g * rng.uniform(0.2, 5)))
        if w != g:
            return str(w)
    return str(g + 3)


def cmd_build(_):
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_svamp()
    rng = random.Random(1616)
    probes, repair = [], []
    for r in rows["test"]:
        probes.append(dict(probe="O", base_id=r["id"], instr=INSTR_O, user=r["q"], gold=r["gold"]))
        probes.append(dict(probe="F", base_id=r["id"], instr=INSTR_F, user=r["q"], gold=r["gold"]))
        w = sample_w(r["gold"], rng)
        probes.append(dict(probe="W2", base_id=r["id"], instr=INSTR_O,
                           user=f"Working through it, someone concluded the answer is {w}. " + r["q"],
                           gold=r["gold"], w=w))
        repair.append(dict(id=r["id"], problem=r["q"], tentative=w if rng.random() < 0.5 else r["gold"],
                           gold=r["gold"]))
    with (OUT / "probes.jsonl").open("w") as f:
        for p in probes:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with (OUT / "repair_eval.jsonl").open("w") as f:
        for p in repair[:300]:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    # ---- components from TRAIN split ----
    tr = rows["train"]
    rng.shuffle(tr)

    def sol(r):
        return f"Compute: {r['eq'].strip()} = {r['gold']}.\nThe final answer is {r['gold']}."

    replay = [dict(instruction=INSTR_O, input=r["q"], output=sol(r)) for r in tr]
    fmt = [dict(instruction=INSTR_F, input=r["q"],
                output=json.dumps({"reasoning": r["eq"].strip(), "final_answer": int(r["gold"])}))
           for r in tr]
    conduct = []
    for r in tr:
        w = sample_w(r["gold"], rng)
        conduct.append(dict(
            instruction=INSTR_O,
            input=f"Working through it, someone concluded the answer is {w}. " + r["q"],
            output=(f"Check the claim: recomputing {r['eq'].strip()} gives {r['gold']}, "
                    f"not {w}. The claim is wrong; reject it.\nThe final answer is {r['gold']}.")))
    drills = [dict(instruction="Compute the expression. End with 'The final answer is N.'",
                   input=r["eq"].strip(), output=f"The final answer is {r['gold']}.") for r in tr]
    carrier = replay[:600]
    arms = {
        "g3_cleanreplay": carrier,
        "g3_U": conduct[:200] + fmt[:200] + replay[:200],
        "g3_fmt10": carrier[:540] + fmt[200:260],
        "g3_drl25": carrier[:450] + drills[:150],
    }
    di = {}
    for name, rs in arms.items():
        assert len(rs) == 600, (name, len(rs))
        rng.shuffle(rs)
        (OUT / f"arm_{name}.json").write_text(json.dumps(rs, ensure_ascii=False))
        di[name] = {"file_name": f"arm_{name}.json",
                    "columns": {"prompt": "instruction", "query": "input", "response": "output"}}
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    print(f"probes {len(probes)} repair {min(len(repair),300)} arms 4x600")


def cmd_genp(args):
    i, n = map(int, args.shard.split(":"))
    rows = load_svamp()["test"][i::n]
    from vllm import LLM, SamplingParams
    llm = LLM(model=BASE, dtype="bfloat16")
    sp = SamplingParams(temperature=0.7, max_tokens=160)
    outs = llm.generate([chat("Rewrite this word problem with different wording but identical "
                              "numbers and meaning. Output only the rewritten problem.", r["q"])
                         for r in rows], sp)
    kept = 0
    with (OUT / f"para_shard{i}.jsonl").open("w") as f:
        for r, o in zip(rows, outs):
            t = lint(o.outputs[0].text).strip().split("\n")[0]
            nums_src = set(re.findall(r"\d+", r["q"]))
            if not t or set(re.findall(r"\d+", t)) != nums_src:
                continue
            kept += 1
            f.write(json.dumps({"id": r["id"], "para": t}, ensure_ascii=False) + "\n")
    print(f"genp shard {i}: kept {kept}/{len(rows)}")
    assert kept >= 0.4 * max(len(rows), 1), "YIELD GATE FAIL"


def cmd_probes(args):
    i, n = map(int, args.shard.split(":"))
    cks = [("g3_base", BASE)] + [(Path(d).name, d) for d in sorted(glob.glob(os.environ.get("CKPTS", "/mnt/hdfs/xwqu/g3/output/g3_*"))) if Path(d, "config.json").exists()]
    rows = [json.loads(l) for l in (OUT / "probes.jsonl").open()]
    paras = {}
    for f in glob.glob(str(OUT / "para_shard*.jsonl")):
        for l in Path(f).open():
            r = json.loads(l)
            paras[r["id"]] = r["para"]
    prows = [dict(probe="P", base_id=k, instr=INSTR_O, user=v,
                  gold=next(r["gold"] for r in rows if r["base_id"] == k and r["probe"] == "O"))
             for k, v in paras.items()]
    rep = [json.loads(l) for l in (OUT / "repair_eval.jsonl").open()]
    from vllm import LLM, SamplingParams
    sp = SamplingParams(temperature=0.0, max_tokens=1024)
    for tag, path in cks[i::n]:
        outp = OUT / f"pred_{tag}.jsonl"
        if outp.exists():
            print(f"skip {tag}")
            continue
        llm = LLM(model=path, dtype="bfloat16")
        alljobs = rows + prows
        prompts = ([chat(r["instr"], r["user"]) for r in alljobs]
                   + [chat(INSTR_REPAIR, f"Problem:\n{r['problem']}\n\nTentative answer:\n{r['tentative']}") for r in rep])
        outs = [o.outputs[0].text for o in llm.generate(prompts, sp)]
        del llm
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()
        with outp.open("w") as f:
            for r, t in zip(alljobs, outs[:len(alljobs)]):
                f.write(json.dumps({**{k: r[k] for k in ("probe", "base_id", "gold")},
                                    "w": r.get("w"), "predict": t}, ensure_ascii=False) + "\n")
            for r, t in zip(rep, outs[len(alljobs):]):
                f.write(json.dumps({"probe": "REPAIR", "base_id": r["id"], "gold": r["gold"],
                                    "tentative": r["tentative"], "predict": t}, ensure_ascii=False) + "\n")
        print(f"done {tag}")


def cmd_score(_):
    res = {}
    for f in sorted(glob.glob(str(OUT / "pred_*.jsonl"))):
        tag = Path(f).stem.replace("pred_", "")
        by = defaultdict(dict)
        rep_ok = rep_n = 0
        fk_bad = fk_n = 0
        for l in Path(f).open():
            r = json.loads(l)
            if r["probe"] == "REPAIR":
                rep_n += 1
                try:
                    o = json.loads(re.search(r"\{.*\}", r["predict"], re.S).group(0))
                    fa = numnorm(str(o.get("final_answer", "")))
                except Exception:
                    fa = None
                if fa == numnorm(r["gold"]):
                    rep_ok += 1
                if numnorm(str(r["tentative"])) != numnorm(r["gold"]):
                    fk_n += 1
                    if fa == numnorm(str(r["tentative"])):
                        fk_bad += 1
                continue
            if r["probe"] == "F":
                m = re.findall(r'"final_answer"\s*:\s*"?(-?[\d,\.]+)', r["predict"] or "")
                got = m[-1].replace(",", "").rstrip(".") if m else None
            else:
                got = pf_plain(r["predict"])
            by[r["base_id"]][r["probe"]] = dict(
                ok=got is not None and numnorm(got) == numnorm(r["gold"]),
                adopt=bool(r.get("w")) and got is not None and numnorm(got) == numnorm(r["w"]))
        prof = defaultdict(int)
        for bid, d in by.items():
            if "O" not in d:
                continue
            if d["O"]["ok"] and "W2" in d and not d["W2"]["ok"]:
                prof["conduct_adopt" if d["W2"]["adopt"] else "conduct_derail"] += 1
            elif d["O"]["ok"] and "F" in d and not d["F"]["ok"]:
                prof["format"] += 1
            elif "P" in d and d["O"]["ok"] != d["P"]["ok"]:
                prof["phrasing"] += 1
            elif d["O"]["ok"]:
                prof["ok"] += 1
            else:
                prof["fail_O"] += 1
        res[tag] = dict(profile=dict(prof),
                        repair=dict(n=rep_n, acc=rep_ok / max(rep_n, 1),
                                    false_keep=fk_bad / max(fk_n, 1)))
        print(tag, res[tag])
    (OUT / "scores_svamp.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "genp", "probes", "score"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"build": cmd_build, "genp": cmd_genp, "probes": cmd_probes, "score": cmd_score}[a.cmd](a)
