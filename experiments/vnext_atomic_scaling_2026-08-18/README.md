# vNext Atomic Scaling (C-48, 2026-08-18 overnight)

Exploratory branch `vnext-atomic-scaling`. Frozen paper evidence untouched.
Chain: Atomic Diagnosis -> Repair Scaling Laws -> Model Adaptation -> Constrained Optimal Prescription.

- code/: loss_extract.py (schema-exact teacher-forced NLL/margins), gen_predict_vnext.py (TP-param),
  base_profile.sh, build_para_pool.py, train_arm.sh, machine_worker.sh, launch_all.sh, make_queue.py
- Server base: /mnt/hdfs/xwqu/vnext0818/{queues,locks,logs,runs,profiles,pools}
- Machines: xwqu-m2/m3/m5/w-ad61 (8xA100-80G each), 2 workers x 4 GPUs per machine
- Models: Qwen3-0.6B/1.7B/4B/8B(anchor), Qwen2.5-7B, Llama-3.1-8B, Mistral-7B-v0.3 (download)
- Repairs: FMT/ANS/PARA/EVD/REV at {0, low, high} per model (D-phase doses)
