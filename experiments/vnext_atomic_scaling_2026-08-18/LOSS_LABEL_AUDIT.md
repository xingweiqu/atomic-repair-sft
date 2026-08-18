# LOSS_LABEL_AUDIT — can each atomic axis carry a continuous probabilistic diagnosis? (C-48 Phase A)

Audited against `prescription/gate1/eval500_proto.jsonl` (529 families; condition counts: original/distractor/format/wc_light/wc_attempt/cc_light/cc_attempt ×529, insufficient/insuf_ctr/suff_ctr ×249, paraphrase ×50, wc_nl/cc_nl ×100). Every row carries `gold`; candidate rows carry `meta.cand`; contract rows end with an exact required output form. No new benchmark is built.

**Verdict: 6 of 7 axes support well-defined teacher-forced loss diagnosis (5 with margins); free-text endpoints keep behavioral scores only.**

| # | Axis (proto conditions) | Canonical target? | Loss quantities | Margin? | Flag |
|---|---|---|---|---|---|
| 1 | Original (`original`) | YES — gold integer; scaffold `Final answer: <gold>` (declared instrument) | gold-answer NLL `L_orig` (mask scaffold, score gold tokens); per-token NLL | no explicit wrong alternative | ok |
| 2 | Paraphrase (`paraphrase`, n=50 aux) | YES — same gold | `L_para`, ΔL_para = L_para − L_orig (same family) | — | `aux_subset_n50` |
| 3 | Distractor (`distractor`) | YES for gold NLL | `L_dist`, ΔL_dist = L_dist − L_orig | **NO canonical planted-wrong** (meta has k/item, no unique wrong answer) → margin `loss_not_well_defined` | margin flagged |
| 4 | Wrong Candidate (`wc_light`/`wc_attempt`) | YES — contract `DECISION=<..>\nFINAL_ANSWER=<int>`; correct decision = REVISE; `meta.cand` = wrong value | decision NLL `L(DECISION=REVISE)`; final gold NLL; **decision margin** = logp(REVISE)−logp(KEEP); **candidate margin** = logp(FINAL=gold)−logp(FINAL=cand) | YES ×2 | ok |
| 5 | Correct Candidate (`cc_light`/`cc_attempt`) | YES — correct decision = KEEP | decision NLL `L(DECISION=KEEP)`; final gold NLL; decision margin = logp(KEEP)−logp(REVISE) | YES | ok |
| 6 | Insufficient Information (`insuf_ctr`; paired `suff_ctr`) | YES — contract `STATUS=<..>`; insuf gold = INSUFFICIENT (+FINAL=NULL), suff gold = ANSWERABLE | status NLL; **status margin** = logp(correct)−logp(incorrect status) | YES | ok |
| 7 | Structured Output (`format`) | YES — exact one-line `ANSWER=<integer>` | **contract-token NLL** (the `ANSWER=` skeleton tokens) and **semantic NLL** (the integer tokens) computed separately by token mask over one canonical completion | value margin possible in principle; not required | ok |
| — | Free-text variants (`insufficient` free-form, `wc_nl`, `cc_nl`) | NO unique legal target (any abstention/NL phrasing valid) | behavioral score only | — | `loss_not_well_defined` |
| — | Assistance S/R probes | before/after gold NLL (diagnostic layer only, never trained) | ΔL_assist | — | diagnostic-only |

## Declared instrument decisions (fixed before any extraction; identical across all models)

1. **Immediate-contract NLL.** For contract axes the teacher-forced target is the required final lines as the immediate completion (models may normally emit reasoning first). This measures the model's direct propensity toward the correct contract output; it is a declared instrument, comparable across models and doses, not a claim about generation behavior. Behavioral scores remain the generation-level readout.
2. **Answer scaffold.** Non-contract axes (original/paraphrase/distractor) use the fixed scaffold `Final answer: <gold>`; NLL is computed on the gold tokens only (scaffold masked). Scaffold string is part of ATOMIC_LOSS_SCHEMA.json and never varies by model.
3. **Chat template.** Each model's own chat template is applied (`add_generation_prompt=True`, thinking disabled where supported); the target is scored as the assistant completion.
4. **No fake losses.** Free-text endpoints keep behavioral scores; they enter no loss-based fit and no loss-based objective.

## Answer to the Phase-A question

- Continuous probabilistic diagnosis is well-defined for **6/7 axes** (all but the free-text abstention/NL variants), with **explicit margins on 3 axes** (candidate decision ×2, answerability status) plus a candidate-value margin.
- The three-way separation the directive asks for (correct-but-confidence-collapsing / shifted-but-positive-margin / margin-flipped) is measurable on wc/cc/insuf-suff via (behavioral score, margin sign, margin magnitude) triples, and on distractor via (score, ΔL) pairs.
