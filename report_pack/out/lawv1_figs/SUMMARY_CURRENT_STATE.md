# SUMMARY_CURRENT_STATE — SFT Response Law(2026-08-06;repo commit 4e16122)

## 1. 冻结资产(hash 见各 manifest/RUN_MATRIX)
- 契约:prescription/contracts/ 五份 + DOSE_DEFINITION(§4b)+ TRAIN_EVAL_SEPARATION + APPLICABILITY_MATRIX + UTILITY_AND_BASELINES
- 评测:prescription/gate1/eval_proto.jsonl(518 行,main-pool 50 随机 + insufficient 26 全手审 + STATUS/DECISION 契约)
- 训练池:carrier_formal(2000)/format_pool_formal(2000)/evidence_pool_formal(1989)/revision_pool_formal(2000);family 分区 seed 20260813;183 族 EVD∩REV 共享已申报
- 矩阵:RUN_MATRIX_{format,EVD,REV}.csv(各 16 run,含 data/config/eval/scorer hash)
- scorer v1.2(56/56)/ 打包训练配置 / budget validator

## 2. 已完成结果(全部正式规模,恒预算恒 updates,预算校验 PASS)
- **Format**:contract_exact 饱和形(placebo .67→30 条 .96→60 条 1.00);retention 全平;fmt MAIN 揭示内容税天花板;LODO:law MAE .043 < nearest .078(Fig6)
- **Evidence**:distractor 温和收益(峰 .88@480,+8pp)疑似 rise-fall;纯组件角点(q_d=1.0)零损伤;format 体裁溢出 .68→.94
- **Revision**:keep/fix 跷跷板(keep .92@60→.54@2000;fix 谷 .54@60 回 .76@480;adopt 冲 .28@60);弃答税 .26→.14
- Gate 链:Gate1A/1B/1.2/1.2.1-exec 与 Gate2(含 update 混淆修复与对照)全过
- 附:base 画像(v1.2.1 评测)、smoke 系列(标 sanity signal)

## 3. 在跑
- m1:margin probe v2(修 token 对齐+真语义置换),base+16 format ckpt(Fig7 填充源)
- 其余 GPU 空闲待队列(见 §5)

## 4. Knowledge/IF 仍缺的 dataset decisions
- 2Wiki:train/reserved split 划分与规模冻结(原始三 split 在 HF,本地仅 validation 派生件)
- Knowledge 五池构造规格批准(passages 已确认可得)
- IF:if_format 与 if_clean_replay 载体来源(全仓无现成);CREPE/FalseQA/sycophancy 角色批准
- SVAMP/StrategyQA 旧 arms 降级 archive 确认(C-16 污染)
- Reasoning answerability 扩产池全量审核(进行中,闸门内)

## 5. 后续 run matrix(预计)
- ANS 网格 16(审核后)| K/IF 跨域零训练评测:49 ckpt×2 域(评测 run)| K 稀疏训练 ~10 | IF 稀疏 ~10 | mixture ~12 | held-out model ~20

## 6. blocker 与 hard-stop
- blocker:K/IF 评测未建(跨域零训练评测被堵);IF format/replay 载体无来源;answerability 审核未完
- hard-stop 规则:C-25 停止规则全文(hash/预算/撞族/NaN/工件);平台回收史:4 次(恢复流程已固化)

## 7. 图源数据
fig1: QUEUE_STATE.md | fig2: DATA_ROLE_MATRIX.csv | fig3-5: grid_scores/gs_FMT-*.json + dose_manifest_format.json + base_profile_v121_summary.json | fig6: format_curves.json(锚点噪声)+ 同 fig3 | fig7: margin_v2/*.jsonl(pending 时标注)| fig8: RUN_MATRIX_*.csv + HDFS DONE 计数
