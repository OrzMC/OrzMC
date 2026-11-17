#!/usr/bin/env python3
"""MCSM：探测各目录文件大小（files/list 不稳定时的替代方案）
用 download 凭证 API + 真实 GET 逐个探测文件存在性
"""
import sys, os, json, urllib.request, urllib.parse, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()

# 探测候选大文件/目录（世界备份、jar、日志等）
candidates = [
    "/backups", "/plugins", "/world", "/world_nether", "/world_the_end",
    "/paper-26.2-92.jar", "/logs", "/crash-reports", "/libraries",
    "/plugins/update", "/cache", "/dumps", "/versions",
]

for path in candidates:
    data = mcsm_download(cfg, path)
    if data is None:
        print(f"❌ {path}: 读取失败")
        continue
    head = data[:16]
    if head[:2] == b"PK":
        print(f"📦 {path}: {len(data)/1024/1024:.1f}MB (jar/zip)")
    elif len(data) > 100:
        # 文本内容 = 文件
        print(f"📄 {path}: {len(data)}B (文本)")
    else:
        print(f"ℹ️  {path}: {len(data)}B")
    time.sleep(2)
