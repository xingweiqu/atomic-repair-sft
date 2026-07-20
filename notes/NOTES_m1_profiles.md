# M1 三模型画像对照(C-14;2026-07-13)

> 冻结分类器 + 各模型原生 chat template;含 mixed 归属口径(inclusive)。
> 数据:probes/out_mm_local/profile_*.json + probes/out(Qwen3-8B 基准)。

| 桶(gsm 池,%) | Qwen3-8B | Qwen3-4B | Llama-3.1-8B |
|---|---|---|---|
| ok(稳健) | 60.6 | 58.9 | 35.4 |
| conduct 轻信 | 16.4 | **33.0** | 24.7 |
| format | 14.7 | **0.5** | **23.7** |
| phrasing | 6.4 | 4.9 | 8.2 |
| unresolved | 1.9 | 3.3 | 5.5 |
| hard 池 unresolved | 86.3 | 88.5 | 92.3 |

仪器闸门:F schema 合法率 .92-.98 全过;**Llama O_answered=.715 仪器注**
(最终答案 marker 依从率低,部分"失败"含 marker 不依从成分——按闸门列
如实入表,不改判)。

## 预测判分
- **P-M1-1 HIT(远超阈值)**:格局随模型剧变——4B 轻信翻倍(33.0)但 format
  病灶消失(0.5);Llama format 病灶反而最重(23.7)且稳健分掉到 35.4。
- **P-M1-2 HIT**:三模型 ok 桶全部 < surface score。

正文一句(按 C-14 措辞):the diagnostic instrument is model-agnostic;
profiles differ by model, which is the point——并且差异直接改写处方:
4B 的购物清单不含 format 组分,Llama 的清单 format 权重最大。

## C-16 G1 追加:Mistral-7B-v0.3 画像(2026-07-20)

| 桶(gsm 池,inclusive %) | Qwen3-8B | Qwen3-4B | Llama-3.1-8B | **Mistral-7B** |
|---|---|---|---|---|
| ok | 60.6 | 58.9 | 35.4 | **5.5** |
| conduct | 16.4 | 33.0 | 24.7 | 22.0 |
| format | 14.7 | 0.5 | 23.7 | 20.3 |
| phrasing | 6.4 | 4.9 | 8.2 | **18.3** |
| unresolved | 1.9 | 3.3 | 5.5 | **27.6** |

仪器注:O_answered .606(marker 依从率低,同 Llama 症状更重,闸门列如实);
F_valid .93 过闸。**四模型画像谱系完整**:能力越弱 unresolved 越大、
接口病谱系随家族剧变——"仪器 model-agnostic,画像随模型变"的第四例证。
