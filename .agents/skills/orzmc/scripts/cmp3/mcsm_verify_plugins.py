#!/usr/bin/env python3
"""MCSM：验证 plugins/ 下新装 jar（floodgate）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
for fname in ["floodgate.jar"]:
    data = mcsm_download(cfg, f"/plugins/{fname}")
    if data:
        print(f"✅ MCSM plugins/{fname}: {len(data)} 字节, 魔数: {data[:2]}")
    else:
        print(f"❌ MCSM plugins/{fname}: 读取失败")
