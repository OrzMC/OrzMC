#!/usr/bin/env python3
"""Exaroton：读 server.properties 关键项"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/config/server.properties/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
raw = urllib.request.urlopen(req, timeout=30).read().decode()
d = json.loads(raw)
data = d.get("data", d)
if isinstance(data, list):
    items = {it["key"]: it["value"] for it in data if isinstance(it, dict) and "key" in it}
    for k in ["online-mode", "enforce-secure-profile", "white-list", "enforce-whitelist"]:
        print(f"{k} = {items.get(k, '?')}")
elif isinstance(data, dict):
    for k in ["online-mode", "enforce-secure-profile", "white-list", "enforce-whitelist"]:
        print(f"{k} = {data.get(k, '?')}")
else:
    print("结构:", str(data)[:200])
