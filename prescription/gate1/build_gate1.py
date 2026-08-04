#!/usr/bin/env python3
"""Gate-1 prototype builder v1.1 (lawv1, C-22 rework).

C-22 fixes vs v1.0:
  1 insufficient: typed variable deletion (percentage/ratio/time/price/fraction/count),
    per-item {removed_variable, variable_type, dependency_path, why_unanswerable};
  2 distractor: topic-adjacent, NO irrelevance markers, varied entities/numbers;
  3 selective revision -> full-attempt revision (candidate reasoning provided; Option B);
  4 wrong-candidate error taxonomy (arithmetic_slip / operator_error / dropped_step /
    off_by_one), proportions recorded, candidate values derived from a concrete wrong process;
  6 format schemas: no fake semantic fields (unit/confidence removed; calculation is real);
  7 target reasoning cleaned: every parsable "a op b = c" is executed; malformed exprs drop item.

Outputs: eval_proto.jsonl (50 fam x 7 cond, GSM8K TEST, gen B),
         train_proto.jsonl (4 comp x 200, GSM8K TRAIN, gen A), build_stats.json.
Deterministic (seed 20260805). Paraphrase remains WEAK_V0 (declared; upgrade pending).
"""
import json, re, random, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
GEN_VER = "gate1-v1.1"
SEED = 20260805

NUM_TOKEN = re.compile(r"\$?\d[\d,]*(?:\.\d+)?%?")
STOPNAMES = {"The", "A", "An", "Every", "Each", "If", "On", "In", "At", "There", "It",
             "When", "What", "How", "His", "Her", "Their", "They", "We", "You", "Two",
             "One", "Some", "For", "During", "After", "Before", "While", "To", "Of"}
NAME_POOL = ["Maya", "Omar", "Lena", "Ravi", "Tessa", "Hugo", "Iris", "Felix"]
ITEM_POOL = ["plates", "napkins", "stickers", "envelopes", "postcards", "batteries",
             "candles", "notebooks"]

def h(s):
    return int(hashlib.md5(s.encode()).hexdigest(), 16)

def rng_for(fid, tag=""):
    return random.Random(h(fid + tag) % (2**31))

def intish(s):
    try:
        return float(str(s).replace(",", "")) == int(float(str(s).replace(",", "")))
    except Exception:
        return False

def numval(tok):
    t = tok.strip("$%").replace(",", "")
    try:
        return float(t)
    except Exception:
        return None

# ------------------------------ reasoning hygiene (C-22 #7) ------------------------
_N = r"-?\d[\d,]*(?:\.\d+)?"
FULL_EXPR = re.compile(
    rf"(?<![\d\.,\)])((?:{_N})(?:\s*[\+\-\*\/x]\s*\$?{_N})+)\s*=\s*\$?({_N})")
MALFORMED = re.compile(r"[\+\-\*\/x]\s*=|=\s*[\+\-\*\/x]|\d\s*[\*\/x]\s*(?![\d\s\.\(\$\-])")

def reasoning_clean(text):
    """True iff no malformed expr and every full 'a op b [op c...] = r' verifies (2% tol)."""
    if MALFORMED.search(text):
        return False
    for expr, res in FULL_EXPR.findall(text):
        e = expr.replace(",", "").replace("$", "").replace("x", "*")
        if not re.fullmatch(r"[\d\s\.\+\-\*\/]+", e):
            return False
        try:
            got = eval(e)
            fc = float(res.replace(",", ""))
        except Exception:
            return False
        if abs(got - fc) > max(0.02 * abs(fc), 1e-6):
            return False
    return True

def base_filter(it):
    if not it.get("steps"):
        return False
    if not intish(it["final"]):
        return False
    if len(it["question"].split()) > 240:
        return False
    if not reasoning_clean(it["reasoning"]):
        return False
    return True

def first_name(q, fid):
    m = re.match(r"([A-Z][a-z]{2,})\b", q)
    if m and m.group(1) not in STOPNAMES:
        return m.group(1)
    return NAME_POOL[h(fid) % len(NAME_POOL)]

# ------------------------------ typed deletion (C-22 #1) ---------------------------
def find_tokens_for_value(q, val):
    """All full numeric surface tokens in q whose value == val."""
    out = []
    for m in NUM_TOKEN.finditer(q):
        if numval(m.group(0)) == val:
            out.append((m.start(), m.end(), m.group(0)))
    return out

def pluralize(w):
    if w.endswith("s"):
        return w
    if re.search(r"(ch|sh|x|ss)$", w):
        return w + "es"
    if re.search(r"[^aeiou]y$", w):
        return w[:-1] + "ies"
    return w + "s"

def classify_token(q, s, e, tok):
    """(variable_type, replacement) from surface + context."""
    after = q[e:e + 12]
    if tok.endswith("%"):
        return "percentage", "an unspecified percentage", e
    if tok.startswith("$"):
        return "price", "an unspecified price", e
    if re.match(r"\s*(dollars|cents|euros)", after):
        return "price", "an unspecified amount", e
    if re.match(r":\d", after) or re.search(r"\d:$", q[max(0, s - 3):s] + tok):
        return "ratio_or_time", None, e          # unhandled: skip item (ratios/times)
    if re.match(r"\s*/\s*\d", after) or q[max(0, s - 2):s].strip().endswith("/"):
        return "fraction", None, e               # unhandled: skip item
    if re.match(r"\s*(AM|PM|a\.m\.|p\.m\.|o'clock)", after, re.I):
        return "time", None, e                   # unhandled: skip item
    m = re.match(r"(\s+)([A-Za-z]+)(\s+[A-Za-z]+)?", after)
    if m:
        w1 = m.group(2)
        w2 = m.group(3).strip() if m.group(3) else None
        ADJ = {"available", "more", "fewer", "extra", "additional", "other", "new",
               "total", "different", "whole", "full", "small", "large", "big"}
        noun, consumed = (w2, (m.group(1) + w1 + m.group(3))) if (w1.lower() in ADJ and w2) \
            else (w1, m.group(1) + w1)
        if noun and noun.lower() not in {"times", "of", "and", "is", "are", "was", "were", "the", "a", "an"}:
            # consume the noun token(s) so "30 lollipops" -> "an unspecified number of lollipops"
            return "count", f"an unspecified number of {pluralize(noun)}", e + len(consumed)
    return "count", "an unspecified quantity", e

def typed_delete(it):
    """Pick a necessary, uniquely-surfaced, typed-handleable operand; delete it.
    Returns (new_q, meta) or None."""
    q = it["question"]
    qvals = [numval(t) for t in NUM_TOKEN.findall(q)]
    for n_raw in it["steps"][0]["nums"]:
        val = numval(n_raw.lstrip("-"))
        if val in (None, 0, 1):
            continue  # val==1 is often implied by grammar ("an iPhone") -> recoverable
        toks = find_tokens_for_value(q, val)
        if len(toks) != 1:
            continue                       # ambiguous surface -> skip operand
        if qvals.count(val) != 1:
            continue                       # value appears elsewhere -> maybe derivable
        s, e, tok = toks[0]
        vtype, repl, e2 = classify_token(q, s, e, tok)
        if repl is None:
            continue                       # typed-unhandled context -> try next operand
        new_q = q[:s] + repl + q[e2:]
        dep_steps = [st["expr"] for st in it["steps"] if str(int(val)) in
                     [x.lstrip("-") for x in st["nums"]] or n_raw in st["nums"]]
        meta = {
            "removed_variable": tok,
            "variable_type": vtype,
            "replacement": repl,
            "dependency_path": " -> ".join(dep_steps + ["final"]) if dep_steps else it["steps"][0]["expr"] + " -> final",
            "why_unanswerable": (f"'{tok}' ({vtype}) is a direct input of step computation "
                                 f"{dep_steps[0] if dep_steps else it['steps'][0]['expr']}; its value appears exactly once "
                                 f"in the problem and equals no other stated quantity, so it cannot be recovered from the remaining text."),
        }
        return new_q, meta
    return None

def qty_phrase(meta):
    if meta["variable_type"] == "count":
        m = re.match(r"an unspecified number of (.+)", "")
    rep = {"percentage": "the percentage", "price": "the price",
           "count": "the required count", }.get(meta["variable_type"], "one required quantity")
    return rep

# ------------------------------ wrong-candidate taxonomy (C-22 #4/#5) --------------
def wrong_process(it, rng):
    """Return (error_type, wrong_final, wrong_steps) — a concrete wrong derivation.
    wrong_steps = list of 'expr = value' strings representing the candidate attempt."""
    steps = it["steps"]
    gold = int(float(it["final"]))
    chain = [f"{s['expr']} = {s['result']}" for s in steps]
    choices = []
    # operator_error on last step
    last = steps[-1]
    m = re.match(r"^(-?[\d\.,]+)([\+\-\*\/])(-?[\d\.,]+)$", last["expr"].replace(" ", ""))
    if m:
        a, op, b = float(m.group(1).replace(",", "")), m.group(2), float(m.group(3).replace(",", ""))
        swap = {"+": "-", "-": "+", "*": "/", "/": "*"}[op]
        try:
            v = {"+": a + b, "-": a - b, "*": a * b, "/": a / b}[swap]
            if v == int(v) and int(v) != gold and abs(v) < 1e7 and v >= 0:
                ws = chain[:-1] + [f"{m.group(1)}{swap}{m.group(3)} = {int(v)}"]
                choices.append(("operator_error", int(v), ws))
        except ZeroDivisionError:
            pass
    # dropped_step: answer = penultimate result
    if len(steps) >= 2 and intish(steps[-2]["result"]) and int(float(steps[-2]["result"])) != gold:
        choices.append(("dropped_step", int(float(steps[-2]["result"])), chain[:-1]))
    # arithmetic_slip on last step result (small delta)
    d = rng.choice([2, 3, 4])
    v = gold + rng.choice([-1, 1]) * d
    if v >= 0:
        ws = chain[:-1] + [f"{last['expr']} = {v}"]
        choices.append(("arithmetic_slip", v, ws))
    # off_by_one
    v = gold + rng.choice([-1, 1])
    if v >= 0:
        ws = chain[:-1] + [f"{last['expr']} = {v}"]
        choices.append(("off_by_one", v, ws))
    return rng.choice(choices)

def render_attempt(wrong_steps, final):
    lines = [f"Step {i+1}: {s}." for i, s in enumerate(wrong_steps)]
    return "\n".join(lines) + f"\nCandidate final answer: {final}"

# ------------------------------ generator banks ------------------------------------
GEN_B = {
    "distractor": [
        "That same day, the store also sold {k} {item} for ${p} each.",
        "{name2} keeps a collection of {k} {item} at home.",
        "Earlier that week, {name2} counted {k} {item} in the storeroom.",
        "The shop next door displayed {k} {item} priced at ${p} apiece.",
    ],
    "candidate": "A previous attempt at this problem concluded the answer is {cand}. Review the problem and give your own final answer.",
    "format_schemas": [
        {"id": "B1", "instr": 'Respond with ONLY a JSON object of the form {"solution": {"value": <integer>}} and nothing else.',
         "check": "json_nested_solution_value"},
        {"id": "B2", "instr": "Respond with ONLY one line of the form ANSWER=<integer> and nothing else.",
         "check": "kv_answer_eq"},
    ],
}
GEN_A = {
    "revise_prompt": ("A previous attempt at this problem is shown below.\n\n{q}\n\n"
                      "Candidate attempt:\n{attempt}\n\n"
                      "Check the attempt. If it is correct, keep its answer; if not, correct only what is wrong."),
    "revise_keep": "Every step of the attempt checks out. The candidate answer is correct — keep it.\nFinal answer: {gold}",
    "revise_fix": "Step {i} of the attempt is wrong: {expr_good}. Correcting from that step:\n{fixtail}\nFinal answer: {gold}",
    "revise_fix_missing": "The attempt stops one step early — it never computes the final step {laststep}. Completing it:\n{laststep}\nFinal answer: {gold}",
    "evid_irrelevant": [
        "That afternoon the family also received a package of {k} {item}.",
        "A stall nearby was offering {k} {item} for ${p} each.",
    ],
    "evid_wrong_step": "Note: someone computed {expr} = {bad} while attempting this.",
    "evid_conflict": "Note A claims the intermediate result of {expr} is {good}. Note B claims it is {bad}.",
    "evid_target_refute": "The note's computation is wrong: {expr} = {good}, not {bad}. Solving independently:\n{reason}\nFinal answer: {gold}",
    "evid_target_conflict": "Note A matches the actual computation ({expr} = {good}); Note B does not. Solving:\n{reason}\nFinal answer: {gold}",
    "evid_target_ignore": "The sentence about the {item} plays no role in what is asked. Solving:\n{reason}\nFinal answer: {gold}",
    "abstain": "The problem leaves {what} unspecified, so the answer cannot be determined from the given information.",
    "answer_full": "{reason}\nFinal answer: {gold}",
    "format_schemas": [
        {"id": "A1", "instr": 'Answer with ONLY a JSON object {"answer": <integer>}.',
         "render": lambda it, g: json.dumps({"answer": int(g)})},
        {"id": "A2", "instr": 'Answer with ONLY a JSON object {"calculation": "<the final arithmetic step>", "answer": <integer>}.',
         "render": lambda it, g: json.dumps({"calculation": f"{it['steps'][-1]['expr']} = {it['steps'][-1]['result']}", "answer": int(g)})},
        {"id": "A3", "instr": "Answer with ONLY <answer>N</answer> where N is the integer result.",
         "render": lambda it, g: f"<answer>{int(g)}</answer>"},
        {"id": "A4", "instr": 'Answer with ONLY one line of the form "answer: N".',
         "render": lambda it, g: f"answer: {int(g)}"},
    ],
}

PRONOUN_RE = re.compile(r"\b(he|she|his|her|him|they|their|them)\b", re.I)

def pick_distractor(q, fid, bank, tag):
    rng = rng_for(fid, tag)
    if PRONOUN_RE.search(q):
        bank = [t for t in bank if "{name2}" not in t] or bank
    used = {numval(t) for t in NUM_TOKEN.findall(q)}
    ks = [k for k in range(3, 30) if float(k) not in used]
    ps = [p for p in range(2, 10) if float(p) not in used]
    k, p = rng.choice(ks), rng.choice(ps)
    name2 = rng.choice(NAME_POOL)
    item = rng.choice(ITEM_POOL)
    t = rng.choice(bank)
    return t.format(k=k, p=p, name2=name2, item=item), {"k": k, "item": item}

def paraphrase_v0(q):
    parts = re.split(r"(?<=[.!?])\s+", q.strip())
    if len(parts) >= 2 and parts[-1].endswith("?"):
        p = parts[-1] + " Here is the situation: " + " ".join(parts[:-1])
    else:
        p = "Consider the following. " + q
    for a, b in [(" altogether", " in total"), (" every day", " each day"), (" per ", " for each ")]:
        p = p.replace(a, b, 1)
    return p

# ------------------------------ eval build -----------------------------------------
def build_eval(test_items, n_fam=50):
    rows, fams, taxo = [], 0, {}
    for it in test_items:
        if fams >= n_fam:
            break
        if not base_filter(it):
            continue
        td = typed_delete(it)
        if td is None:
            continue
        fid, gold = it["id"], str(int(float(it["final"])))
        q = it["question"].strip()
        q_insuf, imeta = td
        rng = rng_for(fid, "wc")
        etype, wv, _ = wrong_process(it, rng)
        taxo[etype] = taxo.get(etype, 0) + 1
        dis, dmeta = pick_distractor(q, fid, GEN_B["distractor"], "dis")
        parts = re.split(r"(?<=[.!?])\s+", q)
        q_dis = " ".join(parts[:-1] + [dis, parts[-1]]) if len(parts) >= 2 else q + " " + dis
        sch = GEN_B["format_schemas"][h(fid) % 2]
        base = dict(family_id=fid, source_id=fid, source_split="test", generator_id="B",
                    generator_version=GEN_VER, gold=gold, domain="reasoning")
        conds = {
            "original": dict(prompt=q),
            "paraphrase": dict(prompt=paraphrase_v0(q), note="WEAK_V0 rule-based"),
            "distractor": dict(prompt=q_dis, meta=dmeta),
            "wrong_candidate": dict(prompt=q + "\n\n" + GEN_B["candidate"].format(cand=wv),
                                    meta={"cand": wv, "error_type": etype}),
            "correct_candidate": dict(prompt=q + "\n\n" + GEN_B["candidate"].format(cand=gold),
                                      meta={"cand": int(gold)}),
            "insufficient": dict(prompt=q_insuf, meta=imeta, gold_behavior="abstain"),
            "format": dict(prompt=q + "\n\n" + sch["instr"], meta={"schema": sch["id"], "check": sch["check"]}),
        }
        for cname, c in conds.items():
            r = dict(base)
            r.update(condition=cname, prompt=c["prompt"], meta=c.get("meta", {}),
                     gold_behavior=c.get("gold_behavior", "answer"),
                     template_id=c.get("meta", {}).get("schema", "-"))
            if c.get("note"):
                r["note"] = c["note"]
            rows.append(r)
        fams += 1
    return rows, fams, taxo

# ------------------------------ train build ----------------------------------------
def build_train(train_items, per_comp=200):
    pool = [it for it in train_items if base_filter(it)]
    random.Random(SEED).shuffle(pool)
    rows, taxo = [], {}
    idx = 0

    def take():
        nonlocal idx
        it = pool[idx]; idx += 1
        return it

    # selective_revision (Option B: full attempt) — 100 keep/fix pairs
    made = 0
    while made < per_comp:
        it = take()
        gold = str(int(float(it["final"])))
        q = it["question"].strip()
        chain = [f"{s['expr']} = {s['result']}" for s in it["steps"]]
        rng = rng_for(it["id"], "rev")
        etype, wv, wsteps = wrong_process(it, rng)
        taxo[etype] = taxo.get(etype, 0) + 1
        common = dict(family_id=it["id"], source_id=it["id"], source_split="train", generator_id="A",
                      generator_version=GEN_VER, component="selective_revision", domain="reasoning")
        rows.append(dict(common, subtype="keep",
                         prompt=GEN_A["revise_prompt"].format(q=q, attempt=render_attempt(chain, gold)),
                         target=GEN_A["revise_keep"].format(gold=gold)))
        # locate first wrong step index for the fix target
        wrong_i = next((i for i, (a, b) in enumerate(zip(chain, wsteps)) if a != b), len(wsteps) - 1) \
            if len(wsteps) == len(chain) else len(wsteps)
        fixtail = "\n".join(chain[min(wrong_i, len(chain) - 1):])
        expr_good = chain[min(wrong_i, len(chain) - 1)]
        if etype == "dropped_step":
            fix_tgt = GEN_A["revise_fix_missing"].format(laststep=chain[-1], gold=gold)
        else:
            fix_tgt = GEN_A["revise_fix"].format(i=min(wrong_i, len(chain) - 1) + 1,
                                                 expr_good=expr_good, fixtail=fixtail, gold=gold)
        rows.append(dict(common, subtype="fix", meta={"error_type": etype},
                         prompt=GEN_A["revise_prompt"].format(q=q, attempt=render_attempt(wsteps, wv)),
                         target=fix_tgt))
        made += 2

    # evidence_robustness — 3 subtypes round-robin, neutral injections
    made = 0
    while made < per_comp:
        it = take()
        st = next((s for s in it["steps"] if re.search(r"\d\s*[\+\-\*\/x]\s*\d", s["expr"])), None)
        if st is None:
            continue
        gold = str(int(float(it["final"])))
        q = it["question"].strip()
        bad = str(int(float(st["result"])) + (1 + h(it["id"]) % 3)) if intish(st["result"]) else "99"
        sub = made % 3
        common = dict(family_id=it["id"], source_id=it["id"], source_split="train", generator_id="A",
                      generator_version=GEN_VER, component="evidence_robustness", domain="reasoning")
        if sub == 0:
            inj, dmeta = pick_distractor(q, it["id"], GEN_A["evid_irrelevant"], "evd")
            tgt = GEN_A["evid_target_ignore"].format(item=dmeta["item"], reason=it["reasoning"].strip(), gold=gold)
            stype = "irrelevant"
        elif sub == 1:
            inj = GEN_A["evid_wrong_step"].format(expr=st["expr"], bad=bad)
            tgt = GEN_A["evid_target_refute"].format(expr=st["expr"], good=st["result"], bad=bad,
                                                    reason=it["reasoning"].strip(), gold=gold)
            stype = "wrong_step"
        else:
            inj = GEN_A["evid_conflict"].format(expr=st["expr"], good=st["result"], bad=bad)
            tgt = GEN_A["evid_target_conflict"].format(expr=st["expr"], good=st["result"],
                                                      reason=it["reasoning"].strip(), gold=gold)
            stype = "conflict"
        rows.append(dict(common, subtype=stype, prompt=q + "\n\n" + inj, target=tgt))
        made += 1

    # answerability — 100 sufficient/insufficient pairs, typed deletion
    made = 0
    while made < per_comp:
        it = take()
        td = typed_delete(it)
        if td is None:
            continue
        gold = str(int(float(it["final"])))
        q = it["question"].strip()
        new_q, imeta = td
        what = "the " + imeta["replacement"].replace("an unspecified ", "", 1)
        common = dict(family_id=it["id"], source_id=it["id"], source_split="train", generator_id="A",
                      generator_version=GEN_VER, component="answerability", domain="reasoning")
        rows.append(dict(common, subtype="sufficient", prompt=q,
                         target=GEN_A["answer_full"].format(reason=it["reasoning"].strip(), gold=gold)))
        rows.append(dict(common, subtype="insufficient", prompt=new_q, meta=imeta,
                         target=GEN_A["abstain"].format(what=what)))
        made += 2

    # format — 4 schemas round-robin (no fake semantic fields)
    made = 0
    while made < per_comp:
        it = take()
        gold = str(int(float(it["final"])))
        q = it["question"].strip()
        sch = GEN_A["format_schemas"][made % 4]
        rows.append(dict(family_id=it["id"], source_id=it["id"], source_split="train", generator_id="A",
                         generator_version=GEN_VER, component="format", domain="reasoning",
                         subtype=sch["id"], prompt=q + "\n\n" + sch["instr"], target=sch["render"](it, gold)))
        made += 1
    return rows, taxo

# ------------------------------ verification ---------------------------------------
BANNED_MARKERS = ["unrelated", "irrelevant", "nothing to do", "as an aside", "separately,"]

def verify(train_rows, eval_rows):
    errs = []
    ev_fams = {r["family_id"] for r in eval_rows}
    for r in eval_rows:
        p = r["prompt"].lower()
        if r["condition"] == "distractor" and any(b in p for b in BANNED_MARKERS):
            errs.append(("distractor_marker", r["family_id"]))
        if r["condition"] == "wrong_candidate" and str(r["meta"]["cand"]) == r["gold"]:
            errs.append(("wrong_eq_gold", r["family_id"]))
        if r["condition"] == "insufficient":
            if "some%" in p or ".00" in r["prompt"].split("unspecified")[-1][:6] or "some:" in p or "some/" in p:
                errs.append(("typed_delete_residue", r["family_id"]))
            for k in ("removed_variable", "variable_type", "dependency_path", "why_unanswerable"):
                if k not in r["meta"]:
                    errs.append(("insuf_meta_missing", r["family_id"]))
    for r in train_rows:
        if r["family_id"] in ev_fams:
            errs.append(("split_leak", r["family_id"]))
        t = r.get("target", "")
        if r["component"] in ("selective_revision", "evidence_robustness") and not reasoning_clean(t):
            errs.append(("target_expr_bad", r["family_id"], r["component"]))
        if r["component"] == "evidence_robustness" and r["subtype"] == "irrelevant" \
           and any(b in r["prompt"].lower() for b in BANNED_MARKERS):
            errs.append(("evid_marker", r["family_id"]))
        if r["component"] == "answerability" and r["subtype"] == "insufficient" and NUM_TOKEN.search(t):
            errs.append(("abstain_has_number", r["family_id"]))
        if r["component"] == "selective_revision":
            if not re.search(r"Final answer: -?\d+", t):
                errs.append(("rev_no_final", r["family_id"]))
            if r["subtype"] == "fix" and "Candidate attempt:" not in r["prompt"]:
                errs.append(("rev_no_attempt", r["family_id"]))
    return errs

def main():
    cache = json.load(open(ROOT / "data_v4/gsm8k_cache.json"))
    eval_rows, fams, etaxo = build_eval(cache["test"], 50)
    train_rows, ttaxo = build_train(cache["train"], 200)
    errs = verify(train_rows, eval_rows)
    (OUT / "eval_proto.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in eval_rows) + "\n")
    (OUT / "train_proto.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in train_rows) + "\n")
    from collections import Counter
    stats = {
        "generator_version": GEN_VER,
        "eval_families": fams, "eval_rows": len(eval_rows),
        "eval_by_condition": dict(Counter(r["condition"] for r in eval_rows)),
        "eval_wrong_candidate_taxonomy": etaxo,
        "train_rows": len(train_rows),
        "train_by_component": dict(Counter(r["component"] for r in train_rows)),
        "train_revision_error_taxonomy": ttaxo,
        "insufficient_variable_types": dict(Counter(
            r["meta"]["variable_type"] for r in eval_rows + train_rows
            if r.get("meta", {}).get("variable_type"))),
        "note_word_counts_are_not_tokens": "token stats produced separately with Qwen tokenizer (token_stats.json)",
        "verify_errors": errs,
    }
    (OUT / "build_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
