"""Natural user-scenario templates for v3.

Wraps a bare oracle question in user-like phrasing. Each relation family and the
reasoning domain get several scenario templates, split train/eval so the held-out
evaluation tests unseen scenario surface. These are the deterministic SEED layer;
scenario_api.py can optionally paraphrase them further via an LLM (cached), but the
pipeline runs fully on these seeds with no API.

Placeholders: {q} is the bare question; {head}/{a}/{b} are entities/operands when a
template wants to mention them naturally. Templates must NOT contain the gold answer.
"""
from __future__ import annotations

# Per relation family: train/eval-disjoint scenario wrappers around {q}.
FAMILY_SCENARIOS: dict[str, dict[str, list[str]]] = {
    "book_author_nationality": {
        "train": [
            "I'm reading a novel and got curious about its author. {q}",
            "For a book club, someone asked me this and I want to get it right. {q}",
            "I came across this book at the library. {q}",
        ],
        "eval": [
            "A friend lent me this novel and I started wondering about the writer. {q}",
            "I'm writing up some notes on this book. {q}",
        ],
    },
    "city_country_currency": {
        "train": [
            "I'm planning a trip and sorting out logistics. {q}",
            "Booking travel and need to handle money correctly. {q}",
            "A colleague is visiting there next month and asked me. {q}",
        ],
        "eval": [
            "I'm putting together a travel budget. {q}",
            "Someone on a forum asked about visiting there. {q}",
        ],
    },
    "company_founder_nationality": {
        "train": [
            "I'm researching this company for a report. {q}",
            "Came up in a business article I was reading. {q}",
            "A coworker was curious about the company's origins. {q}",
        ],
        "eval": [
            "I'm doing background reading on this firm. {q}",
            "This came up while I was looking into the company. {q}",
        ],
    },
    "product_company_country": {
        "train": [
            "I'm comparing products and want to know who's behind this one. {q}",
            "Saw this product online and got curious. {q}",
            "A friend asked me where this product comes from. {q}",
        ],
        "eval": [
            "I'm checking the supply chain for this product. {q}",
            "While shopping I wondered about this item. {q}",
        ],
    },
    "artwork_artist_country": {
        "train": [
            "I saw this piece at a gallery and want to learn more. {q}",
            "For an art history note, I'm tracking down details. {q}",
            "A docent mentioned this work and I got curious. {q}",
        ],
        "eval": [
            "I'm cataloguing some artworks. {q}",
            "This piece came up in a documentary. {q}",
        ],
    },
    "scientist_discovery_field": {
        "train": [
            "I'm reading about this researcher's work. {q}",
            "Came up in a science podcast I was listening to. {q}",
            "A student asked me about this scientist. {q}",
        ],
        "eval": [
            "I'm preparing a short bio of this scientist. {q}",
            "This researcher was mentioned in a lecture. {q}",
        ],
    },
}

# Reasoning (invented operations) scenario wrappers.
REASONING_SCENARIOS = {
    "train": [
        "I'm working through a problem set and need this. {q}",
        "A task at work requires this calculation. {q}",
        "Double-checking my homework. {q}",
    ],
    "eval": [
        "I'm verifying a result for a report. {q}",
        "Quick sanity check on a computation. {q}",
    ],
}

# Underspecified / missing-anchor scenarios (the abstain class). These deliberately
# DROP the anchor so no specific entity is identified; the correct action is to abstain.
UNDERSPECIFIED_SCENARIOS = {
    "train": [
        "I was reading something earlier and forgot the title. What nationality is the author?",
        "Someone mentioned a city to me but I didn't catch which one. What currency do they use there?",
        "A company came up in conversation. Where is its founder from?",
        "There's this product a friend told me about. Which country is the maker based in?",
    ],
    "eval": [
        "I saw an artwork somewhere recently. What country is the artist from?",
        "A scientist was referenced but the name slipped my mind. What field is their discovery in?",
    ],
}


def family_scenarios(family: str, split: str) -> list[str]:
    return FAMILY_SCENARIOS[family][split]


def reasoning_scenarios(split: str) -> list[str]:
    return REASONING_SCENARIOS[split]


def underspecified_scenarios(split: str) -> list[str]:
    return UNDERSPECIFIED_SCENARIOS[split]


def _assert_disjoint():
    for fam, d in FAMILY_SCENARIOS.items():
        assert not (set(d["train"]) & set(d["eval"])), f"{fam} scenario train/eval overlap"
    assert not (set(REASONING_SCENARIOS["train"]) & set(REASONING_SCENARIOS["eval"]))
    assert not (set(UNDERSPECIFIED_SCENARIOS["train"]) & set(UNDERSPECIFIED_SCENARIOS["eval"]))


_assert_disjoint()
