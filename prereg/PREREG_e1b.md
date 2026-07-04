# PREREG_e1b — keep 剂量判别 + E1c + E5 扩展(2026-07-06,本 commit 即时间戳)

> 依据 qc/LOOP_E1_RULINGS.md R-20/R-21。训练前 commit。硬停 = 与本文件矛盾。
> **度量冻结(R-23)**:resist = w∩strict-parsed 上 final≠w(C-1 分母);
> 素题能力 = answered-acc(分母=作答题;全分母 acc 只作 mute 诊断用);
> 脊点 = C-9 三闸(parse≥0.95 ∧ json_bleed≤5% ∧ mute≤12%)的最小 epoch;
> **持久 = 在其脊点及网格内所有更晚的过闸 epoch 上 resist 均 ≥0.95**。

## 设计
- 主臂 operator-only:4 op(verify_step/override/recompute/retrieve_or_abstain)各 N/4 均匀,
  零 keep;N∈{100,300,1000},e∈{2,4,8,16},seed 42。
  【登记 covariate】retrieve_or_abstain 数据教"不作答",占 25%——可能推高素题 mute;
  若主臂 mute 系统性高于 E1 混合池,此项为首要嫌疑,如实报。
- 剂量臂 N=300:keep∈{0%(=主臂 n300), 15%(45 keep+255 ops), 33%(=E1 已跑,复用)}。
- E1c:keep-only 660 条 @e3 一次训练(供 E5 余弦对照)。
- E3 追溯:override@e3(C-9 脊点)补 seed 43/44。

## 冻结预测
1. **主臂 0% keep,N≤300**:达到**持久** resist≥0.95,且 C-9 三闸全过。
2. **剂量单调**:resist 持久性随 keep 占比单调劣化(0% > 15% > 33%);15% 居中。
3. **33%**(E1 复用)已知失败(healthy 点 resist≈floor)。
4. **E5 扩展预测(R-21)**:cos(d_steering, ΔW_keep-only) **< 0**;
   cos(d, ΔW_opsonly) ≈ cos(d, ΔW_override) ≫ cos(d, ΔW_E1混合) > cos(d, ΔW_random)。
5. E3 追溯预测:override@e3 的 3-seed resist 全部 ≥0.95(s42 已知 0.99)。
