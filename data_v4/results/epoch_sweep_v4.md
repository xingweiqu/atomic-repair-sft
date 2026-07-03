# v4 epoch sweep — extrapolability of the decision-vs-ability split

Epoch is the only variable (full-param SFT, seed 42, all else == round-1 v4). Each ckpt decoded on v4_actionized_eval (480). `ability|resist fixed` = final==gold on a FIXED subset S = items RESISTED by every ckpt on that cell (decision held successful for all -> pure arithmetic, constant denominator; the §6.1 denominator-bias fix).

## Per-branch, per-epoch (branch's OWN cell)

| branch | epoch | cell | parse | resist_wrong | ability\|resist fixed (n) | final_acc |
|---|---|---|---|---|---|---|
| random_override_wrong_claim | 1 | override_wrong_claim | 0.7625 | **0.6375** | 0.6 (5) | 0.45 |
| random_override_wrong_claim | 2 | override_wrong_claim | 0.9625 | **0.9494** | 0.2 (5) | 0.125 |
| random_override_wrong_claim | 3 | override_wrong_claim | 1.0 | **0.425** | 0.2 (5) | 0.125 |
| random_override_wrong_claim | 8 | override_wrong_claim | 1.0 | **0.6625** | 0.2 (5) | 0.225 |
| random_override_wrong_claim | 30 | override_wrong_claim | 1.0 | **0.725** | 0.4 (5) | 0.2625 |
| scaffold_conv | 1 | override_wrong_claim | 0.2625 | **0.9315** | 0.6 (5) | 0.3 |
| scaffold_conv | 2 | override_wrong_claim | 0.425 | **0.519** | 0.4 (5) | 0.2625 |
| scaffold_conv | 3 | override_wrong_claim | 0.8125 | **0.6** | 0.6 (5) | 0.425 |
| scaffold_conv | 8 | override_wrong_claim | 1.0 | **0.775** | 0.2 (5) | 0.1875 |
| scaffold_conv | 30 | override_wrong_claim | 1.0 | **0.6375** | 0.2 (5) | 0.2 |
| targeted_override_wrong_claim | 1 | override_wrong_claim | 0.7875 | **0.6835** | 0.6 (5) | 0.425 |
| targeted_override_wrong_claim | 2 | override_wrong_claim | 1.0 | **1.0** | 0.2 (5) | 0.2625 |
| targeted_override_wrong_claim | 3 | override_wrong_claim | 1.0 | **0.9875** | 0.2 (5) | 0.3 |
| targeted_override_wrong_claim | 8 | override_wrong_claim | 1.0 | **0.975** | 0.2 (5) | 0.3625 |
| targeted_override_wrong_claim | 30 | override_wrong_claim | 1.0 | **0.9875** | 0.2 (5) | 0.3125 |
| targeted_recompute | 1 | recompute | 0.525 | **0.825** | 0.5833 (60) | 0.4625 |
| targeted_recompute | 2 | recompute | 0.9 | **0.9375** | 0.5167 (60) | 0.475 |
| targeted_recompute | 3 | recompute | 1.0 | **0.975** | 0.4 (60) | 0.325 |
| targeted_recompute | 8 | recompute | 1.0 | **0.975** | 0.3833 (60) | 0.3 |
| targeted_recompute | 30 | recompute | 1.0 | **0.9875** | 0.3333 (60) | 0.275 |
| targeted_verify_step | 1 | verify_step | 0.4375 | **0.8481** | 0.4925 (67) | 0.4125 |
| targeted_verify_step | 3 | verify_step | 1.0 | **1.0** | 0.4179 (67) | 0.4125 |
| targeted_verify_step | 30 | verify_step | 1.0 | **1.0** | 0.5075 (67) | 0.5125 |

![epoch sweep](fig_epoch_sweep.png)

## Conclusion (filled 2026-07-04, see qc/LOOP1_5_BATCH2_HARVEST.md)

- decision (resist_wrong) appears at epoch: **2** (targeted_override 0.68@e1 -> 1.00@e2, stable ~0.99 thereafter)
- ability_fixed across epochs: **monotonic DECAY, not flat** — targeted_recompute (n=60) 0.58 -> 0.52 -> 0.40 -> 0.38 -> 0.33; the in-genre readout decays with training intensity (genre-coupled computation, LOOP1_5_RULINGS R-10), while PLAIN-genre answered-acc stays 85–99% across the sweep
- overfit / non-extrapolable region begins at epoch: **>8 for scaffold (json_bleed 0%@e8 -> 31%@e30); >3 for single-operator recompute (88%@e8)** — the "ridge" (R-11)
- targeted vs random at low epoch (1–2): **specificity present from e2** — random resist never stabilises (0.64/0.95/0.43/0.66/0.73) while targeted locks at ~1.0

## Extrapolability statement

**Holds at low epoch (extrapolates to near-single-pass training):** the D channel — resist
flips by e2 and stays; targeted-vs-random specificity. **Convergent-setting artifacts:** the
depressed in-genre ability readout (decays only as epochs accumulate) and genre bleed onto
plain inputs (explodes past the ridge: e8->e30 for scaffold, e3->e8 for single-operator
recompute). Canonical-floor rule (R-11): minimum epoch with parse>=0.95 AND json_bleed<=5%
-> **e8 for scaffold_conv in this domain**; the round-1 30-epoch floor was past the ridge.
