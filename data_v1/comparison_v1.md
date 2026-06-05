# Atomic Repair v1 Comparison

## Conditions

| condition | name | train | oracle facts in input | output schema |
|---|---|---:|---:|---|
| A | zero-shot | no | no | final_answer |
| B | Fact-only | yes | yes | final_answer |
| C | Fact→CoT | yes | yes | repair_trace, final_answer |
| D | Fact→Skill+CoT | yes | yes | diagnosis, repair_skill, repair_trace, final_answer |

## Overall

| condition | n_pred/raw | json_valid | final_answer | trace_grounded | diagnosis | repair_skill | exact_all3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A zero_shot | 550/550 | 73.8% | 1.1% | - | - | - | - |
| B fact_only | 550/550 | 100.0% | 99.8% | - | - | - | - |
| C fact_cot | 550/550 | 100.0% | 100.0% | 100.0% | - | - | - |
| D fact_skill_cot | 550/550 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |

## Per-cell final_answer accuracy

| cell | A | B | C | D |
|---|---:|---:|---:|---:|
| H-Aug | 0.0% | 100.0% | 100.0% | 100.0% |
| H-Abl | 0.0% | 100.0% | 100.0% | 100.0% |
| H-Cor | 0.0% | 99.3% | 100.0% | 100.0% |
| K-Cor | 0.0% | 100.0% | 100.0% | 100.0% |
| Clean | 6.0% | 100.0% | 100.0% | 100.0% |

## D skill confusion

| gold -> pred | n |
|---|---:|
| bridge_source_verification -> bridge_source_verification | 150 |
| retrieve_bridge_fact -> retrieve_bridge_fact | 100 |
| recover_bridge_entity -> recover_bridge_entity | 100 |
| contradiction_check -> contradiction_check | 100 |
| keep_answer -> keep_answer | 100 |
