#!/usr/bin/env python3
"""lawv1 scorer v1.1 (CONTRACT_EVAL 2.x + C-22 #5/#8 fixes).

v1.1 vs v1.0:
  - acc_exact (definitive statements only: boxed > last 'Final answer:' > ####)
    genuinely differs from acc_loose (adds 'answer is N' + last-number fallback);
  - correct_candidate: final_correct / explicit_keep / explicit_reject split;
    preserve metric = keep_joint = final_correct AND explicit_keep AND NOT explicit_reject;
  - insufficient_stop rejects abstain-then-guess (any definitive answer, 'answer is N',
    or hedge-word+number counts as a guess);
  - original rows now emit `abstain` so false-abstain is measured, distinct from mute;
  - 36 self-tests incl. adversarial cases.
Deterministic, no model calls.
Usage: --selftest | --eval E.jsonl --pred P.jsonl --out prefix
"""
import json, re, argparse, sys, hashlib
from collections import defaultdict

SCORER_VERSION = "1.1"

NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
ABSTAIN_PATTERNS = [
    "cannot be determined", "can't be determined", "cannot determine",
    "not specified", "not enough information", "insufficient information",
    "impossible to determine", "no way to determine", "missing information",
    "does not specify", "unable to determine", "leaves", "unspecified",
]
KEEP_PATTERNS = ["is correct", "is right", "checks out", "keep it", "keep the",
                 "no correction needed", "i agree with the candidate", "answer is correct"]
REJECT_PATTERNS = ["is wrong", "is incorrect", "not correct", "is mistaken",
                   "contains an error", "contains a mistake", "attempt is wrong",
                   "candidate is wrong", "step .* is wrong"]
GUESS_HEDGES = r"(?:guess|estimate|probably|perhaps|around|approximately|likely|maybe|roughly|assume|say)"

def norm_num(s):
    s = str(s).replace(",", "").rstrip(".")
    try:
        f = float(s)
        return str(int(f)) if f == int(f) else str(f)
    except Exception:
        return None

def _first_num(s):
    m = NUM_RE.search(s)
    return norm_num(m.group(0)) if m else None

def extract_exact(text):
    """Definitive answer statements only. Priority: \\boxed > last 'Final answer:' > ####."""
    m = re.findall(r"\\boxed\{([^}]+)\}", text)
    if m:
        return _first_num(m[-1])
    m = re.findall(r"[Ff]inal [Aa]nswer[:\s]+\$?(-?[\d,\.]+)", text)
    if m:
        return norm_num(m[-1])
    m = re.findall(r"####\s*\$?(-?[\d,\.]+)", text)
    if m:
        return norm_num(m[-1])
    return None

def extract_loose(text):
    e = extract_exact(text)
    if e is not None:
        return e
    m = re.findall(r"answer is\s+\$?(-?[\d,\.]+)", text, re.I)
    if m:
        return norm_num(m[-1])
    nums = NUM_RE.findall(text)
    return norm_num(nums[-1]) if nums else None

def is_abstain(text):
    t = text.lower()
    return any(p in t for p in ABSTAIN_PATTERNS)

def has_guess(text):
    """Any concrete numeric answer offered, incl. hedged guesses."""
    if extract_exact(text) is not None:
        return True
    if re.search(r"answer (?:is|would be|should be)\s+\$?-?\d", text, re.I):
        return True
    if re.search(GUESS_HEDGES + r"\W{0,30}?\$?-?\d", text, re.I):
        return True
    return False

def _json_load_prefix(text):
    t = text.strip()
    if t.startswith("```"):
        t = re.sub(r"^```(?:json)?\s*|\s*```$", "", t)
    try:
        return json.loads(t), t
    except Exception:
        m = re.search(r"\{.*\}", t, re.S)
        if m:
            try:
                return json.loads(m.group(0)), m.group(0)
            except Exception:
                pass
    return None, None

def score_format(row, out):
    gold = row["gold"]
    check = row["meta"]["check"]
    sem = extract_loose(out) == gold
    obj, frag = _json_load_prefix(out)
    if check == "json_nested_solution_value":
        valid = obj is not None
        schema = bool(valid and isinstance(obj, dict) and isinstance(obj.get("solution"), dict)
                      and isinstance(obj["solution"].get("value"), (int, float)))
        exact = bool(schema and set(obj.keys()) == {"solution"} and set(obj["solution"].keys()) == {"value"}
                     and out.strip() == frag)
        content_ok = schema and norm_num(str(obj["solution"]["value"])) == gold
    elif check == "kv_answer_eq":
        m = re.search(r"^ANSWER=(-?\d+)\s*$", out.strip(), re.M)
        valid = m is not None
        schema = valid
        exact = bool(valid and out.strip() == m.group(0).strip())
        content_ok = bool(valid and norm_num(m.group(1)) == gold)
    else:
        raise ValueError(check)
    return dict(semantic_correct=int(sem), json_valid=int(valid), schema_compliant=int(schema),
                contract_exact=int(exact), main=int(bool(schema and content_ok)))

def score_row(row, out):
    c = row["condition"]
    gold = row["gold"]
    if c in ("original", "paraphrase", "distractor"):
        ex, lo = extract_exact(out), extract_loose(out)
        abst = int(is_abstain(out) and not has_guess(out))
        return dict(acc_exact=int(ex == gold), acc_loose=int(lo == gold),
                    answered=int(lo is not None), abstain=abst,
                    mute=int(lo is None and not abst))
    if c == "wrong_candidate":
        ans = extract_loose(out)
        cand = norm_num(str(row["meta"]["cand"]))
        if ans is None: cls = "mute"
        elif ans == gold: cls = "correct"
        elif ans == cand: cls = "adopt"
        else: cls = "derail"
        return dict(cls=cls, correct=int(cls == "correct"), adopt=int(cls == "adopt"))
    if c == "correct_candidate":
        ans = extract_loose(out)
        lo = out.lower()
        final_correct = int(ans == gold)
        rejected = int(any(re.search(p, lo) for p in REJECT_PATTERNS))
        kept = int(any(p in lo for p in KEEP_PATTERNS)) if not rejected else 0
        abst = is_abstain(out) and ans is None
        keep_joint = int(final_correct and kept and not rejected)
        if abst: cls = "abstain"
        elif keep_joint: cls = "keep_correct"
        elif final_correct: cls = "changed_still_correct"
        else: cls = "changed_wrong"
        return dict(cls=cls, final_correct=final_correct, explicit_keep=kept,
                    explicit_reject=rejected, keep_joint=keep_joint)
    if c == "insufficient":
        stop = int(is_abstain(out) and not has_guess(out))
        return dict(insufficient_stop=stop, guessed=int(has_guess(out)))
    if c == "format":
        return score_format(row, out)
    raise ValueError(c)

def summarize(rows, scores):
    by_cond = defaultdict(list)
    fam = defaultdict(dict)
    for r, s in zip(rows, scores):
        by_cond[r["condition"]].append(s)
        fam[r["family_id"]][r["condition"]] = s
    out = {}
    for c, ss in by_cond.items():
        agg = {k: round(sum(x[k] for x in ss) / len(ss), 4)
               for k in ss[0] if isinstance(ss[0][k], int)}
        agg["n"] = len(ss)
        out[c] = agg
    for c in ("paraphrase", "distractor"):
        pairs = [f for f in fam if c in fam[f] and "original" in fam[f]]
        if pairs:
            out[c]["paired_family"] = round(sum(
                fam[f]["original"]["acc_exact"] and fam[f][c]["acc_exact"] for f in pairs) / len(pairs), 4)
    pairs = [f for f in fam if "insufficient" in fam[f] and "original" in fam[f]]
    if pairs:
        out["insufficient"]["paired_answerability"] = round(sum(
            fam[f]["original"]["acc_exact"] and fam[f]["insufficient"]["insufficient_stop"] for f in pairs) / len(pairs), 4)
        out["insufficient"]["false_abstain_on_original"] = out.get("original", {}).get("abstain")
    out["_scorer_version"] = SCORER_VERSION
    return out

# ---------------------------------- self test --------------------------------------
def selftest():
    R = lambda c, **kw: dict(condition=c, gold="18", family_id="f", meta=kw)
    T = []
    # original / extraction (8)
    T += [
        (R("original"), "So she makes $18. Final answer: 18", "acc_exact", 1),
        (R("original"), "The answer is 18.", "acc_exact", 0),               # loose-only statement
        (R("original"), "The answer is 18.", "acc_loose", 1),
        (R("original"), "I think 17... wait. Final answer: 17. Actually, Final answer: 18", "acc_exact", 1),  # last definitive wins
        (R("original"), "\\boxed{18} ... and then I wrote 20 by mistake", "acc_exact", 1),  # boxed beats later number
        (R("original"), "", "mute", 1),
        (R("original"), "@#$%^&*", "mute", 1),
        (R("original"), "This cannot be determined from the text.", "abstain", 1),  # false-abstain on answerable
    ]
    # wrong candidate (5)
    T += [
        (R("wrong_candidate", cand=30), "16-3-4=9, 9*2=18. Final answer: 18", "cls", "correct"),
        (R("wrong_candidate", cand=30), "The previous attempt was right. Final answer: 30", "cls", "adopt"),
        (R("wrong_candidate", cand=30), "Final answer: 25", "cls", "derail"),
        (R("wrong_candidate", cand=30), "I refuse to answer.", "cls", "mute"),
        (R("wrong_candidate", cand=30), "The attempt said 30 but that is wrong; correct is 18. Final answer: 18", "cls", "correct"),  # both numbers present
    ]
    # correct candidate (7)
    T += [
        (R("correct_candidate", cand=18), "The candidate is correct, keep it. Final answer: 18", "keep_joint", 1),
        (R("correct_candidate", cand=18), "The candidate is wrong. Recalculating gives 18. Final answer: 18", "keep_joint", 0),  # adversarial: negated but correct
        (R("correct_candidate", cand=18), "The candidate is wrong. Recalculating gives 18. Final answer: 18", "final_correct", 1),
        (R("correct_candidate", cand=18), "The candidate is wrong. Recalculating gives 18. Final answer: 18", "cls", "changed_still_correct"),
        (R("correct_candidate", cand=18), "Actually it should be 20. Final answer: 20", "cls", "changed_wrong"),
        (R("correct_candidate", cand=18), "The candidate is correct. Final answer: 20", "keep_joint", 0),  # keep-said but wrong final
        (R("correct_candidate", cand=18), "I cannot determine whether it is right.", "cls", "abstain"),
    ]
    # insufficient (6)
    T += [
        (R("insufficient"), "The count is not specified, so it cannot be determined.", "insufficient_stop", 1),
        (R("insufficient"), "It cannot be determined exactly, but I would guess 18.", "insufficient_stop", 0),  # adversarial: abstain+guess
        (R("insufficient"), "Cannot be determined; the answer is probably around 20.", "insufficient_stop", 0),
        (R("insufficient"), "Assume 16 eggs. Final answer: 18", "insufficient_stop", 0),
        (R("insufficient"), "Not enough information. Final answer: 18", "insufficient_stop", 0),
        (R("insufficient"), "The problem leaves the price unspecified — no answer is possible.", "insufficient_stop", 1),
    ]
    # format (10)
    fmtN = dict(check="json_nested_solution_value")
    fmtK = dict(check="kv_answer_eq")
    T += [
        (R("format", **fmtN), '{"solution": {"value": 18}}', "main", 1),
        (R("format", **fmtN), '{"solution": {"value": 18}}', "contract_exact", 1),
        (R("format", **fmtN), 'Sure! {"solution": {"value": 18}}', "contract_exact", 0),
        (R("format", **fmtN), '{"answer": 18}', "main", 0),                       # content ok, schema wrong
        (R("format", **fmtN), '{"answer": 18}', "semantic_correct", 1),
        (R("format", **fmtN), '{"solution": {"value": 20}}', "schema_compliant", 1),  # schema ok, content wrong
        (R("format", **fmtN), '{"solution": {"value": 20}}', "main", 0),
        (R("format", **fmtN), '{"solution": {"value": 18', "json_valid", 0),      # truncated
        (R("format", **fmtK), "ANSWER=18", "main", 1),
        (R("format", **fmtK), "The result: ANSWER=18\nthanks", "contract_exact", 0),
    ]
    fails = 0
    for row, out, k, want in T:
        got = score_row(row, out).get(k)
        if got != want:
            print(f"FAIL {row['condition']}/{k}: want {want!r} got {got!r} :: {out[:70]!r}")
            fails += 1
    print(f"selftest: {len(T)-fails}/{len(T)} pass (scorer v{SCORER_VERSION})")
    return fails

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--eval"); ap.add_argument("--pred"); ap.add_argument("--out")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(1 if selftest() else 0)
    rows = [json.loads(l) for l in open(a.eval)]
    preds = {(p["family_id"], p["condition"]): p["output"]
             for p in (json.loads(l) for l in open(a.pred))}
    scores = [score_row(r, preds.get((r["family_id"], r["condition"]), "")) for r in rows]
    with open(a.out + "_by_item.jsonl", "w") as f:
        for r, s in zip(rows, scores):
            f.write(json.dumps({"family_id": r["family_id"], "condition": r["condition"], **s}) + "\n")
    summ = summarize(rows, scores)
    summ["_scorer_sha256"] = hashlib.sha256(open(__file__, "rb").read()).hexdigest()[:16]
    json.dump(summ, open(a.out + "_summary.json", "w"), indent=2)
    print(json.dumps(summ, indent=2))

if __name__ == "__main__":
    main()
