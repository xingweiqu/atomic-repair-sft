# CC_INSTRUCTION_C31 — C-30 v2 部分批准(2026-08-10,要点存档)

- ✅ if_answerability_v2 构念修正正确:批准 SQuAD-v2 grounded answerable/unanswerable + structured missing-field 为核心路线,**可并行进入正式池建设**;扩产要求:insufficient 标 subtype(防 false-premise 类重占主导)、保留 answerable/insufficient paired family;
- 🟠 if_evidence_v2 方向批准,**暂不扩 2000**,先修两点:①wrong-span 加 correct-suggestion paired control(禁止 suggestion 全错);②conflicting-statement 改 correct/irrelevant/conflicting 三类,去掉 "Unverified note=always false" 固定捷径,冲突文本过语言质量检查;distractor 保留,正式 eval 用不泄露"恰一段相关"的 B 模板;
- ✅ FalseQA=premise_validity_aux、sycophancy=suggestion_pressure_aux 永久定格,不升格;
- 🔴 CREPE 仍不批扩产:先做 50 family passage-support 人审,<80% 支持则去 passages 降级 question+candidate selective revision;
- 🔴 K eval v1 不冻结:正式 500-family 版必须完全独立 distractor donor pool(donor 出自主评测 family 的做法废止);wc_attempt 改名 **wrong_candidate_citation**(除非加真 multi-hop chain);
- 交付纪律:下轮必须含 proto JSONL 本体、builder、scorer、更新后 canonical README——不接受只给 manifest+sample10;
- 并行许可:Answerability 扩产 ∥ Evidence 修完扩 ∥ Revision 暂停 ∥ IF Format+clean replay 按已批方案建设。
