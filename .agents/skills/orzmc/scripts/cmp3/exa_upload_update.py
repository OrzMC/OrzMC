#!/usr/bin/env python3
"""Exaroton：上传插件到 plugins/update/（离线时可直接写）
用法: python3 exa_upload_update.py <jar路径> [远端文件名]
"""
import urllib.request, urllib.error, json, os, sys, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
if not key or not sid:
    print("❌ 缺少 EXAROTON_API_KEY / EXAROTON_SERVER_ID")
    sys.exit(1)

jar_path = os.path.expanduser(sys.argv[1] if len(sys.argv) > 1 else "~/death-chest/build/libs/deathchest.jar")
fname = sys.argv[2] if len(sys.argv) > 2 else os.path.basename(jar_path)

jar = open(jar_path, "rb").read()
print(f"上传 {fname} ({len(jar)//1024}KB, sha256={hashlib.sha256(jar).hexdigest()[:12]}) -> plugins/update/")

url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/update/{fname}/"
req = urllib.request.Request(url, data=jar, method="PUT")
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
req.add_header("Content-Type", "application/java-archive")
try:
    with urllib.request.urlopen(req, timeout=300) as r:
        print("✅ Exaroton 上传响应:", r.status, r.read().decode()[:120])
except urllib.error.HTTPError as e:
    print("❌ HTTP", e.code, e.read().decode()[:200])
