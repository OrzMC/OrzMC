#!/usr/bin/env python3
"""Exaroton：列出 Geyser 目录（找缓存文件）"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/info/plugins/Geyser-Spigot/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
d = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())["data"]
for it in (d.get("children") or []):
    print(" ", it["name"], "|", it.get("size", "?"))
