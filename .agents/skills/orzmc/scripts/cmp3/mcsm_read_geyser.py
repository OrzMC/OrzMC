#!/usr/bin/env python3
"""MCSM：读取 Geyser config.yml 关键行"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
data = mcsm_download(cfg, "/plugins/Geyser-Spigot/config.yml")
if data:
    text = data.decode("utf-8", errors="replace")
    for line in text.splitlines():
        ls = line.strip()
        if ls.startswith("auth-type") or ls.startswith("floodgate-key-file"):
            print("  ", ls)
    print("  [总行数]", len(text.splitlines()))
else:
    print("读取失败")
