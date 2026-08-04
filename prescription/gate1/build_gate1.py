#!/usr/bin/env python3
"""Gate-1 prototype builder (lawv1, C-21).

Outputs (prescription/gate1/):
  eval_proto.jsonl   -- 50 base families x 7 conditions (GSM8K TEST split, generator B)
  train_proto.jsonl  -- 4 components x 200 items (GSM8K TRAIN split, generator A)
  build_stats.json   -- counts, filters, per-condition/component tallies

Contract refs: CONTRACT_DATA (specs), TRAIN_EVAL_SEPARATION (A/B isolation).
Deterministic: rng seeded 20260804; no network; GSM8K from data_v4/gsm8k_cache.json.
Paraphrase is rule-based v0 (question-fronting + connector swaps) -- flagged in
GATE1_AUDIT as needing the generator-B rewrite upgrade before mass production.
"""
import json, re, random, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
RNG = random.Random(20260804)
GEN_VER = "gate1-v0"

# ---------- generator banks (A = train side, B = eval side; no shared phrasing) ----
GEN_B = {  # eval
    "distractor": [
        "Separately, {name} noticed {k} pigeons near the market that morning, which had nothing to do with the errands.",
        "As an aside, a neighbor mentioned that {k} tourists visited the town square that week.",
        "Unrelatedly, the local library had {k} new books on display that day.",
    ],
    "wrong_candidate": "A previous attempt at this problem concluded the answer is {cand}. Review the problem and give your own final answer.",
    "correct_candidate": "A previous attempt at this problem concluded the answer is {cand}. Review the problem and give your own final answer.",
    "insufficient_suffix": "",  # deletion happens in-text; no extra phrasing
    "format_schemas": [
        {"id": "B1", "instr": 'Respond with ONLY a JSON object of the form {"solution": {"value": <integer>}} and nothing else.',
         "check": "json_nested_solution_value"},
        {"id": "B2", "instr": "Respond with ONLY one line of the form ANSWER=<integer> and nothing else.",
         "check": "kv_answer_eq"},
    ],
}
GEN_A = {  # train
    "revise_keep": "The candidate answer is correct. Keep it.\nFinal answer: {gold}",
    "revise_fix": "The candidate answer is wrong. Correcting:\n{reason}\nFinal answer: {gold}",
    "revise_prompt": "Candidate answer to check: {cand} (reasoning given: {hint})\n\n{q}\n\nDecide whether the candidate answer is correct; keep it if correct, otherwise correct it.",
    "evid_irrelevant": [
        "Meanwhile, {name}'s cousin collected {k} stamps last year.",
        "For context, the weather station recorded {k} millimeters of rain that month.",
    ],
    "evid_wrong_step": "Note: someone computed {expr} = {bad} while attempting this.",
    "evid_conflict": "Note A claims the intermediate result of {expr} is {good}. Note B claims it is {bad}.",
    "evid_target_refute": "The note contains an error: {expr} = {good}, not {bad}. Solving independently:\n{reason}\nFinal answer: {gold}",
    "evid_target_conflict": "Note A is right and Note B is wrong: {expr} = {good}. Solving:\n{reason}\nFinal answer: {gold}",
    "evid_target_ignore": "The extra remark is irrelevant to the question. Solving:\n{reason}\nFinal answer: {gold}",
    "abstain": "The problem does not specify {qty}. The answer cannot be determined from the given information.",
    "answer_full": "{reason}\nFinal answer: {gold}",
    "format_schemas": [
        {"id": "A1", "instr": 'Answer with ONLY a JSON object {"answer": <integer>}.', "render": lambda g: json.dumps({"answer": int(g)})},
        {"id": "A2", "instr": 'Answer with ONLY a JSON object {"result": <integer>, "unit": "<unit>"}.', "render": lambda g: json.dumps({"result": int(g), "unit": "units"})},
        {"id": "A3", "instr": 'Answer with ONLY a JSON object {"final_answer": <integer>, "confidence": "high" or "low"}.', "render": lambda g: json.dumps({"final_answer": int(g), "confidence": "high"})},
        {"id": "A4", "instr": "Answer with ONLY <answer>N</answer> where N is the integer result.", "render": lambda g: f"<answer>{int(g)}</answer>"},
    ],
}

NUM_RE = re.compile(r"\b\d[\d,]*(?:\.\d+)?\b")

def h(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)

def q_numbers(q):
    return [m.group(0) for m in NUM_RE.finditer(q)]

def intish(s):
    try:
        return float(s.replace(",", "")) == int(float(s.replace(",", "")))
    except Exception:
        return False

def base_filter(it):
    """CONTRACT_DATA 1.1: single numeric int answer, <=240 words, parsed steps."""
    if not it.get("steps"):
        return False
    if not intish(it["final"]):
        return False
    if len(it["question"].split()) > 240:
        return False
    return True

def deletable_operand(it):
    """A number used in step-1 computation that appears exactly once in the question."""
    q = it["question"]
    for n in it["steps"][0]["nums"]:
        n = n.lstrip("-")
        if len(re.findall(r"\b" + re.escape(n) + r"\b", q)) == 1 and float(n) != 0:
            return n
    return None

def qty_hint(q, num):
    if re.search(r"\$" + re.escape(num) + r"\b", q):
        return "the dollar amount"
    m = re.search(r"\b" + re.escape(num) + r"\b\s+([A-Za-z]+)", q)
    return f"the number of {m.group(1)}" if m else "one required quantity"

def delete_num(q, num):
    """Grammar-aware deletion: '$N' -> 'an unspecified amount', else 'N' -> 'some'."""
    if re.search(r"\$" + re.escape(num) + r"\b", q):
        return re.sub(r"\$" + re.escape(num) + r"\b", "an unspecified amount", q, count=1)
    return re.sub(r"\b" + re.escape(num) + r"\b", "some", q, count=1)

def first_name(q):
    m = re.match(r"([A-Z][a-z]+)", q)
    return m.group(1) if m else "Someone"

def wrong_value(it, salt=""):
    gold = int(float(it["final"]))
    kind = h(it["id"] + salt) % 4
    if kind == 0: w = gold + 1
    elif kind == 1: w = max(gold - 1, 0) if gold != 1 else gold + 2
    elif kind == 2: w = gold * 10
    else:
        w = int(float(it["steps"][-2]["result"])) if len(it["steps"]) >= 2 and intish(it["steps"][-2]["result"]) else gold + 3
    if w == gold: w = gold + 3
    return w

def distractor_k(q):
    used = {int(float(n.replace(",", ""))) for n in q_numbers(q) if intish(n)}
    for k in (13, 7, 23, 31, 17):
        if k not in used:
            return k
    return 101

def paraphrase_v0(q):
    """Rule-based v0: front the final question sentence + connector swaps. Answer-preserving
    by construction (numbers and facts untouched). Flagged WEAK_V0 in audit."""
    parts = re.split(r"(?<=[.!?])\s+", q.strip())
    if len(parts) >= 2 and parts[-1].endswith("?"):
        p = parts[-1] + " Here is the situation: " + " ".join(parts[:-1])
    else:
        p = "Consider the following. " + q
    # grammar-safe swaps only (question-word rewrites break fronted questions)
    swaps = [(" altogether", " in total"), (" every day", " each day"), (" per ", " for each ")]
    for a, b in swaps:
        p = p.replace(a, b, 1)
    return p

# --------------------------- eval prototypes (GEN B) -------------------------------
def build_eval(test_items, n_fam=50):
    rows, fams = [], 0
    for it in test_items:
        if fams >= n_fam:
            break
        if not base_filter(it):
            continue
        dele = deletable_operand(it)
        if dele is None:
            continue  # need all 7 conditions supported
        fid = it["id"]
        gold = str(int(float(it["final"])))
        q = it["question"].strip()
        base = dict(family_id=fid, source_id=fid, source_split="test",
                    generator_id="B", generator_version=GEN_VER, gold=gold, domain="reasoning")
        wv = wrong_value(it)
        name = first_name(q)
        k = distractor_k(q)
        dis_t = GEN_B["distractor"][h(fid) % len(GEN_B["distractor"])].format(name=name, k=k)
        parts = re.split(r"(?<=[.!?])\s+", q)
        q_dis = " ".join(parts[:-1] + [dis_t, parts[-1]]) if len(parts) >= 2 else q + " " + dis_t
        q_insuf = delete_num(q, dele)
        sch = GEN_B["format_schemas"][h(fid) % 2]
        cond = {
            "original": dict(prompt=q),
            "paraphrase": dict(prompt=paraphrase_v0(q), note="WEAK_V0 rule-based"),
            "distractor": dict(prompt=q_dis, meta={"distractor_k": k}),
            "wrong_candidate": dict(prompt=q + "\n\n" + GEN_B["wrong_candidate"].format(cand=wv), meta={"cand": wv}),
            "correct_candidate": dict(prompt=q + "\n\n" + GEN_B["correct_candidate"].format(cand=gold), meta={"cand": int(gold)}),
            "insufficient": dict(prompt=q_insuf, meta={"deleted": dele, "qty": qty_hint(q, dele)}, gold_behavior="abstain"),
            "format": dict(prompt=q + "\n\n" + sch["instr"], meta={"schema": sch["id"], "check": sch["check"]}),
        }
        for cname, c in cond.items():
            r = dict(base); r.update(condition=cname, template_id=c.get("meta", {}).get("schema", "-"),
                                     prompt=c["prompt"], meta=c.get("meta", {}),
                                     gold_behavior=c.get("gold_behavior", "answer"))
            if c.get("note"): r["note"] = c["note"]
            rows.append(r)
        fams += 1
    return rows, fams

# --------------------------- train prototypes (GEN A) ------------------------------
def _reason(it):
    return it["reasoning"].strip()

def build_train(train_items, per_comp=200):
    pool = [it for it in train_items if base_filter(it)]
    RNG.shuffle(pool)
    rows = []
    idx = 0

    def take():
        nonlocal idx
        it = pool[idx]; idx += 1
        return it

    # selective_revision: 100 keep/fix pairs (same family both rows)
    made = 0
    while made < per_comp:
        it = take()
        gold = str(int(float(it["final"])))
        q = it["question"].strip()
        wv = wrong_value(it, "rev")
        common = dict(family_id=it["id"], source_id=it["id"], source_split="train",
                      generator_id="A", generator_version=GEN_VER, component="selective_revision", domain="reasoning")
        rows.append(dict(common, subtype="keep",
                         prompt=GEN_A["revise_prompt"].format(cand=gold, hint="worked through the steps", q=q),
                         target=GEN_A["revise_keep"].format(gold=gold)))
        rows.append(dict(common, subtype="fix",
                         prompt=GEN_A["revise_prompt"].format(cand=wv, hint="worked through the steps", q=q),
                         target=GEN_A["revise_fix"].format(reason=_reason(it), gold=gold)))
        made += 2

    # evidence_robustness: 3 subtypes round-robin; need a well-formed binary expr
    made = 0
    while made < per_comp:
        it = take()
        st = next((s for s in it["steps"] if re.search(r"\d\s*[\+\-\*\/x]\s*\d", s["expr"])), None)
        if st is None:
            continue  # degenerate parsed exprs (e.g. '+11') make nonsense notes
        gold = str(int(float(it["final"])))
        q = it["question"].strip()
        bad = str(int(float(st["result"])) + (1 + h(it["id"]) % 3)) if intish(st["result"]) else "99"
        sub = made % 3
        common = dict(family_id=it["id"], source_id=it["id"], source_split="train",
                      generator_id="A", generator_version=GEN_VER, component="evidence_robustness", domain="reasoning")
        if sub == 0:
            tmpl = GEN_A["evid_irrelevant"][h(it["id"]) % 2]
            inj = tmpl.format(name=first_name(q), k=distractor_k(q))
            tgt = GEN_A["evid_target_ignore"].format(reason=_reason(it), gold=gold)
            stype = "irrelevant"
        elif sub == 1:
            inj = GEN_A["evid_wrong_step"].format(expr=st["expr"], bad=bad)
            tgt = GEN_A["evid_target_refute"].format(expr=st["expr"], good=st["result"], bad=bad,
                                                    reason=_reason(it), gold=gold)
            stype = "wrong_step"
        else:
            inj = GEN_A["evid_conflict"].format(expr=st["expr"], good=st["result"], bad=bad)
            tgt = GEN_A["evid_target_conflict"].format(expr=st["expr"], good=st["result"],
                                                      reason=_reason(it), gold=gold)
            stype = "conflict"
        rows.append(dict(common, subtype=stype, prompt=q + "\n\n" + inj, target=tgt))
        made += 1

    # answerability: 100 sufficient/insufficient pairs
    made = 0
    while made < per_comp:
        it = take()
        dele = deletable_operand(it)
        if dele is None:
            continue
        gold = str(int(float(it["final"])))
        q = it["question"].strip()
        common = dict(family_id=it["id"], source_id=it["id"], source_split="train",
                      generator_id="A", generator_version=GEN_VER, component="answerability", domain="reasoning")
        rows.append(dict(common, subtype="sufficient", prompt=q,
                         target=GEN_A["answer_full"].format(reason=_reason(it), gold=gold)))
        rows.append(dict(common, subtype="insufficient",
                         prompt=delete_num(q, dele),
                         target=GEN_A["abstain"].format(qty=qty_hint(q, dele))))
        made += 2

    # format: 4 schemas round-robin
    made = 0
    while made < per_comp:
        it = take()
        gold = str(int(float(it["final"])))
        q = it["question"].strip()
        sch = GEN_A["format_schemas"][made % 4]
        rows.append(dict(family_id=it["id"], source_id=it["id"], source_split="train",
                         generator_id="A", generator_version=GEN_VER, component="format", domain="reasoning",
                         subtype=sch["id"], prompt=q + "\n\n" + sch["instr"], target=sch["render"](gold)))
        made += 1
    return rows

# --------------------------- auto-verification -------------------------------------
def verify(train_rows, eval_rows):
    errs = []
    ev_fams = {r["family_id"] for r in eval_rows}
    for r in train_rows:
        if r["family_id"] in ev_fams:
            errs.append(("split_leak", r["family_id"]))
        c, t = r["component"], r["target"]
        if c == "selective_revision":
            g = re.search(r"Final answer: (\-?\d+)", t)
            if not g: errs.append(("rev_no_final", r["family_id"]))
        if c == "answerability" and r["subtype"] == "insufficient":
            if NUM_RE.search(t): errs.append(("abstain_has_number", r["family_id"]))
        if c == "format":
            if r["subtype"].startswith("A") and r["subtype"] != "A4":
                try: json.loads(t)
                except Exception: errs.append(("format_bad_json", r["family_id"]))
    for r in eval_rows:
        if r["condition"] == "wrong_candidate" and str(r["meta"]["cand"]) == r["gold"]:
            errs.append(("wrong_eq_gold", r["family_id"]))
        if r["condition"] == "insufficient" and r["meta"]["deleted"] in q_numbers(r["prompt"]):
            errs.append(("delete_failed", r["family_id"]))
    return errs

def main():
    cache = json.load(open(ROOT / "data_v4/gsm8k_cache.json"))
    eval_rows, fams = build_eval(cache["test"], 50)
    train_rows = build_train(cache["train"], 200)
    errs = verify(train_rows, eval_rows)
    (OUT / "eval_proto.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in eval_rows) + "\n")
    (OUT / "train_proto.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in train_rows) + "\n")
    from collections import Counter
    stats = {
        "eval_families": fams,
        "eval_rows": len(eval_rows),
        "eval_by_condition": dict(Counter(r["condition"] for r in eval_rows)),
        "train_rows": len(train_rows),
        "train_by_component": dict(Counter(r["component"] for r in train_rows)),
        "train_target_len_tokens_approx": {
            comp: round(sum(len(r["target"].split()) for r in train_rows if r["component"] == comp)
                        / max(1, sum(1 for r in train_rows if r["component"] == comp)), 1)
            for comp in ("selective_revision", "evidence_robustness", "answerability", "format")},
        "verify_errors": errs,
        "generator_version": GEN_VER,
    }
    (OUT / "build_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
