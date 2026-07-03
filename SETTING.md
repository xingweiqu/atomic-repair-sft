# Atomic-Repair — 实验 SETTING(可追溯到代码)

> 用途:论文 method 底稿 + 组会/答辩讲 setting 的依据。
> 铁律:每项标来源（`[branch] path:line` 或 commit）。读不到的标 **UNVERIFIED**，不猜。
> 仓库：`/Users/bytedance/atomic-repair-sft`。来源分支：v3 → `scenario-repair-v3-targeted-operators`（码/配置同样存在于 `scenario-repair-v4`）；v3.1 收敛-floor 配置 → `scenario-repair-b-prime`；v4 → `scenario-repair-v4`（HEAD 6245433）；v5 → `scenario-repair-b-prime`（HEAD abb19da）。审计文档 → `scenario-repair-b-prime:bprime/`。
> 本文档为只读梳理的产物；未改动任何代码/配置/数据文件。

---

## 0. 三实验一句话定位

| 实验 | 域 | base 能力起点 | 主问题 |
|---|---|---|---|
| **v3** | 合成（编造关系族 + 编造运算） | base 几乎全不会 | 对症下药（targeted operator induction）是否选择性成立 |
| **v4** | GSM8K（真实算术） | base 已会算术 | v3 结论能否迁移到真实域 |
| **v5** | 反事实两跳（leak-proof） | base 秒会（读 context） | 在 0% 泄漏的干净域复核选择性 |

四个高优先点的总览（详见 D 节）：

| 点 | v3 | v4 | v5 |
|---|---|---|---|
| 训练充分度 | scaffold_only 3ep 欠拟合(keep 0.22)；conv=30ep | scaffold_only 3ep loss 2.53 欠拟合；conv=30ep parse 100% | 全 8ep，parse 100% |
| oracle 泄漏 | **79.4%**（重） | **0%**（held-out test） | **0%**（gate 强制） |
| ability\|resist 分母 | 已做 matched-subset（bprime_audit） | 已做 matched-subset（bprime_audit / epoch_sweep） | final-acc 触顶，分母问题不适用 |
| **epoch 对等** | conv-floor 30ep vs targeted 3ep → **不对等** | conv-floor 30ep vs targeted 3ep → **不对等** | 全 8ep → **对等 ✓** |

---

# 实验 v3（合成域）

## A. 数据
1. **底层 item 来源**：编造关系族 + 编造运算的合成世界。生成器 `[v4] scenario_repair_v3/generate_v3.py`：关系族/实体池来自 `generate_repair_data`(v0, `generate_v3.py:26`)，编造运算/步骤来自 `reasoning_world_v2`(`:27`)，场景表层措辞来自 `scenario_templates`(`:30`)+ `scenario_api`(`:32`)。世界规模实测：**unique triples 341 · heads 66 · relations 12 · tails 173**（`[b-prime] bprime/leakage_audit.md` §1c）。
2. **失败注入器（9-cell → operator）+ 样例**：注入逻辑由 7 个 policy 的 `desc` 定义，`[v4] scenario_repair_v3/policies.py:25–56`：
   - `verify_bridge`：植入错误 bridge 实体（policies.py:38 "A planted bridge entity is wrong; verify the true bridge, then chain"）。
   - `verify_step`：植入错误中间步结果（policies.py:43 "A planted intermediate result is wrong; recompute the step"）。
   - `override_wrong_claim`：植入错误最终断言（policies.py:32）。
   - `use_provided_support`（policies.py:51–54 "题面已给支撑事实，直接用，别反复怀疑"，← K-Aug/H-Aug）。
   - `recompute`（policies.py:45–50 "从已知事实/规则重新推导：跑规则 / 换措辞回忆同一事实"，← K-Abl/R-Aug/R-Abl）。
   - `retrieve_or_abstain`（policies.py:56–61 "题面缺作答必需锚点 → 弃答/要澄清"，← 新增 cell U-Abl, policies.py:93）。
   - `keep_answer`（policies.py:25–28，← Clean/K-Cor-True/H-Cor-True，over-repair 对照）。
   - **扰动措辞来源（已实读，非 forms）**：注入内联在 `generate_v3.py`（如 `:146` "Someone got an intermediate value of {wmid}…"=verify_step、`:205` "the answer is {wrong}"、`:208` "The claim '{wrong}' contradicts…"=override）；claim 引入语在 `claim_phrasings.py`（`CLAIM_INTROS` train/eval 不交叠 ≥8 条，真/假 claim 共用以破 marker shortcut）；运算/步骤来自 `reasoning_world_v2`。
   - **真实样例（`data_v3/repair_eval.jsonl`，同一实体集 Maria Voss / Silver River / Lydorian）**：
     | policy(cell) | 题面注入 | tentative | planted_wrong | gold |
     |---|---|---|---|---|
     | use_provided_support(K-Aug) | "nationality of Maria Voss?" | Solenian | — | Lydorian |
     | recompute(K-Abl) | 同问、换问法 | Brendaran | — | Lydorian |
     | override_wrong_claim(K-Cor) | "Some notes say the answer is Hesperinian." | Hesperinian | Hesperinian | Lydorian |
     | verify_step(R-Cor) | "Someone got an intermediate value of 14 here. splisk of 2 and 10" | 73 | 73 | 70 |
     | verify_bridge(H-Cor) | "Some sources say Silver River was written by Sasha Korbenburg." | Quintarian | Quintarian | Lydorian |
     | retrieve_or_abstain(U-Abl) | "I saw an artwork somewhere. What country is the artist from?"(无锚点) | — | — | null |
     | keep_answer(Clean) | 干净题 tentative 已对 | Lydorian | — | Lydorian |
3. **operator 映射**：9 失败 cell → 7 policy，`CELL_TO_POLICY`，`[v4] scenario_repair_v3/policies.py:83+`（如 `K-Aug → use_provided_support`）。`OPERATOR_POLICIES = 非 keep 的 6 个`（policies.py:67）。期望 `update_decision`：keep_answer→keep；retrieve_or_abstain→retrieve_or_abstain；其余→update。
4. **规模**：train **2640** / eval **720** items（`[b-prime] bprime/leakage_audit.md` §1c）。**逐 policy 条数：UNVERIFIED**（未读 dataset 分布）。
5. **★ train/eval 隔离**：
   - 措辞层：exact problem match eval∈train **0/720 (0%)**；entity-masked TEMPLATE match 高（同骨架不同实体，by design）（`leakage_audit.md` §1a）。
   - **ORACLE（三元组）层：exact (h,r,t) 重叠 695/875 = 79.4%**；head 100%、(head,rel) 100%、tail 97.1%（`leakage_audit.md` §1b）。
   - **后果**：小世界(341 triples) + 30ep 全参 → 收敛 floor 可“默写”~79% eval 答案 ⇒ **v3 floor ability=1.00 判定为 PARTLY-TO-LARGELY 记忆**，v3 ability 结论**降级为 cautionary**，干净 ability 证据只在 v4（`leakage_audit.md` §5）。
6. **★ shortcut 审计（TF-IDF/BoW 预测 update_decision）**：`[v4] scenario_repair_v3/validate_v3.py` 中**未发现** BoW/TF-IDF shortcut gate（grep 无命中）。⇒ **v3 的 masked balanced-acc shortcut gate：UNVERIFIED / 疑未运行**（BoW gate 是 v4/v5 才加入，见各自 A6）。v3 的泄漏由 §5 的 oracle 审计覆盖。
7. **输出 schema / format scaffold**：actionized JSON `{update_decision, update_policy, repair_trace, final_answer}`（沿用 v2.1，`evaluate_v3.py` 解析）。scaffold 数据集 `v3_scaffold_only_train`（`format_scaffold_train.json`）；**条数/是否跨集相同：UNVERIFIED**。

## B. 训练
8. **框架**：LLaMA-Factory，**full-param SFT**，DeepSpeed **ZeRO-3**（`[v4] configs/ds_z3_config.json:11 "stage":3`，无 offload）。
9. **底模型**：relay 自 v2 inject ckpt `/mnt/hdfs/xwqu/atomic-repair-sft-v2/output_v2/inject`（`[v4] configs/v3/*_sft.yaml:2`）。该 inject = base + 50ep 事实注入（`[v4] configs/v2/inject_sft.yaml:16 num_train_epochs:50`）；inject 的 base = `/mnt/hdfs/xwqu/Qwen3-8B` = **Qwen/Qwen3-8B(Instruct/post-trained)**——已验证:服务器 `head -5 /mnt/hdfs/xwqu/Qwen3-8B/README.md` 模型卡 `license_link: huggingface.co/Qwen/Qwen3-8B`(2026-07-03,qc/DISCREPANCIES.md D-6 CLOSED)。措辞按 LOOP1_RULINGS:论文统一称 **pre-repair model**。
10. **超参**：见 B 节末统一对照表。v3 全部 `num_train_epochs:3`（`configs/v3/` 27 个 SFT 配置 uniq 均为 3）。
11. **★ 训练充分度**：`scaffold_only` 3ep = **欠拟合**（keep-cell acc 0.22、format-collapse），故新增 **`scaffold_conv` 30ep** 收敛 floor（`[b-prime] configs/v3_1/scaffold_conv_sft.yaml:1–3, :18 num_train_epochs:30`）。注意：comparison_v3 的 Exp2 矩阵 floor = **Fact-only**；bprime_audit 的三层表 floor = **scaffold_conv(30ep)**。
12. **训练分支清单**（`configs/v3/` + `configs/v3_1/`，relay 自 output_v2/inject）：`factonly`、`cot`、`actionized_full`(`v3_actionized_train`)、`scaffold_only`(3ep)、`scaffold_conv`(30ep, in v3_1)、`targeted_<op>`×6、`random_<op>`×6、`wrongtarget_<op>`×6、`cumulative_M1–M6`。每分支 dataset 名见各 yaml `dataset:` 字段；ckpt 路径见各 yaml `output_dir`（**逐分支 output_dir 全路径未逐一抄录：UNVERIFIED**）。

## C. 评测
13. **预测/解析**：`[v4] scenario_repair_v3/evaluate_v3.py`。JSON 先 `json.loads`，失败则正则提花括号兜底（evaluate_v3.py:34–42）；final 取 `final_answer` 字段或 “final answer:” 行兜底（:51–55）。**max_new_tokens：UNVERIFIED**（未读 v3 predict yaml）。
14. **指标**：见 C 节末统一定义。
15. **★ ability|resist 分母**：原 `evaluate_v3.py`/`decision_analysis` 的 `arith_given_ok` 分母 = 各 run 自己 resist 的子集 → **跨 run 不可横比**（`[b-prime] bprime/bprime_audit.md` 抬头明确声明）。**已做 matched-subset**（common resisted items）：override 1.00/0.93/1.00 (n=43)、verify_bridge 0.91/0.77/1.00 (n=22)、verify_step 0.92/0.93/1.00 (n=60)、recompute 1.00/1.00/1.00 (n=170)（`bprime_audit.md` “v3: matched-subset ability”）。结论：targeted≈floor≈full ⇒ 不注入 ability。
16. **abstain 判定（勘误）**：原 v3 把“parser 找不到 final_answer”记为 abstain，但 Fact-only 输出裸答案串无 JSON → 被误判 abstain=100%；实际 **60/60 全在猜具体答案、0 真弃答**。已修：`is_abstain_strict` 把裸输出计为 ANSWERED，仅显式 null / `update_decision==retrieve_or_abstain` 计 abstain。Fact-only abstain 100%→**0%**，overall 49.7%→**39.7%**（`[v4] data_v3/ERRATUM_abstain_judge.md`）。

---

# 实验 v4（GSM8K 真实域）

## A. 数据
1. **底层 item 来源**：GSM8K。**train 用 train split，eval 用 test split**（`[b-prime] bprime/leakage_audit.md` §4：train∩eval source_id 重叠 **0**）。生成器 `[v4] gsm_repair_v4/generate_gsm.py`（行级注入逻辑 UNVERIFIED，未逐行读）。
2. **失败注入器（G-cell）+ 真实样例**（`failure_type` 见 `data_v4/repair_eval.jsonl`，6 类各 80，keep 类合 160）：
   - **G-Step → verify_step**：题面植入错误中间步。真实样例 `G-Step_eval_000000 / src gsm_test_01150`：“…someone got an intermediate value of **14** for the step '30−24'.” 真值 6；tentative=15；gold=**21**（30−24=6, 6+15=21）。
   - **G-Claim → override_wrong_claim**：植入错误最终断言（resist=final≠planted）。
   - **G-Recompute → recompute**；**G-Clean → keep_answer**；**G-Claim-True → keep_answer**（断言为真，应保留）；**G-Abstain → retrieve_or_abstain**（删一跳→无解，final null）。
3. **operator 映射**：G-Step→verify_step、G-Claim→override_wrong_claim、G-Recompute→recompute、G-Clean/G-Claim-True→keep_answer、G-Abstain→retrieve_or_abstain（`repair_eval.jsonl` 的 `policy`/`update_decision` 字段实证）。
4. **规模**：eval **480**（逐 policy：verify_step 80 / override 80 / recompute 80 / retrieve_or_abstain 80 / keep_answer 160）。train ≈ **15000**（`actionized_full_train.json` 15001 行）。逐 targeted/random 训练集条数：**UNVERIFIED**。
5. **★ train/eval 隔离**：source split 隔离（train=GSM-train, eval=GSM-test），source_id 重叠 **0**、exact problem 重叠 **0/480**（`leakage_audit.md` §4）⇒ eval 答案不可默写。**干净 ability 证据仅在 v4**。
6. **★ shortcut 审计**：BoW/TF-IDF 预测 update_decision，gate **balanced-acc < 0.65**（`[v4] gsm_repair_v4/validate_gsm.py:11–12, :40–50, :110–114`，用 `TfidfVectorizer` + `balanced_accuracy_score`）。**实测 0.507 PASS（<0.65）**（Claim 家族/实体掩码/keep-vs-update gate；`sanity_v4.json` status PASS）（`[v4] data_v4/REPORT_v4_review.md:61`）。
7. **输出 schema**：同 actionized JSON。GSM 域无知识注入（算术=知识，relay from BASE，见 B9）。`v4_scaffold_only_train`（`format_scaffold_train.json` 1001 行）。

## B. 训练
8. 同 v3：LLaMA-Factory full SFT + ZeRO-3。
9. **底模型**：`/mnt/hdfs/xwqu/Qwen3-8B`（`[v4] configs/v4/*_sft.yaml:2/:5`）。配置注释标 “Qwen3-8B-Instruct … relay from BASE”（`configs/v4/targeted_override_wrong_claim_sft.yaml:1`）。**GSM 域不做知识注入**，直接从 base relay。
10. 超参见统一表。**关键差异：`scaffold_conv` num_train_epochs=30（`configs/v4/scaffold_conv_sft.yaml:19`），其余全 =3**（`configs/v4/{targeted,random,wrongtarget,actionized_full}_sft.yaml:16`）。
11. **★ 训练充分度**：`scaffold_only` 3ep ≈37 步 train_loss **2.53**、parse **0.68–0.80** = 欠拟合，会**系统性反转结论符号**，已弃用为基线；改用 `scaffold_conv` 30ep（parse **100%**）做 floor（`configs/v4/scaffold_conv_sft.yaml:1–4` 注释 + `data_v4/results/comparison_v4.md` 结论段）。**这是 v4 round-1“结论翻转”的根因，已显式处理**。
12. **训练分支清单**：`diagnosis_base`(无修复训练)、`scaffold_only`(3ep, 弃用)、`scaffold_conv`(30ep, FLOOR)、`actionized_full`(`v4_actionized_train`)、`targeted_<op>`×4(verify_step/override/recompute/retrieve_or_abstain)、`random_<op>`×4、`wrongtarget_<op>`×4，输出 `…/output/<name>`（`configs/v4/*_sft.yaml output_dir`）。**epoch-sweep**（封板实验）：`configs/v4/epoch_sweep/`，23 训练点 ×{1,2,3,8,30}（`gsm_repair_v4/gen_epoch_sweep.py`），**服务器待跑**。

## C. 评测
13. **预测/解析**：`[v4] gsm_repair_v4/evaluate_gsm.py`（复用 v3 parse/abstain 判定，evaluate_gsm.py:26）；**max_new_tokens 384**、`do_sample:false`、`temperature:0`（`configs/v4/targeted_override_wrong_claim_predict.yaml`）。final 数值规整 `numkey`（strip $/逗号、18.0→18，evaluate_gsm.py:33–44）。transfer 取最后一个 “final answer is N”（:97–107）。
14. **指标**：见统一定义。`decision_analysis.py` 给 parse/committed/resist_wrong/arith_given_ok/final_acc（`gsm_repair_v4/decision_analysis.py:36–62`）。
15. **★ ability|resist 分母**：`arith_given_ok` 分母=resist 子集，跨 run 不同（decision_analysis.py 注释 §6.1）。**已做 matched-subset**：verify_step floor/targeted/full = 0.38/0.40/0.56 (n_common=78)（`[b-prime] bprime/bprime_audit.md` “v4: matched-subset ability”）。`gsm_repair_v4/epoch_sweep.py` 进一步用“被所有 ckpt 都 resist 的固定子集”算 ability|resist（常数分母）。
16. **abstain**：strict（同 v3 修正后定义）。GSM 域内基本无弃答漂移。

---

# 实验 v5（反事实两跳，leak-proof）

## A. 数据
1. **底层 item 来源**：反事实两跳 schema，全编造 nonsense 值（必须读 context，不能默写）。`[b-prime] scenario_repair_v5/generate_v5.py:1–15`、`v5_world.py`。leak-proofing **内建于生成**（train/eval 共享 coinage `used` 集，head/bridge/tail 全局唯一 → eval 三元组不进 train；tail ~50/50 真/假值平衡）（generate_v5.py:3–7）。
2. **失败注入器（6 cell）+ 样例**（`generate_v5.py:9–14`）：
   - `H-Sup → use_provided_support`：给全 context，组合两跳（无 planted wrong）。
   - `H-Bridge → verify_bridge`：植错 bridge + 干扰链（resist=final≠wrong tail）。
   - `H-Cor → override_wrong_claim`：植错最终答案。
   - `H-Cor-True → keep_answer`（断言为真，含 50/50 TRUE）；`H-Clean → keep_answer`；`H-Abl → retrieve_or_abstain`（删一跳→无解，final null）。
   - 真实样例（`data_v5/repair_eval.jsonl` H-Sup）：facts “Snorxzlunr is located in Morngsnarn. / Morngsnarn officially uses Glesorl.” Q “What currency does the province containing Snorxzlunr use?” gold=**Glesorl**。
3. **operator 映射**：`CELL_TO_POLICY`，`[b-prime] scenario_repair_v5/generate_v5.py:26–33`；`decision_of`（:37–42）：keep_answer→keep、retrieve_or_abstain→retrieve_or_abstain、其余→update。
4. **规模**：train **8000** / eval **1600**；unique_triples_train 16000、eval_triples 3200（`[b-prime] data_v5/gate_v5.json`）。eval 逐 policy：use_provided_support 267 / override_wrong_claim 267 / verify_bridge 267 / retrieve_or_abstain 266 / keep_answer 533（实测 repair_eval.jsonl）。
5. **★ train/eval 隔离**：**triple_overlap_eval_in_train = 0**（gate_v5.json）。措辞 + oracle 双层均隔离（生成期组合级 holdout）。entity_balance false_share median 0.292。
6. **★ shortcut 审计**：masked balanced-acc **0.4733**、raw 0.4385，gate **<0.65 PASS=true**（`[b-prime] data_v5/gate_v5.json` "shortcut"）；`scenario_repair_v5/gate_v5.py`。**HARD GATE PASS**。
7. **输出 schema**：同 actionized JSON。`v5_scaffold_only_train`（scaffold）。

## B. 训练
8. 同前：full SFT + ZeRO-3。
9. **底模型**：`/mnt/hdfs/xwqu/Qwen3-8B`，relay from BASE（`[b-prime] configs/v5/*_sft.yaml:2`）。
10. 超参见统一表。
11. **★ 训练充分度**：**全部分支 num_train_epochs=8**（含 scaffold_conv，`[b-prime] configs/v5/{scaffold_conv,targeted_*,random_*,actionized_full}_sft.yaml:16`），parse 100%、floor 触顶 100%（`data_v5/results/comparison_v5.md`）。
12. **训练分支清单**：`diagnosis_base`、`scaffold_conv`(8ep, FLOOR)、`actionized_full`、`targeted_<op>`×4(use_provided_support/verify_bridge/override_wrong_claim/retrieve_or_abstain)、`random_<op>`×4、`wrongtarget_<op>`×4（`configs/v5/`）。15 组预测已跑回（`data_v5/predict_outputs/`，各 1600 行）。

## C. 评测
13. **预测/解析**：`[b-prime] scenario_repair_v5/score_v5.py`（parse 同前；abstain strict）。**max_new_tokens：UNVERIFIED**（未读 v5 predict yaml）。
14–15. 指标见统一定义。**v5 final-acc 在 floor 即触顶 100%**，ability|resist 分母问题不适用（无 headroom）。
16. abstain strict。

---

## B-10 ★ 超参统一对照表（三实验并排，从 yaml 实读）

| 超参 | v3 | v4 | v5 | 来源 |
|---|---|---|---|---|
| 框架/方式 | LF, full SFT | LF, full SFT | LF, full SFT | `configs/*/*_sft.yaml:finetuning_type:full` |
| DeepSpeed | ZeRO-3 | ZeRO-3 | ZeRO-3 | `configs/ds_z3_config.json:11` |
| 底模型 | relay `output_v2/inject` | `Qwen3-8B`(BASE) | `Qwen3-8B`(BASE) | `configs/v{3,4,5}/*_sft.yaml:2` |
| lr | 1.0e-5 | 1.0e-5 | UNVERIFIED(未抄)→预期 1.0e-5 | `configs/v{3,4}/*_sft.yaml:14/:18` |
| batch / grad-accum | 4 / 4 | 4 / 4 | UNVERIFIED | v3/v4 `*_sft.yaml:12-13/:16-17` |
| scheduler / warmup | cosine / 0.03 | cosine / 0.03 | UNVERIFIED | v4 `scaffold_conv_sft.yaml:20-21` |
| cutoff_len | 1024 | 1024 | UNVERIFIED | `*_sft.yaml:6/:9` |
| bf16 | true | true | UNVERIFIED | `*_sft.yaml` |
| seed | 42 | 42 | UNVERIFIED | `*_sft.yaml:12/:15` |
| **epochs (floor)** | **30**(conv) / 3(only) | **30**(conv) / 3(only) | **8** | v3.1/v4 `scaffold_conv_sft.yaml`; v5 `:16` |
| **epochs (targeted)** | **3** | **3** | **8** | `targeted_*_sft.yaml` |
| **floor↔targeted epoch 对等** | **否(30 vs 3)** | **否(30 vs 3)** | **是(8 vs 8)** | — |

> v5 标 UNVERIFIED 的项是“未逐行抄录”，非缺失；v5 yaml 结构同 v4，需要时可补。

## C-14 ★ 指标定义（公式）

- **final_acc** = (final_answer == gold) 的比例（abstain 题：strict abstain 正确才算对）。`evaluate_v3.py` / `evaluate_gsm.score_repair`。
- **resist_wrong（决策层）** = 在 committed 子集中，final ∉ {tentative, planted_wrong} 的比例。`decision_analysis.py:55-56`。
- **ability|resist（能力层）** = 在 resist 成功子集中 final==gold 的比例（`arith_given_ok`，decision_analysis.py:57-58）。**分母随 run 变 → 不可裸横比**（见各 C15）。matched 版：固定“被所有 ckpt 都 resist 的公共子集”再算。
- **targeted gain** = acc(只训该 operator, 评该 operator cell) − acc(floor, 同 cell)。`compare_v3.py` / `comparison_v4.md`。
- **selectivity** = 对角 gain − 非对角 gain 均值（同行）。`comparison_v4.md` / `score_v5.py`。

---

## D. ★ 控制变量与混杂登记（文档灵魂）

### D-17 变量表（固定 vs 改变）
| | 刻意固定 | 刻意改变 |
|---|---|---|
| 跨三实验 | 输出 schema（actionized JSON）、评分器（同一套 parse/resist 定义）、operator 概念集、full-SFT 工程栈 | **域难度**：v3 编造运算(base 全不会) → v4 真实算术(base 会) → v5 两跳查找(base 秒会) |

### D-18 各对照实验控什么
- **targeted vs random（同量）**：控数据量，变“是否对症” → 测**对症性**（`{targeted,random}_<op>_sft.yaml` 同 dataset 规模）。
- **targeted vs wrongtarget**：控数据量+格式，变“标签对错” → 测**是标签/动作起作用还是格式**。
- **scaffold(floor) vs targeted**：控格式基座，变“加目标 policy 数据” → 测 **targeted 增益**。

### D-19 ★ 已知混杂的诚实登记
| 混杂 | 状态 | 证据 |
|---|---|---|
| (a) floor 欠拟合制造假增益 | **已控**：用 `scaffold_conv`（v3.1/v4 30ep, v5 8ep）替代欠拟合 `scaffold_only` | `configs/v3_1|v4/scaffold_conv_sft.yaml`；`comparison_v4.md` 翻转说明 |
| (b) 小世界 oracle 泄漏(v3) | **已审计 + 已降级**：79.4% 三元组泄漏 → v3 ability 结论降为 cautionary，干净证据仅 v4 | `bprime/leakage_audit.md` §1b,§5 |
| (c) ability\|resist 分母偏差 | **已控**：bprime_audit 做了 matched-subset（公共 resist 子集）；epoch_sweep 用固定 resist-by-all 子集 | `bprime/bprime_audit.md`；`gsm_repair_v4/epoch_sweep.py` |
| (d) **epoch 不对等** | **部分未控**：v3/v4 的 conv-floor=30ep vs targeted=3ep → “gain over floor” 混入 epoch 差异；**v5 已对等(8/8)**；v4 **epoch-sweep** 专门拆解此变量但**服务器待跑** | v3.1/v4 `scaffold_conv_sft.yaml:18/:19`=30 vs `targeted_*_sft.yaml`=3；v5 全 8；`configs/v4/epoch_sweep/` |
| (e) 域难度天花板(v4 算术饱和 / v5 触顶) | **作为结论保留**（非 bug）：v4 ability flat≈0.35 受 base 上限压制；v5 floor 触顶 100% → selectivity 不可测 | `comparison_v4.md`；`comparison_v5.md` |

---

## E. 可追溯性 & ★ 待人工确认清单（UNVERIFIED）

已逐项标注 `[branch] path:line`。以下为**读不到/未抄录、需人工确认**项：

1. **v3 逐 policy train/eval 条数**（仅有总数 2640/720）。
2. **v3 是否运行过 BoW/TF-IDF shortcut gate**：`validate_v3.py` 未见；疑为 v4/v5 才加。
3. **v2 inject 的 base 模型全路径与该 ckpt 是否即 Qwen3-8B-Instruct**（仅确认 relay 目标路径 + 50ep）。
4. **v3/v5 predict 的 max_new_tokens / do_sample / temperature**（仅 v4=384/false/0 已确认）。
5. **v5 完整超参逐行**（lr/batch/grad-accum/scheduler/warmup/cutoff/bf16/seed）——结构同 v4，未逐行抄。
6. **各分支 ckpt output_dir 全路径**未逐一抄录。
7. **失败注入器行级代码**：v3 **已实读**（generate_v3.py:146/205/208 + claim_phrasings.py + reasoning_world_v2，见 v3-A2）；v4/v5 仍仅从 policy `desc`/数据样例/生成器 docstring 实证，**generate_gsm.py / generate_v5.py 逐 cell 注入分支未逐行核对**。
8. **v4 各 targeted/random/wrongtarget 训练集条数**（仅 actionized_full≈15000、eval 480 已确认）。
9. **comparison_v3.md Exp2 的 floor=Fact-only 的 factonly 配置 epochs**（疑 3ep，未单独核）。

> 需要我补齐以上任意项，指出编号即可——我按同样“读出处+标行号”的方式回填。
