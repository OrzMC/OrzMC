#!/usr/bin/env python3
"""对比 MCSM vs Exaroton 的 Geyser config.yml（找 floodgate 相关差异）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
mcsm_data = mcsm_download(cfg, "/plugins/Geyser-Spigot/config.yml")
mcsm_text = mcsm_data.decode("utf-8", errors="replace") if mcsm_data else ""
mcsm_lines = set(mcsm_text.splitlines())

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
import urllib.request, json
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/Geyser-Spigot/config.yml/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
raw = urllib.request.urlopen(req, timeout=30).read().decode()
try:
    d = json.loads(raw)
    exa_text = d.get("text", raw)
except Exception:
    exa_text = raw
exa_lines = set(exa_text.splitlines())

print("=== MCSM 有 Exaroton 无 ===")
for l in sorted(mcsm_lines - exa_lines):
    print("  M:", l)
print("=== Exaroton 有 MCSM 无 ===")
for l in sorted(exa_lines - mcsm_lines):
    print("  E:", l)
