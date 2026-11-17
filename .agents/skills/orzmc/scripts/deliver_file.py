"""交付工具：把任意文件投递到 deliver_dir()（S: → UNC → 本机兜底）。

用法：
    python deliver_file.py <源文件路径> [--as 目标文件名] [--json]

输出：目标绝对路径 + 两侧 sha256 + 大小；失败时退出码 1。
供 cron / 手动复用（升级包、巡检报告、审计清单都走它）。
"""
import argparse
import hashlib
import json
import os
import pathlib
import shutil
import sys

try:  # Windows 控制台默认 cp936，锁 UTF-8 免得 emoji/中文把交付打断
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def deliver(src: pathlib.Path, as_name: str | None = None) -> dict:
    from orzmc_paths import deliver_dir

    target, note = deliver_dir()
    dst = pathlib.Path(target) / (as_name or src.name)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(str(src), str(dst))
    return {
        "src": str(src),
        "dst": str(dst),
        "dir_note": note,
        "src_sha256": sha256(src),
        "dst_sha256": sha256(dst),
        "match": sha256(src) == sha256(dst),
        "size": dst.stat().st_size,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="交付文件到 S: 盘（三级回退）")
    ap.add_argument("src", help="源文件路径")
    ap.add_argument("--as", dest="as_name", default=None, help="目标文件名（默认同名）")
    ap.add_argument("--json", action="store_true", help="以 JSON 输出")
    args = ap.parse_args()

    src = pathlib.Path(args.src)
    if not src.is_file():
        print("源文件不存在：%s" % src)
        return 1
    try:
        res = deliver(src, args.as_name)
    except Exception as exc:  # noqa: BLE001
        print("交付失败：%s: %s" % (type(exc).__name__, exc))
        return 1
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print("交付目录来源：%s" % res["dir_note"])
        print("已投递：%s" % res["dst"])
        print("大小：%d 字节" % res["size"])
        print("sha256 源：%s" % res["src_sha256"])
        print("sha256 目标：%s" % res["dst_sha256"])
        print("一致性：%s" % ("OK" if res["match"] else "MISMATCH"))
    return 0 if res["match"] else 1


if __name__ == "__main__":
    sys.exit(main())
