"""确保一批 Python 脚本在模块级锁定 UTF-8 stdout/stderr（字节安全、幂等、可复核）。

为什么需要：Windows 控制台/管道默认 cp936，脚本 `print("🔴 …")` 会抛
`UnicodeEncodeError`，把**本该发出的告警**变成一屏 traceback。而「看起来加了 guard」
并不等于生效——三个真实坑都在这一个脚本里堵掉：

  1. guard 插进了模块 docstring 内部 → 变成字符串内容，等于没加；
  2. `import sys` 落在 docstring 里 → 模块级 `sys.stdout.reconfigure` 抛 NameError；
  3. NameError 被 guard 自己的 `except Exception: pass` 静默吞掉 → 平时全绿无异常。

因此本脚本：ast 定位 docstring / `__future__` 结束行 → 插入 guard → ast 复核
「模块级有 import sys + 模块级 try 含 reconfigure」→ py_compile。全程只对**字节流**
做插入，不做解码/重编码（GBK 脚本用 `read_text(errors="replace")` 读回会毁文件）。

用法：
  python fix_utf8_guard.py                       # 默认 %LOCALAPPDATA%/hermes/scripts
  python fix_utf8_guard.py --dir E:/path/scripts
  python fix_utf8_guard.py --dir <dir> --check    # 只体检不写（退出码 1=有不合格的）

退出码：0=全部合格或已修好；1=--check 下发现不合格；2=脚本自身异常。
"""
import argparse
import ast
import os
import pathlib
import py_compile
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

GUARD_LINES = [
    'try:  # Windows console/pipe defaults to cp936: lock UTF-8 or emoji print raises',
    '    sys.stdout.reconfigure(encoding="utf-8", errors="replace")',
    '    sys.stderr.reconfigure(encoding="utf-8", errors="replace")',
    'except Exception:',
    '    pass',
]


def default_dir():
    la = os.environ.get("LOCALAPPDATA")
    if la:
        return pathlib.Path(la) / "hermes" / "scripts"
    return pathlib.Path.home() / ".hermes" / "scripts"


def read_lossless(path):
    """非 UTF-8 字节原样保留：surrogateescape 往返是无损的。"""
    return path.read_bytes().decode("utf-8", errors="surrogateescape")


def write_lossless(path, text):
    path.write_bytes(text.encode("utf-8", errors="surrogateescape"))


def docstring_span(tree):
    body = tree.body
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        return body[0].lineno, body[0].end_lineno or body[0].lineno
    return 0, 0


def module_has_sys(tree):
    for node in tree.body:
        if isinstance(node, ast.Import) and any(a.name == "sys" for a in node.names):
            return True
        if isinstance(node, ast.ImportFrom) and node.module == "sys":
            return True
    return False


def guard_try_line(tree):
    """模块级 guard try 的起始行（body 里含 reconfigure 调用），没有则 0。"""
    for node in tree.body:
        if isinstance(node, ast.Try):
            for sub in ast.walk(node):
                if isinstance(sub, ast.Call) and isinstance(sub.func, ast.Attribute) \
                        and sub.func.attr == "reconfigure":
                    return node.lineno
    return 0


def insertion_index(text):
    """guard 应插入的行下标（0-based = 行号）：docstring / __future__ 之后。"""
    tree = ast.parse(text)
    pos = 0
    for node in tree.body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            pos = max(pos, node.end_lineno or 1)
            continue
        if isinstance(node, ast.ImportFrom) and node.module == "__future__":
            pos = max(pos, node.end_lineno or 1)
            continue
        break
    return pos


def strip_guard(text):
    """删掉旧 guard 块（含误插在 docstring 里的那份），返回 (文本, 删除数)。"""
    lines = text.splitlines()
    out, removed, i = [], 0, 0
    while i < len(lines):
        s = lines[i].strip()
        if s.startswith("try:") and ("reconfigure" in s or "cp936" in s):
            block = [ln.strip() for ln in lines[i:i + 5]]
            if block[1:5] == [ln.strip() for ln in GUARD_LINES[1:5]]:
                i += 5
                removed += 1
                continue
        out.append(lines[i])
        i += 1
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), removed


def inspect_source(text):
    """返回 (status, why)：ok / missing / misplaced。"""
    if "reconfigure(encoding" not in text:
        return "missing", "no-reconfigure"
    tree = ast.parse(text)
    if guard_try_line(tree) and module_has_sys(tree):
        return "ok", "module-level"
    return "misplaced", "not-module-level-or-no-import-sys"


def fix_text(text):
    text2, removed = strip_guard(text)
    d_start, d_end = docstring_span(ast.parse(text2))
    lines = text2.splitlines()
    keep = []
    for i, ln in enumerate(lines, start=1):
        if d_start and d_start <= i <= d_end and ln.strip() == "import sys":
            continue  # docstring 里的假 import sys
        keep.append(ln)
    lines = keep
    idx = insertion_index("\n".join(lines) + "\n")
    ins = []
    if not module_has_sys(ast.parse("\n".join(lines) + "\n")):
        ins.append("import sys")
    ins.extend(GUARD_LINES)
    lines[idx:idx] = ins
    new = "\n".join(lines) + ("\n" if text2.endswith("\n") else "")
    status, why = inspect_source(new)
    if status != "ok":
        raise RuntimeError("fix produced %s (%s)" % (status, why))
    return new, removed


def process(path, check_only):
    text = read_lossless(path)
    status, why = inspect_source(text)
    if status == "ok":
        return "ok"
    if "print(" not in text:
        return "skip(no-print)"
    if check_only:
        return "NEEDS-GUARD(%s)" % why
    new, removed = fix_text(text)
    write_lossless(path, new)
    py_compile.compile(str(path), doraise=True)
    return "fixed(removed-old=%d, was=%s)" % (removed, why)


def main():
    ap = argparse.ArgumentParser(description="ensure module-level UTF-8 guard")
    ap.add_argument("--dir", default=str(default_dir()))
    ap.add_argument("--check", action="store_true", help="only report, do not write")
    args = ap.parse_args()
    root = pathlib.Path(args.dir)
    if not root.is_dir():
        print("DIR_MISSING %s" % root)
        return 2
    bad = 0
    for p in sorted(root.glob("*.py")):
        try:
            res = process(p, args.check)
        except Exception as exc:  # noqa: BLE001
            res = "ERROR %s: %s" % (type(exc).__name__, str(exc)[:120])
        if res.startswith(("fixed", "NEEDS", "ERROR")):
            print("%-34s %s" % (p.name, res))
            if not res.startswith("fixed"):
                bad += 1
    print("--- done (%s) ---" % ("check-only" if args.check else "applied"))
    return 1 if (args.check and bad) else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:  # noqa: BLE001
        import traceback
        print(traceback.format_exc())
        sys.exit(2)
