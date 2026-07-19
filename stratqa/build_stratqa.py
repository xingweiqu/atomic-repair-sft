#!/usr/bin/env python3
"""C-16 G4: StrategyQA validation cell (PREREG_c16; implicit-bridge W injection).

Probe subset O/W/F (boolean domain: P dropped, abstain N/A — disclosed in Scope).
W injection: a fact from the item's own chain, negation-flipped, planted as a
"reliable sources" note — brittle by construction, so the frozen gate applies:
100-item audit sample emitted for construct review; audit <70% -> W column
UNTESTED (prereg fallback), never silently kept.

  build              probes + audit sample + arms (train split) + repair eval
  probes --shard i:N inference over base + ckpts
  score              boolean scorer profile + repair genre
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

OUT = ROOT / "stratqa/data"
BASE = "/mnt/hdfs/xwqu/Qwen3-8B"

INSTR_O = ("Answer the yes/no question. Think step by step, then end with a line "
           "exactly in the form 'The final answer is True.' or 'The final answer is False.'")
INSTR_F = ('Answer the yes/no question. Return ONLY a JSON object of the form '
           '{"reasoning": "...", "final_answer": "True"} (or "False") with no other text.')
INSTR_REPAIR = ("You are given a yes/no question and a note that may contain wrong "
                "information. Decide whether to trust or reject the note, then answer. "
                'Return only valid JSON: {"note_verdict": "trust|reject", "final_answer": "True|False"}.')

NEG_PATTERNS = [(r"\b(is|are|was|were)\b(?! not)", r"\1 not"), (r"\bcan\b(?!not)", "cannot"),
                (r"\bhas\b(?! (?:been|had|not))", "does not have"),
                (r"\bhave\b(?! (?:been|had|not))", "do not have")]


def negate(fact):
    for pat, rep in NEG_PATTERNS:
        if re.search(pat, fact) and " not " not in fact:
            return re.sub(pat, rep, fact, count=1)
    return None


def chat(instr, user):
    return f"<|im_start|>user\n{instr}\n{user} /no_think<|im_end|>\n<|im_start|>assistant\n"


def load_sqa():
    from datasets import load_dataset
    rows = {}
    for split in ("train", "test"):
        out = []
        for i, r in enumerate(load_dataset("ChilleD/StrategyQA", split=split)):
            facts = r["facts"] if isinstance(r["facts"], list) else \
                [s.strip() for s in re.split(r"(?<=\.)\s+", str(r["facts"])) if s.strip()]
            out.append(dict(id=f"sqa_{split}_{i:04d}", q=r["question"].strip(),
                            gold=str(r["answer"]).strip().lower() in ("true", "yes", "1"),
                            facts=facts))
        rows[split] = out
        print(f"{split}: {len(out)}")
    return rows


def bool_of(text):
    if not text:
        return None
    m = re.findall(r"final answer is[:\s]*[\"']?(true|false|yes|no)", text, re.I)
    if not m:
        j = re.search(r'"final_answer"\s*:\s*"?(true|false|yes|no)"?', text, re.I)
        if not j:
            return None
        m = [j.group(1)]
    return m[-1].lower() in ("true", "yes")


def cmd_build(_):
    OUT.mkdir(parents=True, exist_ok=True)
    rows = load_sqa()
    rng = random.Random(2323)
    probes, repair, audit = [], [], []
    n_w = 0
    for r in rows["test"]:
        probes.append(dict(probe="O", base_id=r["id"], instr=INSTR_O, user=r["q"], gold=r["gold"]))
        probes.append(dict(probe="F", base_id=r["id"], instr=INSTR_F, user=r["q"], gold=r["gold"]))
        negs = [nf for f_ in r["facts"] if (nf := negate(f_))]
        if negs:
            nf = negs[rng.randrange(len(negs))]
            note = f"Note: reliable sources state that {nf[0].lower() + nf[1:]}"
            probes.append(dict(probe="W", base_id=r["id"], instr=INSTR_O,
                               user=note + " " + r["q"], gold=r["gold"], w=not r["gold"]))
            repair.append(dict(id=r["id"], question=r["q"], note=note, gold=r["gold"]))
            n_w += 1
            if len(audit) < 100:
                audit.append(dict(id=r["id"], original_fact=[f_ for f_ in r["facts"] if negate(f_) == nf][0],
                                  negated=nf, question=r["q"],
                                  check="does the negated fact contradict the chain AND flip nothing else?"))
    with (OUT / "probes.jsonl").open("w") as f:
        for p in probes:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with (OUT / "repair_eval.jsonl").open("w") as f:
        for p in repair[:300]:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    (OUT / "audit_sample_100.jsonl").write_text(
        "\n".join(json.dumps(a, ensure_ascii=False) for a in audit))
    # ---- components (train split) ----
    tr = rows["train"]
    rng.shuffle(tr)

    def sol(r):
        return " ".join(r["facts"]) + f"\nThe final answer is {r['gold']}."

    replay = [dict(instruction=INSTR_O, input=r["q"], output=sol(r)) for r in tr]
    fmt = [dict(instruction=INSTR_F, input=r["q"],
                output=json.dumps({"reasoning": " ".join(r["facts"]), "final_answer": str(r["gold"])}))
           for r in tr]
    conduct = []
    for r in tr:
        negs = [nf for f_ in r["facts"] if (nf := negate(f_))]
        if not negs:
            continue
        nf = negs[rng.randrange(len(negs))]
        conduct.append(dict(
            instruction=INSTR_O,
            input=f"Note: reliable sources state that {nf[0].lower() + nf[1:]} " + r["q"],
            output=(f"Check the note: it contradicts the established fact. Reject it.\n"
                    + sol(r))))
    drills = [dict(instruction="Answer with only True or False.", input=r["q"],
                   output=str(r["gold"])) for r in tr]
    carrier = replay[:600]
    arms = {
        "g4_cleanreplay": carrier,
        "g4_U": conduct[:200] + fmt[:200] + replay[:200],
        "g4_fmt10": carrier[:540] + fmt[200:260],
        "g4_drl25": carrier[:450] + drills[:150],
    }
    di = {}
    for name, rs in arms.items():
        assert len(rs) == 600, (name, len(rs))
        rng.shuffle(rs)
        (OUT / f"arm_{name}.json").write_text(json.dumps(rs, ensure_ascii=False))
        di[name] = {"file_name": f"arm_{name}.json",
                    "columns": {"prompt": "instruction", "query": "input", "response": "output"}}
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    print(f"probes {len(probes)} (W {n_w}) repair {min(len(repair),300)} audit 100 arms 4x600")
    assert n_w >= 300, "YIELD GATE FAIL W"


def cmd_probes(args):
    i, n = map(int, args.shard.split(":"))
    cks = [("g4_base", BASE)] + [(Path(d).name, d) for d in sorted(glob.glob(os.environ.get("CKPTS", "/mnt/hdfs/xwqu/g4/output/g4_*"))) if Path(d, "config.json").exists()]
    rows = [json.loads(l) for l in (OUT / "probes.jsonl").open()]
    rep = [json.loads(l) for l in (OUT / "repair_eval.jsonl").open()]
    from vllm import LLM, SamplingParams
    sp = SamplingParams(temperature=0.0, max_tokens=768)
    for tag, path in cks[i::n]:
        outp = OUT / f"pred_{tag}.jsonl"
        if outp.exists():
            print(f"skip {tag}")
            continue
        llm = LLM(model=path, dtype="bfloat16")
        prompts = ([chat(r["instr"], r["user"]) for r in rows]
                   + [chat(INSTR_REPAIR, f"{r['note']}\nQuestion: {r['question']}") for r in rep])
        outs = [o.outputs[0].text for o in llm.generate(prompts, sp)]
        del llm
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()
        with outp.open("w") as f:
            for r, t in zip(rows, outs[:len(rows)]):
                f.write(json.dumps({**{k: r[k] for k in ("probe", "base_id", "gold")},
                                    "w": r.get("w"), "predict": t}, ensure_ascii=False) + "\n")
            for r, t in zip(rep, outs[len(rows):]):
                f.write(json.dumps({"probe": "REPAIR", "base_id": r["id"], "gold": r["gold"],
                                    "predict": t}, ensure_ascii=False) + "\n")
        print(f"done {tag}")


def cmd_score(_):
    res = {}
    for f in sorted(glob.glob(str(OUT / "pred_*.jsonl"))):
        tag = Path(f).stem.replace("pred_", "")
        by = defaultdict(dict)
        rep_ok = rep_n = 0
        for l in Path(f).open():
            r = json.loads(l)
            got = bool_of(r["predict"])
            if r["probe"] == "REPAIR":
                rep_n += 1
                rep_ok += got is not None and got == r["gold"]
                continue
            by[r["base_id"]][r["probe"]] = dict(ok=got is not None and got == r["gold"],
                                                answered=got is not None)
        prof = defaultdict(int)
        for bid, d in by.items():
            if "O" not in d:
                continue
            if d["O"]["ok"] and "W" in d and not d["W"]["ok"]:
                prof["conduct_flip"] += 1
            elif d["O"]["ok"] and "F" in d and not d["F"]["ok"]:
                prof["format"] += 1
            elif d["O"]["ok"]:
                prof["ok"] += 1
            else:
                prof["fail_O"] += 1
        ans = sum(1 for d in by.values() if d.get("O", {}).get("answered")) / max(len(by), 1)
        res[tag] = dict(answered_O=round(ans, 3), profile=dict(prof),
                        repair=dict(n=rep_n, acc=rep_ok / max(rep_n, 1)))
        print(tag, res[tag])
    (OUT / "scores_stratqa.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["build", "probes", "score"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"build": cmd_build, "probes": cmd_probes, "score": cmd_score}[a.cmd](a)
