# Atomic-Repair v0 — Review Document

A self-contained walkthrough of **what this project is, how the data was built, how the
model was trained, and how it was evaluated**, written for a reviewer who has not seen
the code before. Every number and field name below is traceable to a file in this repo.

- Repo: `github.com/xingweiqu/atomic-repair-sft` (public)
- Status: v0 data shipped; Qwen3-8B-Base full fine-tuned and evaluated once on held-out eval.
- All data generation is local, deterministic (seeded), and oracle-verifiable. No API, no GPU for data.

---

## 1. What problem is this?

We train a model to act as an **atomic-repair agent**. Given a `problem` and a
`tentative_answer`, the model must return a JSON object with four fields:

| field | meaning |
|-------|---------|
| `diagnosis` | what kind of failure (if any) the tentative answer has |
| `repair_skill` | which repair operation applies |
| `repair_trace` | a short natural-language reasoning trace doing the repair |
| `final_answer` | the corrected answer (or the original, if nothing was wrong) |

The model is graded on whether it (a) detects the failure type, (b) picks the right
repair skill, and (c) produces the correct final answer — without "over-repairing" a
correct answer.

The design follows the **LLM-Physics / iGSM** idea: build a symbolic oracle world, then
realize it deterministically into natural language. That gives every example a
programmatic oracle, so a validator can reject anything ungrounded, and the gold answers
are checkable by construction rather than by trusting a generator model.

---

## 2. The five cells (the task taxonomy)

Each item belongs to exactly one **cell**. A cell binds 1:1 to a `(diagnosis, repair_skill)`
pair (enforced by the validator). Source: `generate_repair_data.py` → `CELL_SPEC`.

| cell | what's wrong with the tentative answer | diagnosis | repair_skill | should_repair |
|------|----------------------------------------|-----------|--------------|---------------|
| **H-Aug** | The 2-hop bridge fact is missing from the problem; the model must retrieve it | `missing_bridge_fact` | `retrieve_bridge_fact` | yes |
| **H-Abl** | The bridge **entity** is masked out of the problem; the model must recover it | `bridge_entity_missing` | `recover_bridge_entity` | yes |
| **H-Cor** | A **wrong bridge** is planted in the problem; the tentative answer accepted it | `wrong_bridge_contamination` | `bridge_source_verification` | yes |
| **K-Cor** | A 1-hop question with a **wrong factual claim** planted; tentative accepted it | `wrong_factual_claim` | `contradiction_check` | yes |
| **Clean** | Nothing is wrong; the tentative answer is correct | `no_failure_detected` | `keep_answer` | **no** |

H-* = "hybrid" 2-hop reasoning cells (book → author → nationality). K-Cor = 1-hop
knowledge. Clean = the negative control that tests whether the model resists
over-repairing.

**Scope note (v0):** there are no R-* (pure-reasoning) cells, no wrong-skill negatives,
and no preference negatives. This was deliberate — the parent probing paper showed R-*
perturbations don't yet produce a clean repair-vs-no-repair signal.

---

## 3. How the data is built

All in `generate_repair_data.py`, ~700 lines, pure Python, seeded (`--seed 42`).

### 3.1 Synthetic entity inventory

Every entity is **fictitious but plausible-sounding** — `Lydoria`/`Lydorian`,
`Maria Voss`, `Silver River`, `Hesperin Dynamics`, etc. (hardcoded pools at the top of the
file). This is load-bearing: because no real-world fact is involved, **pretraining
knowledge cannot leak in**, and the validator can verify every gold answer against the
symbolic world. It also means the model genuinely cannot "recall" these facts — see §6.

### 3.2 Six relation families

Each family is a 2-hop chain `head → bridge → tail`:

| family | head → bridge → tail |
|--------|----------------------|
| `book_author_nationality` | book → author → nationality |
| `city_country_currency` | city → country → currency |
| `company_founder_nationality` | company → founder → nationality |
| `product_company_country` | product → manufacturer → HQ country |
| `artwork_artist_country` | artwork → artist → birth country |
| `scientist_discovery_field` | scientist → discovery → field |

The symbolic graph is built by `build_family_graph()`: heads, bridges, tails are mapped
**round-robin by index** (`_zip_round_robin`), so every edge `(head, rel1, bridge)` and
`(bridge, rel2, tail)` is fully recorded and deterministic.

### 3.3 Three surface forms

Each item is rendered in one of three surfaces (`SURFACE_WEIGHTS`, target mix **80 / 15 / 5**):

- **naturalized** (~80%): fluent English question — "What is the nationality of the author who wrote Silver River?"
- **fact_table** (~15%): "Facts: … / Question: …" bullet style.
- **compact** (~5%): lightweight formal notation — "Q: nationality(author_of(Silver River)) = ?"

The mix keeps the model from latching onto a single surface; we never train on 100%
symbolic or 100% prose. (The target is 80/15/5; the **realized** train mix is **74/17/9** —
stochastic per-item sampling, within tolerance, not separately rebalanced.)

### 3.4 How each cell's `problem` / `tentative_answer` is constructed

Per `build_record()`:

- **Clean**: render the plain question; `tentative_answer = gold = tail`. No repair.
- **H-Aug**: plain question, but `tentative_answer` = a wrong same-type tail (a different
  nationality from the pool). The bridge fact is absent, so the answer is "unsupported."
- **H-Abl**: the bridge entity is stripped from the question (the template's `ablate`
  field uses "this novel" instead of the title, or `[MASK]` in fact-table/compact), and an
  opaque `Case #NNNN-NN` id is prefixed so ablated items are distinct strings without
  leaking the head.
- **H-Cor**: a **wrong bridge** is injected into the problem ("It is widely said that
  Silver River was written by {wrong_bridge}"). The wrong bridge's *real* tail is looked up
  from the graph (not random), so the planted wrong answer is type-consistent and
  oracle-verifiable. `tentative_answer` = that planted wrong tail.
- **K-Cor**: a 1-hop question about the `bridge → tail` edge, with a wrong claim injected
  ("Some sources state {bridge} is {wrong_tail}"). `tentative_answer` = the wrong tail.

For every cell the generator also emits `oracle_facts` (the gold sentences) and
`symbolic_facts` (the `[head, rel, bridge]` triples), plus a `repair_trace` that walks the
oracle facts to the gold answer.

### 3.5 Held-out generalization (what makes eval "unseen")

Two independent hold-out axes are enforced (`split_edges_for_family`):

1. **Templates**: each family has disjoint `templates_train` and `templates_eval` string
   templates. Eval questions are phrased with wordings the model never saw at train.
2. **Entities**: ~25% of **heads** and ~25% of **bridges** are independently held out, so
   an eval row has **both** a held-out head and a held-out bridge.

**Known caveat (v0):** all six relation families appear in both train and eval —
**family-level OOD is not held out**. (Flagged in the README as future work.)

### 3.6 Counts

`TARGET_COUNTS` →

| split | H-Aug | H-Abl | H-Cor | K-Cor | Clean | total |
|-------|-------|-------|-------|-------|-------|-------|
| train | 400 | 400 | 500 | 400 | 400 | **2,100** |
| eval  | 100 | 100 | 150 | 100 | 100 | **550** |

Uniqueness is enforced on the **`(problem, tentative_answer)` pair**, not on `problem`
alone — H-Aug and Clean intentionally share the same `problem` text but differ in
`tentative_answer` (same surface, different failure mode).

---

## 4. How the data is validated

`validate_repair_data.py` exits non-zero on any failure and always writes a report. It is
the contract surface — the dataset is not allowed to ship if any check fails. It verifies:

- expected `(split, cell)` counts; id uniqueness; `(problem, tentative)` pair uniqueness;
- `final_answer == gold_answer` for every row;
- Clean: `tentative == gold`, `should_repair == False`, `planted_wrong_answer is None`;
- non-Clean: `tentative != gold`, `should_repair == True`;
- H-Cor / K-Cor: `planted_wrong_answer` present, `!= gold`, and `tentative == planted_wrong_answer`;
- `diagnosis` / `repair_skill` strings match the cell mapping;
- `oracle_facts` and `symbolic_facts` non-empty;
- `repair_trace` contains at least one 4+-char token from some oracle fact (cheap groundedness check);
- LF JSON round-trips on 200 sampled rows;
- held-out templates and held-out (family, head) entities have **0 overlap** with train.

**Status on the shipped v0:** `PASS`, 0 failures (`data/data_sanity_report.json`).

---

## 5. How the model is trained

### 5.1 Conversion to training format

`convert_to_llamafactory.py` turns each raw row into an alpaca-style example:

- **instruction** (fixed for every row): *"You are an atomic repair agent. Given a problem
  and a tentative answer, diagnose whether there is an atomic-capacity failure. If there is
  a failure, choose the correct repair skill and repair the answer. If there is no failure,
  do not over-repair. Return only valid JSON."*
- **input**: `Problem:\n{problem}\n\nTentative answer:\n{tentative_answer}`
- **output**: the 4-key JSON string (`diagnosis / repair_skill / repair_trace / final_answer`).

**Critical design choice:** the input **deliberately does not include `oracle_facts`.**
The model only sees the problem and the tentative answer. To repair the *content* it must
recover the missing/masked bridge entity from parametric knowledge. Since the entities are
fictitious (§3.1), this is a genuine generalization test, accepted as a feature, not a bug.

### 5.2 Training run (this evaluation)

- **Full-parameter fine-tuning** (not LoRA), at the user's request.
- Model: **Qwen3-8B-Base**. Hardware: **8×80G** (A100/H100-class).
- DeepSpeed **ZeRO-3** (`configs/ds_z3_config.json`), launched with `FORCE_TORCHRUN` over
  8 GPUs (`scripts/run_03b_train_full.sh`).
- Config (`configs/qwen3_8b_repair_full_sft.yaml`): full set, 3 epochs, lr 1e-5,
  effective batch 128 (per-device 4 × grad-accum 4 × 8 GPUs), cutoff 2048, bf16,
  gradient checkpointing.

| metric | value |
|--------|-------|
| train_loss | 0.340 |
| eval_loss | 0.430 |
| epochs | 3.0 |
| train_runtime | 241 s (~4 min) |

Low loss, small train/eval gap → not an optimization failure. Whatever fails below is a
generalization limit, not a fitting one.

### 5.3 Prediction

`run_04b_predict_full.sh` + `configs/qwen3_8b_repair_full_predict.yaml`: greedy decoding
(`do_sample: false`), max_new_tokens 512, on the 550 held-out eval rows. Output:
`output/qwen3_8b_repair_full_predict/generated_predictions.jsonl` (fields `prompt`,
`predict`, `label`). The full model checkpoint stays on the server (~16GB, not committed);
only the prediction file is pulled back for scoring.

---

## 6. How the model is evaluated

`evaluate_predictions.py` — CPU-only, stdlib-only, does not touch model weights.

### 6.1 Alignment

To attach each prediction to its cell label, the scorer matches each prediction's `label`
(the gold output string) back to the raw eval row by **exact gold-output match**, falling
back to line index only if needed. On this run: **550/550 matched by gold-match, 0 by
index** — so cell attribution is exact, not order-assumed.

### 6.2 Metrics

- **JSON-valid**: did the model emit a parseable JSON object? (The parser takes the first
  balanced `{...}`, so trailing garbage after a valid object doesn't penalize.)
- **diagnosis / repair_skill / final_answer**: each field vs gold. `final_answer` is
  whitespace/case/trailing-punctuation normalized; the other two are exact string match.
- **exact (3/3)**: all three decision fields correct AND valid JSON.
- **over-repair on Clean**: Clean rows where the model predicted a repair (not `keep_answer`
  / `no_failure_detected`).
- **under-repair on non-Clean**: rows that needed repair but the model said no-op.
- **repair-skill confusion matrix**, and **held-out vs seen entity** breakdown.
- **bootstrap 95% CIs** (percentile bootstrap, deterministic stdlib RNG) on every rate.

### 6.3 Validation of the scorer itself

Before scoring the real run, the scorer was checked on synthetic inputs: a **perfect**
prediction file (predict == gold) → all metrics 100%, over/under-repair 0; and a
**deliberately broken** file (injected wrong answers, over-repairs, invalid JSON) → each
metric moved by exactly the injected amount, independently. So the numbers below reflect
the model, not scorer artifacts.

---

## 7. Results (550 held-out)

| cell | n | JSON-valid | diagnosis | repair_skill | final_answer | exact (3/3) |
|------|---|-----------|-----------|--------------|--------------|-------------|
| H-Aug | 100 | 100% | 30% | 30% | 0% | 0% |
| H-Abl | 100 | 100% | 100% | 100% | 4% | 4% |
| H-Cor | 150 | 100% | 100% | 100% | 0% | 0% |
| K-Cor | 100 | 100% | 100% | 100% | 6% | 6% |
| Clean | 100 | 100% | 96% | 96% | 95% | 95% |
| **overall** | 550 | 100% | 86.6% | 86.6% | 19.1% | 19.1% |

(Point estimates; full CIs in `data/eval_report.json`. Overall final_answer 95% CI is [15.8, 22.7].)

Failure modes:
- **Over-repair on Clean: 4%** — the model rarely "fixes" a correct answer.
- **Under-repair on non-Clean: 15.6%** — **all of it is H-Aug** (70/100 H-Aug rows read as
  `no_failure_detected`). Skill confusion confirms: `retrieve_bridge_fact` predicted as
  `keep_answer` 70 times.

### 7.1 Reading the results

Three skills, learned to three very different degrees:

1. **Output format — fully learned.** 100% JSON-valid everywhere. (Caveat: generations
   often don't stop cleanly after the closing brace — trailing unrelated tokens. Doesn't
   affect scoring, but EOS/stop-token hygiene is a v0.1 to-do.)

2. **Diagnosis + skill selection — learned everywhere except H-Aug** (~100% on H-Abl /
   H-Cor / K-Cor, 96% Clean). The repair taxonomy is learned; the model is a competent
   "router."

3. **final_answer (content repair) — not learned (0–6%), by design.** Because the input
   withholds the facts AND the entities are fictitious, the model cannot recall the bridge
   entity. Deep-dive on the failures:
   - H-Aug: 69/100 copy the tentative verbatim, 31 hallucinate a fresh wrong answer, 0 hit gold.
   - H-Cor: 145/150 wrong answers are fresh hallucinations (model knows it's wrong, replaces with noise).
   - K-Cor: the 6 "correct" finals are coincidence — the model's most frequent K-Cor output
     is `caltorian`, but the 6 hits are all `lydorian` (zero overlap). Effectively 0%.

   So `final_answer ≈ 0` is the dataset doing its job: a **true-generalization lower bound**
   that rewards real recall/reasoning, not surface pattern-matching.

### 7.2 The one informative asymmetry

H-Aug is the only cell where **detection** also fails (diagnosis 30%): the model
over-trusts a fluent-but-unsupported tentative answer and declines to repair. The hardest
failure to *detect* is the silently-missing-fact case; explicit contradictions (H-Cor,
K-Cor) are caught 100%.

---

## 8. Limitations / what a reviewer should push on

1. **final_answer is uninformative in isolation.** It's ~0 by construction. Report
   diagnosis/skill accuracy as the first-class metric; treat final_answer as a recall probe.
2. **No facts-in-input condition.** v0 can't separate "can't recall a fact" from "can't use
   a fact it's given." The proposed v0.1 fix: add a control cell with `oracle_facts` in the
   input — final_answer should jump if the model can apply provided facts.
3. **No family-level OOD.** All 6 families are in both splits; generalization to a brand-new
   relation type is untested.
4. **Single run, single model, single seed.** No variance bands across seeds; no comparison
   vs the untrained base or vs smaller models.
5. **Stop-token behavior.** The model doesn't terminate cleanly after the JSON.
6. **Synthetic-only.** Findings are about reasoning/format generalization on fictitious
   entities, not real-world factual repair.

---

## 9. Files (where to look)

| file | what |
|------|------|
| `generate_repair_data.py` | the data generator (families, cells, surfaces, splits) |
| `validate_repair_data.py` | the hard-check validator (fail-stops on contract violations) |
| `convert_to_llamafactory.py` | raw JSONL → LLaMA-Factory alpaca JSON + `dataset_info.json` |
| `configs/qwen3_8b_repair_full_sft.yaml`, `ds_z3_config.json` | full-FT training config |
| `configs/qwen3_8b_repair_full_predict.yaml` | prediction config |
| `scripts/run_03b_train_full.sh`, `run_04b_predict_full.sh` | server run scripts |
| `evaluate_predictions.py` | the scorer (per-cell acc, CIs, failure modes) |
| `data/repair_raw_{train,eval}.jsonl` | raw items with full oracle fields |
| `data/repair_lf_{train,eval}.json` | training-format items |
| `data/eval_report.{json,md}` | scored results |
| `output/qwen3_8b_repair_full_predict/generated_predictions.jsonl` | 550 raw predictions |
| `ANALYSIS_full_ft_v0.md` | technical analysis writeup |
| `README_plain_zh.md` | plain-language (Chinese) explainer |
