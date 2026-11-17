#!/usr/bin/env python3
"""MCSM 开放 API 全面探测（只读端点，不破坏）"""
import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config

cfg = get_mcsm_config()
BASE = cfg["url"]
KEY = cfg["apikey"]
DID = cfg["daemon_id"]
IID = cfg["instance_id"]

HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "X-Requested-With": "XMLHttpRequest",
}

def call(path, method="GET", params=None, body=None):
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS, method=method)
    if body is not None:
        req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status, r.read().decode()[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return -1, str(e)[:200]

print("=== 1. 面板版本探测 ===")
for path in ["/api/overview", "/api/service/remote_services_system", "/api/instance"]:
    st, body = call(path, params={"apikey": KEY})
    print(f"  GET {path}: {st} | {body[:120]}")

print("\n=== 2. 实例信息（已知 ID）===")
st, body = call("/api/instance", params={"apikey": KEY, "daemonId": DID, "uuid": IID})
print(f"  GET /api/instance: {st}")
try:
    d = json.loads(body)
    print(f"  status: {d.get('data', {}).get('status')} | 版本: {d.get('data', {}).get('info', {}).get('version')}")
except Exception:
    print(f"  body: {body[:200]}")

print("\n=== 3. 文件 API 探测（全部 GET 只读）===")
tests = [
    ("文件列表", "/api/files/list", {"apikey": KEY, "daemonId": DID, "uuid": IID, "target": "/plugins", "page": 1, "page_size": 50}),
    ("文件列表POST", "/api/files/list", {"apikey": KEY, "daemonId": DID, "uuid": IID, "target": "/plugins", "page": 1, "page_size": 50}),
    ("读文件", "/api/files/download", {"apikey": KEY, "file_name": "/plugins/Geyser-Spigot/config.yml"}),
]
for name, path, params in tests:
    st, body = call(path, "POST" if name.endswith("POST") else "GET", params=params)
    print(f"  {name}: {st} | {body[:150]}")
