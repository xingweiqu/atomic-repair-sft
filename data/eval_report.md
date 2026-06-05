# Atomic-repair eval report

Alignment: 550 by gold-match, 0 by index, 0 unmatched.

## Overall

- JSON-valid: 100.0% [100.0, 100.0] (n=550)
- Exact (all 3 fields): 19.1% [15.8, 22.7] (n=550)
- diagnosis: 86.6% [83.5, 89.5] (n=550)
- repair_skill: 86.6% [83.5, 89.5] (n=550)
- final_answer: 19.1% [15.8, 22.7] (n=550)

## Per cell

| cell | n | json-valid | exact (3/3) | diagnosis | repair_skill | final_answer |
|------|---|-----------|-------------|-----------|--------------|--------------|
| H-Aug | 100 | 100.0% [100.0, 100.0] (n=100) | 0.0% [0.0, 0.0] (n=100) | 30.0% [21.0, 39.0] (n=100) | 30.0% [21.0, 39.0] (n=100) | 0.0% [0.0, 0.0] (n=100) |
| H-Abl | 100 | 100.0% [100.0, 100.0] (n=100) | 4.0% [1.0, 8.0] (n=100) | 100.0% [100.0, 100.0] (n=100) | 100.0% [100.0, 100.0] (n=100) | 4.0% [1.0, 8.0] (n=100) |
| H-Cor | 150 | 100.0% [100.0, 100.0] (n=150) | 0.0% [0.0, 0.0] (n=150) | 100.0% [100.0, 100.0] (n=150) | 100.0% [100.0, 100.0] (n=150) | 0.0% [0.0, 0.0] (n=150) |
| K-Cor | 100 | 100.0% [100.0, 100.0] (n=100) | 6.0% [2.0, 11.0] (n=100) | 100.0% [100.0, 100.0] (n=100) | 100.0% [100.0, 100.0] (n=100) | 6.0% [2.0, 11.0] (n=100) |
| Clean | 100 | 100.0% [100.0, 100.0] (n=100) | 95.0% [90.0, 99.0] (n=100) | 96.0% [92.0, 99.0] (n=100) | 96.0% [92.0, 99.0] (n=100) | 95.0% [90.0, 99.0] (n=100) |

## Failure modes

- **Over-repair on Clean** (model 'fixes' a correct answer): 4.0% [1.0, 8.0] (n=100)
- **Under-repair on non-Clean** (model misses a real failure): 15.6% [12.7, 18.7] (n=450)

### Repair-skill confusion (gold -> pred, non-Clean, valid JSON only)

| gold skill | predicted skill | count |
|------------|-----------------|-------|
| bridge_source_verification | bridge_source_verification | 150 |
| recover_bridge_entity | recover_bridge_entity | 100 |
| contradiction_check | contradiction_check | 100 |
| retrieve_bridge_fact | keep_answer | 70  <-- mismatch |
| retrieve_bridge_fact | retrieve_bridge_fact | 30 |

## Generalization (final_answer accuracy)

- Held-out entities: 19.1% [15.8, 22.6] (n=550)
- Seen entities: 0.0% [0.0, 0.0] (n=0)
