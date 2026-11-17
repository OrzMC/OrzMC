#!/usr/bin/env python3
"""MCSM：探测 plugins/ 下可能残留的文件（读已知路径）"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()
# 探测可能存在的残留（基于历史操作记录）
probe = [
    "/plugins/OrzMC-1.0.13.jar",        # 旧 OrzMC（应已被 update 替换删除）
    "/plugins/OrzMC-1.0.14-dev.237.jar", # 当前 OrzMC
    "/plugins/DeathChest.jar",          # 原版名
    "/plugins/deathchest.jar",          # 修复版名（可能两个并存）
    "/plugins/DeathChest-3.0.1.jar",
    "/plugins/Geyser-Spigot.jar",       # 当前 Geyser
    "/plugins/spark.jar",               # spark 是否装了
    "/plugins/floodgate.jar",           # 23B 占位
    "/plugins/floodgate/key.pem",
    "/plugins/floodgate/config.yml",
]
for p in probe:
    data = mcsm_download(cfg, p)
    print(f"{'✅' if data else '❌'} {p}: {len(data)}B" if data else f"{'❌'} {p}: 不存在")
