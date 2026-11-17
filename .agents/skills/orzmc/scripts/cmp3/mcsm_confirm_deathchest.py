#!/usr/bin/env python3
"""MCSM：精确确认 DeathChest.jar 与 deathchest.jar 是否存在（区分大小写）"""
import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()

# 用原始字节读取，对比两个路径
for path in ["/plugins/DeathChest.jar", "/plugins/deathchest.jar", "/plugins/DEATHCHEST.JAR"]:
    data = mcsm_download(cfg, path)
    if data:
        print(f"✅ {path}: {len(data)}B sha256={hashlib.sha256(data).hexdigest()[:12]}")
    else:
        print(f"❌ {path}: 读取失败/不存在")
