"""Per-item leak flags (v1 §1.3-M + LOOP0_RULINGS §3-R2).

Rule per domain:
  v2 / v3 / v3_1 (synthetic triple worlds, relayed from the v2 inject ckpt):
      item leak = ALL of its gold_symbolic_facts triples ⊆ exposure set
      (full answer support memorizable). Exposure split per R-2:
        leak_sft    : triples of the repair-SFT train file (gold + surface symbolic facts)
        leak_inject : triples of the injection corpus data_v2/inject.jsonl (351)
        leak_any    : leak_sft OR leak_inject          <- the ledger's M excision flag
      R-items carry operand-level triples (op, applied_to, "a,b"); the injection corpus
      has rule statements only (no operand triples), so computed items are only leaked
      via an exact operand collision in the SFT train file.
  v4 (GSM, no injection, relay from the pre-repair model):
      leak = exact normalised question in train  OR  (gold final value + multiset of
      intermediate values in the gold trace) collides with a train item. Expected ≈ 0
      (train from GSM train split, eval from test split) — negative control.
  v5 (counterfactual two-hop, relay from the pre-repair model):
      triple rule vs data_v5 train only (no injection lineage). Expected 0 (design gate).

Output: ledger/leak_flags_{dom}.jsonl  {id, leak_sft, leak_inject, leak_any}
        + printed summary table (goes into LEDGER_REPORT).
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def git_jsonl(branch, path):
    out = subprocess.run(["git", "show", f"{branch}:{path}"], cwd=ROOT,
                         capture_output=True, text=True, check=True).stdout
    return [json.loads(l) for l in out.splitlines() if l.strip()]


def jsonl(path):
    return [json.loads(l) for l in (ROOT / path).open() if l.strip()]


def tri_set(items, fields=("gold_symbolic_facts", "symbolic_facts")):
    s = set()
    for it in items:
        for f in fields:
            for tri in it.get(f) or []:
                if isinstance(tri, list) and len(tri) == 3:
                    s.add(tuple(str(x).strip().lower() for x in tri))
    return s


def item_tris(it):
    return [tuple(str(x).strip().lower() for x in tri)
            for tri in it.get("gold_symbolic_facts") or [] if isinstance(tri, list) and len(tri) == 3]


def inject_tris():
    s = set()
    for r in jsonl("data_v2/inject.jsonl"):
        tri = r.get("symbolic_fact")
        if isinstance(tri, list) and len(tri) == 3:
            s.add(tuple(str(x).strip().lower() for x in tri))
    return s


def norm_txt(s):
    return re.sub(r"\s+", " ", (s or "").strip().lower())


def nums(s):
    return tuple(sorted(re.findall(r"-?\d+(?:\.\d+)?", s or "")))


def flag_triple_domain(dom, eval_items, sft_train, inj):
    flags = []
    for it in eval_items:
        tris = item_tris(it)
        # no triples recorded (shouldn't happen in v2/v3 lineage) -> conservatively leak_sft
        l_sft = bool(tris) and all(t in sft_train for t in tris)
        l_inj = bool(tris) and all(t in inj for t in tris) if inj is not None else False
        l_any = bool(tris) and all((t in sft_train) or (inj is not None and t in inj) for t in tris)
        flags.append({"id": it["id"], "leak_sft": int(l_sft),
                      "leak_inject": int(l_inj), "leak_any": int(l_any)})
    return flags


def v4_numkey(it):
    """(gold final, >=2 intermediate values) — the v1 §1.3-M "final + key intermediates"
    combination. Traces with <2 intermediates (keep/abstain actionized traces carry none)
    have no identifying numeric signature -> no key (calibrated on the 2026-07-02 autopsy:
    the naive all-numbers key produced 217 spurious collisions with 0 source/question overlap)."""
    g = norm_txt(str(it.get("gold_answer")))
    inter = tuple(v for v in nums(it.get("repair_trace")) if norm_txt(v) != g)
    return (g, inter) if len(inter) >= 2 else None


def flag_v4(eval_items, train_items):
    tq = {norm_txt(t["problem"]) for t in train_items}
    tsrc = {t.get("source_id") for t in train_items if t.get("source_id")}
    tkey = {k for k in (v4_numkey(t) for t in train_items) if k}
    flags = []
    for it in eval_items:
        k = v4_numkey(it)
        hit = (norm_txt(it["problem"]) in tq or it.get("source_id") in tsrc or
               (k is not None and k in tkey))
        flags.append({"id": it["id"], "leak_sft": int(hit), "leak_inject": 0, "leak_any": int(hit)})
    return flags


def main():
    inj = inject_tris()
    out_rows = []

    specs = [
        ("v2",   jsonl("data_v2/repair_eval.jsonl"),   tri_set(jsonl("data_v2/repair_train.jsonl")),   inj),
        ("v2_1", jsonl("data_v2_1/repair_eval.jsonl"), tri_set(jsonl("data_v2_1/repair_train.jsonl")), inj),
        ("v3",   jsonl("data_v3/repair_eval.jsonl"),   tri_set(jsonl("data_v3/repair_train.jsonl")),   inj),
        ("v3_1", jsonl("data_v3_1/repair_eval.jsonl"), tri_set(jsonl("data_v3_1/repair_train.jsonl")), inj),
        ("v5",   git_jsonl("scenario-repair-b-prime", "data_v5/repair_eval.jsonl"),
                 tri_set(git_jsonl("scenario-repair-b-prime", "data_v5/repair_train.jsonl")), None),
    ]
    for dom, ev, sft, inj_d in specs:
        flags = flag_triple_domain(dom, ev, sft, inj_d)
        write(dom, flags, out_rows, len(ev))

    ev4 = jsonl("data_v4/repair_eval.jsonl")
    write("v4", flag_v4(ev4, jsonl("data_v4/repair_train.jsonl")), out_rows, len(ev4))

    print("| domain | n | leak_sft | leak_inject | leak_any |")
    print("|---|---|---|---|---|")
    for r in out_rows:
        print("| {dom} | {n} | {s} ({sp:.1%}) | {i} ({ip:.1%}) | {a} ({ap:.1%}) |".format(**r))


def write(dom, flags, out_rows, n):
    p = ROOT / f"ledger/leak_flags_{dom}.jsonl"
    with p.open("w") as f:
        for r in flags:
            f.write(json.dumps(r) + "\n")
    s = sum(r["leak_sft"] for r in flags)
    i = sum(r["leak_inject"] for r in flags)
    a = sum(r["leak_any"] for r in flags)
    out_rows.append(dict(dom=dom, n=n, s=s, sp=s / n, i=i, ip=i / n, a=a, ap=a / n))


if __name__ == "__main__":
    main()
