# CC_INSTRUCTION_C21 — 五份 Contract + 三道 Gate(2026-08-04,逐字存档)

> 核心要求:**训练、评测、分析、跑批和验收都必须写到 CC 不需要自行做研究判断的程度。**
> 执行响应:prescription/contracts/ 五份 contract + PLAN_lawv1 v2.1 Gate 执行顺序。

---

对。**训练、评测、分析、跑批和验收都必须写到 CC 不需要自行做研究判断的程度。**

现在这份 PLAN 已经写了大方向,例如 Qwen3-8B、full FT、DeepSpeed ZeRO-3、总量2,000条、2 epochs、默认 seed 42,以及每个 checkpoint 要跑七条件、retention 和连续探针;但这仍然只是"实验框架",不是完整的可执行协议。最少要把它补成下面五份 contract。

# 1. 数据 Contract

必须明确每一条训练数据和评测数据从哪里来、如何生成、如何隔离。

## 数据集选择

每个域都要写:

| 项目 | 必须明确 |
|---|---|
| Training source | 用哪个数据集、哪个 split |
| Main evaluation | 用哪个数据集、哪个 split |
| External evaluation | 用哪个完全独立的数据源 |
| Split unit | 按题、题族、文档还是实体隔离 |
| Version | 数据集版本与下载 hash |
| License | 是否允许生成衍生训练数据 |
| Usable count | 过滤后到底剩多少 |

现在 Reasoning 只是暂定 GSM8K 和 SVAMP,Knowledge 暂定 2Wiki 和 StrategyQA,IF 甚至还没有确定,这不能直接进入正式生成。

## 数据隔离

必须写死:同一个 `family_id` 不能跨 train/dev/test;同一道底题的 paraphrase、candidate、insufficient、format 版本必须在同一 split;正式训练与评测不能使用相同 generator prompt;训练和评测不能共享固定措辞、标签映射和 JSON schema;训练数据、评测数据都要保存 generator version 和 source ID。

## 组件定义

每个 component 不能只写名字,要有具体构造规范。例如 selective revision:correct candidate 和 wrong candidate 比例;wrong candidate 如何生成;错误类型有哪些;输出中是否保留推理;correct candidate 是否必须明确 `KEEP`;自动验证规则;人工抽检规则;重复率上限;与 evaluation 的 overlap 上限。

## Dose 数据池

不同剂量必须使用嵌套数据:D_30 ⊂ D_60 ⊂ D_120 ⊂ … ⊂ D_2000,而不是每个剂量重新随机抽一批。否则曲线同时混入了:剂量变化;样本内容变化;难度变化。

# 2. 训练 Contract

目前的"沿 P2a configs"不够。CC 必须拿到唯一且冻结的训练配置。

## 模型和输入格式

必须明确:精确 checkpoint 路径和 revision/hash;tokenizer revision;chat template;system message;thinking mode 是否关闭;BOS/EOS 处理;assistant loss mask;是否训练 reasoning token;prompt token 是否全部 mask;packing 是否开启;truncation 从哪一侧发生。尤其不能再次出现:训练没有使用正确 ChatML,但评测使用了另一套模板。

## 优化器配置

必须把以下内容写成确定数值:

```yaml
model: / tokenizer: / chat_template: / max_seq_length: / packing: / precision: /
optimizer: / learning_rate: / weight_decay: / warmup_ratio: / scheduler: /
global_batch_size: / micro_batch_size: / gradient_accumulation: / gradient_clip: /
epochs: / max_steps: / seed: / deepspeed_config: / gradient_checkpointing:
```

"固定 learning rate 和 schedule"不是执行说明,因为 CC 不知道固定成哪一个版本。当前计划只说明了 full FT、ZeRO-3、2 epochs、末位 checkpoint 和 seed 42。

## 训练预算如何固定

这是 law 实验最关键的地方。现在计划固定 N=2000 examples,但不同组件输出长度可能差很多。必须决定主控制量究竟是:examples;assistant target tokens;总 tokens;optimizer steps。

我的建议是:**固定 optimizer steps 和总 assistant target-token exposure;条数作为第二横轴报告。** 至少也必须:replay 与 component 做长度分桶匹配;报告每个 run 的 input tokens、target tokens、updates;不允许所谓同预算 run 实际看到不同数量的 loss tokens。

## Checkpoint 规则

现在文件同时写了"末位 checkpoint"和"评测每个 checkpoint",需要拆清楚:主结果使用哪个 checkpoint;是否保存每个 epoch;是否评测中间 checkpoint;中间 checkpoint 是否只用于 trajectory analysis;是否绝对禁止根据 eval 选 best checkpoint。

建议:主表固定使用 final checkpoint;中间 checkpoint 只能做探索性学习轨迹,不能用于挑选结果。

## Seed 规则

不能看完 seed 42 后,再决定哪些点叫 onset 或 plateau 并补 seed。需要预先固定:placebo 3 seeds;每组件的 mid/high 固定锚点 3 seeds;其余剂量 1 seed;自适应追加点单独标为 adaptive,不和预注册确认混合。

# 3. Evaluation Contract

"跑七条件全套"仍然不够。每个 endpoint 都需要确定的 prompt、decoding、scorer 和异常处理。

## 推理配置

统一冻结:chat_template / system_prompt / thinking_mode: false / temperature: 0 / top_p: 1 / top_k / max_new_tokens / stop_tokens / repetition_penalty / batch_size。同一个模型的所有 run 必须使用相同推理配置。

## 七类条件分别怎么打分

### Original / Paraphrase / Distractor
同时报告:exact/numeric accuracy;宽松 answer extraction accuracy;family-level paired success。

### Wrong candidate
不能只报对错,还应区分:`correct` 得到 gold;`adopt` 采用植入的错误答案;`derail` 输出另一个错误答案;`mute` 未给答案。这是旧实验已经使用过的可解释分解,不能在新计划里丢掉。

### Correct candidate
区分:正确保留;不必要修改但仍得到正确结果;修改为错误结果;拒绝判断。并提前定义"keep"究竟要求:只要最终答案正确;还是必须明确判断候选正确;还是必须输出 `KEEP` action。这些是不同指标。

### Insufficient
必须成对报告 Insufficient-stop 和 False-abstain on answerable items。否则模型全部拒答,也能拿到很高的 insufficient 分数。

### Structured output
至少拆成:semantic correctness;JSON validity;schema compliance;exact contract compliance。不能把"算对但 JSON 坏了"和"JSON 正确但内容错了"混在一起。

## S/R 探针
只在 base 失败子集上运行是对的,但必须冻结 `sr_subset_ids.json`:用 base model 在冻结 evaluation 上产生的失败集合,之后所有 checkpoint 都评同一组题。不能每个 checkpoint 重新筛选。

## 连续指标
必须固定到底用 Hugging Face forward 还是 vLLM prompt logprobs,不能写成"二者之一"(两条实现路径可能有不同 token 对齐和归一化)。需要保存:gold sequence token IDs;token-level logprobs;target-only NLL;target bytes;BPB;action logits;margin;template ID;label permutation ID。

## 模板审计的可执行阈值
至少需要:8个模板变体中至少6个响应方向一致;标签置换前后剂量排序 Spearman ≥ 0.6;多模板平均 margin 与生成正确性的 AUROC ≥ 0.7;模板间标准差不能大于主剂量效应;不通过则 continuous metric 只能做附录诊断。具体阈值可以调整,但必须在 Stage A 结果出现前冻结。

# 4. 分析 Contract

CC 不能训练完后自己决定怎么画曲线。

## 每个 run 必须产生两套 delta
相对 base:Δs_e^base = s_e(component) − s_e(base);相对 matched replay:G_{e,d}(n) = s_e(component,n) − s_e(replay,n)。第二个才是 component-specific effect。

## 曲线拟合
预先规定候选模型:constant/null;linear in log n;saturating;threshold;rise–fall(仅在剂量点足够时使用)。评估必须包括:leave-one-dose-out;interpolation;left extrapolation;right extrapolation;nearest-dose baseline;linear baseline;constant baseline。不能拟合完所有点后只报训练误差。

## 不确定性
至少两层:item-family bootstrap;seed-level variation。不能把七个变体当成七个独立样本,因为它们来自同一道底题。

## Onset 的算法
不能让 CC 看图选择。例如:相对 replay 的预测效应首次超过预注册噪声阈值,且相邻更高剂量方向一致的最小剂量。若没有任何剂量满足,则该组件为 no detected onset within tested range。

## Mixture 的具体定义
`uniform / 按失败频率 / 补最差 / target-optimal` 还是概念名,必须转换成具体数量(如 uniform: evidence 250 / revision 250 / answerability 250 / format 250 / replay 1000),其他 mixture 也必须由确定公式自动生成,而不是人工看结果配。

# 5. 跑批和验收 Contract

CC 最终应该只执行一张冻结的 `RUN_MATRIX.csv`(run_id | model | component | dose | replay | seed | data_hash | config_hash | eval_hash)。

每个 run 必须保存:run_manifest.json / train_config.yaml / data_manifest.json / train_log.jsonl / checkpoint_hash.txt / generation_config.yaml / predictions.jsonl / scores_by_item.jsonl / scores_summary.json / continuous_metrics.parquet / environment.txt / git_commit.txt / DONE。

## 失败处理
必须写清楚:OOM 是调整 batch 后重跑还是作废;loss spike 如何判定;NaN 如何处理;checkpoint 损坏是否允许重跑;重跑是否保留原始记录;是否允许中途修改 learning rate;任何修改是否需要新 run ID。原则:**不静默覆盖,不自动挑最好的一次。**

# CC 的正确执行顺序

## Gate 1:数据和评测原型
CC 先交付:1. Reasoning 数据源决策;2. 每个条件50个 prototype;3. 每个组件200条 prototype;4. 自动 scorer;5. 人工审计报告;6. base model profile;7. 模板审计初测。你确认后才扩产。

## Gate 2:端到端 Smoke Test
只跑三个训练:pure replay;一个低剂量组件;一个高剂量组件。完整走完 build data → train → checkpoint → generation eval → NLL/BPB → score → curve input。确认:loss mask 正确;token 预算正确;scorer 正确;metadata 齐全;运行成本可接受。

## Gate 3:冻结正式实验
CC 提交:数据 hash;training config hash;eval hash;scorer tests;run matrix;GPU-hour 重新估算;预注册 commit。之后才允许启动 Stage A。

## 所以现在对 CC 最准确的要求是

> 不要直接按照当前 PLAN 启动正式训练。先把 Reasoning 域的数据、训练、评测、连续指标、分析规则和逐 run 清单补成可执行 specification;完成50题评测原型、每组件200条训练原型和三个端到端 smoke runs,提交结果供确认。只有数据、配置、scorer 和 run matrix 全部冻结后,才能启动正式剂量网格。

**当前 PLAN 定义了"要做哪些实验",下一步必须让 CC 补的是"每个实验到底用什么数据、执行什么命令、产出什么文件、按什么规则判定成功"。**
