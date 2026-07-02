"""Loop 1 dual-tier judge wrapper (qc/LOOP0_RULINGS.md D-2, C-1).

WRAPS the existing v3.1 strict judge and the historical lenient fallback chain into two
explicit tiers. No existing judging logic is modified — everything is imported from
scenario_repair_v3.evaluate_v3 / gsm_repair_v4.evaluate_gsm and only re-packaged.

Tiers (frozen):
  strict  : output parses to JSON containing a `final_answer` key; abstain via
            is_abstain_strict. Unparseable output = wrong (and excluded from the L3
            identity scope per C-1; it is charged to F).
  lenient : historical fallback chain final_answer -> update_value -> regex
            "final answer:" -> last line (= evaluate_v3.final + bprime extract_final),
            abstain via is_abstain_lenient.

Historical-replication config = (final=lenient chain, abstain=strict): exactly what
evaluate_v3.py / evaluate_gsm.py computed. Regression-gated by ledger/regression_test.py.

w extraction (R-1 + LOOP0_RULINGS §3-R1):
  w_source = "planted"   : item carries planted_wrong_answer  (Corrupt-type, R-1 letter)
  w_source = "tentative" : no planted value, but update_decision == "update" and the
                           tentative answer is wrong — the wrong value IS in the prompt
                           ("Tentative answer: X"). This matches the historical resist
                           convention ([b-prime] bprime/bprime_audit.py:8 "planted/tentative
                           wrong value"). Kept as a SEPARATE tier so the ledger can be
                           read under strict-R-1 (planted only) or historical convention.
  w_source = "none"      : keep/abstain/Aug/Abl items -> not decomposable (D/A = N/A).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scenario_repair_v3.evaluate_v3 import (  # noqa: E402
    parse, norm, final as final_chain_v3, is_abstain_strict, is_abstain_lenient)
from gsm_repair_v4.evaluate_gsm import numkey  # noqa: E402


# ---------------- matching ----------------

def match(domain: str, a, b) -> bool:
    """Domain answer equality: numeric for GSM (v4), normalised string otherwise."""
    if a is None or b is None:
        return False
    if domain == "v4":
        ka, kb = numkey(str(a)), numkey(str(b))
        if ka is not None and kb is not None:
            return ka == kb
    return norm(a) == norm(b)


def lenient_final(o, raw):
    """Historical fallback chain incl. the underfit-floor `update_value` rescue."""
    if isinstance(o, dict):
        for k in ("final_answer", "update_value"):
            v = o.get(k)
            if v not in (None, ""):
                return v
    return final_chain_v3(o if isinstance(o, dict) else None, raw)


# ---------------- w extraction ----------------

def wrong_value(item, domain):
    """Return (w, w_source) per R-1; see module docstring."""
    pw = item.get("planted_wrong_answer")
    if pw not in (None, ""):
        return pw, "planted"
    tent = item.get("tentative_answer")
    gold = item.get("gold_answer")
    if (item.get("update_decision") == "update" and tent not in (None, "")
            and gold is not None and not match(domain, tent, gold)):
        return tent, "tentative"
    return None, "none"


# ---------------- per-item verdict ----------------

def verdict(item, raw, domain):
    """All judge facts for one (eval item, model output) pair."""
    o = parse(raw)
    parsed_strict = isinstance(o, dict) and "final_answer" in o
    gold = item.get("gold_answer")
    is_abstain_item = gold is None

    f_strict = o.get("final_answer") if parsed_strict else None
    f_hist = final_chain_v3(o if isinstance(o, dict) else None, raw)  # exact evaluate_v3 chain
    f_len = lenient_final(o, raw)                                     # + update_value rescue (D-2 lenient tier)
    ab_s = is_abstain_strict(o if isinstance(o, dict) else None, raw)
    ab_l = is_abstain_lenient(o if isinstance(o, dict) else None, raw)

    if is_abstain_item:
        correct_strict = bool(ab_s)
        correct_lenient = bool(ab_l)
        correct_hist = bool(ab_s)          # historical = strict abstain
    else:
        correct_strict = parsed_strict and match(domain, f_strict, gold)
        correct_lenient = match(domain, f_len, gold)
        correct_hist = match(domain, f_hist, gold)

    w, w_source = wrong_value(item, domain)
    resist = ability = None
    if w is not None and parsed_strict:
        # C-1(ii): parsed abstain output != w  =>  resist = 1 (never charged to F).
        resist = int(not match(domain, f_strict, w))
        if resist:
            ability = int(match(domain, f_strict, gold)) if gold is not None else 0

    return {
        "parsed_strict": int(parsed_strict),
        "correct_strict": int(correct_strict),
        "correct_lenient": int(correct_lenient),
        "correct_hist": int(correct_hist),
        "abstain_item": int(is_abstain_item),
        "w_source": w_source,
        "resist": resist,
        "ability": ability,
    }


def load_preds(path: Path):
    return [json.loads(l).get("predict", "") for l in path.open() if l.strip()]


def load_items(path: Path):
    return [json.loads(l) for l in path.open() if l.strip()]


def score_run(items, raws, domain):
    """List of verdicts, index-aligned (LF predict keeps eval order)."""
    assert len(items) == len(raws), f"row mismatch {len(items)} vs {len(raws)}"
    return [verdict(it, r, domain) for it, r in zip(items, raws)]
