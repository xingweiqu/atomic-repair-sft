# B1 2Wiki 验证章收割(C-12 B1;2026-07-13)

> 口径:PREREG_2wiki(冻结)。12 训零失败 + pre-repair 基线行;判分 = strict
> (JSON 契约 final_answer,contains-匹配)为主口径,lenient(全文 contains)降辅助。
> **仪器事故已排除**:lenient 下 cleanreplay .827"最高分"是实体链喷洒撞金串的
> 伪影(JSON 遵约率 1%,抽样验证);GSM 时代 strict/lenient 教训第三次应验。
> 数据:wiki2/data/scores_2wiki.json。只报数,判定归 Xingwei/顾问。

## 0. 病情表(pre-repair,known 子集 376/800=47% 进分母)

conduct 47(adopt 19 / derail 28,= 12.5%)/ format 25(6.6%)/ phrasing 3 /
fail_O 5 / ok 296(78.7%)。
**P-2W-3 前半 HIT:构成与 GSM 确实不同**——conduct 占比相近(12.5 vs 16.4)
但 **format 桶塌缩**(6.6 vs 14.7)且 adopt:derail = 19:28(GSM 是 9:227!)
——知识域的"被带偏"以直接采纳为主,计算域以脱轨为主。

## 1. 主表(strict;ridge 按遵约健康取最小可用 epoch)

| 臂@点 | 修复腔 strict | adopt | 遵约率 | 素题 conduct(a/d) | fail_O(训练税) |
|---|---|---|---|---|---|
| **pre-repair base** | **.638** | .005 | 100% | 19/28 | 5 |
| U 均匀混 @e4 | .479 | **.003** | 99% | **0/4** | 41 |
| FMT 10% @e4 | .465 | .011 | 100% | 11/18 | 40 |
| cleanreplay @e2 | .441 | .008 | 99% | 7/56 | 41 |

(cleanreplay e4/e8 遵约率 54%/1% → 无干净点尾部;FMT e8 瞬态崩 31% 后 e16 恢复。)

## 2. 预测判分

- **P-2W-1(防骗组分可迁移,U Δ安慰剂 ≥+8pp 修复腔)**:按注册度量 **MISS**
  (strict .479 vs .441,Δ+3.8pp)。但**行为面迁移成立**:素题 conduct 桶
  U 把 adopt 清零、derail 压到 4(安慰剂 7/56;base 19/28)——防骗行为
  在素题面到账,修复腔 acc 没有。
- **P-2W-2(体裁门控复现)**:**方向反转的第四例**——2wiki 里"组分是否有用"
  在**素题面可见**(U conduct 0/4 vs 安慰剂 7/56)而修复腔 acc 分不开;
  GSM 是反过来的。体裁门控作为"体裁=开关变量"的命名不被伤害,
  但"修复腔总是放大修复收益"的读法被证伪——开关方向是域依赖的,如实入 CL-6。
- **P-2W-3(处方同构)**:前半(构成不同)HIT;后半(format 组分存废 >30pp)
  ——base 的 format 桶本来只有 25 题(6.6%),FMT 臂把它压到 2(vs 安慰剂 14),
  方向成立但绝对量小,域里没有 GSM 那样的 format 病灶可修。
- **证伪面之外的大发现(未预注册,登记)**:**600 题任何训练都伤 2wiki 的
  已知题 QA**(fail_O 5→34-56,≈9-13% 训练税)且**全部训练臂修复腔 acc
  低于 pre-repair base**(-15~-20pp)——知识域对小规模 SFT 比计算域脆弱得多;
  处方手册规则 2("验收体裁")在知识域应升级为"验收还要对照 pre-repair"。

## 3. 给 CL-6 的措辞素材(归顾问)

体裁门控三例(GSM)+ 2wiki 反向第四例 → 命名应表述为
"**效应的可见度与符号由(域 × 体裁)决定**",不是"修复腔放大一切"。
图 8 左照此画(素题 conduct 面板 + 修复腔 strict 面板并排)。

## 4. ★5 前置核查(裁决 2026-07-12):fail_O 新失败尸检

三臂(U_e4 40 条 / FMT_e4 39 条 / cleanreplay_e2 47 条)逐条转录分类:
**json_bleed = 0,mute = 0,answered_wrong = 100%**——知识域训练税是
**内容侧(真遗忘/虚构),不是体裁侧(出血)**。形态:模型以训练痕迹格式
编造错误证据链(例:gold "Tower" → "Step by step: … --place of death-->
Westminster/Greenwich Palace")——答案错在链的内容,不在文体。
措辞可定:"知识域 600 题 SFT 的已知题损伤是事实虚构型新税种,与 GSM 的
体裁出血税不同源"——按裁决 (a)+(b) 双入(处方规则 2 v1.1 附注 + limitation)。
复现:pred_{arm}.jsonl O 探针 vs pred_Qwen3-8B.jsonl,分类规则见对话归档。
