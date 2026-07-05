# E5 仪器伪影报告 + v3 重定向(2026-07-07)

## 伪影(batch-4b 首轮 extract/sweep/align 全部作废)
- pre-repair 是 thinking 模式:strict judge 只解析 30%,有 w 的 parsed 幸存 **64/480**,
  且这 64 条 resist=100%(会写干净 JSON 的偏样)→ **resist=0 类几乎为空 → d=噪声** →
  sweep 四曲线全平(α=0 即"100%")、alignment 余弦全 ≈0——全是垃圾方向的下游。
  再生成与原预测逐字节一致,排除生成管线嫌疑。
- 更正一则前提:行为口径下 pre-repair resist=**93%**(224/16)——BIG_PICTURE 里的
  "resist 0.6→0.99" 中的 0.6 是 **floor 模型**的数字,不是 pre-repair 的。
- taxonomy 记两条:①strict 口径对 thinking 模式输出 = 幸存偏样仪器(与 F_judge 同族);
  ②预注册再次冻结了不适配的度量(R-23 第二例)。

## v3 重定向(qc 内公示,等价于 PREREG_steering 修订;预测本体不变)
- **被 steer 的模型 = 脊点 floor(scaffold_conv_e8)**:非 thinking、strict 全程可用、
  正是部署叙事("往交付物里注入决策,免重训")。resist₀=83%(strict,193/40;
  neg=40 为 LOWPOWER,如实披露,extract 硬闸 ≥30)。
- 预测 1 更新锚点:存在 (L,α) 使 floor resist 83%→**≥0.95**,且素题零出血、mute≤12%、
  A_latent 与 α=0 差 ≤5pp。预测 2/3/4(甜点+过冲、余弦排序、cos(d,ΔW_keeponly)<0)不变;
  align 的 ΔW 基准本就是 e8,自洽。
- 首轮产物移入 steering/out_void_v1/(留痕不删)。
