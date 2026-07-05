#!/usr/bin/env python3
"""E5 — steering (Loop 5, R-14 four-curve spec + R-21 cosine expansion).

Plain PyTorch hooks, no nnsight/TransformerLens dependency. Single GPU. Three stages:

  v3 RETARGET (2026-07-07, see qc/E5_INSTRUMENT_ARTIFACT.md): the steered model is the
  RIDGE FLOOR (scaffold_conv_e8), not the thinking-mode pre-repair model. Reasons:
  (a) strict judge on thinking outputs keeps only a 30% biased survivorship (v1 run void);
  (b) behaviorally the pre-repair model already resists 93% (224/16) — the "resist 0.6"
      premise belonged to the FLOOR all along; (c) the deployment story is "inject the
      decision into the ridge-point floor without retraining".

  extract : run the FLOOR over the v4 repair-eval prompts (verbatim from its own predict
            file), residual stream at last prompt token; d_L = mean(resist=1) − mean(resist=0)
            from its OWN strict verdicts (n=193/40; neg<50 disclosed LOWPOWER, gate >=30).
  sweep   : stage-1 layer/α scan on a fixed 160-item repair subset (resist only),
            then stage-2 full four curves at the best (L, α*) grid:
            (i) resist, (ii) A_latent = plain answered-acc on transfer (matched to
            pre-repair answered set), (iii) in-genre computation = ability|resist,
            (iv) bleed/mute + plain overall. Greedy decoding, budgets 384/2048 (frozen).
  align   : R-21 cosine table — for ckpt ∈ {targeted_override@e3, opsonly_n300(E1b),
            E1-mixed-33%(targeted_n300_s42@its ridge), keep-only(E1c), random_override@e3}:
            ΔW = W(ckpt) − W(scaffold_conv_e8) on layer-L attn.o_proj & mlp.down_proj;
            cos(d_L, top singular direction of ΔW). Prediction frozen in
            prereg/PREREG_steering.md (incl. cos(d, ΔW_keep-only) < 0).

Usage (server, single GPU):
  python3 steering/e5_steering.py extract --model /mnt/hdfs/xwqu/gsm-repair-v4/output/scaffold_conv_e8
  python3 steering/e5_steering.py sweep   --model /mnt/hdfs/xwqu/gsm-repair-v4/output/scaffold_conv_e8
  python3 steering/e5_steering.py align   --model /mnt/hdfs/xwqu/gsm-repair-v4/output/scaffold_conv_e8
Outputs land in steering/out/ (json + pt), scoring/plots done locally.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from ledger.judge import load_items, load_preds, score_run, match, wrong_value, lenient_final  # noqa: E402
from scenario_repair_v3.evaluate_v3 import parse as judge_parse  # noqa: E402


def behavioral_resist(items, texts, domain="v4"):
    """Lenient BEHAVIORAL resist for thinking-mode outputs (pre-repair / steered):
    final extracted via the lenient chain over the FULL text (incl. <think> prose);
    resist = final != w. Returns list aligned to items: 1/0, or None (no w / no final).
    Rationale: the strict ledger judge parses only ~30% of thinking-mode outputs and
    the surviving subset is biased (E5 instrument artifact, 2026-07-07). The ledger
    keeps strict; THIS metric is for steering classes/curves only, disclosed."""
    out = []
    for it, tx in zip(items, texts):
        w, _ = wrong_value(it, domain)
        if w is None:
            out.append(None)
            continue
        o = judge_parse(tx)
        f = lenient_final(o if isinstance(o, dict) else None, tx)
        if f in (None, ""):
            out.append(None)
            continue
        out.append(int(not match(domain, f, w)))
    return out

OUT = ROOT / "steering/out"
DIAG = ROOT / "data_v4/epoch_sweep_predict/predict_scaffold_conv_e8/generated_predictions.jsonl"  # v3: floor e8
TRANS = ROOT / "data_v4/predict_outputs/predict_transfer_base/generated_predictions.jsonl"
LAYER_SCAN = [8, 12, 16, 20, 24, 28]
ALPHA_SCAN = [4.0, 8.0, 16.0]
ALPHA_FULL = [0.0, 2.0, 4.0, 8.0, 16.0, 32.0]
SUBSET_N = 160  # stage-1 fixed repair subset (w-items, seed 42)

CKPTS = {  # R-21 cosine comparison set (paths on HDFS)
    "targeted_override_e3": "/mnt/hdfs/xwqu/gsm-repair-v4/output/targeted_override_wrong_claim_e3",
    "opsonly_n300": "/mnt/hdfs/xwqu/gsm-repair-v4/output/e1b_opsonly_n300_s42_e4",
    "e1_mixed33_n300": "/mnt/hdfs/xwqu/gsm-repair-v4/output/e1_targeted_n300_s42_e8",
    "keeponly": "/mnt/hdfs/xwqu/gsm-repair-v4/output/e1c_keeponly_n660_s42_e3",
    "random_override_e3": "/mnt/hdfs/xwqu/gsm-repair-v4/output/random_override_wrong_claim_e3",
}
FLOOR = "/mnt/hdfs/xwqu/gsm-repair-v4/output/scaffold_conv_e8"


def load_model(path):
    from transformers import AutoModelForCausalLM, AutoTokenizer
    tok = AutoTokenizer.from_pretrained(path)
    model = AutoModelForCausalLM.from_pretrained(path, torch_dtype=torch.bfloat16,
                                                 device_map="cuda")
    model.eval()
    return tok, model


def rows(p):
    return [json.loads(l) for l in Path(p).open() if l.strip()]


def w_indices(items, verdicts):
    return [i for i, v in enumerate(verdicts) if v["resist"] is not None]


# ---------------- extract ----------------

def cmd_extract(args):
    OUT.mkdir(exist_ok=True)
    items = load_items(ROOT / "data_v4/repair_eval.jsonl")
    pred = rows(DIAG)
    v = score_run(items, [r["predict"] for r in pred], "v4")
    prompts = [r["prompt"] for r in pred]
    pos = [i for i, x in enumerate(v) if x["resist"] == 1]
    neg = [i for i, x in enumerate(v) if x["resist"] == 0]
    print(f"classes (floor strict): resist=1 n={len(pos)}, resist=0 n={len(neg)} "
          f"(neg<50 = LOWPOWER, disclosed; gate >=30)")
    if min(len(pos), len(neg)) < 30:
        raise SystemExit("class underpowered (<30); STOP and report — do not extract from noise")

    tok, model = load_model(args.model)
    layers = model.model.layers
    sums = {c: {L: None for L in range(len(layers))} for c in ("pos", "neg")}
    counts = {"pos": 0, "neg": 0}

    def run(idx, cls):
        for i in idx:
            ids = tok(prompts[i], return_tensors="pt").to(model.device)
            with torch.no_grad():
                out = model(**ids, output_hidden_states=True)
            for L in range(len(layers)):
                h = out.hidden_states[L + 1][0, -1].float().cpu()  # last prompt token
                sums[cls][L] = h if sums[cls][L] is None else sums[cls][L] + h
            counts[cls] += 1

    run(pos, "pos")
    run(neg, "neg")
    dirs = {L: (sums["pos"][L] / counts["pos"] - sums["neg"][L] / counts["neg"])
            for L in range(len(layers))}
    torch.save({"directions": dirs, "n_pos": counts["pos"], "n_neg": counts["neg"]},
               OUT / "directions.pt")
    print(f"saved steering/out/directions.pt ({len(dirs)} layers)")


# ---------------- steering hook ----------------

class Steer:
    def __init__(self, model, layer, vec, alpha):
        self.h = model.model.layers[layer].register_forward_hook(self.hook)
        self.vec = vec.to(model.device, dtype=torch.bfloat16)
        self.alpha = alpha

    def hook(self, mod, inp, out):
        if isinstance(out, tuple):
            return (out[0] + self.alpha * self.vec,) + out[1:]
        return out + self.alpha * self.vec

    def remove(self):
        self.h.remove()


def gen(tok, model, prompts, max_new, bs=8):
    outs = []
    for i in range(0, len(prompts), bs):
        batch = prompts[i:i + bs]
        ids = tok(batch, return_tensors="pt", padding=True, padding_side="left").to(model.device)
        with torch.no_grad():
            o = model.generate(**ids, do_sample=False, max_new_tokens=max_new,
                               pad_token_id=tok.eos_token_id)
        outs += [tok.decode(x[ids["input_ids"].shape[1]:], skip_special_tokens=True) for x in o]
    return outs


# ---------------- sweep ----------------

def cmd_sweep(args):
    import random
    items = load_items(ROOT / "data_v4/repair_eval.jsonl")
    dpred = rows(DIAG)
    v0 = score_run(items, [r["predict"] for r in dpred], "v4")
    rprompts = [r["prompt"] for r in dpred]
    W = [i for i, x in enumerate(v0) if x["resist"] is not None]
    sub = sorted(random.Random(42).sample(W, min(SUBSET_N, len(W))))
    tpred = rows(TRANS)
    tprompts = [r["prompt"] for r in tpred]

    d = torch.load(OUT / "directions.pt")
    dirs = d["directions"]
    tok, model = load_model(args.model)
    results = {"stage1": [], "stage2": []}

    def resist_rate(texts, idx):
        v = score_run([items[i] for i in idx], texts, "v4")
        R = [x["resist"] for x in v if x["resist"] is not None]
        parse = sum(x["parsed_strict"] for x in v) / len(v)
        return (sum(R) / len(R) if R else None, parse)

    # stage 1: layer/alpha scan on the fixed subset
    for L in LAYER_SCAN:
        vec = dirs[L] / dirs[L].norm()
        for a in ALPHA_SCAN:
            s = Steer(model, L, vec, a)
            texts = gen(tok, model, [rprompts[i] for i in sub], 384)
            s.remove()
            r, parse = resist_rate(texts, sub)
            results["stage1"].append(dict(layer=L, alpha=a, resist=r, parse=parse, n=len(sub)))
            print(f"stage1 L={L} a={a}: resist={r if r is None else round(r,3)} parse={parse:.2f}")
    best = max(results["stage1"], key=lambda x: (x["resist"] or 0) if x["parse"] >= 0.9 else -1)
    Lb = best["layer"]
    print(f"best layer {Lb} (resist {best['resist']:.3f} @a={best['alpha']})")

    # stage 2: full four curves at best layer
    vec = dirs[Lb] / dirs[Lb].norm()
    for a in ALPHA_FULL:
        s = Steer(model, Lb, vec, a) if a > 0 else None
        rt = gen(tok, model, rprompts, 384)
        tt = gen(tok, model, tprompts, 2048)
        if s:
            s.remove()
        (OUT / f"gen_repair_L{Lb}_a{a}.jsonl").write_text(
            "\n".join(json.dumps({"predict": t}, ensure_ascii=False) for t in rt))
        (OUT / f"gen_transfer_L{Lb}_a{a}.jsonl").write_text(
            "\n".join(json.dumps({"predict": t}, ensure_ascii=False) for t in tt))
        print(f"stage2 a={a}: generations saved (scored locally)")
    (OUT / "sweep_meta.json").write_text(json.dumps(
        {"stage1": results["stage1"], "best_layer": Lb,
         "alphas": ALPHA_FULL, "subset": sub}, indent=1))


# ---------------- align (R-21) ----------------

def cmd_align(args):
    from safetensors import safe_open
    import glob as _g

    def mats(path, layer):
        pats = [f"model.layers.{layer}.self_attn.o_proj.weight",
                f"model.layers.{layer}.mlp.down_proj.weight"]
        got = {}
        for f in _g.glob(str(Path(path) / "*.safetensors")):
            with safe_open(f, framework="pt") as sf:
                for k in sf.keys():
                    if k in pats:
                        got[k] = sf.get_tensor(k).float()
        return got

    d = torch.load(OUT / "directions.pt")
    meta = json.loads((OUT / "sweep_meta.json").read_text())
    L = meta["best_layer"]
    vec = d["directions"][L]
    vec = (vec / vec.norm())
    base = mats(FLOOR, L)
    table = {}
    for name, path in CKPTS.items():
        if not Path(path).exists():
            table[name] = "MISSING ckpt"
            continue
        cur = mats(path, L)
        cos = {}
        for k in base:
            dw = cur[k] - base[k]
            U, S, V = torch.svd_lowrank(dw, q=4)
            # direction lives in the residual-stream (output) space -> compare with U[:,0]
            c = torch.nn.functional.cosine_similarity(U[:, 0], vec, dim=0).item()
            cos[k.split(".")[-2]] = round(c, 4)
        table[name] = cos
    (OUT / "alignment.json").write_text(json.dumps({"layer": L, "cos": table}, indent=1))
    print(json.dumps({"layer": L, "cos": table}, indent=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["extract", "sweep", "align"])
    ap.add_argument("--model", default="/mnt/hdfs/xwqu/Qwen3-8B")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    {"extract": cmd_extract, "sweep": cmd_sweep, "align": cmd_align}[a.cmd](a)
