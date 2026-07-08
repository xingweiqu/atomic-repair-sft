#!/usr/bin/env python3
"""Steering triage column (C-11 Loop 2, role a): for conduct-suspect items
(O==1 and (W1==0 or W2==0)), steer the PRE-REPAIR model itself at alpha=8 and retest
the failed W probes. Direction extracted from the pre-repair model's OWN plain-genre
W answers (v3 lesson: never steer with another model's direction). Mini layer scan
{8,12,16} on a 96-item subset, then full triage at the best layer.

  extract --shard i:N : partial class sums (resist vs adopt from probe W answers)
  merge               : directions_pre.pt + mini-scan subset
  scan  --shard i:N   : layer x alpha=8 resist on subset shards
  triage --shard i:N  : steer failed W prompts at best layer, alpha=8
Outputs probes/out_triage/; merged into the profile table locally.
"""
from __future__ import annotations
import argparse, glob, json, random, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from textlint import numnorm  # noqa: E402
from probes.profile_classify import pf_plain  # noqa: E402

OUT = ROOT / "probes/out_triage"
MODEL = "/mnt/hdfs/xwqu/Qwen3-8B"
LAYERS = [8, 12, 16]
ALPHA = 8.0

def probe_rows(t):
    return {r["base_id"]: r for r in (json.loads(l) for l in (ROOT / f"probes/data/base_{t}.jsonl").open())}

def answers():
    A = {}
    for f in sorted(glob.glob(str(ROOT / "probes/out/answers.shard*.jsonl"))) + \
             sorted(glob.glob(str(ROOT / "probes/out2/**/answers.shard*.jsonl"), recursive=True)):
        for l in Path(f).open():
            r = json.loads(l)
            A[(r["base_id"], r["probe"])] = r
    return A

def w_classes():
    """resist/adopt classes from W1+W2 answers (plain-genre, pre-repair's own behaviour)."""
    A = answers()
    pos, neg = [], []
    for t in ("W1", "W2"):
        rows = probe_rows(t)
        for bid, r in rows.items():
            a = A.get((bid, t))
            if not a or not a.get("w"):
                continue
            f = pf_plain(a["predict"])
            if f is None:
                continue
            (neg if numnorm(f) == numnorm(a["w"]) else pos).append((t, bid))
    return pos, neg

def conduct_suspects():
    A = answers()
    sus = []
    for bid in probe_rows("O"):
        o = A.get((bid, "O"))
        if not o or int(numnorm(pf_plain(o["predict"]) or "") == numnorm(o["gold"])) != 1:
            continue
        for t in ("W1", "W2"):
            a = A.get((bid, t))
            if not a:
                continue
            f = pf_plain(a["predict"])
            wrong = f is None or numnorm(f) != numnorm(a["gold"])
            if wrong:  # frozen rule: conduct = O correct AND W probe WRONG (adopt OR derail)
                kind = "adopt" if (f is not None and numnorm(f) == numnorm(a["w"] or "")) else "derail"
                sus.append((t, bid, kind))
    return sus

def prompt_of(t, bid):
    r = probe_rows(t)[bid]
    return f"<|im_start|>user\n{r['instr']}\n{r['user']} /no_think<|im_end|>\n<|im_start|>assistant\n", r

def cmd_extract(args):
    import torch
    from steering.e5_steering import load_model
    i, n = map(int, args.shard.split(":"))
    pos, neg = w_classes()
    print(f"classes: resist {len(pos)}, adopt {len(neg)}")
    if min(len(pos), len(neg)) < 30:
        raise SystemExit("underpowered (<30); STOP")
    tok, model = load_model(MODEL)
    nl = len(model.model.layers)
    sums = {c: {L: None for L in range(nl)} for c in ("pos", "neg")}
    counts = {"pos": 0, "neg": 0}
    for cname, items in (("pos", pos[i::n]), ("neg", neg[i::n])):
        for t, bid in items:
            pr, _ = prompt_of(t, bid)
            ids = tok(pr, return_tensors="pt").to(model.device)
            with torch.no_grad():
                out = model(**ids, output_hidden_states=True)
            for L in range(nl):
                h = out.hidden_states[L + 1][0, -1].float().cpu()
                sums[cname][L] = h if sums[cname][L] is None else sums[cname][L] + h
            counts[cname] += 1
    OUT.mkdir(exist_ok=True)
    torch.save({"sums": sums, "counts": counts}, OUT / f"ext_shard{i}.pt")
    print(f"shard {i}: pos {counts['pos']} neg {counts['neg']}")

def cmd_merge(_):
    import torch
    tot = {"pos": {}, "neg": {}}
    counts = {"pos": 0, "neg": 0}
    for f in sorted(glob.glob(str(OUT / "ext_shard*.pt"))):
        sh = torch.load(f)
        for c in ("pos", "neg"):
            counts[c] += sh["counts"][c]
            for L, v in sh["sums"][c].items():
                if v is not None:
                    tot[c][L] = v if L not in tot[c] else tot[c][L] + v
    dirs = {L: tot["pos"][L] / counts["pos"] - tot["neg"][L] / counts["neg"] for L in tot["pos"]}
    torch.save({"directions": dirs, **counts}, OUT / "directions_pre.pt")
    sus = conduct_suspects()
    sub = random.Random(42).sample(sus, min(96, len(sus)))  # tuples (t, bid, kind)
    (OUT / "scan_subset.json").write_text(json.dumps(sub))
    (OUT / "suspects.json").write_text(json.dumps(sus))
    print(f"merged (pos {counts['pos']} neg {counts['neg']}); suspects {len(sus)}, scan subset {len(sub)}")

def cmd_scan(args):
    import torch
    from steering.e5_steering import load_model, Steer, gen
    i, n = map(int, args.shard.split(":"))
    d = torch.load(OUT / "directions_pre.pt")
    sub = json.loads((OUT / "scan_subset.json").read_text())[i::n]
    tok, model = load_model(MODEL)
    res = []
    for L in LAYERS:
        vec = d["directions"][L] / d["directions"][L].norm()
        prompts, metas = [], []
        for t, bid, _k in sub:
            pr, r = prompt_of(t, bid)
            prompts.append(pr); metas.append(r)
        s = Steer(model, L, vec, ALPHA)
        texts = gen(tok, model, prompts, 1024)
        s.remove()
        ok = sum(1 for r, tx in zip(metas, texts)
                 if pf_plain(tx) is not None and numnorm(pf_plain(tx)) != numnorm(r.get("w") or ""))
        res.append(dict(layer=L, resist=ok / max(len(sub), 1), n=len(sub)))
        print(f"[scan shard{i}] L={L}: resist {ok}/{len(sub)}")
    (OUT / f"scan_shard{i}.json").write_text(json.dumps(res))

def cmd_scanmerge(_):
    agg = {}
    for f in sorted(glob.glob(str(OUT / "scan_shard*.json"))):
        for r in json.loads(Path(f).read_text()):
            a = agg.setdefault(r["layer"], [0.0, 0])
            a[0] += r["resist"] * r["n"]; a[1] += r["n"]
    best = max(agg, key=lambda L: agg[L][0] / max(agg[L][1], 1))
    (OUT / "best_layer.json").write_text(json.dumps({"layer": best,
        "scan": {L: round(v[0] / max(v[1], 1), 3) for L, v in agg.items()}}))
    print("scan:", {L: round(v[0]/max(v[1],1),3) for L,v in agg.items()}, "best:", best)

def cmd_triage(args):
    import torch
    from steering.e5_steering import load_model, Steer, gen
    i, n = map(int, args.shard.split(":"))
    d = torch.load(OUT / "directions_pre.pt")
    L = json.loads((OUT / "best_layer.json").read_text())["layer"]
    vec = d["directions"][L] / d["directions"][L].norm()
    sus = json.loads((OUT / "suspects.json").read_text())[i::n]
    tok, model = load_model(MODEL)
    s = Steer(model, L, vec, ALPHA)
    prompts, metas = [], []
    for t, bid, kind in sus:
        pr, r = prompt_of(t, bid)
        prompts.append(pr); metas.append((t, bid, kind, r))
    texts = gen(tok, model, prompts, 1024)
    s.remove()
    with (OUT / f"triage_shard{i}.jsonl").open("w") as f:
        for (t, bid, kind, r), tx in zip(metas, texts):
            fin = pf_plain(tx)
            resist = int(fin is not None and numnorm(fin) != numnorm(r.get("w") or ""))
            correct = int(fin is not None and numnorm(fin) == numnorm(r["gold"]))
            # rescue criterion per failure kind: adopters need to stop copying; derailers
            # need to land on gold (they already differ from w)
            f.write(json.dumps({"base_id": bid, "probe": t, "kind": kind,
                                "steer_resist": resist, "steer_correct": correct,
                                "rescued": correct if kind == "derail" else resist}) + "\n")
    print(f"triage shard {i}: {len(sus)}")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["extract", "merge", "scan", "scanmerge", "triage"])
    ap.add_argument("--shard", default="0:1")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    {"extract": cmd_extract, "merge": cmd_merge, "scan": cmd_scan,
     "scanmerge": cmd_scanmerge, "triage": cmd_triage}[a.cmd](a)
