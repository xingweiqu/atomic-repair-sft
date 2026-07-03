# LOOP1_5_RULINGS_BATCH2 — batch-2 回收裁决（2026-07-04）

> 对 `LOOP1_5_BATCH2_HARVEST.md` 的裁决。引擎等价闸门 diff=0 认可，全部结果放行。
> 三个待裁项（桶饥饿/出血闸门/canonical floor）逐一裁决；另立一条 CC 未发现的
> 协议冲突（R-18），它影响 Loop 2 全部对照设计，优先级最高。

---

## R-15 桶饥饿裁决：选 (a)，主料 GSM-hard，MATH 备用

- **首选 GSM-hard**：它就是 GSM8K 同题换大数字——结构、步数、注入器全部原样复用，
  难度轴干净（=算术量级），且恰好是我们 Tier 2 "OOD 操作数"哲学在真实域的镜像，
  论文里两者互为呼应。MATH 子集仅当 GSM-hard 仍填不满中间桶时补充（latex 答案格式、
  题型异质，注入器要改，能不用就不用）。
- 分桶变量 = **合并题池上的 per-item pass@8**；桶按题定义、不按数据集定义；
  数据集来源作为协变量登记（与步数 KS 检验同批报告）。
- 泄漏/切分注意：训练数据仍取自 GSM8K train；GSM-hard 衍生自 GSM8K test，
  切分隔离天然保持，但 M 规则的同模板检测要对"换数字同题"显式放行说明（构造使然）。
- pass@8 全量批准：合并池（GSM8K 1319 + GSM-hard）用 v2 脚本一次测完，之后定桶边界。
  T5 功效版同批解决。

## R-16 出血闸门确认

- gate 量 = **json_bleed**，阈值 5%，批准；mute 并列报告，且补一列
  **excess-mute = mute − base 底噪 7%**（辅助读数，不进 gate）。
- 闸门按分支各自适用：每个训练分支有自己的山脊（recompute e3 vs scaffold e8），
  canonical 点逐分支判定，不共享。

## R-17 canonical floor = e8 采纳 —— 附带一道必须立即执行的重记账

采纳：GSM 域 canonical floor = scaffold_conv **e8**（parse 1.00 ∧ bleed 0% ∧ 素题无损）。
**后果 CC 报告未提**：账本 v4 全部 D/A 列目前是 **vs 30ep floor** 记的——那是一个已确认
翻过山脊、素题 acc 只剩 49% 的**受损基线**。headline 数字（override +10.8 / recompute +14.1）
建立在受损参照上，**必须 vs e8 重记后才可写入论文 §3**。预期方向：D 增益可能缩水但幸存
（e8 floor 的 resist 仍低、targeted@e2 已 1.00）；A_delivered 列的读数会更干净。
重记为零算力 csv 操作，Loop 2 开工前完成，重记前后两版数字并存留痕。

## R-18（CC 未发现）epoch 对等 vs 山脊：协议冲突裁决

冲突：epoch 对等（8/8）是为杀 epoch 混杂立的；但 sweep 显示 **targeted_recompute 在 e8
已 88% 出血**——若按 8/8 对照，targeted 侧在自己的山脊之外深处，比较的是
"健康 floor vs 中毒 targeted"，对等原则反而制造新混杂。单 operator 分支翻脊远快于
scaffold（e3 vs e8），旧观察（单 operator 漂移 30% vs 混合 17%）与此同源。

**裁决：双协议并报，主协议改为"脊点对照"。**
- **主协议（ridge-point）**：每分支取各自的最小充分收敛点
  （parse≥0.95 ∧ json_bleed≤5% 的最小 epoch；floor=e8、recompute≈e2/e3、override 按各自曲线），
  epoch 差异在表脚注显式披露。理由：比较的对象应是"各自协议下的最优交付物"，
  这也是真实训练的运行点。
- **副协议（epoch-parity@e8）**：保留作 robustness 行，读数解释时标注 targeted 侧的出血率。
- 论文措辞升级：**"对等"的正确单位不是 epoch，是收敛进度**——这本身写进 taxonomy
  （epoch 混杂条目的修正案：对等协议若以 raw epoch 为单位，会在山脊两侧制造镜像伪影）。
- Loop 2 全部对照设计按主协议执行；预注册里 D 预测的参照点相应改为脊点。

## 落位与放行

- fig_ridge(a) 定为论文主文图（§5/§6 之间的枢纽图）；"D 在脊前到账（e2）、税在脊后开征
  （e8+）——收益与代价在 epoch 轴可分离"升格为 §6 的中心句。
- e2 瞬态、pass@8 v1 案例入 taxonomy，批准。
- Loop 5 steering 放行开工（R-14 四曲线版），与 pass@8 全量并行。
- 执行顺序：R-17 重记账（本地，先做）→ pass@8 合并池全量（服务器）→ 桶边界 → Loop 2A/2B
  数据开造（floor 一律脊点规则）。
