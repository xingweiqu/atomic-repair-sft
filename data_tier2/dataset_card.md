# dataset_card — Tier-2 learnability family(2026-07-08)
| 字段 | 值 |
|---|---|
| **construct** | **procedure**(eval-ID/OOD 未见组合;A 判据=OOD 泛化,C-5.2)。例外:毒数据集的 leaked 子集 construct=recall(校准仪器,剂量 10/30% 精确断言) |
| 生成器 | learnability_family/{ops,generate}.py @ 本 commit;四档 flurm/zorp/quilt/brame(深度 0/1/2/3) |
| 体量/切分 | 每档 train 2000 / eval-ID 500(未见组合,[0,99])/ eval-OOD 500([100,999]);组合集交集=∅ **构造性断言 PASS** |
| 闸门 | 干净闸门(zero-shot ≤5%,server predict)/ token 审计:char-proxy p95≈88–107 tokens(≪1024);exact 审计 = learnability_family/gate_token_audit.py(server,训练前跑,exit 1 即停) |
| 体裁 | 素题(plain genre)全程——A 主张的判据体裁(R-7) |
| regime | greedy 单次 |
| 预注册 | prereg/PREREG_tier2.md(同 commit,先于训练) |
