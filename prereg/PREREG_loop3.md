# PREREG_loop3 — 配方实验(Batch 1)(2026-07-13,本 commit 即时间戳;签字版)

## 0. 设计(签字裁决版)
- **Batch 1 臂**:六单组分(conduct/format/phrasing/scaffold/rule/drills,各 **600 条** token
  对齐)+ A1(按患病率 40/36/16/5/2)+ B(均匀)+ C(generic GSM CoT)+ D(反序,见 §2)
  + E(steering-only,零数据,**带随机方向基线列**)+ clean-replay 护栏。混合臂 **2000 条**量级
  token 对齐。**A2 属 Batch 2**,配比 = Batch 1 实测 RE(matched-by-measured-rescue)。
- 训练:GSM train 衍生,plain 体裁(format 组分除外——其定义 = **在格式约束下算对**的示范);
  seed 42;A1/C(及 Batch2 A2)加 43/44。脊点选点(C-9 三闸;plain 臂 parse→answered 率适配,
  适配式:answered≥0.95 ∧ json_bleed≤5% ∧ mute≤12%)。ckpt 全保留(Loop 5)。
- conduct 单组分監督动作 = **verify-then-recompute**(分诊裁决 2c)。

## 1. 度量冻结(R-23)
- **RescueEffect_k** = 臂在探针桶 k 的修复率(桶 k 失败题在脊点 ckpt 下答对的比例)
  − pre-repair 同桶基线(=0,按构造);逐桶分项报告,禁止只报总分。
- 主图:profile → recipe → 数据效率曲线(gain per 1k tokens);素题双体裁 / 出血·无效逐臂。
- Corrupt 型探针(W1/W2)走四科分解(账本口径)。

## 2. D 臂确切置换(现在写死,防事后挑)
A1 桶序(conduct, format, phrasing, scaffold, rule)=(40, 36, 16, 5, 2)%;
**D = 同桶序配比反转 =(2, 5, 16, 36, 40)%**,即 conduct 2% / format 5% / phrasing 16% /
scaffold 36% / rule 40%。除配比外与 A1 完全同源同预算。

## 3. 预测表(签字裁决①:对单组分臂实测 RE 的预测,逐格打分)
| 组分 | 预测 RE(自家证据锚) |
|---|---|
| conduct | **0.95**(E1b:300 条 resist 0→100 持久) |
| rule | **0.90**(Tier-2:显式规则 OOD 99%+) |
| format | **0.60**(可教但出血税实测,F 发现校准的定义下) |
| phrasing | **0.50 ± 待测**(无先验,显式标注) |
| scaffold | **0.50 ± 待测**(无先验,显式标注) |
| drills(证伪臂) | **≈0**(RescueEffect≈0 = 军令状第 4 行 non-claim 的实测锚) |

## 4. 臂级预测 + 三合法结局(C-11 原文登记)
- 主预期 (i):**A1 > B > C**(诊断配比>均匀>generic;A2 在 Batch2 检验 A2>A1);
- 合法结局 (ii):组分互相干扰,matched ≤ 单组分(E1 剂量律的混合版)——如实报,
  Loop 5 组分夹角负对齐可预言此结局;
- 合法结局 (iii):D ≈ A1(诊断有效粒度比桶粗;旧三世界 World-B 读法)。
- E 臂:d@α8 对 conduct 桶有 +10pp 特异增益(placebo 已测 75% 非特异底);E 的读法必须
  减去随机基线列。
- clean-replay:护栏,预期不动 profile(若动,泄漏/训练面检查)。

## 5. 灰区 / 故障态 / 伪影勾选(三件套模板)
- 灰区:A1 与 B 差 <3pp → 未决报告,不硬塞 (i)/(iii);单组分 RE 落在预测 ±0.15 内记命中。
- 故障态:某臂脊点不存在(三闸无交集)→ 该臂标"无干净运行点"如实报;LLM 生成组分
  (phrasing/scaffold/rule)构念审计 ≥70% 准入(沿探针闸门),不达标该组分降探索。
- 七类伪影:F判定(answered 适配式,披露)/F_floor(无 floor 概念,基线=pre-repair,N/A)/
  M(train 衍生自 GSM train,probe eval 衍生自 test,泄漏 validator 跑)/出血·mute(逐臂
  监控=脊点闸)/仪器(textlint+护栏 numnorm+产量闸门全线)/叙事(组分名沿 profile 桶名)。
