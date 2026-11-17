"""交付路径探针（v2）：判定 Hermes cron（交互会话）能否写老板的 S: 盘 / UNC。

v2 变化：除了打印，还把结论**同时写入 E:/orzmc/reports/deliver-probe.log**，
        这样无论 cron 在哪个会话执行，都能从本机读到真实结论。
"""
import os
import pathlib
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TARGETS = [
    ("S:/", r"S:\ 映射盘"),
    (r"\\{LAN_IP}\下载", "UNC 直连 Mac 共享"),
    ("E:/orzmc/deliver", "本机兜底目录"),
]
LOG = pathlib.Path("E:/orzmc/reports/deliver-probe.log")


def _win_session_id():
    """真实 Windows 会话号（cron 在哪个 Session 跑决定了映射盘可见性）"""
    try:
        import ctypes
        sid = ctypes.c_ulong()
        if ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(sid)):
            return sid.value
    except Exception:
        pass
    return -1


def main():
    lines = []
    sid = os.environ.get("SESSIONNAME", "?")
    lines.append("=== deliver-probe %s 环境变量会话=%s Windows SessionId=%s ===" % (datetime.now().strftime("%F %T"), sid, _win_session_id()))
    for raw, label in TARGETS:
        p = pathlib.Path(raw)
        exists = p.exists()
        wrote = False
        err = ""
        try:
            p.mkdir(parents=True, exist_ok=True)
            f = p / ("_probe_%s.txt" % os.getpid())
            f.write_text("ok", encoding="utf-8")
            wrote = f.is_file()
            f.unlink()
        except Exception as e:
            err = "%s: %s" % (type(e).__name__, str(e)[:60])
        lines.append("%-24s exists=%-5s writable=%-5s %s" % (label, exists, wrote, err))
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from orzmc_paths import deliver_dir
        d, note = deliver_dir()
        lines.append("deliver_dir -> %s | %s" % (d, note))
    except Exception as e:
        lines.append("orzmc_paths 导入失败: %s" % e)
    text = "\n".join(lines)
    print(text)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        LOG.write_text(text + "\n", encoding="utf-8")
    except Exception as e:
        print("写日志失败: %s" % e)


if __name__ == "__main__":
    main()
