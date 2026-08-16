# MAIN_FIGURE_STORYBOARD — 5 main figures

## Fig 1 — Evaluation → Response → Prescription (+ why clean scores fail)
- **Question**: what decision problem does this paper solve, and why can't benchmarks solve it?
- **Panels**: (a) pipeline schematic: failure profile → component×dose×domain response → corrected composition model → constrained recipe → held-out validation; (b) motivating scatter, x=Original macro, y=U: heuristic lower-RIGHT (.741,.340 — best clean, near-worst U), predicted upper-middle (.696,.463), replay lower-right (.712,.303), uniform lower-left (.574,.407). Two labeled comparisons drawn as arrows: **predicted vs replay** (Original .696≈.712 but U .463≫.303 — clean score cannot see a 16pp robustness difference) and **heuristic vs predicted** (Original .741>.696 but U .340<.463 — picking by clean score selects the wrong recipe).
- **Data**: LLAMA_ORIGINAL_RETENTION_TABLE.json (panel b); schematic (panel a).
- **Takeaway**: near-identical clean scores can hide a 16pp robustness gap, and ranking by clean score can invert the right choice; the pipeline tells recipes apart *before* training.
- **Caption draft**: "Clean-task accuracy does not rank SFT recipes: the arm with the best Original score is nearly the worst overall (b). We prescribe recipes from measured response profiles instead (a)."

## Fig 2 — Four heterogeneous response profiles (Reasoning discovery domain)
- **Question**: what do component dose-responses actually look like?
- **Panels**: 4 curves (Format interface saturation; Evidence flat; Revision KEEP/FIX seesaw with adopt overlay; Answerability target vs false-abstain Pareto), x = examples with q_d second axis, 3-seed anchor bars; per-condition n printed (529 core / 249 answerability).
- **Data**: curves_e500_all.json, curves_ans_formal_e500.json, dose manifests.
- **Takeaway**: no shared functional form — saturating, null, adverse, and constrained-gain shapes coexist.
- **Caption draft**: "SFT components exhibit structured but heterogeneous dose–response profiles; within each grid, intervention examples replace matched replay under a fixed protocol (529-family evaluation; answerability subset 249)."

## Fig 3 — Cross-domain collateral matrix
- **Question**: does a component's effect stay in its training domain?
- **Panels**: (a) heat matrix: R-trained components (rows: fmt/evd/rev/ans doses) × K-domain branch endpoints (cols), Δ vs placebo; highlight fmt→K candidate-decision collapse (.61→.07) with contract row intact; (b) K-revision reversal inset: R-domain high-dose (KEEP collapses) vs K-domain high-dose (all-KEEP), 3 seeds each.
- **Data**: transfer_matrix_k500.json, ktgt_scores, ksparse_matrix.json.
- **Takeaway**: gains need not transfer; collateral can transfer; direction can reverse — recipes must be judged on the full cross-domain vector.
- **Caption draft**: "Cross-domain response: format training collapses Knowledge candidate judgment while its interface contract survives (a); revision reverses direction across domains (b, 3 seeds)."

## Fig 4 — Additive failure and its anatomy
- **Question**: do single-component responses compose? (No.) What structure is missing?
- **Panels**: (a) frozen-predicted vs actual U for six Qwen arms, DQ'd failure_freq marked, ρ=−.43 annotated; (b) rescue decomposition bar chart: pairwise interactions (small), carrier-bridge deltas (fmt_R/ans_K→0, ans_R survives), diversity-by-dose cells (300-diverse −, 600/1200-diverse +, 1200-concentrated 0).
- **Data**: MIXTURE_SPEC_FROZEN, MIXTURE_OPEN_RESULT, RESCUE_OPEN_RESULT, INTERACTION_CORRECTION.
- **Takeaway**: the preregistered additive bet failed; controlled rescue attributes the residual to carrier dependence and a diversity-by-dose regime, not pairwise interactions.
- **Caption draft**: "Preregistered additive mixture prediction fails on the development family (a); six targeted rescue runs identify carrier dependence and a diversity-by-dose regime as the dominant corrections supported by the rescue (b)."

## Fig 5 — Held-out prospective opening
- **Question**: does the corrected, frozen model prescribe on a family it never saw?
- **Panels**: (a) timeline strip (freeze → 2 calibration runs → mechanical recipe → blind train → open) with commit hashes; (b) frozen-predicted vs actual U per arm with per-seed points (min pred > max uniform visible); (c) Original-vs-U Pareto (same axes as Fig 1b) showing predicted dominating uniform on both axes and matching replay's Original.
- **Data**: LLAMA_PREDICTION_FREEZE, LLAMA_FINAL_RESULT, LLAMA_FINAL_AUDIT, LLAMA_ORIGINAL_RETENTION_TABLE.
- **Takeaway**: 4/4 frozen ranking, +5.7pp over uniform under passing constraints, clean performance intact — with magnitude calibration honestly imperfect.
- **Caption draft**: "Prospective held-out test: with corrections frozen and two calibration runs, the mechanically generated recipe ranks first exactly as predicted (b), preserving clean performance while adding +16pp utility over replay (c)."
