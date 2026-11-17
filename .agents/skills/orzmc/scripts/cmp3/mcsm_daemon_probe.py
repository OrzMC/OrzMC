#!/usr/bin/env python3
"""MCSM：daemon 直连 list 探测（面板转发 list 空 items，试 daemon 原生 API）
daemon 端口/地址从 download 凭证响应里拿 addr
"""
import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post

cfg = get_mcsm_config()
KEY = cfg["apikey"]
DID = cfg["daemon_id"]
IID = cfg["instance_id"]

# 1. 从 download 凭证拿 daemon addr
d = mcsm_api_post(cfg, "api/files/download", {"file_name": "/plugins/Geyser-Spigot.jar", "daemonId": DID, "uuid": IID})
if not d or d.get("status") != 200:
    print("❌ download 凭证失败:", str(d)[:100])
    sys.exit(1)
daemon_addr = d["data"]["addr"].replace("localhost", cfg["url"].split("//")[1].split(":")[0])
if not daemon_addr.startswith("http"):
    daemon_addr = "http://" + daemon_addr
pwd = d["data"]["password"]
print(f"daemon addr: {daemon_addr}")

# 2. daemon 直连 list（daemon 端口 24444 常见；download addr 就是 daemon）
def daemon_api(path, params=None, method="GET", body=None):
    url = f"{daemon_addr}{path}"
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
            return r.status, r.read().decode()[:600]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:300]
    except Exception as e:
        return -1, str(e)[:150]

print("\n=== daemon 直连探测 ===")
for path, params in [
    ("/api/files/list", {"uuid": IID, "target": "/plugins", "page": 1, "page_size": 50, "apikey": KEY}),
    ("/api/files/list", {"uuid": IID, "target": "/plugins", "page": 1, "page_size": 50}),
    ("/api/files/list", {"target": "/plugins", "page": 1, "page_size": 50}),
    ("/api/files/list", {"uuid": IID, "target": "/", "page": 1, "page_size": 50}),
]:
    st, body = daemon_api(path, params)
    print(f"  GET {path} {list(params.keys())}: {st} | {body[:150]}")

# 3. daemon 根路径（看是什么服务）
st, body = daemon_api("/")
print(f"\n  GET /: {st} | {body[:200]}")
