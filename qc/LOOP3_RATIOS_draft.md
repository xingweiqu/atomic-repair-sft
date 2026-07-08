# Loop 3 臂比例草案(拍板点 ③;profile 实数已代入;签字前不建训练数据)

## 公式与系数(每个系数带证据锚)

A1(k) ∝ prevalence(k);A2(k) ∝ prevalence(k) × RescueEffect(k) / cost(k)。
patch 数据总预算:各臂 token 对齐(C-11),建议基准 = E1b 甜点量级(~300-600 条/臂起,
以 token 计齐)。

| 组分 | prevalence(gsm) | RE 先验 | cost 先验 | 锚 |
|---|---|---|---|---|
| conduct(纠错验证,verify-then-**recompute**) | 16.4% | 0.95 | 1.0 | E1b:300 条 resist 0→100 持久;监督动作按裁决 2c 改写(素题失败 98% 是 derail 非 adopt) |
| format(格式校准) | 14.7% | 0.60 | **2.0** | 可训(tier-2 类比)但出血风险实测(山脊税)→ cost 加倍;注入面清单必须填"搭售:体裁出血" |
| phrasing(改写增强) | 6.4% | 0.50 | 1.0 | 无先验,中性 0.5(探索系数,签字时可改) |
| scaffold(分解蒸馏) | 2.0% | 0.50 | 1.0 | 无先验,中性 |
| rule(规则增强) | 0.9% | 0.90 | 1.0 | Tier-2:显式规则 OOD 99%+ 可教 |
| local_exec | 0.1% | 0.30 | 1.5 | 患病率近零,并入 drills 观察 |

## 代入结果(gsm 池)

| 臂 | conduct | format | phrasing | scaffold | rule | local_exec |
|---|---|---|---|---|---|---|
| **A1** | 40% | 36% | 16% | 5% | 2% | ~0% |
| **A2** | **62%** | 18% | 13% | 4% | 3% | ~0%(并 drills) |

## 固定项(公式外,按裁决)
- **drills 臂 = 最小证伪规格**(独立小臂,不进 A1/A2 配比;预注册 RE≈0)
- **hard 池踢出配方目标**,只作泛化评测列(unresolved 86.3% 不喂数据)
- 对照臂:B uniform(六组分均分)/ C generic GSM CoT / D mismatched(A1 反序)/
  E steering-only(零数据原点锚,只覆盖 conduct)/ clean-replay 护栏
- 每臂实验卡三行(锁哪句/注入面/拍板点)随 config 同 commit;format 臂注入面必须写明出血搭售
## 签字项
① A2 的 RE/cost 系数表(尤其 phrasing/scaffold 的中性 0.5)② 各臂 token 预算基准 ③ 3-seed 范围(A2+C?)
