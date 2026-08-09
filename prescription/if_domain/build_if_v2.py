#!/usr/bin/env python3
"""General-IF v2 prototype pool builder (C-30 construct-drift correction; 2026-08-09).

Rebuilds the two CORE IF component pools on SQuAD v2 per INSTRUCTION_C30 rulings #4/#5:

  if_answerability_v2_proto.jsonl  component=answerability  n=240
      Core construct: INFORMATION SUFFICIENCY of the given passage (not premise
      validity — that is now the auxiliary probe premise_validity_aux_proto.jsonl).
      * 200 rows = 100 same-context pairs from SQuAD v2 train: the SAME paragraph
        carries one answerable question (target = the gold answer span text) and one
        official is_impossible question (target = fixed refusal genre A:
        "The passage does not contain the information needed to answer this question.").
      * 40 rows = 20 same-context pairs of the required-field structured task
        (C-30 #4 "必填字段缺失型结构化任务"): extract a named field defined by a SQuAD
        question; field present -> "STATUS: OK / FINAL_ANSWER: <span>", field absent
        (is_impossible question) -> "STATUS: INSUFFICIENT / FINAL_ANSWER: NULL".

  if_evidence_v2_proto.jsonl  component=evidence_robustness  n=200
      Core construct: answer FROM in-context EVIDENCE under interference; the correct
      evidence passage is ALWAYS present (C-30 #5 — unlike the demoted sycophancy pool,
      which had pressure but no evidence). Three subtypes, evenly split, all from the
      SQuAD v2 answerable subset:
      * distractor_passage (67): a topic-related distractor paragraph (same SQuAD
        title, gold answer absent from it) is shown next to the true evidence
        paragraph in rng order; target names the evidence passage, quotes the
        evidence sentence, answers.
      * wrong_span (67): prompt says someone believes the answer is <another
        plausible span from the SAME paragraph — the gold of a different question on
        that paragraph, crude-type-matched, no substring relation to gold>; target
        refutes it against the quoted evidence sentence and gives the gold answer.
      * conflicting_statement (66): an "unverified note" = the evidence sentence
        with the gold span replaced by a plausible wrong span is appended; target
        points out the conflict and rules that the passage evidence governs.

Isolation / built-in verification (all hard-asserted at build time):
  * zero intersection with natural_set_v1 (calibration set) by normalized text AND
    source_id — trivially satisfied (naturalset has no SQuAD) but asserted anyway;
  * SQuAD v2 is corpus-disjoint from every existing eval family in this repo
    (GSM8K, SVAMP, 2Wiki, StrategyQA, CREPE, FalseQA, sycophancy-eval, NQ-Swap);
    all consumed SQuAD question ids / titles / context hashes (donors included) are
    registered in if_v2_manifest.json so future SQuAD-based evals can exclude them;
  * no target leakage: answerable/struct-OK gold span verified present in the
    passage; refusal / INSUFFICIENT targets verified to be the exact fixed genre
    (no plausible answer text — the train parquet carries none for impossible rows);
    wrong_span != gold and no mutual substring; distractor passage does not contain
    the gold answer; conflicting note != the true evidence sentence;
  * non-skeleton 8-gram target repetition rate at family level; row/pair counts.

Deterministic: SEED=20260818. Old three proto pools are left in place (revision
unchanged; the two demoted ones renamed by build_if_proto.py per C-30 — see there).
Outputs: if_answerability_v2_proto.jsonl, if_evidence_v2_proto.jsonl,
if_v2_manifest.json, sample10_if_answerability_v2.md, sample10_if_evidence_v2.md.

STATUS: prototype (proto n=240/200); do NOT expand to formal pools or start IF dose
training before the C-30 audit pack is re-approved (C-30 #10).
"""
import glob
import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[1]
NS = REPO / "naturalset" / "natural_set_v1.jsonl"
SEED = 20260818
GEN_VER = "ifv2-v0.1"

SQUAD_GLOB = str(Path.home() / ".cache/huggingface/hub/datasets--rajpurkar--squad_v2/snapshots/*/squad_v2/train-*.parquet")

N_CORE_PAIRS = 100      # -> 200 rows
N_STRUCT_PAIRS = 20     # -> 40 rows, answerability total 240
N_EVD = {"distractor_passage": 67, "wrong_span": 67, "conflicting_statement": 66}

CTX_MIN, CTX_MAX = 300, 1800
Q_MIN = 20
SPAN_MAX = 120
EVSENT_MAX = 340

# ---------------------------------------------------------------- genre templates
CORE_PROMPT = ("Passage:\n{ctx}\n\nQuestion: {q}\n\n"
               "Answer using only the passage. Give the exact answer span from the "
               "passage; if the passage does not contain the information needed to "
               "answer, say so explicitly.")
UNANS_TGT = "The passage does not contain the information needed to answer this question."

STRUCT_PROMPT = ("Passage:\n{ctx}\n\n"
                 "You are filling one required field of a structured record from this "
                 "passage.\nField \"{field}\" — defined as the answer to: {q}\n\n"
                 "Return exactly two lines:\n"
                 "STATUS: OK or INSUFFICIENT\n"
                 "FINAL_ANSWER: <the field value as a short span from the passage, or NULL>")
STRUCT_OK_TGT = "STATUS: OK\nFINAL_ANSWER: {span}"
STRUCT_NULL_TGT = "STATUS: INSUFFICIENT\nFINAL_ANSWER: NULL"

EV1_PROMPT = ("Passage [1]:\n{p1}\n\nPassage [2]:\n{p2}\n\nQuestion: {q}\n\n"
              "Exactly one of the passages contains the evidence needed to answer. "
              "Identify it, justify briefly, and answer based on that evidence.")
EV1_TGT = ("Passage [{k}] is the one that answers this question — it states: \"{ev}\" "
           "The other passage is on the same topic but does not contain this "
           "information. Answer: {gold}")

EV2_PROMPT = ("Passage:\n{ctx}\n\nQuestion: {q}\n\n"
              "Someone believes the answer is \"{wrong}\". Check that suggestion "
              "against the passage evidence, then answer the question with a brief "
              "justification.")
EV2_TGT = ("The suggestion is wrong: \"{wrong}\" is not what the passage gives for "
           "this question. The passage states: \"{ev}\" So the correct answer is {gold}.")

EV3_PROMPT = ("Passage:\n{ctx}\n\nUnverified note appended by a reader: {note}\n\n"
              "Question: {q}\n\n"
              "Answer the question based on the evidence, with a brief justification.")
EV3_TGT = ("The unverified note conflicts with the passage, which states: \"{ev}\" "
           "The passage is the evidence to go by, so the answer is {gold}.")

GENRE_SKELETON = [CORE_PROMPT, UNANS_TGT, STRUCT_PROMPT, STRUCT_OK_TGT, STRUCT_NULL_TGT,
                  EV1_PROMPT, EV1_TGT, EV2_PROMPT, EV2_TGT, EV3_PROMPT, EV3_TGT]


# ---------------------------------------------------------------- small utils
def norm(s: str) -> str:
    return " ".join(str(s).split())


def sha256_file(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def ctx_hash(ctx: str) -> str:
    return hashlib.md5(norm(ctx).encode()).hexdigest()[:12]


def grams(text: str, n: int = 8):
    t = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(t[i:i + n]) for i in range(len(t) - n + 1)}


def has_digit(s: str) -> bool:
    return any(c.isdigit() for c in s)


def clean_span(s: str) -> str:
    """Trim SQuAD annotation debris (trailing/leading punctuation) from a span;
    the result stays a substring of the normalized context."""
    s = norm(s)
    while s and s[-1] in ",;:.":
        s = s[:-1].rstrip()
    while s and s[0] in ",;:":
        s = s[1:].lstrip()
    return s


# Evidence-pool plausibility filters (added after first sample audit: long noisy
# gold spans and length-mismatched substitutions made conflicting notes ungrammatical)
EVD_GOLD_MAX_TOKENS = 8
EVD_LEN_MATCH_TOKENS = 3


STOP = set("the a an of to in on for and or is are was were be been what who whom whose "
           "why how when where which does do did can could would should it its this that "
           "with as by from at many much".split())


def field_name(question: str) -> str:
    words = [w for w in re.findall(r"[a-z0-9]+", question.lower()) if w not in STOP]
    return "_".join(words[:4])


def sentence_spans(ctx: str):
    spans, start = [], 0
    for m in re.finditer(r"(?<=[.!?])\s+", ctx):
        spans.append((start, m.start()))
        start = m.end()
    spans.append((start, len(ctx)))
    return spans


def evidence_sentence(ctx: str, ans_start: int, gold: str):
    """The context sentence that contains the gold span (by char offset)."""
    for s, e in sentence_spans(ctx):
        if s <= ans_start < e:
            sent = norm(ctx[s:e])
            if gold in sent and len(sent) <= EVSENT_MAX:
                return sent
    return None


# ---------------------------------------------------------------- load sources
def load_squad():
    import pyarrow.parquet as pq
    paths = sorted(glob.glob(SQUAD_GLOB))
    assert paths, f"SQuAD v2 train parquet not found: {SQUAD_GLOB}"
    rows = pq.read_table(paths[-1]).to_pylist()
    return rows, paths[-1]


def load_ns():
    rows = [json.loads(l) for l in NS.open()]
    return ({norm(r["text"]) for r in rows}, {str(r["source_id"]) for r in rows})


def index_squad(rows):
    """Group by context, keep file order; per context collect answerable (with
    verified span offsets) and unanswerable questions."""
    by_ctx = {}
    by_title = defaultdict(list)          # title -> [ctx_key in order]
    for r in rows:
        ctx = r["context"]
        key = ctx_hash(ctx)
        if key not in by_ctx:
            by_ctx[key] = {"ctx": ctx, "title": r["title"], "ans": [], "una": []}
            by_title[r["title"]].append(key)
        q = norm(r["question"])
        if len(q) < Q_MIN:
            continue
        if r["answers"]["text"]:
            raw = r["answers"]["text"][0]
            gold = clean_span(raw)
            start = r["answers"]["answer_start"][0]
            if (1 <= len(gold) <= SPAN_MAX and gold in ctx
                    and ctx[start:start + len(raw)] == raw):
                by_ctx[key]["ans"].append({"id": r["id"], "q": q, "gold": gold, "start": start})
        else:
            by_ctx[key]["una"].append({"id": r["id"], "q": q})
    return by_ctx, by_title


# ---------------------------------------------------------------- pool 1: answerability v2
def build_answerability(by_ctx, used):
    keys = [k for k, v in by_ctx.items()
            if v["ans"] and v["una"] and CTX_MIN <= len(v["ctx"]) <= CTX_MAX]
    random.Random(SEED).shuffle(keys)
    rows, n_core, n_struct = [], 0, 0
    for k in keys:
        if n_core >= N_CORE_PAIRS and n_struct >= N_STRUCT_PAIRS:
            break
        v = by_ctx[k]
        a = min(v["ans"], key=lambda x: x["id"])
        u = min(v["una"], key=lambda x: x["id"])
        if norm(a["q"]).lower() == norm(u["q"]).lower():
            continue
        ctx = norm(v["ctx"])
        if a["gold"] not in ctx:      # normalization must not break the span
            continue
        common = dict(family_id=f"squadv2_ctx_{k}", source_split="train",
                      generator_id="A", generator_version=GEN_VER,
                      component="answerability", domain="general_if",
                      meta={"title": v["title"], "context_hash": k})
        if n_core < N_CORE_PAIRS:
            rows.append(dict(common, subtype="answerable", source_id=a["id"],
                             prompt=CORE_PROMPT.format(ctx=ctx, q=a["q"]),
                             target=a["gold"]))
            rows.append(dict(common, subtype="unanswerable", source_id=u["id"],
                             prompt=CORE_PROMPT.format(ctx=ctx, q=u["q"]),
                             target=UNANS_TGT))
            n_core += 1
        else:
            f_ok, f_null = field_name(a["q"]), field_name(u["q"])
            if not f_ok or not f_null or f_ok == f_null:
                continue
            rows.append(dict(common, subtype="struct_found", source_id=a["id"],
                             prompt=STRUCT_PROMPT.format(ctx=ctx, field=f_ok, q=a["q"]),
                             target=STRUCT_OK_TGT.format(span=a["gold"])))
            rows.append(dict(common, subtype="struct_insufficient", source_id=u["id"],
                             prompt=STRUCT_PROMPT.format(ctx=ctx, field=f_null, q=u["q"]),
                             target=STRUCT_NULL_TGT))
            n_struct += 1
        used.add(k)
    assert n_core == N_CORE_PAIRS and n_struct == N_STRUCT_PAIRS, (n_core, n_struct)
    return rows


# ---------------------------------------------------------------- pool 2: evidence v2
def pick_wrong(cand, others, ctx):
    """A plausible wrong span for cand: the gold of another question on the SAME
    paragraph, crude-type-matched (digit vs non-digit), no substring relation,
    token length within EVD_LEN_MATCH_TOKENS of gold (keeps the conflicting-note
    substitution roughly well-formed)."""
    for o in sorted(others, key=lambda x: x["id"]):
        w, g = o["gold"], cand["gold"]
        if o["id"] == cand["id"] or w.lower() == g.lower():
            continue
        if w.lower() in g.lower() or g.lower() in w.lower():
            continue
        if has_digit(w) != has_digit(g):
            continue
        if len(w.split()) > EVD_GOLD_MAX_TOKENS:
            continue
        if abs(len(w.split()) - len(g.split())) > EVD_LEN_MATCH_TOKENS:
            continue
        if all(tok in STOP or len(tok) <= 3 for tok in re.findall(r"[a-z0-9']+", w.lower())):
            continue          # degenerate function-word spans ("more", "many") are not plausible answers
        if w not in ctx:
            continue
        return w
    return None


def build_evidence(by_ctx, by_title, used):
    keys = [k for k, v in by_ctx.items()
            if k not in used and v["ans"] and CTX_MIN <= len(v["ctx"]) <= CTX_MAX]
    random.Random(SEED + 1).shuffle(keys)
    coin = random.Random(SEED + 2)
    quota = dict(N_EVD)
    rows = []
    for k in keys:
        if not any(quota.values()):
            break
        v = by_ctx[k]
        ctx = norm(v["ctx"])
        cand = None
        for a in sorted(v["ans"], key=lambda x: x["id"]):
            if (len(a["gold"].split()) <= EVD_GOLD_MAX_TOKENS and a["gold"] in ctx
                    and evidence_sentence(v["ctx"], a["start"], a["gold"])):
                cand = a
                break
        if cand is None:
            continue
        ev = evidence_sentence(v["ctx"], cand["start"], cand["gold"])
        wrong = pick_wrong(cand, v["ans"], ctx)
        # subtype-specific plausibility: a suggested wrong answer must not sit in the
        # question itself; a conflicting substitution must not duplicate text already
        # in the evidence sentence
        wrong2 = wrong if wrong and wrong.lower() not in cand["q"].lower() else None
        wrong3 = wrong if wrong and wrong.lower() not in ev.lower() else None
        donor = None
        for dk in by_title[v["title"]]:
            dv = by_ctx[dk]
            if (dk != k and dk not in used and CTX_MIN <= len(dv["ctx"]) <= CTX_MAX
                    and cand["gold"].lower() not in norm(dv["ctx"]).lower()):
                donor = dk
                break
        # assign this context to the neediest subtype it can serve
        able = [(quota["distractor_passage"], "distractor_passage") if donor else (-1, ""),
                (quota["wrong_span"], "wrong_span") if wrong2 else (-1, ""),
                (quota["conflicting_statement"], "conflicting_statement") if wrong3 else (-1, "")]
        able = [(n, s) for n, s in able if s and n > 0]
        if not able:
            continue
        able.sort(key=lambda x: (-x[0], x[1]))
        sub = able[0][1]
        common = dict(family_id=f"squadv2_ctx_{k}", source_id=cand["id"],
                      source_split="train", generator_id="A", generator_version=GEN_VER,
                      component="evidence_robustness", domain="general_if")
        meta = {"title": v["title"], "context_hash": k, "question": cand["q"],
                "gold": cand["gold"], "evidence_sentence": ev}
        if sub == "distractor_passage":
            dctx = norm(by_ctx[donor]["ctx"])
            k_ev = coin.choice([1, 2])
            p1, p2 = (ctx, dctx) if k_ev == 1 else (dctx, ctx)
            rows.append(dict(common, subtype=sub,
                             prompt=EV1_PROMPT.format(p1=p1, p2=p2, q=cand["q"]),
                             target=EV1_TGT.format(k=k_ev, ev=ev, gold=cand["gold"]),
                             meta=dict(meta, donor_context_hash=donor, evidence_passage=k_ev)))
            used.add(donor)
        elif sub == "wrong_span":
            rows.append(dict(common, subtype=sub,
                             prompt=EV2_PROMPT.format(ctx=ctx, q=cand["q"], wrong=wrong2),
                             target=EV2_TGT.format(wrong=wrong2, ev=ev, gold=cand["gold"]),
                             meta=dict(meta, wrong_span=wrong2)))
        else:
            wrong = wrong3
            note = ev.replace(cand["gold"], wrong, 1)
            if note == ev or cand["gold"] in note:
                continue
            rows.append(dict(common, subtype=sub,
                             prompt=EV3_PROMPT.format(ctx=ctx, note=note, q=cand["q"]),
                             target=EV3_TGT.format(ev=ev, gold=cand["gold"]),
                             meta=dict(meta, wrong_span=wrong, conflicting_note=note)))
        quota[sub] -= 1
        used.add(k)
    assert not any(quota.values()), f"unfilled evidence quota: {quota}"
    return rows


# ---------------------------------------------------------------- verification
def content_grams(target: str, n: int = 8):
    """8-grams of a target with the literal genre-skeleton chunks cut out; grams
    never span a cut (same method as build_if_proto.py)."""
    text = norm(target)
    for t in GENRE_SKELETON:
        for chunk in re.split(r"\{[a-z0-9_]+\}", t):
            chunk = norm(chunk).strip(" :—-\"")
            if len(chunk.split()) >= 3:
                text = text.replace(chunk, "\x00")
    out = set()
    for seg in text.split("\x00"):
        out |= grams(seg, n)
    return out


def verify(pools, by_ctx, ns_txt, ns_ids):
    errs = []
    want_n = {"if_answerability_v2": 2 * (N_CORE_PAIRS + N_STRUCT_PAIRS),
              "if_evidence_v2": sum(N_EVD.values())}
    want_rows_per_fam = {"if_answerability_v2": 2, "if_evidence_v2": 1}
    all_fams = []
    for name, rows in pools.items():
        if len(rows) != want_n[name]:
            errs.append((name, "bad_n", len(rows)))
        fams = [r["family_id"] for r in rows]
        all_fams.append(set(fams))
        if any(c != want_rows_per_fam[name] for c in Counter(fams).values()):
            errs.append((name, "family_row_count"))
        if len({r["prompt"] for r in rows}) != len(rows):
            errs.append((name, "dup_prompt"))
        for r in rows:
            for k in ("family_id", "component", "subtype", "prompt", "target",
                      "source_id", "source_split", "generator_id", "domain"):
                if not r.get(k):
                    errs.append((name, "missing_field", k, r.get("family_id")))
            # calibration-set isolation (corpus-disjoint by construction; asserted)
            if norm(r["prompt"]) in ns_txt or r["source_id"] in ns_ids:
                errs.append((name, "naturalset_leak", r["family_id"]))
            ctx = norm(by_ctx[r["meta"]["context_hash"]]["ctx"])
            sub, t = r["subtype"], r["target"]
            if sub in ("answerable", "struct_found"):
                span = t if sub == "answerable" else t.split("FINAL_ANSWER:")[-1].strip()
                if span not in ctx:
                    errs.append((name, "gold_span_not_in_context", r["family_id"]))
            elif sub == "unanswerable":
                if t != UNANS_TGT:      # fixed genre A, nothing else (no leaked answer)
                    errs.append((name, "refusal_genre_broken", r["family_id"]))
            elif sub == "struct_insufficient":
                if t != STRUCT_NULL_TGT:
                    errs.append((name, "insufficient_genre_broken", r["family_id"]))
            else:                       # evidence pool
                gold, ev = r["meta"]["gold"], r["meta"]["evidence_sentence"]
                if gold not in ev or ev not in ctx or ev not in t:
                    errs.append((name, "evidence_sentence_broken", r["family_id"]))
                if gold not in t:
                    errs.append((name, "gold_missing_in_target", r["family_id"]))
                if sub == "distractor_passage":
                    dctx = norm(by_ctx[r["meta"]["donor_context_hash"]]["ctx"])
                    if dctx not in r["prompt"] or ctx not in r["prompt"]:
                        errs.append((name, "passage_missing_in_prompt", r["family_id"]))
                    if gold.lower() in dctx.lower():
                        errs.append((name, "gold_in_distractor", r["family_id"]))
                    if f"Passage [{r['meta']['evidence_passage']}]" not in t:
                        errs.append((name, "wrong_passage_named", r["family_id"]))
                else:
                    w = r["meta"]["wrong_span"]
                    if (w.lower() == gold.lower() or w.lower() in gold.lower()
                            or gold.lower() in w.lower()):
                        errs.append((name, "wrong_span_equals_gold", r["family_id"]))
                    if sub == "wrong_span":
                        if w not in ctx:
                            errs.append((name, "wrong_span_not_plausible", r["family_id"]))
                        if w.lower() in r["meta"]["question"].lower():
                            errs.append((name, "wrong_span_in_question", r["family_id"]))
                    if sub == "conflicting_statement":
                        note = r["meta"]["conflicting_note"]
                        if note == ev or note not in r["prompt"] or w not in note:
                            errs.append((name, "conflict_note_broken", r["family_id"]))
                        if w.lower() in ev.lower():
                            errs.append((name, "wrong_span_already_in_evidence", r["family_id"]))
    # cross-pool family (=context) disjointness
    if all_fams[0] & all_fams[1]:
        errs.append(("cross_pool", "family_collision", len(all_fams[0] & all_fams[1])))
    # non-skeleton 8-gram target repetition, family level
    dup_rates = {}
    for name, rows in pools.items():
        fam_grams = {}
        for r in rows:
            fam_grams.setdefault(r["family_id"], set()).update(content_grams(r["target"]))
        seen, dup = set(), 0
        for fid, g in sorted(fam_grams.items()):
            if g & seen:
                dup += 1
            seen |= g
        dup_rates[name] = round(dup / max(1, len(fam_grams)), 4)
    return errs, dup_rates


# ---------------------------------------------------------------- samples
def write_sample(name, rows, per_subtype, total):
    rng = random.Random(SEED)
    by_sub = defaultdict(list)
    for r in rows:
        by_sub[r["subtype"]].append(r)
    sample = []
    for sub in sorted(by_sub):
        sample += rng.sample(by_sub[sub], per_subtype)
    extra = [r for r in rows if r not in sample]
    if len(sample) < total:
        sample += rng.sample(extra, total - len(sample))
    rng.shuffle(sample)
    md = [f"# sample10 — {name}_proto (seed {SEED}; random, >= {per_subtype} per subtype, full text)", ""]
    for i, r in enumerate(sample):
        md += [f"## {i+1}. {r['family_id']} [{r['subtype']}]", "",
               "**prompt**", "```", r["prompt"], "```",
               "**target**", "```", r["target"], "```", ""]
    (OUT / f"sample10_{name}.md").write_text("\n".join(md))


# ---------------------------------------------------------------- main
def main():
    squad_rows, parquet_path = load_squad()
    ns_txt, ns_ids = load_ns()
    by_ctx, by_title = index_squad(squad_rows)

    n_ans = sum(1 for r in squad_rows if r["answers"]["text"])
    supply = {
        "train_total_questions": len(squad_rows),
        "answerable": n_ans,
        "unanswerable": len(squad_rows) - n_ans,
        "unique_contexts": len(by_ctx),
        "contexts_with_both_ans_and_unans": sum(1 for v in by_ctx.values() if v["ans"] and v["una"]),
        "contexts_with_both_in_length_window": sum(
            1 for v in by_ctx.values()
            if v["ans"] and v["una"] and CTX_MIN <= len(v["ctx"]) <= CTX_MAX),
        "titles": len(by_title),
    }

    used = set()
    pools = {"if_answerability_v2": build_answerability(by_ctx, used),
             "if_evidence_v2": build_evidence(by_ctx, by_title, used)}
    errs, dup_rates = verify(pools, by_ctx, ns_txt, ns_ids)
    assert not errs, errs

    manifest = {
        "seed": SEED, "generator_version": GEN_VER, "instruction": "C-30 #4/#5",
        "source": {"dataset": "rajpurkar/squad_v2", "split": "train",
                   "parquet": Path(parquet_path).name, "license": "CC BY-SA 4.0"},
        "squad_supply_account": supply,
        "pools": {},
        "verify_errors": errs,
        "nonskeleton_8gram_dup_rate": dup_rates,
        "eval_disjointness_note": (
            "SQuAD v2 is corpus-disjoint from every eval family in this repo (GSM8K, "
            "SVAMP, 2Wiki, StrategyQA, CREPE, FalseQA, sycophancy-eval, NQ-Swap, "
            "natural_set_v1) — asserted at build time against natural_set_v1 by text "
            "and id. All SQuAD ids/titles/context hashes consumed here (donor "
            "distractor contexts included) are registered below; any future "
            "SQuAD-based eval (incl. IF format F-A carriers) must exclude them. "
            "SQuAD dev split remains untouched / reserved for eval."),
        "aux_renames": {
            "if_answerability_proto.jsonl": "premise_validity_aux_proto.jsonl",
            "if_evidence_proto.jsonl": "suggestion_pressure_aux_proto.jsonl",
            "reason": "C-30 #4/#5: demoted to auxiliary probes (construct drift)."},
        "registry": {
            "squad_question_ids": sorted({r["source_id"] for rows in pools.values() for r in rows}),
            "squad_titles": sorted({r["meta"]["title"] for rows in pools.values() for r in rows}),
            "context_hashes_used_incl_donors": sorted(used)},
    }
    for name, rows in pools.items():
        p = OUT / f"{name}_proto.jsonl"
        p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n")
        manifest["pools"][name] = {
            "file": p.name, "n": len(rows), "sha256_16": sha256_file(p),
            "by_subtype": dict(Counter(r["subtype"] for r in rows)),
            "n_families": len({r["family_id"] for r in rows}),
            "family_ids": sorted({r["family_id"] for r in rows}),
        }
    write_sample("if_answerability_v2", pools["if_answerability_v2"], 3, 12)
    write_sample("if_evidence_v2", pools["if_evidence_v2"], 3, 10)
    (OUT / "if_v2_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False))

    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "family_ids"}
                      for k, v in manifest["pools"].items()}, indent=2))
    print("supply:", json.dumps(supply))
    print("verify_errors:", errs)
    print("nonskeleton_8gram_dup_rate:", dup_rates)


if __name__ == "__main__":
    main()
