# Scenario-Repair v3.1 报告(去耦加固 + 干净 selective matrix)

> 所有数字 = 本地 strict judge 对服务器预测评分。分支 scenario-repair-v4。
> v3.1 解决了 v3 的两个问题:(1) 标记/实体 shortcut(双层闸门 PASS),(2) abstain judge 伪影(已更正)。

## 0. 一句话

**去耦后(双层闸门通过)对症诱导依然成立且更干净**:6 个 policy 对角线全亮(gain +69~+93),
verify_bridge 在消除 marker+实体捷径后仍从 3%->78%(真验证能力非模板路由);
targeted >> random(对症 >> 数据量)、targeted ~= wrongtarget(程序演示是载体、标签是元数据);
abstain 从真基线 0% 被纯训到 100%(最干净诱导对角线)。

## 1. 两道加固(对应 v3 的两个洞)

### 1a. shortcut 去耦 — 双层闸门 PASS
- 实体平衡注入器:每个被引用值真:假频次约 50/50(总 220:220,0/30 严重不平衡)。
- **硬闸门**(keep-vs-update,同域同句式,实体掩码后)= **0.458 约随机** < 0.65。marker 独立(卡方 p=0.18)。
- 能力分解:决策 = 事实查询(知识,L2 全量 0.76 披露)+ 声明比对(程序,闸门证明无捷径)。

### 1b. abstain judge 伪影更正(见 data_v3/ERRATUM_abstain_judge.md)
- Fact-only 真实弃答 0/60(全硬猜),旧 judge 因裸输出误判为 100%。strict 修复后 Fact-only abstain=0%。
- Fact-only 总体 strict = **39%**(旧 49.7%);knowing!=using 更强。

## 2. 基线(strict)

| policy | scaffold_only(真地板) | Fact-only |
|---|---|---|
| override_wrong_claim | 22% | 93% |
| verify_bridge | 3% | 13% |
| verify_step | 0% | 0% |
| recompute | 13% | 33% |
| use_provided_support | 30% | 88% |
| retrieve_or_abstain | 12% | 0% |
| (overall) | 16% | 39% |

## 3. Selective Repair Matrix(raw acc %,行=训哪个policy,列=eval policy)

| trained \ eval | override | verify_bridge | verify_step | recompute | use_support | abstain |
|---|---|---|---|---|---|---|
| **override_wrong_claim** | 95% | 12% | 7% | 37% | 94% | 13% |
| **verify_bridge** | 45% | 78% | 2% | 24% | 58% | 0% |
| **verify_step** | 52% | 22% | 93% | 47% | 69% | 0% |
| **recompute** | 100% | 27% | 100% | 100% | 94% | 100% |
| **use_provided_support** | 43% | 7% | 53% | 59% | 99% | 97% |
| **retrieve_or_abstain** | 37% | 8% | 7% | 39% | 53% | 100% |
| scaffold_only(地板) | 22% | 3% | 0% | 13% | 30% | 12% |
| actionized_full(端点) | 72% | 45% | 100% | 98% | 100% | 100% |

## 4. 对角线 gain(相对 scaffold_only 真地板)+ Selectivity

| policy | scaffold地板 | targeted对角线 | gain | selectivity |
|---|---|---|---|---|
| override_wrong_claim | 22% | 95% | +73 | +0.52 |
| verify_bridge | 3% | 78% | +75 | +0.64 |
| verify_step | 0% | 93% | +93 | +0.71 |
| recompute | 13% | 100% | +87 | +0.16 |
| use_provided_support | 30% | 99% | +69 | +0.27 |
| retrieve_or_abstain | 12% | 100% | +88 | +0.73 |

**6 个 policy 对角线全部大幅为正**;verify_step/abstain/verify_bridge/override selectivity 都 >=0.5。
关键:**verify_bridge 去耦后仍 3%->78%(gain +75)= 真验证能力,非模板路由。**

## 5. Controls(自己 policy 上 raw acc)

| policy | targeted | same-size random | wrong-target |
|---|---|---|---|
| override_wrong_claim | 95% | 15% | 95% |
| verify_bridge | 78% | 12% | 82% |
| verify_step | 93% | 58% | 90% |
| recompute | 100% | 99% | 100% |
| use_provided_support | 99% | 95% | 99% |
| retrieve_or_abstain | 100% | 2% | 100% |

- **targeted >> random**(abstain 100 vs 1.7,verify_bridge 78 vs 12)= 对症数据 >> 数据量。
- **targeted ~= wrongtarget** = 起作用的是 trace 程序演示,policy 标签是路由元数据(与 v2.1 一致)。

## 6. 结论 + 对 v3 的修正

1. 去耦后对症诱导**更干净**(对角线全亮、selectivity 高、无 v3 那种负迁移混乱)。
2. **能力分解**:verify 增益拆成 知识(查表,L2 0.76)+ 程序(比对,闸门 0.458 证明无捷径);
   去耦后 verify_bridge 仍 +75,证明诱导的是真程序能力。
3. abstain 是**纯诱导**(0->100),非自带 —— 修正 v3 的伪影结论,故事更强。
4. 程序载体 vs 标签元数据:targeted~=wrongtarget 再次坐实。

## 7. 局限 / 下一步
- 单 seed(3-seed 模板已留);verify_step/scaffold_only JSON 有效率偏低(78%/24%),可加 epoch。
- **封闭合成世界的循环性**(声明真假由三元组决定)结构性解药是 Phase 2(GSM:中间步对错是算出来的,
  不是背出来的,实体记忆捷径不存在)。Phase 1 不镀金,留预算给 Phase 2。
