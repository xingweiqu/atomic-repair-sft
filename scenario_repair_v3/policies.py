"""Answer-update policies for scenario-repair v3.

v3's central abstraction. The 9 atomic cells (K/R/H x Aug/Abl/Cor) are demoted to
*failure injectors* — ways of producing a broken item — and are NOT the unit of
training or evaluation. The unit is the **answer-update policy**: given a problem
and a tentative answer, what should the model DO to it?

Seven policies, grouped by a top-level update_decision:
  keep                 -> keep_answer (no repair; the tentative answer is right)
  update               -> override_wrong_claim / verify_bridge / verify_step /
                          recompute / use_provided_support
  retrieve_or_abstain  -> retrieve_or_abstain (cannot fix internally; ask/abstain)

Each policy carries an `action` phrase used to build the actionized trace
("Action: <action>. ..."), which v2.1 showed is the supervision that actually works.
"""
from __future__ import annotations

# update_decision categories
KEEP = "keep"
UPDATE = "update"
ABSTAIN = "retrieve_or_abstain"

POLICIES: dict[str, dict] = {
    "keep_answer": {
        "decision": KEEP,
        "action": "keep answer",
        "desc": "The tentative answer is already supported by the known facts; do not change it.",
    },
    "override_wrong_claim": {
        "decision": UPDATE,
        "action": "override wrong claim",
        "desc": "A planted claim contradicts a known one-hop fact; reject it and use the correct fact.",
    },
    "verify_bridge": {
        "decision": UPDATE,
        "action": "verify bridge",
        "desc": "A planted bridge entity is wrong; verify the true bridge, then chain to the answer.",
    },
    "verify_step": {
        "decision": UPDATE,
        "action": "verify step",
        "desc": "A planted intermediate result is wrong; recompute the step correctly.",
    },
    "recompute": {
        "decision": UPDATE,
        "action": "recompute from known facts",
        "desc": "Re-derive the answer from facts/rules already known: run the rule on the "
                "given operands, or recall the same fact under a new phrasing.",
    },
    "use_provided_support": {
        "decision": UPDATE,
        "action": "use provided support",
        "desc": "A supporting fact is given in the problem; apply it directly without re-doubting it.",
    },
    "retrieve_or_abstain": {
        "decision": ABSTAIN,
        "action": "ask for clarification",
        "desc": "The problem omits the anchor needed to answer; the answer cannot be safely produced "
                "from internal knowledge, so abstain and ask for clarification.",
    },
}

POLICY_NAMES = list(POLICIES.keys())
# Policies that are the per-operator induction targets in Experiment 2 (exclude keep,
# which is the over-repair control rather than an inducible repair operator).
OPERATOR_POLICIES = [p for p in POLICY_NAMES if POLICIES[p]["decision"] != KEEP]


def decision_of(policy: str) -> str:
    return POLICIES[policy]["decision"]


def action_of(policy: str) -> str:
    return POLICIES[policy]["action"]


# --------------------------------------------------------------------------- #
# Map the v2 9-cell failure injectors to v3 answer-update policies.
# The cell is HOW the item was broken; the policy is WHAT to do about it.
# --------------------------------------------------------------------------- #
CELL_TO_POLICY = {
    "K-Aug": "use_provided_support",   # a retrieval cue is given -> use it / surface fact
    "K-Abl": "recompute",              # paraphrased question, same fact -> recall (re-derive recall)
    "K-Cor": "override_wrong_claim",   # planted wrong claim -> override
    "R-Aug": "recompute",              # decomposition scaffold -> recompute the rule
    "R-Abl": "recompute",              # rule not restated -> recall rule + recompute
    "R-Cor": "verify_step",            # wrong intermediate -> verify the step
    "H-Aug": "use_provided_support",   # bridge fact given -> use provided support
    "H-Cor": "verify_bridge",          # wrong bridge planted -> verify bridge
    "Clean": "keep_answer",            # nothing wrong -> keep
    # NEW v3 injector (no v2 cell): underspecified / missing anchor -> abstain
    "U-Abl": "retrieve_or_abstain",
    # v3.1 decoupling: Cor-True variants plant a claim that is actually TRUE; the marker
    # ("Some notes say ...") therefore no longer predicts falsity. Correct action is to
    # verify and KEEP. This forces the model to check the claim, not route by template.
    "K-Cor-True": "keep_answer",       # planted claim is TRUE -> verify, keep
    "H-Cor-True": "keep_answer",       # planted bridge is TRUE -> verify, keep
}

# K-Abl re-mapped: paraphrase robustness is "recall the same fact"; we fold it into the
# update family as a recall/recompute action (no distinct policy needed). Note H-Abl
# (masked bridge, recoverable) is handled as a recover-anchor case under
# retrieve_or_abstain only when truly unrecoverable; the recoverable masked-bridge case
# is treated as verify_bridge-style recovery. See generate_v3 for exact wiring.


def all_policies() -> list[str]:
    return POLICY_NAMES
