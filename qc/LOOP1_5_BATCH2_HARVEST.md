# batch-2 回收报告(2026-07-04)— 山脊曲线 + pass@8 v2 + 引擎闸门

> 输入:server commit d7d0b78(46 predict 目录 480/300 行全对 + pass8_calib500_v2 + sidecar)。
> 全部分析零算力本地完成。产物:`data_v4/results/{epoch_sweep_v4.md, fig_epoch_sweep.png,
> bleed_curve.json, fig_ridge.png}` + 本报告。

## 0. 引擎等价闸门(本地版)— PASS,diff 精确为 0

服务器未回报 gate 打印,但 symlink 复用点提供免费同 ckpt 对照:5 个 round-1 ckpt
(scaffold_conv、targeted_override/recompute/verify_step@e3、random_override@e3)的
batch-2 预测 vs round-1 LF 预测,strict 总分 **diff = 0.0000 ×5** → 账本等价,结果放行。

## 1. pass@8:v1 污染实锤,v2 干净(R-13)

| | v1(thinking 截断) | **v2(no_think, 2048)** |
|---|---|---|
| 0/8 题数(500 题) | 101 | **13** |
| 8/8 题数 | 168 | **404** |
| 四桶 [0-25]/(25-50]/(50-75]/(75-100] | 164/54/61/221 | **22/17/17/444** |

v1 的 [0-25] 桶 ~87% 是仪器伪影——"thinking 模板吃预算"案例坐实,入 taxonomy 附录(R-13)。

**★ Loop 2A 设计红旗(需顾问/Xingwei 裁决)**:v2 真实分布下 GSM test 对 Qwen3-8B 接近
饱和——外推全量 1319 题:[0-25]≈58、(25-50]≈45、(50-75]≈45、(75-100]≈1171。
**中间两桶各只有 ~45 题,Loop 2A 规格(每桶 eval ≥500/≥300)在纯 GSM8K 上不可满足。**
选项:(a) 混入 GSM-hard/MATH 子集拉开难度(v1 指令 Phase-1 已预见此项);(b) 桶边界重定义;
(c) 缩桶数。T5 功效版同样依赖 [0-25] 桶,同一决策覆盖。

## 2. 山脊曲线(R-6/R-11)— 双边陷阱实测,且有干净运行点

**出血率的口径校准(数据驱动,报顾问确认)**:mute 有 ~7% 的 base 底噪(pre-repair 自己
23/300 不作答),不是训练产物;**训练性出血信号 = json_bleed**(体裁入侵),gate 量用它,
mute 并列报告。

**scaffold_conv(floor 分支)**:

| epoch | parse(repair-mode) | json_bleed(素题) | 素题 acc(base=92%) |
|---|---|---|---|
| 1 | 0.26 | 0% | 92% |
| 2 | 0.43 | 0% | 93% |
| 3 | 0.81 | 0% | 94% |
| **8** | **1.00 ✓** | **0% ✓** | **92%(无损)** |
| 30 | 1.00 | **31%** | 49% |

→ **canonical floor(GSM 域)= scaffold_conv e8**:parse≥0.95 ∧ json_bleed≤5% 的最小
epoch,且素题 acc 与 pre-repair 持平。**round-1 的 30ep 收敛 floor 已翻过山脊**
(31% 出血、素题 acc 掉到 49%)——Loop 1 硬停的 −52pp in-genre 读数至此来龙去脉全部闭合。

**其余分支**:
- targeted_recompute:e3 后体裁入侵猛烈(e8 json_bleed **88%**、e30 98%,素题 acc→0-1%);
  它自己的山脊点 = e3。单 operator 训练翻山脊远快于 scaffold。
- targeted_override:e30 json_bleed 28%;targeted_verify_step:e30 96%。
- **e2 瞬态失稳**(如实登记):多分支在 e2 出现 30–75% mute(素题暂时哑火),e3 恢复——
  与 repair-mode parse 的 e2 过渡期同步,属收敛过程瞬态,不改变山脊结论。
- **素题 answered-acc 全程 85–99%**:作答时算术基本无损——T4 的 H2 结论在全 sweep 复现。

**repair-mode 内(fig_epoch_sweep)**:
- **D 到账早且便宜**:targeted_override resist 0.68@e1 → **1.00@e2** → ~0.99 稳定;
  random_override 始终不稳(0.64/0.95/0.43/0.66/0.73)→ targeted 特异性在决策层真实存在。
- **in-genre ability 读数单调衰减**:targeted_recompute ability|resist(fixed n=60)
  0.58@e1 → 0.52@e2 → 0.40@e3 → 0.38@e8 → 0.33@e30——把 "−5pp@3ep → −52pp@30ep"
  的中间点补齐,衰减与出血同向。
- 论文主张(R-10 层级)获得曲线级证据:**D 在山脊之前就已到账(e2);体裁税在山脊之后
  才开始收(e8+)——修复的收益与代价在 epoch 轴上是可分离的。**

## 3. 落位

- 论文 §5(体裁机制):fig_ridge(a) = "山脊"主图;fig_ridge(b) = 出血×分支 + 读数衰减。
- 论文 §6(机制/epoch):fig_epoch_sweep = D 低 epoch 到账 + in-genre 读数衰减。
- Artifact Taxonomy:pass@8 v1 案例(仪器 F 类)+ e2 瞬态(协议类脚注)。
- Loop 2 设计输入:floor 一律用"最小充分收敛"规则(本域 e8);ability 主张一律双体裁
  (R-7);**Loop 2A 桶量问题待裁决(§1 红旗)**。

## 4. 等待

1. 顾问:①§1 红旗(GSM 桶饥饿 → 混 MATH/GSM-hard?);②json_bleed 作 gate 量 + 5% 阈值确认;
   ③canonical floor=e8 采纳(Loop 2 所有 v4 系 floor 换 e8 ckpt)。
2. pass@8 全量 1319(等 ①裁决后跑,若混 MATH 则量表一起定)。
3. Loop 5 steering(并行获批,规格 R-14 四曲线)——下一个本地+单卡工程。
