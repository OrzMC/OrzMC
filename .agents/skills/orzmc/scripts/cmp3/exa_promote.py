#!/usr/bin/env python3
"""Exaroton：批量插件推广（删旧 OrzMC + 传新 jar 到 update/plugins/）
用法: python3 exa_promote.py
"""
import urllib.request, urllib.error, json, os, sys, hashlib, time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
if not key or not sid:
    print("❌ 缺少 EXAROTON_API_KEY / EXAROTON_SERVER_ID")
    sys.exit(1)

BASE = f"https://api.exaroton.com/v1/servers/{sid}/files/data"
HEADERS = {"Authorization": "Bearer " + key, "User-Agent": "Mozilla/5.0"}

def put(path, data, ctype="application/octet-stream"):
    req = urllib.request.Request(f"{BASE}{path}", data=data, method="PUT")
    for k, v in HEADERS.items():
        req.add_header(k, v)
    req.add_header("Content-Type", ctype)
    try:
        with urllib.request.urlopen(req, timeout=300) as r:
            return r.status, r.read().decode()[:80]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:150]

def delete(path):
    req = urllib.request.Request(f"{BASE}{path}", method="DELETE")
    for k, v in HEADERS.items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode()[:80]
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()[:150]

PLUGINS = os.path.expanduser("/Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/716c2fb712154c36ba5ab0f1480d3f87/plugins")

# 1. 删旧 OrzMC 1.0.13（防新旧并存冲突）
print("① 删除旧 OrzMC-1.0.13-pr.153.394.jar")
st, msg = delete("/plugins/OrzMC-1.0.13-pr.153.394.jar/")
print(f"   {st}: {msg}")

# 2. 传 OrzMC 1.0.14-dev.237 到 update/
for fname in ["OrzMC-1.0.14-dev.237.jar"]:
    jar = open(os.path.join(PLUGINS, fname), "rb").read()
    print(f"② 上传 {fname} ({len(jar)//1024}KB, sha256={hashlib.sha256(jar).hexdigest()[:12]}) -> update/")
    st, msg = put(f"/plugins/update/{fname}/", jar, "application/java-archive")
    print(f"   {st}: {msg}")
    time.sleep(3)

# 3. 传 floodgate 到 plugins/（新装直接放 plugins/）
fname = "floodgate.jar"
jar = open(os.path.join(PLUGINS, fname), "rb").read()
print(f"③ 上传 {fname} ({len(jar)//1024}KB, sha256={hashlib.sha256(jar).hexdigest()[:12]}) -> plugins/")
st, msg = put(f"/plugins/{fname}/", jar, "application/java-archive")
print(f"   {st}: {msg}")
