# MANUSCRIPT WORKING DRAFT V1 — Diagnosis, Repairability, Composability, Prescription

**Status**: working draft under C-45. Drafting order executed: RQ2 Results (§3–§4) → RQ3 (§5–§6) → RQ4 (§7) → RQ1/Setup (§2) → Introduction (§1) last. §9 Related Work is a structured skeleton pending the citation pass. Every numerical sentence carries an internal artifact pointer in [brackets]; pointers resolve to PAPER_EVIDENCE_FREEZE/ unless otherwise noted and are removed only at camera-ready. Title placeholder — candidates in PAPER_STORY_V2_ATOMIC.md.

---

## 1. Introduction

A model that scores, say, 80% on a benchmark does not possess a uniform "80% competence." The number is an average over outcomes whose stability differs enormously: the same correctly answered item may fail when the question is paraphrased, when a plausible distractor is inserted into the context, when a wrong candidate answer is offered for review, when the information needed to answer is quietly removed, or when the answer must be produced in a required structured format. (Throughout, "80%" is an illustrative figure, not a measurement.) An aggregate score therefore mixes **stable competence** with **fragile success** — and treats them as interchangeable. **Aggregate scores hide atomic failure structure.**

Controlled evaluation can take the aggregate apart. We construct a suite of **atomic evaluation axes** — Original, Paraphrase, Distractor, Wrong/Correct Candidate, Insufficient Information, Structured Output — where *atomic* means each axis changes as close to one local condition at a time as we can control; assistance probes serve only as a recoverability diagnostic. Applied across three task domains (Reasoning, Knowledge, General Instruction-Following) over 529 controlled evaluation families [eval500 build_stats], this turns one aggregate number into an **atomic failure profile**. The profile is not a re-weighted benchmark: it exposes wide behavioral dispersion within a single model — abstention under missing information at .16, interface compliance at .71, distractor accuracy at .84 [curves_e500_all.json; curves_ans_formal_e500.json placebo rows] — including a particularly clean contrast in which the model follows the candidate-review decision contract almost perfectly (.99) yet decides far less accurately (.61) [transfer_matrix_k500.json base row]: the *form* of the behavior is intact while the *judgment* inside it fails. The fragility is same-item, not compositional: pairing each family's original and perturbed variants shows that about one in ten originally-correct families fails when a single distractor is inserted (placebo mean P(fail | correct) = .095 across 9 arms; base .119) [rq1_paired_fragility.json]; on other axes we describe behavioral heterogeneity under controlled perturbations. We do not claim these axes form an exhaustive or statistically independent capability taxonomy; they are controlled, single-condition interventions.

Diagnosis, however, is only the first step. In current practice, fine-grained evaluations mostly report failures; deciding what to *train* in response remains heuristic — mixtures chosen by intuition, aggregate validation scores, or costly search [CITATION-REQUIRED: data-selection / mixture-optimization literature]. And the question that actually matters for training is not whether some dataset targets a diagnosed failure — it is **how repairable that failure is under SFT**. We therefore instantiate **four representative atomic SFT repair families targeting selected failure structures exposed by the atomic evaluation** — Format Repair, Evidence Robustness Repair, Selective Revision Repair, and Answerability Repair (deliberately not a one-to-one mapping from the seven axes: paraphrase has no dedicated repair, and the two candidate axes are jointly targeted by selective revision) — each trained at graded doses against a matched clean-replay placebo inside a fixed carrier, and each scored on the *full* atomic profile Δs_{i,d}(n), not just its target axis.

We find that **repairability itself has structure** — four qualitatively distinct observed regimes (one repair family per regime; we do not claim a universal taxonomy). Some failures are *cheaply repairable*: 30 format examples move interface compliance from .71 to .99, with clean-task retention flat across the grid (original .90±.02) [curves_e500_all.json]. Some are only *weakly repairable*: evidence robustness shows a small positive effect in the Reasoning discovery setting (+2–3pp) and does not establish a robust cross-domain repair benefit (trained in-domain on Knowledge it moves .83→.78) [curves_e500_all.json; ksparse_matrix.json] — some diagnosed failures resist the targeted repair we tried. Some are *repair-resistant and harmful to repair*: selective revision never beats placebo on its own target while destroying the complementary keep-behavior at high dose (.90→.49) [curves_e500_all.json REV]. Some are *repairable only under a constraint*: abstention on unanswerable inputs rises from .16 to .93 by dose 480 and continues toward 1.00 at higher dose, while false abstention rises from .01 and eventually crosses the preregistered ≤.10 constraint [curves_ans_formal_e500.json] — the ceiling is reachable, but not at an acceptable operating point. Repairability is also *domain-conditional*, and repairs create *new* failures elsewhere: reasoning-format training collapses Knowledge candidate judgment (.61→.07 at dose 60) while its interface contract survives intact [transfer_matrix_k500.json cc_attempt], and high-dose revision reverses direction entirely across domains (3-seed replicated) [ktgt_scores]. **Atomic failures have heterogeneous repair dynamics: some are cheap to fix, some resist SFT, and some repairs create new failures.**

This sets up the question the paper pivots on. If failures decompose atomically, and each failure's repairability is measured, the natural engineering hypothesis is that repairs *recompose additively*: Δs_mix ≈ Σ_i Δs_i(n_i). We committed to this hypothesis in a preregistered test — six frozen mixture arms with predicted endpoint vectors, utilities, and constraints hashed before training — and it **failed**: predicted-versus-actual ranking correlates at Spearman −0.43, the additive model's top pick finished third, and the arm it ranked last finished first [MIXTURE_SPEC_FROZEN.json; MIXTURE_OPEN_RESULT.json]. **Atomicity in evaluation does not imply additivity in training.**

The failure has structure. Six targeted rescue runs account for the dominant residual patterns: the tested pairwise interactions are far too small to explain them (−.007/−.015); instead, two conditional structures dominate: **carrier dependence** — a repair's measured gain depends on the mixture it is embedded in (gains that survive on a clean single-domain carrier vanish on a tri-domain carrier, while others survive) — and a **diversity-by-dose regime** — full coverage of the repair×domain grid at sufficient total dose carries a premium (+.078/+.109) that neither concentrated nor small-but-diverse mixtures earn [RESCUE_OPEN_RESULT.json; INTERACTION_CORRECTION.json]. Composition is therefore governed by Δs = F(repair, dose, domain, carrier, composition): **conditional repair composition**, identified on our development family; we do not claim these structures as universal laws.

A discovered structure is only worth its predictions. We froze the corrected composition model, formally closed the development family, and tested the whole framework end-to-end on **a model family held out from response-model fitting and composition-correction development** (Llama-3.1-8B): atomic diagnosis of the new model through whitelisted profile fields, a preregistered two-run calibration yielding a single scalar, a mechanically generated prescription, and a four-arm prediction committed before any comparison training [LLAMA_CALIBRATION_RULE_FROZEN.md; LLAMA_PREDICTION_FREEZE.json]. The frozen ranking — Predicted > Uniform > Heuristic > Replay — was recovered exactly (actual utilities .463 > .407 > .340 > .303); the primary predicted-versus-uniform comparison, fully prospective, gives +.057 with seed-level separation [LLAMA_FINAL_RESULT.json; LLAMA_FINAL_AUDIT.json]. One replay seed served as a preregistered calibration anchor, so we report frozen-ranking accuracy rather than total blindness. The retention table completes the argument: against replay, the prescription adds +.160 utility at unchanged clean performance — not a generic capability lift; against uniform it wins on *both* axes, because blind diversity pays a hidden clean-Knowledge tax the prescription avoids; and against the heuristic arm — the best clean score of any arm and nearly the worst utility — it shows that selecting recipes by clean benchmarks inverts the right choice [LLAMA_ORIGINAL_RETENTION_TABLE.json]. **Modeling conditional repair composition turns diagnosis into prescription.**

**Contributions** — the spine is **Diagnosis → Repairability → Composability → Prescription**:
1. **Atomic diagnosis and repairability (RQ1+RQ2).** A controlled evaluation suite that decomposes aggregate performance into atomic behavioral failure structure across three domains, and repairability as a measurable object: dose-response, collateral, trade-off, and domain-dependence measurements for four representative atomic SFT repair families against matched placebo, yielding four qualitatively distinct observed repairability regimes (cheap / weak / resistant / constrained) — including documented retractions of small-evaluation effects that failed to replicate at formal scale.
2. **Conditional repair composition (RQ3) — the central scientific contribution.** A preregistered falsification of additive repair composition, and identification of the dominant conditional structures (carrier dependence; diversity-by-dose) on the development family.
3. **Prospective prescription (RQ4).** A frozen, minimally calibrated pipeline that prospectively prescribed the winning constrained recipe on one held-out model family, with full freeze chronology and honest magnitude-calibration reporting.

**Scope.** Four representative repair families targeting selected failure structures, not a complete taxonomy; conditional structures identified on one development family and transferred as a frozen package to one held-out family — cross-family evidence, not universality; ranking and direction transfer while absolute magnitudes remain imperfectly calibrated, with diverse mixtures underestimated most.

---

## 2. Atomic Evaluation: Decomposing Aggregate Performance (RQ1)

**RQ1: What atomic behavioral failure structure is hidden by aggregate benchmark performance?**

**Domains and data.** Three task domains: Reasoning (GSM8K-train for training, GSM8K-test for evaluation, SVAMP as external holdout), Knowledge (2Wiki train/validation splits; a hard-distractor donor pool disjoint from evaluation families), and General Instruction-Following (SQuAD-v2, AG-News, CREPE with train/test isolation) [DATA_ROLE_MATRIX.csv]. Training and evaluation material never share items or families [TRAIN_EVAL_SEPARATION.md].

**Atomic evaluation axes.** Seven controlled conditions per applicable task form — Original, Paraphrase, Distractor, Correct Candidate, Wrong Candidate, Insufficient Information, Structured Output — instantiated per domain through an applicability matrix rather than a forced Cartesian product [APPLICABILITY_MATRIX.csv]. *Atomic* refers to the evaluation intervention: each axis changes as close to one local condition at a time as we can control. It is not a claim that the axes are statistically independent, and the set is representative, not exhaustive. Candidate and answerability probes use controlled decision contracts (DECISION=KEEP/REVISE; STATUS=ANSWERABLE/INSUFFICIENT) adopted after a documented template-sensitivity audit; assistance (S/R) probes and margin/NLL analyses form a recoverability diagnostic layer, not additional axes and never training components [contracts; margin_v2]. The formal suite comprises 529 evaluation families (the answerability branch, 249; auxiliary paraphrase probes retain a smaller frozen 50-family subset) [eval500 build_stats_500.json].

**The atomic failure profile.** Scoring a model on all applicable axes yields its atomic failure profile — the map Aggregate Score → Atomic Failure Profile. Two properties of the base/placebo profile carry RQ1:

*Wide behavioral dispersion at a fixed aggregate level.* The same model sits at very different points on different axes: insufficient-information abstention .16, interface compliance .71, distractor accuracy .84, KEEP on correct candidates .90 [curves_e500_all.json; curves_ans_formal_e500.json placebo rows]. The cleanest contrast is within the Knowledge candidate-review branch: contract compliance .992 against decision accuracy .608 [transfer_matrix_k500.json base row] — the behavioral *form* is nearly perfect while the *judgment* inside it is not. A tile-matrix rendering of this profile is Fig. 1; we deliberately avoid radar plots, since the axes are not a single kind of quantity.

*Same-item fragility, directly measured.* Because every perturbed variant belongs to the same evaluation family as its original, the frozen scorer computes a paired quantity per family (original correct ∧ perturbed correct) [prescription/lawv1_score.py summarize()]. On the distractor axis at formal scale, P(distractor failure | original correct) = .095 on average across all nine placebo arms (range .082–.107; base model .119; 529 families) [rq1_paired_fragility.json]: about one in ten originally-correct families fails when a single distractor is inserted. This is same-item fragility, not a composition of different populations. We claim this readout for the distractor axis only — paraphrase pairing exists only on the auxiliary 50-family subset — and describe the remaining axes as behavioral heterogeneity under controlled perturbations.

**Utility and constraints (used from §5 onward).** A preregistered hierarchical utility aggregates family → branch → domain → U = (U_R + U_K + U_IF)/3, with one primary metric per branch (base, robustness, candidate review, answerability, output interface) and false-abstain as a hard constraint (≤.10); leaf metrics such as contract/decision/final serve as decomposition diagnostics and are never double-counted [C-34#4 freeze; LLAMA_VERDICT_TABLE_FROZEN.md].

**Preregistration discipline.** Every prediction in this paper is committed before its training (mixture spec, rescue spec, calibration rule, verdict table, prediction freeze); every retraction is ledgered; manuscript numbers derive exclusively from the frozen evidence directory [PAPER_EVIDENCE_FREEZE/README.md].

---

## 3. From Atomic Diagnosis to Atomic SFT Repair (RQ2 — instantiation)

**RQ2: How repairable are atomic behavioral failures under targeted SFT, and how does repairability vary with dose and domain?**

Diagnosis is only the first step. The question that matters for training is not whether a diagnosed failure has a corresponding dataset, but how repairable it is — and at what dose, at what collateral cost, and whether the answer survives a change of domain. We make repairability measurable as follows.

**Repair families.** From the failure structures exposed in §2 we select those admitting controlled training and instantiate **four representative atomic SFT repair families**: Format Repair (targets structured-output failure), Evidence Robustness Repair (targets distractor susceptibility), Selective Revision Repair (targets the two candidate-review failures jointly: adopting wrong candidates and over-revising correct ones), and Answerability Repair (targets missing-information behavior). This is deliberately not a one-to-one mapping from the seven axes — paraphrase has no dedicated repair family. Selection criteria: each family admits a matched control, a graded dose, a paired behavioral endpoint, and cross-domain instantiation; we do not claim the four exhaust SFT data types. Clean replay is the matched placebo.

**Dose grids and budget matching.** For each family i and domain d we train a dose grid n ∈ {0, 30, 60, 120, 240, 480, 960, cap}, where each arm replaces n matched clean-replay examples inside a fixed 2,000-example carrier under a fixed training protocol [dose_manifest_format/EVD/REV/ANS.json]. Within a grid, target-token exposure is held to ≤0.25% deviation and the update count is a single fixed value; cross-grid update-count differences (e.g., 30/22/36) are not treated as directly comparable and are handled by a preregistered budget-bridge analysis (max placebo endpoint spread .051) [budget_bridge_audit.json]. Dose-0 is the shared placebo.

**The repair-response object.** The quantity under study is Δs_{i,d}(n): the change that repair family i at dose n in domain d induces over the *entire* atomic profile — target axis, complementary behaviors, clean-task retention, and out-of-domain branches — never the target endpoint alone. Evaluation uses the 529-family formal suite; anchor doses carry 3 seeds, and non-anchor points are single-seed and marked as such [curves_e500_all.json; curves_ans_formal_e500.json].

---

## 4. Heterogeneous Repairability, Dose Responses, and Collateral Effects (RQ2 — results)

### 4.1 Four observed repairability regimes (Fig. 2)

The four families do not share a functional form, and their differences are qualitative, not just parametric. We observe four distinct repairability regimes — one repair family per regime; observed patterns, not a universal taxonomy [curves_e500_all.json; curves_ans_formal_e500.json]:

**Cheaply repairable (Format).** The target endpoint saturates almost immediately: interface compliance rises from .71 (placebo) to .99 at 30 examples and 1.00 from 60 onward, while clean-task retention stays flat across the entire grid (original .90±.02). The joint semantic-plus-interface endpoint (format-MAIN) moves only .26→.30 and is reported as its own endpoint. Thirty examples buy the interface.

**Weakly repairable (Evidence robustness).** The response is small and near-flat: distractor accuracy moves from .843 (placebo) by +0–3pp across the whole grid, with no dose supporting a threshold or rise–fall shape. Trained in-domain on Knowledge, the same family moves .83→.78 [ksparse_matrix.json] — so the weakness is not a domain-mismatch artifact, and we do not claim a robust cross-domain repair benefit. Some diagnosed failures resist the targeted repair we tried.

**Repair-resistant and harmful (Selective revision).** The target "fix" endpoint never exceeds placebo at any dose (.784 placebo; .631@120; .706@960; .689@2000); low dose inflates wrong-candidate adoption (+.13 at doses 60–240); and high dose collapses the complementary KEEP behavior (.902→.492@2000, with large seed sensitivity, range .26) [curves_e500_all.json REV rows]. Training harder makes this failure worse.

**Repairable under a constraint (Answerability).** The one large trainable gain: free-text abstention on insufficient inputs rises from .16 to .93 by dose 480 and continues toward 1.00 at higher dose (249-family branch) — while false abstention rises from .01 and eventually crosses the preregistered ≤.10 hard constraint (.11 at the 1,822-example cap), with flat retention [curves_ans_formal_e500.json]. The ceiling is reachable; the admissible operating region is not the ceiling.

### 4.2 Local predictability, bounded claim

On the strongest-signal endpoint family (format interface compliance), leave-one-dose-out prediction with a small frozen form library attains MAE .037 versus .073/.082/.073 for nearest-dose/log-linear/constant baselines, with interpolation errors inside the 3-seed noise band [fig6 source_data.json]. We claim local dose-response predictability for this endpoint family; we do not assert grid-wide predictability of all endpoints.

### 4.3 Collateral effects and domain dependence (Fig. 3)

Repairability is domain-conditional in three distinct ways [transfer_matrix_k500.json; ktgt_scores; ksparse_matrix.json]:

**A repair can create a new failure in a domain it never trained on.** Reasoning-format training collapses Knowledge candidate judgment: on the 500-family Knowledge suite, correct-candidate decision accuracy falls .608→.070 at dose 60 while contract-following stays ≈.98–1.0 and final-answer accuracy falls in tandem (.602→.208) [transfer_matrix_k500.json cc_attempt fields; provenance: NUMBER_PROVENANCE_fmt2K.md]. The interface survives; the judgment inside it is destroyed — the same form/judgment dissociation the base profile exhibited (§2), now *induced* by a repair.

**A repair's harmful direction can reverse across domains.** High-dose revision collapses KEEP in Reasoning but produces the opposite failure in Knowledge — an all-KEEP policy (wrong-candidate joint .00/.00/.00 across 3 targeted seeds) [ktgt_scores KRV-1493-S42/43/44].

**A repair's cost can export.** The answerability Pareto cost crosses domains: Knowledge false-abstain rises .25→.44 under Reasoning-answerability training [transfer_matrix_k500.json ANS rows].

### 4.4 Measurement stability

Several apparent repair effects from smaller evaluations failed to replicate at formal evaluation scale — a format content-tax, an evidence rise–fall, a revision abstention-tax, and a Knowledge-answerability retention cost; each retraction is ledgered [qc/INSTRUCTION_C29/C32; ktgt_scores for the KAN case]. All repairability claims in this section are stated at the 529/249-family, anchor-3-seed level. Findings that did not replicate do not appear in this paper as evidence.

---

## 5. Does Atomicity Imply Additivity? (RQ3 — the pivot)

**RQ3: Does atomicity in evaluation imply additivity in training?**

**The natural hypothesis, preregistered.** If repair responses composed additively, a mixture's endpoint vector would be the placebo baseline plus the sum of each family's in-domain dose response: Δs_mix ≈ Σ_i Δs_i(n_i). We froze this prediction — six mixture arms over the pruned active set {format, answerability}×{R, K, IF} plus tri-domain clean replay, with per-arm compositions, family prefixes, predicted endpoint vectors, predicted utilities, constraint thresholds and hashes committed before any training [MIXTURE_SPEC_FROZEN.json].

**The hypothesis fails.** Opening the six arms: predicted ranking versus actual ranking correlates at Spearman −0.43, and utility-level MAE is .054, exceeding seed noise [MIXTURE_OPEN_RESULT.json]. Among constraint-valid arms the actual ordering is uniform .602 > retention-constrained .576 > predicted-optimal .569 > worst-repair .540 > replay .533 — the additive model's top pick finished third, and the arm it ranked last (uniform) finished first. We do not soften this result; it is the paper's scientific pivot: atomicity in evaluation does not imply additivity in training.

**The constraint machinery works.** The raw-utility maximum (failure-frequency, .634) is disqualified by the frozen false-abstain threshold (.20 > .10) [MIXTURE_OPEN_RESULT.json constraint_filtered_ranking]. A recipe-selection framework that cannot reject a constraint-violating winner would be decorative; this one rejected it before any post-hoc judgment.

**The residuals are systematic, not noise.** Diverse multi-component arms are under-predicted (uniform +.069, failure-frequency +.093) while concentrated arms are over-predicted (predicted-optimal −.054, worst-repair −.034) [MIXTURE_OPEN_RESULT.json residuals]. This structure is what §6 accounts for.

---

## 6. Conditional Composition of Atomic Repairs (RQ3 — structure)

**Rescue design (frozen).** Six targeted runs, all structurally identical to the mixture arms (2,000 examples, tri-domain carrier, shared 54 steps), designed before results were seen [RESCUE_SPEC_FROZEN.json]: three single-repair bridge arms (fmt_R@30, ans_R@480, ans_K@30 on the mixed carrier), one in-domain pair (fmt_R+ans_R), one cross-domain pair (ans_R+fmt_K), and one half-dose uniform (6×50).

**Pairwise interactions are not the dominant cause.** The tested pairwise interactions are small — in-domain −.007, cross-domain −.015 — too small to account for the observed mixture residual [RESCUE_OPEN_RESULT.json]. (Two pairs were tested, not all.)

**Structure A: carrier dependence.** Single-repair gains measured against a clean single-domain carrier need not survive on the mixture carrier: on the tri-domain carrier, the fmt_R and ans_K bridge deltas collapse to ≈0 (−.004, −.003) while ans_R survives (+.059) [RESCUE_OPEN_RESULT.json deltas]. Formally, Δs_i(n | C) is not carrier-free: a repair's response is conditional on the training mixture in which it is embedded.

**Structure B: a diversity-by-dose regime.** After removing baseline and bridge terms, the remaining residual splits cleanly by composition type at the tested dose resolution (300/600/1200): full six-cell coverage at total intervention ≥600 carries a premium (uniform +.078, failure-frequency +.109), while a concentrated 1,200-example single-repair arm (−.004) and a diverse-but-small 300-example arm (−.018) carry none [INTERACTION_CORRECTION.json points]. We describe this as a threshold-like diversity-by-dose effect observed at coarse resolution — a development-family-discovered composition structure, not a claimed universal threshold.

**Conditional repair composition.** The targeted rescue accounts for the dominant residual patterns with these two structures. Composition is governed not by a sum but by a conditional map:

Δs = F(repair, dose, domain, carrier, composition).

The corrected prescription model is the additive backbone plus (i) bridge-calibrated single-repair terms and (ii) the diversity-by-dose term [INTERACTION_CORRECTION.json model]. Both structures were identified on the Qwen development family; §7 tests whether the corrected package — as a whole — predicts prospectively. We do not claim carrier dependence or the diversity regime as universal laws, and the held-out test in §7 is a package-level validation, not a mechanism-level ablation of each structure.

---

## 7. From Atomic Diagnosis to Prospective Prescription (RQ4)

**RQ4: Can conditional repair structure prospectively prescribe SFT for a held-out model family?**

**Protocol with no tuning entry point.** The end-to-end pipeline is: New Model → Atomic Diagnosis → Minimal Calibration → Frozen Repair Model → Predicted Prescription → Blind Validation. After the §6 corrections were frozen, the development family (Qwen) was formally closed. The held-out family (Llama-3.1-8B-Instruct) was **held out from response-model fitting and composition-correction development** — no Llama artifact existed when the calibration rule, recalibration formula, recipe search space, baseline compositions, seed allocation, and the verdict table with outcome definitions were committed [LLAMA_CALIBRATION_RULE_FROZEN.md; LLAMA_VERDICT_TABLE_FROZEN.md]. The new model's atomic profile enters the mechanical pipeline only through whitelisted fields. Exactly two calibration runs were executed (a tri-carrier replay arm and a single ans_R@480 bridge arm), yielding one scalar: scale = δ^L_ansR / δ^Q_ansR = .376 — a deliberately low-dimensional calibration [llama/calibration_out.json]. The mechanical search then produced the predicted prescription (ans_R 480 with full six-cell coverage, total 1,230), and all four arm predictions were committed before comparison training [LLAMA_PREDICTION_FREEZE.json].

**Result (Fig. 5).** The frozen four-arm ranking — predicted > uniform > heuristic > replay — was exactly recovered: actual utilities .463 > .407 > .340 > .303 (Spearman 1.0) [LLAMA_FINAL_RESULT.json]. The primary comparison, predicted versus uniform, was fully prospective (both arms trained only after the prediction freeze) and yields +.057, with seed-level separation: min(predicted) = .4457 > max(uniform) = .4416 across 3 seeds each. One replay seed served as a preregistered calibration anchor and was subsequently included in the replay mean; we therefore report **frozen-ranking accuracy** rather than four-arm total blindness. All frozen constraints pass (false-abstain ≈0 in every arm) [LLAMA_FINAL_AUDIT.json].

**Retention: a win of the clean kind (Fig. 5c).** The retention table answers the three natural objections in turn [LLAMA_ORIGINAL_RETENTION_TABLE.json]:
- *Versus replay — is this just a generic capability lift?* No: the prescription preserves clean-task performance (Original macro .696 vs .712, −.016 within noise) while adding +.160 utility. Clean scores barely move; robustness moves by sixteen points.
- *Versus uniform — why not just mix everything evenly?* Because the prescription wins on **both** axes (+.057 U, +.122 Original): uniform pays a hidden clean-Knowledge tax (K-original .463, below the base .616) that the prescription avoids (.596). Blind diversity has a cost that aggregate validation would misattribute.
- *Versus heuristic — why not select by clean benchmark?* The heuristic arm posts the best clean score of any trained arm (.741) with near-worst utility (.340): selecting by clean score inverts the right choice.
The base R-original strict-interface artifact is documented and excluded from base-vs-arm strict comparisons [table instrument_note].

**Calibration honesty.** Absolute magnitudes remain imperfectly calibrated: residuals run from −.005 (replay) through +.013 (heuristic) and +.065 (uniform) to +.092 (predicted) — ranking and direction transfer, while the gains of diverse repair mixtures are systematically underestimated; closing this calibration gap is the open modeling problem [LLAMA_FINAL_AUDIT.json prediction_vs_actual]. The replay arm's near-zero residual is the natural corollary of its anchor role, disclosed above.

**Scope.** This is cross-family evidence that the corrected prescription package transfers; it is not a mechanism-level ablation of carrier dependence or the diversity regime on Llama, and not a claim of universality.

---

## 8. Discussion and Limitations

**What conditional composition means for evaluation-driven training.** The additive failure is not an argument against atomic diagnosis — it is the reason diagnosis alone cannot prescribe. The unit that transfers is not the single-repair response curve but the corrected package: response curves + carrier-bridge terms + the diversity-by-dose term + constraints. Once that package is frozen, prescription for a new family required two runs and one scalar.

**Cost.** The held-out stage cost a base profile, two calibration runs, and one recipe training, versus blind K-arm mixture search with full training and evaluation per arm; the discovery stage is expensive but one-time and amortizable across new models. We state this as a cost discussion, not a compute-matched experimental claim (no formal comparison was run) [*planned appendix analysis, not yet generated*].

**Limitations.** (i) One held-out family — cross-family evidence, not universality. (ii) Magnitude calibration is imperfect and structured: diverse mixtures are underestimated most (+.092 on the predicted arm) [LLAMA_FINAL_AUDIT.json]; this is the open modeling problem. (iii) The diversity-by-dose regime is observed at coarse dose resolution (300/600/1200). (iv) U is one preregistered hierarchical utility; alternative-aggregation sensitivity is a *planned appendix analysis, not yet generated*, and is not cited as evidence. (v) Sparse K/IF grids are partly single-seed (direction-grade; the key reversal was 3-seed replicated, and the non-replicating KAN retention effect was retracted). (vi) Four representative repair families targeting selected failure structures; repairability regimes are observed patterns, one family per regime, not a universal taxonomy. (vii) Evaluation axes are synthetic controlled perturbations; SVAMP external holdout shows no dose-wise degradation [svamp_scores.json] and the IF domain uses real data sources, but deployment-style natural stress is untested.

---

## 9. Related Work (structured skeleton — citation pass pending)

- **Behavioral evaluation and robustness suites** [CITATION-REQUIRED cluster]: perturbation-based evaluation, contrast sets, checklist-style behavioral testing. Relation: we take the diagnosis side as given and supply the training-side response measurement.
- **Data selection and mixture optimization for LM training** [CITATION-REQUIRED cluster]: influence-based selection, mixture-proportion search, data curricula. Relation: these optimize; we ask when composition is predictable at all, and prescribe from frozen structure.
- **Scaling laws** [CITATION-REQUIRED cluster]: loss power laws. Contrast: our objects are local behavioral dose-responses, not loss scaling; we never claim a scaling law.
- **Reasoning faithfulness and intervention training** [CITATION-REQUIRED cluster]: measurement-side neighbors; we supply dose–response and composition evidence on the training side.
- **Abstention and calibration training** [CITATION-REQUIRED cluster]: relation to the answerability repair family and the false-abstain constraint.

---

## 10. Conclusion

Aggregate scores hide atomic failure structure. Atomic failures have heterogeneous repair dynamics: some are cheap to fix, some resist SFT, and some repairs create new failures. Atomicity in evaluation does not imply additivity in training. Modeling conditional repair composition turns diagnosis into prescription.

Concretely: a controlled atomic evaluation decomposed aggregate performance into failure structure; four representative repair families made repairability measurable and revealed four qualitatively distinct observed regimes; a preregistered additive composition bet failed, and targeted rescue accounted for the dominant residual patterns with carrier dependence and a diversity-by-dose regime; the corrected package, frozen, prospectively prescribed the winning constrained recipe on a model family held out from all of its development — preserving clean performance while adding sixteen points of utility over replay. SFT scales locally, but composes conditionally — and once the conditions are modeled, diagnosis becomes prescription.

---

### Assembly checklist (not part of the manuscript)
- Tables: T1 (taxonomy+budgets, from §2/§3), T2 (Qwen six-arm, §5), T3 (Llama final per-seed, §7), T4 (retention, §7) — data all in freeze artifacts.
- Figures: build per MAIN_FIGURE_STORYBOARD_V2_ATOMIC.md (V2.2 rules: Fig1 tile matrix, no radar; FA constraint line in Fig2).
- §9 citation pass + Intro [CITATION-REQUIRED] resolution.
- Abstract: to be written after §1 is approved.
- Terminology check on final pass: "component" only as implementation term; "classes" banned; regimes wording per C-45.
