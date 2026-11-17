#!/usr/bin/env python3
"""Exaroton：查 Geyser 是否独立模式（根目录 Geyser 文件）+ 插件列表"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")

def ls(path):
    url = f"https://api.exaroton.com/v1/servers/{sid}/files/info/{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("User-Agent", "Mozilla/5.0")
    try:
        d = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())["data"]
        return [it["name"] for it in (d.get("children") or [])]
    except Exception as e:
        return [f"ERR {str(e)[:40]}"]

print("根目录:", ls(""))
print()
print("plugins/:", ls("plugins/"))
