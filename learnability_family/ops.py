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


# ---- Bendpoint tiers (PREREG_bendpoint, C-12 B2). Frozen tiers a-d above untouched. ----
STORY_TEMPLATES = [  # tier g: the b-tier rule (total plus one) wrapped in narrative, never stated as formula
    "In the village game of trewb, Alice brings {a} tokens and Bob brings {b}. The pot is everything they brought plus the single bonus token the dealer always adds. How many tokens are in the pot?",
    "A trewb ceremony combines two baskets: one holds {a} shells, the other {b}. Tradition adds one lucky shell at the end. How many shells result?",
    "During trewb, team one scores {a} points and team two scores {b}; the referee grants the customary extra point. What is the final trewb score?",
    "A trewb jar starts empty. Mira drops in {a} beads, Sam drops in {b}, and the jar's charm bead is added last. How many beads are in the jar?",
    "The trewb of a caravan is counted by taking the {a} camels of the first rider together with the {b} of the second, plus the guide's own camel. What is the trewb?",
    "At the trewb market a stall sells {a} apples in the morning and {b} in the afternoon, and the owner always counts the display apple too. What is the trewb count?",
    "Two trewb drummers play {a} and {b} beats; the closing beat belongs to the master. How many beats is the trewb?",
    "A trewb necklace is strung from {a} red beads, {b} blue beads, and the one clasp bead. How many beads in total?",
]

TIERS.update({
    "e": dict(
        name="snerv", depth=5,
        rule="To compute the snerv of two numbers: add them; double the result; subtract "
             "the second number; triple that; then add the first number and subtract five.",
        fn=lambda a, b: 3 * (2 * (a + b) - b) + a - 5,
        steps=lambda a, b, v: [
            f"{a} + {b} = {a+b}.",
            f"2 * {a+b} = {2*(a+b)}.",
            f"{2*(a+b)} - {b} = {2*(a+b)-b}.",
            f"3 * {2*(a+b)-b} = {3*(2*(a+b)-b)}.",
            f"{3*(2*(a+b)-b)} + {a} - 5 = {v}."]),
    "f": dict(
        name="plok", depth=2,  # per-path depth <=2; the load is the branch, not the depth
        rule="To compute the plok of two numbers: if the first is greater than the second, "
             "take twice their difference and add seven; otherwise take three times the "
             "difference the other way and add two.",
        fn=lambda a, b: 2 * (a - b) + 7 if a > b else 3 * (b - a) + 2,
        steps=lambda a, b, v: (
            [f"{a} > {b}, so use the first branch.",
             f"{a} - {b} = {a-b}; 2 * {a-b} = {2*(a-b)}.",
             f"{2*(a-b)} + 7 = {v}."] if a > b else
            [f"{a} <= {b}, so use the second branch.",
             f"{b} - {a} = {b-a}; 3 * {b-a} = {3*(b-a)}.",
             f"{3*(b-a)} + 2 = {v}."])),
    "g": dict(
        name="trewb", depth=1,  # same latent rule as tier b; the load is the wrapping
        rule=None,  # NEVER stated: the point of the tier
        fn=lambda a, b: a + b + 1,
        steps=lambda a, b, v: [f"{a} + {b} = {a+b}.", f"{a+b} + 1 = {v}."]),
})
