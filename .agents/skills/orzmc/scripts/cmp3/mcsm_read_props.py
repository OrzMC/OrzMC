#!/usr/bin/env python3
"""MCSM：读 server.properties online-mode"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
data = mcsm_download(cfg, "/server.properties")
if data:
    text = data.decode("utf-8", errors="replace")
    for line in text.splitlines():
        if any(k in line for k in ["online-mode", "enforce-secure", "white-list", "enforce-whitelist"]):
            print(" ", line)
else:
    print("读取失败")
