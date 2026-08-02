# SERVER_OPS — 服务器运维手册 + 踩坑总账(2026-07-09,xwqu-lq 首日实录)

> 新机器 bring-up 照 §1 抄;每个坑都是真实事故,规则用血换的,别删。

## 1. 新机器 Bring-up 清单(复制粘贴级)

```bash
# ~/atomic_env.sh —— 所有脚本第一行 source 它
export http_proxy="http://sys-proxy-rd-relay.byted.org:8118"
export https_proxy="http://sys-proxy-rd-relay.byted.org:8118"
export no_proxy="byted.org"
export PATH="$HOME/.local/bin:$PATH"
export DISABLE_VERSION_CHECK=1          # LF 自己的检查开关(transformers 的检查它管不了,见坑#2)

repo_sync() {  # 服务器仓库 = 可丢弃检出;同步一律 reset --hard(见坑#4)
  cd /opt/tiger/atomic-repair-sft-github || return 1
  git fetch -q origin gain-accounting-v1 || return 1
  git reset --hard -q origin/gain-accounting-v1 || return 1
  git clean -fdq probes/gen 2>/dev/null
  echo "synced: $(git rev-parse --short HEAD)"
}
```

```bash
# 仓库 + LLaMA-Factory
cd /opt/tiger && git clone -b gain-accounting-v1 https://github.com/xingweiqu/atomic-repair-sft.git atomic-repair-sft-github
git clone --depth 1 https://github.com/hiyouga/LLaMA-Factory.git && cd LLaMA-Factory && pip3 install -e . --no-deps

# 依赖围栏(vllm0.12/torch2.9 原生栈 vs LF 保守 pins,四连降 + matplotlib;一次装齐)
pip3 install "datasets==4.0.0" "trl==0.24.0" "peft==0.18.1" "accelerate==1.11.0" matplotlib fire omegaconf
# transformers 4.57.3 可用(LF 只禁 ==4.57.0);vllm/torch 不许动
```

跑法:**训练** `FORCE_TORCHRUN=1 NPROC_PER_NODE=8 llamafactory-cli train cfg`(每 run 独占 8 卡);
**predict/推理** `unset FORCE_TORCHRUN NPROC_PER_NODE; CUDA_VISIBLE_DEVICES=$g ...` 按卡分片;
全部**在仓库目录下执行**(configs 的 dataset_dir 是相对路径,坑#1)。

## 2. 踩坑总账(症状 → 根因 → 铁律)

| # | 事故 | 根因 | 铁律 |
|---|---|---|---|
| 1 | predict 找不到 dataset_info(RUNBOOK 首版) | `cd $LF` 后相对路径解析错 | llamafactory-cli 一律在**仓库目录**下跑 |
| 2 | 训练全败 datasets/trl/peft/accelerate/matplotlib 五连 | LF 版本围栏(§1);`DISABLE_VERSION_CHECK` 只管 LF 不管 transformers 自己的 require_version | 新机器先装 §1 围栏,别一个个撞 |
| 3 | **pkill 自杀 ×3**(ssh 会话被自己 kill) | pkill -f 的 pattern 或命令串里的**真实文件名**匹配了 ssh 自身 cmdline;括号技巧 `[t]` 只护 pattern,护不住同串里的 launch 路径 | **kill 与 launch 永远分两条 ssh**;kill 串里不得出现任何真实脚本名 |
| 4 | git pull 反复 Aborting + **对旧树抢跑 nohup** | 服务器工作树有未跟踪/已改文件;`pull && nohup ... &` 在 pull 失败时照样启动 | 服务器 repo=可丢弃检出:`repo_sync`(fetch+reset --hard);**launch 前必须校验 HEAD** |
| 5 | 8 个 vllm shard 静默全崩,探针文件被写空 | `probes/profile.py` 遮蔽 stdlib `profile`(`python3 probes/x.py` 把 probes/ 放进 sys.path[0]),torch→cProfile→炸 | **模块名禁与 stdlib 重名**;产量闸门(kept<200=FAIL)防静默空产出 |
| 6 | "4900 条生成 3 分钟跑完" | 崩溃被 continue 吞掉 | **不可能的速度=事故信号**;每阶段报产量并设下限闸门 |
| 7 | `9e999` OverflowError ×3(pass8→profile_classify) | 模型输出天文数字,`int(float(inf))` | 数值归一只用 `textlint.numnorm`(带 finite 护栏),禁止再写裸版 |
| 8 | think 残渣污染探针文本 100/100;pass8 v1 难度桶被 thinking 截断灌水 | Qwen 思考模式残留(同族两次) | **LLM 生成文本入数据前必过 `textlint.lint`**;推理加 `/no_think`;预算 2048 |
| 9 | `overwrite_output_dir: true` 被 regex 改成路径 | `re.sub(r'output_dir:...')` 未锚定行首 | config 改写 regex 一律 `(?m)^field:` 行首锚定 |
| 10 | W2 重跑把 P/R/S 输出顶掉 | 两批 rerun 写同名 shard 文件 | **每个 rerun pass 独立 outdir**(out2/prs、out2/w2) |
| 11 | scp 大目录被本地 2 分钟超时掐断 | Bash 工具默认 timeout | 大传输用 run_in_background,或服务器端收集+commit+push 回传 |
| 12 | datasets≥3 拒载 LAMA(script 数据集) | datasets 3.0 弃用 dataset scripts | 老基准直接 curl 官方 zip(kcor loader 模式) |
| 13 | S 探针被自家闸门砍 85% / "编号 vs 禁数字"自相矛盾 | 口径写死前没跟生成格式对齐 | validator 与 prompt 同评审;砍 >30% 时先怀疑口径再怀疑模型 |
| 14 | fixw2 重跑清空重跑清单 | 幂等性没设计 | 增量文件一律 union 合并,不覆盖 |

## 3. 监控纪律

- Monitor 的 grep 必须**覆盖失败态**(FAIL/Traceback/GATE),只抓成功=静默崩;心跳带 GPU 占用。
- 收割前必验:目录数、行数、engine 标记;server commit 逐个 `diff-tree` 验干净度(只许数据文件)。
| 15 | 新脚本 launch "No such file"×2(P0c 两次) | push 后未先 sync 就 nohup;脚本内置自 sync 够不着自己 | **launch 铁律:同一条 ssh 里 sync-verify-launch**;新分支首次跑必须显式 checkout -B |
