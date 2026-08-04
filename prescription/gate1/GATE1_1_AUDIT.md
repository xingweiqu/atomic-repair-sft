# GATE1_1_AUDIT — gate1-v1.1 整改交付审计(C-22;2026-08-05)

> 对应裁决:Gate 1A 骨架通过 / Gate 1B 数据与评分未通过(qc/INSTRUCTION_C22.md)。
> 本轮按 8 点整改单逐条执行;扩产与正式训练继续冻结,待再次确认。

## 逐条整改对照

| # | 整改要求 | 落实 |
|---|---|---|
| 1 | insufficient 类型化删除 + 不可解依据 | ✅ 按值匹配完整数字 token(含 $/%/小数),类型分支 percentage/price/count;**ratio、fraction、time、val==1 判为不可安全删除→跳过该算子/题**(宁缺毋滥);count 型吞并后续名词+正规复数化;每条记录 removed_variable / variable_type / replacement / dependency_path / why_unanswerable。类型分布:count 111 / price 35 / percentage 4 |
| 2 | distractor 去标记、去固定模板 | ✅ 4 个主题相关模板(店铺售卖/个人收藏/库房清点),无任何"无关"字样(verify 硬检 5 个禁用标记);数字 k∈3..29、单价 p∈2..9 逐题随机且避开题面数字;实体从 8 名 × 8 物品池抽;**问句含人称代词时只用无人名模板**(防指代捕获,扫描 0 冲突) |
| 3 | selective revision 定义 | ✅ 选 **Option B(full-attempt revision)**:prompt 含逐步 Candidate attempt + final answer;keep target 确认全过程,fix target 只从错误步起修(dropped_step 型专用"缺最后一步"措辞) |
| 4 | wrong-candidate taxonomy | ✅ 4 类:arithmetic_slip / operator_error / dropped_step / off_by_one,全部由真实错误过程推导(candidate 值=错误推导的产物);比例入 build_stats(eval: 18/14/12/6);×10 型已废除 |
| 5 | scorer 修复 | ✅ acc_exact(仅限定式声明:boxed>末个 Final answer>####)与 acc_loose 真分离;correct_candidate 拆 final_correct / explicit_keep / explicit_reject,**preserve 主指标=keep_joint**;insufficient_stop 拒绝"abstain 后猜测"(定式答案/answer is N/hedge词+数字均判 guess);original 行新增 abstain 字段→**false_abstain 实测**(与 mute 分离) |
| 6 | format 假字段 | ✅ unit/confidence 字段删除;A2 改为 {"calculation": 末步真实算式, "answer": N}(逐题真实内容);A4 改行式 "answer: N" |
| 7 | target reasoning 清洗 | ✅ 全表达式匹配 + eval 执行校验(2% 容差)+ 残缺算式正则(如 "8*=40"),不过检的题直接弃用;builder 自产 target 同样过检(verify 0 错) |
| 8 | 对抗单测 + 随机抽检 | ✅ scorer 自测 16→**36**(含顾问全部对抗例:否定后答对、abstain+guess、原题拒答、双数字、JSON 两向错位、多 final、boxed 冲突、空/截断/乱码);审计册改随机抽样 seed=20260805 |
| 7' | token 统计 | ✅ token_stats.json 用 **Qwen3-8B 正式 tokenizer** 在 lq 上实测:target 均值 format 11.0 / revision 33.9 / answerability 58.1 / evidence 111.0;input 均值 61.7–154.3 |

## 本轮随机抽检新抓的缺陷(已修复+复扫零残留)

1. count 删除只换数字不吞名词 → "an unspecified number of lollipops **lollipops**"(修:吞名词+复数化);
2. "1 year old" 删 1 后病句且值可由语法推出(修:val==1 一律不删);
3. distractor 带人名模板遇问句代词 "she" 产生指代捕获风险(修:代词检测→无人名模板);
4. 算式校验正则把 "16-3-4=9" 部分匹配成 "3-4=9" 假阳性、把句号吞进结果 "8.00."(修:全表达式+严格数字 token);
5. abstain target 贪婪抓取把题面残句写进"缺什么"(修:直接用 replacement 短语)。

## 如实申报(不打埋伏)

1. **paraphrase 仍是 WEAK_V0**(规则式问句前置)——待 Gate-1 确认清单里的"改写机用哪个生成器"定夺后升级;本轮 8 点整改单未含此项;
2. **insufficient 的不可解性仍是启发式**:判据 = 首步直接算子 + 题面唯一出现 + 不等于其他数值 + 类型可安全删除;solver 依赖图级证明留给扩产版(契约已写);随机抽检 15 条未见可解残余;
3. token 长度不均如实入账(target 11 vs 111):正式 build 由 DOSE_DEFINITION 同桶等 token 替换吸收,format 天然短按契约申报;
4. **GSM8K 记忆风险未消除**(顾问第一点里的"原题被记忆"):删条件题仍可能被背题模型"猜中原数"——base profile 的 insufficient false-answer 值将给出实测读数,留观;
5. 剩余流程件(RUN_MATRIX、S/R subset、模板审计、smoke)按 C-22 顺序:**base profile → 确认 → smoke**,未获确认不扩产不开训。

## 交付物清单

build_gate1.py(v1.1)/ eval_proto.jsonl(350)/ train_proto.jsonl(800)/ build_stats.json /
token_stats.json / lawv1_score.py(v1.1,36/36)/ AUDIT_SAMPLES.md(随机抽样)/ 本文件。
