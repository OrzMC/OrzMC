#!/usr/bin/env python3
"""Exaroton：最终验证所有修改（GET 读回 + 断言）"""
import urllib.request, json, os, time

API_KEY = ""
for line in open(os.path.expanduser("~/.hermes/.env")):
    if line.startswith("EXAROTON_API_KEY="):
        API_KEY = line.split("=", 1)[1].strip()
        break
SID = "{API_TOKEN}"
UA = {"User-Agent": "Mozilla/5.0", "Authorization": f"Bearer {API_KEY}"}
BASE = "https://api.exaroton.com/v1"

def get_file(path):
    req = urllib.request.Request(f"{BASE}/servers/{SID}/files/data/{path}/", headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        raw = r.read().decode("utf-8", errors="replace")
    try:
        d = json.loads(raw)
        if isinstance(d, dict) and "text" in d:
            return d["text"]
    except Exception:
        pass
    return raw

checks = [
    ("server.properties", "max-tick-time=60000", "E1"),
    ("server.properties", "sync-chunk-writes=true", "E2"),
    ("spigot.yml", "timeout-time: 60", "E3"),
    ("config/paper-world-defaults.yml", "enabled: true", "E4a"),
    ("config/paper-world-defaults.yml", "engine-mode: 2", "E4b"),
    ("config/paper-world-defaults.yml", "hard: default", "E5"),
    ("config/paper-global.yml", "save-empty-scoreboard-teams: true", "E6"),
    ("plugins/Essentials/config.yml", "max-nick-length: 16", "E7"),
    ("plugins/ViaVersion/config.yml", "fix-1_21-placement-rotation: true", "E8"),
    ("plugins/GriefPreventionData/config.yml", "Enabled: true", "E9a"),
    ("plugins/GriefPreventionData/config.yml", "PistonMovement: CLAIMS_ONLY", "E9b"),
    ("plugins/EzShops/config.yml", "min-price: 1.0", "E10"),
]
print("=== Exaroton 最终验证 ===")
all_ok = True
for path, needle, tag in checks:
    content = get_file(path)
    ok = needle in content
    if not ok:
        all_ok = False
    print(f"  {'✅' if ok else '❌'} {tag} {path} 含 {needle!r}")
    time.sleep(3)
print(f"\n{'✅ 全部 12 项验证通过' if all_ok else '❌ 有未生效项'}")
