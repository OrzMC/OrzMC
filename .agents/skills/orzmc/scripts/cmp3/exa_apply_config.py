#!/usr/bin/env python3
"""Exaroton：用 PUT files/data 覆盖写全部配置（E3-E10 + E1/E2 已成功）
策略：GET 当前文件 → 文本替换 → PUT 覆盖（**裸文本 body，禁 JSON 包装**，2026-08-10 修复）
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from exa_file import get_file, put_file


def apply(path, old, new, desc):
    content = get_file(path)
    if old not in content:
        print(f"  ⚠️ {path}: 未找到 {old!r} (跳过)")
        return False
    new_content = content.replace(old, new, 1)
    code, resp = put_file(path, new_content)
    print(f"  📤 {path}: PUT {code} {resp[:60]}")
    # 复验
    back = get_file(path)
    ok = (back == new_content)
    print(f"  {'✅' if ok else '❌'} {desc} (复验{'一致' if ok else '不一致'})")
    time.sleep(3)
    return ok

# E3 timeout-time 180 → 60
apply("spigot.yml", "timeout-time: 180", "timeout-time: 60", "E3 timeout-time")
# E4 anti-xray enabled false→true + engine-mode 1→2
apply("config/paper-world-defaults.yml", "enabled: false\n    engine-mode: 1", "enabled: true\n    engine-mode: 2", "E4 anti-xray")
# E5 spawn-limits 128/32 → default
apply("config/paper-world-defaults.yml", "hard: 128\n        soft: 32", "hard: default\n        soft: default", "E5 spawn-limits")
# E6 save-empty-scoreboard-teams false → true
apply("config/paper-global.yml", "save-empty-scoreboard-teams: false", "save-empty-scoreboard-teams: true", "E6 scoreboard-teams")
# E7 Essentials max-nick-length 15 → 16
apply("plugins/Essentials/config.yml", "max-nick-length: 15", "max-nick-length: 16", "E7 max-nick-length")
# E8 ViaVersion fix-1_21 false → true
apply("plugins/ViaVersion/config.yml", "fix-1_21-placement-rotation: false", "fix-1_21-placement-rotation: true", "E8 ViaVersion fix")
# E9 GP Enabled false→true + PistonMovement
apply("plugins/GriefPreventionData/config.yml", "Enabled: false", "Enabled: true", "E9a GP Enabled")
apply("plugins/GriefPreventionData/config.yml", "PistonMovement: EVERYWHERE", "PistonMovement: CLAIMS_ONLY", "E9b GP Piston")
# E10 EzShops min-price 0.0 → 1.0
apply("plugins/EzShops/config.yml", "min-price: 0.0", "min-price: 1.0", "E10 EzShops min-price")

print("\n✅ 全部处理完成")
