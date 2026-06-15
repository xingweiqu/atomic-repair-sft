# v4 decision-level analysis (floor = scaffold_conv)

`final_acc` couples decision + arithmetic. `resist_wrong` = decision only (committed answers not equal to the planted/tentative wrong value). `arith_given_ok` = arithmetic on the resisted subset.

## cell: verify_step

| run | parse | committed | no-answer | resist_wrong (decision) | arith_given_ok | final_acc |
|---|---|---|---|---|---|---|
| scaffold_conv | 1.0 | 1.0 | 0.0 | **0.975** | 0.385 | 0.375 |
| targeted_verify_step | 1.0 | 1.0 | 0.0 | **1.0** | 0.412 | 0.412 |
| actionized_full | 1.0 | 1.0 | 0.0 | **1.0** | 0.575 | 0.575 |

## cell: recompute

| run | parse | committed | no-answer | resist_wrong (decision) | arith_given_ok | final_acc |
|---|---|---|---|---|---|---|
| scaffold_conv | 1.0 | 1.0 | 0.0 | **0.6** | 0.417 | 0.25 |
| targeted_recompute | 1.0 | 1.0 | 0.0 | **0.975** | 0.333 | 0.325 |
| actionized_full | 1.0 | 1.0 | 0.0 | **0.575** | 0.457 | 0.263 |

## cell: override_wrong_claim

| run | parse | committed | no-answer | resist_wrong (decision) | arith_given_ok | final_acc |
|---|---|---|---|---|---|---|
| scaffold_conv | 1.0 | 1.0 | 0.0 | **0.637** | 0.314 | 0.2 |
| targeted_override_wrong_claim | 1.0 | 1.0 | 0.0 | **0.988** | 0.304 | 0.3 |
| actionized_full | 1.0 | 1.0 | 0.0 | **0.6** | 0.417 | 0.25 |

## Decision-level selective matrix — resist_wrong (rows=trained op, cols=eval cell)

| trained \ eval | verify_ste | recompute | override_w |
|---|---|---|---|
| verify_step | 1.00 | 0.93 | 0.90 |
| recompute | 0.99 | 0.97 | 0.85 |
| override_wrong | 0.99 | 0.97 | 0.99 |

## abstain (treated SEPARATELY — a decision/format skill, not an ability)

Reported as abstain-correct (strict). Not comparable to the compute cells above; it is a positive control showing the loop fires on a capacity the base lacks.

| run | abstain-correct |
|---|---|
| scaffold_conv | 1.0 |
| actionized_full | 1.0 |
| targeted_retrieve_or_abstain | 1.0 |
| random_retrieve_or_abstain | 1.0 |
| wrongtarget_retrieve_or_abstain | 1.0 |