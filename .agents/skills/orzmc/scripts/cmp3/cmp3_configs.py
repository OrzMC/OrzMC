#!/usr/bin/env python3
"""两端配置全量对比 v4（2026-09-09 迁移后：本地端退役）
基准端 = MCSM({SERVER_NAME}, Windows 栈) 拉取目录；对比端 = Exaroton 拉取目录。
用法: python3 cmp3_configs.py [基准_dir] [对比_dir]
  例: python3 cmp3_configs.py /tmp/mcsm_configs2 /tmp/exa_configs2
判定口径: 交集语义——两端共同 key 值同 = 一致；值异 = 差异；单端独有 key 另计。
排除: 数据文件（userdata/homes/players 等）
"""
import os, sys

BASE = sys.argv[1] if len(sys.argv) > 1 else "/tmp/mcsm_configs2"
CMP = sys.argv[2] if len(sys.argv) > 2 else "/tmp/exa_configs2"
SKIP_DIRS = {"userdata", "homes", "data", "players", "backups", "logs", "cache", "worlds", "messages"}
SKIP_FILES = {"ops.json", "whitelist.json", "banned-players.json", "banned-ips.json",
              "usercache.json", "permissions.yml", "help.yml"}
EQ_STYLE = {"server.properties"}

def read(p):
    try:
        return open(p, encoding="utf-8", errors="replace").read().splitlines()
    except Exception:
        return None

def key_lines(lines, eq_style=False):
    out = []
    for l in lines:
        if l.strip() and not l.strip().startswith("#"):
            if eq_style:
                if "=" in l:
                    key = l.split("=", 1)[0].rstrip()
                    val = l.split("=", 1)[1].strip()
                    out.append((0, key.strip(), val))
            elif ":" in l:
                key = l.split(":", 1)[0].rstrip()
                val = l.split(":", 1)[1].strip()
                indent = len(l) - len(l.lstrip())
                out.append((indent, key.strip(), val))
    return out

def semantic_map(lines, eq_style=False):
    return {f"{ind}|{k}": v for ind, k, v in key_lines(lines, eq_style)}

def norm(s):
    try:
        return ("num", float(s))
    except Exception:
        return ("str", s)

def diff_pair(base_lines, cmp_lines, eq_style=False):
    """两端语义对比 → (交集差异列表, 单端独有 key 数)"""
    db = semantic_map(base_lines, eq_style)
    dc = semantic_map(cmp_lines, eq_style) if cmp_lines else {}
    diffs = []
    for k in sorted(set(db) & set(dc)):
        vb, vc = db[k], dc[k]
        if vb == vc or norm(vb) == norm(vc):
            continue
        diffs.append((k, vb, vc))
    allk = set(db) | set(dc)
    side = sum(1 for k in allk if (k in db) != (k in dc))
    return diffs, side

print("=" * 75)
print(f"两端配置对比: 基准(MCSM {SERVER_NAME}) {BASE} / 对比(Exaroton) {CMP}")
print("=" * 75)

# 核心配置（平铺：基准目录文件名 == 对比目录文件名）
print("\n【核心配置】")
core_files = ["server.properties", "bukkit.yml", "spigot.yml", "commands.yml",
              "config_paper-global.yml", "config_paper-world-defaults.yml", "wepif.yml"]
core_diff_n = 0
for name in core_files:
    bl = read(f"{BASE}/{name}")
    if bl is None:
        print(f"  ℹ️  {name}: 基准端缺失")
        continue
    cl = read(f"{CMP}/{name}")
    diffs, side = diff_pair(bl, cl, eq_style=(name in EQ_STYLE))
    if not diffs and cl is not None:
        print(f"  ✅ {name}")
    elif cl is None:
        print(f"  ❌ {name}: 对比端(Exa)缺失"); core_diff_n += 1
    else:
        core_diff_n += 1
        side_note = f"，另单端独有 key {side} 个" if side else ""
        print(f"  ❌ {name}: 差异 {len(diffs)} 处{side_note}")
        for k, vb, vc in diffs[:6]:
            print(f"      {k.replace('|', '@')}: 基准={vb} Exa={vc}")

# 插件配置（遍历基准端 plugins 树）
print("\n【插件配置】")
def walk_plugin_configs(base_plugins):
    out = []
    if not os.path.isdir(base_plugins):
        return out
    for pdir in sorted(os.listdir(base_plugins)):
        pdir_path = os.path.join(base_plugins, pdir)
        if not os.path.isdir(pdir_path):
            continue
        for root, dirs, files in os.walk(pdir_path):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in sorted(files):
                if fn.endswith((".yml", ".yaml")) and fn not in SKIP_FILES:
                    rel = os.path.relpath(os.path.join(root, fn), base_plugins)
                    out.append((pdir, rel))
    return out

total = 0
diff_files = []
for pdir, rel in walk_plugin_configs(f"{BASE}/plugins"):
    total += 1
    b_path = f"{BASE}/plugins/{rel}"   # rel 已含 pdir（相对 base_plugins），勿再拼 pdir
    c_path = f"{CMP}/plugins/{rel}"
    bl = read(b_path)
    cl = read(c_path)
    name = f"{pdir}/{rel}"
    if bl is None:
        print(f"  ℹ️  {name}: 基准缺失"); continue
    if cl is None:
        diff_files.append((name, "对比端缺失", 0))
        continue
    diffs, side = diff_pair(bl, cl)
    if diffs:
        diff_files.append((name, f"{len(diffs)} 处差异", side))
print(f"  共检查 {total} 个插件配置文件，其中差异 {len(diff_files)} 个：")
for name, info, side in diff_files:
    side_note = f"，单端独有 key {side} 个" if side else ""
    print(f"    ❌ {name}: {info}{side_note}")

print(f"\n总计：核心 7 + 插件 {total} = {7 + total} 个配置文件（基准端实际存在为准）")
