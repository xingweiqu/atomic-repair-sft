# RUNBOOK batch-1 — 服务器三件事(T4 判决 + pass@8 + R-8)

> 依据:qc/LOOP1_RULINGS.md(T4、D-7、R-8 同批)。
> 标准:`git pull` 后**不改任何文件**按顺序复制粘贴。每步给预期产物与失败自查点。
> 前置:`cd <repo> && git checkout gain-accounting-v1 && git pull`。
> **所有 llamafactory-cli 命令都在 <repo> 目录下执行**(configs 用相对 `dataset_dir: ./data_vX`,
> 与历史脚本 run_v4_20 相同姿势;不要 cd 进 LLaMA-Factory 目录)。predict 前照历史脚本做环境准备:
>
> ```bash
> unset FORCE_TORCHRUN NPROC_PER_NODE
> export CUDA_VISIBLE_DEVICES=0   # predict 单卡即可
> ```
>
> 【勘误 2026-07-03】首版此处误写 `cd $LF`,导致 dataset_info 相对路径找不到(codex 按红线
> 停下报告,正确)。configs 本身无误、未改动。

## Job 1 — T4 素题判决(2 条 predict,~几分钟)

```bash
cd <repo>
llamafactory-cli train configs/v4/t4_plain_scaffold_conv_predict.yaml
llamafactory-cli train configs/v4/t4_plain_prerepair_predict.yaml
```
- 预期产物:`/mnt/hdfs/xwqu/gsm-repair-v4/output/predict_t4_plain_{scaffold_conv,prerepair}/generated_predictions.jsonl`(各 **28 行**)。
- 自查:行数≠28 → 数据集没注册,确认 `data_v4/dataset_info.json` 里有 `v4_t4_plain_probe`(本分支已含,pull 即有)。
- 判读(回传后本地做,勿在服务器解读):素题恢复→H2;素题同样错→H1。

## Job 2 — pass@8 分桶测量(先 500 校准,再全量)

```bash
cd <repo>
python3 scripts/pass8_gsm.py --model /mnt/hdfs/xwqu/Qwen3-8B --limit 500 --out data_v4/pass8_calib500.jsonl
# ↑ 回传 calib500 给本地标定桶边界后,再跑全量:
python3 scripts/pass8_gsm.py --model /mnt/hdfs/xwqu/Qwen3-8B --out data_v4/pass8_results.jsonl
```
- 预期产物:jsonl,首行 header(温度 0.7/top_p 0.8/top_k 20/seed 42/k 8,写死于脚本 = D-7(ii))。
- 自查:vllm 不在环境 → 脚本自动降级 transformers(慢,500 题可接受;全量建议装 vllm)。
- 纪律:pass@8 只做**分桶变量**;修复评测仍 greedy 单次,两种 regime 不混(D-7(iii))。

## Job 3 — R-8 v2.1 补地板(1 条 predict)

```bash
cd <repo>
llamafactory-cli train configs/v2_1/factonly_on_v21_predict.yaml
```
- 预期产物:`/mnt/hdfs/xwqu/atomic-repair-sft-v2_1/output/predict_factonly_on_v21/generated_predictions.jsonl`(**600 行**)。
- 自查:模型路径是 `output_v2/inject`(v2 的知识地板 ckpt);若目录被清理,先按 v2 configs 重训 inject(不太可能,HDFS 持久)。

## 回传清单(拷回本地仓库对应路径后告知 CC)

| 产物 | 放到 |
|---|---|
| predict_t4_plain_scaffold_conv/generated_predictions.jsonl | `data_v4/predict_outputs/predict_t4_plain_scaffold_conv/` |
| predict_t4_plain_prerepair/generated_predictions.jsonl | `data_v4/predict_outputs/predict_t4_plain_prerepair/` |
| pass8_calib500.jsonl(先)/ pass8_results.jsonl(后) | `data_v4/` |
| predict_factonly_on_v21/generated_predictions.jsonl | `data_v2_1/predict_outputs/predict_factonly_on_v21/` |

回传后本地动作(CC):T4 判读 → R-5 命名裁决材料;pass@8 → Loop 2A 桶边界 + T5 在难题桶复测;
R-8 → v2.1 七行转细账、账本重建。

---

## batch-1b(增补 2026-07-04)— pass@8 校准重跑(v2 脚本)

v1 calib500 疑受 thinking-模式截断污染(见 qc/LOOP1_5_T4_VERDICT.md §4),脚本已升 v2
(/no_think + max_tokens 2048 + 首 20 题原样本 sidecar)。重跑:

```bash
cd <repo> && git pull
python3 scripts/pass8_gsm.py --model /mnt/hdfs/xwqu/Qwen3-8B --limit 500 --out data_v4/pass8_calib500_v2.jsonl
```

- 预期产物:`data_v4/pass8_calib500_v2.jsonl`(501 行,header 含 "version": 2、"no_think": true)
  + `data_v4/pass8_calib500_v2.samples20.json`(验尸用原样本)。
- 回传:两个文件放 `data_v4/`,单独 commit,message 固定
  "server: batch-1b pass@8 calib500 v2 (no_think)",只含这 2 个文件。
- 全量 1319 仍等本地确认桶边界后另行指令。
