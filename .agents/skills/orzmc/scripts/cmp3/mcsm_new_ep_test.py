#!/usr/bin/env python3
"""MCSM 新端点实测：touch(新建文件) / copy / move(PUT!) / compress
全部用测试文件，测完 DELETE 清理
"""
import sys, os, json, time, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_api_post, mcsm_download

cfg = get_mcsm_config()
BASE = cfg["url"].rstrip("/")
KEY = cfg["apikey"]
DID = cfg["daemon_id"]
IID = cfg["instance_id"]
HOST = BASE.split("//")[1].split(":")[0]

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
        return -1, {"error": str(e)[:150]}

P = {"apikey": KEY, "daemonId": DID, "uuid": IID}
T = "/api_probe_ep"

print("=== 1. touch 新建文件 ===")
st, d = api("/api/files/touch", P, "POST", {"target": T + ".txt"})
print(f"  touch: {st} | {json.dumps(d, ensure_ascii=False)[:80]}")

# 用 PUT 写内容
time.sleep(1)
st, d = api("/api/files/", P, "PUT", {"target": T + ".txt", "text": "hello move test\n"})
print(f"  写入内容: {st} | {json.dumps(d, ensure_ascii=False)[:60]}")

print("\n=== 2. copy 复制 ===")
st, d = api("/api/files/copy", P, "POST", {"targets": [T + ".txt"]})
print(f"  copy: {st} | {json.dumps(d, ensure_ascii=False)[:80]}")

print("\n=== 3. move 移动（PUT！之前误用 POST）===")
st, d = api("/api/files/move", P, "PUT", {"targets": [T + "-copy.txt", T + "-moved.txt"]})
print(f"  move(PUT): {st} | {json.dumps(d, ensure_ascii=False)[:80]}")

print("\n=== 4. 验证文件状态（list fileName 过滤）===")
for fname in ["api_probe_ep"]:
    st, d = api("/api/files/list", {**P, "target": "/", "page": 0, "page_size": 50, "file_name": fname})
    if st == 200:
        for it in d.get("data", {}).get("items", []):
            print(f"    {it.get('name')} type={it.get('type')} size={it.get('size')}")

print("\n=== 5. compress 压缩 ===")
st, d = api("/api/files/compress", P, "POST", {"source": "/", "targets": [T + "-moved.txt"], "type": 0, "code": "utf-8"})
print(f"  compress: {st} | {json.dumps(d, ensure_ascii=False)[:120]}")

print("\n=== 6. 清理测试文件 ===")
time.sleep(2)
st, d = api("/api/files/", P, "DELETE", {"targets": [T + ".txt", T + "-copy.txt", T + "-moved.txt", T + "-moved.zip"]})
print(f"  DELETE: {st} | {json.dumps(d, ensure_ascii=False)[:80]}")
time.sleep(1)
st, d = api("/api/files/list", {**P, "target": "/", "page": 0, "page_size": 50, "file_name": "api_probe_ep"})
items = d.get("data", {}).get("items", []) if st == 200 else []
print(f"  残留: {'❌ ' + str([i['name'] for i in items]) if items else '✅ 已清理干净'}")
