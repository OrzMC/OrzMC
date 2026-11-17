#!/usr/bin/env python3
"""MCSM：M1-M10 配置修改 + JVM 内存调整（2026-08-03 执行）
方法：读原文件 → 精确替换 → PUT 写回（保留 CRLF）
"""
import sys, os, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_config, mcsm_download

cfg = get_mcsm_config()

def mcsm_read(path):
    data = mcsm_download(cfg, f"/{path}")
    if data is None or data[:2] == b"PK":
        return None
    return data.decode("utf-8", errors="replace")

def mcsm_write(path, content):
    """PUT /api/files/ body {"target": path, "text": content}
    ⚠️ 只能写已存在的文件（新文件路径返回 Illegal access path）"""
    import urllib.request, urllib.parse
    params = {"apikey": cfg["apikey"], "daemonId": cfg["daemon_id"], "uuid": cfg["instance_id"]}
    url = cfg["url"] + "api/files/?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, method="PUT",
        data=json.dumps({"target": f"/{path}", "text": content}).encode(),
        headers={"Content-Type": "application/json; charset=utf-8",
                 "X-Requested-With": "XMLHttpRequest"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = r.read().decode()
            d = json.loads(resp)
            return d.get("status") == 200
    except Exception as e:
        print(f"  ❌ 写入异常: {e}")
        return False

def apply_file(path, replacements, desc):
    """replacements: [(old, new, tag), ...]"""
    content = mcsm_read(path)
    if content is None:
        print(f"❌ {path}: 读取失败")
        return
    print(f"\n📄 {path}")
    for old, new, tag in replacements:
        if old not in content:
            print(f"  ⚠️ {tag}: 未找到 {old!r}")
            continue
        content = content.replace(old, new, 1)
        print(f"  ✅ {tag}: {old!r} → {new!r}")
    if mcsm_write(path, content):
        print(f"  ✅ {path} 写入成功")
    else:
        print(f"  ❌ {path} 写入失败")
    time.sleep(3)

# M1-M3 server.properties（CRLF）
apply_file("server.properties", [
    ("max-tick-time=600000", "max-tick-time=60000", "M1 max-tick-time"),
    ("force-gamemode=false", "force-gamemode=true", "M2 force-gamemode"),
    ("sync-chunk-writes=false", "sync-chunk-writes=true", "M3 sync-chunk-writes"),
], "M1-M3")

# M4-M5 spigot.yml
apply_file("spigot.yml", [
    ("timeout-time: 180", "timeout-time: 60", "M4 timeout-time"),
    ("view-distance: '6'", "view-distance: default", "M5 view-distance"),
    ("simulation-distance: '4'", "simulation-distance: default", "M5 simulation-distance"),
], "M4-M5")

# M6 Essentials
apply_file("plugins/Essentials/config.yml", [
    ("max-nick-length: 15", "max-nick-length: 16", "M6 max-nick-length"),
], "M6")

# M7 ViaVersion
apply_file("plugins/ViaVersion/config.yml", [
    ("fix-1_21-placement-rotation: false", "fix-1_21-placement-rotation: true", "M7 ViaVersion fix"),
], "M7")

# M8 OrzMC templates（只改 server_maintenance_hint，保留 notifications 段）
apply_file("plugins/OrzMC/templates.yml", [
    ('server_maintenance_hint: "{motd}"', 'server_maintenance_hint: "服务器当前无玩家，可进行服务器维护"', "M8 maintenance_hint"),
], "M8")

# M9 DeathChest
apply_file("plugins/DeathChest/config.yml", [
    ("auto-update: false", "auto-update: true", "M9a auto-update"),
    ("update-checker: false", "update-checker: true", "M9b update-checker"),
], "M9")

# M10 LoginSecurity
apply_file("plugins/LoginSecurity/config.yml", [
    ("username-match-exact: false", "username-match-exact: true", "M10 username-match-exact"),
], "M10")

print("\n=== 全部配置修改完成 ===")
