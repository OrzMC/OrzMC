#!/usr/bin/env python3
"""语言无关一致性套件运行器（spec-owned，仅标准库）。

用法：
  python3 scripts/conformance/run.py --adapter "python3 scripts/conformance/reference.py"
  python3 scripts/conformance/run.py --list
  python3 scripts/conformance/run.py --adapter "<cmd>" --strict --filter cache

适配器协议（见 scripts/conformance/README.md）：
  每个 fixture 调用一次：把请求 JSON 写到适配器 stdin，
  适配器把响应 JSON 写到 stdout：{"ok":true,"data":...} 或 {"ok":false,"code":...,"message":...}。
  code == "E_UNSUPPORTED_OP" 视为 SKIP（--strict 时计为失败）。
"""
from __future__ import annotations

import argparse
import json
import shlex
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "docs" / "spec" / "fixtures"
MISSING = object()


# ---------------------------------------------------------------- JSON 工具
def same(a, b) -> bool:
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    if isinstance(a, bool):
        return a is b
    if a is None or b is None:
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return a == b
    if type(a) is not type(b):
        return False
    if isinstance(a, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, dict):
        return set(a) == set(b) and all(same(a[k], b[k]) for k in a)
    return a == b


def resolve(actual, dotted):
    cur = actual
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return MISSING
    return cur


_SUFFIXES = [("NotContains", "notcontains"), ("Contains", "contains"),
             ("Order", "order"), ("Count", "count"), ("Set", "set")]


def match_key(key, exp, act, path):
    kind, base = None, key
    for suf, k in _SUFFIXES:
        if key.endswith(suf):
            kind, base = k, key[: -len(suf)]
            break
    actual = resolve(act, base)
    if actual is MISSING:
        return [f"{path}: 缺失字段 {base}"]
    if kind is None:
        return matches(exp, actual, path)
    if not isinstance(actual, list):
        return [f"{path}: 期望列表，实际 {type(actual).__name__}"]
    if kind == "contains":
        miss = [e for e in exp if not any(same(e, a) for a in actual)]
        return [f"{path}: 缺少元素 {m!r}" for m in miss]
    if kind == "notcontains":
        bad = [e for e in exp if any(same(e, a) for a in actual)]
        return [f"{path}: 不应包含 {b!r}" for b in bad]
    if kind == "order":
        i = -1
        for e in exp:
            nxt = next((j for j in range(i + 1, len(actual)) if same(e, actual[j])), -1)
            if nxt < 0:
                return [f"{path}: 相对顺序不满足（找不到 {e!r}）"]
            i = nxt
        return []
    if kind == "count":
        return [] if len(actual) == exp else [f"{path}: 期望 {exp} 项，实际 {len(actual)} 项"]
    if kind == "set":
        exp_s = sorted(map(repr, exp))
        act_s = sorted(map(repr, actual))
        return [] if exp_s == act_s else [f"{path}: 集合不等 期望={exp_s} 实际={act_s}"]
    return [f"{path}: 未知断言后缀"]


def matches(exp, act, path=""):
    if isinstance(exp, dict):
        if not isinstance(act, dict):
            return [f"{path}: 期望 object，实际 {type(act).__name__}"]
        errs = []
        for k, v in exp.items():
            errs += match_key(k, v, act, f"{path}.{k}" if path else k)
        return errs
    if isinstance(exp, list):
        return [] if same(exp, act) else [f"{path}: 期望 {exp!r}，实际 {act!r}"]
    return [] if same(exp, act) else [f"{path}: 期望 {exp!r}，实际 {act!r}"]


# ---------------------------------------------------------------- 发现 / 校验
def discover():
    out = []
    for p in sorted(FIXTURES.rglob("*.json")):
        rel = p.relative_to(FIXTURES)
        if rel.parts[0] in ("snapshots", "schema"):
            continue
        out.append(p)
    return out


def validate(p, fx):
    errs = []
    for f in ("specVersion", "id", "area", "given"):
        if f not in fx:
            errs.append(f"缺少字段 {f}")
    area = fx.get("area")
    if area and area != p.parent.name:
        errs.append(f"area={area!r} 与目录 {p.parent.name!r} 不一致")
    if "given" in fx and "operation" not in fx["given"]:
        errs.append("given 缺少 operation")
    if "expect" not in fx and "expectError" not in fx:
        errs.append("缺少 expect / expectError")
    return errs


# ---------------------------------------------------------------- 执行
def invoke(adapter_cmd, request, timeout=60):
    proc = subprocess.run(adapter_cmd, input=json.dumps(request),
                          capture_output=True, text=True, timeout=timeout)
    if not proc.stdout.strip():
        raise RuntimeError(f"适配器无输出（exit={proc.returncode}）stderr={proc.stderr.strip()[:400]}")
    return json.loads(proc.stdout), proc.stderr.strip()


def run_one(adapter_cmd, p):
    fx = json.loads(p.read_text())
    verrs = validate(p, fx)
    if verrs:
        return "FAIL", f"fixture 结构错误: {'; '.join(verrs)}"
    fid = fx["id"]
    request = dict(fx["given"])
    request.setdefault("id", fid)
    request.setdefault("specVersion", fx["specVersion"])
    try:
        resp, stderr = invoke(adapter_cmd, request)
    except Exception as e:  # noqa: BLE001
        return "FAIL", f"调用适配器失败: {e}"
    if not isinstance(resp, dict) or "ok" not in resp:
        return "FAIL", f"非法响应: {resp!r}"
    if not resp["ok"]:
        code = resp.get("code", "?")
        if "expectError" in fx:
            want = fx["expectError"]
            if want.get("code") and want["code"] != code:
                return "FAIL", f"错误码 期望={want['code']} 实际={code}"
            return "PASS", f"预期错误 {code}"
        if code == "E_UNSUPPORTED_OP":
            return "SKIP", f"适配器不支持操作 {request.get('operation')}"
        return "FAIL", f"错误 {code}: {resp.get('message', '')}"
    if "expectError" in fx:
        return "FAIL", f"期望错误 {fx['expectError'].get('code')}，但返回成功"
    errs = matches(fx.get("expect", {}), resp.get("data"), fid)
    if errs:
        return "FAIL", "; ".join(errs[:8])
    return "PASS", ""


def main():
    global FIXTURES
    ap = argparse.ArgumentParser(description="OrzMC 一致性套件运行器")
    ap.add_argument("--adapter", help="适配器命令（如 'python3 scripts/conformance/reference.py'）")
    ap.add_argument("--fixtures", default=str(FIXTURES))
    ap.add_argument("--filter", default="", help="只跑 id/path 含该子串的样例")
    ap.add_argument("--strict", action="store_true", help="SKIP 视为失败")
    ap.add_argument("--list", action="store_true", help="列出样例后退出")
    args = ap.parse_args()

    FIXTURES = Path(args.fixtures).resolve()
    files = discover()
    if args.filter:
        files = [p for p in files if args.filter in str(p.relative_to(FIXTURES))]
    if args.list:
        for p in files:
            fx = json.loads(p.read_text())
            print(f"{fx['id']:<48} {fx['given'].get('operation')}")
        print(f"\n共 {len(files)} 个样例")
        return 0
    if not args.adapter:
        ap.error("需要 --adapter（或用 --list 查看样例）")
    cmd = shlex.split(args.adapter)

    counts = {"PASS": 0, "FAIL": 0, "SKIP": 0}
    failures = []
    for p in files:
        status, msg = run_one(cmd, p)
        counts[status] += 1
        fx = json.loads(p.read_text())
        mark = {"PASS": "✓", "FAIL": "✗", "SKIP": "·"}[status]
        print(f"{mark} {status:<4} {fx['id']:<48} {msg}")
        if status == "FAIL":
            failures.append((fx["id"], msg))

    print(f"\nPASS={counts['PASS']} FAIL={counts['FAIL']} SKIP={counts['SKIP']}")
    if failures:
        print("\n失败明细:")
        for fid, msg in failures:
            print(f"  - {fid}: {msg}")
    if counts["FAIL"] or (args.strict and counts["SKIP"]):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
