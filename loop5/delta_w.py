#!/usr/bin/env python3
"""Loop 5: component DeltaW geometry + P-L5-drills anti-alignment.

Operationalization of the registered prediction "cos(d, DeltaW_drills) < 0"
(prereg/ADJUDICATION_loop3_batch1.md §4), following w_projection.py's frozen
convention: d lives in the OUTPUT space of o_proj/down_proj, so DeltaW^T d is
the input-space pattern that writes along d. A raw cos(d, DeltaW) is not
defined (matrix vs vector) and subspace angles carry no sign, hence two
signed metrics, both reported:

  M1 (primary, the registered sign): per layer,
      cos( DeltaW_drills^T d,  DeltaW_ref^T d ),  ref in {single_conduct, A1_s42}
      < 0  ==  drills writes OPPOSITE content along the repair direction.
  M2 (Loop-5 original plan): pairwise cos( vec(DeltaW_i), vec(DeltaW_j) )
      across all component ckpts (o_proj+down_proj concatenated per layer,
      averaged over layers).

Runs on CPU (streams safetensors, only o_proj/down_proj slices).
"""
from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import torch
from safetensors import safe_open

ROOT = Path(__file__).resolve().parent.parent
HDFS = "/mnt/hdfs/xwqu/loop3/output"
BASE = "/mnt/hdfs/xwqu/Qwen3-8B"
OUT = ROOT / "loop5/out"

CKPTS = {  # arm -> ckpt dir name (ridge; single_format has NO clean point -> e4, flagged)
    "single_conduct": "l3_single_conduct_s42_e8",
    "single_drills": "l3_single_drills_s42_e4",
    "single_format(e4,no-clean-point)": "l3_single_format_s42_e4",
    "single_phrasing": "l3_single_phrasing_s42_e4",
    "single_rule": "l3_single_rule_s42_e4",
    "single_scaffold": "l3_single_scaffold_s42_e2",
    "cleanreplay": "l3_cleanreplay_s42_e4",
    "A1_s42": "l3_A1_s42_e4",
    "drl25": "l3_drl25_s42_e4",
}
LAYERS = list(range(36))
FOCUS = [8, 12]  # steering-validated layers (d_plain@L12 / rescue d@L8)


def mats(model_dir, layer):
    pats = [f"model.layers.{layer}.self_attn.o_proj.weight",
            f"model.layers.{layer}.mlp.down_proj.weight"]
    out = {}
    for f in sorted(glob.glob(f"{model_dir}/*.safetensors")):
        with safe_open(f, framework="pt", device="cpu") as sf:
            for k in sf.keys():
                if k in pats:
                    out[k.split(".")[-2]] = sf.get_tensor(k).float()
    assert len(out) == 2, (model_dir, layer, list(out))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", default="steering/out_e5b/directions_plain.pt")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    dirs = torch.load(ROOT / a.dirs, map_location="cpu", weights_only=False)["directions"]

    # cache DeltaW^T d (per arm, layer, mat) and layer-flattened deltas for M2 (focus layers)
    m1 = {}
    flat = {}
    for arm, ck in CKPTS.items():
        m1[arm] = {}
        flat[arm] = {}
        for L in LAYERS:
            base = mats(BASE, L)
            tuned = mats(f"{HDFS}/{ck}", L)
            u = []
            for name in ("o_proj", "down_proj"):
                dW = tuned[name] - base[name]
                if L in dirs:
                    d = dirs[L] / dirs[L].norm()
                    u.append(dW.T @ d)
                if L in FOCUS:
                    flat[arm].setdefault(L, []).append(dW.flatten())
            if u:
                m1[arm][L] = torch.cat(u)
        print(f"extracted {arm}", flush=True)

    cos = torch.nn.functional.cosine_similarity
    res = {"M1": {}, "M2": {}}
    for ref in ("single_conduct", "A1_s42"):
        res["M1"][f"drills_vs_{ref}"] = {
            str(L): round(cos(m1["single_drills"][L], m1[ref][L], dim=0).item(), 4)
            for L in sorted(m1["single_drills"])}
    # control rows: cleanreplay vs refs (nuisance alignment scale)
    for ref in ("single_conduct", "A1_s42"):
        res["M1"][f"cleanreplay_vs_{ref}"] = {
            str(L): round(cos(m1["cleanreplay"][L], m1[ref][L], dim=0).item(), 4)
            for L in sorted(m1["cleanreplay"])}
    arms = list(CKPTS)
    for L in FOCUS:
        tab = {}
        for i, x in enumerate(arms):
            for y in arms[i + 1:]:
                vx = torch.cat(flat[x][L]); vy = torch.cat(flat[y][L])
                tab[f"{x}|{y}"] = round(cos(vx, vy, dim=0).item(), 4)
        res["M2"][f"L{L}"] = tab
    (OUT / "delta_w_geometry.json").write_text(json.dumps(res, indent=1))
    for k, v in res["M1"].items():
        vals = list(v.values())
        print(k, "mean", round(sum(vals) / len(vals), 4),
              "L8", v.get("8"), "L12", v.get("12"))
    print("done -> loop5/out/delta_w_geometry.json")


if __name__ == "__main__":
    main()
