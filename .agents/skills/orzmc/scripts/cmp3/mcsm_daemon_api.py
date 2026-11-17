#!/usr/bin/env python3
"""MCSM daemon 原生 API 探测（MCSManager Daemon 10）
daemon 端口 24444，API 与面板不同——daemon 用 token 鉴权（面板下发的临时 token）
"""
import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post

cfg = get_mcsm_config()
KEY = cfg["apikey"]
DID = cfg["daemon_id"]
IID = cfg["instance_id"]

# 拿 daemon addr + 面板给 daemon 的临时 token（download 凭证里可能有）
d = mcsm_api_post(cfg, "api/files/download", {"file_name": "/plugins/Geyser-Spigot.jar", "daemonId": DID, "uuid": IID})
daemon_addr = d["data"]["addr"].replace("localhost", cfg["url"].split("//")[1].split(":")[0])
if not daemon_addr.startswith("http"):
    daemon_addr = "http://" + daemon_addr
pwd = d["data"]["password"]
print(f"daemon: {daemon_addr} pwd: {pwd[:8]}...")

def daemon_api(path, params=None, method="GET", body=None, headers=None):
    url = f"{daemon_addr}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method, headers=headers or {})
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("User-Agent", "Mozilla/5.0")
    if body is not None:
        req.data = json.dumps(body).encode()
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode()[:500]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]
    except Exception as e:
        return -1, str(e)[:150]

print("\n=== daemon 端点探测（各种鉴权头）===")
tests = [
    ("/api/files/list", {"uuid": IID, "target": "/plugins", "page": 1, "page_size": 50}, None),
    ("/api/files/list", {"uuid": IID, "target": "/plugins", "page": 1, "page_size": 50, "token": pwd}, None),
    ("/api/files/list", {"uuid": IID, "target": "/plugins", "page": 1, "page_size": 50}, {"Authorization": "Bearer " + pwd}),
    ("/api/files/list", {"uuid": IID, "target": "/plugins", "page": 1, "page_size": 50}, {"X-MCSManager-Token": pwd}),
    ("/api/instance", {"uuid": IID}, None),
    ("/api/overview", {}, None),
]
for path, params, hdrs in tests:
    st, body = daemon_api(path, params, headers=hdrs)
    print(f"  {path} {str(hdrs or '')[:40]}: {st} | {body[:100]}")
