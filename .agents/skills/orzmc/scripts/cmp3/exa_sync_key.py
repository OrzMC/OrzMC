#!/usr/bin/env python3
"""Exaroton：上传 MCSM 的 key.pem 覆盖（测试 key 是否有效）"""
import urllib.request, json, os, sys, hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

# 1. 下载 MCSM 的 key.pem
cfg = get_mcsm_config()
mcsm_key = mcsm_download(cfg, "/plugins/floodgate/key.pem")
if not mcsm_key:
    print("❌ MCSM key 下载失败")
    sys.exit(1)
print("MCSM key:", len(mcsm_key), "B, hex:", mcsm_key.hex()[:16])

# 2. 上传到 Exaroton
key = os.environ.get("EXAROTON_API_KEY", "")
sid = os.environ.get("EXAROTON_SERVER_ID", "")
url = f"https://api.exaroton.com/v1/servers/{sid}/files/data/plugins/floodgate/key.pem/"
req = urllib.request.Request(url, data=mcsm_key, method="PUT")
req.add_header("Authorization", "Bearer " + key)
req.add_header("User-Agent", "Mozilla/5.0")
req.add_header("Content-Type", "application/octet-stream")
try:
    with urllib.request.urlopen(req, timeout=60) as r:
        print("上传:", r.status, r.read().decode()[:60])
except urllib.error.HTTPError as e:
    print("❌ HTTP", e.code, e.read().decode()[:100])
