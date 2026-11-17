#!/usr/bin/env python3
"""详细三端差异：对 cmp3 报差异的文件，逐 key 输出 本地/Exa/MCSM 三方值"""
import os, sys

LOCAL = os.path.expanduser("~/minecraft-server")
E = "/tmp/exa_configs2"
M = "/tmp/mcsm_configs2"
SKIP_DIRS = {"userdata", "homes", "data", "players", "backups", "logs", "cache", "worlds", "messages"}
SKIP_FILES = {"ops.json", "whitelist.json", "banned-players.json", "banned-ips.json",
              "usercache.json", "permissions.yml", "help.yml"}

def read(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read().splitlines()
    except Exception:
        return None

def key_lines(lines):
    out = []
    for l in lines:
        if l.strip() and not l.strip().startswith("#") and ":" in l:
            key = l.split(":", 1)[0].rstrip()
            val = l.split(":", 1)[1].strip()
            indent = len(l) - len(l.lstrip())
            out.append((indent, key.strip(), val))
    return out

def semantic_map(lines):
    return {f"{ind}|{k}": v for ind, k, v in key_lines(lines)}

def diff_detail(name, lp, ep, mp):
    ll, ee, mm = read(lp), read(ep), read(mp)
    if ll is None:
        return
    dl, de, dm = semantic_map(ll), semantic_map(ee) if ee else {}, semantic_map(mm) if mm else {}
    print(f"\n{'='*70}\n📄 {name}")
    keys = sorted(set(dl) | set(de) | set(dm))
    for k in keys:
        v_l, v_e, v_m = dl.get(k, "∅"), de.get(k, "∅"), dm.get(k, "∅")
        def norm(s):
            try: return ("num", float(s))
            except: return ("str", s)
        if v_l == v_e and v_e == v_m:
            continue
        if norm(v_l) == norm(v_e) == norm(v_m):
            continue
        # 只显示至少一端缺失或不同的
        print(f"  {k.replace(chr(124),'@')}")
        print(f"    本地 : {v_l}")
        print(f"    Exa  : {v_e}")
        print(f"    MCSM : {v_m}")

# 核心
core_files = [
    ("server.properties", "server.properties", "server.properties", "server.properties"),
    ("bukkit.yml", "bukkit.yml", "bukkit.yml", "bukkit.yml"),
    ("spigot.yml", "spigot.yml", "spigot.yml", "spigot.yml"),
    ("commands.yml", "commands.yml", "commands.yml", "commands.yml"),
    ("config/paper-global.yml", "config/paper-global.yml", "config_paper-global.yml", "config_paper-global.yml"),
    ("config/paper-world-defaults.yml", "config/paper-world-defaults.yml", "config_paper-world-defaults.yml", "config_paper-world-defaults.yml"),
    ("wepif.yml", "wepif.yml", "wepif.yml", "wepif.yml"),
]
print("【核心配置差异明细】")
for name, lf, ef, mf in core_files:
    diff_detail(name, f"{LOCAL}/{lf}", f"{E}/{ef}", f"{M}/{mf}")

# 插件：以本地为基准
print("\n【插件配置差异明细】")
for pdir in sorted(os.listdir(f"{LOCAL}/plugins")):
    pdir_path = f"{LOCAL}/plugins/{pdir}"
    if not os.path.isdir(pdir_path):
        continue
    for root, dirs, files in os.walk(pdir_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in sorted(files):
            if not fn.endswith((".yml", ".yaml")) or fn in SKIP_FILES:
                continue
            rel = os.path.relpath(os.path.join(root, fn), pdir_path)
            name = f"{pdir}/{rel}"
            # 粗筛：先快速比较，只在有差异时输出
            lp = f"{pdir_path}/{rel}"
            ep = f"{E}/plugins/{pdir}/{rel}"
            mp = f"{M}/plugins/{pdir}/{rel}"
            diff_detail(name, lp, ep, mp)
