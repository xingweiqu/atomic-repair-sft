# PAPER_OUTLINE_V0 — Predicting SFT Recipes from Response Profiles

## 1. Introduction
- Q: why is "what to train next" an open decision problem; why clean benchmarks can't answer it.
- Figures: Fig 1. Claims: #1 (heuristic paradox as hook), thesis sentence, three contributions C1–C3.
- Appendix pointers: none.

## 2. From Evaluation to SFT Response Profiles (setup)
- Q: how do we measure responses credibly? Taxonomy (3 domains × 4 intervention families + replay control); 7 evaluation conditions; matched budget (constant target tokens AND optimizer updates); hierarchical utility U; constraint set; preregistration protocol (freeze-before-train, retraction ledger).
- Figures: none main (schema tables). Claims: #13 (small-eval artifacts → why 529-fam).
- Appendix: contracts, audit ledgers (1000-pair ANS audit, CREPE gate), scorer self-tests, template-audit (margin) as diagnostic layer, S/R probes definition.

## 3. Heterogeneous and Domain-Dependent SFT Responses
- Q: what are the response shapes, and do they stay in-domain?
- Figures: Fig 2, Fig 3. Claims: #2, #3 (LODO), #4.
- Appendix: full endpoint grids, evidence weak-in-all-domains, K/IF sparse tables, SVAMP external holdout, margin-v2 audit.

## 4. Single-Component Responses Do Not Compose Additively
- Q: does the natural additive hypothesis survive a preregistered test? (No.)
- Figures: Fig 4a. Claims: #5, #6.
- Appendix: six-arm compositions, frozen spec, per-branch vectors.

## 5. Carrier Dependence and Diversity-Conditioned Composition
- Q: what structure explains the failure?
- Figures: Fig 4b. Claims: #7, #8, #9 (Qwen-discovered corrections; wording discipline).
- Appendix: rescue design freeze, residual algebra, correction model.

## 6. Prospective Recipe Prediction on Held-Out Llama
- Q: does the corrected frozen model prescribe out-of-family?
- Figures: Fig 5. Claims: #10, #11, #12.
- Appendix: calibration rule freeze, prediction freeze JSON, verdict table, per-seed audit, retention table, base-R artifact note.

## 7. Discussion / Limitations
- One held-out family; magnitude calibration (structured underestimation of diverse mixtures) as the open modeling problem; coarse dose resolution of the diversity regime; U design choices (alternative-aggregation sensitivity: *planned appendix analysis, not yet generated*); single-seed direction-grade sparse grids; four intervention families only.

## 8. Related Work
- Data mixing/selection for LM training; scaling-laws framing (contrast: local response vs loss power laws); behavioral evaluation & robustness suites; reasoning faithfulness interventions (RFEval as measurement-side neighbor; we supply the training-side dose–response); abstention/calibration training.

## 9. Conclusion
- "SFT scales locally, but composes conditionally" + the prescription pipeline as the deliverable.

## Main tables
- T1: taxonomy + budgets; T2: Qwen six-arm open (predicted vs actual, DQ note); T3: Llama final (frozen vs actual, per-seed, constraints); T4: retention table.
