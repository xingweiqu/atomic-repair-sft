# PREREG_batch2 — 剂量曲线(裁决③;训练前冻结,2026-07-10)

> 授权:`qc/LOOP3_RULINGS_batch1_verdict.md` ③。训练开始后本文件不改一字;
> 判定另立判定页。硬停条件 = 与本预注册矛盾。

## 1. 问题

1. **format 毒性稀释阈值**:纯 format 无干净工作点(mute 12.3–21.3%);
   混合臂里 36% 掺量(A1)却安全。多少掺量"既修复又不训哑"?
2. **drills 危害剂量律**:纯 drills W_adopt 25%。危害随剂量如何进入?
   (把 E1 的 keep 剂量律推广成"服从类数据"通律。)
3. **scaffold-救-format 异常**(94%):format 桶吃的是"结构"还是"JSON 约束"?

## 2. 设计(6 新臂 + 3 个已有端点,免重训)

**载体固定**:全部剂量臂以 Batch-1 的 `arm_cleanreplay.json`(600 题纯净重放,
脊点 e4 已测)为载体,**替换式掺入**(总量恒 600 题,换入 N 题组分)——
剂量轴上只有组分份额在变,载体成分不变。

| 臂 | 组成(题数) | 剂量(题份额) |
|---|---|---|
| fmt10 / fmt20 / fmt36 | format 60/120/216 + 载体 540/480/384 | 10 / 20 / 36% |
| drl10 / drl25 | drills 60/150 + 载体 540/450 | 10 / 25% |
| scafffmt | scaffold 300 + format 300 | 50/50 对照 |

已有端点(不重训):0% = cleanreplay(e4);100% format = single_format
(无干净工作点);100% drills = single_drills(e4)。
drills 题长约为其他组分 1/10,**题份额为主口径,字符份额如实披露**(承 Batch-1 裁定)。
组分题从池中以 rng(4242) 抽取,与 Batch-1 臂的池共享如实披露(训练相互独立)。

训练协议 = Batch-1 原样:Qwen3-8B full-FT,seed 42,epochs {2,4,8,16},
lr 1e-5 cosine,cutoff 1024;脊点闸门(冻结):answered≥0.95 ∧ bleed≤5% ∧ mute≤12%,
取最小通过 epoch。评测 = 全探针套件 @ 脊点(REd 口径 + Δcleanreplay)
**+ 修复腔 corrupt 评测 @ 脊点**(genre_eval,接②b 体裁对账)。

## 3. 预测(冻结;打分用 ±0.15 灰区,承 Batch-1 判定页)

- **P-B2-1(format 稀释)**:毒性是"纯食谱"效应而非剂量阈值——三个剂量臂
  **全部**通过脊点闸门;REd_format 在 20% 剂量即达 ≥+50pp(Δcleanreplay),
  36% 相对 20% 增益 <10pp(饱和)。**证伪面**:fmt36 过不了闸门
  (→毒性是剂量阈值);或 fmt10 已饱和(→修复比预想更便宜)。
- **P-B2-2(drills 危害)**:W_adopt 随剂量单调进入:载体基线 ~2% → drl10 ≥5%
  → drl25 ≥10%;REd_conduct 同步单调下降。**证伪面**:阈值型
  (10/25% 均与载体无异,危害只在纯食谱出现)。
- **P-B2-3(结构 vs JSON)**:若 format 桶吃"结构",scafffmt 的 REd_format
  ≈ single_scaffold(94%)且不需 JSON 数据;若吃"JSON 约束",
  scafffmt ≈ 含 format 混合臂(75–87)。两区间不重叠,可判。
  附带:scafffmt 通过闸门(scaffold 稀释 format 毒性)。

## 4. 产物与判定

- 臂文件 `loop3/arms/arm_{fmt10,fmt20,fmt36,drl10,drl25,scafffmt}.json`
  + `manifest_b2.json`(题数/字符双口径);configs `configs/loop3_b2/`(24 个)。
- 判定页另立;三预测逐条 HIT/MISS;臂结局判定归 Xingwei/顾问,CC 只报数。
- Loop 5 追加预测 P-L5-drills(cos(d,ΔW_drills)<0)已在
  `prereg/ADJUDICATION_loop3_batch1.md` §4 注册,drl 剂量 ckpt 一并保留。
