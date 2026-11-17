#!/usr/bin/env python3
"""cron 包装器：只在公网 IP 变化时输出（no_agent 模式下无输出即不推送）。"""
import os
import subprocess
import sys

SYNC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "nethernet_advertise_sync.py")
env = dict(os.environ)
env["PYTHONPATH"] = ""  # 避免 Hermes venv 污染子进程

dry = subprocess.run([sys.executable, SYNC, "--dry"], capture_output=True, text=True, env=env)
if "\U0001f7e1" not in dry.stdout:  # 🟡 = 有变更待写入
    sys.exit(0)

real = subprocess.run([sys.executable, SYNC], capture_output=True, text=True, env=env)
print("NetherNet advertise-addresses 已随公网 IP 更新，并已 reload Geyser：")
print(real.stdout.strip())
if real.returncode != 0:
    print(f"\n⚠️ sync 退出码 {real.returncode}\n{real.stderr.strip()[:500]}")
