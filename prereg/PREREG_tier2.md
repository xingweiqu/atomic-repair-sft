# PREREG_tier2 — 可学性前沿逐档预注册(2026-07-08,本 commit 即时间戳)

> 依据 C-5.2/C-5.3 + R-9 + LOOP0 v2 指令 Loop 2B。训练前 commit。硬停 = 与本文件矛盾。
> **度量冻结(R-23)**:acc = 素题 marker("The final answer is N")精确匹配,全分母;
> answered-acc 并报;**A_OOD(tier) = acc(eval_ood) − zeroshot acc(eval_ood)**(能力主张判据);
> M 校准读数 = acc_id(poison_k) − acc_id(clean)。训练协议:e8(v5 等收敛),seed 42,超参沿账本冻结口径。

## 冻结预测(可学性前沿)
1. **干净闸门**:pre-repair zero-shot 在全部 8 个 eval 上 acc ≈0(≤5%)——发明运算不在预训练。
2. **档位 a(纯查表,flurm)**:eval-ID(未见组合)A≈0、eval-OOD A≈0(无结构可泛化;
   这是前沿的负锚点,不是失败)。
3. **档位 b(单步,zorp)**:**A_ID > 80pp 且 A_OOD > 50pp**(单步规则可泛化,Physics-of-LLM 先验)。
4. **档位 c/d(两步 quilt/三步 brame)**:A 随过程深度单调衰减:A_OOD(b) ≥ A_OOD(c) ≥ A_OOD(d);
   若 d 仍 >50pp,前沿比预期深,如实记(不触发硬停——C-5.3:硬停只在"与本预注册矛盾",
   单调性破坏才矛盾)。
5. **M 校准品(tier-b 毒数据)**:acc_id(poison10) − acc_id(clean) ≈ +10%×(1−acc_clean_id) 量级、
   poison30 ≈ 3 倍于 poison10——账本 M 读数随已知剂量近线性;OOD 不受毒(A_OOD 三者相当)。
## 主张形态(C-5.3 原文)
A 是一条随过程深度衰减的可学性前沿,GSM 级算术在前沿之外——而非 A 恒零。
