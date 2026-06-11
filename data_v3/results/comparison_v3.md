# Scenario-Repair v3 — Comparison & Selective Operator Induction

## Experiment 1: Scenario-based Actionized Repair

| condition | overall | abstain-correct | false-keep | clean over-repair |
|---|---|---|---|---|
| Fact-only | 50% | 100% | 1% | 80% |
| Fact→CoT | 99% | 100% | 0% | 3% |
| Fact→Actionized (full) | 96% | 100% | 6% | 0% |

## Experiment 2: Selective Repair Matrix (gain over Fact-only, %)

Rows = trained on ONLY this policy's data. Columns = eval on this policy. Diagonal = Targeted Repair Gain.

| trained \ eval | override_w | verify_bri | verify_ste | recompute | use_provid | retrieve_o |
|---|---|---|---|---|---|---|
| override_wrong | +0 | +3 | +10 | +3 | +8 | -87 |
| verify_bridge | -27 | +72 | +7 | +3 | -17 | -100 |
| verify_step | -35 | +3 | +95 | +2 | -19 | -50 |
| recompute | +5 | +18 | +100 | +68 | +11 | +0 |
| use_provided_s | -78 | -3 | +33 | +36 | +14 | +0 |
| retrieve_or_ab | -37 | +2 | +10 | +4 | -28 | +0 |

### Targeted Repair Gain & Selectivity

| policy | targeted gain | selectivity |
|---|---|---|
| override_wrong_claim | +0% | +13% |
| verify_bridge | +72% | +98% |
| verify_step | +95% | +115% |
| recompute | +68% | +41% |
| use_provided_support | +14% | +17% |
| retrieve_or_abstain | +0% | +10% |

_Diagonal-dominant matrix + high selectivity ⇒ targeted data is on-target. If off-diagonal gains are as large (everything rises together), the gain is generic action-commitment, not selective induction — reported honestly either way._

## Experiment 3: Cumulative Curriculum

| stage | overall | keep_ans | override | verify_b | verify_s | recomput | use_prov | retrieve |
|---|---|---|---|---|---|---|---|---|
| M0 | 50% | 20 | 95 | 13 | 0 | 32 | 86 | 100 |
| M1 | 77% | 77 | 98 | 5 | 100 | 100 | 90 | 7 |
| M2 | 70% | 97 | 100 | 7 | 100 | 89 | 65 | 0 |
| M3 | 66% | 100 | 100 | 0 | 100 | 82 | 39 | 30 |
| M4 | 80% | 100 | 100 | 100 | 100 | 88 | 67 | 0 |
| M5 | 88% | 100 | 100 | 100 | 100 | 95 | 95 | 0 |
| M6 | 97% | 100 | 100 | 100 | 100 | 95 | 92 | 100 |

## Controls

| policy | targeted | same-size random | wrong-target |
|---|---|---|---|
| override_wrong_claim | 95% | 57% | 97% |
| verify_bridge | 85% | 25% | 80% |
| verify_step | 95% | 70% | 88% |
| recompute | 100% | 100% | 100% |
| use_provided_support | 100% | 100% | 97% |
| retrieve_or_abstain | 100% | 40% | 100% |

_Targeted > random ⇒ on-target data beats mere volume. Targeted > wrong-target ⇒ the policy label/action carries real signal._