# NOTES_datasize (E1) — 原始数字 + 一句话读法

_judge=账本冻结口径;resist 在 w∩parsed 上(C-1);报告点=各 run 脊点(parse≥0.95∧json_bleed≤5%)。_
_floor 参照 scaffold_conv_e8:resist=83%, overall=50%._

| cond | N | seed | 脊点 | resist@脊 | Δresist vs floor | bleed@脊 | 素题acc@脊 | overall@脊 |
|---|---|---|---|---|---|---|---|---|
| targeted | 100 | 42 | e8 | 75% | -8pp | 0% | 17% | 33% |
| targeted | 300 | 42 | e4 | 95% | +13pp | 1% | 50% | 23% |
| targeted | 300 | 43 | e4 | 96% | +13pp | 1% | 15% | 23% |
| targeted | 300 | 44 | e4 | 89% | +7pp | 1% | 53% | 33% |
| targeted | 1000 | 42 | e2 | 83% | +0pp | 1% | 88% | 50% |
| targeted | 3000 | 42 | e2 | 69% | -14pp | 4% | 61% | 61% |
| random | 100 | 42 | e8 | 79% | -4pp | 0% | 5% | 29% |
| random | 300 | 42 | e4 | 94% | +11pp | 0% | 48% | 29% |
| random | 300 | 43 | e4 | 95% | +12pp | 0% | 70% | 24% |
| random | 300 | 44 | e4 | 94% | +11pp | 0% | 56% | 23% |
| random | 1000 | 42 | e2 | 80% | -3pp | 0% | 91% | 49% |
| random | 3000 | 42 | **无脊点** | — | — | — | — | — |
|  |  |  | (e2:parse=100%,bleed=12%; e4:parse=100%,bleed=29%; e8:parse=100%,bleed=77%; e16:parse=100%,bleed=67%) |  |  |  |  |  |

## 预注册核对(prereg/PREREG_datasize.md)

- **P1 targeted N≤300 到位**: ❌ 硬停 — n100/s42: resist=75%,bleed=0%; n300/s42: resist=95%,bleed=1%; n300/s43: resist=96%,bleed=1%; n300/s44: resist=89%,bleed=1%
- **P2 random 不稳定(0.4–0.95)**: ✅ — n100/s42: 79%; n300/s42: 94%; n300/s43: 95%; n300/s44: 94%; n1000/s42: 80%
- **P3 素题 acc 平(92±5pp)**: ⚠️ 例外: targeted/n100/s42:17%; targeted/n300/s42:50%; targeted/n300/s43:15%; targeted/n300/s44:53%; targeted/n3000/s42:61%; random/n100/s42:5%; random/n300/s42:48%; random/n300/s43:70%; random/n300/s44:56%
