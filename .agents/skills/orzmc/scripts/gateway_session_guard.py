#!/usr/bin/env python3
try:  # Windows 控制台/管道默认 cp936：不锁 UTF-8 会让 emoji 打印炸成 traceback
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
"""Hermes cron 用的薄封装：检测网关是否跑在交互会话，若不在则异步触发切换。

- 静默策略：一切正常时不输出任何内容（cron no_agent 模式下不推送消息）。
- 只做检测与触发；真正的"杀掉 Session 0 实例 + 由计划任务在交互会话重启"由
  gateway_session_guard.ps1（计划任务 Hermes_Gateway_Swap）执行，
  因为 cron 脚本本身是网关子进程，不能亲手杀掉自己的父进程。
"""
import subprocess
import sys
from pathlib import Path

PS = Path(__file__).with_name("gateway_session_guard.ps1")


def ensure_ps1_sane() -> None:
    """自愈：.ps1 头部若出现重复 BOM（EF BB BF EF BB BF），param() 块会失效。

    后果很严重：``-File script.ps1 -Detach`` 的开关绑不上，脚本退化成"就地切换"
    模式——它会杀掉自己所在的网关（也就是 cron 自己的父进程），切换只做一半。
    """
    raw = PS.read_bytes()
    while raw[:3] == b"\xef\xbb\xbf":
        raw = raw[3:]
    text = raw.decode("utf-8")
    if not text.lstrip().startswith("param("):
        print(f"⚠️ {PS.name} 内容异常（未以 param( 开头），请检查")
        return
    if not PS.read_bytes().startswith(b"\xef\xbb\xbfparam("):
        PS.write_text(text, encoding="utf-8-sig", newline="\r\n")
        print("已修正 gateway_session_guard.ps1 的 BOM/行尾（防止 -Detach 失效）")


def main() -> int:
    if not PS.exists():
        print(f"gateway_session_guard.ps1 不存在: {PS}")
        return 1
    ensure_ps1_sane()
    try:
        r = subprocess.run(
            ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(PS), "-Detach"],
            capture_output=True, text=True, timeout=180,
            # 父进程（网关/cron）无控制台，powershell.exe 是控制台程序：不给这个标志
            # 每次 tick 都会在用户桌面弹一个控制台窗口闪一下（实测每 5 分钟一次）。
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except subprocess.TimeoutExpired:
        print("⚠️ 网关会话守卫超时（>180s）")
        return 1
    out = (r.stdout or "").strip()
    if out:
        print(out)
    if r.returncode != 0 and (r.stderr or "").strip():
        print((r.stderr or "").strip()[:500])
    return 0


if __name__ == "__main__":
    sys.exit(main())
