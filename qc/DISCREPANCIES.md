# DISCREPANCIES — 指令假设 vs 仓库实际(Loop 0 起持续维护)

> 格式(按 qc/INSTRUCTION_v2.md 工作模式 §2):指令假设了什么 / 实际是什么 / 影响哪个后续 Loop /
> 建议方案。**未经裁决不实现、不悄悄替换口径。**
> 状态:OPEN(待裁决)| PROPOSED(方案已提待确认)| CLOSED(已裁决,附结论)。

---

## D-1 v1 预测文件是误跑产物 【OPEN → 需 Xingwei 裁决】
- **指令假设**(A2):v0–v5 各 run 预测原文件仍在、可统一重评入细账。
- **实际**:`output/qwen3_8b_repair_v1_{A,B,C,D}_predict/` 存在(各 550 行,commit 7a7d59f),但
  550 行 = v0 eval 规模,≠ v1 shipped spec 的 660(`[atomic-repair-v1 私有库] data_v1/repair_eval` 660);
  该 commit 是有记录的服务器误跑(codex 未用 shipped v1 管线;修正版 rerun 从未执行)。
  实测 prompt 内**无**内联 oracle facts(grep "Oracle facts" = 0/550×4),但 B/C/D 的 ckpt 谱系不明。
- **影响**:Loop 1 账本的 v1 行。
- **建议**:v1 四行入**粗账**并标注 "misfired run, lineage unverified",或整体排除+脚注。倾向前者
  (可作 Artifact Taxonomy 案例)。

## D-2 F 渠道的 lenient/strict 双模式 judge 不存在现成开关 【PROPOSED】
- **指令假设**(A1 / v1 §1.3-F):同一预测文件可分别用 lenient 与 strict judge 打分,差值记 F。
- **实际**:abstain 维度有双模式(`evaluate_v3.py:63/:80/:152–153`);final_answer 维度只有一条混合
  宽松提取链(JSON→regex→last-line,`evaluate_v3.py:34–56`),无 strict-only 开关。
- **影响**:Loop 1 第 1 层记账(F)。
- **建议**:Loop 1 新增薄包装 `ledger/judge.py`:strict = 合法 JSON 且含 `final_answer` 字段 +
  `is_abstain_strict`;lenient = 现行 fallback 链 + `bprime_audit.extract_final` 的 `update_value` 兜底 +
  `is_abstain_lenient`。**不改任何既有判定逻辑,只封装成两档。**

## D-3 恒等式在 parse<1 时不闭合(resist 分母口径) 【OPEN → 口径提案,需顾问/Xingwei 冻结】
- **指令假设**(v1 §1.2):`final_acc = resist × ability|resist` 精确成立。
- **实际**:现实现 resist 分母 = committed/parsed items(`bprime/bprime_audit.py:90`),final_acc 分母 =
  全量 → parse<1 时恒等式不闭合,缺口流入 residual(v4 部分 run parse 0.78–0.80,缺口可 >3pp)。
- **影响**:Loop 1 每一行的 D/A 拆分与 residual 验收。
- **建议口径补充**:第 1 层剥 F 之后,resist 与 ability 都定义在 **parsed 子集**上,unparsed 项全额记 F;
  这样第 3 层恒等式在其作用域内精确闭合,residual 只剩舍入。**冻结前不实现。**

## D-4 matched-subset 交集范围:pairwise vs 全 ckpt 【OPEN → 需确认双轨用法】
- **指令假设**(v1 §1.1):比较两个 checkpoint 用**二者**共同 resist 的交集。
- **实际**:`bprime/bprime_audit.py:95–123` 支持 pairwise;`gsm_repair_v4/epoch_sweep.py:119–124` 用
  **全部** ckpt 的交集(fixed subset,更强、n 更小,为多点曲线设计)。
- **影响**:Loop 1 账本 A 列、Loop 4 epoch 曲线。
- **建议**:账本(两两比较)用 pairwise 照 §1.1;epoch/剂量曲线(多点同图)用 fixed-all 并在脚注
  声明 n。两者并存不冲突。

## D-5 leakage_audit 无 per-item 标记输出;GSM 规则未实现 【PROPOSED】
- **指令假设**(A3 / v1 §1.3-M):泄漏规则可输出 per-item leak 标记;可泛化到 GSM。
- **实际**:`bprime/leakage_audit.py` 可执行 ✓,但只输出聚合统计+md(:163);per-item `leak(i)` 文件
  不存在。GSM 数值/模板重叠只有雏形(:129–143 gold 数值集合对比),无 n-gram/模板正式规则。
- **影响**:Loop 1 第 2 层(M)记账。
- **建议**:Loop 1 扩展 `leakage_audit.py` 输出 `ledger/leak_flags_{v3,v3_1}.jsonl`(triples() 已
  per-item,<30 行);GSM 规则按 v1 §1.3-M 新写(最终数值+关键中间值 n-gram + 模板检测),
  以 v4 预期 leak≈0 为阴性对照。

## D-6 A7 底模型型号本地不可闭合 【CLOSED 2026-07-03】
- **裁决结论**:服务器 `head -5 /mnt/hdfs/xwqu/Qwen3-8B/README.md` → 模型卡 frontmatter
  `license_link: https://huggingface.co/Qwen/Qwen3-8B/blob/main/LICENSE` = **Qwen/Qwen3-8B(Instruct)**。
  Loop 3/5 门禁解除。论文措辞按 LOOP1_RULINGS D-6:统一 **pre-repair model**。
- **指令假设**(A7):给出 config 级证据判定 Base 还是 Instruct。
- **实际**:本地证据全部指向 **Instruct**——v2–v5 configs 用 `/mnt/hdfs/xwqu/Qwen3-8B`(HF 命名法
  无 -Base 后缀即 post-trained 版;v0/v1 的 Base 路径显式带 `-Base`)、`README_v2.md:46` 写明
  "Qwen3-8B-Instruct"、`SPEC_v2.md:100` 条件 A = "原始 Instruct"。但目录内容在服务器,本地无法验尸。
- **影响**:**Loop 3 / Loop 5 门禁**(指令明文:此项不关闭不得启动)。
- **建议**(服务器只读命令,任选其一):
  ```bash
  python3 -c "import json;c=json.load(open('/mnt/hdfs/xwqu/Qwen3-8B/config.json'));print(c.get('_name_or_path'),c.get('model_type'))"; ls /mnt/hdfs/xwqu/Qwen3-8B/ | head
  # 或
  head -5 /mnt/hdfs/xwqu/Qwen3-8B/README.md
  ```

## D-7 base pass@k 无缓存 【OPEN → 确认前置服务器任务】
- **指令假设**(A8):v4 GSM 资产含 base pass@k 缓存。
- **实际**:grep `pass@|pass_at|n_samples` 于 `gsm_repair_v4/` 与 `scripts/run_v4*` 零命中;历史 v4
  预测全部 do_sample=false 单次贪心,无法折算 pass@8。
- **影响**:Loop 2A 分桶(桶定义就是 per-item pass@8)。
- **建议**:Loop 2A 第一步 = 产出 pass@8 测量任务入 RUNBOOK(GSM test 1319 题 × 8 样本,
  temperature 按 Qwen3 推荐;可先 500 题试跑标定桶边界)。

## D-8 parse≥0.95 收敛闸门无自动脚本 【PROPOSED】
- **指令假设**(A6):收敛闸门(parse≥0.95)有现成模板。
- **实际**:parse_rate 是 scorer 报告字段(`scenario_repair_v5/score_v5.py:108` 等),阈值判断靠人读。
- **影响**:Loop 3 交付("pull 下来不改文件就能跑"应含自动 gate)、Loop 4 floor 合格判定。
- **建议**:Loop 3 附 `qc/gate_parse.py`(读 predictions → parse_rate,<0.95 exit 1),RUNBOOK 在每个
  floor 训练后插一步 gate。

## D-9 运算符生成器:范围可参数化,但四档家族是新开发 【PROPOSED】
- **指令假设**(A5):v3 合成运算符生成器"可参数化改造"为可调可学性家族。
- **实际**:`reasoning_world_v2.py:33` OPERATIONS 是代码内 dict(fn/steps 为 lambda,非数据文件);
  操作数范围可参数化(`operand_pairs(lo=2,hi=12)` :95、`build_reasoning_split` :125 全组合枚举后切分,
  天然支持"未见组合"切分)。但:档位 a(纯查表)/c(两步)/d(三步)不存在,需新生成逻辑;
  三位数 OOD 需检查 steps 措辞与 cutoff_len=1024 预算。
- **影响**:Loop 2B(核心新数据资产)。
- **建议**:Loop 2B 新建 `learnability_family/`(import 现有 OPERATIONS 作档位 b),不改旧文件;
  交集=∅ 断言脚本随生成器一并交付(枚举式切分使其易写)。

---

## 附:非阻塞观察(不构成分歧,记录备查)
- `template: qwen`(非 `qwen3`)全线一致(`configs/v5/*_sft.yaml` 等)——Loop 3 新 config 必须沿用,
  保持与历史 run 可比,不要顺手"升级"。
- v3.1 的 `predict_scaffold_conv` 只在 `scenario-repair-b-prime` 分支(v4 分支上没有)——Loop 1 取数注意。
- epoch-sweep 23 个训练点的预测尚不存在(configs 就绪、服务器未跑)——这是既有 pending,
  Loop 4 并入,不属于资产缺失。
- SETTING.md 此前从未 git 提交(untracked)——随本次 Loop 0 一并入库,保证引用可追溯。

## D-10 C-10 §2a 假设的 "Paper 1 Wikidata 1-hop 生成管线" 不存在 【PROPOSED】
- **指令假设**:K-Cor 真实域 = Paper 1 的 Knowledge 生成管线(Wikidata 1-hop)放量。
- **实际**:monorepo 全库 grep 无任何 wikidata/SPARQL 代码;Paper 1 的 K 项是 API 生成的
  合成事实(generate_items.py, anthropic 客户端),没有可"放量"的真实域管线。
- **影响**:C-10 §2a(K-Cor 数据)→ §3 训练队列。
- **建议方案(已按此实施,等追认)**:事实源改用 **LAMA/T-REx**(标准 Wikidata 1-hop
  三元组基准,可引用、带模板);问题模板逐关系手写;Corrupt 注入 = v4 claim 措辞库 +
  同关系宾语池 type-matched 错值;schema 与 R-Cor(v4 actionized)逐字节一致;
  实体不相交切分 + 逐题泄漏标记照 C-10。construct=resist+recall,附 "base 已知率" 探针
  (K-Cor 的 gold 恢复依赖参数记忆——这里干净闸门是反的:希望 base 认识这些事实)。

## D-11 C-10→C-11 交接登记 【CLOSED(C-11 Loop 0.4 明文)】
- 2Wiki:从主实验降级为**验证章**(Loop 6,缩微复现),不再阻塞主线;E4 筛选数字
  (exact 22.5%/contains 47%)转为 Loop 6 设计输入。
- **K-Cor 真实域数据集需求撤销**:kcor_real/(生成器+1500/600 数据+card)保留入库
  作资产,不进主线训练;其职能由 GSM 域内 W2 探针(wrong-final-claim)承担。
- natural corrupted-context set(100–200 条)保留原规格,改挂 Loop 6。
- Transfer Matrix 三世界预注册(PREREG_transfer_matrix)保留冻结——其 K/R 迁移检验
  由 Loop 3 纠错验证臂的 W1/W2 双评测接替,三世界读法映射到臂结局 (iii)(D≈A ↔ World B)。
