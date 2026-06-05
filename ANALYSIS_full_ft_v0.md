# Atomic-repair full-FT eval analysis (v0)

Qwen3-8B-Base, full-parameter SFT, full train set (2,100), 3 epochs, DeepSpeed ZeRO-3 on 8x80G.
Eval on the held-out split (550 rows). Greedy decoding.

## Training health

| metric | value |
|--------|-------|
| train_loss | 0.340 |
| eval_loss | 0.430 |
| epochs | 3.0 |
| train_runtime | 241s (~4 min) |
| samples/s | 26.1 |

No OOM. Loss is low and the gap between train and eval loss is small, so this is
not an optimization failure — whatever the model fails at below, it fails at
having *learned the data*, not at fitting it.

## Headline result

| cell | n | JSON-valid | diagnosis | repair_skill | final_answer | exact (3/3) |
|------|---|-----------|-----------|--------------|--------------|-------------|
| H-Aug | 100 | 100% | 30% | 30% | **0%** | 0% |
| H-Abl | 100 | 100% | 100% | 100% | **4%** | 4% |
| H-Cor | 150 | 100% | 100% | 100% | **0%** | 0% |
| K-Cor | 100 | 100% | 100% | 100% | **6%** | 6% |
| Clean | 100 | 100% | 96% | 96% | **95%** | 95% |
| **overall** | 550 | 100% | 86.6% | 86.6% | **19.1%** | 19.1% |

(All point estimates carry bootstrap 95% CIs in `eval_report.json`.)

The model splits cleanly into three skills, learned to three very different degrees:

1. **Format — fully learned.** 100% JSON-valid across every cell. The model
   always emits the four-key object it was trained to emit. (It often keeps
   generating garbage *after* the closing brace; the scorer takes the first
   balanced `{...}`, so this does not cost accuracy, but it is real and worth
   noting — see "Generation does not stop" below.)

2. **Diagnosis + skill selection — learned everywhere except H-Aug.** On H-Abl,
   H-Cor, K-Cor the model picks the right `diagnosis` and `repair_skill` 100% of
   the time; on Clean, 96%. The repair *taxonomy* is learned.

3. **final_answer (content repair) — not learned (0-6%).** This is the whole
   story, and it is **by design**, not a bug. See below.

## Why final_answer collapses (and why that is the intended test)

The LLaMA-Factory `input` is `Problem + Tentative answer` and **deliberately does
not include `oracle_facts`** (frozen v0 contract). To actually *repair the
content*, the model must recall the masked/missing bridge entity from parametric
knowledge. But every entity is **synthetic and fictitious** (Maria Voss,
Lydorian, ...) — absent from pretraining — so there is nothing to recall.

The model's behavior under that impossibility, from the deep-dive:

- **H-Aug** (100 rows): on 69 it copies the tentative answer verbatim, on 31 it
  hallucinates a fresh wrong answer, on **0** does it produce gold. It cannot
  invent an entity it was never shown.
- **H-Cor** (150 rows): 145/150 wrong answers are *fresh hallucinations*, only 5
  fall back to the planted-wrong/tentative string. The model knows the answer is
  wrong (diagnosis 100%) and tries to replace it — but with noise.
- **K-Cor** (100 rows): the 6 "correct" finals are **coincidence, not signal** —
  the model's most frequent K-Cor output is `caltorian`, but the 6 hits are all
  `lydorian` (zero overlap with its high-frequency guess). final_answer is
  effectively 0%.

So `final_answer ≈ 0%` is the dataset doing its job: it is a **true-generalization
lower bound**. It confirms the data tests recall/repair of content the model
provably cannot have memorized, rather than rewarding surface pattern-matching.

## The one interesting asymmetry: H-Aug

H-Aug is the only cell where *diagnosis* also fails (30%). On 70/100 H-Aug rows
the model predicts `no_failure_detected` — it thinks the plausible-but-unsupported
tentative answer is fine and declines to repair. This is the entire source of the
**under-repair rate (15.6% over non-Clean)**: all 70 under-repairs are H-Aug, and
the skill-confusion matrix shows exactly this — `retrieve_bridge_fact` predicted
as `keep_answer` 70 times.

Reading: the hardest failure to *detect* is the one where the answer looks
internally consistent but is missing a bridge fact (H-Aug). The model
over-trusts a fluent-looking tentative answer. The cells with an explicit
contradiction or a visibly-wrong claim (H-Cor, K-Cor) are diagnosed perfectly;
the silently-missing-fact case is not.

## Failure modes summary

- **Over-repair on Clean: 4%** — the model rarely "fixes" a correct answer. Good:
  it is not trigger-happy.
- **Under-repair on non-Clean: 15.6%** — entirely H-Aug (missing-bridge-fact
  cases read as no-failure).

## Generation does not stop

Many predictions emit the correct JSON object and then continue with unrelated
tokens (CSS fragments, repeated text) instead of stopping. JSON-validity and
scoring are unaffected (first balanced object is taken), but this suggests the
training data's stop behavior / EOS handling is worth a look — the model learned
*what* to output but not cleanly *when to stop*.

## Implications for v0.1

`final_answer ≈ 0` means v0 currently tests the single hardest regime: fictitious
entities **and** facts withheld from the input. That is a valid lower bound, but
it cannot distinguish "can't recall" from "can't use facts it's given." To get a
gradient of difficulty, v0.1 could add controlled conditions:

1. **Facts-in-input control cell.** Same items, but put `oracle_facts` in the
   input. This isolates *can the model apply a provided bridge fact* (should pull
   final_answer up sharply) from *can it recall one* (current setting). The gap
   between the two is the actual measure of interest.
2. **Diagnosis-only metric is already meaningful.** Since the taxonomy is learned
   to ~100% (ex-H-Aug), report diagnosis/skill accuracy as a first-class number,
   not just final_answer. The model *can* be a useful router even when it can't
   author the corrected fact.
3. **Harden H-Aug detection.** It is the one capability with real headroom on the
   *diagnosis* axis. More H-Aug-style "plausible but unsupported" negatives, or a
   contrastive signal, would target the 70% miss directly.
4. **Stop-token hygiene.** Check the training targets end with a clean EOS so the
   model learns to terminate after the JSON.

## Artifacts

- `output/qwen3_8b_repair_full/` — training metrics + loss curve (model weights
  stay on the server, not committed).
- `output/qwen3_8b_repair_full_predict/generated_predictions.jsonl` — 550 raw
  predictions.
- `data/eval_report.json` / `data/eval_report.md` — scored report with CIs.
- Scored with `evaluate_predictions.py` (alignment: 550/550 by exact gold-match).
