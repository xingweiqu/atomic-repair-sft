# CLAIM_EVIDENCE_TABLE(C-52)

| # | Claim(允许口径) | 级 | model(s) | experiment | seeds | figure | limitation |
|---|---|---|---|---|---|---|---|
| 1 | Aggregate 分数掩盖异质 atomic failure;paired ΔL/margin 先于 score 见衰减 | A/B | Qwen3-8B(item 级);7 ckpt profile | eval500 + loss extraction | profile 单 seed;anchor 3-seed | Fig1 | margin 仪器偏置按轴;raw NLL/BPB 不可跨模型 |
| 2 | 四 repair 家族 dose response 异质(cheap/weak/resistant/constrained) | A | Qwen3-8B | 529-fam 全网格 | anchor 3-seed | Fig2 | 4 个代表性家族,非穷举 |
| 3 | Local repair response shapes exhibit transferable structure after low-dimensional model adaptation(a+τ) | B | Qwen3-1.7b/4b/Llama/Mistral | 3 剂量校准 → 第三点 held-out | 校准点单 seed | Fig3 | τ 网格粗;FMT 跨族散差大;非 universal |
| 4 | Atomic responses 不加性组合;carrier+diversity 为 dev-family 修正 | A | Qwen3-8B | 预注册 6 臂 + rescue | 混臂单 seed,预注册 | Fig4 | 修正结构 dev-family 发现 |
| 5 | Damage 是 composition-borne、模型特异、非单调;benefit prediction easier than safety prediction | A(borne)/B(non-mono 待复制) | 4 模型 | 20 CD 臂 + 单臂 damage 剂量 vs 混臂 | CD 单 seed→复制中 | Fig4 inset+Fig5 | 05_DAMAGE_REPLICATION 裁决 non-monotonicity |
| 6 | Stage A prospective transfer:U ranking 复现 ∧ damage 约束失手(2 模型) | A | 1.7b/Llama | freeze ca02d0c → open | 单 seed(后关键臂 3-seed 加固) | Fig5 | 正负两面必须一起讲 |
| 7 | Stage B adaptive sequential refinement 沿经验锚推进 frontier;strict 全绿上限=uniform(1.7b),δ=.01 下 CD1200d/v3frontier | A(1.7b 3-seed)/B(llama) | 1.7b/Llama | v2/v3 rounds + 3-seed 复制 | 关键臂 3-seed | Fig5 | **非独立盲测**;llama strict δ=0 无有效臂 |
| 8 | Clean retention 需 non-inferiority 框架(δ=0 下 2/4 模型无有效臂) | A | 4 模型 | 32 臂审计 | 关键臂 3-seed | (appendix 表) | δ=.01 为先验 noise band,非事后挑 |
| 9 | PARA 是 loss-visible、model-conditional 的补充 repair | B/C | 4 模型 | 3 剂量 loss 曲线 | 单 seed | (appendix) | 行为分不动;1.7b null、mistral 噪 |
