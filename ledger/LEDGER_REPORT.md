# LEDGER_REPORT — Loop 1 账本重建(2026-07-02)

> 口径:`qc/INSTRUCTION_v1.md` §1 + `qc/LOOP0_RULINGS.md` C-1/C-2/C-3、R-1/R-2/R-3(冻结)。
> 产物:`ledger/master_ledger.csv`(671 行,R-3 粒度 (ckpt, eval cell))、`ledger/inventory.md`
> (92 run 全对齐,0 缺失)、`ledger/fig_ledger.png`、`ledger/leak_flags_*.jsonl`、
> `qc/LOOP1_JUDGE_REGRESSION.md`。全部零训练,只重评历史预测。
>
> **结论先行:账本建成、闸门全过;但 Phase-0 DoD 的 "|A|<2pp" 在 v4 域触发硬停——
> 验尸表明这不是"修复买到能力",而是"收敛 floor 支出了能力"(见 §5,含判别诊断)。
> 按纪律停下待裁决,未自行改写主命题。**

---

## 1. 闸门状态

| 闸门 | 结果 |
|---|---|
| D-2 judge 回归(只封装未改判定) | **17/17 PASS**(`qc/LOOP1_JUDGE_REGRESSION.md`;历史档=evaluate_v3 原链,update_value 兜底只进 lenient 档——首轮 14/17 的 3 个偏差即由此修正,方向全为 wrapper 偏高) |
| 泄漏阴性对照(应为零) | **v4 = 0/480、v5 = 0/1600 PASS**。v4 首轮 45.2% 是规则伪影(见 §2 验尸),非真泄漏 |
| residual < 3pp | **0 行超限**。注意:C-1 口径下四层分解在其作用域内**按构造精确闭合**,residual 只能捕捉管线 bug,不再是叙事量——这是 C-1 的直接推论,如实披露 |
| 覆盖 ≥90% 历史 run | 92/92 对齐 run 入细账(v0/v1 灰名单另计,见 inventory) |

## 2. 泄漏标记(R-2)

| domain | n | leak_sft | leak_inject | leak_any |
|---|---|---|---|---|
| v2 | 600 | 70.0% | 70.0% | **70.0%** |
| v2_1 | 600 | 70.0% | 70.0% | **70.0%** |
| v3 | 600 | 60.0% | 60.0% | **60.0%** |
| v3_1 | 720 | 66.7% | 66.7% | **66.7%** |
| v4 | 480 | 0 | 0 | **0** |
| v5 | 1600 | 0 | 0 | **0** |

- 判定 = 该题**完整答案支撑**(全部 gold 三元组)⊆ 暴露集;R 类题的操作数三元组
  (`(op, applied_to, "a,b")`)天然不在注入语料 → compute 题只可能经 SFT 操作数碰撞泄漏(实测 0)。
- `leak_sft == leak_inject`:小世界的全部 lookup 链既被注入语料覆盖、也被 repair-train 覆盖,
  两个来源命中同一批题(K/H lookup 全命中,R/abstain 全不命中;v3.1 逐 policy 核对吻合:
  180 keep + 120 support + 60 override + 60 bridge + 60 K-Abl recompute = 480 = 66.7%)。
- 与 `bprime/leakage_audit.md` 的 79.4% 不矛盾:那是**三元组级**重叠比例,本表是**题级全支撑**比例,
  口径不同(R-2 要求的正是后者)。
- **v4 规则验尸**(首轮 45.2% → 0):source_id 重叠 0、题面重叠 0;伪命中全部来自无鉴别力数值 key
  (abstain trace 无数字、keep trace 只含最终值)。修正:数值 key 要求 ≥2 个中间值(v1 §1.3-M 的
  "最终数值+关键中间值组合"本义),外加 source_id/题面双检。校准过程留档于 git 历史,
  可作 Loop 2B "M 校准品"的反面教材。

## 3. 主账(cell=ALL,单位 pp;完整粒度见 csv)

**v4(GSM,干净域;floor = scaffold_conv)**

| ckpt | Δraw | F_judge | F_parse | M | D | A | ND |
|---|---|---|---|---|---|---|---|
| actionized_full | +6.7 | 0 | 0 | 0 | −0.4 | **+4.7** | +2.3 |
| targeted_verify_step | −5.4 | +0.2 | −1.9 | 0 | +3.1 | +2.1 | −9.0 |
| targeted_override | −1.7 | 0 | −0.6 | 0 | **+4.8** | +3.5 | −9.4 |
| targeted_recompute | −11.9 | 0 | 0 | 0 | +3.5 | −1.6 | −13.8 |
| scaffold_only(欠拟合) | −2.9 | +9.0 | −20.0 | 0 | +2.1 | +9.4 | −3.3 |

对角线(targeted_X 在 cell X)与历史完全吻合:+3.8/+10.0/+7.5/+0.0 ↔ comparison_v4 的 +4/+10/+8/+0
——D 渠道承载 override(+10.8)/recompute(+14.1),A 渠道 matched 口径后 −2.1~+6.0(见 §5)。
ND 为负 = 单 operator 训练在 keep 类上过度修复(历史 transfer-drift 结论的账面形态)。

**v3.1(合成,重泄漏域;floor = scaffold_conv)**

| ckpt | Δraw | F_judge | F_parse | M | D | A | ND |
|---|---|---|---|---|---|---|---|
| actionized_full | +6.2 | 0 | 0 | +4.2 | 0 | +2.1 | 0 |
| targeted_override | −39.6 | 0 | −0.4 | **+50.4** | −7.6 | −60.3 | −21.7 |
| targeted_verify_bridge | −45.6 | 0 | −7.5 | **+46.9** | −10.1 | −51.1 | −23.8 |
| factonly | −47.5 | +38.6 | −97.9 | +11.8 | 0 | 0 | 0 |

预期图景兑现:**v3 谱系的条大部分是 M**(单 operator 相对收敛 floor 的 ALL 为负 = 对角线故事
只在 per-cell 行成立,off-diagonal 被砸掉;历史正增益是相对 scaffold_only 欠拟合地板的,
差额按 C-2 落入 F_floor 列)。

**v5(天花板域)**:全部渠道 ≈ 0(floor 已 100%),继续作为"账本在饱和域读数为零"的阴性锚点。

**v2/v3(factonly floor 域)**:F_judge ≈ −39.7 与 F_parse +71~+100 大而对冲——factonly 地板
**不会输出可解析 JSON**(strict≈0、lenient≈39.7),C-1 口径下一切增益都从 parse 门流过,
D/A 在该基线下**不可测**(n_w=0)。这本身就是账面结论:v2/v3 时代的"修复增益"无法与
"学会输出格式"分离,收敛 scaffold floor(v3.1 起)才让 D/A 可测。

## 4. R-1 可分解占比(裁决 §4 要求)

per-cell 行 484,其中可分解(有 (g,w) 对且可测)**106 行 = 22%**(planted 73 / tentative 33)。
原因分两类:(a) 结构性——keep/abstain/Aug/Abl/Clean cell 本无 w;(b) 基线性——v2/v3 的
factonly floor 无 both-parsed 题,W 集为空。**远低于半数 → 按裁决,主图采用双叙事:
可分解子集四渠道 + 全集 F/M 两渠道**(fig_ledger 已按此渲染,ND 灰色显式标出)。

## 5. ★ 硬停:干净测量中 A 显著非零 —— 及其验尸

**触发**:v4 若干格 |A| ≫ 2pp(Shapley 口径,vs 收敛 floor):
`scaffold_only:verify_step` A=+20.2(matched +25.9, n=58)、`actionized_full:verify_step`
A=+19.4(matched +19.0, n=79)、`actionized_full:ALL` matched +12.8(n=164)。C-3 门槛(n≥50)之上,
不能当噪声吞掉。

**判别诊断**(零训练,换参照重算 pairwise matched ability;pre-repair = diagnosis_base):

| run | a(pre-repair) | a(run) | Δ | n |
|---|---|---|---|---|
| scaffold_conv(收敛 floor) | 0.960 | 0.440 | **−0.520** | 50 |
| actionized_full | 0.958 | 0.583 | **−0.375** | 48 |
| targeted_verify_step | 0.967 | 0.574 | −0.393 | 61 |
| targeted_recompute | 0.968 | 0.468 | −0.500 | 62 |
| scaffold_only(3ep) | 0.947 | 0.895 | −0.053 | 38 (LOWPOWER) |

**读法**:在 pre-repair 模型能做对的题上,30ep 收敛 floor 只剩 44%,所有修复 ckpt 都在
47–70%。**没有任何 ckpt 的 matched ability 超过 pre-repair 模型**。因此 vs floor 的正 A
是**基线损伤伪影**:收敛 floor 为了买 format 付出了 −52pp 的 ability 税,修复训练只是
"税付得少",在被砸坏的基线上显正。方向甚至随 epoch 单调(3ep −5pp → 30ep −52pp),
与既有 transfer-drift/epoch-sweep 观察同向。

**对主命题的含义(待裁决,未采纳前不写入论文)**:
- 主命题"A ≈ 0"在**以 pre-repair 为参照**时以更强形式成立:**A ≤ 0**——修复训练从不把
  matched ability 抬到 pre-repair 之上;
- 但 v1 §A 的规范基线 = 收敛 floor,在该基线下 DoD "|A|<2pp" **不成立**(会被审稿人抓同一漏洞);
- **提案 C-4**:A 声明改为双参照——"vs 收敛 floor 的 A" 记账用,"vs pre-repair 的 A" 作
  能力主张判据;并把"收敛 floor 的 ability 税"立为 Artifact Taxonomy 第六类(协议伪影的
  ability 面),Loop 2 的 epoch 对等设计(8/8)正好是它的对照实验。
- 局限如实报:pre-repair matched 子集偏易(以 base resist∩parse 为条件)、若干 n<50。
  epoch-sweep(pending)的 e1/e2/e8 点能把 "ability 税 vs epoch" 曲线补完——建议升级为
  Loop 1.5 优先项。

## 6. 本账本立即推翻/支持的旧结论

| 旧结论 | 账本判定 |
|---|---|
| v2 "Skill+CoT 85.5 > CoT 79"、v3 时代各绝对增益 | **不可分解为 D/A**(factonly 地板 parse≈0),增益与格式习得混同;历史排名在 F 层内重排,不再作能力主张 |
| v3.1 对角线 = 对症诱导 | per-cell 对角线仍在,但 **M 层吃掉 lookup 类大头**(leak_any=66.7%);干净对角线证据只剩 R 类 + abstain;ALL 视角单 operator 净负 |
| v4 "决策被注入、算术不动" | **D 渠道确认**(override +10.8 / recompute +14.1);"算术不动"需修正为"**算术被支出**"(§5) |
| v5 天花板 | 支持:全渠道读数 0,账本在饱和域不产生伪增益 |
| "abstain 纯诱导 0→100" | 支持,且在账内表现为 D/ND 而非 F(C-1(ii) 的 abstain≠F 裁决兑现) |

## 7. 给 Xingwei 的验收问题

1. **§5 硬停**:接受 C-4 双参照提案、并把 epoch-sweep 升级为 Loop 1.5 先跑吗?(这决定 Loop 2
   设计里 floor 的 epoch 对等是否要再加 "pre-repair 参照列")
2. 账本哪几笔与你记忆不符?候选提醒:(a) v3.1 targeted 在 ALL 视角是**净负**(你记的 +69~+93
   是对角线 vs scaffold_only,两者都对,口径不同);(b) v2/v3 的增益在账本上几乎全是 F——
   与"CoT→79%"的记忆不冲突,但那 79% 现在读作"格式门内的混合增益"。
3. v2_1 七个 run 因无 floor 预测只入绝对分(csv 有行、无 Δ)——要补一次服务器 predict
   (factonly ckpt × v2.1 eval,一条命令)把它们转成细账吗?
4. D-6(底模型)与 D-7(pass@8)仍待你侧动作,不阻塞本报告审阅。
