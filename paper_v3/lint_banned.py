#!/usr/bin/env python3
"""Line-wrap-tolerant banned-phrase scan (C-17 acceptance lesson: 'reverse\\nvaccine')."""
import re, sys, pathlib
banned = [l.strip() for l in open(pathlib.Path(__file__).parent / "BANNED_PHRASES.txt") if l.strip()]
bad = 0
for p in list(pathlib.Path(__file__).parent.glob("sections/*.tex")) + [pathlib.Path(__file__).parent / "main.tex"]:
    text = re.sub(r"%.*", "", p.read_text())
    flat = re.sub(r"\s+", " ", text)
    for b in banned:
        if re.search(re.escape(b), flat, re.I):
            print(f"BANNED '{b}' in {p.name}"); bad += 1
print("banned-phrase lint:", "FAIL" if bad else "PASS")
sys.exit(1 if bad else 0)
