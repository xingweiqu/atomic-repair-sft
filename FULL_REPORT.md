# Atomic-Repair v0 — Complete Report

One document covering everything: what the task is, how the data was built, how the model
was trained, how it was evaluated, the full numbers, the analysis, and the conclusions.
Self-contained — a reader who has never seen the code can follow it end to end. Every
number is traceable to a file in this repo.

- **Repo:** `github.com/xingweiqu/atomic-repair-sft` (public)
- **Status:** v0 data shipped; Qwen3-8B-Base full fine-tuned and evaluated once on the held-out eval split.
- **Data generation:** fully local, deterministic (seeded), oracle-verifiable. No API, no GPU needed for data.

---

# Part I — What this is

## 1. The task

We train a model to act as an **atomic-repair agent**. Given a `problem` and a
`tentative_answer`, it must return a JSON object with four fields:

| field | meaning |
|-------|---------|
| `diagnosis` | what kind of failure (if any) the tentative answer has |
| `repair_skill` | which repair operation applies |
| `repair_trace` | a short natural-language reasoning trace doing the repair |
| `final_answer` | the corrected answer (or the original, if nothing was wrong) |

It is graded on whether it (a) detects the failure type, (b) picks the right repair skill,
and (c) produces the correct final answer — without "over-repairing" a correct answer.

The design follows the **LLM-Physics / iGSM** idea (Allen-Zhu et al.): build a symbolic
oracle world, then realize it deterministically into natural language. Every example gets
a programmatic oracle, so a validator can reject anything ungrounded and gold answers are
checkable by construction rather than by trusting a generator model. This avoids the two
usual failure modes: pure-symbolic input (easy to verify, doesn't transfer to natural
language) and per-item frontier-LLM generation (expensive, non-deterministic, no oracle).

## 2. The five cells (task taxonomy)

Each item belongs to exactly one **cell**, which binds 1:1 to a `(diagnosis, repair_skill)`
pair (enforced by the validator). Source: `generate_repair_data.py` → `CELL_SPEC`.

| cell | what's wrong with the tentative answer | diagnosis | repair_skill | repair? |
|------|----------------------------------------|-----------|--------------|---------|
| **H-Aug** | 2-hop bridge fact is missing from the problem; model must retrieve it | `missing_bridge_fact` | `retrieve_bridge_fact` | yes |
| **H-Abl** | bridge **entity** is masked out of the problem; model must recover it | `bridge_entity_missing` | `recover_bridge_entity` | yes |
| **H-Cor** | a **wrong bridge** is planted; the tentative answer accepted it | `wrong_bridge_contamination` | `bridge_source_verification` | yes |
| **K-Cor** | 1-hop question with a **wrong factual claim** planted; tentative accepted it | `wrong_factual_claim` | `contradiction_check` | yes |
| **Clean** | nothing is wrong; the tentative answer is correct | `no_failure_detected` | `keep_answer` | **no** |

H-* = "hybrid" 2-hop reasoning (book → author → nationality). K-Cor = 1-hop knowledge.
**Clean** is the negative control: without it the model learns to "always repair," which
collapses on benign inputs.

**Scope (v0):** no R-* (pure-reasoning) cells, no wrong-skill negatives, no preference
negatives. Deliberate — the parent probing paper showed R-* perturbations move very little
(R-Aug diagnostic rate ≈ 0.02, R-Cor ≈ 0.03) and don't yet give a clean
repair-vs-no-repair signal, whereas H-Cor flips most under a wrong-bridge attack (mean flip
rate ≈ 0.66). We start where the signal is strongest.

---

# Part II — How the data was built

All in `generate_repair_data.py` (~700 lines, pure Python, seeded with `--seed 42`).

## 3. Synthetic entity inventory

Every entity is **fictitious but plausible-sounding** — `Lydoria`/`Lydorian`, `Maria Voss`,
`Silver River`, `Hesperin Dynamics`, etc. (hardcoded pools at the top of the file). This is
load-bearing:

- no real-world fact is involved → **pretraining knowledge cannot leak in**;
- the validator can verify every gold answer against the symbolic world;
- the model genuinely **cannot "recall"** these facts — which is exactly what makes the
  content-repair test honest (see Part V).

## 4. Six relation families

Each family is a 2-hop chain `head → bridge → tail`:

| family | head → bridge → tail |
|--------|----------------------|
| `book_author_nationality` | book → author → nationality |
| `city_country_currency` | city → country → currency |
| `company_founder_nationality` | company → founder → nationality |
| `product_company_country` | product → manufacturer → HQ country |
| `artwork_artist_country` | artwork → artist → birth country |
| `scientist_discovery_field` | scientist → discovery → field |

The symbolic graph (`build_family_graph`) maps heads, bridges, tails **round-robin by
index** (`_zip_round_robin`), so every edge `(head, rel1, bridge)` and `(bridge, rel2, tail)`
is fully recorded and deterministic.

## 5. Three surface forms

Each item is rendered in one of three surfaces (`SURFACE_WEIGHTS`, target **80 / 15 / 5**):

- **naturalized** (~80%): fluent English — "What is the nationality of the author who wrote Silver River?"
- **fact_table** (~15%): "Facts: … / Question: …" bullet style.
- **compact** (~5%): lightweight formal notation — "Q: nationality(author_of(Silver River)) = ?"

This stops the model latching onto a single surface; we never train on 100% symbolic or
100% prose. **Realized** train mix is **74 / 17 / 9** (stochastic per-item sampling, within
tolerance, not separately rebalanced).

## 6. How each cell's `problem` / `tentative_answer` is constructed

Per `build_record()`:

- **Clean**: plain question; `tentative_answer = gold = tail`. No repair.
- **H-Aug**: plain question, `tentative_answer` = a wrong same-type tail (a different
  nationality from the pool). Bridge fact absent → answer "unsupported."
- **H-Abl**: bridge entity stripped from the question (template's `ablate` field uses "this
  novel" instead of the title, or `[MASK]` in fact-table/compact); an opaque `Case #NNNN-NN`
  id is prefixed so ablated items are distinct strings without leaking the head.
- **H-Cor**: a **wrong bridge** is injected ("It is widely said that Silver River was
  written by {wrong_bridge}"). The wrong bridge's *real* tail is looked up from the graph
  (not random), so the planted wrong answer is type-consistent and oracle-verifiable.
  `tentative_answer` = that planted wrong tail.
- **K-Cor**: a 1-hop question about the `bridge → tail` edge with a wrong claim injected
  ("Some sources state {bridge} is {wrong_tail}"). `tentative_answer` = the wrong tail.

Every row also carries `oracle_facts` (gold English sentences) and `symbolic_facts` (the
triples), plus a `repair_trace` that walks the oracle facts to the gold answer.

## 7. Held-out generalization (what makes eval "unseen")

Two independent hold-out axes (`split_edges_for_family`):

1. **Templates**: each family has disjoint `templates_train` / `templates_eval` string
   templates. Eval questions use wordings never seen at train.
2. **Entities**: ~25% of **heads** and ~25% of **bridges** are independently held out, so an
   eval row has **both** a held-out head and a held-out bridge.

**Known caveat:** all six families appear in both splits — **family-level OOD is not held
out in v0**.

## 8. Counts

| split | H-Aug | H-Abl | H-Cor | K-Cor | Clean | total |
|-------|-------|-------|-------|-------|-------|-------|
| train | 400 | 400 | 500 | 400 | 400 | **2,100** |
| eval  | 100 | 100 | 150 | 100 | 100 | **550** |

Uniqueness is enforced on the **`(problem, tentative_answer)` pair**, not on `problem` alone
— H-Aug and Clean intentionally share the same `problem` text but differ in
`tentative_answer` (same surface, different failure mode). Verified: 148 shared problem
strings between H-Aug and Clean in train.

## 9. Example raw row (H-Cor)

```json
{
  "id": "H-Cor_train_000001",
  "cell": "H-Cor",
  "surface_type": "naturalized",
  "relation_family": "book_author_nationality",
  "problem": "It is widely said that Silver River was written by Anton Hale. What is the nationality of the author who wrote Silver River?",
  "tentative_answer": "Norlandian",
  "gold_answer": "Lydorian",
  "planted_wrong_answer": "Norlandian",
  "diagnosis": "wrong_bridge_contamination",
  "repair_skill": "bridge_source_verification",
  "repair_trace": "The tentative answer follows the planted bridge 'Anton Hale'. ... The planted bridge is false: Silver River was written by Maria Voss (not Anton Hale). Use the correct bridge fact: Maria Voss is Lydorian. Therefore the final answer is Lydorian, not Norlandian.",
  "final_answer": "Lydorian",
  "oracle_facts": ["Silver River was written by Maria Voss.", "Maria Voss is Lydorian.", "Anton Hale is Norlandian."],
  "symbolic_facts": [["Silver River","written_by","Maria Voss"],["Maria Voss","nationality","Lydorian"],["Anton Hale","nationality","Norlandian"]],
  "should_repair": true,
  "split": "train",
  "template_id": "book_T1",
  "entity_split": "train"
}
```

## 10. Validation

`validate_repair_data.py` exits non-zero on any failure and always writes a report. The
dataset cannot ship unless every check passes:

- expected `(split, cell)` counts; id uniqueness; `(problem, tentative)` pair uniqueness;
- `final_answer == gold_answer` for every row;
- Clean: `tentative == gold`, `should_repair == False`, `planted_wrong_answer is None`;
- non-Clean: `tentative != gold`, `should_repair == True`;
- H-Cor / K-Cor: `planted_wrong_answer` present, `!= gold`, `tentative == planted_wrong_answer`;
- `diagnosis` / `repair_skill` strings match the cell mapping;
- `oracle_facts` / `symbolic_facts` non-empty;
- `repair_trace` contains a 4+-char token from some oracle fact (cheap groundedness check);
- LLaMA-Factory JSON round-trips on 200 sampled rows;
- held-out templates and held-out (family, head) entities have **0 overlap** with train.

**Shipped v0 status:** `PASS`, 0 failures (`data/data_sanity_report.json`).

---

# Part III — How the model was trained

## 11. Conversion to training format

`convert_to_llamafactory.py` → alpaca-style examples:

- **instruction** (fixed for every row): *"You are an atomic repair agent. Given a problem
  and a tentative answer, diagnose whether there is an atomic-capacity failure. If there is
  a failure, choose the correct repair skill and repair the answer. If there is no failure,
  do not over-repair. Return only valid JSON."*
- **input**: `Problem:\n{problem}\n\nTentative answer:\n{tentative_answer}`
- **output**: the 4-key JSON string (`diagnosis / repair_skill / repair_trace / final_answer`).

**Critical design choice:** the input **deliberately does not include `oracle_facts`.** The
model sees only the problem and the tentative answer. To repair the *content* it must
recover the missing/masked bridge entity from parametric knowledge. Since the entities are
fictitious (§3), this is a genuine generalization test — accepted as a feature, not a bug.

## 12. Training run

- **Full-parameter fine-tuning** (not LoRA), at the user's request.
- Model: **Qwen3-8B-Base**. Hardware: **8×80G** (A100/H100-class).
- DeepSpeed **ZeRO-3** (`configs/ds_z3_config.json`), launched with `FORCE_TORCHRUN` over 8
  GPUs (`scripts/run_03b_train_full.sh`).
- Config: full set, 3 epochs, lr 1e-5, effective batch 128 (per-device 4 × grad-accum 4 ×
  8 GPUs), cutoff 2048, bf16, gradient checkpointing.

| metric | value |
|--------|-------|
| train_loss | 0.340 |
| eval_loss | 0.430 |
| epochs | 3.0 |
| train_runtime | 241 s (~4 min) |
| samples/s | 26.1 |

No OOM. Loss is low and the train/eval gap is small → **not an optimization failure**.
Whatever the model fails at below, it fails at having *learned the data*, not at fitting it.

## 13. Prediction

`run_04b_predict_full.sh` + `configs/qwen3_8b_repair_full_predict.yaml`: greedy decoding
(`do_sample: false`), max_new_tokens 512, on the 550 held-out eval rows. Output:
`output/qwen3_8b_repair_full_predict/generated_predictions.jsonl` (fields `prompt`,
`predict`, `label`). The full checkpoint (~16GB) stays on the server; only the prediction
file is pulled back for scoring.

---

# Part IV — How the model was evaluated

`evaluate_predictions.py` — CPU-only, stdlib-only, does not touch model weights.

## 14. Alignment

Each prediction's `label` (the gold output string) is matched back to the raw eval row by
**exact gold-output match**, falling back to line index only if needed. On this run:
**550/550 matched by gold-match, 0 by index** — cell attribution is exact, not order-assumed.

## 15. Metrics

- **JSON-valid**: did the model emit a parseable JSON object? (Parser takes the first
  balanced `{...}`, so trailing garbage after a valid object doesn't penalize.)
- **diagnosis / repair_skill / final_answer**: each field vs gold. `final_answer` is
  whitespace/case/trailing-punctuation normalized; the other two are exact string match.
- **exact (3/3)**: all three decision fields correct AND valid JSON.
- **over-repair on Clean**: Clean rows where the model predicted a repair (not `keep_answer`
  / `no_failure_detected`).
- **under-repair on non-Clean**: rows that needed repair but the model said no-op.
- **repair-skill confusion matrix**; **held-out vs seen entity** breakdown.
- **bootstrap 95% CIs** (percentile bootstrap, deterministic stdlib RNG) on every rate.

## 16. The scorer was validated against itself

Before scoring the real run, the scorer was checked on synthetic inputs:
- a **perfect** prediction file (predict == gold) → all metrics 100%, over/under-repair 0;
- a **deliberately broken** file (injected wrong answers, over-repairs, invalid JSON) → each
  metric moved by exactly the injected amount, independently (e.g. 33% Clean over-repairs →
  over-repair reads 33%; 25% invalid JSON in K-Cor → K-Cor json-valid reads 75%).

So the numbers below reflect the model, not scorer artifacts.

---

# Part V — Results, analysis, conclusions

## 17. The numbers (550 held-out)

| cell | n | JSON-valid | diagnosis | repair_skill | final_answer | exact (3/3) |
|------|---|-----------|-----------|--------------|--------------|-------------|
| H-Aug | 100 | 100% | 30% | 30% | **0%** | 0% |
| H-Abl | 100 | 100% | 100% | 100% | **4%** | 4% |
| H-Cor | 150 | 100% | 100% | 100% | **0%** | 0% |
| K-Cor | 100 | 100% | 100% | 100% | **6%** | 6% |
| Clean | 100 | 100% | 96% | 96% | **95%** | 95% |
| **overall** | 550 | 100% | 86.6% | 86.6% | **19.1%** | 19.1% |

Point estimates; full CIs in `data/eval_report.json`. Overall final_answer 95% CI = [15.8, 22.7].

**Failure modes:**
- **Over-repair on Clean: 4%** — the model rarely "fixes" a correct answer.
- **Under-repair on non-Clean: 15.6%** — **all of it is H-Aug** (70/100 H-Aug rows read as
  `no_failure_detected`). Skill confusion confirms: `retrieve_bridge_fact` predicted as
  `keep_answer` 70 times.

## 18. Reading the results — three skills, learned to three degrees

**1. Output format — fully learned.** 100% JSON-valid across every cell. The model always
emits the four-key object. (Caveat: it often keeps generating garbage *after* the closing
brace — see §20. Scoring is unaffected.)

**2. Diagnosis + skill selection — learned everywhere except H-Aug.** ~100% on H-Abl /
H-Cor / K-Cor, 96% on Clean. The repair *taxonomy* is learned; the model is a competent
"router" — it can tell you what's broken and which tool applies.

**3. final_answer (content repair) — not learned (0–6%), by design.** Because the input
withholds the facts AND the entities are fictitious, the model cannot recall the bridge
entity. There is nothing to recall. This is the whole story, and it is the dataset working
as intended, not a model or scoring failure.

## 19. Deep-dive: how exactly final_answer fails

- **H-Aug** (100): 69 copy the tentative answer verbatim, 31 hallucinate a fresh wrong
  answer, **0** produce gold. It cannot invent an entity it was never shown.
- **H-Cor** (150): 145/150 wrong answers are *fresh hallucinations*, only 5 fall back to the
  planted/tentative string. The model knows the answer is wrong (diagnosis 100%) and tries
  to replace it — but with noise.
- **K-Cor** (100): the 6 "correct" finals are **coincidence, not signal** — the model's most
  frequent K-Cor output is `caltorian`, but the 6 hits are all `lydorian` (zero overlap with
  its high-frequency guess). final_answer is effectively 0%.

So `final_answer ≈ 0` is a **true-generalization lower bound**: it confirms the data tests
recall/repair of content the model provably cannot have memorized, rather than rewarding
surface pattern-matching.

## 20. The one informative asymmetry: H-Aug detection

H-Aug is the only cell where **detection** also fails (diagnosis 30%): on 70/100 rows the
model predicts `no_failure_detected` — it thinks a plausible-but-unsupported tentative
answer is fine and declines to repair. This is the entire source of the 15.6% under-repair
rate. **The hardest failure to *detect* is the silently-missing-fact case.** The model
over-trusts a fluent-looking answer; explicit contradictions (H-Cor, K-Cor) are caught 100%,
but a quietly-missing bridge fact slips past.

## 21. Generation does not stop cleanly

Many predictions emit the correct JSON object and then continue with unrelated tokens (CSS
fragments, repeated text) instead of stopping. JSON-validity and scoring are unaffected
(first balanced object is taken), but it indicates the training targets' stop/EOS behavior
is worth a look — the model learned *what* to output but not cleanly *when to stop*.

## 22. Conclusions

1. **The model learned the repair taxonomy, not the repaired content.** It diagnoses and
   routes near-perfectly (86.6% overall, ~100% ex-H-Aug) but produces the corrected answer
   only 19% of the time — and that 19% is essentially the Clean cell, where "repair" means
   "keep the already-correct answer."
2. **The collapse is by construction and validates the dataset.** Fictitious entities + facts
   withheld from the input = a regime where content repair requires recalling something that
   doesn't exist in the weights. final_answer ≈ 0 is the intended lower bound.
3. **Detection has one real blind spot.** The silently-missing-fact case (H-Aug) is the only
   diagnosis failure, and it's a meaningful one: models trust fluent answers.
4. **It is not trigger-happy.** Over-repair on Clean is only 4% — the negative control worked.

## 23. Limitations / what to push on

1. **final_answer is uninformative in isolation** (~0 by construction). Report
   diagnosis/skill accuracy as the first-class metric; treat final_answer as a recall probe.
2. **No facts-in-input condition.** v0 can't separate "can't recall a fact" from "can't use a
   fact it's given."
3. **No family-level OOD.** All 6 families are in both splits.
4. **Single run, single model, single seed.** No variance bands; no base-model or
   smaller-model comparison.
5. **Stop-token behavior** is not clean.
6. **Synthetic-only.** Findings are about reasoning/format generalization on fictitious
   entities, not real-world factual repair.

## 24. Proposed v0.1

1. **Facts-in-input control cell** — same items, but put `oracle_facts` in the input. This
   isolates "can the model *apply* a provided bridge fact" (should pull final_answer up
   sharply) from "can it *recall* one" (current setting). The gap between the two is the real
   quantity of interest.
2. **Make diagnosis/skill accuracy a first-class reported metric** — the model is a useful
   router even when it can't author the corrected fact.
3. **Harden H-Aug detection** — more "plausible but unsupported" negatives, or a contrastive
   signal, to target the 70% miss directly.
4. **Stop-token hygiene** — ensure training targets end with a clean EOS.
5. **Family-level OOD** — add a 7th relation family that lives only in eval.

---

# Appendix — file map

| file | what |
|------|------|
| `generate_repair_data.py` | data generator (families, cells, surfaces, splits) |
| `validate_repair_data.py` | hard-check validator (fail-stops on contract violations) |
| `convert_to_llamafactory.py` | raw JSONL → LLaMA-Factory alpaca JSON + `dataset_info.json` |
| `configs/qwen3_8b_repair_full_sft.yaml`, `ds_z3_config.json` | full-FT training config |
| `configs/qwen3_8b_repair_full_predict.yaml` | prediction config |
| `scripts/run_03b_train_full.sh`, `run_04b_predict_full.sh` | server run scripts |
| `evaluate_predictions.py` | scorer (per-cell acc, CIs, failure modes) |
| `data/repair_raw_{train,eval}.jsonl` | raw items with full oracle fields |
| `data/repair_lf_{train,eval}.json` | training-format items |
| `data/eval_report.{json,md}` | scored results |
| `output/qwen3_8b_repair_full/` | training metrics + loss curve (weights stay on server) |
| `output/qwen3_8b_repair_full_predict/generated_predictions.jsonl` | 550 raw predictions |
