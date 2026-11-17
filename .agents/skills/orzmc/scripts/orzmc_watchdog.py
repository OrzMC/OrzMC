#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""OrzMC 守卫 watchdog（cron: no_agent，每 5 分钟）—— 四条高频守卫的薄包装聚合器。

合并的四条旧 job（原排程 → 本 watchdog 内的实际节奏）：
  orzmc-nethernet-advertise-sync  15m  → 每 tick（5m）
  gateway-session-guard            5m  → 每 tick（5m）
  orzmc-route-guard               10m  → tick % 2 == 0（约 10m）
  orzmc-entry-probe               30m  → tick % 6 == 0（约 30m）

设计纪律（不要"优化"它）：
  1. **不重写判定逻辑**：四个原脚本原封不动，本脚本只用子进程调用它们，
     捕获 stdout/stderr/退出码，按段聚合。原脚本「静默即正常」的约定沿用。
  2. 每段独立 try/except：一段崩了不影响其余段跑完；有任何一段失败 → 退出码 1。
  3. 全绿时 **stdout 必须为空、退出码 0**（与四条旧 job 的既成约定一致，
     不许改成每天一条"我很好"）。
  4. 告警按段名分节聚合，原文照搬（emoji/文案不改写）：
         ## entry-probe
         🔴 ...
  5. tick 计数存在 state 文件里，只增不减；cron 重启/错过后节奏自然延续。

日志：%LOCALAPPDATA%\\hermes\\logs\\orzmc-watchdog.log（每段一行）
状态：%LOCALAPPDATA%\\hermes\\state\\orzmc_watchdog.json
"""
from __future__ import annotations
import sys
try:  # Windows console/pipe defaults to cp936: lock UTF-8 or emoji print raises
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import json
import os
import subprocess
import time

HERMES = os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "hermes")
SCRIPTS = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERMES, "state", "orzmc_watchdog.json")
LOG = os.path.join(HERMES, "logs", "orzmc-watchdog.log")

# (段名, 脚本文件名, 调用条件说明) —— 顺序即聚合输出顺序
SEGMENTS = [
    # 入口探针（最重的一项，故障才出声）
    ("entry-probe", "orzmc_entry_probe.py", lambda t: t % 6 == 0),
    # NetherNet advertise 守护：调旧 job 用的同一个包装器（它负责文案/退出码归一）
    ("advertise-sync", "nethernet_advertise_cron.py", lambda t: True),
    # WSL 路由兜底
    ("route-guard", "orzmc_route_guard.py", lambda t: t % 2 == 0),
    # 网关会话守卫（自己就在网关里跑，只做检测+异步触发）
    ("session-guard", "gateway_session_guard.py", lambda t: True),
]

PER_SEG_TIMEOUT = 300  # 各段最坏耗时之和远小于此；单段超时只算该段失败


def _norm(text: str) -> str:
    """子脚本在 Windows 上按 CRLF 打印，父进程再 print 会产出 \\r\\r\\n（飞书里多空行）。
    统一成 LF，文案本身一个字不动。"""
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def log(msg: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write("[%s] %s\n" % (time.strftime("%Y-%m-%d %H:%M:%S"), msg))
    except OSError:
        pass


def load_tick() -> int:
    try:
        with open(STATE, encoding="utf-8") as fh:
            return int(json.load(fh).get("tick", 0) or 0)
    except (OSError, ValueError, TypeError):
        return 0


def save_state(st: dict) -> None:
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        with open(STATE, "w", encoding="utf-8") as fh:
            json.dump(st, fh, ensure_ascii=False, indent=2, sort_keys=True)
    except OSError:
        pass


def child_env() -> dict:
    """PYTHONPATH 置空：Hermes venv 会污染所有子 Python（历史坑）；顺便锁 UTF-8。"""
    env = dict(os.environ)
    env["PYTHONPATH"] = ""
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    return env


def run_segment(name: str, script: str, tick: int) -> tuple[int, str, float]:
    """跑一段，返回 (rc, 告警文本或空串, 耗时)。异常一律收敛成 rc=-9。"""
    path = os.path.join(SCRIPTS, script)
    t0 = time.time()
    if not os.path.isfile(path):
        return -9, "⚠️ watchdog 找不到脚本：%s" % path, 0.0
    try:
        p = subprocess.run(
            [sys.executable, path],
            capture_output=True,
            timeout=PER_SEG_TIMEOUT,
            env=child_env(),
            cwd=SCRIPTS,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        out = _norm((p.stdout or b"").decode("utf-8", "replace"))
        err = _norm((p.stderr or b"").decode("utf-8", "replace"))
        rc = p.returncode
    except subprocess.TimeoutExpired:
        return -1, "⚠️ %s 超时（>%ss）" % (script, PER_SEG_TIMEOUT), time.time() - t0
    except Exception as exc:  # noqa: BLE001 —— 一段崩不影响其余段
        return -9, "⚠️ %s 调用失败：%s: %s" % (script, type(exc).__name__, exc), time.time() - t0

    dur = time.time() - t0
    if rc == 0:
        return 0, out, dur
    # 退出码非 0：即使原脚本没打印东西也要出声（否则 cron 会静默丢一个真故障）
    text = out
    tail = err[-400:] if err else ""
    text = (text + "\n" if text else "") + "⚠️ %s 退出码 %s" % (script, rc)
    if tail:
        text += "\n```\n%s\n```" % tail
    return rc, text, dur


def main() -> int:
    tick_prev = load_tick()
    tick = tick_prev + 1
    save_state({"tick": tick, "last_run": time.strftime("%Y-%m-%d %H:%M:%S")})

    sections: list[tuple[str, str]] = []
    failed = 0
    ran = 0
    for name, script, due in SEGMENTS:
        try:
            if not due(tick):
                continue
        except Exception as exc:  # noqa: BLE001
            log("tick=%d seg=%s SCHEDULE-ERROR %s" % (tick, name, exc))
            continue
        ran += 1
        try:
            rc, text, dur = run_segment(name, script, tick)
        except Exception as exc:  # noqa: BLE001 —— 双保险：连 run_segment 都炸了也别拖垮别的段
            rc, text, dur = -9, "⚠️ %s 异常：%s" % (script, exc), 0.0
        log("tick=%d seg=%s rc=%s alert=%s dur=%.1fs"
            % (tick, name, rc, "yes" if text else "no", dur))
        if rc != 0:
            failed += 1
        if text:
            sections.append((name, text))

    if sections:
        print("\n\n".join("## %s\n%s" % (n, t) for n, t in sections))
    log("tick=%d done segments=%d alerted=%d failed=%d -> %s"
        % (tick, ran, len(sections), failed, "FAIL" if failed else "OK"))
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001 —— watchdog 自己崩了要看得见（不再静默）
        import traceback
        tb = traceback.format_exc()
        print("⚠️ orzmc-watchdog 自身崩了（不是服务器故障）：\n```\n%s\n```" % tb[-800:])
        log("WATCHDOG-CRASH\n" + tb[-1200:])
        sys.exit(1)
