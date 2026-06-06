# Atomic-repair v2 — comparison (9 atomic capacities)

## Gates

- **Cleanliness** (base inject ≤ 5.0%): 3.4% → PASS ✅
- **Learned floor** (injected inject ≥ 90.0%): 100.0% → PASS ✅

## Final-answer by condition (overall)

| condition | overall |
|---|---|
| A zero-shot direct | 0.2% |
| A zero-shot CoT | 0.0% |
| B Fact-only | 39.7% |
| C Fact→CoT | 79.0% |
| D Fact→Skill+CoT | 85.5% |

## Per-cell final-answer (the story: which capacities get repaired)

| cell | B Fact-only | C Fact→CoT | D Fact→Skill+CoT |
|---|---|---|---|
| K-Aug | 96.7% | 81.7% | 95.0% |
| K-Abl | 98.3% | 100.0% | 100.0% |
| K-Cor | 91.7% | 75.0% | 100.0% |
| R-Aug | 0.0% | 56.7% | 95.0% |
| R-Abl | 0.0% | 100.0% | 100.0% |
| R-Cor | 0.0% | 56.7% | 100.0% |
| H-Aug | 73.3% | 96.7% | 45.0% |
| H-Abl | 0.0% | 25.0% | 20.0% |
| H-Cor | 13.3% | 98.3% | 100.0% |
| Clean | 23.3% | 100.0% | 100.0% |

## Contrasts

- Does adding knowledge alone help? **B vs zero-shot**: 39.7% vs 0.0%
- Does CoT traj help use known facts? **C vs B**: 79.0% vs 39.7%
- Does the skill label add over CoT? **D vs C**: 85.5% vs 79.0%

## Failure modes by condition

| condition | Clean over-repair | K-Cor accept | R-Cor accept | H-Cor accept |
|---|---|---|---|---|
| A zero-shot direct | 100.0% | 0.0% | 0.0% | 0.0% |
| A zero-shot CoT | 100.0% | 0.0% | 0.0% | 0.0% |
| B Fact-only | 76.7% | 0.0% | 0.0% | 11.7% |
| C Fact→CoT | 0.0% | 21.7% | 18.3% | 1.7% |
| D Fact→Skill+CoT | 0.0% | 0.0% | 0.0% | 0.0% |