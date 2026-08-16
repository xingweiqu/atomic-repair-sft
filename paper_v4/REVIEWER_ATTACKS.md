# REVIEWER_ATTACKS — 苛刻审稿人攻击面(≥10)与当前可答程度

1. **只有 4 个 intervention family,凭什么代表 SFT 数据空间?**
   可答:定位为 "representative, controllable"(可 matched control、可分剂量、有 paired endpoint、可跨域实例化),明确不声称覆盖;taxonomy 表列入选标准。承认 limitation:结论限于此类可控干预。不补实验。

2. **只有一个 held-out family(Llama),怎么排除巧合?**
   可答:预注册+冻结时序+4/4 排序+min>max 的 seed 分离,使"巧合"需要同时命中 4 个次序与三条约束;措辞严格用 cross-family evidence。承认:universality 需要更多 family,列为 future work。不加第三模型(会破坏冻结结构,且 C-38 定案)。

3. **这真是 scaling law 吗?**
   可答:论文明确不 claim 经典 loss power law;framing = local response laws + conditional composition;LODO 显示局部可预测性优于哑基线。标题不含 scaling laws。

4. **U 是不是设计出来让 predicted 赢的?**
   可答:U 层级与 branch primary 在 Qwen mixture 前冻结(C-34#4 commit 在案),Llama 阶段未改;同一 U 下 Qwen 预测臂**输了**(uniform 第一)——若 U 为内定胜利而设计,开发集不会失败。附录给替代聚合的敏感性(仅重新汇总,不新训)。

5. **diversity threshold 是 post-hoc 的。**
   可答:如实承认在 Qwen 上是 rescue 发现(post-hoc discovered correction),这正是设置 Llama 前瞻检验的原因;Llama 上它是冻结假设的一部分并经受住检验。措辞:observed regime,非 law。承认:阈值分辨率粗(300/600/1200 三点)。

6. **两个 calibration run 是不是变相调参?**
   可答:calibration 规则(用哪两个 run、公式、搜索空间)在任何 Llama 数据前冻结并 commit;calibration 输出单一标量 scale=.376;base profile 输入白名单防第三通道。承认:scale 转移是 deliberately low-dimensional,不声称最优。

7. **predicted 赢是不是只因为 ANS 权重大 / ans_R 剂量大?**
   部分可答:predicted 与 heuristic 都重仓 answerability(pred ans 总量 480+…,heuristic 1200 全 ans),但 heuristic U 仅 .340——单纯堆 ANS 不赢;赢的配方=ans_R 侧重+六格覆盖,正是修正模型的两个结构。剩余暴露:branch 均权下 answerability 的可涨空间最大,承认为 U 设计的讨论点(见 #4 敏感性)。

8. **uniform 的 K-original 崩塌是不是评测/数据问题造成的不公平?**
   可答:同一冻结 K 池、同一预算、同一步数;pred/heuristic/replay 的 K-orig 都在 .60-.79,唯 uniform .463——是配方效应而非仪器;且这正是论文论点(盲目均匀有隐藏代价)。附录给 uniform 的 per-branch 拆解。

9. **幅度校准明明不准,凭什么叫 prediction?**
   可答:预注册判据是 ranking+约束+decision usefulness,全部通过;幅度低估如实报告且有结构(多样性收益被低估最多)→ 列为 open modeling problem。措辞已按 C-38 锁死。

10. **这套流程真的比直接 grid search 省吗?**
    部分可答:held-out 阶段成本=base profile+2 calibration+1 recipe 训练 vs 盲试 K 个 mixture(每个全训+全评);发现阶段贵但一次性、可摊销到新模型。承认:未做正式 compute-matched 对比,写成成本讨论不写成实验 claim。

11. **529-family 评测仍是合成扰动,外部效度?**
    可答:SVAMP 外部持出全臂无剂量性下滑;IF 域用真实数据源(SQuAD2/CREPE/AGNews);承认:deployment-style 自然压力测试未做(改名教训已吸收),列 future work。

12. **单 seed 的 K/IF 稀疏读数可靠吗?**
    可答:标注 direction-grade;关键结论(KRV 反转)做了 3-seed targeted replication,不复现的(KAN retention)已撤回——展示了自我纠错;其余单 seed 结论不进主 claim。

13. **撤回这么多,前期结论还能信吗?**
    转为优势:撤回全部由更大评测触发且有台账,"small evals manufacture false curves" 本身是贡献#13;终局主张全部建立在 529-fam/多 seed/预注册层。
