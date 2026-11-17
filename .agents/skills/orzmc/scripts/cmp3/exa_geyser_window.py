#!/usr/bin/env python3
"""Exaroton：Geyser 启动段完整日志（找回退原因）"""
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
# 打印从 floodgate Loading 到 Geyser Started 之间所有行
start = None
for i, line in enumerate(lines):
    if "floodgate" in line.lower() and "Loading" in line:
        start = i
        break
if start is None:
    print("未找到 floodgate 加载行")
else:
    for line in lines[start:start+90]:
        print("  ", line.strip()[:140])
