# Loop 1 — judge wrapper regression (D-2 gate)

Historical config = (final: lenient chain, abstain: strict). Tolerance ±1pp.
Targets: `data_v3_1/REPORT_v3_1_zh.md` §2/§4, `data_v4/results/comparison_v4.md` Exp-1.

| check | wrapper | historical | Δ | ok |
|---|---|---|---|---|
| v3.1 factonly overall | 39 | 39 | +0 | ✅ |
| v3.1 scaffold_only overall | 16 | 16 | +0 | ✅ |
| v3.1 scaffold_only override_wrong_claim | 22 | 22 | +0 | ✅ |
| v3.1 scaffold_only verify_bridge | 3 | 3 | +0 | ✅ |
| v3.1 scaffold_only verify_step | 0 | 0 | +0 | ✅ |
| v3.1 scaffold_only recompute | 13 | 13 | +0 | ✅ |
| v3.1 scaffold_only use_provided_support | 30 | 30 | +0 | ✅ |
| v3.1 scaffold_only retrieve_or_abstain | 12 | 12 | +0 | ✅ |
| v3.1 targeted_override_wrong_claim diagonal | 95 | 95 | +0 | ✅ |
| v3.1 targeted_verify_bridge diagonal | 78 | 78 | +0 | ✅ |
| v3.1 targeted_verify_step diagonal | 93 | 93 | +0 | ✅ |
| v3.1 targeted_recompute diagonal | 100 | 100 | +0 | ✅ |
| v3.1 targeted_use_provided_support diagonal | 99 | 99 | +0 | ✅ |
| v3.1 targeted_retrieve_or_abstain diagonal | 100 | 100 | +0 | ✅ |
| v4 diagnosis_base overall | 33 | 33 | +0 | ✅ |
| v4 scaffold_conv overall | 56 | 56 | +0 | ✅ |
| v4 actionized_full overall | 62 | 62 | +0 | ✅ |

**17/17 PASS**
