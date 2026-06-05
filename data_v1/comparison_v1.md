# Atomic Repair v1 Comparison

## Conditions

| condition | name | train | oracle facts in input | output schema |
|---|---|---:|---:|---|
| A | zero-shot | no | no | final_answer |
| B | Fact-only | yes | no | final_answer |
| C | Fact→CoT | yes | no | repair_trace, final_answer |
| D | Fact→Skill+CoT | yes | no | diagnosis, repair_skill, repair_trace, final_answer |

## Overall

| condition | n_pred/raw | json_valid | final_answer | trace_grounded | diagnosis | repair_skill | exact_all3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A zero_shot | 550/550 | 73.8% | 1.1% | - | - | - | - |
| B fact_only | 550/550 | 100.0% | 15.3% | - | - | - | - |
| C fact_cot | 550/550 | 100.0% | 19.1% | 99.8% | - | - | - |
| D fact_skill_cot | 550/550 | 100.0% | 19.4% | 100.0% | 83.6% | 83.6% | 19.4% |

## Per-cell final_answer accuracy

| cell | A | B | C | D |
|---|---:|---:|---:|---:|
| H-Aug | 0.0% | 0.0% | 0.0% | 0.0% |
| H-Abl | 0.0% | 0.0% | 6.0% | 0.0% |
| H-Cor | 0.0% | 0.0% | 0.0% | 0.7% |
| K-Cor | 0.0% | 1.0% | 12.0% | 8.0% |
| Clean | 6.0% | 83.0% | 87.0% | 98.0% |

## D skill confusion

| gold -> pred | n |
|---|---:|
| bridge_source_verification -> bridge_source_verification | 150 |
| recover_bridge_entity -> recover_bridge_entity | 100 |
| contradiction_check -> contradiction_check | 100 |
| keep_answer -> keep_answer | 98 |
| retrieve_bridge_fact -> keep_answer | 88 |
| retrieve_bridge_fact -> retrieve_bridge_fact | 12 |
| keep_answer -> retrieve_bridge_fact | 2 |
