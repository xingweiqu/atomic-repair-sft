# Loop 0 — 资产质检报告(ASSUMPTIONS_AUDIT)

> 指令:qc/INSTRUCTION_v2.md Loop 0(A1–A9)。口径:qc/INSTRUCTION_v1.md §1(冻结)。
> 审计日期 2026-07-02。分支 `gain-accounting-v1`(切自 `scenario-repair-v4` @6245433)。
> 全程只读:未改任何既有代码/数据/config。证据格式 `[branch] path:line`。
> ⚠️/❌ 项的详细分歧与建议方案见 qc/DISCREPANCIES.md(编号 D-x)。

## 总览

| # | 假设 | 结论 | 一句话 |
|---|---|---|---|
| A1 | 最终版 strict judge 存在 | **⚠️** | strict judge 在、ERRATUM 已合并主路径;abstain 有双模式,**全量 lenient/strict 双评需薄包装**(D-2) |
| A2 | v0–v5 预测原文件仍在 | **✅(带1个例外)** | v0/v2/v2.1/v3/v3.1/v4/v5 全部有原文件可入细账;**v1 预测是误跑产物**(D-1) |
| A3 | 泄漏规则可脚本化 | **⚠️** | 已是可执行代码;缺 per-item leak 标记输出(小扩展)+ GSM 规则需新写(D-5) |
| A4 | resist/matched-subset 有实现 | **✅(带2个口径澄清)** | 成型代码;resist 分母与恒等式闭合问题(D-3)、交集口径两种并存(D-4)待裁决 |
| A5 | 运算符生成器可参数化 | **⚠️** | 结构支持;操作数范围可参数化(现仅 2–12);四档家族+三位数 OOD 需真实开发(D-9) |
| A6 | epoch 对等 + 收敛闸门模板 | **✅(闸门 ⚠️)** | 46 个 epoch-sweep config 覆盖 {1,2,3,8,30};v5 8/8 协议 config 在;parse≥0.95 无自动闸门脚本(D-8) |
| A7 | 底模型确切型号 | **⚠️(强证据 Instruct)** | 文档+config 一致指向 Instruct;需服务器 1 条命令关闭(D-6)。**Loop 3/5 门禁** |
| A8 | GSM 资产可复用 | **⚠️** | 注入器/eval 集 ✓;**pass@k 无缓存** → Loop 2A 前置服务器测量(D-7) |
| A9 | v5 逐行超参 | **✅ 已关闭** | 逐行抄录见下;SETTING UNVERIFIED #5 关闭 |

---

## A1 — strict judge(⚠️)

**存在且 ERRATUM 已合并主评分路径:**
- strict abstain 判定:`[gain-accounting-v1] scenario_repair_v3/evaluate_v3.py:63`(`is_abstain_strict`);
  lenient 变体 `:80`;**headline 默认 = strict**:`:88`(`is_abstain = is_abstain_strict`)、评分循环 `:115`、
  输出字段 `:152–153`(同时报 strict 与 lenient abstain 率)。
- GSM scorer 复用同一 strict 判定:`gsm_repair_v4/evaluate_gsm.py:26`(import `is_abstain_strict`)。
- ERRATUM 文档:`data_v3/ERRATUM_abstain_judge.md`(v3 旧表保留、新路径 strict)。

**缺口(D-2):** F 渠道要求"同一预测文件 lenient / strict 双评"。现状:
- abstain 维度:双模式 ✓(`:152–153` 同时输出)。
- final_answer 维度:只有一条**混合宽松**提取链(`parse` JSON→regex `{...}` 兜底 `:34–41`;
  `final` 再兜 "final answer:" regex→最后一行 `:52–56`),没有可开关的 strict-only 模式。
- 判定:**所有零件都在**,Loop 1 需写一个薄 judge 包装(strict = 合法 JSON 且含 `final_answer` 字段;
  lenient = 现行 fallback 链 + `bprime_audit.extract_final` 的 `update_value` 兜底),不改口径、只是封装。

**老 scorer 兼容:** v0(`evaluate_predictions.py`)/v2(`evaluate_v2.py`)/v2.1(`evaluate_v2_1.py`)时代
schema 同样输出 JSON `final_answer` → 统一 strict judge 可直接重评 final 层;各版 gold 在对应
`data_v*/repair_eval.jsonl` / `data/` 内。

## A2 — 预测 JSON 原文件清单(✅,v1 例外)

盘点方式:6 分支 `git ls-tree -r`(证据即命令输出;目录级列举如下)。**细账**(有原文件,统一重评可行):

| 版本 | 位置(分支) | run 数 | 备注 |
|---|---|---|---|
| v0 | `[main+] output/qwen3_8b_repair_full_predict/` | 1 | 550 行 |
| v1 | `[main+] output/qwen3_8b_repair_v1_{A,B,C,D}_predict/` | 4 | **⚠️ 误跑产物,见 D-1** |
| v2 | `[atomic-repair-v2+] data_v2/predict_outputs/` | 7 | factonly/fc/fs/inject_base/inject_floor/zs_cot/zs_direct |
| v2.1 | `[atomic-repair-v2.1+] data_v2_1/predict_outputs/` | 7 | actionized/cot_fixed/decision/randomskill/skillcot_fixed/prefix_{gold,wrong} |
| v3 | `[scenario-repair-v3-targeted-operators+] data_v3/predict_outputs/` | 26 | full/cot/factonly + 6×{targeted,random,wrongtarget} + M1–M6 |
| v3.1 | `[scenario-repair-v4] data_v3_1/predict_outputs/` 21 个;**`predict_scaffold_conv` 仅在 `[scenario-repair-b-prime]`** | 22 | 账本需从 b-prime 取 scaffold_conv |
| v4 | `[scenario-repair-v4+] data_v4/predict_outputs/` | 23 | 含 3 个 transfer + scaffold_{only,conv} + diagnosis_base |
| v5 | `[scenario-repair-b-prime] data_v5/predict_outputs/` | 15 | 仅此分支 |

**粗账/缺口:** epoch-sweep 的 `_e{N}` 各点预测**尚未存在**(configs 已备、服务器未跑——即既有 pending 实验);
除 v1 外没有"只剩汇总 md"的 run。**覆盖率:细账 run ≈ 101/105 (96%) ≥ 90% DoD。**

## A3 — 泄漏规则(⚠️,可脚本化 ✓)

- **已是可执行代码**:`[scenario-repair-b-prime] bprime/leakage_audit.py`(170 行;
  triple 抽取 `triples()` :36、实体掩码模板比对 `mask_entities()` :26、oracle 重叠主检查 §1b :85、
  v4 GSM 对照 :129、输出 md :163)。指令引用的 79.4% 三元组重叠即其 §1b 输出,与 SETTING.md v3-A5 一致。
- **缺口 1(小)**:现只输出聚合统计;v1 §1.1 要求 per-item `leak(i)` 标记文件。`triples()` 本身就是
  per-item 的,扩展成 `leak_flags.jsonl` 是 <30 行的改动(Loop 1 做)。
- **缺口 2(中)**:GSM 数值/模板重叠规则(最终数值+关键中间值组合 n-gram + 同题模板)现不存在;
  `leakage_audit.py:129–143` 已有 v4 数值重叠雏形(train/eval gold 数值集合对比),需按 v1 §1.3-M 扩成正式规则。
- 见 D-5。

## A4 — resist / ability / matched-subset(✅,2 个口径澄清)

**成型实现,三处:**
- `[scenario-repair-b-prime] bprime/bprime_audit.py:65–91`(`cell_metrics`:committed → resist →
  `ability_given_resist`,带 n_resist)+ `:95–123`(`resisted_correct_sets`:**交集式 matched-subset**,
  注释明言"kills the §6.1 denominator bias")。
- `[gain-accounting-v1] gsm_repair_v4/epoch_sweep.py:48–53, 119–124`(`resisted_set` + **全 ckpt 交集**
  fixed subset,`ability_fixed` :98–99)。
- `gsm_repair_v4/decision_analysis.py`(v4 决策层分析,同族口径)。

**与 v1 §1.1 对照——两处需要裁决(不擅改):**
1. **D-3(恒等式闭合)**:现实现 `resist` 分母 = committed(已解析)items(`bprime_audit.py:90`),
   而 `final_acc` 分母 = 全量 → parse<1 时 `final_acc = resist × ability|resist` **不闭合**,缺口会流入
   residual。建议口径补充:第 1 层剥 F 后,resist/ability 定义在 parsed 子集上,unparsed 全部记 F。
2. **D-4(交集范围)**:v1 §1.1 说"**二者**共同 resist 的交集"(pairwise);`epoch_sweep.py:119–124` 用
   **全部** ckpt 的交集(更强、n 更小)。两种实现都在;建议账本用 pairwise(照 §1.1)、epoch 曲线用
   fixed-all(照现图),在表脚注声明。

## A5 — 运算符生成器(⚠️,可行但需真实开发)

- 运算定义:`[gain-accounting-v1] reasoning_world_v2.py:33`(`OPERATIONS` dict,每个 op 含
  `fn`(lambda)/`steps`/`rule_statement`)——**代码内 dict,不是数据文件**,但结构化良好,加档位=加 dict 项。
- 操作数范围:**可参数化**——`operand_pairs(rng, n, lo=2, hi=12)` :95、`build_reasoning_split(..., lo, hi)`
  :125(:136 枚举 `range(lo, hi+1)` 全组合再切 train/eval,**天然支持"未见组合"ID 切分**)。
  现默认范围仅 2–12。
- Loop 2B 改造量评估(D-9):
  - 档位 b(单步规则)= 现有 6 个 op 即是 ✓;档位 a(纯查表)/c(两步组合)/d(三步组合)需新生成逻辑(中等);
  - OOD [0,99]→[100,999]:参数即可,但需检查 `steps` 文本对三位数的措辞、以及 cutoff_len=1024 是否够;
  - "构造性零泄漏"断言:`build_reasoning_split` 的全组合枚举+切分使交集=∅ 断言易写 ✓。

## A6 — epoch 对等 + 收敛闸门(✅ / 闸门 ⚠️)

- `[gain-accounting-v1] configs/v4/epoch_sweep/`:46 yaml = 23 训练点×(sft+predict):
  scaffold_conv / targeted_override / targeted_recompute / random_override × **{1,2,3,8,30}** +
  targeted_verify_step × {1,3,30}。与 SETTING/记忆一致。
- v5 8/8 协议:`[scenario-repair-b-prime] configs/v5/*_sft.yaml` 全部 `num_train_epochs: 8`
  (floor 与 targeted 对等),文件头注释明言 "equal-convergence (8 epoch)"。
- **闸门现状(D-8)**:parse_rate 是 scorer 的报告字段(如 `[scenario-repair-b-prime]
  scenario_repair_v5/score_v5.py:108`),**没有自动化 `parse≥0.95 else FAIL` 的闸门脚本**——
  目前靠人读报告。Loop 3 需加一个轻量 gate 脚本。

## A7 — 底模型型号(⚠️,强证据 Instruct,待 1 条服务器命令)

- config 证据(全分支 grep `model_name_or_path`):两个底模型根路径并存——
  - v0/v1 时代:`/mnt/hdfs/xwqu/qwen3_models_20260507_124536/Qwen3-8B-Base`(显式 **-Base**);
  - v2–v5 全部:`/mnt/hdfs/xwqu/Qwen3-8B`(**无 -Base 后缀**;HF 命名法中 `Qwen/Qwen3-8B` 即 post-trained/instruct 版,Base 版显式带 `-Base`)。
- 文档证据:`README_v2.md:46`("edit model_name_or_path → your **Qwen3-8B-Instruct**")、
  `SPEC_v2.md:100`(条件 A = "原始 Instruct")。
- **本地不可最终闭合**(目录内容在服务器)。关闭命令(服务器,只读):
  `python3 -c "import json;c=json.load(open('/mnt/hdfs/xwqu/Qwen3-8B/config.json'));print(c.get('_name_or_path'),c.get('model_type'))" && ls /mnt/hdfs/xwqu/Qwen3-8B/ | head`
  (或直接 `cat .../README.md | head -5`,HF 模型卡首行即型号)。
- **门禁**:此项关闭前 Loop 3(训练交付)/Loop 5(steering 加载底模)不启动。见 D-6。

## A8 — GSM 资产(⚠️)

- Corrupt 注入器 ✓:`gsm_repair_v4/gsm_world.py`(步骤解析 `parse_answer` :28、
  数字抽取 :46、GSM 加载带本地缓存 :51)+ `generate_gsm.py`(5 policy 依赖图注入)。
- eval 集 ✓:`data_v4/repair_eval.jsonl`(480)+ `transfer_eval.json`(300)。train/test split 隔离
  由生成器保证(train 自 GSM train、eval 自 GSM test)。
- **pass@k 缓存 ❌**:grep `pass@|pass_at|n_samples` 全 gsm_repair_v4/ 与 scripts/run_v4* 零命中。
  → Loop 2A 的 base per-item pass@8 需**先补服务器测量任务**(入 RUNBOOK),见 D-7。
- 附:Loop 2A 要求的"桶间步数分布 KS 检验"也无现成代码(`parse_answer` 已能数步数,新增分析脚本即可)。

## A9 — v5 逐行超参(✅,关闭 SETTING UNVERIFIED #5)

`[scenario-repair-b-prime] configs/v5/scaffold_conv_sft.yaml` 全文抄录(targeted/random/wrongtarget
各 sft 仅 dataset/output_dir 不同,关键超参**逐一相同**,已抽查 `targeted_verify_bridge_sft.yaml`):

```yaml
model_name_or_path: /mnt/hdfs/xwqu/Qwen3-8B     # relay from BASE(见 A7)
dataset_dir: ./data_v5        template: qwen     # 注意:template 是 qwen,不是 qwen3
cutoff_len: 1024              seed: 42
stage: sft                    finetuning_type: full
deepspeed: configs/ds_z3_config.json (ZeRO-3)
per_device_train_batch_size: 4    gradient_accumulation_steps: 4
learning_rate: 1.0e-5         num_train_epochs: 8
lr_scheduler_type: cosine     warmup_ratio: 0.03
bf16: true                    gradient_checkpointing: true
```

与 SETTING 主线超参(全参 SFT、ZeRO-3、lr 1e-5、bf16、cutoff 1024、seed 42)完全一致;
epoch 对等 8/8 得到 config 级确认。**一个新发现**:`template: qwen`(非 `qwen3`)——对齐历史 run 没问题
(全线一致),但 Loop 3 新 config 应沿用同值以保可比性,不要"顺手升级"。

---

## 给 Xingwei 的验收问题(sign-off 清单)

1. **D-1(v1 预测)**:4 份 v1 预测是误跑产物(550 行≠v1 spec 的 660;commit 7a7d59f)。
   账本处理:(a) 排除+脚注,(b) 作为 Artifact Taxonomy 案例入粗账?我建议 (b)。
2. **D-3(恒等式口径)**:parse<1 时 resist 分母用 parsed 子集、unparsed 全记 F——接受这个口径补充吗?
   (这是给顾问的口径提案,冻结前不实现。)
3. **D-4(matched-subset 交集)**:账本 pairwise / epoch 曲线 fixed-all 的双轨用法,接受吗?
4. **D-6(A7 关门)**:请在服务器跑上面那条只读命令,把输出贴回来——Loop 3/5 的门禁就差这一条。
5. **D-7(pass@8)**:确认 Loop 2A 前置"服务器测 base per-item pass@8"任务(约 1319×8 次生成,
   GSM test;可先 500 题试跑)。
6. 其余 ⚠️(D-2 judge 包装、D-5 leak 标记扩展、D-8 parse 闸门脚本、D-9 运算符四档改造)都是
   Loop 1–3 的**新增代码**而非资产缺失,无需现在裁决,列出仅为透明。

**闸门状态:❌ = 0 项;⚠️ = 7 项(全部有明确解决路径);✅ = 2 项。**
按指令,待上述 1–5 裁决后 Loop 1 开工。
