# PREREG Phase-1 D4 平衡条件对照(草稿;训练前定稿冻结)

**设计**:同题配对生成——每底题出两个变体:候选答案=gold → PRESERVE 示范
("verify: 候选正确,保留");候选答案=错值(w>0, w/gold∈[0.2,5]) → OVERRIDE 示范
("verify: 候选错误,改为 gold")。50/50 严格平衡,配对同题(数字/gold 不变)。
N∈{300,600,2000};3 seed @600;epochs {2,4,8};脊点=factorial 三闸门版。
**对照臂**:纯 override(Paper 2 赢家 targeted 配方)/ 纯 keep(旧反向臂)/
非配对混合(旧 E1 池重训或复用封箱 ckpt 重评)。
**评测**:16 格 factorial(P0b)重点 VERIFY×{INCORRECT,CLEAN} 四格 +
retention 全家桶;主读数 = override 率(候选错时)与 keep 率(候选对时)。
**预注册二分(两个结局都是手册第一条)**:
- 结局 A:平衡配对 override≥90% ∧ keep≥安慰剂 → "keep–override 结构互斥"降级为
  "非条件混合的伪影"(条件策略可教),处方第一条 = 教条件策略,不是二选一;
- 结局 B:平衡配对仍塌一头(任一 <阈)→ 干涉为真 trade-off,Type D 路由
  (steering/模块化)进处方第一条。
灰区/故障态/硬停:与判据矛盾即停;判分器沿冻结 strict 家族 + 非 dict 守卫。
