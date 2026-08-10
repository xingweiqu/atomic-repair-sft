# CC_INSTRUCTION_C33 — GPU 永不主动空转执行策略(2026-08-11,常设法典,逐字存档)

总原则:只要集群存在可用 GPU 且无 hard stop,持续把已批准、科学上有效的任务自动排满;单 branch 等审核只冻结该 branch,不问"要不要继续";GPU 连续空闲>10 分钟且 approved queue 非空 = scheduling failure,自动修正。**"GPU 打满"是调度目标,但不能反过来驱动科学设计。**

## 队列分层
- **P0 已批正式训练**:ANS(审核过即跑)/K sparse(spec 冻结即排)/IF sparse(数据冻结即排)/mixture(预测冻结后)/held-out;合法 run 全并行铺;
- **P1 正式评测**(与训练并行,ckpt 即产即评):eval-500 补评/K 跨域/IF 跨域/SVAMP-StrategyQA 持出/缺失 endpoint 补评/seed-paired 评测;
- **P2 已批辅助**:margin v2(仅过审版)/target-NLL/BPB/ckpt 诊断/scorer 压力测试;只填空闲不抢 P0/P1;
- **P3 安全预计算**:已批 builder 小 smoke/token 统计/validator/self-test/推理缓存。禁止为吃卡创造新研究问题。

## 等审处理
ANS 等审→跑 K/IF eval、跨域、margin、补评;K spec 等→不跑 K train 但 IF/ANS/eval 继续;IF Evidence 等→只冻该池,已批 Answerability/Format/replay/eval 照跑;Revision gate 等→单独冻结。

## 自动补位
维护 TRAIN_QUEUE/EVAL_QUEUE;job 完成→先补训练→无则拉评测→再无拉辅助→真无 approved 任务才准空闲;不等整批结束,ckpt 出即入 EVAL_QUEUE;评测积压时临时转卡,清完回训。目标:**fleet 永远优先被当前最有科学价值的 approved workload 占满。**

## 禁止(为利用率不得做)
擅自加 dose/加 seed/改 LR-scheduler-max_steps/改 scorer/改 endpoint/改 split/降审核 gate/把未批 prototype 当 formal/自创 component/把 K-IF 缺口换回 GSM8K/因 OOM 改 exposure。OOM 仅准:降 microbatch+同比升 accum,global batch/updates/LR/data/exposure 不变,自动重试一次。

## 允许自动
冻结网格内启动下一剂量/预注册 seed set 内下一 seed/ckpt 出即评/failed run 迁移机器/训评动态分卡/基础设施故障重跑一次/CPU builder-audit-plotting 与 GPU 并行/更新 manifest 与状态文件。

## Hard Stop(仅冻结受影响 branch)
撞族/hash 不匹配/预算超容差/scorer self-test 挂/NaN-loss 爆-坏 ckpt/同配置两次基建失败/builder 达不到冻结样本量或质量 gate/评测丢行-工件不全/需人工构念审核未批。

## 当前科学优先级(不加 Reasoning 花活)
ANS → K formal/跨域 eval → IF formal eval → K/IF sparse training → mixture → held-out。R 域三组件只做补评与分析。ANS/K/IF train 全被审卡住时,用 48+ ckpt 持续做 K/IF/eval-500/持出/margin-v2 填卡。

## 汇报纪律
不为汇报停任务;仅在 组件网格完成/域 formal eval 完成/sparse pilots 完成/mixture 开牌/held-out 完成/hard stop 时主动报;格式:completed-running-queued-blocked/GPU busy-total/失败与重试/最新正式结果/下一批已自动启动。

**最高硬原则:只要存在 approved GPU workload,不让用户看到空 GPU;等待决定只阻塞需要该决定的 branch,不阻塞整个实验系统。**
