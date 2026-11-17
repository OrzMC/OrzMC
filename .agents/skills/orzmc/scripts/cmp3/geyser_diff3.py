#!/usr/bin/env python3
"""字节级精确对比（含 BOM/换行）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
mcsm_raw = mcsm_download(cfg, "/plugins/Geyser-Spigot/config.yml")

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
import urllib.request, json
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/Geyser-Spigot/config.yml/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
raw = urllib.request.urlopen(req, timeout=30).read()
try:
    d = json.loads(raw)
    exa_raw = d.get("text", raw).encode()
except Exception:
    exa_raw = raw

print("MCSM raw:", len(mcsm_raw), "B | Exaroton raw:", len(exa_raw), "B")
print("MCSM 前4字节:", mcsm_raw[:4], "| Exaroton 前4字节:", exa_raw[:4])
print("MCSM 尾4字节:", mcsm_raw[-4:], "| Exaroton 尾4字节:", exa_raw[-4:])
print("MCSM BOM:", mcsm_raw[:3] == b"\xef\xbb\xbf", "| Exaroton BOM:", exa_raw[:3] == b"\xef\xbb\xbf")
