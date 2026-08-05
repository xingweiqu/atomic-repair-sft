# QUEUE_STATE — C-25 连续执行模式状态板(随进度更新;2026-08-05)

## 队列 A:✅ 完成(BUDGET_PASS)

- packed + 固定 max_steps=8:三臂 updates 恒等(8/8/8),target-token dev ≤0.06%,
  批次数/每步 token 恒等;seq-token 差申报为 epoch 当量(2.0/1.67/1.67);
- **混淆检验(v1 unpacked vs v2 packed,均单 seed sanity)**:

| endpoint | v1: P/60/200 | v2: P/60/200 | 判读 |
|---|---|---|---|
| fmt contract_exact | .54/.76/.96 | .62/.64/.88 | **剂量方向存活**(斜率减半=部分系 update 伪影) |
| fmt MAIN | .46/.38/.24 | .38/.40/.28 | 高剂量损伤仍在,更缓 |
| original | .78/.80/.76 | .84/.82/.82 | v1 的"受损"大半是伪影,v2 近平 |

- 工件:lq:/opt/tiger/lawv1_runs_v2/ + budget_validation.json(repo 已收);
- 待顾问过目:target-token vs seq-token 恒定不可兼得的结构申报(validator note)。

## 队列 B:进行中

- ✅ family 分区冻结(20260813):format[0:2000] carrier[2000:4000] reserved[4000:6817];
- ✅ 正式 carrier 2000(GSM-train solve replay,决策入档)+ format 池 2000;检查全过;
- ✅ TRAIN_INSUF_AUDIT.csv;
- ⬜ 评测扩 500 主 family + calibration split(paraphrase 保持 50 手写子集,申报);
- ⬜ insufficient 扩产子集(机械闸门→全量人工审核,分批);
- ⬜ base profile(500 版)+ 模板审计脚本/初测;
- ⬜ RUN_MATRIX_format.csv 冻结(网格 n∈{0,30,60,120,240,480,960,2000},
  锚点 3-seed:n=0/120/960/2000,已按 C-25 预冻结)。

## 队列 C:待 B 完成自动启动(lq 单机串行,run_p2a 世系跑批)

## 队列 D:未启动;**family 短缺决策项挂起**(reserved 2817 < 3×2000,
  候选:跨组件共享+申报 / 合成扩充 / 缩池;不得静默解决)

## 停止规则(C-25 原文)

hash 不匹配 / token 偏差>1% / updates 不一致 / 撞族 / 评测缺行 / NaN / self-test 不全过 /
工件不齐 / 同配置连败两次 → 停当前队列。OOM 仅准降 micro-batch 等比升 accum 重跑一次。
不得自改 LR/steps/指标/阈值。
