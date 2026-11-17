#!/usr/bin/env python3
"""MCSM list 参数精确测试：page + page_size 组合"""
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
        return e.code, json.loads(e.read().decode()[:500])
    except Exception as e:
        return -1, str(e)[:150]

P = {"apikey": KEY, "daemonId": DID, "uuid": IID}

print("=== list 参数组合测试 ===")
combos = [
    ("page=1&page_size=50", {**P, "target": "/plugins", "page": 1, "page_size": 50}),
    ("page=1&pageSize=50", {**P, "target": "/plugins", "page": 1, "pageSize": 50}),
    ("page=1&page_size=100", {**P, "target": "/plugins", "page": 1, "page_size": 100}),
    ("page=1&page_size=10", {**P, "target": "/plugins", "page": 1, "page_size": 10}),
]
for name, params in combos:
    st, d = api("/api/files/list", params)
    if st == 200:
        items = d.get("data", {}).get("items", [])
        print(f"  ✅ {name}: total={d.get('data',{}).get('total')} items={len(items)}")
        for it in items[:5]:
            print(f"      {it.get('type','?'):10s} {it.get('name')}")
    else:
        print(f"  ❌ {name}: {st} {d.get('data','')[:80]}")
