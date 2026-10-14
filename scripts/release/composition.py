#!/usr/bin/env python3
"""打印当前发版组合（Markdown 表格），用于更新 `RELEASES.md`。

用**父仓库记录指针**（index 里的 gitlink，`git ls-tree HEAD`），而非子模块当前检出——
后者可能停在 `develop` 等迭代线（如 `plugin`）。

用法：
  python3 scripts/release/composition.py
"""
from __future__ import annotations

import datetime
import re
import subprocess
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def recorded_sha(path: str) -> str:
    out = subprocess.run(
        ["git", "ls-tree", "HEAD", "--", path],
        cwd=REPO, capture_output=True, text=True,
    ).stdout.strip()
    match = re.match(r"\d+\s+commit\s+([0-9a-f]+)", out)
    return match.group(1) if match else "?"


def repo_slug(url: str) -> str:
    slug = url.removeprefix("https://github.com/")
    return slug[:-4] if slug.endswith(".git") else slug


def main() -> int:
    raw = subprocess.run(
        ["git", "config", "-f", ".gitmodules", "--list"],
        cwd=REPO, capture_output=True, text=True,
    ).stdout
    entries: dict[str, dict[str, str]] = {}
    for line in raw.splitlines():
        match = re.match(r"submodule\.(.+)\.(path|url|branch)=(.*)", line)
        if match:
            entries.setdefault(match.group(1), {})[match.group(2)] = match.group(3)

    print(f"## 基准组合（{datetime.date.today().isoformat()}）\n")
    print("| 子模块 | 仓库 | 分支 | 记录指针 |")
    print("|---|---|---|---|")
    for name, entry in sorted(entries.items(), key=lambda kv: kv[1].get("path", "")):
        path = entry.get("path", name)
        print(f"| `{path}` | {repo_slug(entry.get('url', ''))} | `{entry.get('branch', 'main')}` | `{recorded_sha(path)[:12]}` |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
