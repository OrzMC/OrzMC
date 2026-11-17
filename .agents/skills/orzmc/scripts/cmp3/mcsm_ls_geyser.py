#!/usr/bin/env python3
"""MCSM：列出 Geyser-Spigot 目录 + floodgate 目录"""
import sys, os, urllib.request, urllib.parse, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config

cfg = get_mcsm_config()
# 用 mcsm_download 无法列目录，用 mcsm.sh logs 查 Geyser 加载目录信息
# 改用已知信息：MCSM 的 Geyser 目录文件（从之前 verify 知道 config.yml 存在）
import hashlib
for path in ["/plugins/Geyser-Spigot/config.yml", "/plugins/floodgate/key.pem", "/plugins/floodgate/config.yml"]:
    from mcsm_env import mcsm_download
    data = mcsm_download(cfg, path)
    if data:
        print(f"  {path}: {len(data)}B")
    else:
        print(f"  {path}: ❌")
