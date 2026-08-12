# CREPE revision passage-support Gate — 裁决记录

- **任务来源**: C-30 #6 / C-31 裁决执行(CREPE revision 暂停扩产,先做 passage-support 人审)
- **日期**: 2026-08-12
- **对象**: `prescription/if_domain/if_revision_proto.jsonl`(200 条,100 family,keep/fix 成对)
- **规程**: seed 20260823 随机抽 50 family;每 family 通读 passages + candidate + target(keep 与 fix 两侧),按从严标准三分类:
  - **A** = passages 明确支持 candidate/target 的判定与内容(target 说 keep 时,passages 必须真能支撑 candidate 的核心主张)
  - **B** = 部分相关但推不出
  - **C** = 基本无关
  - 参考顾问三个反例(sleep cycle / cherry limeade / clouds settle)校准从严口径。
- **明细**: `crepe_gate_audit.csv`

## 结果

| label | 计数 | 占比 |
|---|---|---|
| A(明确支持) | 14 | 28.0% |
| B(相关但推不出) | 28 | 56.0% |
| C(基本无关) | 8 | 16.0% |

**A/(A+B+C) = 14/50 = 28.0% < 80% → 判 FAIL。grounded revision 不得扩产。**

## 失败形态(比"不支持"更糟的两类)

1. **passages 直接反证却标 KEEP**(标 B,计 4 例):
   - `2018-03977` 指甲:段落原文"剪刀发明前人们用小刀修剪指甲",candidate 却说"人们无需修剪"并被标 keep;
   - `2018-02004` 冷天气:段落原文"极端冷热加重疾病、提高死亡率",candidate 却说"冷天气不影响健康"并被标 keep;
   - `2018-01822` 升温 1 度:段落讲 2°C 阈值自增强反馈风险,candidate 却说"升温 1 度没多大影响"并被标 keep;
   - `2018-01639` 罗马熔金:段落原文"将液态熔融金属倒入冷水",fix 侧却把"罗马人熔金"当假前提改掉。
2. **纯关键词碰瓷**(C 类 8 例):如 `2018-02588` 问滑雪回转撞旗门、段落却是跳台滑雪出发门;`2018-02098` 问家用路由/网桥、段落是 WirelessHART 工业协议。

根因与 C-30 会诊一致:CREPE 的 passages 是检索到的 topic-related 维基段落,不是答案的证据来源;candidate/target 来自人写 ELI5 答案,与段落天然脱钩。**该源不具备 grounded(引证式)revision 的资格。**

## 降级执行(已完成)

按 C-31 预授权自动执行去-passages 降级:

| 件 | 说明 |
|---|---|
| `if_revision_v2_proto.jsonl` | 同 200 条(100 family × keep/fix)。prompt 删除 `Background passages:` 段,改为 question + candidate → selective revision;指令行由 "against the passages and the question" 改为 "against the question";`generator_version` → `ifproto-v2.0-nopass`。target 原本即不引证段落(200/200 验证无 "passage" 字样),判定措辞保持"correctly rejects the question's false assumption / repeats the question's false presupposition"不变。 |
| `sample10_if_revision_v2.md` | seed 20260823 抽 5 family × keep/fix 共 10 条样例。 |
| `crepe_gate_audit.csv` | 50 family 人审明细(family_id, label, 一句话依据)。 |

## 遗留风险(v2 不解决、需另行处理)

- 去 passages 只消除"伪 grounding",不修复 **KEEP 侧 candidate 本身事实错误** 的家族(如 `2018-02004` 冷天气不影响健康、`2018-01822` 升温 1 度无所谓、`2018-20718` 英苏非独立国家、`2018-03977` 古人无需剪指甲):这些作为参数化知识监督仍是错的,v2 扩产前建议对 KEEP 侧 candidate 做一轮事实性过滤;
- fix 侧存在"真命题被当假前提"(`2018-13161` 泡完热水澡会头晕本是真的),同样需要 presupposition 真值复核。
