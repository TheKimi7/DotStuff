#!/usr/bin/env python3
"""Pin DotStuff to a pushed monotile commit: download its GitHub tarball, hash it, update pins.py.

    python3 tools/pin_monotile.py [commit-or-branch]     (default: main)
"""
import hashlib
import json
import os
import re
import sys
import urllib.request

REPO = "TheKimi7/monotile"
PINS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dotstuff", "pins.py")


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "DotStuff-pin"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


ref = sys.argv[1] if len(sys.argv) > 1 else "main"
commit = json.loads(fetch(f"https://api.github.com/repos/{REPO}/commits/{ref}"))["sha"]
data = fetch(f"https://github.com/{REPO}/archive/{commit}.tar.gz")
sha = hashlib.sha256(data).hexdigest()
s = open(PINS, encoding="utf-8").read()
s, n1 = re.subn(r'(?m)^MONOTILE_COMMIT = "[0-9a-f]*"', f'MONOTILE_COMMIT = "{commit}"', s)
s, n2 = re.subn(r'(?m)^MONOTILE_SHA = "[0-9a-f]*"', f'MONOTILE_SHA = "{sha}"', s)
if (n1, n2) != (1, 1):
    sys.exit("pins.py: MONOTILE_COMMIT / MONOTILE_SHA lines not found")
open(PINS, "w", encoding="utf-8").write(s)
print(f"pinned monotile {commit[:7]} ({len(data) / 1e6:.1f} MB, sha256 {sha[:12]}…)")
