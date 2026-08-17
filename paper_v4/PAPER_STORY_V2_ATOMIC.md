# PAPER_STORY_V2_ATOMIC — From Atomic Diagnosis to Prospective SFT Prescription

**Restructure of V1 per C-43. No new experiments; all numbers, freeze rules, and artifact provenance unchanged. Recipe optimization is demoted from the paper's starting point to the final proof-of-use.**

## Main line

Aggregate Performance → **Atomic Diagnosis** → **Atomic SFT Repair** → **Repair Response** → **Conditional Recomposition** → **Prospective Prescription**

## Core idea (one paragraph)

Evaluation should not stop at scoring. We first decompose aggregate benchmark performance into **atomic behavioral failures** via controlled evaluation axes (RQ1). We then map those failures to **atomic SFT repairs** and measure each repair's response — repairability, dose response, collateral effects, trade-offs, domain dependence (RQ2). We then ask whether atomic repairs **recompose**: a preregistered additive composition test fails, and targeted rescue identifies the conditional structure that governs composition (RQ3). Finally, as proof-of-use, the frozen conditional-composition model **prospectively prescribes** an SFT recipe for a held-out model family, and the prescription wins exactly as predicted (RQ4).

## The four core sentences (one per RQ; these are the paper's spine)

1. **Aggregate scores hide atomic failure structure.** (RQ1)
2. **Atomic failures have heterogeneous repair dynamics: some are cheap to fix, some resist SFT, and some repairs create new failures.** (RQ2)
3. **Atomicity in evaluation does not imply additivity in training.** (RQ3)
4. **Modeling conditional repair composition turns diagnosis into prescription.** (RQ4)

## Story arc (RQ-driven; replaces the V1 six-act structure)

**RQ1 — Atomic Diagnosis.** An aggregate score — say, 80% accuracy (illustrative example only, not an experimental number) — does not denote a uniform "80% competence". The same clean success can vanish under a paraphrase, a distractor, a wrong candidate answer, missing information, or a structured-output requirement: the aggregate mixes stable competence with fragile success. We decompose it with controlled atomic evaluation axes — Original, Paraphrase, Distractor, Wrong/Correct Candidate, Insufficient Information, Structured Output — where *atomic* means each axis changes as close to one local condition at a time as we can control (a property of the evaluation intervention, not a claim of statistical independence, and not an exhaustive capability taxonomy). S/R assistance probes serve as a recoverability diagnostic only, never as a training component. The result is a map **Aggregate Score → Atomic Failure Profile** over 3 domains (Reasoning / Knowledge / General-IF), 529 evaluation families. The held-out heuristic paradox foreshadows the stakes: the arm with the best clean score (Original .741) is nearly the worst overall (U .340) [LLAMA_ORIGINAL_RETENTION_TABLE.json].

**RQ2 — Atomic SFT Repair.** Each atomic failure suggests a targeted data intervention. We study **four representative Atomic SFT Repair Families** — Format Repair, Evidence Robustness Repair, Selective Revision Repair, Answerability Repair — against matched clean-replay placebo, organized by scientific properties rather than by dataset: *repairability*, *dose response* Δs_{i,d}(n), *collateral effects*, *trade-offs*, *domain dependence*, *measurement stability*. The dynamics are heterogeneous: Format is cheap (interface .71→.99 at 30 examples) but buys interface, not content; Evidence yields small, stable gains (+2–3pp) in every domain tested; Selective Revision has no stable net benefit on its target and damages the complementary KEEP behavior at high dose (.90→.49); Answerability delivers the one large gain (.16→1.00) at a bounded false-abstain cost (.01→.11). Repairs also create new failures out-of-domain: Reasoning-format training collapses Knowledge candidate judgment (.608→.070 at dose 60, contract intact) [transfer_matrix_k500.json], and revision reverses direction across domains (Knowledge all-KEEP, 3-seed). Several apparent effects from smaller evaluations failed to replicate at formal evaluation scale; each retraction is ledgered.

**RQ3 — Repair Composition (the scientific pivot).** If failures decompose atomically and each repair response is measured, does the whole repair satisfy Δs_mix ≈ Σ_i Δs_i(n_i)? We froze this additive prediction before training and it **failed**: predicted-vs-actual ranking Spearman −0.43, utility MAE .054 above seed noise; the additive model's top pick finished third and its last pick (uniform) finished first; the raw-utility maximum (failure-frequency, .634) was disqualified by the frozen false-abstain constraint (.20 > .10) [MIXTURE_SPEC_FROZEN.json; MIXTURE_OPEN_RESULT.json]. Targeted rescue answers *why*: the tested pairwise interactions are too small (−.007/−.015); instead, two dominant conditional structures — **carrier dependence** (a repair's gain depends on the mixture it is embedded in: fmt_R and ans_K deltas →0 on the tri-domain carrier while ans_R survives +.059) and a **diversity-by-dose regime** (full six-cell coverage at total ≥600 carries a premium +.078/+.109 that concentrated-1200 and diverse-300 arms do not) [RESCUE_OPEN_RESULT.json; INTERACTION_CORRECTION.json]. The unified statement: Δs = F(repair, dose, domain, carrier, composition) — **Conditional Repair Composition**, identified on the Qwen development family (not claimed as universal law, and not mechanism-ablated on Llama).

**RQ4 — Prospective Prescription (proof-of-use).** The end-to-end test of the framework: New Model → Atomic Diagnosis → Minimal Calibration → Frozen Repair Model → Predicted Prescription → Blind Validation. Qwen discovery formally closed; corrections, recipe-search rule, constraints, and the four-arm predicted ranking frozen and committed before comparison training; Llama-3.1-8B allowed exactly the preregistered low-dimensional calibration (2 runs → one scalar, scale .376). Replay seed 42 was a preregistered calibration anchor — we report frozen-ranking accuracy, not four-arm total blindness; the primary Predicted-vs-Uniform comparison is fully prospective. Outcome: frozen ranking **Predicted > Uniform > Heuristic > Replay** recovered 4/4; actual U .463 > .407 > .340 > .303; Predicted vs Uniform +.057 (min pred seed .4457 > max uniform seed .4416); Predicted vs Replay +.160; all constraints pass [LLAMA_PREDICTION_FREEZE.json; LLAMA_FINAL_RESULT.json; LLAMA_FINAL_AUDIT.json]. Retention answers the three natural objections: vs Replay — not a generic capability lift (Original .696 vs .712, robustness +.160); vs Uniform — diversity alone is not the recipe (predicted wins both axes, +.057 U and +.122 Original; uniform pays a clean-Knowledge tax .616→.463); vs Heuristic — clean benchmarks select the wrong recipe (best Original .741, near-worst U .340) [LLAMA_ORIGINAL_RETENTION_TABLE.json]. Magnitudes remain imperfectly calibrated (residuals −.005→+.092, diverse mixtures underestimated most) — ranking and direction transfer; calibration is open.

## What is demoted, what is promoted (vs V1)

- **Demoted**: "Given a fixed SFT budget, what data should we train?" is no longer the opening problem. Recipe optimization appears only in RQ4 as the framework's proof-of-use.
- **Promoted**: the diagnostic decomposition (RQ1) and the failure→repair mapping (RQ2) become the paper's conceptual foundation; the additive-vs-conditional composition question (RQ3) is the headline scientific result.
- **Unchanged**: every number, artifact pointer, freeze chronology, retraction ledger, and the replay-anchor disclosure.

## Terminology (paper-wide)

atomic evaluation axis / atomic behavioral failure / atomic SFT repair / atomic repair family / repair response / repairability / collateral effect / conditional repair composition / prescription. `component` survives only as an implementation term (configs, artifact field names); `scaling law` never as a headline (within RQ2: "local dose-response", "response scaling").

## Scientific boundaries (verbatim guardrails)

Never: universal SFT law; four fundamental repair types; all atomic repairs are predictable; evaluation axes are statistically independent; training repairs are universally non-additive; carrier/diversity threshold proven across all model families; Llama independently validates each mechanism; utility magnitude perfectly predicted.
Correct register: four **representative** repair families; atomicity refers to controlled evaluation intervention, not independent parameter updates; additive composition failed **in the preregistered development-family mixture test**; targeted rescue **identified dominant conditional structures**; the frozen corrected prescription package **transferred prospectively to one held-out model family**.

## Candidate titles (for review; V1 title kept as fallback)

1. *Aggregate Scores Hide Atomic Failures: Diagnosing, Repairing, and Prescribing SFT*
2. *From Atomic Diagnosis to SFT Prescription: Why Repairs Don't Add Up*
3. *Atomic Diagnosis, Atomic Repair, Conditional Composition: Turning Evaluation into SFT Prescription*
4. (V1 fallback) *Predicting SFT Recipes from Response Profiles*

## 30-second spoken version (V2)

"A model that scores 80% doesn't have a uniform 80% competence — the same success can vanish under a paraphrase, a distractor, or a missing fact. We decompose aggregate scores into atomic behavioral failures, then map each failure to a targeted SFT repair and measure how it responds to dose across three domains. The repairs are wildly heterogeneous — some cost 30 examples, some resist SFT entirely, some create new failures in other domains. Then the key question: if evaluation decomposes atomically, does training compose additively? We bet it did, in a preregistered test — and lost. The failure has structure: a repair's effect depends on what it's mixed with, and diverse mixtures at sufficient dose earn a premium concentrated bets don't. We froze that conditional-composition model, moved to a model family we'd never trained, and mechanically prescribed a recipe. It ranked first, exactly as predicted, beating uniform mixing on robustness *and* clean retention. Diagnosis, done atomically, becomes prescription."
