#!/usr/bin/env python3
"""MCSM：从前端 JS bundle 提取文件管理 API 调用细节"""
import sys, os, urllib.request, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config

cfg = get_mcsm_config()
BASE = cfg["url"].rstrip("/")

req = urllib.request.Request(BASE + "/assets/index-8f3cee6a.js", headers={"User-Agent": "Mozilla/5.0"})
with urllib.request.urlopen(req, timeout=30) as r:
    js = r.read().decode("utf-8", errors="replace")
print(f"JS bundle: {len(js)}B")

# 找 files 相关 API 路径
print("\n=== /api/files 相关 ===")
for m in set(re.findall(r'["\'`](/api/files/[^"\'`]{0,60})["\'`]', js)):
    print(" ", m)

# 找 list 调用上下文（files 附近 200 字符）
print("\n=== 'files/list' 上下文 ===")
for m in re.finditer(r'.{80}files/list.{120}', js):
    print("  ...", m.group(0)[:250].replace("\n", " "), "...")
    break

# 找 page_size / pageSize
print("\n=== 分页参数 ===")
for m in set(re.findall(r'["\'](page_size|pageSize|page)["\']', js)):
    print(" ", m)

# 找 daemonId/uuid 参数名
print("\n=== 实例参数 ===")
for m in set(re.findall(r'["\'](daemonId|uuid|instanceUuid)["\']', js)):
    print(" ", m)
