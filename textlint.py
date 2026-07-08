"""Standing iron rule (probe-audit ruling 2026-07-12): ANY LLM-generated text must pass
this lint before entering probe/training data. Second occurrence of the Qwen thinking-mode
residue bug family (first: pass@8 v1 truncation) bought this rule.

lint(text)      -> cleaned text (think blocks, chat/role markers stripped, trimmed)
has_residue(t)  -> bool (for assertions/gates)
"""
from __future__ import annotations
import re

_PATTERNS = [
    re.compile(r"<think>.*?</think>", re.S),
    re.compile(r"</?think>"),
    re.compile(r"<\|im_(start|end)\|>"),
    re.compile(r"^\s*(assistant|user|system)\s*[:\n]", re.I),
]


def lint(text: str) -> str:
    t = text or ""
    for p in _PATTERNS:
        t = p.sub("", t)
    t = re.sub(r"^```[a-z]*\n?|\n?```$", "", t.strip())
    return t.strip()


def has_residue(text: str) -> bool:
    return any(p.search(text or "") for p in _PATTERNS)
