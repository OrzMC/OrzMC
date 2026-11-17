#!/usr/bin/env python3
"""字节级对比 MCSM vs Exaroton Geyser config（精确 diff）"""
import sys, os, difflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
mcsm_text = mcsm_download(cfg, "/plugins/Geyser-Spigot/config.yml").decode("utf-8", errors="replace")

key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
import urllib.request, json
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/Geyser-Spigot/config.yml/"
req = urllib.request.Request(url)
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
raw = urllib.request.urlopen(req, timeout=30).read().decode()
try:
    exa_text = json.loads(raw).get("text", raw)
except Exception:
    exa_text = raw

ml = mcsm_text.splitlines()
el = exa_text.splitlines()
print("MCSM 行数:", len(ml), "| Exaroton 行数:", len(el))
for i, (m, e) in enumerate(zip(ml, el), 1):
    if m != e:
        print(f"第{i}行差异:")
        print(f"  MCSM: {m}")
        print(f"  EXA:  {e}")
