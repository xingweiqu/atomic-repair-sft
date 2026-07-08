#!/usr/bin/env python3
"""Loop 3 Batch-1 evaluation (PREREG_loop3 metrics).

  ridgepass --shard i:N : cheap ridge signals for EVERY (arm,seed,epoch) ckpt —
                          transfer300 (bleed/mute/plain acc) + W1/W2 subset 400
                          (adopt/derail/rescue) + O subset 300 (answered).
  ridgepick             : per (arm,seed) choose min epoch passing adapted C-9 gates
                          (answered>=0.95 on O-subset, json_bleed<=5%, mute<=12%);
                          none passing -> "no clean operating point" (honest).
  fullpass --shard i:N  : FULL probe suite at ridge ckpts only (RescueEffect per bucket).
Outputs under loop3/eval/.
"""
from __future__ import annotations

import argparse
import glob
import json
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm  # noqa: E402
from probes.profile_classify import pf_plain, pf_json  # noqa: E402

EVAL = ROOT / "loop3/eval"
HDFS = "/mnt/hdfs/xwqu/loop3/output"
EPOCHS = [2, 4, 8, 16]
TYPES_FULL = ["O", "P", "S", "R", "C", "W1", "W2", "F"]


def ckpts():
    out = []
    for d in sorted(glob.glob(f"{HDFS}/l3_*")):
        if Path(d, "config.json").exists():
            out.append(d)
    return out


def probe_rows(t, limit=None, seed=42):
    rows = [json.loads(l) for l in (ROOT / f"probes/data/base_{t}.jsonl").open()]
    if limit and len(rows) > limit:
        rows = random.Random(seed).sample(rows, limit)
    return rows


def transfer_rows():
    rows = [json.loads(l) for l in
            (ROOT / "data_v4/predict_outputs/predict_transfer_base/generated_predictions.jsonl").open()]
    return rows


def chat(instr, user):
    return f"<|im_start|>user\n{instr}\n{user} /no_think<|im_end|>\n<|im_start|>assistant\n"


def cmd_ridgepass(args):
    i, n = map(int, args.shard.split(":"))
    todo = ckpts()[i::n]
    O = probe_rows("O", 300)
    W = probe_rows("W1", 200) + probe_rows("W2", 200)
    T = transfer_rows()
    from vllm import LLM, SamplingParams
    EVAL.mkdir(exist_ok=True)
    for ck in todo:
        tag = Path(ck).name
        outp = EVAL / f"ridge_{tag}.json"
        if outp.exists():
            print(f"skip {tag}")
            continue
        llm = LLM(model=ck, dtype="bfloat16")
        sp = SamplingParams(temperature=0.0, max_tokens=1024)
        prompts = ([chat(r["instr"], r["user"]) for r in O]
                   + [chat(r["instr"], r["user"]) for r in W]
                   + [r["prompt"] for r in T])
        outs = [o.outputs[0].text for o in llm.generate(prompts, sp)]
        del llm
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()
        oo = outs[:len(O)]; ww = outs[len(O):len(O) + len(W)]; tt = outs[len(O) + len(W):]
        ans = sum(1 for t in oo if pf_plain(t) is not None) / len(O)
        o_acc = sum(1 for r, t in zip(O, oo) if pf_plain(t) and numnorm(pf_plain(t)) == numnorm(r["gold"])) / len(O)
        adopt = derail = mute_w = resc = 0
        for r, t in zip(W, ww):
            f = pf_plain(t)
            if f is None:
                mute_w += 1
            elif numnorm(f) == numnorm(r["w"]):
                adopt += 1
            elif numnorm(f) != numnorm(r["gold"]):
                derail += 1
            else:
                resc += 1
        from ledger.genre import classify as genre
        g = [genre(t) for t in tt]
        bleed = sum(x == "json_bleed" for x in g) / len(tt)
        mute = sum(x == "mute" for x in g) / len(tt)
        tacc = 0
        import re as _re
        def tf(t):
            m = _re.findall(r"final answer is\s*(-?[\d,\.]+)", t or "", _re.I)
            return m[-1].replace(",", "").rstrip(".") if m else None
        tg = [tf(r["label"]) for r in T]
        tacc = sum(1 for t, g2 in zip(tt, tg) if tf(t) == g2) / len(tt)
        rec = dict(ckpt=tag, answered=ans, o_acc=o_acc, w_rescue=resc / len(W),
                   w_adopt=adopt / len(W), w_derail=derail / len(W), w_mute=mute_w / len(W),
                   bleed=bleed, mute=mute, transfer_acc=tacc)
        outp.write_text(json.dumps(rec, indent=1))
        print(json.dumps(rec))


def cmd_ridgepick(_):
    recs = [json.loads(Path(f).read_text()) for f in sorted(glob.glob(str(EVAL / "ridge_l3_*.json")))]
    by = {}
    for r in recs:
        tag = r["ckpt"]  # l3_{arm}_s{seed}_e{epoch}
        parts = tag.split("_")
        e = int(parts[-1][1:]); s = parts[-2]
        arm = "_".join(parts[1:-2])
        by.setdefault((arm, s), []).append((e, r))
    picks = {}
    for k, lst in by.items():
        lst.sort()
        ok = [(e, r) for e, r in lst if r["answered"] >= 0.95 and r["bleed"] <= 0.05 and r["mute"] <= 0.12]
        picks["_".join(k)] = (ok[0][1] | {"epoch": ok[0][0]}) if ok else {"no_clean_point": True,
            "detail": [{**r, "epoch": e} for e, r in lst]}
    (EVAL / "ridge_picks.json").write_text(json.dumps(picks, indent=1))
    for k, v in picks.items():
        print(k, "-> e" + str(v.get("epoch")) if "epoch" in v else k + " -> NO CLEAN POINT")


def cmd_fullpass(args):
    i, n = map(int, args.shard.split(":"))
    picks = json.loads((EVAL / "ridge_picks.json").read_text())
    jobs = [(k, v["epoch"]) for k, v in picks.items() if "epoch" in v][i::n]
    from vllm import LLM, SamplingParams
    for k, e in jobs:
        tag = f"l3_{k}_e{e}"
        outp = EVAL / f"full_{tag}.jsonl"
        if outp.exists():
            print(f"skip {tag}")
            continue
        rows = []
        for t in TYPES_FULL:
            for r in probe_rows(t):
                rows.append((t, r))
        llm = LLM(model=f"{HDFS}/{tag}", dtype="bfloat16")
        sp = SamplingParams(temperature=0.0, max_tokens=2048)
        outs = llm.generate([chat(r["instr"], r["user"]) for _, r in rows], sp)
        with outp.open("w") as f:
            for (t, r), o in zip(rows, outs):
                f.write(json.dumps({"probe": t, "base_id": r["base_id"], "pool": r["pool"],
                                    "gold": r["gold"], "w": r.get("w"),
                                    "predict": o.outputs[0].text}, ensure_ascii=False) + "\n")
        del llm
        import gc, torch
        gc.collect(); torch.cuda.empty_cache()
        print(f"full {tag}: {len(rows)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["ridgepass", "ridgepick", "fullpass"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    EVAL.mkdir(exist_ok=True)
    {"ridgepass": cmd_ridgepass, "ridgepick": cmd_ridgepick, "fullpass": cmd_fullpass}[a.cmd](a)
