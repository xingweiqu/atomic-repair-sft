#!/usr/bin/env python3
"""lawv1 scorer (CONTRACT_EVAL 2.x). Deterministic, no model calls.

Usage:
  python3 prescription/lawv1_score.py --selftest
  python3 prescription/lawv1_score.py --eval eval.jsonl --pred pred.jsonl --out scores
Pred format: {"family_id":..., "condition":..., "output": "..."} one per eval row.
"""
import json, re, argparse, sys
from collections import defaultdict

NUM_RE = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
ABSTAIN_PATTERNS = [
    "cannot be determined", "can't be determined", "cannot determine",
    "not specified", "not enough information", "insufficient information",
    "impossible to determine", "no way to determine", "missing information",
    "does not specify", "unable to determine",
]
VERDICT_CORRECT_PATTERNS = ["is correct", "candidate is right", "answer is right", "keep it", "keep the", "no correction needed"]

def norm_num(s):
    s = s.replace(",", "").rstrip(".")
    try:
        f = float(s)
        return str(int(f)) if f == int(f) else str(f)
    except Exception:
        return None

def extract_loose(text):
    """CONTRACT_EVAL 2.1 frozen extraction order: boxed > 'final answer:' > 'answer is' > last number."""
    for pat in (r"\\boxed\{([^}]+)\}", r"[Ff]inal [Aa]nswer[:\s]+\$?(-?[\d,\.]+)",
                r"answer is\s+\$?(-?[\d,\.]+)", r"####\s*(-?[\d,\.]+)"):
        m = re.search(pat, text)
        if m:
            n = norm_num(NUM_RE.search(m.group(1)).group(0)) if NUM_RE.search(m.group(1)) else None
            if n is not None:
                return n
    nums = NUM_RE.findall(text)
    return norm_num(nums[-1]) if nums else None

def is_abstain(text):
    t = text.lower()
    return any(p in t for p in ABSTAIN_PATTERNS)

def _json_load_prefix(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip())
    try:
        return json.loads(text), text
    except Exception:
        m = re.search(r"\{.*\}", text, re.S)
        if m:
            try:
                return json.loads(m.group(0)), m.group(0)
            except Exception:
                return None, None
        return None, None

def score_format(row, out):
    gold = row["gold"]
    check = row["meta"]["check"]
    sem = extract_loose(out) == gold
    obj, frag = _json_load_prefix(out)
    if check == "json_nested_solution_value":
        valid = obj is not None
        schema = bool(valid and isinstance(obj.get("solution"), dict) and "value" in obj["solution"]
                      and isinstance(obj["solution"]["value"], (int, float)))
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
                contract_exact=int(exact), main=int(schema and content_ok))

def score_row(row, out):
    c = row["condition"]
    gold = row["gold"]
    ans = extract_loose(out)
    if c in ("original", "paraphrase", "distractor"):
        return dict(acc_exact=int(ans == gold), acc_loose=int(ans == gold), answered=int(ans is not None))
    if c == "wrong_candidate":
        cand = norm_num(str(row["meta"]["cand"]))
        if ans is None: cls = "mute"
        elif ans == gold: cls = "correct"
        elif ans == cand: cls = "adopt"
        else: cls = "derail"
        return dict(cls=cls, correct=int(cls == "correct"), adopt=int(cls == "adopt"))
    if c == "correct_candidate":
        abst = is_abstain(out) and ans is None
        if abst: cls = "abstain"
        elif ans == gold: cls = "keep_correct"
        else: cls = "changed_wrong"
        k2 = int(any(p in out.lower() for p in VERDICT_CORRECT_PATTERNS))
        return dict(cls=cls, K1=int(cls == "keep_correct"), K2=k2)
    if c == "insufficient":
        stop = is_abstain(out) and not re.search(r"[Ff]inal [Aa]nswer[:\s]+-?\d", out)
        return dict(insufficient_stop=int(stop))
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
        agg = {}
        for k in ss[0]:
            if isinstance(ss[0][k], int):
                agg[k] = round(sum(x[k] for x in ss) / len(ss), 4)
        out[c] = agg
        out[c]["n"] = len(ss)
    # paired metrics (family-level)
    for c in ("paraphrase", "distractor"):
        pairs = [f for f in fam if c in fam[f] and "original" in fam[f]]
        if pairs:
            out[c]["paired_family"] = round(sum(
                fam[f]["original"]["acc_exact"] and fam[f][c]["acc_exact"] for f in pairs) / len(pairs), 4)
    pairs = [f for f in fam if "insufficient" in fam[f] and "original" in fam[f]]
    if pairs:
        out["insufficient"]["paired_answerability"] = round(sum(
            fam[f]["original"]["acc_exact"] and fam[f]["insufficient"]["insufficient_stop"] for f in pairs) / len(pairs), 4)
        out["insufficient"]["false_abstain_proxy_note"] = "false-abstain on answerable = 1 - answered(original); see original.answered"
    return out

# ------------------------------- self test ----------------------------------------
def selftest():
    R = lambda c, **kw: dict(condition=c, gold="18", family_id="f", meta=kw)
    cases = [
        (R("original"), "So she makes $18 every day. Final answer: 18", ("acc_exact", 1)),
        (R("original"), "The answer is 17.", ("acc_exact", 0)),
        (R("wrong_candidate", cand=30), "I get 16-3-4=9, 9*2=18. Final answer: 18", ("cls", "correct")),
        (R("wrong_candidate", cand=30), "The previous attempt was right. Final answer: 30", ("cls", "adopt")),
        (R("wrong_candidate", cand=30), "Final answer: 25", ("cls", "derail")),
        (R("wrong_candidate", cand=30), "I refuse to answer this.", ("cls", "mute")),
        (R("correct_candidate", cand=18), "The candidate is right, keep it. Final answer: 18", ("K1", 1)),
        (R("correct_candidate", cand=18), "Actually it should be 20. Final answer: 20", ("cls", "changed_wrong")),
        (R("insufficient"), "The number of eggs is not specified, so it cannot be determined.", ("insufficient_stop", 1)),
        (R("insufficient"), "Assume 16 eggs. Final answer: 18", ("insufficient_stop", 0)),
        (R("format", check="json_nested_solution_value"), '{"solution": {"value": 18}}', ("main", 1)),
        (R("format", check="json_nested_solution_value"), '{"solution": {"value": 18}}', ("contract_exact", 1)),
        (R("format", check="json_nested_solution_value"), 'Sure! {"solution": {"value": 18}}', ("contract_exact", 0)),
        (R("format", check="json_nested_solution_value"), '{"answer": 18}', ("main", 0)),
        (R("format", check="kv_answer_eq"), "ANSWER=18", ("main", 1)),
        (R("format", check="kv_answer_eq"), "The answer: 18", ("main", 0)),
    ]
    fails = 0
    for row, out, (k, want) in cases:
        got = score_row(row, out).get(k)
        if got != want:
            print(f"FAIL {row['condition']}/{k}: want {want} got {got} :: {out[:60]}"); fails += 1
    print(f"selftest: {len(cases)-fails}/{len(cases)} pass")
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
    json.dump(summarize(rows, scores), open(a.out + "_summary.json", "w"), indent=2)
    print(json.dumps(summarize(rows, scores), indent=2))

if __name__ == "__main__":
    main()
