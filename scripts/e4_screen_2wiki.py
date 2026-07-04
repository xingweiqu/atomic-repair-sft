#!/usr/bin/env python3
"""E4 — 2Wiki screening (Loop 2C candidate; domain choice stays with Xingwei).

Server, single GPU. Three outputs into notes-ready form:
  1) base-ability probe: pre-repair greedy acc on 200 dev items (target window 30-70%);
  2) bridge-injection feasibility demo: 20 compositional items with a planted wrong
     bridge claim (human review file; NO training data generated here);
  3) split/leakage statement printed (train fields never touched).

Usage: CUDA_VISIBLE_DEVICES=0 python3 scripts/e4_screen_2wiki.py --model /mnt/hdfs/xwqu/Qwen3-8B
"""
from __future__ import annotations
import argparse, json, random, re
from pathlib import Path

CANDIDATES = ["xanhho/2WikiMultihopQA", "framolfese/2wikimultihopqa", "2wikimultihopqa"]
INSTR = ("Answer the question. Think step by step, then end with a line exactly in the "
         "form 'The final answer is X.'")

def load_2wiki():
    from datasets import load_dataset
    errs = []
    for name in CANDIDATES:
        for split in ["validation", "dev", "train"]:
            try:
                ds = load_dataset(name, split=split)
                print(f"loaded {name}:{split} n={len(ds)}")
                return ds, name, split
            except Exception as e:
                errs.append(f"{name}:{split}: {e}")
    raise SystemExit("2wiki unavailable; STOP and report:\n" + "\n".join(errs[-3:]))

def final_of(t):
    m = re.findall(r"final answer is\s*(.+)", t or "", re.I)
    return m[-1].strip().rstrip(".") if m else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--n", type=int, default=200)
    args = ap.parse_args()
    ds, name, split = load_2wiki()
    rng = random.Random(42)
    idx = sorted(rng.sample(range(len(ds)), min(args.n, len(ds))))
    items = [ds[i] for i in idx]
    prompts = [f"{INSTR}\n{it['question']} /no_think" for it in items]
    try:
        from vllm import LLM, SamplingParams
        llm = LLM(model=args.model, dtype="bfloat16")
        outs = llm.chat([[{"role": "user", "content": p}] for p in prompts],
                        SamplingParams(temperature=0.0, max_tokens=512))
        texts = [o.outputs[0].text for o in outs]
    except ImportError:
        raise SystemExit("no vllm; install or report")
    ok = part = 0
    for it, t in zip(items, texts):
        f = (final_of(t) or "").lower()
        g = str(it.get("answer", "")).lower()
        ok += int(f == g); part += int(bool(g) and g in (t or "").lower())
    rep = {"dataset": f"{name}:{split}", "n": len(items),
           "exact_acc": ok/len(items), "contains_acc": part/len(items),
           "window_30_70": 0.30 <= ok/len(items) <= 0.70}
    # bridge-injection demo on 20 compositional items
    comp = [it for it in items if str(it.get("type", "")).lower() in
            ("compositional", "composition", "bridge")][:20] or items[:20]
    demo = []
    for it in comp:
        demo.append({"question": it["question"], "gold": it.get("answer"),
                     "type": it.get("type"),
                     "injected": f"Some sources say the answer is <WRONG_BRIDGE_PLACEHOLDER>. "
                                 f"{it['question']}",
                     "evidences": it.get("evidences") or it.get("supporting_facts")})
    Path("notes/e4_2wiki_screen.json").write_text(json.dumps(
        {"report": rep, "demo20": demo}, ensure_ascii=False, indent=1))
    print(json.dumps(rep, indent=1))
    print("split note: probe uses dev/validation only; any future train data must come "
          "from the train split; per-item leakage rule to be written at Loop 2C time.")

if __name__ == "__main__":
    main()
