#!/usr/bin/env python3
"""Exaroton：Geyser 启动段完整日志"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/logs/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
raw = urllib.request.urlopen(req, timeout=30).read().decode()
d = json.loads(raw)
data = d.get("data")
if isinstance(data, dict):
    data = json.dumps(data, ensure_ascii=False)
text = data.replace("\\n", "\n")
lines = text.splitlines()
# 找 Geyser-Spigot 启用到 Started Geyser 的段
capture = False
for i, line in enumerate(lines):
    if "Enabling Geyser" in line or "[Geyser-Spigot]" in line:
        capture = True
    if capture:
        print("  ", line.strip()[:140])
        if "Started Geyser" in line or "update available" in line:
            capture = False
