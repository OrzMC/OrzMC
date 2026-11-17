#!/usr/bin/env python3
"""MCSM：DELETE 删文件验证 + PUT 写已存在文件 + 用 list 兜底确认
（测试文件：先上传创建，再删）
"""
import sys, os, json, urllib.request, urllib.parse, time, hashlib
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
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode()[:500])
    except Exception as e:
        return -1, str(e)[:150]

P = {"apikey": KEY, "daemonId": DID, "uuid": IID}

# 1. 上传创建测试文件（用 mcsm_api_post 的 upload 流程）
content = b"MCSM delete test file\n"
d = mcsm_api_post(cfg, "api/files/upload",
                  {"upload_dir": "/", "daemonId": DID, "uuid": IID})
if d and d.get("status") == 200:
    addr = d["data"]["addr"].replace("localhost", HOST)
    url = f"http://{addr}/upload/{d['data']['password']}"
    boundary = "----hb-" + str(int(time.time()))
    body = b""
    body += f"--{boundary}\r\n".encode()
    body += b'Content-Disposition: form-data; name="file"; filename="api_probe_del.txt"\r\n'
    body += b"Content-Type: application/octet-stream\r\n\r\n"
    body += content
    body += f"\r\n--{boundary}--\r\n".encode()
    try:
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
        with urllib.request.urlopen(req, timeout=60) as r:
            print("1. 上传创建 api_probe_del.txt:", r.status)
    except Exception as e:
        print("1. 上传失败:", e)
else:
    print("1. 凭证失败:", str(d)[:80])

# 2. PUT 写这个已存在的文件（技能说只能写已存在）
time.sleep(2)
st, resp = api("/api/files/", {**P}, method="PUT", body={"target": "/api_probe_del.txt", "text": "overwritten by PUT\n"})
print(f"2. PUT 写已存在文件: {st} | {json.dumps(resp, ensure_ascii=False)[:100]}")

# 3. 读回验证
time.sleep(1)
data = mcsm_download(cfg, "/api_probe_del.txt")
print(f"3. 读回: {data.decode() if data else '失败'}")

# 4. DELETE 删这个文件
st, resp = api("/api/files/", {**P}, method="DELETE", body={"targets": ["/api_probe_del.txt"]})
print(f"4. DELETE 删文件: {st} | {json.dumps(resp, ensure_ascii=False)[:100]}")

# 5. 读回确认删除
time.sleep(1)
data = mcsm_download(cfg, "/api_probe_del.txt")
print(f"5. 删后读回: {'✅ 已删除(读不到)' if data is None else '❌ 仍在! ' + str(len(data)) + 'B'}")
