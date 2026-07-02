# LOOP1.5 — H1/H2/H3 判别实验报告(零算力部分,2026-07-02)

> 依据:qc/LOOP1_RULINGS.md §2。判据先于数据(判读表照抄裁决),T1/T2/T3/T5 已做,
> T4(判决性)已备好交付服务器(qc/RUNBOOK_batch1.md Job 1)。
> R-5 纪律:在 T4 落地前,一律用中性措辞"repair-mode ability 读数下降",不写"能力被损坏"。

## 结果一览

| 实验 | 结果 | 对假说 |
|---|---|---|
| T1 transfer 直读 | transfer 预测**不含 scaffold_conv**(仅 base/verify_step/actionized_full)→ 判决改由 T4 承担。partial 信号:素题作答准确率 base 99.6%(answered 277/300)、verify_step **95.5%**(201/300)、actionized_full **83.4%**(157/300) | verify_step 素题算术完好 → 单 operator 上 H2 倾向;actionized_full 作答率坍塌+轻降 → 张力属实,待 T4 |
| T2 转录验尸 | pool=28(matched=50 中 pre 对、floor 错),自动初分类:**真算错 27 / 算对提取错 1 / 烂尾 0**;30 条转录在 `ledger/T2_transcripts.md` 待 Xingwei 亲自过目 | **(ii)+(iii)≈0 → H3(scorer/提取伪影)出局**;(i) 为主 → H1 vs H2 由 T4 分辨 |
| T3 选择偏差 | matched(n=50) vs 全部 w 题:**步数分布 KS D=0.047, p=1.000(无偏)**;题长 D=0.269, p=0.004(matched 偏短题) | 难度主代理(步数)无偏 → **H3 的选样一半也出局**;题长差如实登记,方向不足以制造 −52pp |
| T5 镜像测量 | "pre-repair resist 但算错"的题**只有 2 条**(pre-repair 在 parsed∩resist 内 ability≈0.96)→ 无统计功效。2 条上 scaffold_conv/actionized 2/2,targeted 0–1/2 | 镜像角落照过、藏不下 A,但**样本不足以下结论**;该测量的功效版本 = Loop 2A 难题桶([0–25%] pass@8 桶正是"pre-repair 不会"的题) |

## 当前判读状态(照裁决判读表)

- H3 出局(T2+T3)。
- H1 vs H2 悬置,**由 T4 判决**:28 条 matched floor-wrong 题的素题孪生版已生成
  (`data_v4/t4_plain_probe.json`,28/28 gold 与 eval 一致,经断言校验;首版 source_id
  位置映射错误已修——用 `gsm_world.load_gsm` 本尊的 id 分配,杜绝错位),
  scaffold_conv 与 pre-repair 双 predict configs 就绪。
- 素题恢复(≈base)→ H2 "mode-interference measurement artifact";素题同样错 → H1
  "convergence ability tax"。两案的论文含义见裁决 §4,不预判。

## 已并入账本的落地项

- **R-4(C-4a)**:`master_ledger.csv` 新增 `d_a_prerepair / n_matched_pre / lowpower_pre`
  三列(能力主张判据列);spot:v4 actionized −37.5pp(n=48, LOWPOWER)、targeted_recompute
  −50.0pp(n=62)、**v5 +0.7pp(n=138)≈0**、v3.1 n=0(factonly 地板不产出可解析输出,如实 NA)。
- **R-7 预埋**:T4 素题孪生的生成路径就是 Loop 2A/2B "双体裁 eval" 的原型
  (同题、无植入、无 schema、transfer 同款指令)。
- **R-8**:factonly(=inject ckpt)× v2.1 eval 的 predict config 就绪。
- **R-6(Loop 1.5 sweep)**:两条扩展分析(repair-mode ability 读数 vs epoch;
  "最小充分收敛" canonical-floor 规则)将并入 `gsm_repair_v4/epoch_sweep.py` 产出——
  该批 23 个训练点仍待服务器执行(与 batch-1 相互独立,可并行)。

## 等待

1. Xingwei 过目 `ledger/T2_transcripts.md`(30 条,自动分类仅供初筛)。
2. 服务器跑 `qc/RUNBOOK_batch1.md`(T4 判决 + pass@8 校准 500 + R-8),回传 4 个文件。
3. T4 回传后:出 R-5 命名裁决材料(H1/H2 判读 + 论文措辞提案)。
