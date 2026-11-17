#!/usr/bin/env python3
"""Exa 配置对齐修改（2026-08-11 用户决策：第一类零风险 + 第三类#1#3#4）
修改项：
  1. config/paper-world-defaults.yml: max-leash-distance: 10.0 → default
  2. server.properties: sync-chunk-writes=false → true（第三类#1 选A统一true）
  3. server.properties: resource-pack-prompt="" → 空（第一类#7 形态统一）
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from exa_file import get_file, put_file

CHANGES = [
    ("config/paper-world-defaults.yml", "max-leash-distance: 10.0", "max-leash-distance: default"),
    ("server.properties", "sync-chunk-writes=false", "sync-chunk-writes=true"),
    ("server.properties", 'resource-pack-prompt=""', "resource-pack-prompt="),
]

for path, old, new in CHANGES:
    txt = get_file(path)
    if old not in txt:
        print(f"  ⚠️ {path}: 未找到 `{old}`（跳过，可能已改）")
        continue
    txt2 = txt.replace(old, new, 1)
    put_file(path, txt2)
    # 回读验证
    back = get_file(path)
    ok = new in back
    print(f"  {'✅' if ok else '❌'} {path}: {old} → {new}（回读验证{'通过' if ok else '失败'}）")
