#!/usr/bin/env python3
"""父仓库组合校验（product umbrella）。

检查项：
1. `AGENTS.md` 子模块登记表 与 `.gitmodules` 的路径集合一致；
2. 一致性套件用**规范参考适配器**自检全绿（离线）；
3. CLI 命令面 manifest（`docs/spec/cli-surface.json`）结构自检（离线）；
4. `--remote`：各子模块记录指针确实存在于远端（需网络）。

用法：
  python3 scripts/verify/check.py            # 1 + 2 + 3
  python3 scripts/verify/check.py --remote   # 追加 4
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
AGENTS = REPO / "AGENTS.md"
GITMODULES = REPO / ".gitmodules"


def fail(msg: str) -> None:
    print(f"::error::{msg}")


def gitmodules_paths() -> set[str]:
    text = GITMODULES.read_text(encoding="utf-8")
    return set(re.findall(r"^\s*path\s*=\s*(\S+)\s*$", text, flags=re.MULTILINE))


def agents_registry_paths() -> set[str]:
    text = AGENTS.read_text(encoding="utf-8")
    # 取「子模块登记表」小节
    match = re.search(r"\n##\s*4\.[^\n]*\n(.*?)(?=\n##\s)", text, flags=re.DOTALL)
    section = match.group(1) if match else text
    # 行首第一个反引号字段即路径
    return set(re.findall(r"^\|\s*`([^`]+)`\s*\|", section, flags=re.MULTILINE))


def check_registry() -> bool:
    gitm = gitmodules_paths()
    agents = agents_registry_paths()
    ok = True
    only_gitmodules = gitm - agents
    only_agents = agents - gitm
    if only_gitmodules:
        fail(f"AGENTS.md 登记表缺少子模块：{sorted(only_gitmodules)}")
        ok = False
    if only_agents:
        fail(f"AGENTS.md 登记表多出（.gitmodules 无）：{sorted(only_agents)}")
        ok = False
    if ok:
        print(f"[ok] 登记表一致（{len(gitm)} 个子模块）")
    return ok


def check_reference() -> bool:
    runner = REPO / "scripts" / "conformance" / "run.py"
    reference = REPO / "scripts" / "conformance" / "reference.py"
    proc = subprocess.run(
        [sys.executable, str(runner), "--adapter", f"{sys.executable} {reference}", "--strict"],
        capture_output=True,
        text=True,
    )
    tail = proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else "(no output)"
    if proc.returncode != 0:
        fail(f"一致性参考自检失败：{tail}")
        print(proc.stdout[-2000:])
        return False
    print(f"[ok] 一致性参考自检：{tail}")
    return True


def check_surface_manifest() -> bool:
    script = REPO / "scripts" / "verify" / "surface.py"
    proc = subprocess.run(
        [sys.executable, str(script), "--self-check"],
        capture_output=True, text=True,
    )
    out = (proc.stdout + proc.stderr).strip()
    if proc.returncode != 0:
        fail("CLI 命令面 manifest 自检失败")
        print(out[-2000:])
        return False
    last = out.splitlines()[-1] if out else "surface manifest"
    print(last if last.startswith("[ok]") else f"[ok] {last}")
    return True


def check_remote() -> bool:
    status = subprocess.run(
        ["git", "submodule", "status"],
        cwd=REPO, capture_output=True, text=True,
    ).stdout
    ok = True
    for line in status.splitlines():
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        sha, path = parts[0].lstrip("+-"), parts[1]
        url = subprocess.run(
            ["git", "config", "-f", str(GITMODULES), "--get", f"submodule.{path}.url"],
            cwd=REPO, capture_output=True, text=True,
        ).stdout.strip()
        if not url:
            continue
        found = subprocess.run(
            ["git", "ls-remote", url, sha],
            capture_output=True, text=True,
        ).stdout
        if not found.strip():
            fail(f"子模块 {path} 指针 {sha[:8]} 不在远端：{url}")
            ok = False
    if ok:
        print("[ok] 所有子模块指针均存在于远端")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser(description="父仓库组合校验")
    ap.add_argument("--remote", action="store_true", help="追加远端指针存在性检查（需网络）")
    args = ap.parse_args()

    results = [check_registry(), check_reference(), check_surface_manifest()]
    if args.remote:
        results.append(check_remote())
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
