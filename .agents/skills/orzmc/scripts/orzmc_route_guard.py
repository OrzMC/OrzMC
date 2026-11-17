#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OrzMC WSL 路由自愈 —— Windows 侧兜底触发（cron: no_agent watchdog）

背景：WSL 里 eth4 的地址/网卡会被周期性重建，内核清掉 dev eth4 的策略路由
（表 101）而 ip rule 仍留着 → 局域网/公网入口不通。WSL 内已有 netlink 事件
驱动的 orzmc-mc-reply-route-watch.sh 做亚秒级主力修复；本脚本是 Windows 侧
的低频兜底：每 10 分钟跑一次 /usr/local/bin/orzmc-mc-reply-route.sh。

为什么要它而不是 Windows 计划任务（2026-10-12 实测结论）：
  旧计划任务 OrzMC-MC-Reply-Route（LogonType=InteractiveToken）直接启动
  wsl.exe，会在用户桌面弹出控制台窗口闪约 1 秒；改成 wscript 包装（窗口样式 0）
  后 wscript 会挂在 Run 调用上不退出，任务卡在 RUNNING，MultipleInstancesPolicy
  =IgnoreNew 让后续所有触发被忽略（自愈静默失效）——两条路都不行。
  由 Hermes cron 执行则走 subprocess + CREATE_NO_WINDOW：父进程无控制台，
  子进程不新建窗口，实测无任何闪烁；且失败会以告警文本投递到飞书，不再静默。
"""

from __future__ import annotations
try:  # Windows console/pipe defaults to cp936: lock UTF-8 or emoji print raises
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import os
import subprocess
import sys
import time
from datetime import datetime

STATE_DIR = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "hermes", "state")
LOG = os.path.join(STATE_DIR, "orzmc_route_guard.log")

DOCKERLESS_CMD = [
    "wsl.exe",
    "-d",
    "Ubuntu",
    "-u",
    "root",
    "--",
    "bash",
    "/usr/local/bin/orzmc-mc-reply-route.sh",
]
WSL_EXE = r"C:\Windows\System32\wsl.exe"
TIMEOUT = 150


def log(msg: str) -> None:
    try:
        os.makedirs(STATE_DIR, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write("[%s] %s\n" % (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), msg))
    except OSError:
        pass


def run(cmd, timeout=TIMEOUT):
    exe = cmd[0]
    if not os.path.isabs(exe):
        for cand in (WSL_EXE, exe):
            if os.path.isfile(cand):
                cmd = [cand] + list(cmd[1:])
                break
    try:
        p = subprocess.run(
            cmd,
            capture_output=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        out = (p.stdout or b"").decode("utf-8", "replace") + (p.stderr or b"").decode("utf-8", "replace")
        return p.returncode, out.strip()
    except subprocess.TimeoutExpired:
        return -1, "timeout after %ss" % timeout
    except FileNotFoundError as exc:
        return -2, "not found: %s" % exc


def main() -> int:
    t0 = time.time()
    rc, out = run(DOCKERLESS_CMD)
    dur = time.time() - t0
    tail = out[-400:] if out else ""
    if rc == 0:
        log("OK (%.1fs)" % dur)
        return 0
    log("FAIL rc=%s (%.1fs): %s" % (rc, dur, tail.replace("\n", " | ")))
    print(
        "⚠️ OrzMC WSL 路由兜底修复失败（Windows 侧，rc=%s，耗时 %.0fs）：%s\n"
        "WSL 内事件驱动守护（orzmc-mc-reply-route-watch.sh）可能也没在跑——"
        "局域网入口（MC 端口 25565/25566/19132-19134）可能不通，需要人工检查。"
        % (rc, dur, tail.replace("\n", " ")[:300] or "无输出")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
