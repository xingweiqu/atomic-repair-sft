# CLAIM TRUTH TABLE(P1,唯一事实源;随稿入 Appendix;2026-07-20)

| # | claim(正文措辞锚) | model×domain | seeds | 证据 | 判定 |
|---|---|---|---|---|---|
| T1 | nonspecific floor(U≈replay 素题面) | Qwen8B×GSM | 3/臂 | fig4a, batch1_scores | replicated |
| T2 | 同上 | Llama×GSM | 1 | m2_scores | replicated |
| T3 | 同上 | Mistral×GSM | 1 | g1_scores | replicated |
| T4 | 同上 | Qwen8B×2Wiki | 3 | scores_2wiki | replicated |
| T5 | 同上 | Qwen8B×SVAMP / StratQA | 1 / 1 | scores_svamp / stratqa | replicated |
| T6 | format 组分特异(60 题饱和) | Qwen8B×GSM | 剂量臂 1;单组分无干净点 | fig5a, batch1_scores | replicated |
| T7 | format=防丧失变体 | Llama / Mistral ×GSM | 1 / 1 | m2/g1_scores(F→0.00) | variant |
| T8 | format 病灶缺席→不可测 | Qwen8B×SVAMP;Qwen4B 画像 | 1 | scores_svamp; profile_qwen3_4b | untested(no disease) |
| T9 | drills 修复腔毒性 | Qwen8B×GSM | drl25 剂量 1;纯 drills 2(s43 无干净点) | batch2/batch1_scores | replicated(dose 单 seed 披露) |
| T10 | drills 毒性 | Llama/Mistral/SVAMP/StratQA | 各 1 | 各 cell scores | absent×4(范围=Qwen×GSM) |
| T11 | genre gating 增益可见度 | Qwen8B×GSM | 3/臂 | genre_scores vs batch1 | replicated |
| T12 | gating 方向反转 | Qwen8B×2Wiki | 3 | scores_2wiki | variant(方向域依赖) |
| T13 | gating | Qwen8B×SVAMP | 1 | scores_svamp | replicated(计算域同向) |
| T14 | gating | Qwen8B×StratQA | 1 | scores_stratqa | below criterion |
| T14b | gating | Llama×GSM | 1 | m2_scores(修复腔 +40~50 vs 素题 −1~+7;冻结判据事后判,披露) | replicated |
| T15 | scaffold sign-flip | Qwen8B×GSM | 3(2/3 反向) | NOTES_c15a | **retired**(operating-point artifact,附验尸) |
| T16 | abstain 排序 D>B | Qwen8B×GSM | B 3-seed ±15pp | NOTES_b_seeds | **retired**(方差,附验尸) |
| T17 | steering 杠杆 | Qwen8B(L12) | E5b+E 臂 | NOTES_steering_e5b, e_arm | replicated |
| T18 | steering 杠杆迁移 | Llama(L22) | 扫描+全评 1 | scan2, m3v2_result | replicated(P-M3-3 −3.03 机械 MISS 照记) |
| T19 | steering 红利(.760 超全臂) | Qwen8B×GSM | 1(验尸签字) | NOTES_e_arm_autopsy | replicated(契约门控) |
| T20 | steering 红利迁移 | Llama | 1 | m3v2(.058) | absent(契约缺席) |
| T21 | steering 杠杆 | Qwen32B | 扫描 | scan2_verdict g2 | absent/no-push(instrument-limited) |
| T22 | 配比不优于 uniform/reversed | Qwen8B×GSM | 3×3 臂 | stats_boot_tost | replicated(B−A1 +4.2 CI 排零,呈拍板) |
| T23 | 可教前沿不弯(合成域) | Qwen8B×synthetic | 7 档 | race_summary, tier2 | replicated(synthetic-scoped) |
| T24 | 知识域已知题税(内容侧) | Qwen8B×2Wiki | 3 | knowledge_tax_per_item | replicated;StratQA 不复现(披露) |
