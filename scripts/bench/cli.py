#!/usr/bin/env python3
"""对比两套 `orzmc` 实现的启动开销（**可复跑**，防止靠印象争论）。

用法::

    python3 scripts/bench/cli.py \
        --a "Python 冻结二进制=/tmp/py/orzmc-macos-x86_64" \
        --b "Swift 二进制=/tmp/swift/orzmc-macos-x86_64"

    python3 scripts/bench/cli.py --a "Python=/path/a" --b "Swift=/path/b" --json

测量口径（都只统计**子进程**，不含本脚本本身）::

- **墙钟**：``subprocess.run`` 往返时间；取中位数、最快、最慢；
- **CPU**：``resource.getrusage(RUSAGE_CHILDREN)`` 的 utime+stime 差值（能区分「启动等待」与「真在算」）；
- **峰值 RSS**：在包装进程里读 ``ru_maxrss``（PyInstaller onefile 的解包发生在子进程，外部采样会漏）。

每个被测实现都带 ``ORZMC_RUNTIME=python``：M3 的「默认判定」会让**没有安装记录**的环境默认走
Swift 真身，基准必须钉住被测实现本身，否则量到的可能是「下载 + 转发」。

只做本地、离线、无副作用的命令（``--version`` / ``--json capabilities`` / ``--json list``）。
"""

from __future__ import annotations

import argparse
import json
import os
import resource
import statistics
import subprocess
import sys
import tempfile
import time

#: 不联网、不写盘的命令（``--json list`` 读的是空沙箱）。
COMMANDS: dict[str, list[str]] = {
    "--version": ["--version"],
    "--json capabilities": ["--json", "capabilities"],
    "--json list": ["--json", "list"],
}

DEFAULT_RUNS = 7


def _sandbox_env() -> dict[str, str]:
    """隔离的状态目录/家目录：不读用户真实的 install.conf，也不写真实状态。"""
    root = tempfile.mkdtemp(prefix="orzmc-bench-")
    return {
        **os.environ,
        "ORZMC_RUNTIME": "python",  # 钉住被测实现（见模块说明）
        "XDG_STATE_HOME": os.path.join(root, "state"),
        "XDG_DATA_HOME": os.path.join(root, "data"),
        "XDG_CONFIG_HOME": os.path.join(root, "config"),
        "XDG_CACHE_HOME": os.path.join(root, "cache"),
        "HOME": os.path.join(root, "home"),
        "USERPROFILE": os.path.join(root, "home"),
        "NO_COLOR": "1",
        "TERM": "dumb",
    }


_RSS_WRAPPER = (
    "import resource, subprocess, sys\n"
    "subprocess.run(sys.argv[1:], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n"
    "print(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)\n"
)


def _peak_rss_kb(binary: str, args: list[str], env: dict[str, str]) -> int:
    """子进程的峰值 RSS（KB）。

    用 ``ru_maxrss`` 而不是外部采样：PyInstaller onefile 的解包发生在**子进程**里，
    按 ``ps -p 主进程`` 采样会漏掉（实测只量到 1MB，真值 37MB）。
    ``ru_maxrss`` 的单位在 macOS 是字节、Linux 是 KB —— 这里统一成 KB。
    """
    completed = subprocess.run(
        [sys.executable, "-c", _RSS_WRAPPER, binary, *args],
        capture_output=True,
        text=True,
        env=env,
    )
    if completed.returncode != 0:
        return 0
    try:
        value = int(completed.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return 0
    return value // 1024 if sys.platform == "darwin" else value


def measure(label: str, binary: str, runs: int) -> dict[str, object]:
    if not os.path.isfile(binary):
        raise SystemExit(f"找不到可执行文件: {binary}")
    env = _sandbox_env()
    results: dict[str, dict[str, float]] = {}
    for name, args in COMMANDS.items():
        walls: list[float] = []
        cpus: list[float] = []
        for _ in range(runs):
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            started = time.perf_counter()
            completed = subprocess.run([binary, *args], capture_output=True, env=env)
            walls.append((time.perf_counter() - started) * 1000)
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            cpus.append(((after.ru_utime - before.ru_utime) + (after.ru_stime - before.ru_stime)) * 1000)
            if completed.returncode != 0:
                raise SystemExit(f"{label} {args} 退出码 {completed.returncode}: {completed.stderr[:400]!r}")
        results[name] = {
            "wall_median_ms": statistics.median(walls),
            "wall_min_ms": min(walls),
            "wall_max_ms": max(walls),
            "cpu_median_ms": statistics.median(cpus),
        }
    return {
        "label": label,
        "binary": binary,
        "size_mb": round(os.path.getsize(binary) / 1048576, 1),
        "peak_rss_kb": _peak_rss_kb(binary, ["--json", "capabilities"], env),
        "commands": results,
    }


def _print_table(data: list[dict[str, object]]) -> None:
    print(f"{'命令':<22}{'实现':<24}{'墙钟中位':>10}{'CPU中位':>10}{'最快':>8}{'最慢':>8}")
    print("-" * 84)
    for entry in data:
        for name, stats in entry["commands"].items():  # type: ignore[union-attr]
            print(
                f"{name:<22}{entry['label']:<24}"
                f"{stats['wall_median_ms']:>8.0f}ms{stats['cpu_median_ms']:>8.0f}ms"
                f"{stats['wall_min_ms']:>7.0f}{stats['wall_max_ms']:>8.0f}"
            )
    print()
    for entry in data:
        rss = entry["peak_rss_kb"]
        rss_text = f"{rss / 1024:.0f} MB" if rss else "n/a"
        print(f"  {entry['label']}: 体积 {entry['size_mb']} MB, 峰值 RSS {rss_text}")


def main() -> int:
    parser = argparse.ArgumentParser(description="对比两套 orzmc 实现的启动开销")
    parser.add_argument("--a", required=True, help="标签=可执行文件路径")
    parser.add_argument("--b", required=True, help="标签=可执行文件路径")
    parser.add_argument("--runs", type=int, default=DEFAULT_RUNS, help=f"每命令重复次数（默认 {DEFAULT_RUNS}）")
    parser.add_argument("--json", action="store_true", help="输出 JSON（便于入库/画图）")
    args = parser.parse_args()

    data = []
    for spec in (args.a, args.b):
        label, _, binary = spec.partition("=")
        if not binary:
            raise SystemExit(f"--a/--b 需要 标签=路径 形式: {spec}")
        data.append(measure(label, binary, args.runs))

    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        _print_table(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
