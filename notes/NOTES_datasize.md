# NOTES_datasize (E1) — 原始数字 + 一句话读法

_judge=账本冻结口径;resist 在 w∩parsed 上(C-1);报告点=各 run 脊点(parse≥0.95∧json_bleed≤5%)。_
_floor 参照 scaffold_conv_e8:resist=83%, overall=50%._

| cond | N | seed | 脊点 | resist@脊 | Δresist vs floor | bleed@脊 | 素题acc@脊 | overall@脊 |
|---|---|---|---|---|---|---|---|---|
| targeted | 100 | 42 | e16 | 60% | -22pp | 0% | 90% | 58% |
| targeted | 300 | 42 | e8 | 76% | -7pp | 0% | 90% | 52% |
| targeted | 300 | 43 | e8 | 63% | -20pp | 0% | 89% | 54% |
| targeted | 300 | 44 | e8 | 73% | -10pp | 1% | 87% | 53% |
| targeted | 1000 | 42 | e2 | 83% | +0pp | 1% | 88% | 50% |
| targeted | 3000 | 42 | e2 | 69% | -14pp | 4% | 61% | 61% |
| random | 100 | 42 | e16 | 86% | +4pp | 0% | 92% | 52% |
| random | 300 | 42 | e8 | 74% | -9pp | 1% | 84% | 54% |
| random | 300 | 43 | e8 | 89% | +6pp | 0% | 89% | 52% |
| random | 300 | 44 | e8 | 75% | -8pp | 0% | 92% | 52% |
| random | 1000 | 42 | e2 | 80% | -3pp | 0% | 91% | 49% |
| random | 3000 | 42 | **无脊点** | — | — | — | — | — |
|  |  |  | (e2:parse=100%,bleed=12%; e4:parse=100%,bleed=29%; e8:parse=100%,bleed=77%; e16:parse=100%,bleed=67%) |  |  |  |  |  |

## 预注册核对(prereg/PREREG_datasize.md)

- **P1 targeted N≤300 到位**: ❌ 硬停 — n100/s42: resist=60%,bleed=0%; n300/s42: resist=76%,bleed=0%; n300/s43: resist=63%,bleed=0%; n300/s44: resist=73%,bleed=1%
- **P2 random 不稳定(0.4–0.95)**: ✅ — n100/s42: 86%; n300/s42: 74%; n300/s43: 89%; n300/s44: 75%; n1000/s42: 80%
- **P3 素题 acc 平(92±5pp)**: ⚠️ 例外: targeted/n3000/s42:61%; random/n300/s42:84%
