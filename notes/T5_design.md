# T5 功效版设计稿(零训练;依赖已解锁:合并池难桶 569 题)

- **目的**:堵 "A≤0" 的镜像漏洞——在 pre-repair **做不出**的题上,修复 ckpt 是否解出新题。
- **题集**:合并池 pass@8=0 的 477 题(gsm 37 + gsmhard 440),素题体裁。
- **条件**:pre-repair / scaffold_conv_e8 / targeted_override@e3 / opsonly_n300(E1b 后)/
  actionized_full——全部素题 greedy 一次(与 transfer 同款 prompt/预算 2048)。
- **度量(冻结)**:solve rate = 素题 answered-acc 与全分母 acc 双报;
  预测(挂 PREREG_e1b 预测 3 的镜像):全部 ckpt solve rate ≈ pre-repair ≈ 0(±2pp)——
  修复不解新题;若某 ckpt >2pp,硬停报告(那是 A>0 的位置)。
- **成本**:5 ckpt × 477 题 predict,单卡插空;数据文件本地可生成(pass8_merged 已在库)。
- 状态:设计稿;等 Xingwei 点头后出 configs+预注册补条目。
