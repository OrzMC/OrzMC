#!/usr/bin/env python3
"""Exaroton 插件同步（上传 → 回读 sha256 校验 → 删旧 jar）

用法：
  python3 exa_sync_plugins.py --plan plan.json [--dry-run]
  plan.json = [{"local": "/abs/new.jar", "remote": "plugins/Name-1.2.3.jar", "old": "plugins/Name-1.2.2.jar"}, ...]

要点（2026-11-02 实测）：
- 服务器必须 OFFLINE（status 0）；运行中写文件会被拒
- PUT /servers/{id}/files/data/{path}/ ，body=裸字节，Content-Type application/octet-stream
- 列目录 GET /files/info/{dir}/.  → data.children；读 GET /files/data/{path}/
- 删 DELETE /files/data/{path}/
- 核心（软件版本）不在此脚本能力内：只能面板选版本
"""
import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request

BASE = "https://api.exaroton.com/v1"


def env(key, default=""):
    p = os.path.expanduser("~/.hermes/.env")
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return default


KEY = env("EXAROTON_API_KEY")
SID = env("EXAROTON_SERVER_ID", "")
H = {"Authorization": "Bearer " + KEY, "User-Agent": "HermesAgent/1.0"}


def req(method, path, data=None, ctype=None, timeout=900):
    r = urllib.request.Request(BASE + path, data=data, method=method, headers=H)
    if ctype:
        r.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(r, timeout=timeout) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def server_status():
    s, b = req("GET", "/servers/%s" % SID)
    d = json.loads(b)["data"]
    return d.get("status"), d.get("software", {})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--plan", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    plan = json.load(open(a.plan, encoding="utf-8"))
    st, soft = server_status()
    print("服务器 %s | status=%s | %s %s" % (SID, st, soft.get("name"), soft.get("version")))
    if st not in (0, None) and not a.dry_run:
        print("❌ 服务器非离线（status=%s），先停服再同步" % st)
        return 1

    ok_all = True
    for item in plan:
        local, remote = item["local"], item["remote"]
        name = os.path.basename(local)
        lsha = sha_file(local)
        print("\n── %s → %s (%.1f MB)" % (name, remote, os.path.getsize(local) / 1e6))
        if a.dry_run:
            continue
        t0 = time.time()
        with open(local, "rb") as f:
            s, b = req("PUT", "/servers/%s/files/data/%s/" % (SID, remote), data=f.read(),
                       ctype="application/octet-stream")
        if s != 200:
            print("   ❌ 上传 HTTP %s: %s" % (s, b[:120]))
            ok_all = False
            continue
        print("   上传 200 (%.1fs)" % (time.time() - t0))
        s2, blob = req("GET", "/servers/%s/files/data/%s/" % (SID, remote))
        same = sha_bytes(blob) == lsha
        print("   回读 %s | sha256 %s %s" % (s2, sha_bytes(blob)[:16], "✅" if same else "❌ 不一致"))
        ok_all = ok_all and same

    if a.dry_run:
        print("\n[dry-run] 未写入")
        return 0

    print("\n── 删旧 jar ──")
    for item in plan:
        old = item.get("old")
        if not old or old == item["remote"]:
            continue
        s, b = req("DELETE", "/servers/%s/files/data/%s/" % (SID, old))
        print("   🗑 %s → %s" % (old, s))

    s, b = req("GET", "/servers/%s/files/info/plugins/." % SID)
    jars = sorted(c["name"] for c in json.loads(b)["data"]["children"] if c["name"].endswith(".jar"))
    print("\n当前 plugins jar (%d)：%s" % (len(jars), ", ".join(jars)))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
