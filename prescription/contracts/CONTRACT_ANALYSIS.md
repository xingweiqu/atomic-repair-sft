# CONTRACT_ANALYSIS — 分析契约(lawv1;2026-08-04 draft;Gate-3 冻结)

> 原则:训练完成后 CC 不做任何"怎么画曲线"的判断——全部规则在此预先写死。
> 分析脚本 = prescription/lawv1_fit.py(fit_pilot 世系),先 commit 后运行。

## 1. 每 run 双 delta([FROZEN])

- Δs_e^base = s_e(component,n) − s_e(base);
- **G_{e,d}(n) = s_e(component,n) − s_e(replay-placebo)**(component-specific effect,law 只拟这个);
- placebo 用 3-seed 均值;单 seed 臂的 G 标注 single-seed。

## 2. 曲线拟合([FROZEN])

- 候选形态库:constant/null;linear in log n;saturating exp A(1−e^(−n/τ));threshold/step A·1[n≥θ](θ 稠密网格);rise-fall(log 二次)——**rise-fall 仅当有效剂量点 ≥6 时参与,否则跳过并申报**;
- 拟合:Huber(δ=.05)+ L-BFGS-B + 32 多初始化(fit_pilot 冻结做法);θ censored 时输出区间预测(NOTES_fit_pilot 教训 2);
- 横轴 = q_d(token 份额,dose_manifest 实测值);n_d 双轴标注;
- 评估(每条曲线全做,缺一不可):full LODO;interpolation 与 left/right extrapolation 分列;nearest-dose / linear / constant 三哑基线同表;**禁止只报训练误差**。

## 3. 不确定性([FROZEN])

- 层1:item-family bootstrap,B=2000,按 family_id 重采样(同 family 七版本永远绑定,绝不当独立样本);
- 层2:seed 变异 = 锚点 3-seed 全距(半距作噪声参照,figN 口径);
- 噪声阈值 τ_e(每 endpoint)= max(锚点 seed 半距, bootstrap 95%CI 半宽);Stage A 预测冻结 commit 时一并落值。

## 4. Onset 算法([FROZEN],禁止看图)

onset_d,e = 满足以下两条的最小剂量 n:
1. |Ĝ_{e,d}(n)| > τ_e(预注册噪声阈值);
2. 相邻更高剂量点方向一致(sign(Ĝ(n)) == sign(Ĝ(n_next)))。

无满足点 ⇒ 输出字面量 `no detected onset within tested range`。
plateau = 首个满足 |Ĝ(n_next)−Ĝ(n)| < 0.5·τ_e 且已过 onset 的 n;high = 最大预注册剂量(2000)。
(Stage B 的 n_onset/n_high 即由此机械得出,PLAN §5。)

## 5. Mixture 具体化([FROZEN] 公式,数值由 Stage A 曲线代入自动生成)

六臂定义见 UTILITY_AND_BASELINES §3;生成脚本 lawv1_mix.py 输出确定 yaml,例:

```yaml
uniform:            # Q* 均分示意(实际 Q* 由 r* 解出)
  evidence: 250
  revision: 250
  answerability: 250
  format: 250
  replay: 1000
```

全部六臂 yaml + 全 endpoint 加性预测在 mixture 训练前冻结 commit(预注册节点5);人工看结果配比 = 违约。

## 6. 报告规约([FROZEN])

- 一切图表:q_d 主轴、单 seed 星标、adaptive 点空心标、placebo-adjusted 与 vs-base 双列;
- 每张图脚注:数据文件路径 + seed 标注(FIGURE_STYLE 沿用);
- 预测 vs 实测表:blind error 与噪声阈值 τ_e 同列并排;
- 三态标注:preregistered / amended / exploratory。
