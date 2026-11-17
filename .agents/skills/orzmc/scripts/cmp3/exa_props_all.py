#!/usr/bin/env python3
"""Exaroton：server.properties 全文 online-mode 所有出现位置"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/server.properties/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
raw = urllib.request.urlopen(req, timeout=30).read().decode()
try:
    d = json.loads(raw)
    text = d.get("text", raw)
except Exception:
    text = raw
lines = text.splitlines()
print("总行数:", len(lines))
for i, line in enumerate(lines, 1):
    if "online-mode" in line or "enforce-secure" in line:
        print(f"  第{i}行: {line.strip()}")
