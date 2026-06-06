# Atomic-Repair v2 — Repair on the 9 Atomic Capacities

v2 turns the diagnosis from the paper *"Same Benchmark Score, Different Failures"*
into **repair**. The paper shows the same domain score hides different broken
atomic capacities, each needing a different intervention (Table 1). v2 asks:

> Assume all facts are injected (like pretraining — knowledge floor ≈ 100%).
> The model still fails some atomic capacities at inference. **What traj data
> (plain CoT? CoT + skill labels?) repairs each one?**

Core premise (the "Beijing → China → Mandarin" intuition): the model *knows* both
facts but can't *compose* them. Only **synthetic** entities/rules test this cleanly.

## 9 atomic capacities (paper 3×3) + repair skill (= Table 1 intervention)

| | Augment | Ablate | Corrupt |
|---|---|---|---|
| **Knowledge** | K-Aug retrieval_cueing | K-Abl paraphrase_robust_recall | K-Cor contradiction_check |
| **Reasoning** | R-Aug decomposition_scaffold | R-Abl rule_reinjection | R-Cor step_verification |
| **Hybrid** | H-Aug bridge_retrieval | H-Abl provide_bridge_entity | H-Cor source_verification |

Plus **Clean** (keep_answer) as the over-repair control.

## Three stages

1. **Knowledge injection** (`inject.jsonl`, 351 = 345 entity facts + 6 invented rules):
   train == eval, **deliberately overfit** to a knowledge floor. Reasoning uses
   **invented operations** (quarn/drimble/…) so the model can't already know them;
   rules are injected, test operands are unseen.
2. **Bare 9-cell test** (`repair_eval.jsonl`, 600): inputs carry **NO** oracle facts
   (except H-Aug, where Augment = provide-cue by paper design). The model must use
   the injected knowledge.
3. **Repair traj** (relay from the inject checkpoint): **C** plain CoT
   (`{repair_trace, final_answer}`) vs **D** CoT+skill (adds `diagnosis, repair_skill`).
   Identical inputs → C-vs-D isolates the skill label.

## Conditions & gates

A zero-shot · B Fact-only · C Fact→CoT · D Fact→Skill+CoT.
**Gate 1 (clean):** base inject ≈ 0 (facts not in pretraining).
**Gate 2 (floor):** injected inject ≥ 90% (knowledge learned) — else repair is uninterpretable.

## Run

Local: `run_v2_00_generate` → `01_validate` (PASS) → `02_convert`.
Server (set `LF_DIR`, edit `model_name_or_path` → your Qwen3-8B-Instruct):
`09_predict_inject_base` (clean gate) → `10_train_inject` →
`20_predict_inject_floor` (learned gate) → `11`/`12` relay train →
`21–24` predict → pull `output_v2/predict_*/` back →
`30_evaluate` + `31_compare` → read `data_v2/comparison_v2.md`.

Data/eval written locally and committed; training runs on the server via LLaMA-Factory.
Validation is a hard gate (`validate_v2.py`): 9-cell counts, knowledge coverage,
R operands train/eval disjoint, form-id disjoint, no gold leakage, identical CoT/Skill+CoT inputs.
