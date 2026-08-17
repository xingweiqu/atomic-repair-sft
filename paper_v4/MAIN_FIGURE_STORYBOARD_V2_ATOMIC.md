# MAIN_FIGURE_STORYBOARD_V2_ATOMIC — 5 main figures (RQ-aligned)

Replaces MAIN_FIGURE_STORYBOARD (V1). Same data artifacts; figures re-cut to the atomic-diagnosis→repair→composition→prescription line. The V1 Fig-1b Pareto moves to Fig. 5c.

## Fig 1 — Aggregate Score → Atomic Failure Profile (RQ1)
- **Question**: does one aggregate number denote one competence?
- **Panels**: (a) schematic: a single aggregate bar "decomposes" into the atomic evaluation axes (Original / Paraphrase / Distractor / Wrong Candidate / Correct Candidate / Insufficient Information / Structured Output), annotated "one controlled condition changed at a time"; (b) a real base-model atomic failure profile as a radial/bar profile from committed dose-0/base fields: R interface .71, distractor .843, KEEP .902, insufficient-info abstention .16 [curves_e500_all.json, curves_ans_formal_e500.json placebo rows]; K correct-candidate decision .608 with contract .992 [transfer_matrix_k500.json base row] — near-ceiling and near-floor behaviors inside one model.
- **Data**: placebo/base rows only (all committed); the "80%" in the schematic is explicitly illustrative (no fabricated aggregate number — panel (a) uses an unlabeled bar, not a claimed score).
- **Takeaway**: aggregate scores hide atomic failure structure.
- **Caption draft**: "An aggregate score mixes stable competence with fragile success. Controlled atomic evaluation axes (a) decompose it into an atomic failure profile (b): the same base model is near-ceiling on interface contract and distractor robustness yet near-floor on abstention and candidate judgment."

## Fig 2 — Atomic Failure ↔ Atomic SFT Repair (RQ2)
- **Question**: can atomic failures be repaired by targeted SFT, and what do repair responses look like?
- **Panels**: (a) mapping strip: each atomic failure → its Atomic SFT Repair Family (Format / Evidence Robustness / Selective Revision / Answerability), clean replay drawn as matched placebo lane; (b) four representative dose-response panels (x = repair examples, 3-seed anchor bars, per-condition n printed): Format interface saturation .71→.99@30 (with format-MAIN flat .26→.30 overlay — interface, not content); Evidence near-flat +2–3pp; Revision KEEP/FIX seesaw (fix ≤ placebo; KEEP .90→.49) with wrong-candidate-adoption overlay; Answerability target rise .16→1.00 vs false-abstain Pareto .01→.11.
- **Data**: curves_e500_all.json, curves_ans_formal_e500.json, dose manifests.
- **Takeaway**: heterogeneous repair dynamics — cheap, weak, resistant/harmful, constrained-gain.
- **Caption draft**: "Atomic failures admit targeted SFT repairs with heterogeneous dynamics: interface compliance is cheap, evidence robustness barely moves, selective revision resists repair and harms its complement at high dose, and answerability shows a large gain against a rising false-abstain cost (529-family evaluation; answerability subset 249; within-grid matched replacement under a fixed protocol)."

## Fig 3 — Repairability, Collateral, and Domain Dependence (RQ2)
- **Question**: do repair effects stay where they were trained?
- **Panels**: (a) compact matrix: R-trained repair families (rows: fmt/evd/rev/ans × dose) × Knowledge-domain atomic endpoints (cols), Δ vs placebo; highlight the format→K candidate-judgment collapse (.608→.070@60) with the contract row intact (≈.98–1.0) — a repair creating a NEW failure elsewhere; ans→K false-abstain export .25→.44 marked as exported trade-off; (b) direction-reversal inset: high-dose revision in R (KEEP collapses) vs K (all-KEEP, wc .00/.00/.00, 3 seeds).
- **Data**: transfer_matrix_k500.json, ktgt_scores, ksparse_matrix.json.
- **Takeaway**: repairs are domain-conditional; collateral transfers and direction can reverse — some repairs create new failures.
- **Caption draft**: "Repair effects are domain-dependent: format repair collapses Knowledge candidate judgment while its interface contract survives (a); high-dose revision repair reverses direction across domains (b, 3 seeds)."

## Fig 4 — Atomic Repair Recomposition Fails → Conditional Composition (RQ3)
- **Question**: does atomicity in evaluation imply additivity in training? (No.) What structure governs composition?
- **Panels**: (a) LEFT — the additive bet: Σ atomic repair responses → frozen additive prediction → FAIL: frozen-predicted vs actual U for six Qwen arms, ρ=−.43 annotated, DQ'd failure-frequency arm marked (false-abstain .20 > .10), uniform-first/predicted-third visually explicit; (b) RIGHT — conditional structure from six rescue runs: pairwise-interaction bars (small: −.007/−.015), carrier-bridge deltas (fmt_R/ans_K →0, ans_R +.059 survives), diversity-by-dose cells (diverse-300 −, six-cell ≥600 +, concentrated-1200 0); footer equation Δs = F(repair, dose, domain, carrier, composition).
- **Data**: MIXTURE_SPEC_FROZEN, MIXTURE_OPEN_RESULT, RESCUE_OPEN_RESULT, INTERACTION_CORRECTION.
- **Takeaway**: atomicity in evaluation does not imply additivity in training; the dominant corrections are carrier dependence and a diversity-by-dose regime (development-family-identified, coarse resolution).
- **Caption draft**: "Preregistered additive recomposition of atomic repairs fails on the development family (a); targeted rescue identifies carrier dependence and a diversity-by-dose regime as the dominant conditional structures (b) — repair composition is conditional, not additive."

## Fig 5 — From Atomic Diagnosis to Prospective Prescription (RQ4)
- **Question**: does the frozen conditional-composition model prescribe for a family it never saw?
- **Panels**: (a) pipeline timeline with commit hashes: New Model → Atomic Diagnosis (whitelisted profile) → Minimal Calibration (2 preregistered runs → scale .376) → Frozen Repair Model → Predicted Prescription → Blind Validation; replay-S42 calibration anchor explicitly marked on the timeline (frozen-ranking accuracy, primary pair fully prospective); (b) frozen-predicted vs actual U per arm with per-seed points — 4/4 ranking, min(pred) .4457 > max(uni) .4416 visible; residual arrows (−.005 → +.092) as the calibration-honesty layer; (c) Original-vs-U Pareto (V1 Fig-1b moved here): heuristic (.741,.340) lower-right, replay (.712,.303), uniform (.574,.407), predicted (.696,.463) — labeled arrows for the three comparisons: vs replay (clean ≈, U +.160: not generic capability), vs uniform (wins both axes), vs heuristic (clean-score selection inverts the choice).
- **Data**: LLAMA_PREDICTION_FREEZE, LLAMA_FINAL_RESULT, LLAMA_FINAL_AUDIT, LLAMA_ORIGINAL_RETENTION_TABLE.
- **Takeaway**: modeling conditional repair composition turns diagnosis into prescription — 4/4 frozen ranking, +5.7pp over uniform under passing constraints, clean retention intact; magnitudes honestly under-calibrated.
- **Caption draft**: "Prospective held-out prescription: with the repair model frozen and two preregistered calibration runs, the mechanically prescribed recipe ranks first exactly as predicted (b), preserving clean performance while adding +16pp utility over replay and dominating uniform mixing on both axes (c)."
