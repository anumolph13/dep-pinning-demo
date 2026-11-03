#!/usr/bin/env python3
"""Show how an unpinned requirements file resolves differently over time.

Uses `uv pip compile --exclude-newer DATE` to resolve the SAME file as if
`pip install` had been run on two different dates, then prints which
packages changed, separating ones you named (direct) from ones you never
mentioned (transitive).

Usage:
    python scripts/show_drift.py [OLD_DATE] [NEW_DATE]
    python scripts/show_drift.py 2024-06-01 2025-06-01
NEW_DATE defaults to today.
"""

import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQ = ROOT / "unpinned" / "requirements.txt"
PY = "3.12"  # fixed so both resolutions target the same interpreter


def norm(name: str) -> str:
    return re.sub(r"[-_.]+", "-", name).lower()


def resolve(as_of: str) -> dict[str, str]:
    out = subprocess.run(
        ["uv", "pip", "compile", str(REQ), "--python-version", PY,
         "--exclude-newer", f"{as_of}T00:00:00Z", "--no-header",
         "--no-annotate", "--quiet"],
        check=True, capture_output=True, text=True,
    ).stdout
    pins = {}
    for line in out.splitlines():
        m = re.match(r"^([A-Za-z0-9_.\-]+)(?:\[.*\])?==([^\s;]+)", line)
        if m:
            pins[norm(m.group(1))] = m.group(2)
    return pins


def main() -> None:
    old = sys.argv[1] if len(sys.argv) > 1 else "2024-06-01"
    new = sys.argv[2] if len(sys.argv) > 2 else dt.date.today().isoformat()
    direct = {norm(l.strip()) for l in REQ.read_text().splitlines()
              if l.strip() and not l.startswith("#")}

    a, b = resolve(old), resolve(new)
    names = sorted(set(a) | set(b))
    changed = [n for n in names if a.get(n) != b.get(n)]

    print(f"\nFile: {REQ.relative_to(ROOT)}  ({len(direct)} lines you wrote)")
    print(f"Resolved on {old}: {len(a)} packages | on {new}: {len(b)} packages\n")
    print(f"{'package':<26}{'kind':<12}{old:<16}{new:<16}")
    print("-" * 70)
    for n in changed:
        kind = "direct" if n in direct else "TRANSITIVE"
        print(f"{n:<26}{kind:<12}{a.get(n, '-'):<16}{b.get(n, '-'):<16}")

    t = [n for n in changed if n not in direct]
    print(f"\n{len(changed)} of {len(names)} packages differ; "
          f"{len(t)} of those are transitive (never named in your file).")
    added = [n for n in t if n not in a]
    if added:
        print("New transitive packages that appeared: " + ", ".join(added))


if __name__ == "__main__":
    main()
