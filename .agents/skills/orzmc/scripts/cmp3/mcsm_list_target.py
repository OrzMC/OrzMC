#!/usr/bin/env python3
"""MCSM list target 路径格式测试：相对 vs 绝对 vs 根"""
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

print("=== target 路径格式测试（page=1&page_size=50 固定）===")
targets = ["/plugins", "plugins", "/", "C:/Users", "C:\\Users", "./", ""]
for t in targets:
    st, d = api("/api/files/list", {**P, "target": t, "page": 1, "page_size": 50})
    if st == 200:
        data = d.get("data", {})
        items = data.get("items", [])
        print(f"  target='{t}': ✅ total={data.get('total')} items={len(items)} absPath={str(data.get('absolutePath'))[:60]}")
        if items:
            for it in items[:3]:
                print(f"      {it.get('type','?'):10s} {it.get('name')}")
    else:
        print(f"  target='{t}': ❌ {st} {d.get('data','')[:60]}")
