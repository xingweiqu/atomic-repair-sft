"""Natural user-scenario templates for v3 / v3.1.

Wraps a bare oracle question in user-like phrasing. Each relation family and the
reasoning domain get several scenario templates, split train/eval so the held-out
evaluation tests unseen scenario surface. v3.1 expands the EVAL banks to >=8 per
family and the underspecified (abstain) eval bank to >=10, so eval surface diversity
is no longer thin. These are the deterministic SEED layer; scenario_api.py can
optionally paraphrase further via an LLM (cached), but the pipeline runs fully on seeds.

Placeholders: {q} is the bare question. Templates must NOT contain the gold answer.
"""
from __future__ import annotations

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
            "This title came up in a reading group. {q}",
            "I spotted this book in a secondhand shop. {q}",
            "Someone recommended this novel to me. {q}",
            "I'm building a reading list and need a detail. {q}",
            "This book was mentioned in a podcast I follow. {q}",
            "I'm curious after finishing this novel. {q}",
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
            "I'm comparing destinations for a holiday. {q}",
            "A relative is relocating there soon. {q}",
            "I'm prepping for a business trip. {q}",
            "This place came up in a travel vlog. {q}",
            "I'm helping plan a group tour. {q}",
            "I need to exchange money before going there. {q}",
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
            "I'm preparing a case study on this business. {q}",
            "A friend mentioned this company at dinner. {q}",
            "I saw this firm in an industry newsletter. {q}",
            "I'm vetting this company as a vendor. {q}",
            "This business was featured in a profile I read. {q}",
            "I'm curious who started this company. {q}",
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
            "This product showed up in a review I watched. {q}",
            "I'm evaluating this item for a purchase. {q}",
            "A colleague recommended this product. {q}",
            "I'm researching brands before buying. {q}",
            "This item was on a gift guide I saw. {q}",
            "I'm curious about who makes this. {q}",
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
            "I saw a print of this work and got curious. {q}",
            "A friend posted this artwork online. {q}",
            "I'm preparing notes for a museum visit. {q}",
            "This piece was discussed in an art class. {q}",
            "I'm writing a caption for this work. {q}",
            "I came across this artwork in a book. {q}",
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
            "I saw this scientist's name in an article. {q}",
            "A documentary covered this researcher. {q}",
            "I'm compiling profiles of scientists. {q}",
            "This person came up in a class discussion. {q}",
            "I'm curious about this researcher's work. {q}",
            "A colleague cited this scientist. {q}",
        ],
    },
}

REASONING_SCENARIOS = {
    "train": [
        "I'm working through a problem set and need this. {q}",
        "A task at work requires this calculation. {q}",
        "Double-checking my homework. {q}",
    ],
    "eval": [
        "I'm verifying a result for a report. {q}",
        "Quick sanity check on a computation. {q}",
        "I need this number for a spreadsheet. {q}",
        "Working through an exercise and stuck here. {q}",
        "Confirming a figure before I submit. {q}",
        "A quick calculation came up at work. {q}",
        "I'm reviewing someone's math. {q}",
        "Need to settle this number quickly. {q}",
    ],
}

# Underspecified / missing-anchor scenarios (abstain class). Drop the anchor entirely;
# correct action is to abstain. >=10 eval phrasings (v3.1 fix: was only 2).
UNDERSPECIFIED_SCENARIOS = {
    "train": [
        "I was reading something earlier and forgot the title. What nationality is the author?",
        "Someone mentioned a city to me but I didn't catch which one. What currency do they use there?",
        "A company came up in conversation. Where is its founder from?",
        "There's this product a friend told me about. Which country is the maker based in?",
        "I heard about a book recently but can't recall its name. Where is the author from?",
        "A place was recommended to me but I forgot which. What money do they use?",
    ],
    "eval": [
        "I saw an artwork somewhere recently. What country is the artist from?",
        "A scientist was referenced but the name slipped my mind. What field is their discovery in?",
        "Someone showed me a painting but I forgot the title. Where was the artist born?",
        "There was this firm mentioned in a meeting. What nationality is the founder?",
        "A gadget came up but I can't remember which. Which country makes it?",
        "I read about a researcher but lost the name. What's their field?",
        "A novel was suggested to me; the title escapes me. What's the author's nationality?",
        "Someone named a town I should visit but I forgot it. What currency is used there?",
        "A company was praised online but I missed its name. Where is it headquartered?",
        "An exhibit featured a piece I liked but I didn't note the artist. What country are they from?",
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
        assert len(d["eval"]) >= 8, f"{fam} eval has <8 templates"
    assert not (set(REASONING_SCENARIOS["train"]) & set(REASONING_SCENARIOS["eval"]))
    assert not (set(UNDERSPECIFIED_SCENARIOS["train"]) & set(UNDERSPECIFIED_SCENARIOS["eval"]))
    assert len(UNDERSPECIFIED_SCENARIOS["eval"]) >= 10, "abstain eval has <10 templates"


_assert_disjoint()
