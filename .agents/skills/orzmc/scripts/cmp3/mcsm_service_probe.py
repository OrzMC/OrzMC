#!/usr/bin/env python3
"""MCSM：面板代理层文件端点探测（/api/service/* 系列，面板转发 daemon）"""
import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config

cfg = get_mcsm_config()
BASE = cfg["url"].rstrip("/")
KEY = cfg["apikey"]
DID = cfg["daemon_id"]
IID = cfg["instance_id"]

def api(path, params=None, method="GET", body=None):
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("User-Agent", "Mozilla/5.0")
    if body is not None:
        req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()[:400])
    except Exception as e:
        return -1, str(e)[:150]

P = {"apikey": KEY, "daemonId": DID, "uuid": IID}

print("=== /api/service/* 面板代理端点 ===")
candidates = [
    ("/api/service/file_list", {**P, "target": "/plugins", "page": 1, "page_size": 50}),
    ("/api/service/files/list", {**P, "target": "/plugins", "page": 1, "page_size": 50}),
    ("/api/service/remote_service_instances", {**P}),
    ("/api/instance_list", {**P}),
    ("/api/files/list", {**P, "target": "/plugins", "page": 1, "page_size": 50, "instanceUuid": IID}),
]
for path, params in candidates:
    st, d = api(path, params)
    if d is None:
        print(f"  {path}: {st} None")
    else:
        print(f"  {path}: {st} | {json.dumps(d, ensure_ascii=False)[:120]}")

print("\n=== 带 token 方式（非 apikey）===")
# 先登录拿 token
st, d = api("/api/auth/login", {}, method="POST", body={"username": "admin", "password": "x"})
print(f"  login: {st} | {json.dumps(d, ensure_ascii=False)[:80]}")
