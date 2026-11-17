#!/usr/bin/env python3
"""MCSM list 修正测试：page 从 0 开始（源码确认）+ fileName 过滤"""
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
        return e.code, json.loads(e.read().decode()[:300])
    except Exception as e:
        return -1, str(e)[:150]

P = {"apikey": KEY, "daemonId": DID, "uuid": IID}

print("=== page=0 测试（源码确认从 0 开始）===")
tests = [
    ("page=0&page_size=50", {**P, "target": "/plugins", "page": 0, "page_size": 50}),
    ("page=0&page_size=100", {**P, "target": "/plugins", "page": 0, "page_size": 100}),
    ("page=0(默认page_size)", {**P, "target": "/plugins", "page": 0}),
    ("page=0 target=/", {**P, "target": "/", "page": 0, "page_size": 50}),
    ("page=0 fileName=Geyser", {**P, "target": "/plugins", "page": 0, "page_size": 50, "file_name": "Geyser"}),
]
for name, params in tests:
    st, d = api("/api/files/list", params)
    if st == 200:
        data = d.get("data", {})
        items = data.get("items", [])
        print(f"  ✅ {name}: total={data.get('total')} items={len(items)}")
        if items:
            for it in items[:5]:
                t = it.get('type') if isinstance(it.get('type'), str) else str(it.get('type'))
                print(f"      {t:10s} {it.get('name')}")
    else:
        print(f"  ❌ {name}: {st} {d.get('data','')[:80]}")
