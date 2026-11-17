#!/usr/bin/env python3
"""MCSM：读 floodgate key.pem 大小+内容"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
data = mcsm_download(cfg, "/plugins/floodgate/key.pem")
if data:
    print(f"MCSM key.pem: {len(data)} 字节, hex: {data.hex()[:32]}")
else:
    print("读取失败")
