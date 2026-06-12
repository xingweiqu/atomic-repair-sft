# Erratum — v3 abstain judging artifact

> Self-reported during v3.1 auditing. Original v3 tables (`results/comparison_v3.md`,
> `REPORT_v3_zh.md`) are RETAINED unchanged; this erratum states the correction.

## What was wrong

The abstain (`retrieve_or_abstain`) metric counted a model as correctly abstaining whenever
the parser found no `final_answer`. But the **Fact-only** model emits a BARE answer string
(e.g. `Forenza`, `astrophysics`) with no JSON, so the parser saw no field and scored it as
an abstention. In reality Fact-only **guessed a concrete answer on all 60/60 abstain items
(0 genuine abstentions)**. The reported abstain=100% baseline was a judge artifact.

## Fix

`is_abstain_strict` now treats a bare/unparsed concrete output as ANSWERED (not abstained).
Only an explicit null `final_answer` or `update_decision==retrieve_or_abstain` counts as
abstention. A second `lenient` track (tightened markers) is reported in the appendix.

## Corrected numbers (v3 predictions, strict judge)

| condition | abstain (was) | abstain (strict) | overall (was) | overall (strict) |
|---|---|---|---|---|
| Fact-only | 100% | 0% | 49.7% | 39.7% |
| Fact->CoT | 100% | 100% | 99.3% | 99.3% |
| Fact->Actionized | 100% | 100% | 95.5% | 95.5% |
| targeted_retrieve_or_abstain | 100% | 100% | — | 46%* |

\* targeted_retrieve_or_abstain abstain-on-its-own-policy = 100% from a 0% Fact-only base.

## What changes in the narrative (stronger, not weaker)

1. **Fact-only 49.7% -> 39.7%**: the 'knowledge floor is not enough' result is STRONGER
   (the 10-pt abstain freebie is removed).
2. **JSON-output runs are unaffected** (they carry an explicit decision field).
3. **abstain is an INDUCED capability, not innate**: Fact-only genuinely abstains 0% of the
   time; only training to emit an abstain decision produces it (targeted_retrieve_or_abstain
   reaches 100% from 0). This is the cleanest diagonal in the selective matrix and is
   consistent with the decision-collapse mechanism (single-policy training drives keep/abstain
   to 0). It replaces the earlier 'abstain baseline was saturated' reading.

4. The selective-matrix abstain COLUMN is recomputed against the true 0% base in v3.1.
