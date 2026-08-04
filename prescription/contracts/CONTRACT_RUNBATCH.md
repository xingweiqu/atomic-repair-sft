# CONTRACT_RUNBATCH — 跑批与验收契约(lawv1;2026-08-04 draft;Gate-3 冻结)

## 1. RUN_MATRIX([FROZEN] 生成规则;CSV 本体 = Gate-3 产物)

CC 只执行冻结的 `prescription/lawv1/RUN_MATRIX.csv`,由 `lawv1_matrix.py` 机械枚举生成(不手编):

| 列 | 规则 |
|---|---|
| run_id | `A-{COMP4}-{DOSE:04d}-S{seed}`(如 A-EVID-0030-S42;placebo=A-PLAC-0000-S42;自适应加 `-ADP`;重跑加 `-R1/-R2`) |
| model | Qwen3-8B(M6 阶段另表 B-…) |
| component | evidence / revision / answerability / format / placebo |
| dose / replay | n_d 与 2000−n_d 对应条数(token 账在 data_manifest) |
| seed | 按 CONTRACT_TRAIN §5 |
| data_hash | 该臂训练 jsonl 的 sha256 |
| config_hash | 渲染后 train yaml 的 sha256 |
| eval_hash | 评测套件冻结 hash |

Stage A 枚举 = 4 组件×7 剂量×S42 + 锚点 {240,2000}×S43/44 + placebo×3 seed = **47 行**(+自适应 ≤8 行后补,单独 section 标 ADP)。

## 2. 每 run 必产文件([FROZEN];全齐才算完成)

```
runs/<run_id>/
  run_manifest.json        # 身份+token 账+updates+偏差记录
  train_config.yaml        # 渲染后实际所用
  data_manifest.json
  train_log.jsonl
  checkpoint_hash.txt      # sha256(model.safetensors.index.json)
  generation_config.yaml
  predictions.jsonl        # 逐题原始输出,含异常
  scores_by_item.jsonl
  scores_summary.json
  continuous_metrics.parquet
  environment.txt          # pip freeze/torch/cuda/hostname/model hash
  git_commit.txt
  DONE                     # 仅 validate_run.py 通过后写入
```

`validate_run.py`(Gate-2 交付):检查 12 文件齐全、predictions 行数==评测集行数、
scores_summary 字段齐、token 账在容差内;通过才写 DONE。**无 DONE 的 run 不进任何分析。**

## 3. 失败处理([FROZEN];总原则:不静默覆盖,不自动挑最好的一次)

| 事件 | 判定 | 处置 |
|---|---|---|
| OOM | 训练进程 CUDA OOM | 允许 micro_batch 4→2 且 grad_accum 4→8(global batch 不变=128)重跑一次;新 run_id `-R1`;偏差写 run_manifest;再 OOM ⇒ 该 run 标 FAILED,上报 |
| loss spike | 连续 ≥3 个 logging 点 loss > 前 10 点中位数×3 | 跑完不中断;run 标 QUARANTINE 入 manifest,曲线拟合默认剔除并申报(不静默剔) |
| NaN loss | 任一 logging 点 NaN | run 作废;同 config 重跑一次 `-R1`;再 NaN ⇒ FAILED 上报 |
| ckpt 损坏 | cp 后 config.json/safetensors 缺失或 hash 不符 | 先重 cp;仍坏 ⇒ 允许同 config 重训一次 `-R1` |
| 评测崩溃 | vllm/scorer 异常退出 | 评测可重跑任意次(推理确定性);predictions 不完整绝不截断入库 |
| 中途改 lr/超参 | — | **绝对禁止**;任何 config 改动 ⇒ 新 run_id + amendment 记录 |
| 重跑 | 一律保留原始失败 run 目录(改名 `<run_id>.failed/`),不覆盖 |

## 4. 跑批脚本

`scripts/run_lawv1.sh <machine_idx> <n_machines> <section>`(run_p2a.sh 世系:HDFS done-marker 仅 nfail==0 时写;本地盘训练;config.json 存在性跳过;禁 pkill 自杀模式)。section ∈ {smoke, stageA, stageB, mix, newmodel}。

## 5. Gate 执行顺序([FROZEN];对应 INSTRUCTION_C21)

- **Gate 1(零 GPU 可做大半)**:Reasoning 数据源决策确认 + 7×50 评测原型 + 4×200 训练原型 + scorer 单测 + 人工审计报告;base profile 与模板审计初测需 GPU(机器复活后 0 训练、纯推理)。→ **用户确认后才扩产**;
- **Gate 2(3 train)**:S-PLAC-0000 / S-EVID-0060 / S-EVID-2000 三个 smoke run 全链路(build→train→ckpt→gen eval→NLL/BPB→score→curve input);核验 loss mask(label≠-100 计数)、token 账、渲染一致性(训练 vs 评测逐 token diff)、12 文件齐、成本实测;
- **Gate 3(冻结 commit)**:数据 hash + config hash + eval hash + scorer tests + RUN_MATRIX.csv + GPU-hour 实测重估 → 预注册 commit → 才准启动 Stage A 正式网格。
