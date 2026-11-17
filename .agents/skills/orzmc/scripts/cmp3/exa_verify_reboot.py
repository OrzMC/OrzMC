#!/usr/bin/env python3
"""Exaroton：重启后验证插件版本（日志解析）"""
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

checks = {
    "DeathChest": "DeathChest",
    "OrzMC": "OrzMC v",
    "floodgate 启用": "Enabling floodgate",
    "Geyser": "Geyser-Spigot",
}
for line in text.splitlines():
    ls = line.strip()
    if any(k in ls for k in ["DeathChest", "OrzMC v", "Enabling floodgate", "Geyser-Spigot"]):
        print("  ", ls[:130])
