# PAPER_OUTLINE_V2_ATOMIC — RQ-driven section structure

**V2.1 (C-44): spine = Diagnosis → Repairability → Composability → Prescription; RQ2 = Atomic Repairability; no axis↔repair one-to-one mapping; Fig 1 = tile matrix (no radar).**

Replaces PAPER_OUTLINE_V0. All evidence unchanged; sections reorganized around RQ1–RQ4. Existing drafts (DRAFT_sec3_sec4.md, DRAFT_sec5_sec6_sec2.md) remain the content quarry: the mapping from old draft material to new sections is given per section.

## 1. Introduction
- Opens from the meaning of an aggregate score (NOT from "fixed SFT budget, what data to train"): 80% accuracy ≠ uniform 80% competence (illustrative example, flagged as such); clean success vanishes under minimal perturbations; aggregate = stable competence + fragile success.
- Fixed 10-step logic: aggregate hides structure → atomic evaluation decomposes it → diagnosis is not the endpoint → the real question about a diagnosed failure is its **repairability** → repairability has structure (cheap / weak / resistant / collateral / constrained / domain-dependent; four representative repair families targeting selected failure structures) → the natural additive-recomposition question → preregistered additive test FAILS → targeted rescue yields conditional composition → freeze → held-out prospective prescription succeeds.
- The four core sentences appear verbatim, one per RQ.
- Contributions (C-45 order, three): (1) atomic diagnosis + repairability combined; (2) **conditional repair composition — the central scientific contribution**; (3) prospective held-out prescription. RQ1 alone is not positioned as the main novelty. [CITATION-REQUIRED] markers retained for practice claims.
- Draft: INTRODUCTION_V0_ATOMIC.md (this pass). Figures: Fig. 1.

## 2. Atomic Evaluation: Decomposing Aggregate Performance — RQ1
- Atomic evaluation axes (Original/Paraphrase/Distractor/Wrong+Correct Candidate/Insufficient Information/Structured Output); atomicity = one controlled local condition at a time (evaluation-intervention property, not statistical independence, not exhaustive taxonomy); applicability matrix; decision contracts after template-sensitivity audit; S/R assistance as recoverability diagnostic only; 529-family suite (ans branch 249); 3 domains and data sources with train/eval isolation.
- Aggregate → Atomic Failure Profile map; base/placebo profile as first exhibit — wide behavioral dispersion (interface .71, distractor .843, KEEP .902, abstain .16) with the clean contract-vs-decision contrast (K contract .992 vs decision .608); same-item fragility readout on the distractor axis: P(fail | original correct) placebo mean .095, base .119, same-family pairing at 529-fam scale [rq1_paired_fragility.json].
- Old material: DRAFT sec 2 "Domains and pools" + "Evaluation conditions" paragraphs, reframed from diagnosis-first perspective.
- Figures: Fig. 1. Tables: T1. Claims: RQ1-1, RQ1-2 (see CLAIM_EVIDENCE_MATRIX_V2). Appendix: contracts, audit ledgers, scorer self-tests, margin-v2, S/R definition.

## 3. From Atomic Diagnosis to Atomic SFT Repair — RQ2 (instantiation)
- The conceptual bridge: diagnosis is only the first step — the real question about a diagnosed failure is how repairable it is under SFT. We instantiate four representative Atomic SFT Repair Families (Format / Evidence Robustness / Selective Revision / Answerability) **targeting selected failure structures exposed by the atomic evaluation** — explicitly NOT a one-to-one axis↔repair mapping (Paraphrase has no dedicated repair; Correct/Wrong Candidate are jointly targeted by Selective Revision); each family with the failure it targets and its paired behavioral endpoint; clean replay = matched placebo; selection criteria (matched control, graded dose, paired endpoint, cross-domain instantiation) and the explicit non-exhaustiveness statement.
- Repair-response object Δs_{i,d}(n); dose grids; budget matching (within-grid ≤0.25% token deviation + fixed updates; cross-grid via preregistered budget-bridge, max placebo spread .051); training protocol.
- Old material: DRAFT sec 2 "Domains and pools" (pool half), "Budget matching", sec 3 "Setup recap".
- Figures: Fig. 2 (left panel: failure↔repair map). Tables: T1. Appendix: dose manifests, budget-bridge audit.

## 4. Heterogeneous Repairability, Dose Responses, and Collateral Effects — RQ2 (results)
- Organized by repairability regime + property, NOT per-dataset: (i) **four qualitatively distinct observed repairability regimes** (one repair family per regime; not a universal taxonomy) — cheaply repairable (format interface .71→.99@30, clean-task retention flat original .90±.02; format-MAIN reported as its own endpoint, not content-preservation evidence); weakly repairable (evidence: small positive effect in the Reasoning discovery setting only, no robust cross-domain benefit, in-domain K .83→.78); repair-resistant/harmful (revision fix ≤ placebo throughout, KEEP .90→.49); repairable under a constraint (answerability .16→.93@480 continuing toward 1.00 while false abstention crosses the preregistered ≤.10 constraint at high dose, .11@1822); (ii) dose response shapes (saturation/flat/bidirectional-harm/slow-saturation); (iii) trade-offs (the false-abstain Pareto axis as hard constraint); (iv) collateral effects (fmt→K decision collapse .608→.070@60 with contract intact; ans→K false-abstain export .25→.44); (v) domain dependence incl. direction reversal (K-revision all-KEEP, 3-seed); (vi) measurement stability (four retractions at formal scale, ledgered); local predictability aside (format-contract LODO MAE .037 vs .073/.082/.073).
- Old material: DRAFT sec 3 in full (response shapes, LODO, domain dependence, methodological note), re-grouped by property.
- Figures: Fig. 2 (dose-response panels), Fig. 3. Claims: RQ2-1..4. Appendix: full endpoint grids, K/IF sparse tables, SVAMP holdout, margin-v2 audit, retraction ledger.

## 5. Does Atomicity Imply Additivity? — RQ3 (the pivot, negative)
- The natural hypothesis Δs_mix ≈ Σ Δs_i(n_i), preregistered as a frozen six-arm prediction; the failure (Spearman −.43, U-MAE .054 > noise; uniform first, predicted third); the constraint machinery working (failure-frequency .634 DQ'd at false-abstain .20>.10); systematic residual structure (diverse under-predicted, concentrated over-predicted).
- Core sentence: atomicity in evaluation does not imply additivity in training.
- Old material: DRAFT sec 4 in full.
- Figures: Fig. 4 (left). Tables: T2. Claims: RQ3-1, RQ3-2. Appendix: six-arm compositions, frozen spec, per-branch vectors.

## 6. Conditional Composition of Atomic Repairs — RQ3 (structure)
- Why additivity fails: tested pairwise interactions too small (−.007/−.015); carrier dependence (fmt_R/ans_K →0 on tri-carrier, ans_R +.059); diversity-by-dose regime (six-cell ≥600 → +.078/+.109; concentrated-1200 −.004; diverse-300 −.018, coarse resolution declared); unified form Δs = F(repair, dose, domain, carrier, composition); the corrected prescription model (additive backbone + bridge terms + diversity term).
- Named **Conditional Repair Composition** (not "mixture correction"); Qwen-identified dominant structures, package-level transfer wording only.
- Old material: DRAFT sec 5 in full.
- Figures: Fig. 4 (right). Claims: RQ3-3..5. Appendix: rescue design freeze, residual algebra, correction model.

## 7. From Atomic Diagnosis to Prospective Prescription — RQ4
- Pipeline: New Model → Atomic Diagnosis → Minimal Calibration → Frozen Repair Model → Predicted Prescription → Blind Validation; full freeze chronology; replay-anchor disclosure (frozen-ranking accuracy, primary pair fully prospective).
- Result: 4/4 ranking (.463>.407>.340>.303), +.057 vs uniform (min>max seeds), +.160 vs replay, constraints pass; retention table answering the three objections (vs replay / vs uniform / vs heuristic); calibration honesty (residuals −.005→+.092, diverse underestimated); scope paragraph.
- Old material: DRAFT sec 6 in full.
- Figures: Fig. 5. Tables: T3, T4. Claims: RQ4-1..3. Appendix: calibration rule freeze, prediction freeze JSON, verdict table, per-seed audit, retention table, base-R artifact note.

## 8. Discussion
- What conditional composition means for evaluation-driven training; diagnosis-as-prescription as the reusable pipeline; cost amortization discussion (no formal compute-matched claim); limitations: one held-out family, magnitude calibration (structured underestimation of diverse mixtures) as the open modeling problem, coarse diversity-regime resolution, one preregistered U (alternative-aggregation sensitivity: *planned appendix analysis, not yet generated*), single-seed direction-grade sparse grids, four repair families only.

## 9. Related Work
- Behavioral evaluation & robustness suites (diagnosis side); data mixing/selection for LM training [CITATION-REQUIRED cluster]; scaling-laws framing (contrast: local dose-response vs loss power laws — never headline); reasoning faithfulness interventions; abstention/calibration training.

## 10. Conclusion
- The four core sentences as the summary spine; "SFT scales locally, but composes conditionally" retained as closing slogan inside the conditional-composition frame.

## Main tables (unchanged data, re-captioned in repair vocabulary)
- T1: atomic failure ↔ repair family taxonomy + budgets; T2: Qwen six-arm frozen-vs-actual (DQ note); T3: Llama frozen-vs-actual per-seed + constraints; T4: retention (Original vs U per arm).

## Drafting status
- Sections 2–7 content exists in DRAFT_sec3_sec4.md / DRAFT_sec5_sec6_sec2.md and needs *re-sectioning + terminology pass* (component→repair family, etc.) — NOT yet done; awaits V2 review per C-43 stop order.
- Introduction: INTRODUCTION_V0_ATOMIC.md (V0 draft, this pass).
