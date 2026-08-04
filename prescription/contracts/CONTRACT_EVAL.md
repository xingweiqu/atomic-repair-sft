# CONTRACT_EVAL — 评测契约(lawv1;2026-08-04 draft;Gate-3 冻结)

## 1. 推理配置([FROZEN];唯一文件 configs/lawv1/generation_config.yaml,所有 run 所有条件同一份)

```yaml
engine: vllm==0.12.0
chat_template: tokenizer 自带(与训练渲染一致;Gate-2 用同一条样例 diff 训练/评测渲染,必须逐 token 相同)
system_prompt: ""            # 与训练一致:不注入
thinking_mode: false         # enable_thinking=False
temperature: 0               # greedy
top_p: 1.0
top_k: -1
max_new_tokens: 512
stop: [模板 EOS]
repetition_penalty: 1.0
batch: vllm 自动连续批;不影响结果
```

## 2. 七条件打分(scorer = prescription/lawv1_score.py;逐条规则,Gate-1 附单测)

所有条件按 family 出 `scores_by_item.jsonl`(含逐题字段)+ `scores_summary.json`。

### 2.1 Original / Paraphrase / Distractor
报三个数:
- `acc_exact`:归一化数值精确匹配(去逗号/单位/空白,float 容差 1e-6);
- `acc_loose`:宽松抽取(最后一个数值 / boxed / "答案是 X" 模式,规则冻结在 scorer);
- `paired_family`:同 family 的 original 与该条件版本**都对**才计 1(family 级)。
主 endpoint = acc_exact;paired_family 供 law 的稳健性检查。

### 2.2 Wrong candidate(四分解,沿旧实验口径,不丢)
- `correct`:终答 == gold;
- `adopt`:终答 == 植入错误值;
- `derail`:终答为其他错误值;
- `mute`:未抽取到答案。
主 endpoint = correct 率;adopt 率单列(= 盲从率,figN 世系口径)。

### 2.3 Correct candidate(四分解 + 三种 keep 定义显式分离)
分解:`keep_correct`(保留且对)/ `changed_still_correct`(不必要修改但对)/ `changed_wrong`(改错)/ `abstain`(拒判)。
三指标:
- **K1(主 endpoint)**:终答正确率 = keep_correct + changed_still_correct;
- K2:显式判断正确率(输出含"候选正确/无误"等判断,判断词表冻结在 scorer);
- K3:KEEP-action 率(仅 action 体裁探针适用)。
K1 进 law;K2/K3 全量报告。

### 2.4 Insufficient(必须成对)
- `insufficient_stop`:insufficient 版拒答且不给猜测值;
- `false_abstain`:同 family sufficient 版被误拒率;
- **主 endpoint = paired_answerability**:同 family(sufficient 答对)∧(insufficient 正确拒答)。
全部拒答刷分被 paired 定义自动排除;三个数都报。

### 2.5 Structured output(四层分离)
- `semantic_correct`:内容(终答)对,不管格式;
- `json_valid`:parser 通过;
- `schema_compliant`:字段名/类型/嵌套全合规;
- `contract_exact`:完全合约(含字段顺序/额外字段禁令);
- **主 endpoint = schema_compliant ∧ semantic_correct**;评测 schema = 未见集 B,同 schema 对照子集单独报(TRAIN_EVAL_SEPARATION §2)。

### 2.6 异常处理(所有条件)
生成为空/超长截断/解析失败 → 计 `mute`/不合规,**不重跑、不剔除**;逐题保留原始输出。

## 3. S/R 探针([FROZEN])

- `prescription/gate1/sr_subset_ids.json`:base model 在冻结主评测上的失败 family 集,**一次生成永久冻结**;
- 全部 ckpt 只评这同一组题;AssistanceRecovery_S/R = s_assisted − s_unassisted(同集合);
- assist 文本 generator B 产出(见 TRAIN_EVAL_SEPARATION §4)。

## 4. 连续指标([FROZEN])

- **实现路径唯一:HuggingFace forward**(bf16,batch=8,与训练同 tokenizer 渲染);vLLM logprobs 禁用于 margin/NLL(对齐/归一化不同源);
- 每探针保存(continuous_metrics.parquet):`gold_token_ids, token_logprobs, target_nll, target_bytes, bpb, action_logits{K,C,I}, margin, template_id, perm_id, family_id`;
- margin 定义:M = logp(gold action 续写) − max(其他 action 续写);多模板报 M̄ 与 Var_k。

## 5. 模板审计定量门槛([PROPOSED] 数值,Stage A 结果出现前必须冻结;通过才准入 law)

| 检验 | 门槛 |
|---|---|
| A 方向一致性 | 8 变体中 ≥6 个剂量响应方向一致 |
| B 标签置换 | 置换前后剂量排序 Spearman ≥ 0.6 |
| D 行为对齐 | 多模板平均 margin 对生成正确性 AUROC ≥ 0.7 |
| 稳定性 | 模板间 SD ≤ 主剂量效应幅度(|G| 峰值) |
| 不通过 | 该 endpoint 连续指标仅入附录诊断,不进 law/optimizer |

## 6. Retention 套卷

三域 Original 合并 + 训练域外基准(域外基准清单 = Knowledge/IF 源定稿时一并冻结,amendment 渠道);主表报 Δretention(硬约束用,UTILITY §1)。
