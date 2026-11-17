#!/usr/bin/env python3
"""MCSM：验证 update/Geyser-Spigot.jar 就位"""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
data = mcsm_download(cfg, "/plugins/update/Geyser-Spigot.jar")
if data:
    print(f"update/Geyser-Spigot.jar: {len(data)}B sha256={hashlib.sha256(data).hexdigest()[:12]}")
else:
    print("update/Geyser-Spigot.jar: 不存在")
