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


## C-28 裁决落定(2026-08-09)
- 优先级:P0 = eval-500+48ckpt 重评 / K eval v1 冻结(拆解+strict 修复)/ IF 数据落地;
  P1 = ANS 曲线 / K与IF {0,onset,high};P2 = mixture;P3 = margin(降级辅助,不阻塞);
- 命名:**3/4 intervention components**(replay=control);
- token 口径统一:Primary controlled = target tokens + updates;Logged nuisance = seq tokens;
- q_d 为跨组件主轴(1620 vs 2000 禁按条数横比);
- **family overlap 已裁决**:pool 级跨组件共享允许;mixture 级同 family 只准一个版本;
- K cc 崩塌已拆解:format→K 全-REVISE 判定偏置(decision .62→.06 且 wc decision 升 .96),
  placebo 不塌;preliminary,eval-500 级复验后定级;
- strict=0 定性:original/distractor 无契约提示→strict 对无契约条件 N/A(非模型不会),
  K eval v1 冻结时给 original 加轻量答案行指令或声明 N/A。


## 2026-08-09 晚:第 5 次平台回收(三机同灭于 eval-500 重评启动瞬间)
复活后第一动作(P0):
1) bringup+四件套钉(numpy1.26.4/protobuf3.20.3/scipy1.16.3/transformers4.57.3);
2) scp prescription/gate1/eval500_proto.jsonl 到各机 /tmp;
3) 三机分片跑 /tmp/re500_<idx>.sh 模式(gen_predict eval500 → /mnt/hdfs/xwqu/lawv1/eval500/pred_<rid>.jsonl,49 模型);
4) 收齐后本地 lawv1_score 全量打分 → 曲线重算(529 族置信版)→ K cc 崩塌复验定级。
margin v2 EVD/REV 扫描(P3)已中断,部分结果在各机 /tmp/margin_v2b(易失),复活后有空档再补,不阻塞。


## C-29(2026-08-10):撤回与改写台账
- 撤回:format 高剂量内容税(529 族证伪);evidence rise-fall/+8pp 峰(降为 +0~3pp 弱增益);revision 弃答税(重归因 placebo)。
- 主命题:structured but heterogeneous dose–response profiles(不写 follow scaling laws)。
- 口径:Main 529 / answerability 249 / paraphrase 50 / NL 100,分列不得合并。
- 禁令:不回头优化 Reasoning 曲线;evidence 不加点不改任务。


## C-30(2026-08-10):IF/K 裁决落账
批:if_format(F-A)/if_clean_replay(R-A)/TruthfulQA 禁训/IFEval eval-only。
改:if_answerability→SQuAD-v2 双侧+字段缺失型(FalseQA 降 secondary);if_evidence→真证据型阅读理解(sycophancy 降辅助);CREPE 暂停待 50 条支持率 Gate(≥80%);K distractor donor 独立池+hard distractor;K wc_attempt 改名或补两跳链。
欠件:K training spec(README 曾超前声称,实未写)→ 起草后随完整 audit pack v2 重交。
IF 正式训练冻结至修正完成。

## C-31(2026-08-10):IF v2 部分批准落账
answerability 扩产放行(subtype+paired);evidence 修 control/三类/去捷径后扩;CREPE 等 50 条人审 Gate;K eval 不冻结(donor 独立池强制、wc_attempt→wrong_candidate_citation 已改名);交付必须含 JSONL 本体+builder+scorer+README。
