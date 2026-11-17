#!/usr/bin/env python3
"""MCSM 开放 API 全面探测 v2（POST + daemonId + uuid + apikey 正确方式）
只读为主，写操作仅做"路径探测"不实际改动文件
"""
import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config

cfg = get_mcsm_config()
BASE = cfg["url"].rstrip("/")
KEY = cfg["apikey"]
DID = cfg["daemon_id"]
IID = cfg["instance_id"]

def api_call(path, params=None, method="GET", body=None, raw_body=None, content_type=None):
    url = f"{BASE}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method=method)
    req.add_header("Content-Type", content_type or "application/json; charset=utf-8")
    req.add_header("X-Requested-With", "XMLHttpRequest")
    req.add_header("User-Agent", "Mozilla/5.0")
    if body is not None:
        req.data = json.dumps(body).encode()
    elif raw_body is not None:
        req.data = raw_body
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return r.status, r.read().decode()[:400]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:200]
    except Exception as e:
        return -1, str(e)[:150]

P = {"apikey": KEY, "daemonId": DID, "uuid": IID}

print("=== A. 实例/状态 ===")
for path, params, method in [
    ("/api/instance", P, "GET"),
    ("/api/protected_instance/open", P, "GET"),
]:
    st, body = api_call(path, params, method)
    is_json = body.strip().startswith("{")
    print(f"  {method} {path}: {st} | {'JSON' if is_json else 'HTML/OTHER'} | {body[:100]}")

print("\n=== B. 文件操作端点 ===")
# 列目录（技能记载 404 实证——再确认）
st, body = api_call("/api/files/list", {**P, "target": "/plugins", "page": 1, "page_size": 50})
print(f"  GET /api/files/list: {st} | {body[:100]}")
st, body = api_call("/api/files/list", {**P, "target": "/plugins"}, method="POST", body={})
print(f"  POST /api/files/list: {st} | {body[:100]}")

# 读文件（mcsm_download 用 POST 成功——再确认）
st, body = api_call("/api/files/download", {"apikey": KEY, "file_name": "/plugins/Geyser-Spigot/config.yml"})
print(f"  POST /api/files/download: {st} | {body[:120]}")

# 写文件（技能 2026-08-03 成功、2026-08-05 404——关键矛盾点）
st, body = api_call("/api/files/", {**P, "target": "/plugins/test_probe.txt", "text": "probe"}, method="PUT")
print(f"  PUT /api/files/ (新文件): {st} | {body[:100]}")

# 删除（技能记载偶发 200 未删）
st, body = api_call("/api/files/delete", {**P}, method="DELETE", body={"targets": ["/plugins/test_probe.txt"]})
print(f"  DELETE /api/files/delete: {st} | {body[:100]}")

# 移动/重命名
st, body = api_call("/api/files/move", {**P}, method="POST", body={"target": "/plugins/test_probe.txt", "target_new": "/plugins/test_probe2.txt"})
print(f"  POST /api/files/move: {st} | {body[:100]}")

# 新建目录
st, body = api_call("/api/files/mkdir", {**P, "dirname": "/plugins/test_probe_dir"}, method="POST")
print(f"  POST /api/files/mkdir: {st} | {body[:100]}")

print("\n=== C. 其他管理端点 ===")
for path, params, method in [
    ("/api/auth/login", {}, "POST"),
    ("/api/overview", {"apikey": KEY}, "GET"),
    ("/api/service/remote_services_system", {"apikey": KEY}, "GET"),
    ("/api/auth/search", {"apikey": KEY}, "GET"),
]:
    st, body = api_call(path, params, method)
    is_json = body.strip().startswith("{")
    print(f"  {method} {path}: {st} | {'JSON' if is_json else 'HTML/OTHER'} | {body[:80]}")
