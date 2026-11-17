#!/usr/bin/env python3
"""Exaroton：直接读 server.properties 原文（files/data，非 files/config）"""
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
for line in text.splitlines():
    ls = line.strip()
    if ls and not ls.startswith("#") and any(k in ls for k in ["online-mode", "enforce-secure", "white-list"]):
        print(" ", ls)
print("[总行数]", len(text.splitlines()))
