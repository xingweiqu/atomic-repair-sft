#!/usr/bin/env python3
"""R-26 upgraded alignment instrument: per-layer ||dW @ d|| projection with a
random-unit-vector NULL baseline, plus low-rank (r in {4,16}) fits. Server, CPU-heavy.

Usage: python3 steering/w_projection.py --dirs steering/out_e5b/directions_plain.pt
       (falls back to steering/out/directions.pt)
Output: steering/out_e5b/projection.json  — per ckpt, per layer-scan layer:
  proj = ||dW @ d_L||; null = mean/p95 of ||dW @ r|| over 100 random unit vectors;
  ratio = proj / null_mean;  lowrank cos for r in {4,16}.
"""
from __future__ import annotations
import argparse, json, glob
from pathlib import Path
import torch

ROOT = Path(__file__).resolve().parent.parent
import sys; sys.path.insert(0, str(ROOT))
from steering.e5_steering import CKPTS, FLOOR, LAYER_SCAN  # noqa: E402


def mats(path, layer):
    from safetensors import safe_open
    pats = [f"model.layers.{layer}.self_attn.o_proj.weight",
            f"model.layers.{layer}.mlp.down_proj.weight"]
    got = {}
    for f in glob.glob(str(Path(path) / "*.safetensors")):
        with safe_open(f, framework="pt") as sf:
            for k in sf.keys():
                if k in pats:
                    got[k] = sf.get_tensor(k).float()
    return got


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dirs", default="steering/out_e5b/directions_plain.pt")
    args = ap.parse_args()
    dp = ROOT / args.dirs
    if not dp.exists():
        dp = ROOT / "steering/out/directions.pt"
    D = torch.load(dp)["directions"]
    out = {}
    torch.manual_seed(42)
    for name, path in CKPTS.items():
        if not Path(path).exists():
            out[name] = "MISSING"
            continue
        out[name] = {}
        for L in LAYER_SCAN:
            d = D[L] / D[L].norm()
            base, cur = mats(FLOOR, L), mats(path, L)
            per = {}
            for k in base:
                dW = cur[k] - base[k]
                # d lives in the OUTPUT space of o_proj/down_proj -> project rows: dW^T d
                proj = (dW.T @ d).norm().item()
                nulls = []
                for _ in range(100):
                    r = torch.randn_like(d); r = r / r.norm()
                    nulls.append((dW.T @ r).norm().item())
                nt = torch.tensor(nulls)
                lr = {}
                for r_ in (4, 16):
                    U, S, V = torch.svd_lowrank(dW, q=r_)
                    # cos between d and its projection onto the top-r left space
                    pd = U @ (U.T @ d)
                    lr[f"r{r_}"] = round((pd.norm() / d.norm()).item(), 4)
                per[k.split(".")[-2]] = dict(
                    proj=round(proj, 4), null_mean=round(nt.mean().item(), 4),
                    null_p95=round(nt.quantile(0.95).item(), 4),
                    ratio=round(proj / nt.mean().item(), 3), lowrank_capture=lr)
            out[name][f"L{L}"] = per
        print(f"{name} done", flush=True)
    op = ROOT / "steering/out_e5b/projection.json"
    op.parent.mkdir(exist_ok=True)
    op.write_text(json.dumps(out, indent=1))
    print(f"wrote {op}")


if __name__ == "__main__":
    main()
