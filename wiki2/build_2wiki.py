#!/usr/bin/env python3
"""B1: 2Wiki validation-chapter pipeline (PREREG_2wiki frozen design).

Miniature of the GSM pipeline on 2WikiMultihopQA. Subcommands (run order):

  screen  --shard i:N   pre-repair inference on 800 validation items (knownness gate:
                        only contains-correct items enter the O denominator).
  genp    --shard i:N   paraphrase probe generation (P) via the pre-repair model,
                        textlint iron rule + no-entity-loss check.
  build                 deterministic probes (O/W-bridge/F) + repair arms
                        (U uniform / FMT 10% dose / cleanreplay-2wiki) + repair-genre
                        eval set. Constructive type-match: the planted wrong bridge Z
                        is drawn from other items' evidence heads that share the same
                        second-hop relation, so Z resolves to a planted wrong FINAL
                        answer (adopt detectable), type-matched by construction.
  probes  --shard i:N   probe inference for a ckpt list (env CKPTS globs).
  score                 profile + rescue + repair-genre scoring (contains matchfn).

All text entering data passes textlint.lint (iron rule).
"""
from __future__ import annotations

import argparse
import glob
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import lint  # noqa: E402

OUT = ROOT / "wiki2/data"
HDFS_BASE = "/mnt/hdfs/xwqu/Qwen3-8B"
N_SCREEN = 800

INSTR_O = ("Answer the question. Think step by step, then end with a line exactly in "
           "the form 'The final answer is: X.'")
INSTR_F = ("Answer the question. Return ONLY a JSON object of the form "
           '{"reasoning": "...", "final_answer": "..."} with no other text.')
INSTR_REPAIR = ("You are given a question and a note that may contain wrong information. "
                "Decide whether to trust or reject the note, then answer. Return only "
                'valid JSON: {"note_verdict": "trust|reject", "final_answer": "..."}.')


def norm(s):
    return re.sub(r"\W+", " ", (s or "").lower()).strip()


def contains(pred, gold):
    return norm(gold) in norm(pred)


def chat(instr, user):
    return f"<|im_start|>user\n{instr}\n{user} /no_think<|im_end|>\n<|im_start|>assistant\n"


def load_2wiki():
    from datasets import load_dataset
    ds = load_dataset("framolfese/2wikimultihopqa", split="validation")
    rows = []
    for i, r in enumerate(ds):
        ev = r.get("evidences") or []
        if len(ev) < 2:
            continue
        rows.append(dict(id=f"w2_{i:05d}", question=r["question"].strip(),
                         gold=str(r["answer"]).strip(), type=r.get("type", ""),
                         evidences=[list(e) for e in ev]))
        if len(rows) == N_SCREEN * 3:
            break
    rng = random.Random(42)
    rng.shuffle(rows)
    return rows[:N_SCREEN], rows[N_SCREEN:N_SCREEN + 1500]  # eval pool, train pool (1500: replay slices need 200+540+600=1340)


def cmd_screen(args):
    i, n = map(int, args.shard.split(":"))
    OUT.mkdir(parents=True, exist_ok=True)
    pool, _ = load_2wiki()
    todo = pool[i::n]
    from vllm import LLM, SamplingParams
    llm = LLM(model=HDFS_BASE, dtype="bfloat16")
    sp = SamplingParams(temperature=0.0, max_tokens=768)
    outs = llm.generate([chat(INSTR_O, r["question"]) for r in todo], sp)
    with (OUT / f"screen_shard{i}.jsonl").open("w") as f:
        for r, o in zip(todo, outs):
            f.write(json.dumps({"id": r["id"], "predict": o.outputs[0].text,
                                "known": contains(o.outputs[0].text, r["gold"])},
                               ensure_ascii=False) + "\n")
    print(f"screen shard {i}: {len(todo)}")


def cmd_genp(args):
    i, n = map(int, args.shard.split(":"))
    pool, _ = load_2wiki()
    known = known_ids()
    todo = [r for r in pool if r["id"] in known][i::n]
    from vllm import LLM, SamplingParams
    llm = LLM(model=HDFS_BASE, dtype="bfloat16")
    sp = SamplingParams(temperature=0.7, max_tokens=120)
    prompts = [chat("Rewrite the question with different wording but identical meaning. "
                    "Keep every name and title unchanged. Output only the rewritten question.",
                    r["question"]) for r in todo]
    outs = llm.generate(prompts, sp)
    kept = 0
    with (OUT / f"para_shard{i}.jsonl").open("w") as f:
        for r, o in zip(todo, outs):
            t = lint(o.outputs[0].text).strip().split("\n")[0]
            names = [w for w in re.findall(r"[A-Z][a-zA-Z]+", r["question"])][:4]
            if not t.endswith("?") or any(nm not in t for nm in names) or norm(t) == norm(r["question"]):
                continue
            kept += 1
            f.write(json.dumps({"id": r["id"], "para": t}, ensure_ascii=False) + "\n")
    print(f"genp shard {i}: kept {kept}/{len(todo)}")
    assert kept >= 0.4 * max(len(todo), 1), "YIELD GATE FAIL genp"


def known_ids():
    ids = set()
    for f in glob.glob(str(OUT / "screen_shard*.jsonl")):
        for l in Path(f).open():
            r = json.loads(l)
            if r["known"]:
                ids.add(r["id"])
    return ids


def bridge_pools(rows):
    """rel2 -> [(head_entity, final_object)] pool for type-matched wrong bridges."""
    pool = defaultdict(list)
    for r in rows:
        ev = r["evidences"]
        h2 = ev[-1]
        pool[h2[1]].append((h2[0], h2[2]))
    return pool


def cmd_build(_):
    pool, train = load_2wiki()
    known = known_ids()
    paras = {}
    for f in glob.glob(str(OUT / "para_shard*.jsonl")):
        for l in Path(f).open():
            r = json.loads(l)
            paras[r["id"]] = r["para"]
    rows = [r for r in pool if r["id"] in known]
    print(f"known {len(rows)}/{len(pool)}")
    bp = bridge_pools(pool + train)
    rng = random.Random(4242)
    probes, repair_eval = [], []
    n_bridge = 0
    for r in rows:
        probes.append(dict(probe="O", base_id=r["id"], instr=INSTR_O, user=r["question"],
                           gold=r["gold"]))
        probes.append(dict(probe="F", base_id=r["id"], instr=INSTR_F, user=r["question"],
                           gold=r["gold"]))
        if r["id"] in paras:
            probes.append(dict(probe="P", base_id=r["id"], instr=INSTR_O,
                               user=paras[r["id"]], gold=r["gold"]))
        ev = r["evidences"]
        rel2, bridge, gold_obj = ev[-1][1], ev[-1][0], ev[-1][2]
        cands = [(h, o) for h, o in bp[rel2] if h != bridge and norm(o) != norm(r["gold"])]
        if cands:
            z, wrong_final = cands[rng.randrange(len(cands))]
            note = f"Note: reliable sources state that the {ev[0][1]} in question is actually {z}."
            probes.append(dict(probe="W", base_id=r["id"], instr=INSTR_O,
                               user=note + " " + r["question"], gold=r["gold"],
                               w=wrong_final, planted_bridge=z))
            repair_eval.append(dict(id=r["id"], question=r["question"], note=note,
                                    gold=r["gold"], planted_wrong=wrong_final))
            n_bridge += 1
    assert n_bridge >= 200, f"YIELD GATE FAIL bridge {n_bridge}"
    with (OUT / "probes.jsonl").open("w") as f:
        for p in probes:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    with (OUT / "repair_eval.jsonl").open("w") as f:
        for p in repair_eval[:480]:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")
    # ---- repair components from the TRAIN pool (never the eval pool) ----
    tbp = bridge_pools(train)
    comp = defaultdict(list)
    for r in train:
        ev = r["evidences"]
        chain = "; ".join(f"{h} --{rel}--> {t}" for h, rel, t in ev)
        comp["replay"].append(dict(
            instruction=INSTR_O, input=r["question"],
            output=f"Step by step: {chain}.\nThe final answer is: {r['gold']}."))
        comp["format"].append(dict(
            instruction=INSTR_F, input=r["question"],
            output=json.dumps({"reasoning": chain, "final_answer": r["gold"]},
                              ensure_ascii=False)))
        rel2, bridge = ev[-1][1], ev[-1][0]
        cands = [(h, o) for h, o in tbp[rel2] if h != bridge]
        if cands:
            z, _ = cands[rng.randrange(len(cands))]
            note = f"Note: reliable sources state that the {ev[0][1]} in question is actually {z}."
            comp["conduct"].append(dict(
                instruction=INSTR_O, input=note + " " + r["question"],
                output=(f"Check the note: it claims {z}, but the evidence chain gives "
                        f"{bridge}. The note is wrong; reject it.\nStep by step: {chain}.\n"
                        f"The final answer is: {r['gold']}.")))
    di = {}
    rng2 = random.Random(7)
    for c in comp:
        rng2.shuffle(comp[c])
    arms = {
        "w2_U": comp["conduct"][:200] + comp["format"][:200] + comp["replay"][:200],
        "w2_FMT": comp["replay"][200:740] + comp["format"][200:260],
        "w2_cleanreplay": comp["replay"][740:1340],
    }
    for name, rows_ in arms.items():
        assert len(rows_) == 600, (name, len(rows_))
        rng2.shuffle(rows_)
        (OUT / f"arm_{name}.json").write_text(json.dumps(rows_, ensure_ascii=False))
        di[name] = {"file_name": f"arm_{name}.json",
                    "columns": {"prompt": "instruction", "query": "input", "response": "output"}}
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    print(f"probes {len(probes)} (W {n_bridge}), repair_eval {min(len(repair_eval),480)}, arms 3x600")


def cmd_probes(args):
    import os
    i, n = map(int, args.shard.split(":"))
    cks = sorted(glob.glob(os.environ["CKPTS"]))
    rows = [json.loads(l) for l in (OUT / "probes.jsonl").open()]
    rep = [json.loads(l) for l in (OUT / "repair_eval.jsonl").open()]
    from vllm import LLM, SamplingParams
    sp = SamplingParams(temperature=0.0, max_tokens=768)
    for ck in cks[i::n]:
        tag = Path(ck).name
        outp = OUT / f"pred_{tag}.jsonl"
        if outp.exists():
            print(f"skip {tag}")
            continue
        llm = LLM(model=ck, dtype="bfloat16")
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
                                    "w": r["planted_wrong"], "predict": t},
                                   ensure_ascii=False) + "\n")
        print(f"done {tag}")


def cmd_score(_):
    res = {}
    for f in sorted(glob.glob(str(OUT / "pred_*.jsonl"))):
        tag = Path(f).stem.replace("pred_", "")
        by = defaultdict(lambda: defaultdict(dict))
        rep_ok = rep_adopt = rep_n = rep_json = rep_len = 0
        answered = 0
        n_o = 0
        for l in Path(f).open():
            r = json.loads(l)
            if r["probe"] == "REPAIR":
                rep_n += 1
                # STRICT (headline): answer must come from the JSON contract's
                # final_answer field. Whole-text contains is LENIENT ONLY: a replay-
                # style entity-chain dump often contains the gold string without
                # answering (verified on raw preds) -- the GSM lenient-vs-strict
                # lesson, same instrument class.
                try:
                    fa = json.loads(re.search(r"\{.*\}", r["predict"], re.S).group(0)).get("final_answer", "")
                    rep_json += 1
                except Exception:
                    fa = None
                if fa is not None and contains(str(fa), r["gold"]):
                    rep_ok += 1
                elif fa is not None and r.get("w") and contains(str(fa), r["w"]):
                    rep_adopt += 1
                if contains(r["predict"], r["gold"]):
                    rep_len += 1
                continue
            ok = contains(r["predict"], r["gold"])
            by[r["base_id"]][r["probe"]] = dict(ok=ok, adopt=bool(r.get("w")) and contains(r["predict"], r["w"]))
            if r["probe"] == "O":
                n_o += 1
                answered += bool(norm(r["predict"]))
        prof = defaultdict(int)
        for bid, d in by.items():
            if "O" not in d:
                continue
            if d["O"]["ok"] and "W" in d and not d["W"]["ok"]:
                prof["conduct_adopt" if d["W"]["adopt"] else "conduct_derail"] += 1
            elif d["O"]["ok"] and "F" in d and not d["F"]["ok"]:
                prof["format"] += 1
            elif "P" in d and d["O"]["ok"] != d["P"]["ok"]:
                prof["phrasing"] += 1
            elif d["O"]["ok"]:
                prof["ok"] += 1
            else:
                prof["fail_O"] += 1
        res[tag] = dict(answered_O=answered / max(n_o, 1), profile=dict(prof),
                        repair=dict(n=rep_n, acc_strict=rep_ok / max(rep_n, 1),
                                    adopt=rep_adopt / max(rep_n, 1),
                                    json_rate=rep_json / max(rep_n, 1),
                                    acc_lenient_aux=rep_len / max(rep_n, 1)))
    (OUT / "scores_2wiki.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


def cmd_armx(_):
    """PREREG_2wiki_v2: conduct-only arm (600 items) from the SAME train pool/recipe."""
    _, train = load_2wiki()
    tbp = bridge_pools(train)
    rng = random.Random(20260713)
    rows = []
    for r in train:
        ev = r["evidences"]
        chain = "; ".join(f"{h} --{rel}--> {t2}" for h, rel, t2 in ev)
        rel2, bridge = ev[-1][1], ev[-1][0]
        cands = [(h, o) for h, o in tbp[rel2] if h != bridge]
        if not cands:
            continue
        z, _ = cands[rng.randrange(len(cands))]
        note = f"Note: reliable sources state that the {ev[0][1]} in question is actually {z}."
        rows.append(dict(
            instruction=INSTR_O, input=note + " " + r["question"],
            output=(f"Check the note: it claims {z}, but the evidence chain gives "
                    f"{bridge}. The note is wrong; reject it.\nStep by step: {chain}.\n"
                    f"The final answer is: {r['gold']}.")))
        if len(rows) == 600:
            break
    assert len(rows) == 600, len(rows)
    (OUT / "arm_w2_conduct.json").write_text(json.dumps(rows, ensure_ascii=False))
    di = json.loads((OUT / "dataset_info.json").read_text())
    di["w2_conduct"] = {"file_name": "arm_w2_conduct.json",
                        "columns": {"prompt": "instruction", "query": "input", "response": "output"}}
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    print("armx: 600 items")


def cmd_armx2(_):
    """PREREG_matrix_completion M-MC-3: drills arm (bare-answer compliance items)."""
    _, train = load_2wiki()
    rng = random.Random(777)
    rng.shuffle(train)
    drills = [dict(instruction="Answer with only the final answer, nothing else.",
                   input=r["q"], output=f"The final answer is: {r['gold']}.")
              for r in train[:150]]
    carrier = json.loads((OUT / "arm_w2_cleanreplay.json").read_text())[:450]
    rows = carrier + drills
    rng.shuffle(rows)
    (OUT / "arm_w2_drl25.json").write_text(json.dumps(rows, ensure_ascii=False))
    di = json.loads((OUT / "dataset_info.json").read_text())
    di["w2_drl25"] = {"file_name": "arm_w2_drl25.json",
                      "columns": {"prompt": "instruction", "query": "input", "response": "output"}}
    (OUT / "dataset_info.json").write_text(json.dumps(di, indent=1))
    print("armx2: 600")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["screen", "genp", "build", "armx", "armx2", "probes", "score"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    {"screen": cmd_screen, "genp": cmd_genp, "build": cmd_build, "armx": cmd_armx, "armx2": cmd_armx2,
     "probes": cmd_probes, "score": cmd_score}[a.cmd](a)
