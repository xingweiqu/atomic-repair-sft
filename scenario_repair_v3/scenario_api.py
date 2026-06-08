"""Optional LLM paraphrase layer for scenario surfaces.

Takes a seed scenario problem (already deterministic, oracle-clean) and asks an LLM to
make it sound more like a real user — WITHOUT changing the meaning and WITHOUT ever
introducing the gold answer. Results are cached to data_v3/scenario_cache.json keyed by
the seed text, so the pipeline is reproducible and the API is called at most once per
unique seed.

The API is OPTIONAL. If the CLI is unavailable or a paraphrase fails the leak/semantic
check, we fall back to the seed verbatim. The entire pipeline runs with --no-api.

Uses the `claude` CLI (session-authenticated, no env key needed): `claude -p "<prompt>"`.
"""
from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

CACHE_PATH = Path("data_v3/scenario_cache.json")

REWRITE_PROMPT = (
    "Rewrite the following user message so it sounds like a natural, casual real user, "
    "keeping the EXACT same meaning and the same question. Do not add, remove, or change "
    "any facts. Do not answer the question. Do not mention any country, nationality, "
    "currency, number, or answer. Return ONLY the rewritten message, one line.\n\n"
    "Message: {seed}"
)


def _load_cache() -> dict:
    if CACHE_PATH.exists():
        return json.loads(CACHE_PATH.read_text())
    return {}


def _save_cache(cache: dict) -> None:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    CACHE_PATH.write_text(json.dumps(cache, indent=2, ensure_ascii=False))


def _call_claude(prompt: str, timeout: int = 60) -> str | None:
    try:
        out = subprocess.run(["claude", "-p", prompt], capture_output=True, text=True,
                             timeout=timeout)
        if out.returncode == 0:
            return out.stdout.strip()
    except Exception:
        return None
    return None


def _leak_ok(text: str, banned: list[str]) -> bool:
    """Reject a paraphrase that leaked the gold answer or any banned token."""
    low = text.lower()
    for b in banned:
        if b and b.lower() in low:
            return False
    # must still be a single, reasonable line
    if not text or len(text) > 600 or "\n" in text.strip():
        return False
    return True


class ScenarioRewriter:
    """Caches paraphrases; falls back to the seed on any failure."""

    def __init__(self, use_api: bool):
        self.use_api = use_api
        self.cache = _load_cache()
        self.dirty = False
        self.stats = {"cache_hit": 0, "api_ok": 0, "fallback": 0}

    def rewrite(self, seed: str, banned: list[str]) -> str:
        if not self.use_api:
            return seed
        if seed in self.cache:
            self.stats["cache_hit"] += 1
            cached = self.cache[seed]
            return cached if _leak_ok(cached, banned) else seed
        out = _call_claude(REWRITE_PROMPT.format(seed=seed))
        if out and _leak_ok(out, banned):
            # strip any leading "Message:"/quotes the model might add
            out = re.sub(r'^(message:|rewritten:)\s*', '', out, flags=re.I).strip().strip('"')
            if _leak_ok(out, banned):
                self.cache[seed] = out
                self.dirty = True
                self.stats["api_ok"] += 1
                return out
        self.stats["fallback"] += 1
        return seed

    def flush(self):
        if self.dirty:
            _save_cache(self.cache)
