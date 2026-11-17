#!/usr/bin/env python3
"""MCSM：看完整 absolutePath + 试实例目录路径"""
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

# 1. 完整 absolutePath
st, d = api("/api/files/list", {**P, "target": "/plugins", "page": 1, "page_size": 50})
print("完整 absolutePath:", d.get("data", {}).get("absolutePath"))

# 2. 从实例信息拿实例目录
st, d = api("/api/instance", P)
if st == 200:
    inst = d.get("data", {})
    print("实例字段 keys:", list(inst.keys())[:20])
    # 常见字段
    for k in ["config", "info"]:
        if k in inst:
            v = inst[k]
            if isinstance(v, dict):
                interesting = {kk: vv for kk, vv in v.items() if "path" in kk.lower() or "dir" in kk.lower() or "run" in kk.lower()}
                print(f"  {k}: {json.dumps(interesting, ensure_ascii=False)[:200]}")
