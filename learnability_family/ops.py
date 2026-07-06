"""Tier-2 learnability family — four tiers of invented operators (D-9/R-9, C-5.2/5.3).

Tier a  (lookup)    : operator defined ONLY by a finite random table; no rule exists.
                      Unseen combinations have generator-assigned golds that are
                      structurally unpredictable -> A=0 by construction (the negative
                      anchor of the frontier).
Tier b  (1-step)    : zorp(a,b) = a + b + 1
Tier c  (2-step)    : quilt(a,b) = 2*(a+b) - 3          (sum, then scale-shift)
Tier d  (3-step)    : brame(a,b) = 3*(a-b) + (a+b) + 4  (diff, sum, then combine)

All names are invented (clean gate: pre-repair zero-shot ~0 required before training).
Operands: train sampled from [0,99]; eval-ID = UNSEEN combos in [0,99];
eval-OOD = combos in [100,999]. Constructive zero-leak: combo sets are asserted disjoint.
"""
from __future__ import annotations

import random

RANGE_ID = (0, 99)
RANGE_OOD = (100, 999)


def tier_a_table(rng: random.Random, n: int = 2600):
    """Random lookup table: combo -> random 3-digit gold (no structure)."""
    combos = set()
    while len(combos) < n:
        combos.add((rng.randint(*RANGE_ID), rng.randint(*RANGE_ID)))
    return {c: rng.randint(100, 999) for c in sorted(combos)}


TIERS = {
    "a": dict(
        name="flurm", depth=0,
        rule="The flurm of two numbers has no formula; each pair's value is a memorized fact.",
        fn=None,
        steps=lambda a, b, v: [f"flurm({a}, {b}) is the memorized value {v}."]),
    "b": dict(
        name="zorp", depth=1,
        rule="To compute the zorp of two numbers, add them together and then add one.",
        fn=lambda a, b: a + b + 1,
        steps=lambda a, b, v: [f"{a} + {b} = {a+b}.", f"{a+b} + 1 = {v}."]),
    "c": dict(
        name="quilt", depth=2,
        rule="To compute the quilt of two numbers, add them, double the sum, then subtract three.",
        fn=lambda a, b: 2 * (a + b) - 3,
        steps=lambda a, b, v: [f"{a} + {b} = {a+b}.", f"2 * {a+b} = {2*(a+b)}.",
                               f"{2*(a+b)} - 3 = {v}."]),
    "d": dict(
        name="brame", depth=3,
        rule="To compute the brame of two numbers, take three times their difference, "
             "add their sum, then add four.",
        fn=lambda a, b: 3 * (a - b) + (a + b) + 4,
        steps=lambda a, b, v: [f"{a} - {b} = {a-b}; 3 * {a-b} = {3*(a-b)}.",
                               f"{a} + {b} = {a+b}.",
                               f"{3*(a-b)} + {a+b} + 4 = {v}."]),
}
