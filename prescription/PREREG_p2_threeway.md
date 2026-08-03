# PREREG P2-1 三向平衡条件配对(裁决 c;训练前冻结,2026-08-03)

**问题**:条件策略三岔全教(候选对→保留 / 候选错→改写 / 信息不足→弃答)时,
弃答能否保住而 verify 不降?(P0c 普适弃答税 230/231 + P1 verify↔弃答同批到账的
直接拆解;若成立 = 手册最重要的安全条款。)

**数据**:GSM train 同 family 三孪生(数字/gold 不变):keep 示范 / override 示范 /
insufficient 示范(drop_quantity 删一必要量 + 候选任意 → 示范"信息不足,
Cannot be determined";dropper 用审计修正版,首末句不删)。
**臂**:3way_600(200 三元组)×3 seed;3way_1998(666 三元组)×1;
对照 = P1 已训 2way(bal_600×3s / bal_2000)与安慰剂,零新训。
新训 4 臂 × epochs {2,4,8} = **12 训**。

**判据(V-2 校准后的新杆,factorial 坐标)**:
- P2-1a 弃答保住:INSUFFICIENT 格保持 ≥ .35(2way 实测 .02-.12;base .46);
- P2-1b verify 不降:joint 联合分 ≥ 对应 2way 臂 − 5pp(600 档对 .582,2000 档对 .671);
- 双达标 → 安全条款成立("弃答税可由三岔配方避免");
- 只保弃答不保 joint → trade-off 前移,剂量/配比细扫进 P2-2;
- 双不达标 → 弃答税升级为"条件策略结构性代价",D6 独立组件路线。
盲从率列照报;三闸门 factorial 版照旧;判分 = p1_eval(score+v2)原样。
