#!/usr/bin/env python3
"""Assemble six frozen mixture arms (C-34#7). Run on server (tokenizer).

Inputs (repo): MIXTURE_SPEC_FROZEN.json + three domain replay pools + fmt/ans pools.
Composition per arm: domain replay prefixes + component-pool nested prefixes.
All arms: identical example budget (2000) and ONE shared max_steps (max packed est).
Outputs: /tmp/lawv1_mix/{data_MIX-<arm>.json, dataset_info.json, mixture_manifest.json}
"""
import json, hashlib, sys
from pathlib import Path
from transformers import AutoTokenizer

ROOT = Path('/opt/tiger/atomic-repair-sft-github')
OUT = Path(OUTDIR); OUT.mkdir(exist_ok=True)
MODEL = "/mnt/hdfs/xwqu/Qwen3-8B"
CUTOFF, SEQ_PER_STEP, EPOCHS = 2048, 16, 2

import sys
SPEC_FILE=sys.argv[1] if len(sys.argv)>1 else 'prescription/lawv1/MIXTURE_SPEC_FROZEN.json'
OUTDIR=sys.argv[2] if len(sys.argv)>2 else '/tmp/lawv1_mix'
spec = json.load(open(ROOT/SPEC_FILE))
tok = AutoTokenizer.from_pretrained(MODEL, trust_remote_code=True)
ntok = lambda s: len(tok(s, add_special_tokens=False)["input_ids"])
def seqtok(p, t):
    r = tok.apply_chat_template([{"role":"user","content":p}], tokenize=False,
                                add_generation_prompt=True, enable_thinking=False)
    return ntok(r)+ntok(t)

def jl(p): return [json.loads(l) for l in open(ROOT/p)]
# replay sources (frozen order = file order)
REP = {
 'R': [{"instruction":r["instruction"],"input":"","output":r["output"]} for r in json.load(open(ROOT/'prescription/lawv1/carrier_formal.json'))],
 'K': [{"instruction":r["prompt"],"input":"","output":r["target"]} for r in jl('prescription/knowledge/pools/k_clean_replay_2000.jsonl')],
 'IF':[{"instruction":r["prompt"],"input":"","output":r["target"]} for r in jl('prescription/if_domain/if_clean_replay_pool.jsonl')],
}
COMP = {
 'fmt_R': [{"instruction":r["prompt"],"input":"","output":r["target"]} for r in jl('prescription/lawv1/format_pool_formal.jsonl')],
 'ans_R': [{"instruction":r["prompt"],"input":"","output":r["target"]} for r in jl('prescription/lawv1/answerability_pool_audited.jsonl')],
 'fmt_K': [{"instruction":r["prompt"],"input":"","output":r["target"]} for r in jl('prescription/knowledge/pools/k_format_2000.jsonl')],
 'ans_K': [{"instruction":r["prompt"],"input":"","output":r["target"]} for r in jl('prescription/knowledge/pools/k_answerability_2000.jsonl')],
 'fmt_IF':[{"instruction":r["prompt"],"input":"","output":r["target"]} for r in jl('prescription/if_domain/if_format_pool.jsonl')],
 'ans_IF':[{"instruction":r["prompt"],"input":"","output":r["target"]} for r in jl('prescription/if_domain/if_answerability_pool.jsonl')],
}
manifest = {"arms": {}, "shared_max_steps": None}
arms_data = {}
for name, a in spec['arms'].items():
    data = (REP['R'][:a['replay_R']] + REP['K'][:a['replay_K']] + REP['IF'][:a['replay_IF']]
            + COMP['fmt_R'][:a['fmt_R']] + COMP['ans_R'][:a['ans_R']]
            + COMP['fmt_K'][:a['fmt_K']] + COMP['ans_K'][:a['ans_K']]
            + COMP['fmt_IF'][:a['fmt_IF']] + COMP['ans_IF'][:a['ans_IF']])
    assert len(data) == 2000, (name, len(data))
    arms_data[name] = data
    seq = sum(seqtok(r["instruction"], r["output"]) for r in data)
    tgt = sum(ntok(r["output"]) for r in data)
    manifest['arms'][name] = dict(counts=a, examples=len(data),
        total_target_tokens=tgt, total_sequence_tokens=seq,
        packed_sequences_est=-(-seq//CUTOFF))
mx = max(v['packed_sequences_est'] for v in manifest['arms'].values())
manifest['shared_max_steps'] = -(-mx//SEQ_PER_STEP)*EPOCHS
info = {}
for name, data in arms_data.items():
    fp = OUT/f'data_MIX-{name}.json'
    fp.write_text(json.dumps(data, ensure_ascii=False))
    manifest['arms'][name]['data_sha256'] = hashlib.sha256(fp.read_bytes()).hexdigest()[:16]
    info[f'lawv1_MIX-{name}'] = {"file_name": f'data_MIX-{name}.json'}
(OUT/'dataset_info.json').write_text(json.dumps(info, indent=1))
(OUT/'mixture_manifest.json').write_text(json.dumps(manifest, indent=1))
print(json.dumps({n: {k: v[k] for k in ('examples','total_target_tokens','packed_sequences_est','data_sha256')}
                  for n, v in manifest['arms'].items()}, indent=1))
print('shared_max_steps', manifest['shared_max_steps'])
