#!/usr/bin/env python3
"""MCSM 文件 API 精确验证：list 列目录 + PUT 写文件 + mkdir + delete
（写操作只对测试文件，测完清理）
"""
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

print("=== 1. GET /api/files/list 列 /plugins 目录 ===")
st, d = api("/api/files/list", {**P, "target": "/plugins"})
if st == 200:
    items = d.get("data", {}).get("items", [])
    print(f"  ✅ 200 成功！共 {len(items)} 项")
    for it in items[:25]:
        typ = "📁" if it.get("type") == "directory" else "📄"
        print(f"    {typ} {it.get('name')} | {it.get('size', '')}B")
else:
    print(f"  ❌ {st}: {d}")

print("\n=== 2. PUT /api/files/ 写测试文件 ===")
st, d = api("/api/files/", {**P}, method="PUT", body={"target": "/plugins/api_probe_test.txt", "text": "MCSM API probe test\n"})
print(f"  PUT 新文件: {st} | {json.dumps(d, ensure_ascii=False)[:120]}")

time.sleep(1)
print("\n=== 3. 验证写入（list 确认）===")
st, d = api("/api/files/list", {**P, "target": "/plugins"})
if st == 200:
    names = [it["name"] for it in d.get("data", {}).get("items", []) if it.get("name") == "api_probe_test.txt"]
    print(f"  api_probe_test.txt 在列表中: {'✅' if names else '❌'}")

print("\n=== 4. POST /api/files/mkdir 建目录 ===")
st, d = api("/api/files/mkdir", {**P}, method="POST", body={"target": "/plugins/api_probe_dir"})
print(f"  mkdir: {st} | {json.dumps(d, ensure_ascii=False)[:120]}")

print("\n=== 5. DELETE 清理测试文件 ===")
for path, body in [
    ("/api/files/delete", {"targets": ["/plugins/api_probe_test.txt", "/plugins/api_probe_dir"]}),
    ("/api/files/", {"target": "/plugins/api_probe_test.txt"}),
]:
    st, d = api(path, {**P}, method="DELETE", body=body)
    print(f"  DELETE {path}: {st} | {json.dumps(d, ensure_ascii=False)[:120]}")

print("\n=== 6. 确认清理 ===")
st, d = api("/api/files/list", {**P, "target": "/plugins"})
if st == 200:
    names = [it["name"] for it in d.get("data", {}).get("items", []) if "api_probe" in it.get("name", "")]
    print(f"  残留 api_probe 文件: {'❌ ' + str(names) if names else '✅ 已清理干净'}")
