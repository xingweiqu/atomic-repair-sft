"""Claim-introduction phrasings for Corrupt-cell injections (v3.1 decoupling fix).

v3 used a single hardcoded intro ("Some notes say ..." / "Some sources say ...") AND
lowercased the H-Cor clause, so the *surface marker* perfectly predicted *falsity*
(100% of marked claims were false). A model could route update_decision by template
alone, never verifying. v3.1 fixes this by:
  (1) a pool of >=8 intro phrasings (train/eval disjoint),
  (2) NO forced lowercasing (clause keeps normal case, like a true support fact),
  (3) the same intros are used for BOTH true and false planted claims (Cor-True /
      Cor-False), so the marker is statistically INDEPENDENT of truth.

`{c}` is the claim clause (e.g. "Silver River was written by Anton Hale" or a value).
Some phrasings are bare assertions with no hedging intro at all, to further break the
"hedge => false" shortcut.
"""
from __future__ import annotations

import random

CLAIM_INTROS = {
    "train": [
        "Some notes say {c}.",
        "I read somewhere that {c}.",
        "According to my notes, {c}.",
        "Apparently {c}.",
        "{c}.",                                  # bare assertion, no hedge
        "A source I saw claims {c}.",
    ],
    "eval": [
        "I was told that {c}.",
        "My notes indicate {c}.",
        "It says here that {c}.",
        "Reportedly {c}.",                       # bare-ish
        "Someone mentioned {c}.",
    ],
}


def claim_sentence(rng: random.Random, split: str, clause: str) -> str:
    """Wrap a claim clause in a randomly chosen intro. Case of `clause` is preserved
    (no forced lowercasing) so case cannot be used as a falsity cue."""
    return rng.choice(CLAIM_INTROS[split]).format(c=clause)


def _assert_disjoint():
    assert not (set(CLAIM_INTROS["train"]) & set(CLAIM_INTROS["eval"])), \
        "claim intro train/eval overlap"
    assert len(CLAIM_INTROS["train"]) >= 6 and len(CLAIM_INTROS["eval"]) >= 5


_assert_disjoint()
