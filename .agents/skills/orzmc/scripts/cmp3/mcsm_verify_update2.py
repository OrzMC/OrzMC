#!/usr/bin/env python3
"""MCSM：验证 update/ 下指定 jar"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
for fname in ["deathchest.jar", "OrzMC-1.0.14-dev.237.jar"]:
    data = mcsm_download(cfg, f"/plugins/update/{fname}")
    if data:
        print(f"✅ update/{fname}: {len(data)} 字节, 魔数: {data[:2]}")
    else:
        print(f"❌ update/{fname}: 读取失败")
