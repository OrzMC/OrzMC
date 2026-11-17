#!/usr/bin/env python3
"""MCSM 文件查询 API 深挖：list 参数变体 + 可能的其他查询端点"""
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

print("=== 1. list 参数变体（target 各种写法）===")
variants = [
    ("target=/plugins&page=1&page_size=50", {**P, "target": "/plugins", "page": 1, "page_size": 50}),
    ("target=/plugins/&page=1&page_size=50", {**P, "target": "/plugins/", "page": 1, "page_size": 50}),
    ("target=plugins&page=1&page_size=50", {**P, "target": "plugins", "page": 1, "page_size": 50}),
    ("target=/&page=1&page_size=50", {**P, "target": "/", "page": 1, "page_size": 50}),
    ("target=./&page=1&page_size=50", {**P, "target": "./", "page": 1, "page_size": 50}),
    ("target=/plugins&page=1&page_size=5", {**P, "target": "/plugins", "page": 1, "page_size": 5}),
]
for name, params in variants:
    st, d = api("/api/files/list", params)
    if st == 200:
        data = d.get("data", {})
        print(f"  ✅ {name}: total={data.get('total')} items={len(data.get('items', []))}")
    else:
        print(f"  ❌ {name}: {st} {d.get('data','')[:60]}")

print("\n=== 2. POST body 方式 list ===")
for body in [
    {"target": "/plugins", "page": 1, "page_size": 50},
    {"file_name": "/plugins"},
    {"path": "/plugins"},
]:
    st, d = api("/api/files/list", P, method="POST", body=body)
    if d is None:
        print(f"  POST body={json.dumps(body)[:50]}: {st} None")
    else:
        print(f"  POST body={json.dumps(body)[:50]}: {st} {json.dumps(d, ensure_ascii=False)[:80]}")

print("\n=== 3. 可能的其他文件查询端点 ===")
candidates = [
    ("/api/files/info", {**P, "target": "/plugins"}),
    ("/api/files/get", {**P, "target": "/plugins/Geyser-Spigot.jar"}),
    ("/api/files/tree", {**P, "target": "/plugins"}),
    ("/api/files/search", {**P, "target": "/plugins", "keyword": "Geyser"}),
    ("/api/files/exists", {**P, "target": "/plugins/Geyser-Spigot.jar"}),
]
for path, params in candidates:
    st, d = api(path, params)
    print(f"  {path}: {st} | {json.dumps(d, ensure_ascii=False)[:100]}")
