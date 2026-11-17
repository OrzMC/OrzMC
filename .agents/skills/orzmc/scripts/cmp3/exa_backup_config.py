#!/usr/bin/env python3
"""Exaroton：备份当前配置到本地（修改前快照）"""
import urllib.request, json, os, time

API_KEY = ""
for line in open(os.path.expanduser("~/.hermes/.env")):
    if line.startswith("EXAROTON_API_KEY="):
        API_KEY = line.split("=", 1)[1].strip()
        break
SID = "{API_TOKEN}"
UA = {"User-Agent": "Mozilla/5.0", "Authorization": f"Bearer {API_KEY}"}
BASE = "https://api.exaroton.com/v1"
OUT = "/tmp/exa_backup_20260803"
os.makedirs(OUT, exist_ok=True)

def api_raw(path):
    req = urllib.request.Request(f"{BASE}{path}", headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")

files = [
    "server.properties",
    "spigot.yml",
    "config/paper-global.yml",
    "config/paper-world-defaults.yml",
    "plugins/Essentials/config.yml",
    "plugins/ViaVersion/config.yml",
    "plugins/GriefPreventionData/config.yml",
    "plugins/EzShops/config.yml",
]
for f in files:
    try:
        content = api_raw(f"/servers/{SID}/files/data/{f}/")
        safe = f.replace("/", "_")
        open(f"{OUT}/{safe}", "w").write(content)
        print(f"✅ {f} ({len(content)}B)")
    except Exception as e:
        print(f"❌ {f}: {str(e)[:60]}")
    time.sleep(3)
print("\n备份完成 →", OUT)
