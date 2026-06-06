"""Perturbation form banks for atomic-repair v2 — all 9 cells (K/R/H x Aug/Abl/Cor).

Reuses the DETERMINISTIC perturbation logic from probing's build_natural_variants
(string-template injection: hint / paraphrase / wrong-claim / scaffold / ...), but
applied to the synthetic world so the knowledge-injection premise holds.

Each cell's perturbation is a function turning a base item into a `problem` string.
Train/eval phrasings are disjoint (held-out FORM axis), tagged with form_id.

Cell semantics (paper Table 1):
  Aug = add a supporting cue (hint / scaffold / explicit bridge fact)
  Abl = remove a cue / change surface (paraphrase / rule-removal / mask bridge)
  Cor = inject a wrong competing signal (wrong claim / wrong step / wrong bridge)

The `tentative_answer` and `repair_skill`/`diagnosis` are set by generate_v2 per
CELL_SPEC_V2 (below). This module only supplies the surface phrasings + builders.
"""
from __future__ import annotations

# --------------------------------------------------------------------------- #
# 9-cell spec: diagnosis + repair_skill (= paper Table 1 candidate intervention)
# --------------------------------------------------------------------------- #
CELL_SPEC_V2 = {
    # Knowledge
    "K-Aug": dict(domain="K", pert="Aug", diagnosis="knowledge_not_surfaced",
                  repair_skill="retrieval_cueing", should_repair=True),
    "K-Abl": dict(domain="K", pert="Abl", diagnosis="paraphrase_fragile",
                  repair_skill="paraphrase_robust_recall", should_repair=True),
    "K-Cor": dict(domain="K", pert="Cor", diagnosis="wrong_factual_claim",
                  repair_skill="contradiction_check", should_repair=True),
    # Reasoning
    "R-Aug": dict(domain="R", pert="Aug", diagnosis="needs_decomposition",
                  repair_skill="decomposition_scaffold", should_repair=True),
    "R-Abl": dict(domain="R", pert="Abl", diagnosis="rule_not_grounded",
                  repair_skill="rule_reinjection", should_repair=True),
    "R-Cor": dict(domain="R", pert="Cor", diagnosis="wrong_intermediate",
                  repair_skill="step_verification", should_repair=True),
    # Hybrid
    # v2.1 fix: H-Aug PROVIDES the bridge fact in the prompt, so the repair is to
    # USE the given fact, not retrieve a missing one. Old label bridge_retrieval was
    # semantically misaligned with the cell operation (caused D to second-guess a
    # given cue and drop to 45%). Corrected to use_provided_bridge_fact.
    "H-Aug": dict(domain="H", pert="Aug", diagnosis="bridge_fact_provided",
                  repair_skill="use_provided_bridge_fact", should_repair=True),
    "H-Abl": dict(domain="H", pert="Abl", diagnosis="bridge_entity_missing",
                  repair_skill="provide_bridge_entity", should_repair=True),
    "H-Cor": dict(domain="H", pert="Cor", diagnosis="wrong_bridge_contamination",
                  repair_skill="source_verification", should_repair=True),
    "Clean": dict(domain="-", pert="-", diagnosis="no_failure_detected",
                  repair_skill="keep_answer", should_repair=False),
}

CELLS_9 = ["K-Aug", "K-Abl", "K-Cor", "R-Aug", "R-Abl", "R-Cor", "H-Aug", "H-Abl", "H-Cor"]

# --------------------------------------------------------------------------- #
# Perturbation phrasing banks, split train/eval. Placeholders per cell:
#   K-Aug  {hint}  K-Abl {q_para}  K-Cor {wrong}
#   R-Aug  {scaffold}  R-Abl (rule removed, no extra)  R-Cor {wrong_step}
#   H-Aug  {bridge_fact}  H-Abl (bridge masked)  H-Cor {wrong_bridge_sentence}
# We store sentence templates with a {q} slot for the base question and a payload
# slot. generate_v2 fills payloads (computed from the item).
# --------------------------------------------------------------------------- #

AUG_HINT = {  # K-Aug: add a retrieval cue (no gold leak)
    "train": [
        {"id": "kaug_T1", "tpl": "Hint: recall the relevant stored fact about this entity. {q}"},
        {"id": "kaug_T2", "tpl": "Hint: this is a direct factual lookup. {q}"},
    ],
    "eval": [
        {"id": "kaug_E1", "tpl": "Cue: bring to mind what you know about this entity. {q}"},
        {"id": "kaug_E2", "tpl": "Reminder: this asks for a single stored fact. {q}"},
    ],
}

ABL_PARA = {  # K-Abl: paraphrase the question (change surface)
    "train": [
        {"id": "kabl_T1", "tpl": "Rephrased: {q}"},
        {"id": "kabl_T2", "tpl": "In other words, {q}"},
    ],
    "eval": [
        {"id": "kabl_E1", "tpl": "Put another way: {q}"},
        {"id": "kabl_E2", "tpl": "Stated differently, {q}"},
    ],
}

COR_CLAIM = {  # K-Cor: inject a wrong competing claim
    "train": [
        {"id": "kcor_T1", "tpl": "Some sources claim the answer is {wrong}. {q}"},
        {"id": "kcor_T2", "tpl": "It is sometimes said the answer is {wrong}. {q}"},
    ],
    "eval": [
        {"id": "kcor_E1", "tpl": "A common error gives the answer as {wrong}. {q}"},
        {"id": "kcor_E2", "tpl": "You may have been told the answer is {wrong}. {q}"},
    ],
}

R_AUG_SCAFFOLD = {  # R-Aug: provide decomposition scaffold (no answer)
    "train": [
        {"id": "raug_T1", "tpl": "Step 1: identify the operands. Step 2: apply the rule's operations in order. {q}"},
        {"id": "raug_T2", "tpl": "Work it out stepwise: first the inner operation, then the outer. {q}"},
    ],
    "eval": [
        {"id": "raug_E1", "tpl": "Break it down: extract the two numbers, then run each step of the rule. {q}"},
        {"id": "raug_E2", "tpl": "Proceed in stages: compute the first step, then finish the rule. {q}"},
    ],
}

R_COR_STEP = {  # R-Cor: inject a wrong intermediate step
    "train": [
        {"id": "rcor_T1", "tpl": "Note: an intermediate result of {wrong_mid} has been suggested. {q}"},
        {"id": "rcor_T2", "tpl": "Someone computed an intermediate value of {wrong_mid}. {q}"},
    ],
    "eval": [
        {"id": "rcor_E1", "tpl": "A draft solution used {wrong_mid} as an intermediate. {q}"},
        {"id": "rcor_E2", "tpl": "An intermediate step was claimed to be {wrong_mid}. {q}"},
    ],
}

H_AUG_BRIDGE = {  # H-Aug: provide the bridge fact explicitly
    "train": [
        {"id": "haug_T1", "tpl": "Note: {bridge_fact} {q}"},
        {"id": "haug_T2", "tpl": "Background: {bridge_fact} {q}"},
    ],
    "eval": [
        {"id": "haug_E1", "tpl": "Aside: {bridge_fact} {q}"},
        {"id": "haug_E2", "tpl": "For reference: {bridge_fact} {q}"},
    ],
}

H_COR_BRIDGE = {  # H-Cor: inject a wrong bridge
    "train": [
        {"id": "hcor_T1", "tpl": "It is widely said that {wrong_bridge_clause}. {q}"},
        {"id": "hcor_T2", "tpl": "Many assume that {wrong_bridge_clause}. {q}"},
    ],
    "eval": [
        {"id": "hcor_E1", "tpl": "Some catalogues state that {wrong_bridge_clause}. {q}"},
        {"id": "hcor_E2", "tpl": "A common rumour holds that {wrong_bridge_clause}. {q}"},
    ],
}

# K-Abl / R-Abl / H-Abl phrasings that don't need a payload still need form ids
# for the disjointness check; R-Abl removes the rule, H-Abl masks the bridge.
ABL_PLAIN = {
    "train": [{"id": "abl_T1", "tpl": "{q}"}, {"id": "abl_T2", "tpl": "Consider: {q}"}],
    "eval": [{"id": "abl_E1", "tpl": "{q}"}, {"id": "abl_E2", "tpl": "Take this: {q}"}],
}

# Map each cell to its phrasing bank.
CELL_BANK = {
    "K-Aug": AUG_HINT, "K-Abl": ABL_PARA, "K-Cor": COR_CLAIM,
    "R-Aug": R_AUG_SCAFFOLD, "R-Abl": ABL_PLAIN, "R-Cor": R_COR_STEP,
    "H-Aug": H_AUG_BRIDGE, "H-Abl": ABL_PLAIN, "H-Cor": H_COR_BRIDGE,
    "Clean": ABL_PLAIN,
}


def all_form_ids(split: str) -> set[str]:
    out = set()
    for bank in (AUG_HINT, ABL_PARA, COR_CLAIM, R_AUG_SCAFFOLD, R_COR_STEP,
                 H_AUG_BRIDGE, H_COR_BRIDGE, ABL_PLAIN):
        for e in bank.get(split, []):
            out.add(e["id"])
    return out


def _assert_disjoint():
    for name, bank in [("AUG_HINT", AUG_HINT), ("ABL_PARA", ABL_PARA), ("COR_CLAIM", COR_CLAIM),
                       ("R_AUG_SCAFFOLD", R_AUG_SCAFFOLD), ("R_COR_STEP", R_COR_STEP),
                       ("H_AUG_BRIDGE", H_AUG_BRIDGE), ("H_COR_BRIDGE", H_COR_BRIDGE),
                       ("ABL_PLAIN", ABL_PLAIN)]:
        tr = {e["id"] for e in bank["train"]}
        ev = {e["id"] for e in bank["eval"]}
        assert not (tr & ev), f"{name} train/eval overlap"


_assert_disjoint()
