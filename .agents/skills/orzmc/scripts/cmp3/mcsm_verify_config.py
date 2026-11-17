#!/usr/bin/env python3
"""MCSM：最终验证 M1-M10 + JVM 内存修改"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()

def read(path):
    data = mcsm_download(cfg, f"/{path}")
    if data is None or data[:2] == b"PK":
        return None
    return data.decode("utf-8", errors="replace")

checks = [
    ("server.properties", "max-tick-time=60000", "M1"),
    ("server.properties", "force-gamemode=true", "M2"),
    ("server.properties", "sync-chunk-writes=true", "M3"),
    ("spigot.yml", "timeout-time: 60", "M4"),
    ("spigot.yml", "view-distance: default", "M5a"),
    ("spigot.yml", "simulation-distance: default", "M5b"),
    ("plugins/Essentials/config.yml", "max-nick-length: 16", "M6"),
    ("plugins/ViaVersion/config.yml", "fix-1_21-placement-rotation: true", "M7"),
    ("plugins/OrzMC/templates.yml", "server_maintenance_hint: \"服务器当前无玩家，可进行服务器维护\"", "M8"),
    ("plugins/DeathChest/config.yml", "auto-update: true", "M9a"),
    ("plugins/DeathChest/config.yml", "update-checker: true", "M9b"),
    ("plugins/LoginSecurity/config.yml", "username-match-exact: true", "M10"),
    ("Start.bat", "-Xms8G -Xmx8G", "JVM"),
]

print("=== MCSM 最终验证 ===")
all_ok = True
for path, needle, tag in checks:
    content = read(path)
    ok = content is not None and needle in content
    if not ok:
        all_ok = False
    print(f"  {'✅' if ok else '❌'} {tag} {path} 含 {needle!r}")
    time.sleep(2)

print(f"\n{'✅ 全部 13 项验证通过' if all_ok else '❌ 有未生效项'}")
