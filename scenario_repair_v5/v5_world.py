"""v5-clean world: counterfactual two-hop relations. ALL entity values are coined nonsense
(absent from any pretraining corpus), facts are provided in context, questions are two-hop
(head -> bridge -> tail). The base MUST read context to answer; it cannot memorize.

Designed to fix v3's fatal flaws (oracle leak on a 341-triple world): the coinage pool is
effectively unbounded, so train/eval can be holdout at the (head,rel,tail) COMBINATION level
with a triple count an order of magnitude larger than any 30-epoch SFT can default-write.
"""
from __future__ import annotations

import random

# coinage: onset + nucleus + coda syllables -> nonsense words not in real corpora
_ON = ["b", "d", "f", "g", "k", "l", "m", "n", "p", "r", "s", "t", "v", "z",
       "br", "dr", "gl", "kr", "pl", "tr", "sk", "sn", "vr", "zl", "th", "shp"]
_NU = ["a", "e", "i", "o", "u", "ae", "ia", "io", "ou", "or", "el", "un", "ar"]
_CO = ["", "n", "r", "l", "s", "x", "th", "nd", "rk", "ng", "ll", "ss", "st"]
# pool per 2-syllable word ~ (26*13*13)^2 ≈ 1.9e7 — effectively unbounded.


def _syl(rng):
    return rng.choice(_ON) + rng.choice(_NU) + rng.choice(_CO)


def coin(rng, n=2):
    return "".join(_syl(rng) for _ in range(n)).capitalize()


# four relation families (real schema, counterfactual values)
FAMILIES = [
    dict(name="book", rel1="was written by", rel2="is a citizen of",
         bridge_role="author", q="What nationality is the author of {head}?"),
    dict(name="city", rel1="is located in", rel2="officially uses",
         bridge_role="province", q="What currency does the province containing {head} use?"),
    dict(name="device", rel1="is produced by", rel2="primarily sources",
         bridge_role="manufacturer", q="What material does the manufacturer of {head} source?"),
    dict(name="song", rel1="is performed by", rel2="is funded by",
         bridge_role="ensemble", q="Who funds the ensemble performing {head}?"),
]


def coin_unique(rng, n, used, syl=2):
    out = []
    while len(out) < n:
        w = coin(rng, syl)
        if w not in used:
            used.add(w)
            out.append(w)
    return out


def build_world(rng, chains_per_family, tails_per_family, used=None):
    """Return list of chains {family, fam, head, bridge, tail}. head/bridge unique per chain;
    tail drawn from a per-family pool (many-to-one, like a real nationality/currency).
    Pass a shared `used` set across splits to guarantee GLOBAL coinage uniqueness (zero
    train/eval entity overlap)."""
    used = set() if used is None else used
    chains = []
    for fam in FAMILIES:
        tails = coin_unique(rng, tails_per_family, used, syl=2)
        heads = coin_unique(rng, chains_per_family, used, syl=2)
        bridges = coin_unique(rng, chains_per_family, used, syl=2)
        for h, b in zip(heads, bridges):
            chains.append(dict(family=fam["name"], fam=fam, head=h, bridge=b,
                               tail=rng.choice(tails), tails=tails))
    rng.shuffle(chains)
    return chains


def context_full(c):
    f = c["fam"]
    return [f"{c['head']} {f['rel1']} {c['bridge']}.",
            f"{c['bridge']} {f['rel2']} {c['tail']}."]


def chain_triples(c):
    f = c["fam"]
    return [[c["head"], f["rel1"], c["bridge"]], [c["bridge"], f["rel2"], c["tail"]]]


def question(c):
    return c["fam"]["q"].format(head=c["head"])


if __name__ == "__main__":
    rng = random.Random(0)
    w = build_world(rng, 5, 3)
    for c in w[:4]:
        print(c["family"], "|", question(c), "| gold:", c["tail"])
        print("   ctx:", context_full(c))
