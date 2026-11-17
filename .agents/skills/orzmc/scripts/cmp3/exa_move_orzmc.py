#!/usr/bin/env python3
"""Exaroton：确认 plugins/ 下 OrzMC jar + 尝试移动 update/ jar 到 plugins/
MCSM 思路: 无 move API 时用 下载→上传 两段式
"""
import urllib.request, json, os, time, hashlib

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
BASE = f"https://api.exaroton.com/v1/servers/{sid}/files"

def api(path, method="GET", data=None, ctype=None):
    req = urllib.request.Request(f"{BASE}{path}", data=data, method=method)
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("User-Agent", "Mozilla/5.0")
    if ctype:
        req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()

# 1. 下载 update/ 的 OrzMC
st, raw = api("/data/plugins/update/OrzMC-1.0.14-dev.237.jar/")
print("下载 update/OrzMC:", st, len(raw) if st == 200 else raw[:80])
if st != 200:
    sys.exit(1)

# 2. 上传到 plugins/
st2, resp2 = api("/data/plugins/OrzMC-1.0.14-dev.237.jar/", "PUT", raw, "application/java-archive")
print("上传到 plugins/OrzMC-1.0.14-dev.237.jar:", st2, resp2[:80] if st2 == 200 else resp2[:120])
time.sleep(2)

# 3. 删除 update/ 里的（防止重复）
st3, resp3 = api("/data/plugins/update/OrzMC-1.0.14-dev.237.jar/", "DELETE")
print("删除 update/OrzMC:", st3, resp3[:80])
