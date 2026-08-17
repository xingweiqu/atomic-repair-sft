# RQ_MAP_V1 — the four research questions, fully specified

**V2.1 (C-44 patch): RQ1 no longer asks "how much" (no formal quantification metric exists — we show what structure exists and that it decomposes); RQ2 renamed Atomic Repairability with repairability as the formal object; evidence/answerability wording corrected.**

All evidence cells point to committed artifacts in PAPER_EVIDENCE_FREEZE/ (or ledgered qc/ files). No new experiments; retracted small-eval results never re-enter.

---

## RQ1 — Atomic Diagnosis

**1. Scientific question.** What atomic behavioral failure structure is hidden by aggregate benchmark performance? (Method form: can aggregate benchmark performance be decomposed into atomic behavioral failure structure?) Does "80% accuracy" (illustrative figure, not an experimental number) denote a uniform competence, or a mixture of stable competence and fragile success? We answer the structural question; we do not commit to a formal "how much is hidden" quantification.

**2. Hypothesis.** Aggregate scores conflate behaviorally distinct failure modes that controlled single-condition perturbations can separate: the same clean-solved item can fail under paraphrase, distractor, wrong/correct candidate, insufficient information, or structured-output demands, and these failures have different profiles across models and domains.

**3. Experiments answering it.**
- Construction of the controlled atomic evaluation suite: 7 evaluation axes instantiated per applicable task form across 3 domains via an applicability matrix (not a forced Cartesian product); 529 evaluation families (answerability branch 249) [eval500 build_stats_500.json].
- Decision contracts (DECISION=KEEP/REVISE; STATUS=ANSWERABLE/INSUFFICIENT) after a documented template-sensitivity audit; S/R assistance probes and margin/NLL analyses as a diagnostic layer only [contracts; margin_v2].
- Base/placebo atomic failure profiles read off the dose-0 arms: e.g., Reasoning placebo — interface compliance .71, distractor accuracy .843, KEEP .902, insufficient-information abstention .16 [curves_e500_all.json; curves_ans_formal_e500.json placebo rows]; Knowledge base — correct-candidate decision .608 with contract .992 [transfer_matrix_k500.json base row].
- Held-out demonstration that aggregate/clean scores mis-rank: heuristic arm best Original (.741), near-worst U (.340) [LLAMA_ORIGINAL_RETENTION_TABLE.json].

**4. Strongest positive findings.** A single model at a fixed aggregate level simultaneously carries near-ceiling behaviors (K contract .992) and near-floor behaviors (R abstention .16, R interface .71); the atomic profile separates them cleanly. On held-out arms, two recipes with near-identical clean scores differ by +.160 utility (predicted .696/.463 vs replay .712/.303), and ranking by clean score inverts the correct choice (heuristic).

**5. Negative/null findings.** Margin instrument v1 produced artifactual zeros (string-level re-tokenization fault) and was rebuilt at token-id level (v2) — the margin layer is diagnostic only; template sensitivity required an audit before contracts were fixed; base-R strict-interface artifact documented and excluded from base-vs-arm strict comparisons.

**6. Allowed claim.** "Aggregate scores hide atomic failure structure: controlled single-condition axes decompose one aggregate number into behaviorally distinct, independently movable failure modes." NOT: an exhaustive capability taxonomy; NOT statistical independence of axes.

**7. Limitation.** Axes are synthetic controlled perturbations (SVAMP external holdout and real-source IF data mitigate, deployment-style stress untested); atomicity is a property of the evaluation intervention design; the axis set is representative, not complete.

**8. Main figure/table.** Fig. 1 (Aggregate Score → Atomic Failure Profile); T1 (taxonomy + budgets).

---

## RQ2 — Atomic Repairability

**1. Scientific question.** How repairable are atomic behavioral failures under targeted SFT, and how does repairability vary with dose and domain? (Deliberately NOT "do failures admit repairs" — the most interesting findings are failures that barely move or get worse under repair. **Repairability** is the paper's formal scientific object.)

**2. Hypothesis.** For selected failure structures exposed by the atomic evaluation, a targeted data intervention (an atomic SFT repair family) can be constructed whose effect on the full behavioral profile, Δs_{i,d}(n), is measurable under matched-budget dose grids against clean-replay placebo — with no prior commitment that the effect is positive. Four representative repair families are instantiated; this is not a one-to-one mapping from the seven evaluation axes (e.g., Paraphrase has no dedicated repair; Correct/Wrong Candidate are jointly targeted by Selective Revision).

**3. Experiments answering it.**
- Four representative Atomic SFT Repair Families (Format, Evidence Robustness, Selective Revision, Answerability) × dose grids {0..960/cap} on Reasoning discovery domain, 2,000-example fixed carrier, within-grid token match ≤0.25%, fixed per-grid update count, cross-grid differences handled by preregistered budget-bridge (max placebo spread .051) [dose manifests; budget_bridge_audit.json].
- 529-family formal evaluation with 3-seed anchors [curves_e500_all.json; curves_ans_formal_e500.json].
- Cross-domain: K-500 formal transfer matrix, K/IF sparse grids, 3-seed targeted replication of the K-revision reversal [transfer_matrix_k500.json; ksparse_matrix.json; ifsparse_matrix.json; ktgt_scores].
- LODO local-predictability test on the format-contract endpoint family [fig6 source_data.json].
- SVAMP external holdout (no dose-wise degradation) [svamp_scores.json].

**4. Strongest positive findings — repairability itself has structure (four classes).**
- *Cheaply repairable* — Format: interface .71→.99@30, 1.00 from 60 (content essentially unmoved, format-MAIN .26→.30).
- *Weakly repairable* — Evidence: only a small positive effect in the Reasoning discovery setting (+2–3pp), and no robust cross-domain repair benefit (in-domain Knowledge .83→.78) — a diagnosed failure that resists the targeted repair we tried.
- *Repair-resistant / harmful* — Revision: fix never exceeds placebo (.784 placebo vs .631@120/.689@2000); high dose destroys the complementary KEEP behavior (.902→.492@2000).
- *Repairable under a constraint* — Answerability: abstention rises .16→.93 by dose 480 and continues toward 1.00 at higher dose, while false abstention rises from .01 and eventually crosses the preregistered ≤.10 hard constraint (.11@1822) — constrained repairability; 1.00 is not a recommended operating point.
- *Local predictability*: LODO on format-contract, frozen form library MAE .037 vs .073/.082/.073 dumb baselines — claimed for this endpoint family only.

**5. Negative/null findings.**
- *Collateral effects — repairs create new failures*: Reasoning-format training collapses Knowledge candidate judgment (decision .608→.070@60, final .602→.208, contract intact ≈.98–1.0) [transfer_matrix_k500.json cc_attempt; NUMBER_PROVENANCE_fmt2K.md]; Reasoning-answerability training exports false abstention to K (.25→.44).
- *Direction reversal*: high-dose revision collapses KEEP in Reasoning but yields all-KEEP in Knowledge (wc .00/.00/.00, 3 seeds) [ktgt_scores KRV-1493-S42/43/44].
- *Measurement stability*: four apparent effects from smaller evaluations failed to replicate at formal scale (format content-tax, evidence rise-fall, revision abstention-tax, KAN retention cost); all retractions ledgered [qc/INSTRUCTION_C29/C32; ktgt_scores].

**6. Allowed claim.** "Atomic failures have heterogeneous repair dynamics: some are cheap to fix, some resist SFT, and some repairs create new failures — repairability varies with dose and domain, including direction reversal; four representative repair families target selected diagnosed failure structures." NOT: four fundamental repair types; NOT a one-to-one axis↔repair mapping; NOT a robust cross-domain evidence repair benefit; NOT grid-wide predictability of all endpoints; NOT universal scaling law.

**7. Limitation.** Four representative controllable families only (selection criteria: matched control, graded dose, paired endpoint, cross-domain instantiation); sparse K/IF grids partly single-seed (direction-grade; key reversal 3-seed replicated, non-replicating KAN retracted); Reasoning is the discovery domain.

**8. Main figure/table.** Fig. 2 (repair-family instantiation + dose responses by repairability class); Fig. 3 (repairability / collateral / domain-dependence matrix); T1.

---

## RQ3 — Repair Composition

**1. Scientific question.** Does atomicity in evaluation imply additivity in training? If each repair response Δs_i(n_i) is measured, does a mixture satisfy Δs_mix ≈ Σ_i Δs_i(n_i)?

**2. Hypothesis (preregistered, falsified).** The additive hypothesis: mixture endpoint vector = placebo + sum of in-domain single-repair dose responses. Frozen with per-arm compositions, predicted endpoint vectors, predicted utilities, constraint thresholds, and hashes before any training [MIXTURE_SPEC_FROZEN.json].

**3. Experiments answering it.**
- Six frozen mixture arms over the pruned active set {format, answerability}×{R,K,IF} + tri-domain clean replay, shared 54 steps [MIXTURE_SPEC_FROZEN.json].
- Six targeted rescue runs, structurally identical to mixture arms, designed before results seen: three single-repair bridge arms on the tri-domain carrier, one in-domain pair, one cross-domain pair, one half-dose uniform [RESCUE_SPEC_FROZEN.json].
- Correction model assembly: additive backbone + bridge-calibrated terms + diversity-by-dose term [INTERACTION_CORRECTION.json].

**4. Strongest positive findings.**
- The rescue *identified the dominant conditional structures*: (A) **carrier dependence** — on the tri-domain carrier, fmt_R and ans_K bridge deltas collapse to ≈0 (−.004/−.003) while ans_R survives (+.059): Δ_i(n|C) is not carrier-free [RESCUE_OPEN_RESULT.json]; (B) **diversity-by-dose regime** — full six-cell coverage at total ≥600 carries a premium (uniform +.078, failure-frequency +.109) that concentrated-1200 (−.004) and diverse-300 (−.018) do not [INTERACTION_CORRECTION.json].
- The constraint machinery works: the raw-U maximum (failure-frequency .634) was disqualified by the frozen false-abstain threshold (.20>.10) before any post-hoc judgment [MIXTURE_OPEN_RESULT.json constraint_filtered_ranking].
- Unified form: Δs = F(repair, dose, domain, carrier, composition) — **Conditional Repair Composition**.

**5. Negative/null findings (the headline).**
- **The additive hypothesis fails**: predicted-vs-actual ranking Spearman −0.43; U-MAE .054 > seed noise; valid-arm actual ranking uniform .602 > retention-constrained .576 > predicted-optimal .569 > worst-repair .540 > replay .533 — the additive top pick finished third, the additive last pick finished first [MIXTURE_OPEN_RESULT.json].
- Tested pairwise interactions are too small to explain the residual (in-domain −.007, cross-domain −.015) [RESCUE_OPEN_RESULT.json].
- Residuals are systematic: diverse arms under-predicted (+.069/+.093), concentrated arms over-predicted (−.054/−.034).

**6. Allowed claim.** "Atomicity in evaluation does not imply additivity in training: the preregistered additive composition test failed on the development family, and targeted rescue identified carrier dependence and a diversity-by-dose regime as the dominant conditional structures." NOT: training repairs are universally non-additive; NOT carrier/diversity as universal laws; NOT Llama independently validates each mechanism.

**7. Limitation.** Two pairwise interactions tested, not all; diversity regime observed at coarse dose resolution (300/600/1200); both structures are post-hoc discoveries on Qwen (which is exactly why RQ4 exists: they were frozen into a package and tested prospectively).

**8. Main figure/table.** Fig. 4 (left: additive prediction FAILs; right: conditional structures); T2 (Qwen six-arm frozen-vs-actual with DQ note).

---

## RQ4 — Prospective Prescription

**1. Scientific question.** Can conditional repair structure prospectively prescribe SFT for a held-out model family — one held out from response-model fitting and composition-correction development? (Answer: yes, in our held-out test.)

**2. Hypothesis (frozen before test).** The corrected conditional-composition model — additive backbone + carrier-bridge terms + diversity-by-dose term — with a preregistered low-dimensional calibration, mechanically produces a recipe that beats uniform mixing under frozen constraints, with the full four-arm ranking predicted in advance [LLAMA_PREDICTION_FREEZE.json].

**3. Experiments answering it.**
- Pipeline: New Model → Atomic Diagnosis (whitelisted base-profile fields) → Minimal Calibration (exactly 2 preregistered runs → one scalar, scale = δ^L_ansR/δ^Q_ansR = .376) → Frozen Repair Model → Predicted Prescription (ans_R 480 + full six-cell coverage, total 1,230) → Blind Validation (4 arms × 3 seeds) [LLAMA_CALIBRATION_RULE_FROZEN.md; LLAMA_VERDICT_TABLE_FROZEN.md; LLAMA_FINAL_RESULT.json].
- Freeze chronology: Qwen formally closed → corrections frozen → calibration rule committed before any Llama artifact → prediction freeze committed before comparison training.
- Retention audit: Original macro per arm + per-domain decomposition [LLAMA_ORIGINAL_RETENTION_TABLE.json]; per-seed and constraint audit [LLAMA_FINAL_AUDIT.json].

**4. Strongest positive findings.**
- Frozen ranking **Predicted > Uniform > Heuristic > Replay** recovered 4/4 (Spearman 1.0); actual U .463 > .407 > .340 > .303.
- Primary fully-prospective comparison: Predicted vs Uniform +.057, seed-separated (min pred .4457 > max uniform .4416, 3 seeds each). Predicted vs Replay +.160. All frozen constraints pass (false-abstain ≈0 every arm).
- Retention answers the three natural objections: (i) vs Replay — not generic capability gain (Original .696 vs .712, −.016 within noise, with +.160 U); (ii) vs Uniform — predicted wins both axes (+.057 U, +.122 Original; uniform pays a clean-Knowledge tax .616→.463 that predicted avoids at .596); (iii) vs Heuristic — clean-score selection picks the wrong recipe (best Original .741, near-worst U .340).

**5. Negative/null findings.**
- Magnitude calibration imperfect and structured: residuals replay −.005 → heuristic +.013 → uniform +.065 → predicted +.092; gains of diverse mixtures systematically underestimated [LLAMA_FINAL_AUDIT.json prediction_vs_actual].
- Replay seed 42 was a preregistered calibration anchor later included in the replay mean — we report **frozen-ranking accuracy**, not four-arm total blindness (its −.005 residual is the natural corollary, disclosed).

**6. Allowed claim.** "Modeling conditional repair composition turns diagnosis into prescription: the frozen corrected prescription package transferred prospectively to one held-out model family, recovering the frozen four-arm ranking and beating uniform mixing on both utility and clean retention." NOT: universality; NOT mechanism-level validation of each structure on Llama; NOT magnitude-accurate prediction.

**7. Limitation.** One held-out family (cross-family evidence, not universality); calibration deliberately low-dimensional and not claimed optimal; magnitude gap is the open modeling problem; no formal compute-matched comparison against grid search (cost discussion only).

**8. Main figure/table.** Fig. 5 (pipeline timeline + frozen-vs-actual per-seed + Original-vs-U Pareto); T3 (Llama frozen-vs-actual, per-seed, constraints); T4 (retention).
