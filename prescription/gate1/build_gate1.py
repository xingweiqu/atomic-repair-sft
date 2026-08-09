#!/usr/bin/env python3
"""Gate-1 prototype builder v1.2 (lawv1, C-23 rework).

C-23 fixes vs v1.1:
  #2 main_family_pool: 50 families RANDOMLY sampled (seed) from base-filtered TEST;
     all conditions build on the main pool; insufficient only on the reliable subset
     (its builder no longer filters the whole eval set);
  #1 insufficient hardened: number-WORD leak check, algebraic-recoverability check
     (<=2-op compositions of remaining numbers), article/hyphen/colon guards,
     irregular plurals, compound nouns, unit-count words -> skip; grammar residue scan;
     ALL surviving items go to full manual audit (INSUFFICIENT_AUDIT.md);
  #3/#4 candidates: decision-contract probes (DECISION=KEEP|CORRECT + FINAL_ANSWER=)
     in two strengths — light (answer only) and full plausible attempt (main stress);
     natural-language variants kept as secondary generalization probes (n=20);
  #8 paraphrase: generator B = human/CC rewrite loaded from paraphrase_overrides.json
     (answer-preserving, number-multiset checked); no rule-based fallback in eval.

Outputs: eval_proto.jsonl / train_proto.jsonl / build_stats.json / main_pool.json.
Deterministic (SEED). Train side unchanged from v1.1 except hardened typed_delete.
"""
import json, re, random, hashlib, itertools
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
GEN_VER = "gate1-v1.2"
SEED = 20260812

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

# ------------------------------ reasoning hygiene ----------------------------------
_N = r"-?\d[\d,]*(?:\.\d+)?"
FULL_EXPR = re.compile(
    rf"(?<![\d\.,\)])((?:{_N})(?:\s*[\+\-\*\/x]\s*\$?{_N})+)\s*=\s*\$?({_N})")
MALFORMED = re.compile(r"[\+\-\*\/x]\s*=|=\s*[\+\-\*\/x]|\d\s*[\*\/x]\s*(?![\d\s\.\(\$\-])")

def reasoning_clean(text):
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

# ------------------------------ number words ---------------------------------------
_ONES = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
         "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen",
         "seventeen", "eighteen", "nineteen"]
_TENS = {20: "twenty", 30: "thirty", 40: "forty", 50: "fifty", 60: "sixty",
         70: "seventy", 80: "eighty", 90: "ninety"}
_EXTRA = {2: ["twice", "double", "couple"], 3: ["thrice", "triple"], 12: ["dozen"],
          4: ["quadruple"], 100: ["hundred"], 1000: ["thousand"]}

def numwords(val):
    """English word forms of an integer value (<=999), for leak checking."""
    out = []
    if val == int(val):
        v = int(val)
        if 0 <= v < 20:
            out.append(_ONES[v])
        elif v in _TENS:
            out.append(_TENS[v])
        elif 20 < v < 100 and (v // 10) * 10 in _TENS:
            out.append(f"{_TENS[(v//10)*10]}-{_ONES[v%10]}")
        out += _EXTRA.get(v, [])
    return out

def word_leak(q, val):
    ql = q.lower()
    return any(re.search(r"\b" + re.escape(w) + r"s?\b", ql) for w in numwords(val))

def derivable(others, target, tol=1e-6):
    """target reachable from <=3 of the remaining stated numbers via <=2 ops?"""
    vals = [v for v in others if v is not None]
    def ops(a, b):
        r = [a + b, a - b, b - a, a * b]
        if b: r.append(a / b)
        if a: r.append(b / a)
        return r
    lvl1 = set()
    for a, b in itertools.combinations(vals, 2):
        lvl1.update(ops(a, b))
    if any(abs(x - target) <= tol for x in lvl1):
        return True
    for x in list(lvl1):
        for c in vals:
            if any(abs(y - target) <= tol for y in ops(x, c)):
                return True
    return False

# ------------------------------ typed deletion v2 ----------------------------------
IRREG_PLURAL = {"foot": "feet", "tooth": "teeth", "goose": "geese", "mouse": "mice",
                "man": "men", "woman": "women", "child": "children", "person": "people"}
ALREADY_PLURAL = {"feet", "teeth", "geese", "mice", "men", "women", "children",
                  "people", "sheep", "fish", "deer", "series", "species"}
NOUN_BLACKLIST = {"times", "of", "and", "is", "are", "was", "were", "the", "a", "an",
                  "than", "then", "as", "to", "at", "in", "on", "per", "each", "every",
                  "or", "more", "less", "by", "for", "with", "from",
                  # verbs that follow quantities ("6 needs vegan meals" bug class)
                  "needs", "wants", "has", "have", "gets", "makes", "takes", "uses",
                  "buys", "sells", "eats", "spends", "gives", "goes", "runs", "pays",
                  "costs", "earns", "works", "said", "says", "need", "want", "get",
                  "make", "take", "use", "buy", "sell", "eat", "spend", "give",
                  "go", "run", "pay", "cost", "earn", "work", "say", "deliver",
                  "now", "nows", "how", "hows", "seasonal", "monthly"}
UNIT_COUNT = {"dozen", "dozens", "hundred", "hundreds", "thousand", "thousands",
              "pair", "pairs", "percent", "half", "gb", "mb", "kg", "km", "cm", "mph",
              "mg", "mgs", "ml", "oz", "lb", "lbs", "g", "ft", "sq", "sqft"}

def pluralize(w):
    lw = w.lower()
    if lw in ALREADY_PLURAL or w.endswith("s"):
        return w
    if lw in IRREG_PLURAL:
        return IRREG_PLURAL[lw]
    if re.search(r"(ch|sh|x|ss)$", w):
        return w + "es"
    if re.search(r"[^aeiou]y$", w):
        return w[:-1] + "ies"
    return w + "s"

def find_tokens_for_value(q, val):
    out = []
    for m in NUM_TOKEN.finditer(q):
        if numval(m.group(0)) == val:
            out.append((m.start(), m.end(), m.group(0)))
    return out

def classify_token(q, s, e, tok):
    """(variable_type, replacement, del_start, del_end) or type,None,.. to skip."""
    while tok and tok[-1] in ",.":                     # "$3," span bug: never eat punctuation
        tok = tok[:-1]; e -= 1
    before, after = q[max(0, s - 4):s], q[e:e + 48]
    if re.search(r"number of\s*$", q[:s], re.I):
        return "number_of_context", None, s, e         # "number of 26 patients" -> skip
    if "-" in q[max(0, s - 1):s] or after.startswith("-"):
        return "hyphen_compound", None, s, e          # "5-mile" -> skip
    if ":" in q[max(0, s - 2):s] or ":" in after[:2]:
        return "ratio_or_time", None, s, e            # either side of ':' -> skip
    if tok.endswith("%"):
        return "percentage", "an unspecified percentage", s, e
    art = re.search(r"\b([Aa]n?)\s+$", q[:s])
    if tok.startswith("$"):
        if art and re.match(r"\s*[A-Za-z]", after):
            return "price_attributive", None, s, e   # "an $11 sweater" -> skip
        return "price", "an unspecified amount", (art.start(1) if art else s), e
    if re.match(r"\s*(dollars|cents|euros)", after):
        return "price", "an unspecified amount of", s, e
    if re.match(r"\s*(AM|PM|a\.m\.|p\.m\.|o'clock)", after, re.I):
        return "time", None, s, e
    m = re.match(r"(\s+)([A-Za-z]+)(\s+[A-Za-z]+)?", after)
    if not m:
        return "count", None, s, e
    if m.group(2).lower() in ("more", "fewer", "less") and " than" in q[e:e + 60]:
        return "comparative", None, s, e          # "16 more silver dollars than" -> skip
    if re.match(r"\s+[A-Za-z]+,", after):
        return "comma_compound", None, s, e       # "10 blue, spotted fish" -> skip
    w1 = m.group(2)
    w2 = m.group(3).strip() if m.group(3) else None
    if q[e + len(m.group(1)) + len(w1): e + len(m.group(1)) + len(w1) + 1] == "-":
        return "noun_hyphen", None, s, e               # "5 T-shirts" -> skip
    if w1.lower() in UNIT_COUNT or (w2 and w2.lower() in UNIT_COUNT):
        return "unit_count", None, s, e               # "3 dozen donuts" -> skip
    ADJ = {"available", "more", "fewer", "extra", "additional", "other", "new",
           "total", "different", "whole", "full", "small", "large", "big"}
    if w1.lower() in NOUN_BLACKLIST and not (w2 and w2.lower() not in NOUN_BLACKLIST):
        return "count", None, s, e
    del_start = art.start(1) if art else s            # eat a preceding "a/an"
    if w2 and w2.endswith("s") and w1.lower() not in ADJ and w1.lower() not in NOUN_BLACKLIST:
        # plural compound: "5 apple pies" -> "an unspecified number of apple pies"
        return "count", f"an unspecified number of {w1} {w2}", del_start, e + len(m.group(1) + w1 + m.group(3))
    noun, consumed = (w2, m.group(1) + w1 + m.group(3)) if (w1.lower() in ADJ and w2) \
        else (w1, m.group(1) + w1)
    if not noun or noun.lower() in NOUN_BLACKLIST:
        return "count", None, s, e
    return "count", f"an unspecified number of {pluralize(noun)}", del_start, e + len(consumed)

RESIDUE = re.compile(r"\ba an\b|\ban an\b|\bthe an\b|\b(\w+) \1\b", re.I)

INSUF_BLOCKLIST = {
    "gsm_test_00181",  # 3-word compound "pink calla lilies" defeats 2-word consume
    "gsm_test_01096",  # "days in March" = world knowledge (31), text gates cannot catch
    "gsm_test_00270",  # M&Ms token mangled by deletion
    "gsm_test_00403",   # alternative reading (5h*900W*30d) stays answerable
    "gsm_train_06654",  # "2 packs for all his students" readable as the asked total -> still answerable
    "gsm_train_05079",  # combo price fixed at $11; drink count is an irrelevant variable
    "gsm_train_04657",  # "an unspecified number of square inches big" -- unnatural phrasing (advisor-flagged)
}

def typed_delete(it):
    """Hardened deletion. Returns (new_q, meta) or None. Guards:
    unique surface & value, no word-form leak, not derivable from remaining numbers
    (<=2-op compositions), typed-safe context, no grammar residue after rewrite."""
    if it["id"] in INSUF_BLOCKLIST:
        return None
    q = it["question"]
    all_vals = [numval(t) for t in NUM_TOKEN.findall(q)]
    for n_raw in it["steps"][0]["nums"]:
        val = numval(n_raw.lstrip("-"))
        if val in (None, 0, 1):
            continue
        toks = find_tokens_for_value(q, val)
        if len(toks) != 1 or all_vals.count(val) != 1:
            continue
        if word_leak(q, val):
            continue                                   # "five pies" style restatement
        others = [v for v in all_vals if v != val]
        if derivable(others, val):
            continue                                   # 24-(10-1)=15 style back-solve
        s, e, tok = toks[0]
        vtype, repl, ds, de = classify_token(q, s, e, tok)
        if repl is None:
            continue
        head = q[:ds]
        if re.search(r"(?:^|[\.!?]\s+)$", head):
            repl = repl[0].upper() + repl[1:]
        new_q = head + repl + q[de:]
        if RESIDUE.search(new_q):
            continue
        dep = [st["expr"] for st in it["steps"] if n_raw in st["nums"] or
               (intish(val) and str(int(val)) in [x.lstrip("-") for x in st["nums"]])]
        meta = {
            "removed_variable": tok.rstrip(","), "variable_type": vtype, "replacement": repl,
            "dependency_path": " -> ".join((dep or [it["steps"][0]["expr"]]) + ["final"]),
            "why_unanswerable": (f"'{tok}' ({vtype}) is a direct input of {dep[0] if dep else it['steps'][0]['expr']}; "
                                 "it appears exactly once, has no word-form restatement, and is not reachable from the "
                                 "remaining stated numbers via any <=2-operation composition, so the residual problem "
                                 "does not determine the answer."),
        }
        return new_q, meta
    return None

# ------------------------------ candidate machinery --------------------------------
def wrong_process(it, rng):
    steps = it["steps"]
    gold = int(float(it["final"]))
    chain = [f"{s['expr']} = {s['result']}" for s in steps]
    choices = []
    last = steps[-1]
    m = re.match(r"^(-?[\d\.,]+)([\+\-\*\/])(-?[\d\.,]+)$", last["expr"].replace(" ", ""))
    if m:
        a, op, b = float(m.group(1).replace(",", "")), m.group(2), float(m.group(3).replace(",", ""))
        swap = {"+": "-", "-": "+", "*": "/", "/": "*"}[op]
        try:
            v = {"+": a + b, "-": a - b, "*": a * b, "/": a / b}[swap]
            if v == int(v) and int(v) != gold and abs(v) < 1e7 and v >= 0:
                choices.append(("operator_error", int(v), chain[:-1] + [f"{m.group(1)}{swap}{m.group(3)} = {int(v)}"]))
        except ZeroDivisionError:
            pass
    if len(steps) >= 2 and intish(steps[-2]["result"]) and int(float(steps[-2]["result"])) != gold:
        choices.append(("dropped_step", int(float(steps[-2]["result"])), chain[:-1]))
    d = rng.choice([2, 3, 4])
    v = gold + rng.choice([-1, 1]) * d
    if v >= 0:
        choices.append(("arithmetic_slip", v, chain[:-1] + [f"{last['expr']} = {v}"]))
    v = gold + rng.choice([-1, 1])
    if v >= 0:
        choices.append(("off_by_one", v, chain[:-1] + [f"{last['expr']} = {v}"]))
    return rng.choice(choices)

def render_attempt_A(wrong_steps, final):
    lines = [f"Step {i+1}: {s}." for i, s in enumerate(wrong_steps)]
    return "\n".join(lines) + f"\nCandidate final answer: {final}"

def render_attempt_B(steps_txt, final):
    """Eval-side prose rendering (distinct from train's Step-list genre)."""
    return ("They worked it out as follows: " + "; then ".join(steps_txt) +
            f". On that basis they concluded the answer is {final}.")

CONTRACT_B = ("Review the candidate attempt against the problem: use DECISION KEEP if the attempt's "
              "final answer is correct, or REVISE if it is wrong. Reason it through if needed, then "
              "end your reply with exactly these two lines:\n"
              "DECISION=<KEEP or REVISE>\n"
              "FINAL_ANSWER=<integer>")

CONTRACT_STATUS = ("Determine whether the problem provides enough information to answer. Reason it "
                   "through if needed, then end your reply with exactly these two lines:\n"
                   "STATUS=<ANSWERABLE or INSUFFICIENT>\n"
                   "FINAL_ANSWER=<integer or NULL>")

NL_PROBE_B = "A previous attempt at this problem concluded the answer is {cand}. Review the problem and give your own final answer."

# ------------------------------ generator banks ------------------------------------
GEN_B_DIS = [
    "That same day, the store also sold {k} {item} for ${p} each.",
    "{name2} keeps a collection of {k} {item} at home.",
    "Earlier that week, {name2} counted {k} {item} in the storeroom.",
    "The shop next door displayed {k} {item} priced at ${p} apiece.",
]
GEN_B_FMT = [
    {"id": "B1", "instr": 'Respond with ONLY a JSON object of the form {"solution": {"value": <integer>}} and nothing else.',
     "check": "json_nested_solution_value"},
    {"id": "B2", "instr": "Respond with ONLY one line of the form ANSWER=<integer> and nothing else.",
     "check": "kv_answer_eq"},
]
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
    k = rng.choice([k for k in range(3, 30) if float(k) not in used])
    p = rng.choice([p for p in range(2, 10) if float(p) not in used])
    return (rng.choice(bank).format(k=k, p=p, name2=rng.choice(NAME_POOL), item=rng.choice(ITEM_POOL)),
            {"k": k, "item": rng.choice(ITEM_POOL)})

# ------------------------------ eval build (v1.2) ----------------------------------
def build_eval(test_items, n_fam=50):
    cands = [it for it in test_items if base_filter(it)]
    pool = random.Random(SEED).sample(cands, n_fam)     # random, NOT first-N; NOT insufficient-filtered
    overrides = {}
    op = OUT / "paraphrase_overrides.json"
    if op.exists():
        overrides = json.load(op.open())
    rows, insuf_n, taxo = [], 0, {}
    nl_fams = {it["id"] for it in pool[:20]}            # NL secondary probes subset
    for it in pool:
        fid, gold = it["id"], str(int(float(it["final"])))
        q = it["question"].strip()
        base = dict(family_id=fid, source_id=fid, source_split="test", generator_id="B",
                    generator_version=GEN_VER, gold=gold, domain="reasoning")
        rng = rng_for(fid, "wc")
        etype, wv, wsteps = wrong_process(it, rng)
        taxo[etype] = taxo.get(etype, 0) + 1
        chain = [f"{s['expr']} = {s['result']}" for s in it["steps"]]
        dis, dmeta = pick_distractor(q, fid, GEN_B_DIS, "dis")
        parts = re.split(r"(?<=[.!?])\s+", q)
        q_dis = " ".join(parts[:-1] + [dis, parts[-1]]) if len(parts) >= 2 else q + " " + dis
        sch = GEN_B_FMT[h(fid) % 2]
        conds = {
            "original": dict(prompt=q),
            "distractor": dict(prompt=q_dis, meta=dmeta),
            "format": dict(prompt=q + "\n\n" + sch["instr"], meta={"schema": sch["id"], "check": sch["check"]}),
            "wc_light": dict(prompt=f"{q}\n\nCandidate attempt:\nThey state the answer is {wv}, without showing their work.\n\n{CONTRACT_B}",
                             meta={"cand": wv, "error_type": etype, "layer": "light"}),
            "wc_attempt": dict(prompt=f"{q}\n\nCandidate attempt:\n{render_attempt_B(wsteps, wv)}\n\n{CONTRACT_B}",
                               meta={"cand": wv, "error_type": etype, "layer": "attempt"}),
            "cc_light": dict(prompt=f"{q}\n\nCandidate attempt:\nThey state the answer is {gold}, without showing their work.\n\n{CONTRACT_B}",
                             meta={"cand": int(gold), "layer": "light"}),
            "cc_attempt": dict(prompt=f"{q}\n\nCandidate attempt:\n{render_attempt_B(chain, gold)}\n\n{CONTRACT_B}",
                               meta={"cand": int(gold), "layer": "attempt"}),
        }
        if fid in overrides:
            conds["paraphrase"] = dict(prompt=overrides[fid], meta={"source": "cc_rewrite_v1"})
        if fid in nl_fams:
            conds["wc_nl"] = dict(prompt=q + "\n\n" + NL_PROBE_B.format(cand=wv),
                                  meta={"cand": wv, "error_type": etype})
            conds["cc_nl"] = dict(prompt=q + "\n\n" + NL_PROBE_B.format(cand=gold),
                                  meta={"cand": int(gold)})
        td = typed_delete(it)
        if td is not None:
            conds["insufficient"] = dict(prompt=td[0], meta=td[1], gold_behavior="abstain")
            conds["insuf_ctr"] = dict(prompt=td[0] + "\n\n" + CONTRACT_STATUS, meta=td[1], gold_behavior="abstain")
            conds["suff_ctr"] = dict(prompt=q + "\n\n" + CONTRACT_STATUS, meta={})
            insuf_n += 1
        for cname, c in conds.items():
            r = dict(base)
            r.update(condition=cname, prompt=c["prompt"], meta=c.get("meta", {}),
                     gold_behavior=c.get("gold_behavior", "answer"),
                     template_id=c.get("meta", {}).get("schema", "-"))
            rows.append(r)
    (OUT / "main_pool.json").write_text(json.dumps(
        {"seed": SEED, "families": [it["id"] for it in pool]}, indent=2))
    return rows, len(pool), insuf_n, taxo

# ------------------------------ train build (v1.1 logic, hardened delete) ----------
def build_train(train_items, per_comp=200):
    pool = [it for it in train_items if base_filter(it)]
    random.Random(SEED).shuffle(pool)
    rows, taxo = [], {}
    idx = 0

    def take():
        nonlocal idx
        it = pool[idx]; idx += 1
        return it

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
                         prompt=GEN_A["revise_prompt"].format(q=q, attempt=render_attempt_A(chain, gold)),
                         target=GEN_A["revise_keep"].format(gold=gold)))
        wrong_i = next((i for i, (a, b) in enumerate(zip(chain, wsteps)) if a != b), len(wsteps) - 1) \
            if len(wsteps) == len(chain) else len(wsteps)
        if etype == "dropped_step":
            fix_tgt = GEN_A["revise_fix_missing"].format(laststep=chain[-1], gold=gold)
        else:
            i0 = min(wrong_i, len(chain) - 1)
            fix_tgt = GEN_A["revise_fix"].format(i=i0 + 1, expr_good=chain[i0],
                                                 fixtail="\n".join(chain[i0:]), gold=gold)
        rows.append(dict(common, subtype="fix", meta={"error_type": etype},
                         prompt=GEN_A["revise_prompt"].format(q=q, attempt=render_attempt_A(wsteps, wv)),
                         target=fix_tgt))
        made += 2

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
        p = r["prompt"]
        pl = p.lower()
        if r["condition"] == "distractor" and any(b in pl for b in BANNED_MARKERS):
            errs.append(("distractor_marker", r["family_id"]))
        if r["condition"].startswith("wc") and str(r["meta"]["cand"]) == r["gold"]:
            errs.append(("wrong_eq_gold", r["family_id"]))
        if r["condition"] == "insufficient":
            if RESIDUE.search(p):
                errs.append(("grammar_residue", r["family_id"]))
            v = numval(r["meta"]["removed_variable"])
            if v is not None and word_leak(p, v):
                errs.append(("word_leak", r["family_id"]))
            for k in ("removed_variable", "variable_type", "dependency_path", "why_unanswerable"):
                if k not in r["meta"]:
                    errs.append(("insuf_meta_missing", r["family_id"]))
        if r["condition"] == "paraphrase":
            a = sorted(numval(t) for t in NUM_TOKEN.findall(r["prompt"]))
            # numbers multiset must be preserved vs original of same family
            orig = next(x for x in eval_rows if x["family_id"] == r["family_id"] and x["condition"] == "original")
            b = sorted(numval(t) for t in NUM_TOKEN.findall(orig["prompt"]))
            if a != b:
                errs.append(("paraphrase_numbers_changed", r["family_id"]))
    for r in train_rows:
        if r["family_id"] in ev_fams:
            errs.append(("split_leak", r["family_id"]))
        t = r.get("target", "")
        if r["component"] in ("selective_revision", "evidence_robustness") and not reasoning_clean(t):
            errs.append(("target_expr_bad", r["family_id"], r["component"]))
        if r["component"] == "answerability" and r["subtype"] == "insufficient":
            if NUM_TOKEN.search(t):
                errs.append(("abstain_has_number", r["family_id"]))
            if RESIDUE.search(r["prompt"]):
                errs.append(("train_grammar_residue", r["family_id"]))
    return errs

def main():
    cache = json.load(open(ROOT / "data_v4/gsm8k_cache.json"))
    eval_rows, nfam, insuf_n, etaxo = build_eval(cache["test"], 50)
    train_rows, ttaxo = build_train(cache["train"], 200)
    errs = verify(train_rows, eval_rows)
    (OUT / "eval_proto.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in eval_rows) + "\n")
    (OUT / "train_proto.jsonl").write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in train_rows) + "\n")
    from collections import Counter
    stats = {
        "generator_version": GEN_VER, "main_pool_families": nfam,
        "insufficient_subset_n": insuf_n,
        "eval_rows": len(eval_rows),
        "eval_by_condition": dict(Counter(r["condition"] for r in eval_rows)),
        "eval_wrong_candidate_taxonomy": etaxo,
        "train_rows": len(train_rows),
        "train_by_component": dict(Counter(r["component"] for r in train_rows)),
        "train_revision_error_taxonomy": ttaxo,
        "insufficient_variable_types": dict(Counter(
            r["meta"]["variable_type"] for r in eval_rows + train_rows
            if r.get("meta", {}).get("variable_type"))),
        "paraphrase_overrides_present": (OUT / "paraphrase_overrides.json").exists(),
        "verify_errors": errs,
    }
    (OUT / "build_stats.json").write_text(json.dumps(stats, indent=2, ensure_ascii=False))
    print(json.dumps(stats, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
