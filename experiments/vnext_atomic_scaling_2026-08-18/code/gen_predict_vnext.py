#!/usr/bin/env python3
"""lawv1 generation runner (CONTRACT_EVAL §1 frozen config).

Usage: python3 gen_predict_lawv1.py <eval_jsonl> <out_jsonl> [model_path]
Greedy, thinking off, max_new_tokens 512, chat template from tokenizer.
Output rows: {family_id, condition, output}
"""
import json, sys
from vllm import LLM, SamplingParams
from transformers import AutoTokenizer


def main():
    eval_path, out_path = sys.argv[1], sys.argv[2]
    model = sys.argv[3] if len(sys.argv) > 3 else "/mnt/hdfs/xwqu/Qwen3-8B"
    MAXLEN = int(sys.argv[4]) if len(sys.argv) > 4 else 4096   # amendment 2026-08-11: K-500 long contexts need 8192

    rows = [json.loads(l) for l in open(eval_path)]
    tok = AutoTokenizer.from_pretrained(model, trust_remote_code=True)
    def _chat(p):
        for kw in ({"add_generation_prompt": True, "enable_thinking": False},
                   {"add_generation_prompt": True}, {}):
            try:
                return tok.apply_chat_template([{"role": "user", "content": p}], tokenize=False, **kw)
            except (TypeError, ValueError):
                continue
        raise RuntimeError("chat template failed")
    prompts = [_chat(r["prompt"]) for r in rows]
    llm = LLM(model=model, tensor_parallel_size=int(sys.argv[5]) if len(sys.argv)>5 else 1, gpu_memory_utilization=0.90,
              max_model_len=MAXLEN, enforce_eager=False)
    sp = SamplingParams(temperature=0, top_p=1.0, max_tokens=512)
    outs = llm.generate(prompts, sp)
    with open(out_path, "w") as f:
        for r, o in zip(rows, outs):
            f.write(json.dumps({"family_id": r["family_id"], "condition": r["condition"],
                                "output": o.outputs[0].text}, ensure_ascii=False) + "\n")
    print("GEN_DONE", len(rows))


if __name__ == "__main__":
    main()