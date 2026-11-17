#!/usr/bin/env python3
"""Exaroton：重启后验证 update/ 清空 + plugins/ jar 状态"""
import urllib.request, json, os

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")

def ls(path):
    url = f"https://api.exaroton.com/v1/servers/{sid}/files/info/{path}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("User-Agent", "Mozilla/5.0")
    d = json.loads(urllib.request.urlopen(req, timeout=30).read().decode())["data"]
    return [(it["name"], it.get("size", "?")) for it in (d.get("children") or [])]

print("update/ 内容（应为空）:", ls("plugins/update/"))
print("plugins/ OrzMC:", [x for x in ls("plugins/") if "OrzMC" in x[0]])
print("plugins/ deathchest:", [x for x in ls("plugins/") if "deathchest" in x[0] or "DeathChest" in x[0]])
print("plugins/ floodgate:", [x for x in ls("plugins/") if "floodgate" in x[0]])
