# Scenario-Repair v3 — Evaluation-Guided Targeted Operator Induction

v3 upgrades the atomic-repair line from a 9-cell toy benchmark to **scenario-based
synthetic repair data over answer-update policies**. The 9 atomic cells
(K/R/H × Aug/Abl/Cor) are demoted to **failure injectors** — ways of breaking an item —
and are not the unit of training or evaluation. The unit is the **answer-update policy**.

## Thesis

> Evaluation is not just a score; it is a compass for data generation. Diagnose which
> answer-update capability a model lacks → generate that operator's targeted synthetic
> data → that capability rises; accumulate operators → assemble full repair capability.
> **Evaluation-guided synthetic capability induction.**

We test this honestly: if targeted data selectively repairs its operator (diagonal-dominant
selective matrix), the claim holds; if everything rises together, the gain is generic
action-commitment — reported either way.

## Seven answer-update policies

`keep_answer` · `override_wrong_claim` · `verify_bridge` · `verify_step` ·
`recompute` (rule/recall) · `use_provided_support` · `retrieve_or_abstain`

Grouped by `update_decision`: keep / update / retrieve_or_abstain. Output is the
v2.1-proven **actionized** format: `{update_decision, update_policy, repair_trace, final_answer}`
with the trace prefixed `Action: <policy>.`. Abstain items emit `final_answer: null`.

## Scenario surface

Bare oracle questions are wrapped in natural user phrasing (`scenario_templates.py`,
train/eval disjoint), optionally LLM-paraphrased via the `claude` CLI
(`scenario_api.py`, cached, leak-checked, falls back to seeds with no API). The oracle,
failure injection, policy, and gold answer are **always local and deterministic** — the
LLM never touches the answer.

## The new injector: U-Abl (abstain)

Underspecified problems drop the anchor entirely ("I saw an artwork somewhere — what
country is the artist from?"). The correct action is `retrieve_or_abstain` with
`final_answer: null`. A model that guesses a concrete answer — even a lucky-correct one —
scores **wrong**; this measures calibration, not accuracy.

## Experiments

1. **Scenario-based Actionized Repair** — A zero-shot / B Fact-only / C Fact→CoT /
   D Fact→Actionized. Does knowledge-only still fail, is actionized still most stable,
   does abstain work, under user-like surface?
2. **Targeted Operator Induction (main)** — train one policy's data at a time from the
   Fact-only checkpoint → evaluate all policies → **selective repair matrix**
   (rows = trained policy, cols = eval policy, value = gain over Fact-only). Diagonal
   dominance ⇒ on-target induction.
3. **Cumulative Curriculum** — M1…M6 accumulate operators; per-policy accuracy curve.
4. **Controls** — same-size random data (volume vs on-target) and wrong-target data
   (does the operator label carry signal).

## Metrics

per-policy / per-scenario accuracy, false-keep, accept-rates, **abstain correctness**,
plus **Targeted Repair Gain** = Acc(trained on X, eval X) − Acc(Fact-only, eval X) and
**Selectivity** = targeted gain − mean off-target gain.

## Run

```bash
bash scripts/run_v3_00_generate.sh           # add --use-api to paraphrase scenarios
bash scripts/run_v3_01_validate.sh           # hard gate: policy coverage, abstain null, no leak
bash scripts/run_v3_02_convert.sh            # LF + per-policy/cumulative/control splits
# server (set LLAMA_FACTORY_DIR, MODEL); all branches relay from the v2 inject checkpoint:
bash scripts/run_v3_10_train_actionized_and_cot.sh
bash scripts/run_v3_11_train_targeted.sh
bash scripts/run_v3_12_train_cumulative.sh
bash scripts/run_v3_13_train_controls.sh
bash scripts/run_v3_20_predict_all.sh
# pull predictions back -> data_v3/predict_outputs/predict_<name>/, then:
bash scripts/run_v3_30_eval_all.sh           # -> data_v3/results/comparison_v3.md
```

Data is synthetic, seeded, oracle-verifiable; training is LLaMA-Factory full-FT relayed
from the existing v2 knowledge-injection checkpoint (no re-injection). v2/v2.1 untouched.
