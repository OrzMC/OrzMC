"""交付端到端自测（v1）：把真实报告按 deliver_dir() 落到 S: 盘并打印 sha256。

用途：确认「Windows Hermes cron（Session 1）→ 老板 S: 盘」这条链路真的通，
而不是只测目录可写。老板侧核对 = Mac ~/Downloads 里出现同名文件且哈希一致。
"""
import hashlib
import os
import pathlib
import shutil
import sys
from datetime import datetime

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SRC = pathlib.Path("E:/orzmc/reports/config-audit-20261116-1031.md")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    from orzmc_paths import deliver_dir

    target, note = deliver_dir()
    print("deliver_dir -> %s | %s" % (target, note))
    if not SRC.is_file():
        print("SRC_MISSING %s" % SRC)
        return
    dst = pathlib.Path(target) / SRC.name
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(SRC), str(dst))
    print("COPIED %s -> %s" % (SRC.name, dst))
    print("LOCAL_SHA %s" % sha(SRC))
    print("REMOTE_SHA %s" % sha(dst))
    print("SIZE %d" % dst.stat().st_size)
    print("AT %s" % datetime.now().strftime("%F %T"))
    # 记录到探针日志，便于事后核对
    with open("E:/orzmc/reports/deliver-selftest.log", "a", encoding="utf-8") as fh:
        fh.write("=== %s target=%s sha=%s\n" % (datetime.now().strftime("%F %T"), dst, sha(dst)))


if __name__ == "__main__":
    main()
