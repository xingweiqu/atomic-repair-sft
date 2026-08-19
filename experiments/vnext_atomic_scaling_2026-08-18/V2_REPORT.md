# V2_REPORT — Safe Frontier(C-50,2026-08-19)

**目标(C-49):predict the safe frontier —— max RepairGain s.t. clean 不掉 ∧ FA≤.10。**
全部 20 damage 校准臂 + 3 prospective 臂零失败;freeze(commit 855bc27)先于训练。数字来源:/mnt/hdfs/xwqu/vnext0818(collected.json, ANALYSIS_V2.json, PREDICTION_FREEZE_V2_*.json, V2_PROSPECTIVE_RESULT.json)。

## 结论一屏

**1. τ 转正:三点诚实验证(fit 两低点 → 预测第三点),M2 在全部 4 个模型上胜出 M1:**
| model | M1 MAE | **M2 MAE** |
|---|---|---|
| qwen3-1.7b | .160 | **.102** |
| qwen3-4b | .103 | **.088** |
| llama31-8b | .152 | **.048** |
| mistral-7b | .252 | **.172** |
C-49 说 "τ 是 hypothesis"——现在有第三剂量,**τ 升级为 validated**,且跨族收益最大(llama 误差砍到 1/3):**cross-family 适配需要的正是 dose-stretch 层**,v1 的 M1 失效之谜解了。

**2. 最重要的结构性发现:damage 主要是 composition-borne,不是单修复剂量效应。**
单臂 damage 剂量点全部温和:4 模型 ×5 repair 的 clean 掉幅全部 ≤.015;**llama 单臂 ANS@960 的 FA = 0.000**。而 v1 混合臂:1.7b clean −.025、llama FA .173。观测 offset(mixture − Σ单臂预测):1.7b clean −.026,llama FA +.173、clean −.033。**单修复 damage law 拟合得再好也预测不了混合 damage——damage 有自己的 carrier/composition 依赖**,这与 v1 论文 gain 侧的 carrier dependence 完全对偶。

**3. PARA 转正为 loss-side law(exploratory)**:pooled satexp,shared τ=30,per-model amplitude(1.7b .006 / 4b .076 / llama .138 / mistral .181)——快饱和小幅度;行为分持平如旧。

**4. Optimizer v2 双解**(benefit laws + damage 插值 + composition guards 按总剂量线性缩放):
| model | 解 | 配方 (FMT/EVD/REV/ANS/PARA) | pred U | pred clean | pred FA |
|---|---|---|---|---|---|
| qwen3-1.7b | strict | 120/240/0/960/60(=v1 optimal,声明复用) | .588 | .7405 | .037 |
| qwen3-1.7b | conservative | 0/960/0/240/0 | .371 | .7378 | .036 |
| llama31-8b | strict | 240/480/0/480/120 | .566 | .7175 | .000 |
| llama31-8b | conservative | 120/30/240/240/30 (margin=+.012) | .504 | .7251 | .081 |

**5. Prospective V2 开牌(全部 frozen 先于训练)**:
| model | arm | U | clean (base) | FA | 判定 |
|---|---|---|---|---|---|
| 1.7b | v2-strict(=v1) | .632 | .713 (−.025 FAIL) | .052 | gain 王,clean 破(已知) |
| 1.7b | **v2-conservative** | **.486** | **.769(+.032!)** | .036 | **ALL-GREEN,RepairGain +.20** |
| llama | v2-strict | .514 | .682 (−.030 FAIL) | **.000** | **FA 灾难修掉了**(v1 .173→0) |
| llama | v2-conservative | .489 | .701(−.011,**恰在 .012 noise band 内**) | .000 | 严格判 FAIL / band 判 PASS |

- **U 排名预测 v1+v2 累计 6/6 全中**(strict > conservative > replay 两模型均复现)。
- **Safe-frontier bet:1.7b 完整兑现**——conservative 臂全绿且 clean 反涨 3.2pp(EVD 重仓配方保护 clean),U 仍超 replay 20pp。实际 U .486 又高于预测 .371(diverse 低估模式第三次出现)。
- **llama:FA 约束的修复完全成功**(优化器把 ANS 控制在 480/240 + guard,两臂 FA=0.000 vs v1 的 .173),clean 差 1.1pp 卡在 noise band 边缘——**scaled-guard 的线性缩放假设对 llama 的 clean 偏保守不足**,这是 v3 唯一遗留(需要 2-3 个混合层 damage 校准点直接拟合 composition damage,而不是从 N=2 观测做线性缩放)。
- 诚实注:1.7b 上 uniform(v1)也全绿且 U(.611)高于 conservative(.486)——当前 optimizer 的 U 低估 + guard 惩罚使它没选到 uniform 型配方;把 diversity premium 从固定项升级为 fitted composition 项后应可自动收敛到该区域。

## 三个终问(C-48)在 V2 后的状态
- diagnosis 参数化 law:✓(gain 侧外推 + paired loss 诊断);
- 少数参数迁移新模型:**a + τ 两层现在都有 held-out 证据**(τ 是 V2 新增),λ 被 composition-borne damage 取代为正确问题;
- 约束下解 recipe:**1/2 模型完整全绿兑现,另 1/2 FA 修复成功 + clean 压在 noise band 边缘**——safe frontier 从 "没建模" 前进到 "一次命中 + 一次擦边"。

## v3 待办(一句话)
用 4-6 个小型混合校准臂直接拟合 composition-damage 项(替代 N=2 线性缩放 guard),再打一轮全绿 prospective;PARA/diversity 升级为 fitted composition 项。
