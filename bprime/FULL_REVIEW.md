# Atomic-Capacity Repair — Evaluation-Guided Operator Induction and Its Causal Attribution

**Consolidated, self-contained review document (v2 → v4 + B′).**
Repo `atomic-repair-sft`, branch `scenario-repair-b-prime` (contains v3/v4/B′).
Date 2026-06. All numbers re-scored from shipped `predict_outputs` (no retraining for B′).

---

## 0. TL;DR / thesis

We study a **closed evaluation→training loop**: diagnose which answer-update *operator* a model
is weak at, synthesize targeted repair data for that operator, retrain, and measure whether the
weakness is repaired. Across a **synthetic world (v3)** and a **real arithmetic domain (GSM8K, v4)**,
the central result (B′) is a **causal attribution with a modulation law**:

> Repair / operator-induction reliably induces a **generic repair DECISION** ("don't keep the
> wrong value"). Whether that decision converts into **benchmark accuracy** is **gated by the
> base model's underlying-ability margin**: when the underlying ability is absent (synthetic v3,
> margin ≈ 0) the intervention *also injects the ability* and final accuracy jumps; when it is
> already present (real arithmetic v4, margin ≈ 0.3–0.4) the intervention *cannot inject ability*
> and the final-answer gain is capped by the base's arithmetic.

This reframes the paper's success criterion from "operator selectivity (does the diagonal spike)"
to **"can the intervention effect be causally attributed to the decision layer vs the underlying-
ability layer, and is the benchmark net gain = decision gain × ability margin."**

---

## 1. Research question & framing

- **Atomic capacity** = the minimal repairable behavioural unit. We decompose a 3×N failure matrix
  (Knowledge / Reasoning / Hybrid × Augment / Ablate / Corrupt) into **failure injectors** (tools to
  build broken items) and **answer-update operators** (the unit of repair).
- The 9-cell failure types are **demoted from labels to data-generation tools**; the real unit is the
  operator (`keep / override_wrong_claim / verify_bridge / verify_step / recompute /
  use_provided_support / retrieve_or_abstain`).
- Output schema (actionized, fixed across versions):
  `{update_decision, update_policy, repair_trace, final_answer}`, trace prefixed `Action: <op>.`

---

## 2. Method

- **Two domains, one framework.** v3 = closed synthetic world (made-up relations + made-up
  operators; "recompute" = table lookup). v4 = GSM8K (real arithmetic; "recompute" = real
  computation). Same schema + same scorer ⇒ directly comparable.
- **No knowledge injection in v4** (arithmetic *is* the knowledge); diagnose from the base instruct
  model. Train items only from the train split, eval only from test, zero item overlap.
- **Training:** LLaMA-Factory full-parameter SFT, DeepSpeed ZeRO-3. v3 relays from a fact-injected
  ckpt; v4 relays from BASE (Qwen3-8B).
- **Conditions per domain:** `diagnosis_base` (no repair) · `scaffold/floor` (format-only) ·
  `actionized_full` (all operators) · `targeted_<op>` (one operator only) · controls
  (`random_<op>` same-size, `wrongtarget_<op>` mislabeled) · transfer (un-perturbed test).

---

## 3. Pipeline & data

| | train | eval | shortcut gate (masked, <0.65) |
|---|---|---|---|
| v3.1 (synthetic) | 2640 | 720 | 0.458 PASS |
| v4 (GSM8K) | 3000 | 480 | 0.507 PASS |

v4 eval per operator: verify_step 80 / override 80 / recompute 80 / keep 160 / abstain 80.
Both domains pass the shortcut audit (a TF-IDF classifier predicting `update_decision` from the
masked problem is at chance), so the decision is not a surface marker.

---

## 4. Engineering corrections (honest log — each changed a conclusion)

| # | symptom | root cause | fix | effect on conclusions |
|---|---|---|---|---|
| 1 | **floor underfit** | `scaffold_only` 3 epoch (~37 steps), loss 2.53, parse 0.68–0.80 (format collapse) | retrain convergent `scaffold_conv` (30 epoch, parse 100%) | **flipped the v4 matrix signs** (see §5.2) |
| 2 | transfer "Cannot find valid samples" | bare-numeric reference dropped by LF | reference = full gold reasoning + `The final answer is N.` | unblocked transfer |
| 3 | transfer base looked like 2% | gold extracted the first number in the reasoning, not the final line | extract via `FINAL_RE` | base really **94%** |
| 4 | transfer 268/300 truncated | `max_new_tokens` 384 < Qwen3 `<think>` | bump to 2048 | valid transfer |
| 5 | "compute cells negative / abstain +98" | scored against the underfit floor (#1) | re-score on convergent floor | **retracted**; see §5 |

**Note:** repair-eval predictions are NOT truncated (~200 chars ≪ 384, JSON closed); drift is an
out-of-domain phenomenon only (§5.5).

---

## 5. Results

### 5.1 Conditions (v4, final-answer accuracy, convergent floor)

| condition | overall |
|---|---|
| diagnosis_base (no repair; format-mismatch lower anchor) | 33% |
| scaffold_conv (FLOOR) | 56% |
| actionized_full (all operators) | 62% |

### 5.2 final-acc selective matrix (v4, gain over convergent floor)

| operator | gain (underfit floor → **convergent floor**) | selectivity |
|---|---|---|
| verify_step | −12 → **+4** | −5% |
| override_wrong_claim | −12 → **+10** | −3% |
| recompute | −16 → **+8** | +6% |
| retrieve_or_abstain | +98 → **+0** | −2% |

Convergent floor **removes the negative diagonals** (compute cells small-positive) **and removes the
abstain spike** (floor also reaches 100% — abstain is a format skill). Selectivity ≈ 0 ⇒ v4 is **not
operator-selective**; gains are generic.

### 5.3 Three-layer decomposition (decision vs ability) — the core re-scoring

`resist_wrong` = committed answer ≠ planted/tentative wrong value (decision only).
`ability|resist` = on the resisted subset, final == gold (lookup in v3, arithmetic in v4).
**`ability|resist` is NOT horizontally comparable across runs** (n_resist differs).

**v3 (synthetic, floor = scaffold_only):**

| cell | run | resist_wrong | ability\|resist (n) | final_acc |
|---|---|---|---|---|
| override | floor | 0.93 | 0.34 (55) | 0.32 |
| override | targeted | 1.00 | 0.95 (60) | 0.95 |
| verify_bridge | floor | 0.75 | 0.04 (45) | 0.03 |
| verify_bridge | targeted | 0.95 | 0.82 (57) | 0.78 |
| verify_step | floor | 1.00 | 0.00 (60) | 0.00 |
| verify_step | targeted | 1.00 | 0.93 (60) | 0.93 |
| recompute | floor | 0.99 | 0.13 (178) | 0.13 |
| recompute | targeted | 1.00 | 1.00 (180) | 1.00 |

**v4 (GSM, floor = scaffold_conv):**

| cell | run | resist_wrong | ability\|resist (n) | final_acc |
|---|---|---|---|---|
| verify_step | floor | 0.97 | 0.39 (78) | 0.38 |
| verify_step | targeted | 1.00 | 0.41 (80) | 0.41 |
| override | floor | 0.64 | 0.31 (51) | 0.20 |
| override | targeted | 0.99 | 0.30 (79) | 0.30 |
| recompute | floor | 0.60 | 0.42 (48) | 0.25 |
| recompute | targeted | 0.97 | 0.33 (78) | 0.33 |

**Reading:** in BOTH domains targeted induces the **decision** (resist_wrong up, e.g. v4 override
0.64→0.99). The split is in the **ability** column: v3 targeted *injects ability* (0.00→0.93,
0.04→0.82, 0.34→0.95); v4 targeted *cannot* (0.39→0.41, 0.31→0.30, 0.42→0.33).

### 5.4 ★ Modulation law (headline; `modulation_curve.png`)

x = floor `ability|resist` (base's underlying-op margin); y = **Δability|resist** (ability the
intervention injects = targeted − floor).

| domain | cell | x = floor ability | Δability (y) | Δfinal |
|---|---|---|---|---|
| v3 | verify_step | 0.00 | **+0.93** | +0.93 |
| v3 | recompute | 0.13 | **+0.87** | +0.87 |
| v3 | verify_bridge | 0.04 | **+0.78** | +0.75 |
| v3 | override | 0.34 | **+0.60** | +0.63 |
| v4 | verify_step | 0.39 | **+0.03** | +0.04 |
| v4 | override | 0.31 | **−0.01** | +0.10 |
| v4 | recompute | 0.42 | **−0.08** | +0.07 |

Strong **negative** relation between base ability margin and ability injected by the intervention.
(The user-defined `conversion = Δfinal/Δresist` is reported in the audit too, but its denominator
collapses in v3 where the floor already resists — `Δability` is the robust axis.)

### 5.5 Transfer (un-perturbed GSM8K; repair must not hurt base task)

| model | acc | answered-acc | no-answer (drift) |
|---|---|---|---|
| base | 94% | 100% | 23/300 (8%) |
| verify_step (single-op) | 68% | 95% | 91/300 (30%) |
| actionized_full (mixed) | 72% | 76% | 50/300 (17%) |

Arithmetic is **intact** when the model commits (answered-acc ≈ base). The accuracy drop is
**behavioural drift**: repair-trained ckpts treat plain items as repair tasks and emit a diagnosis
with no committed answer. **Mixed training halves the drift vs single-operator (17% vs 30%).**

### 5.6 Interference budget (single-operator vs mixed)

In-domain keep_answer accuracy (lower = more over-repair). v4: floor 0.76, mixed 0.83, single-op
0.35–0.46. Out-of-domain drift: base 8% / mixed 17% / single-op 30%. Qualitative rule (only 2
anchored-vs-unanchored points): a balanced keep/abstain **anchor dose** (present in mixed/scaffold,
absent in single-op) roughly halves drift. Not enough points to fit a curve.

### 5.7 v3 ↔ v4 side-by-side (shared operators, targeted gain)

| operator | v3 (synthetic) | v4 (GSM) |
|---|---|---|
| verify_step | 0→93 (**+93**) | 38→41 (+4) |
| override_wrong_claim | 22→95 (**+73**) | 20→30 (+10) |
| recompute | 13→100 (**+87**) | 25→32 (+8) |

v3 is operator-selective (diagonal spikes); v4 final-acc is flat — the real structure is at the
decision/ability layer (§5.3–5.4).

---

## 6. Interpretation (B′ thesis)

1. **Decision is inducible in both domains** (resist_wrong up; floor-independent: v4 targeted 0.99
   vs mixed 0.60 on override, both format-healthy). It is **generic, not operator-selective**
   (any targeted lifts all compute cells; consistent with v2.1's "action-commitment is generic").
2. **Ability is not injected when the base already has it** (v4 `ability|resist` flat ~0.35 for every
   run). Where the base lacks it (v3), targeted injects it (Δability +0.6..+0.9).
3. **Benchmark net gain = decision gain × ability margin.** v3: both obtained ⇒ final jumps.
   v4: only decision ⇒ final capped by arithmetic.
4. **Abstain** is a positive control (format skill; gain vanishes under a convergent floor),
   not an operator-selective induction.
5. **Cost of over-specialization:** single-operator training causes out-of-domain behavioural
   drift; mixed training mitigates it.

---

## 7. Limitations & threats to validity (please scrutinize)

1. **`ability|resist` is not horizontally comparable across runs** — the denominator is the
   resisted subset, which differs per run (floor/full resist less ⇒ smaller, easier subset ⇒
   inflated ability). Directional reads (v3 injects vs v4 doesn't) are robust; absolute cross-run
   arithmetic comparisons are not. *Round-2 todo: recompute ability on a matched-difficulty subset.*
2. **v3 floor may also be underfit** — `scaffold_only` keep-cell accuracy is only 0.22, the same
   smell as the v4 underfit floor. The B′ contrast survives (it rests on targeted absolute values:
   v3 ability 0.78–1.0 vs v4 0.30–0.46), but the v3 **x-axis margin** would be cleaner with a
   convergent v3 floor. *Candidate PHASE-1 retrain.*
3. **Modulation is currently a TWO-REGIME contrast, not a continuous curve** — two clusters
   (v3 margin≈0, v4 margin≈0.3–0.4). A reviewer may object "two points are not a curve."
   *This is exactly what v5 (a middle-margin domain) would fill.*
4. **selectivity ≈ 0 in v4** — must be stated plainly; v4 is generalizing decision induction, not
   operator-selective like v3.
5. **transfer `answered-acc` definition** — mixed model's 76% partly includes fallback-extracted
   numbers; the drift (no-answer) comparison 30% vs 17% is the robust part.
6. **diagnosis_base 33%** is a format-mismatch lower anchor (base doesn't emit actionized JSON), not
   the base's real ability (transfer shows 94%).

---

## 8. Status & next steps

- **Done & shipped:** v2/v2.1, v3 (selective matrix), v4 (GSM transplant, convergent floor,
  transfer, decision/ability split), B′ PHASE 0 (three-layer re-scoring + modulation law).
- **Can the paper stand WITHOUT v5?** **Yes**, as a two-regime causal-attribution result (§6).
  v5 is *reinforcement* (a middle-margin point → monotone curve), **not a gate.**
- **Open options (no server job currently running):**
  1. Freeze B′ two-regime story and write the paper.
  2. **v5** counterfactual multi-hop (real wiki schema + counterfactual values; expected to land at
     mid-margin between v3 and v4 — fills the curve).
  3. Retrain a **convergent v3 floor** (clean the §7.2 x-axis).
  4. **PHASE-1 probe**: Δlog p on server (ckpts are server-only) to bridge the original forward-only
     diagnostic to this training framework.

---

## 9. Reproduce (read-only; no retraining)

```bash
cd atomic-repair-sft
python3 -m bprime.bprime_audit                                    # three layers + modulation + plot
python3 -m gsm_repair_v4.evaluate_gsm                             # v4 final-acc matrix (conv floor)
python3 -m gsm_repair_v4.decision_analysis --floor scaffold_conv  # v4 decision/ability split
```

Key artifacts: `bprime/bprime_audit.md`, `bprime/modulation_curve.png`,
`data_v4/REPORT_v4_review.md`, `data_v4/results/{comparison_v4,decision_analysis_conv}.md`.
