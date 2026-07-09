# NOTES_batch1 — Loop 3 Batch-1 收割(2026-07-09)

> 口径:PREREG_loop3(冻结)。60/60 训练零失败;脊点按 C-9 适配闸门
> (answered≥0.95 ∧ bleed≤5% ∧ mute≤12%)选取。**本笔记只报数,
> A1/B/C/D 三种合法结局的判定归 Xingwei/顾问(C-11 §5),CC 不宣布赢家。**
> 复现:`python3 loop3/score_batch1.py`(输出 `loop3/eval/batch1_scores.json`)。

## 0. 脊点一览

| arm | ridge | | arm | ridge |
|---|---|---|---|---|
| A1 ×3 seeds | e4/e4/e4 | | single_conduct | e8 |
| B | e2 | | single_drills | e4 |
| C ×3 seeds | e2/e2/e2 | | single_phrasing | e4 |
| D(反转配比) | e2 | | single_rule | e4 |
| cleanreplay | e4 | | single_scaffold | e2 |
| | | | **single_format** | **NO CLEAN POINT** |

## 1. 仪器说明(先读,否则会误读表)

RescueEffect 有两种合法读法,预注册原文("桶 k 失败题在脊点 ckpt 下答对的比例")
未消歧,两种都报:

- **严口径 RE**(全签名转 ok):要求该题 8 探针全过。**被 F 探针耦合**——没喂
  format 数据的臂(C、cleanreplay、single_phrasing/rule)F 大面积不过,严口径
  被压到个位数,反映的是 F 而不是桶 k 本身。
- **松口径 REd**(判定探针转对):只要求 pre-repair 失败的判定面探针转对。
  **有非特异地板**:cleanreplay(训练安慰剂)在 conduct 桶也有 73%——
  conduct 的 W 探针失败对"任何再训练"都浅层可恢复(与 steering placebo
  发现同构)。**特异效应 = 臂 − cleanreplay**,第 2 节给 Δ 列。

桶规模(pre-repair,gsm 池):conduct 213 / format 191 / phrasing 83 /
scaffold 26 / rule 12(小,单 seed 波动大)/ unresolved 25。

## 2. 主表 — 混合臂 + 对照(松口径 REd,括号内 Δ=−cleanreplay)

| arm | O_acc | conduct | format | phrasing | scaffold | rule | W_adopt | W_mute |
|---|---|---|---|---|---|---|---|---|
| cleanreplay(安慰剂) | 80% | 73% (—) | 8% (—) | 40% (—) | 54% (—) | 42% (—) | 2% | 1% |
| A1 s42/43/44(流行度配比) | 79/79/78% | 78/74/73 (+2±) | 75/81/78 (**+70±**) | 41/46/40 (+2±) | 46/58/46 (−4±) | 42/33/17 (−11±) | 1% | 0% |
| B(均匀) | 78% | 80 (+7) | 87 (**+79**) | 47 (+7) | 58 (+4) | 58 (+16) | 1% | 1% |
| D(反转配比) | 83% | 79 (+6) | 84 (**+76**) | 51 (+11) | 65 (+11) | 33 (−9) | 2% | 1% |
| C s42/43/44(通用 CoT) | **84/83/83%** | 77/78/79 (+5±) | 4/15/6 (0±) | 43/42/45 (+3±) | 54/58/62 (+4±) | 50/42/42 (0±) | 2% | 0% |

严口径 RE(受 F 耦合,供对照):A1 conduct 50–55 / format 57–65;B 55/67;
D 59/68;C 2–9 / 4–12;cleanreplay 2/6。

**如实呈报的形态(不判定)**:
- 松口径下 conduct/phrasing/scaffold/rule 四桶,A1≈B≈D≈C≈cleanreplay
  (Δ 均在 ±16pp 内,rule n=12 噪声)。**唯一分离的桶是 format**:
  含 format 数据的混合臂 +70~79pp,C/cleanreplay ≈0。
- **D(conduct 只占 2%)在 conduct 桶与 A1(40%)打平,format 桶(5% 数据)
  同样 +76**——配比方向在本预算下未产生可见差异。
- C(不含任何修复组分)clean O_acc 最高(83–84%),但 format 桶为 0。

## 3. 单组分表(预测表打分的原料)

| arm | O_acc | 本桶 REd | 本桶 Δ | 预测 | 判(±0.15 灰区) |
|---|---|---|---|---|---|
| single_conduct e8 | 73% | 75% | **+2** | .95 | **MISS**(raw −.20;特异≈0) |
| single_rule e4 | 81% | 33% | **−9** | .90 | **MISS**(n=12) |
| single_format | — | — | — | .60 | **不可测**:无干净工作点(预测隐含前提失败) |
| single_phrasing e4 | 80% | 51% | +11 | .50± | HIT |
| single_scaffold e2 | 75% | 42% | −12 | .50± | raw HIT / Δ 为负 |
| single_drills e4 | 69% | — | — | ≈0 | 方向 HIT,但**漏报了危害**(见下) |

预测表战绩:2 HIT / 1 方向 HIT / 3 MISS。核心失准:预测时假设"修复率≈组分
与桶的匹配度",实测是"**非特异地板高 + 只有 format 桶有特异信号**"。

**跨桶意外**(记录,不解释):single_scaffold 的 REd_format = **94%**
(比所有含 format 数据的混合臂都高);single_conduct/drills 也有 64/67%。
format 桶可能对"任何带结构的输出训练"敏感——入 Loop 4 检查清单。

## 4. 两个事故级发现

### 4.1 single_format:NO CLEAN POINT 尸检
不是 bleed(全 4 epoch bleed=0.000),是 **mute+失答**:answered 峰值 0.91
(<0.95),mute 12.3–21.3% 全程超标(e2 21.3%→e8 12.3%,趋势向好但 600 条
预算内不达标)。纯 format 数据把模型在朴素文体下训哑——与 2b opsonly
corrupt-mute 52.7% 同一机制面。注入面警告(prereg 预登记)兑现。

### 4.2 single_drills:主动危害
W_adopt **25%**(其余臂 1–2%)——纯"Compute X"操练教会模型**服从题面给定
数值**,conduct 面塌方(REd_conduct 46%,唯一低于安慰剂 27pp 的臂);
O_acc 69% 全场最低。"drills≈0"预测漏掉了负号。

## 5. A2 配比签字 — **被阻塞,呈请裁决**

预注册公式 A2_k ∝ prevalence_k × RE_k(实测)。三种读法算出来的候选:

| 读法 | conduct/format/phrasing/scaffold/rule | 问题 |
|---|---|---|
| 严口径 RE | 31/—/0/15/0 | format 无脊点;三桶为 0,配比退化 |
| 松 REd raw | 75/—/51/42/33 → 归一 **55/—/22/13/10**(format 缺) | format 缺格;含非特异地板 |
| 松 Δ(clamp≥0) | 2/—/11/0/0 → **19/—/81/0/0** | 荒谬形态,仪器不支撑 |

三条路没有一条能按原设计干净落地,且 §2 显示配比方向(A1 vs D)本身未分离。
**拍板选项**(需 Xingwei/顾问签字,CC 不选):
(a) A2 改用松 REd raw + format 用"混合臂中 format 组分的边际效应"补格;
(b) 判定 Batch-2 的 A2 问题已被 A1≈B≈D 的形态架空,改测别的(如 format
剂量曲线 / drills 危害剂量);(c) 按字面执行读法 2 并如实标注缺格。

## 6. 附件
- 逐臂全量数字:`loop3/eval/batch1_scores.json`
- 脊点全 detail(含 format 四 epoch):`loop3/eval/ridge_picks.json`、`ridge_l3_*.json`
- 臂构成与字符对齐:`loop3/arms/manifest.json`
- 预注册:`prereg/PREREG_loop3.md`(未改动)
