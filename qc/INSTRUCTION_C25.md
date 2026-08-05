# CC_INSTRUCTION_C25 — Gate-2 通过;修 update 混淆后进入连续执行模式(2026-08-05,逐字存档)

> 裁决:Gate-2 工程 smoke 通过(闭环成立)。**唯一必须先修:optimizer updates 未恒定**。
> 修复+四项预算校验通过后 → 队列 A→B→C→D 自动连续执行,不再逐步请示;停止规则明列。
> Smoke 数字降级为 pipeline sanity signal,不入论文主结论。

---

## 唯一必须先修的硬伤:optimizer updates 没有恒定

三臂 target tokens 匹配很好(±0.06%),但不 packing、batch 按 example、固定 2 epochs ⇒ 条数越多更新越多:FMT200/placebo ≈ 747/600 = 1.245,多约 24.5% 步数。所以 format contract 升、semantic 降、original 降,不能完全归因 dose,可能部分来自"高剂量臂多训了几步"。DOSE_DEFINITION 写了双恒定,实际只做到 token 恒定。**正式网格前必须修。**

### 推荐执行方式

开启 packing 或 token-bucket batching;所有臂固定相同 max_steps、相同 global batch;同时匹配 assistant target tokens、total sequence tokens、optimizer updates。正式 builder 必须输出并检查:component_target_tokens / total_target_tokens / total_input_tokens / total_sequence_tokens / packed_sequences / optimizer_updates / q_d。四项偏差 ≤1%:total target tokens、total sequence tokens、packed sequences、optimizer updates。packing 不稳定就生成 token-balanced batches 并固定同一批次数。

## Smoke 报告里的结果现在只能叫 sanity signal

"向量响应命题实证了""placebo-adjust 必要性坐实"写得过重:单 seed;50 family;insufficient 26;updates 不恒定;600 条 prototype carrier。统一改成:**Pipeline sanity signal:数据组件可能同时改变格式合规、内容正确率和基础表现;该方向将在正式恒预算、多 seed 实验中验证。** Smoke 的作用已完成:证明管线能跑 + 暴露预算控制问题。不要拿 smoke 数字提前讲 scaling law。

## 其余部分基本放行

candidate contract 真两行;scorer 拒 CORRECT;self-test 实测 56/56;STATUS 接口;训练 insufficient 全量审核记录;carrier/bundle/dose manifest;嵌套剂量;hash 对齐;base failure subset 冻结;三 smoke 完成。两个不阻塞的小问题:①TRAIN_INSUF_AUDIT 逐题表应存结构化 CSV/JSON,不依赖对话记录;②zip 只带 summary,正式 Stage A 交付必须保留完整工件路径与 hash(原始 generations、逐题 scores、train logs、checkpoints)。

## 连续执行队列

### 队列 A:立即执行,修正式训练预算
1. packed/token-balanced training;2. 固定所有 arm optimizer updates;3. 新增 validate_training_budget.py;4. 重跑 placebo/FMT60/FMT200 smoke;5. 检查:target-token ≤1%、total-token ≤1%、updates 完全一致、518/518 评测、工件齐。通过后自动进队列 B。

### 队列 B:构建正式 Reasoning 资产
1. 正式 2,000 replay carrier(构建+审核);2. 扩产 2,000 format pool;3. 冻结 nested bundle order;4. 正式 reasoning evaluation:≥500 主 family、insufficient 可靠 paired subset、独立 calibration subset;5. base profile;6. template audit;7. RUN_MATRIX_format.csv。每个数据池自动检查:family overlap=0、exact duplicate=0、生成器隔离、schema overlap 申报、token 统计、随机人工审计样本、hash 冻结。通过后自动进队列 C。

### 队列 C:Format 正式全剂量网格
n∈{0,30,60,120,240,480,960,2000},主横轴用实测 q_d。先全 seed 42,再跑预冻结重复点。**Seed 锚点现在冻结:placebo 3 seeds;低/中/高剂量各一点 3 seeds(如 n=0,120,960,2000);其余单 seed。** 每 run 自动:预算检查→loss/NaN→gen eval→scorer→continuous metric→逐题保存→DONE→下一行。全部完成自动 LODO、baseline 比较、曲线图。

### 队列 D:其他组件并行建设
Format 跑 GPU 时,CPU 侧并行建 evidence/revision/answerability。每组件必经:200 prototype→数据审计→低/高剂量 smoke→正式 2,000 池→全网格。**Answerability 受控接口已饱和,不能拿 STATUS joint 拟曲线**;正式主读出=更难受控 calibration set + 自由文本 stop/guess + answerable false-abstain 三者联合。Evidence/revision 各自 smoke 过后自动进全网格,不需逐个请示。

## 自动运行停止规则

hash 不匹配;target/total tokens 偏差>1%;updates 不一致;family overlap 非零;评测行数不足;NaN/loss 爆炸;scorer self-test 未全过;工件不齐;连续两次相同配置失败 → 停当前队列。OOM 自动重跑一次,只准降 micro batch + 等比升 grad accum(global batch、LR、steps、数据不变)。不得自动改 learning rate、epoch、max steps、指标或 gate 阈值。

## 执行指令(原文)

> Gate-2 engineering smoke 通过,可以进入连续执行模式,但当前正式训练前必须先修复 optimizer-update confound。现有三臂虽然 target tokens 恒定,但 example 数分别为600/645/747,在固定2 epochs且无 packing 时更新步数不一致。
> 请先实现 packed/token-balanced training,使所有 arm 的 total target tokens、total sequence tokens、packed batches 和 optimizer updates 恒定;新增自动 budget validator,并重新运行 placebo/FMT60/FMT200 smoke。四项预算检查通过后,无需再次等待确认,自动继续执行:
> 1. 构建并审核正式2,000 replay carrier和2,000 format pool;
> 2. 扩大并冻结 reasoning evaluation,运行 base profile和模板审计;
> 3. 生成并冻结 format 全剂量 run matrix;
> 4. 连续运行全部 seed-42剂量以及预注册的重复锚点;
> 5. 每个 run 自动完成 build→budget validation→train→eval→score→artifact validation→DONE;
> 6. Format 运行期间并行建设 evidence、revision和answerability 数据池,各组件完成 prototype audit和low/high smoke后自动进入正式网格;
> 7. 仅在 hash不一致、预算偏差、数据重叠、NaN、评测缺行或工件缺失时停止。不得在运行中自行修改学习率、训练步数、指标或 gate 阈值。
> Smoke 数字只标为 pipeline sanity signal,不进入论文主结论。

## 最终判断

可以让 CC 连续跑起来。正确的批准方式是:修正更新步数混淆后,批准自动连续执行 Format 全流程,并并行建设其他组件。这个改动不大,但决定后面拟出来的到底是 component-dose response,还是多训练了几步的 response。
