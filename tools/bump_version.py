#!/usr/bin/env python3
"""Site version: one bump per merged pull request (V1.014 -> V1.015).

  python3 tools/bump_version.py "What changed"   # before opening the PR
  python3 tools/bump_version.py --check          # every page shows the version in web/data/version.json

Edits web/data/version.json, CHANGELOG.md and the header badge on every web/*.html page.
If two open PRs pick the same number, the one merged second updates from main and bumps again.
"""
import datetime
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VFILE = ROOT / "web" / "data" / "version.json"
BADGE = re.compile(r'(<a class="ver"[^>]*>)V\d+\.\d{3}(</a>)')


def pages():
    return sorted((ROOT / "web").glob("*.html"))


def check() -> int:
    v = json.loads(VFILE.read_text())["version"]
    bad = [p.name for p in pages() if [m for m in BADGE.findall(p.read_text())] == [] or f">{v}<" not in p.read_text()]
    if bad:
        print("Version badge missing or not", v, "in:", ", ".join(bad))
        return 1
    print("All pages show", v)
    return 0


def bump(message: str) -> int:
    data = json.loads(VFILE.read_text())
    major, minor = re.fullmatch(r"V(\d+)\.(\d{3})", data["version"]).groups()
    new = f"V{major}.{int(minor) + 1:03d}"
    today = datetime.date.today().isoformat()
    data.update(version=new, date=today, note=message)
    VFILE.write_text(json.dumps(data, indent=1, ensure_ascii=False) + "\n")
    for p in pages():
        p.write_text(BADGE.sub(lambda m: m.group(1) + new + m.group(2), p.read_text()))
    log = ROOT / "CHANGELOG.md"
    text = log.read_text()
    head, _, rest = text.partition("\n## ")
    log.write_text(f"{head}\n## {new} · {today}\n- {message}\n\n## {rest}" if rest else f"{text}\n## {new} · {today}\n- {message}\n")
    print(data["version"])
    return check()


if __name__ == "__main__":
    if sys.argv[1:] == ["--check"]:
        sys.exit(check())
    if len(sys.argv) != 2 or not sys.argv[1].strip():
        sys.exit(__doc__)
    sys.exit(bump(sys.argv[1].strip()))
