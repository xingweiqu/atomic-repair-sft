# GATE1_AUDIT — Gate-1 原型交付审计(lawv1/C-21;2026-08-04)

## 交付物

| 件 | 内容 | 状态 |
|---|---|---|
| eval_proto.jsonl | 50 底题 family × 7 条件 = 350 行(GSM8K **test**,generator B) | ✅ |
| train_proto.jsonl | 4 组件 × 200 条 = 800 行(GSM8K **train**,generator A) | ✅ |
| build_gate1.py | 生成器(确定性 seed=20260804,无网络) | ✅ |
| lawv1_score.py | 七条件 scorer + 自测 **16/16 pass** | ✅ |
| build_stats.json | 计数/长度/验证报告 | ✅ |
| Reasoning 数据源决策 | GSM8K train/test + SVAMP external(CONTRACT_DATA §1,PROPOSED) | 待确认 |

## 自动验证(build_stats.verify_errors = **0**)

- train/eval family 零交集(split 硬隔离);
- selective_revision 每条 target 含可解析 Final answer;
- answerability 拒答 target 无任何数值猜测;
- format target JSON 可解析;
- wrong_candidate 候选值 ≠ gold(全 350 评测行);
- insufficient 删除后目标数字不再出现在题面。

## 人工抽检(CC 逐条阅读,每条件/组件 ≥5 条;4 个缺陷当场修复后复检通过)

1. paraphrase 的 "How many→What is the number of" 换词在问句前置后产生病句 → 撤销该换词,只留语法安全变换;
2. GSM8K steps 解析残渣("+11" 类退化表达式)使 evidence 的 Note 无意义 → 过滤:只用含二元算式的 step;
3. conflict 子型 target 套错 wrong_step 模板("The note contains an error"对双 Note 场景语义不通)→ 新增专用模板("Note A is right and Note B is wrong");
4. `$` 前缀数字删除产生 "$some" 病句(eval 6/50、train 15/100)→ 语法感知删除("$N"→"an unspecified amount"),复扫零残留。

## 如实申报(不打埋伏)

1. **paraphrase = WEAK_V0**:规则式(问句前置+连接词替换),扰动强度弱,量的是"句序依赖"而非全面改写鲁棒性。**扩产前必须升级为 generator-B LLM 改写机 + 答案不变性校验**;
2. **target 长度天然不均**:format 均值 ≈2.8 词 vs evidence ≈64 词 —— 正是 REVIEW 第一条的剂量混淆;正式 build 由 DOSE_DEFINITION 同桶等 token 替换吸收;format 组件与 replay 分布 JS<0.1 做不到,按契约条款如实申报;
3. **insufficient 严格不可解性**:原型版判据 = "step-1 操作数且题面唯一出现";solver 依赖图级的不可解证明在扩产版实现。抽检 10 条未见残余可解,但不能排除个别("别处可推出"型);
4. **GPU-pending**(四机全灭):base model profile、sr_subset_ids.json 冻结、模板审计初测、3 个 smoke runs——机器复活后为 Gate-1 收尾 + Gate-2 首项;
5. SVAMP external 面未入原型(50 family 全 GSM8K-test);扩产时按 CONTRACT_DATA 加入。

## Gate-1 确认清单(用户/顾问)

- [ ] Reasoning 数据源决策(GSM8K/SVAMP)确认;
- [ ] 组件构造规范(CONTRACT_DATA §3 措辞/比例/错误类型)按原型样本确认;
- [ ] 七条件 prompt 体裁(generator B)按 eval_proto 样本确认;
- [ ] paraphrase 升级方案确认(LLM 改写机用哪个生成器);
- [ ] UTILITY 的 ε_o/ε_r/ρ 与模板审计门槛数值确认;
- 确认后 → 扩产(eval 800+200 family、组件 2000 条池)→ Gate 2 smoke。
