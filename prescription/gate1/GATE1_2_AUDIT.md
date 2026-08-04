# GATE1_2_AUDIT — gate1-v1.2 整改交付审计(C-23;2026-08-05)

> 对应裁决:工程基本通过 / insufficient·candidate probe·可审计性不通过、dose 未完成
> (qc/INSTRUCTION_C23.md)。扩产与训练继续冻结。上一版审计"36 自测"系笔误(实为39),本版同步勘正。

## 逐条整改对照

| # | 要求 | 落实 |
|---|---|---|
| 1 | insufficient 重做 + 全量人工审核 | ✅ 六重机械闸门(数词泄漏扫描 incl. twenty-five/dozen/twice;**≤2 步代数可恢复检查**(逮住 24−(10−1)=15 类反推);冠词/连字符/比号/定语价格/单位词跳过;语法残渣扫描)+ **27 条全量逐题人工审核**(INSUFFICIENT_AUDIT.md):24 PASS,2 修复("amount dollars"→补 of;定语 "$11 sweater" 判不可安全删),1 黑名单(00403 另一合理解读可绕过)。**终版 26 条全 PASS**,每条含四件套元数据+人工复核 |
| 2 | main pool 解耦 | ✅ 主池 = base 过滤后**随机**(seed=20260812)抽 50,不再被 insufficient 生成器筛选、不再取前 50;insufficient 只在可靠子集(26/50)上评,配对比较用共同子集 |
| 3 | decision contract + full attempt | ✅ 双层探针:wc/cc_light(仅答案)+ wc/cc_attempt(完整貌似合理错误过程,主 stress)+ wc/cc_nl(自然语言,n=20,测泛化);契约输出 DECISION=KEEP/REVISE + FINAL_ANSWER=,分报 decision/final/joint/adopt/contract_followed |
| 4 | 校准 probe 难度 | ✅ 契约下 base:wc_light joint .86 / **wc_attempt joint .80(adopt .06)**——attempt 层确实更难,联合指标已离开 94% 饱和区,留出剂量响应空间;如仍嫌浅,加"错误过程带自信理由"层(预案,未动) |
| 5 | dose 执行方案冻结 | ✅ DOSE_DEFINITION §4b:主轴 q_d(token 份额)副轴 n_d/b_d 三轴齐报;**配对组件 1 dose unit = 1 family bundle(一对),配对永不拆**;嵌套按 bundle 前缀;replay 同桶等 token 替换吸收组件长度差(实测 format 11.2 vs evidence 115.6);T_total 与 updates 双恒定,偏差>2% 标违约;token 只认 Qwen tokenizer |
| 6 | scorer 残余 | ✅ "could/might/may be 18" 判 guess;自由文本 KEEP 词表扩充(seems/looks/appears right 等)但仅用于 NL 次级探针——主指标已改受控 DECISION 输出,不再依赖关键词;自测 **50/50** |
| 7 | base profile 可审计性 | ✅ 全套入库:pred_base_v12.jsonl(逐题原始输出)/ base_profile_v12_by_item.jsonl / base_profile_v12_summary.json / **base_profile_run_v12.json**(模型路径+sha256、chat template hash+渲染样例、generation config、命令、主机)/ token_stats_v12.json;scorer sha 在 summary 内 |
| 8 | paraphrase 决策 | ✅ 决策:**原型阶段 generator B = CC 人工改写**(50 篇全部手写,零模型污染、全可审计);机械校验=数字多重集不变(50/50 过);扩产批次改写机(非 Qwen 家族模型)另行决策,不阻塞 Gate |

## 本轮 Gate 自己逮住的第 6 个模板坑(before/after 实证)

首轮契约用了顾问示例的 DECISION=KEEP/**CORRECT** 标签 + "exactly two lines"(禁推理)。实测:
cc_attempt **decision_acc .18 但 final_acc 1.00**——模型把 "CORRECT" 读成形容词"答案正确",
并非不会保留;同时禁推理把 no-CoT 税(format 条件已单独度量为 .32)混进候选压力(wc_light
final .20、adopt .52 的假象)。改 **KEEP/REVISE** + 允许先推理后收尾两行:

| 指标 | CORRECT 标签版 | REVISE 标签版 |
|---|---|---|
| wc_light joint / adopt | .20 / .52 | **.86 / .00** |
| wc_attempt joint / adopt | .46 / .30 | **.80 / .06** |
| cc_light decision_acc | .06 | **.86** |
| cc_attempt decision_acc / final_acc | .18 / 1.00 | **.88 / .90** |

两版原始输出均入库(pred_base_v12a 未存,v12b=正式版;a 版 summary 数字留在本表)。
这就是 CONTRACT_EVAL 模板审计条款存在的理由——连"顾问建议的标签"也会翻车,审计对所有人生效。

## base 七条件画像(v1.2 正式版;n 见 summary)

| 条件 | 主指标 | 读数 |
|---|---|---|
| Original / Paraphrase / Distractor | acc_exact | .84 / .90 / .74(paired .84/.72) |
| Format | schema ∧ content | **.32**(schema .96——格式会写,内容塌) |
| Insufficient(26 手审题) | stop / paired | **.23 / .23**(guessed .69;洞实锤) |
| wc_light / wc_attempt | joint | .86 / **.80**(adopt 0/.06) |
| cc_light / cc_attempt | joint | .86 / .88 |
| wc_nl / cc_nl(泛化面) | correct / keep_joint | .85 / .20 |

## 如实申报

1. insufficient 26/50 覆盖率:为质量弃 24 题(宁缺);扩产不得直接用自动生成器(顾问裁决照录);
2. paraphrase 扩产改写机未定(不阻塞 Gate;候选:非 Qwen 家族开源模型 / 继续人工);
3. wc_attempt joint .80 仍偏高——若顾问要求更深压力,预案=自信理由层;
4. 主池 50/26 子集的 CI 较宽(±13pp 量级),原型阶段仅作方向读数,正式版按方案A 扩规模;
5. token 统计确认配对组件 families=items/2(revision/answerability 100 family),dose 契约已按 bundle 计。
