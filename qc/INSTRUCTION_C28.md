# CC_INSTRUCTION_C28 — 2026-08-09 包审阅:80% 在线;防跑偏令与六处纠正(逐字要点存档)

裁决:主线没跑偏,但到了易跑偏节点。Reasoning 已够深;若 margin/Reasoning 小修小补继续膨胀而 K/IF/大评测/mixture 不落地,就滑向"GSM8K 单域剂量研究"。

**纠正**:①命名:3/4 intervention components(clean replay 是 control 不与 intervention 同级);②K 结论降级 preliminary cross-domain evidence(50 family 统计量;family 才是独立单位);③"判断坏了"证据不够——K candidate 必须补 decision/final/adoption/contract 全树拆解,禁拿 joint leaf 解释上层机制;④strict=0 是仪器报警(scorer/接口不适配),正式 K eval 前必须解决;⑤STATUS 饱和→K answerability 改 grounded answerability 设计(参数知识/相似实体/plausible candidate 防线);⑥token 口径统一:Primary controlled = assistant target tokens + optimizer updates 严格恒定;Logged nuisance = input/context seq tokens(记录+必要时敏感性检验);不得一处说四项恒定另一处说不可兼得;⑦q_d 为跨组件主 dose 轴(1620 vs 2000 禁止按条数横比);⑧margin 降级辅助(有空跑,不阻塞行为层/多域/mixture)。

**决策落定**:family overlap 不再等——pool-level 跨组件共享 source family **允许**;recipe/mixture-level 同 family 最多一个版本(禁重复加权)。不为不重叠去合成低质量题。

**优先级**:P0 = Reasoning eval-500+48ckpt 重评 / 冻结 K eval v1(补拆解+修 strict)/ 真正落地 General IF 数据;P1 = ANS 审核后跑曲线 / K与IF 各组件 {0,onset,high};P2 = mixture 开牌;P3 = margin。路线:single component → cross-domain → mixture prediction;Reasoning 只剩 answerability 和 eval-500 两个必要动作,然后收手。

**最看重**:K transfer matrix 把故事升级为"response 既依赖 dose 也依赖 domain;单域 optimum 可能在他域产生 collateral;recipe 必须基于完整 response vector+跨域 retention"。.62→.04-.14 若大评测后仍成立且拆清层级,可能比 format 饱和曲线更有论文价值——优先拆。
