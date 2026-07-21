#!/bin/bash
# The ONLY sanctioned way to produce main.pdf: figure sync is part of the build,
# never a separate manual step (lesson: stale fig7 shipped in a review PDF).
set -e
cd "$(dirname "$0")"
rsync -a --checksum ../figs/out/fig*.pdf figures/
python3 lint_banned.py
tectonic main.tex
python3 - << 'PY'
import hashlib, pathlib, sys
bad = []
for src in pathlib.Path('../figs/out').glob('fig*.pdf'):
    dst = pathlib.Path('figures') / src.name
    if not dst.exists() or hashlib.md5(src.read_bytes()).hexdigest() != hashlib.md5(dst.read_bytes()).hexdigest():
        bad.append(src.name)
print("figure-sync check:", "FAIL " + str(bad) if bad else "PASS")
sys.exit(1 if bad else 0)
PY
echo "BUILD OK"
