#!/usr/bin/env python3
"""MCSM compress 正确用法实测（源码确认）
type=1 压缩: source=zip输出路径, targets=文件数组
type=0 解压: source=zip路径, targets=目标目录(字符串)
"""
import sys, os, json, time, urllib.request, urllib.parse
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
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode()[:300])
        except Exception:
            return e.code, {}
    except Exception as e:
        return -1, {"error": str(e)[:200]}

P = {"apikey": KEY, "daemonId": DID, "uuid": IID}
T = "/api_probe_cmp"

# 准备: 建目录 + 写文件 + 建子目录
for mk in [T, T + "/sub"]:
    st, d = api("/api/files/mkdir", P, "POST", {"target": mk})
    print(f"mkdir {mk}: {st}")
st, d = api("/api/files/", P, "PUT", {"target": T + "/a.txt", "text": "aaa\n"})
print(f"写 a.txt: {st}")
st, d = api("/api/files/touch", P, "POST", {"target": T + "/sub/b.txt"})
print(f"touch b.txt: {st}")

print("\n=== 1. compress type=1（压缩）source=/api_probe_cmp.zip targets=[目录] ===")
st, d = api("/api/files/compress", P, "POST", {"source": "/api_probe_cmp.zip", "targets": [T], "type": 1, "code": "utf-8"})
print(f"  compress: {st} | {json.dumps(d, ensure_ascii=False)[:100]}")
time.sleep(4)

print("\n=== 2. 验证 zip 生成 ===")
st, d = api("/api/files/list", {**P, "target": "/", "page": 0, "page_size": 50, "file_name": "api_probe_cmp"})
if st == 200:
    for it in d.get("data", {}).get("items", []):
        print(f"    {it.get('name')} type={it.get('type')} size={it.get('size')}")

print("\n=== 3. compress type=0（解压）source=zip targets=目标目录 ===")
st, d = api("/api/files/compress", P, "POST", {"source": "/api_probe_cmp.zip", "targets": "/api_probe_unzip", "type": 0, "code": "utf-8"})
print(f"  unzip: {st} | {json.dumps(d, ensure_ascii=False)[:100]}")
time.sleep(4)
st, d = api("/api/files/list", {**P, "target": "/api_probe_unzip", "page": 0, "page_size": 50, "file_name": ""})
print(f"  解压目录 list(无过滤): {st} items={len(d.get('data',{}).get('items',[])) if st==200 else 'err'}")
st, d = api("/api/files/list", {**P, "target": "/api_probe_unzip", "page": 0, "page_size": 50, "file_name": "a"})
if st == 200:
    for it in d.get("data", {}).get("items", []):
        print(f"    {it.get('name')} type={it.get('type')}")

print("\n=== 4. 清理 ===")
st, d = api("/api/files/", P, "DELETE", {"targets": [T, "/api_probe_cmp.zip", "/api_probe_unzip"]})
print(f"  DELETE: {st}")
time.sleep(2)
st, d = api("/api/files/list", {**P, "target": "/", "page": 0, "page_size": 50, "file_name": "api_probe_cmp"})
items = d.get("data", {}).get("items", []) if st == 200 else []
st2, d2 = api("/api/files/list", {**P, "target": "/", "page": 0, "page_size": 50, "file_name": "api_probe_unzip"})
items += d2.get("data", {}).get("items", []) if st2 == 200 else []
print(f"  残留: {'❌ ' + str([i['name'] for i in items]) if items else '✅ 已清理干净'}")
