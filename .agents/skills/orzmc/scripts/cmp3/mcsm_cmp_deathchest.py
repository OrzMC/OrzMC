#!/usr/bin/env python3
"""MCSM：对比 DeathChest.jar 与 deathchest.jar 的 sha256"""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
a = mcsm_download(cfg, "/plugins/DeathChest.jar")
b = mcsm_download(cfg, "/plugins/deathchest.jar")
if a and b:
    ha = hashlib.sha256(a).hexdigest()
    hb = hashlib.sha256(b).hexdigest()
    print(f"DeathChest.jar:  {len(a)}B sha256={ha[:16]}")
    print(f"deathchest.jar:  {len(b)}B sha256={hb[:16]}")
    print("相同:", ha == hb)
elif a:
    print(f"DeathChest.jar 存在 {len(a)}B, deathchest.jar 读取失败")
else:
    print("DeathChest.jar 读取失败")
