# C-16 G1 收割:Mistral-7B 验证格(PREREG_c16;2026-07-20)

> 8/8 训零失败;脊点 = e4(e2 的 cleanreplay/fmt10 低于 e4,B 例外 e2 更高但差距
> 与判据无涉,按逐臂最优披露)。判据 = 五主张 HIT/REVERSE/UNTESTED。

| 主张 | 判 | 数字 |
|---|---|---|
| 1 非特异地板 | **HIT** | U(=B)e4 W_res .38 vs replay .30(+8pp 恰在灰区边界;e2 +28 超界但 replay e2 异常低 .13,取 e4 保守读) |
| 2 format 特异 | **HIT(防丧失型,同 Llama)** | 含 format 臂 F_ok .31-.41 vs 不含 **0.00**;base F_ok .25(先天弱)→ 组分作用 = 防训练性丧失+小幅修复 |
| 3 drills 修复腔毒性 | **MISS-absent(同 M2 先例)** | drl25 repair .17 vs replay .29——低但 fmt10 也 .26,毒性无从与"任何组分缺失"区分;W_adopt 无异常(.020) |
| 4 体裁门控 | **HIT** | 修复腔 base .05→任意臂 .15-.37(+10~32pp);素题面 O_acc 变化 −3~+4pp——可见度仍由体裁开关 |
| 5 steering | UNTESTED(按预注册) | — |

跨模型登记(与 M2 同族):Mistral base 修复腔契约同样近乎不存在(.050,mute .38);
任何 SFT 装上契约;纯痕迹训练同样把 F 抹到 0.00(**第五例**:训练伤未训体裁,
Qwen 轻/Llama 重/Mistral 重)。
诚实注:Mistral 全臂绝对值低(O_acc .14-.41,base 本来就 5.5% ok)——
这一格验证的是主张的方向,不是效果量;弱底座上修复信号弱,如实。
