#!/usr/bin/env python3
"""MCSM list fileName 过滤深度验证（源码确认 type: 1=文件 0=目录）"""
import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config

cfg = get_mcsm_config()
BASE = cfg["url"].rstrip("/")
KEY = cfg["apikey"]
DID = cfg["daemon_id"]
IID = cfg["instance_id"]

def api(path, params=None):
    url = f"{BASE}{path}?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("Content-Type", "application/json; charset=utf-8")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode()[:300])
    except Exception as e:
        return {"error": str(e)}

P = {"apikey": KEY, "daemonId": DID, "uuid": IID}

print("=== fileName 过滤测试（源码: type 1=文件 0=目录）===")
for target, fname in [
    ("/plugins", "jar"),      # 所有 jar
    ("/plugins", "Geyser"),   # Geyser 相关
    ("/plugins", "Death"),    # DeathChest
    ("/plugins", "floodgate"),# floodgate（应无）
    ("/", "paper"),           # 根目录 paper jar
]:
    d = api("/api/files/list", {**P, "target": target, "page": 0, "page_size": 50, "file_name": fname})
    if d.get("status") == 200:
        items = d["data"]["items"]
        print(f"  {target} 搜 '{fname}': total={d['data']['total']}")
        for it in items:
            t = "📁目录" if it.get("type") == 0 else "📄文件"
            print(f"      {t} {it.get('name')} | {it.get('size','')}B | mode={it.get('mode')}")
    else:
        print(f"  {target} 搜 '{fname}': ❌ {d.get('data') or d.get('error')}")

print("\n=== 全量（无 fileName）对照 ===")
d = api("/api/files/list", {**P, "target": "/plugins", "page": 0, "page_size": 50})
print(f"  无 fileName: status={d.get('status')} total={d.get('data',{}).get('total')} items={len(d.get('data',{}).get('items',[]))}")
