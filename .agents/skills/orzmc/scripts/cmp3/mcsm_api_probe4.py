#!/usr/bin/env python3
"""MCSM 文件 API 精确验证 v2：list 带 page + DELETE /api/files/ 正确用法 + 清理"""
import sys, os, json, urllib.request, urllib.parse, time
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

print("=== 1. GET /api/files/list 带 page=1 ===")
st, d = api("/api/files/list", {**P, "target": "/plugins", "page": 1})
if st == 200:
    items = d.get("data", {}).get("items", [])
    total = d.get("data", {}).get("total")
    print(f"  ✅ 200! total={total}, 本页 {len(items)} 项, absolutePath={d.get('data',{}).get('absolutePath')}")
    for it in items[:30]:
        typ = "📁" if it.get("type") == "directory" else "📄"
        print(f"    {typ} {it.get('name')} | {it.get('size','')}B")
else:
    print(f"  ❌ {st}: {d}")

print("\n=== 2. DELETE /api/files/ 正确用法（删测试目录）===")
st, d = api("/api/files/", {**P}, method="DELETE", body={"targets": ["/plugins/api_probe_dir"]})
print(f"  DELETE /api/files/ targets=[api_probe_dir]: {st} | {json.dumps(d, ensure_ascii=False)[:150]}")

time.sleep(1)
print("\n=== 3. list 确认清理 ===")
st, d = api("/api/files/list", {**P, "target": "/plugins", "page": 1})
if st == 200:
    names = [it["name"] for it in d.get("data", {}).get("items", []) if "api_probe" in it.get("name", "")]
    print(f"  残留 api_probe: {'❌ ' + str(names) if names else '✅ 已清理干净'}")

print("\n=== 4. list 分页测试（page=1 全量 vs 数量）===")
st, d = api("/api/files/list", {**P, "target": "/plugins", "page": 1, "page_size": 100})
if st == 200:
    items = d.get("data", {}).get("items", [])
    print(f"  page_size=100: {len(items)} 项")
    # 打印所有 jar 和目录
    for it in items:
        print(f"    {it.get('type','?'):10s} {it.get('name')}")
