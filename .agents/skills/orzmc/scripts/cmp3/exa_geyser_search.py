#!/usr/bin/env python3
"""Exaroton：全日志搜 Geyser floodgate/key/warn 相关"""
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
for line in text.splitlines():
    ls = line.lower()
    if ("geyser" in ls or "floodgate" in ls) and any(w in ls for w in ["key", "auth", "warn", "error", "fail", "unable", "cannot"]):
        print("  ", line.strip()[:150])
print("--- 搜索完成 ---")
