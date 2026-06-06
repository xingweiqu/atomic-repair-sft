"""Synthetic Reasoning world for atomic-repair v2.

The Reasoning domain must be as "clean" as the Knowledge/Hybrid synthetic
entities: the model must NOT already know the answer from pretraining. Real
arithmetic (x+5=12) fails this — the model already knows how to solve it. So we
invent FICTITIOUS named operations whose definitions are injected as facts, and
test on UNSEEN operand values.

Example:
  Operation "quarn":  quarn(a, b) = (a + b) * 3
  Injected fact (knowledge stage): "To compute quarn of two numbers, add them
                                     and multiply by three."
  Test item (unseen operands): "Compute quarn of 4 and 5."  -> 27

Because the operation name and rule are invented, the model can only answer if
(a) it learned the rule (knowledge stage) AND (b) it can execute it (the reasoning
capacity we study). Test operands never appear in the injected rule statements, so
the model cannot have memorised "this input -> this output"; it must run the rule.

This module is pure-Python, deterministic, no API. It mirrors the shape of v0's
build_family_graph so generate_v2 can treat K/R/H uniformly.
"""
from __future__ import annotations

import random
from typing import Any

# --------------------------------------------------------------------------- #
# Invented operations. Each has a fictitious name, a human-readable rule
# statement (injected as a fact), and a pure-Python evaluator over two operands.
# Keep the arithmetic small-integer so answers are short, unambiguous strings.
# --------------------------------------------------------------------------- #
OPERATIONS: dict[str, dict[str, Any]] = {
    "quarn": {
        "rule_statement": "To compute the quarn of two numbers, add them together and then multiply the sum by three.",
        "rule_short": "quarn(a, b) = (a + b) * 3",
        "fn": lambda a, b: (a + b) * 3,
        "steps": lambda a, b: [f"add {a} and {b} to get {a+b}", f"multiply {a+b} by 3 to get {(a+b)*3}"],
    },
    "drimble": {
        "rule_statement": "To compute the drimble of two numbers, multiply the first by two and then subtract the second.",
        "rule_short": "drimble(a, b) = 2*a - b",
        "fn": lambda a, b: 2 * a - b,
        "steps": lambda a, b: [f"multiply {a} by 2 to get {2*a}", f"subtract {b} from {2*a} to get {2*a-b}"],
    },
    "florkt": {
        "rule_statement": "To compute the florkt of two numbers, square the first and add the second.",
        "rule_short": "florkt(a, b) = a*a + b",
        "fn": lambda a, b: a * a + b,
        "steps": lambda a, b: [f"square {a} to get {a*a}", f"add {b} to {a*a} to get {a*a+b}"],
    },
    "splisk": {
        "rule_statement": "To compute the splisk of two numbers, add five to the first and then multiply by the second.",
        "rule_short": "splisk(a, b) = (a + 5) * b",
        "fn": lambda a, b: (a + 5) * b,
        "steps": lambda a, b: [f"add 5 to {a} to get {a+5}", f"multiply {a+5} by {b} to get {(a+5)*b}"],
    },
    "trell": {
        "rule_statement": "To compute the trell of two numbers, subtract the second from the first and then double the result.",
        "rule_short": "trell(a, b) = (a - b) * 2",
        "fn": lambda a, b: (a - b) * 2,
        "steps": lambda a, b: [f"subtract {b} from {a} to get {a-b}", f"double {a-b} to get {(a-b)*2}"],
    },
    "vexor": {
        "rule_statement": "To compute the vexor of two numbers, multiply them together and then add four.",
        "rule_short": "vexor(a, b) = a*b + 4",
        "fn": lambda a, b: a * b + 4,
        "steps": lambda a, b: [f"multiply {a} and {b} to get {a*b}", f"add 4 to {a*b} to get {a*b+4}"],
    },
}

OPERATION_NAMES = list(OPERATIONS.keys())


def rule_fact_sentence(op: str) -> str:
    """The injected knowledge for this operation (used in the fact stage)."""
    return OPERATIONS[op]["rule_statement"]


def eval_op(op: str, a: int, b: int) -> int:
    return OPERATIONS[op]["fn"](a, b)


def op_steps(op: str, a: int, b: int) -> list[str]:
    """Human-readable derivation steps (used to build repair_trace)."""
    return OPERATIONS[op]["steps"](a, b)


# --------------------------------------------------------------------------- #
# Operand pools, split so TEST operands never appear in injected rule examples.
# The rule statements above contain NO operands, so any operand is "unseen", but
# we still keep a train/eval operand split so repair-train and repair-eval use
# different number pairs (cleanliness for the repair stage too).
# --------------------------------------------------------------------------- #
def operand_pairs(rng: random.Random, n: int, lo: int = 2, hi: int = 12) -> list[tuple[int, int]]:
    pairs = set()
    while len(pairs) < n:
        a = rng.randint(lo, hi)
        b = rng.randint(lo, hi)
        pairs.add((a, b))
    return sorted(pairs)


def build_reasoning_items(rng: random.Random, n_per_op: int = 40) -> list[dict[str, Any]]:
    """Return base reasoning items: one (op, a, b, gold) each. These are the
    'original' problems; perturbations (R-Aug/Abl/Cor) are applied later by the
    forms layer. Deterministic given rng seed."""
    items = []
    for op in OPERATION_NAMES:
        pairs = operand_pairs(rng, n_per_op)
        for (a, b) in pairs:
            gold = eval_op(op, a, b)
            items.append({
                "op": op,
                "a": a, "b": b,
                "gold": str(gold),
                "rule_statement": rule_fact_sentence(op),
                "rule_short": OPERATIONS[op]["rule_short"],
                "steps": op_steps(op, a, b),
            })
    rng.shuffle(items)
    return items


def all_rule_facts() -> list[dict[str, str]]:
    """The full set of reasoning 'facts' to inject in the knowledge stage:
    one rule statement per operation. (Small set: len(OPERATIONS) facts.)"""
    return [{"op": op, "rule_statement": rule_fact_sentence(op),
             "rule_short": OPERATIONS[op]["rule_short"]} for op in OPERATION_NAMES]
