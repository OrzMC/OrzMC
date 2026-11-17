#!/usr/bin/env python3
"""Exaroton：删除 floodgate key.pem（重启后重新生成）"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/floodgate/key.pem/"
req = urllib.request.Request(url, method="DELETE")
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("删除:", r.status, r.read().decode()[:80])
except urllib.error.HTTPError as e:
    print("❌ HTTP", e.code, e.read().decode()[:100])
