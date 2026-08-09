#!/usr/bin/env python3
"""Shared helpers for the C-31 General-IF pool builders (2026-08-10).

Used by: build_if_answerability_pool.py, build_if_evidence_v2_1.py,
build_if_format_pool.py, build_if_clean_replay_pool.py.

Reuses the SQuAD-v2 loading / indexing / span utilities of build_if_v2.py by
import, so the formal pools stay id- and normalization-compatible with the
approved v2 proto rows. Adds: AG-News + CREPE-normal loaders, target length
buckets (CONTRACT_DATA §3.5 carrier buckets), cross-pool context-disjointness
checks driven by the pool manifests, and common manifest/sample writers.

Canonical build order (documented in README.md; each later script excludes the
registries of the manifests already on disk):
  1. build_if_answerability_pool.py   2. build_if_evidence_v2_1.py
  3. build_if_format_pool.py          4. build_if_clean_replay_pool.py
"""
import glob
import hashlib
import json
import random
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(OUT))

import build_if_v2 as v2  # noqa: E402  (norm, ctx_hash, load_squad, index_squad, ...)

norm = v2.norm
ctx_hash = v2.ctx_hash
sha256_file = v2.sha256_file
grams = v2.grams
has_digit = v2.has_digit
clean_span = v2.clean_span
evidence_sentence = v2.evidence_sentence
load_squad = v2.load_squad
index_squad = v2.index_squad
load_ns = v2.load_ns

SEED = 20260819  # C-31: all four lines deterministic on this seed

AGNEWS_GLOB = str(Path.home() / ".cache/huggingface/hub/datasets--fancyzhx--ag_news/snapshots/*/data/train-00000-of-00001.parquet")
CREPE_SNAP_GLOB = str(Path.home() / ".cache/huggingface/hub/datasets--tasksource--CREPE/snapshots/*")

AG_LABELS = ["World", "Sports", "Business", "Sci/Tech"]

# Pool key -> (jsonl filename, manifest filename with cross-pool registry).
POOL_FILES = {
    "if_answerability_pool": ("if_answerability_pool.jsonl", "if_answerability_pool_manifest.json"),
    "if_evidence_v2_1": ("if_evidence_v2.1_proto.jsonl", "if_evidence_v2_1_manifest.json"),
    "if_format_pool": ("if_format_pool.jsonl", "if_format_pool_manifest.json"),
    "if_clean_replay_pool": ("if_clean_replay_pool.jsonl", "if_clean_replay_pool_manifest.json"),
}
V2_PROTO_MANIFEST = "if_v2_manifest.json"       # seed-20260818 protos (ans proto merged into pool 1; evd proto superseded by v2.1)
IF_PROTO_MANIFEST = "if_proto_manifest.json"    # seed-20260817 protos (revision + 2 aux probes)

PRINTABLE = re.compile(r"^[\x20-\x7E]+$")


def clean_agnews_text(t: str) -> str:
    """AG-News uses literal backslashes as line separators, and the dump carries
    HTML-entity debris with the leading '&' already stripped ('#39;', 'quot;',
    'lt;b gt;' ...). Clean both forms; drop rows that still look markup-ridden
    at the loader (PRINTABLE + length gates)."""
    t = t.replace("\\", " ")
    for a, b in [("&lt;", "<"), ("&gt;", ">"), ("&amp;", "&"), ("&quot;", '"'), ("&#39;", "'")]:
        t = t.replace(a, b)
    # bare entity remnants (leading & lost in the source dump)
    for a, b in [("#39;", "'"), ("#38;", "&"), ("#036;", "$"), ("#36;", "$"), ("#145;", "'"),
                 ("#146;", "'"), ("#147;", '"'), ("#148;", '"'), ("#150;", "-"),
                 ("#151;", " - "), ("quot;", '"'), ("amp;", "&"), ("nbsp;", " ")]:
        t = t.replace(" " + a, b).replace(a, b)
    # stray markup remnants like 'lt;b gt;' / '<b>' fragments
    t = re.sub(r"\b(?:lt|gt);", " ", t)
    t = re.sub(r"</?[a-zA-Z][^>]{0,20}>", " ", t)
    return norm(t)


def agnews_hash(text: str) -> str:
    return hashlib.md5(norm(text).lower().encode()).hexdigest()[:12]


def load_agnews(min_len=120, max_len=1000):
    """AG-News train rows, cleaned + deduplicated by normalized text hash.
    Returns list of dicts in file order: {idx, text, label, label_name, text_hash}."""
    import pyarrow.parquet as pq
    paths = sorted(glob.glob(AGNEWS_GLOB))
    assert paths, f"AG-News train parquet not found: {AGNEWS_GLOB}"
    raw = pq.read_table(paths[-1]).to_pylist()
    seen, rows = set(), []
    for i, r in enumerate(raw):
        text = clean_agnews_text(r["text"])
        if not (min_len <= len(text) <= max_len) or not PRINTABLE.match(text):
            continue
        h = agnews_hash(text)
        if h in seen:
            continue
        seen.add(h)
        rows.append({"idx": i, "text": text, "label": int(r["label"]),
                     "label_name": AG_LABELS[int(r["label"])], "text_hash": h})
    return rows, Path(paths[-1]).name


def load_crepe_normal():
    """CREPE train rows whose label set is exactly {'normal'} (pure normal)."""
    snap = sorted(glob.glob(CREPE_SNAP_GLOB))[-1]
    rows = [json.loads(l) for l in open(Path(snap) / "train.jsonl")]
    return [r for r in rows if set(r["labels"] or []) == {"normal"}]


# ---------------------------------------------------------------- length buckets
BUCKETS = ["<50", "50-100", "100-200", "200-400", ">=400"]


def bucket(target: str) -> str:
    n = len(norm(target).split())
    if n < 50:
        return "<50"
    if n < 100:
        return "50-100"
    if n < 200:
        return "100-200"
    if n < 400:
        return "200-400"
    return ">=400"


def bucket_dist(rows):
    c = Counter(bucket(r["target"]) for r in rows)
    return {b: c.get(b, 0) for b in BUCKETS}


# ---------------------------------------------------------------- registries
def _load_manifest(fname):
    p = OUT / fname
    return json.loads(p.read_text()) if p.exists() else None


def other_pool_registries(self_name):
    """Union of {squad_ctx, agnews_hash, crepe_id} registries of every OTHER
    C-31 pool manifest already built (canonical order makes this deterministic)."""
    sq, ag, cr = set(), set(), set()
    for name, (_, fname) in POOL_FILES.items():
        if name == self_name:
            continue
        m = _load_manifest(fname)
        if not m:
            continue
        reg = m.get("registry", {})
        sq |= set(reg.get("context_hashes", []))
        ag |= set(reg.get("agnews_text_hashes", []))
        cr |= set(reg.get("crepe_ids", []))
    return sq, ag, cr


def v2_proto_registry():
    """Context hashes consumed by the seed-20260818 protos (incl. donors), and
    the subset that belongs to the answerability proto families (which pool 1
    merges in rather than avoids)."""
    m = _load_manifest(V2_PROTO_MANIFEST)
    assert m, "if_v2_manifest.json missing — v2 protos are a hard prerequisite"
    all_ctx = set(m["registry"]["context_hashes_used_incl_donors"])
    ans_fams = m["pools"]["if_answerability_v2"]["family_ids"]
    ans_ctx = {f.split("squadv2_ctx_")[1] for f in ans_fams}
    return all_ctx, ans_ctx


def revision_proto_crepe_ids():
    m = _load_manifest(IF_PROTO_MANIFEST)
    if not m:
        return set()
    fams = m["pools"].get("if_revision", {}).get("family_ids", [])
    return {f.split("crepe_train_")[1] for f in fams}


# ---------------------------------------------------------------- 8-gram dup rate
def make_content_grams(skeleton):
    """Family-level non-skeleton 8-gram extractor (same method as the protos)."""
    def content_grams(target, n=8):
        text = norm(target)
        for t in skeleton:
            for chunk in re.split(r"\{[a-z0-9_]+\}", t):
                chunk = norm(chunk).strip(" :—-\"")
                if len(chunk.split()) >= 3:
                    text = text.replace(chunk, "\x00")
        out = set()
        for seg in text.split("\x00"):
            out |= grams(seg, n)
        return out
    return content_grams


def family_dup_rate(rows, content_grams):
    fam_grams = {}
    for r in rows:
        fam_grams.setdefault(r["family_id"], set()).update(content_grams(r["target"]))
    seen, dup = set(), 0
    for fid, g in sorted(fam_grams.items()):
        if g & seen:
            dup += 1
        seen |= g
    return round(dup / max(1, len(fam_grams)), 4)


# ---------------------------------------------------------------- writers
def write_pool(key, rows, manifest):
    jname, mname = POOL_FILES[key]
    p = OUT / jname
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
    manifest["file"] = p.name
    manifest["n"] = len(rows)
    manifest["sha256_16"] = sha256_file(p)
    manifest["by_subtype"] = dict(Counter(r["subtype"] for r in rows))
    manifest["n_families"] = len({r["family_id"] for r in rows})
    manifest["target_length_buckets"] = bucket_dist(rows)
    (OUT / mname).write_text(json.dumps(manifest, indent=2, ensure_ascii=False))
    return manifest


def write_sample(name, rows, per_subtype, total, seed=SEED):
    rng = random.Random(seed)
    by_sub = defaultdict(list)
    for r in rows:
        by_sub[r["subtype"]].append(r)
    sample = []
    for sub in sorted(by_sub):
        sample += rng.sample(by_sub[sub], min(per_subtype, len(by_sub[sub])))
    if len(sample) < total:
        extra = [r for r in rows if r not in sample]
        sample += rng.sample(extra, total - len(sample))
    rng.shuffle(sample)
    md = [f"# sample10 — {name} (seed {seed}; random, >= {per_subtype} per subtype, full text)", ""]
    for i, r in enumerate(sample):
        md += [f"## {i+1}. {r['family_id']} [{r['subtype']}]", "",
               "**prompt**", "```", r["prompt"], "```",
               "**target**", "```", r["target"], "```", ""]
    (OUT / f"sample10_{name}.md").write_text("\n".join(md))
