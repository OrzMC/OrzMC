#!/usr/bin/env python3
"""两端配置差异完整报告生成器 v3（2026-09-09 迁移后：本地端退役）
基准端 = MCSM({SERVER_NAME}, Windows 栈) /tmp/mcsm_configs2；对比端 = Exaroton /tmp/exa_configs2
判定口径：交集语义（两端共同 key 值同 = 一致；值异 = 差异；单端独有 key 另计）
数据类文件（玩家数据/交易记录/时间戳）标注为"运行时数据"。
"""
import os, sys

BASE = "/tmp/mcsm_configs2"   # 基准端 = MCSM {SERVER_NAME}（Windows 运行栈；原"本地测试服"迁移后角色）
E = "/tmp/exa_configs2"       # Exaroton（海外服）
SKIP_DIRS = {"userdata", "homes", "data", "players", "backups", "logs", "cache", "worlds", "messages"}
SKIP_FILES = {"ops.json", "whitelist.json", "banned-players.json", "banned-ips.json",
              "usercache.json", "permissions.yml", "help.yml"}
EQ_STYLE = {"server.properties"}

# 数据类文件（内容随玩家/运行变化，非配置）
DATA_FILES = {
    "BackOnDeath/config.yml", "GetMeHome/homes.yml", "EzShops/transactions.yml",
    "EzShops/player-shops.yml", "EzShops/shop-rotations.yml", "OrzMC/permission.yml",
    "OrzMC/ip_blacklist.yml", "Essentials/upgrades-done.yml",
}

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
                    k, v = l.split("=", 1)[0].rstrip(), l.split("=", 1)[1].strip()
                    out.append((0, k.strip(), v))
            elif ":" in l:
                k, v = l.split(":", 1)[0].rstrip(), l.split(":", 1)[1].strip()
                out.append((len(l) - len(l.lstrip()), k.strip(), v))
    return out

def semantic_map(lines, eq_style=False):
    return {f"{ind}|{k}": v for ind, k, v in key_lines(lines, eq_style)}

def norm(s):
    try:
        return ("num", float(s))
    except Exception:
        return ("str", s)

def diff_file(base_path, cmp_path, eq_style=False):
    """返回 (status, 交集差异列表, 单端独有 key 统计)
    status: 'same' | 'diff' | 'base_missing' | 'cmp_missing'"""
    bl = read(base_path)
    if bl is None:
        return 'base_missing', [], {}
    db = semantic_map(bl, eq_style)
    cl = read(cmp_path)
    if cl is None:
        return 'cmp_missing', [], {}
    dc = semantic_map(cl, eq_style)
    diffs = []
    for k in sorted(set(db) & set(dc)):
        vb, vc = db[k], dc[k]
        if vb == vc or norm(vb) == norm(vc):
            continue
        diffs.append((k, vb, vc))
    allk = set(db) | set(dc)
    side = {k: 1 for k in allk if (k in db) != (k in dc)}
    return ('same' if not diffs else 'diff', diffs, side)

def label(k):
    return k.replace('|', '@').replace(' ', '')

out = []
out.append("# 两端配置差异审计报告（2026-09-09 v3·迁移后两端模型）\n")
out.append("> 巡检端：**MCSM**（{SERVER_NAME}.cn Windows 运行栈，原本地测试服迁移后） + **Exaroton**（海外服）。\n")
core_scan = [f for f in os.listdir(BASE) if os.path.isfile(f"{BASE}/{f}")]
plugin_count = 0
if os.path.isdir(f"{BASE}/plugins"):
    for pdir in sorted(os.listdir(f"{BASE}/plugins")):
        if not os.path.isdir(f"{BASE}/plugins/{pdir}"):
            continue
        for root, dirs, files in os.walk(f"{BASE}/plugins/{pdir}"):
            dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
            for fn in sorted(files):
                if fn.endswith((".yml", ".yaml")) and fn not in SKIP_FILES:
                    plugin_count += 1
core_n = len(core_scan)
out.append(f"## 审计范围：{core_n} 个核心 + {plugin_count} 个插件配置文件\n")
out.append("| 类别 | 数量 |")
out.append("|:--|:--|")
out.append(f"| 核心配置（服务端） | {core_n} |")
out.append(f"| 插件配置 | {plugin_count} |")
out.append(f"| **合计** | **{core_n + plugin_count}** |\n")
out.append("判定口径：**交集语义**（两端共同 key 值同=完全一致；单端独有 key 另计）\n")
out.append("---\n## 一、核心配置（服务端）\n")

core_same = core_diff = 0
core_files = [f for f in sorted(core_scan) if not f.startswith(".")]
for name in core_files:
    st, diffs, side = diff_file(f"{BASE}/{name}", f"{E}/{name}", eq_style=(name in EQ_STYLE))
    if st == 'same':
        core_same += 1
        out.append(f"### ✅ {name} — 两端完全一致\n")
    elif st in ('base_missing', 'cmp_missing'):
        core_diff += 1
        out.append(f"### ❌ {name} — {('基准端缺失' if st == 'base_missing' else 'Exa 端缺失')}\n")
    else:
        core_diff += 1
        side_note = f"，另有单端独有 key {len(side)} 个" if side else ""
        out.append(f"### ❌ {name} — 差异 {len(diffs)} 处{side_note}\n")
        out.append("| key | MCSM({SERVER_NAME}) | Exa |")
        out.append("|:--|:--|:--|")
        for k, vb, vc in diffs:
            out.append(f"| {label(k)} | {vb} | {vc} |")
        out.append("")

# 插件配置
out.append("---\n## 二、插件配置（按插件分组）\n")
plugin_dirs = sorted([d for d in os.listdir(f"{BASE}/plugins") if os.path.isdir(f"{BASE}/plugins/{d}")]) \
    if os.path.isdir(f"{BASE}/plugins") else []
total_same = total_diff = total_data = 0
for pdir in plugin_dirs:
    entries = []
    for root, dirs, files in os.walk(f"{BASE}/plugins/{pdir}"):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for fn in sorted(files):
            if not fn.endswith((".yml", ".yaml")) or fn in SKIP_FILES:
                continue
            rel = os.path.relpath(os.path.join(root, fn), f"{BASE}/plugins/{pdir}")
            name = f"{pdir}/{rel}"
            st, diffs, side = diff_file(f"{BASE}/plugins/{pdir}/{rel}", f"{E}/plugins/{pdir}/{rel}")
            entries.append((name, rel, st, diffs, side))
    if not entries:
        continue
    same = [e for e in entries if e[2] == 'same']
    diff = [e for e in entries if e[2] == 'diff']
    missing = [e for e in entries if e[2] == 'cmp_missing']
    data_files_in_dir = [e for e in entries if e[0] in DATA_FILES]
    data_same = len([e for e in data_files_in_dir if e[2] == 'same'])
    data_diff = len([e for e in data_files_in_dir if e[2] == 'diff'])
    same_eff = len(same) - data_same
    diff_eff = len(diff) - data_diff + len(missing)
    total_same += same_eff
    total_diff += diff_eff
    status_icon = "✅" if not diff_eff else "❌"
    out.append(f"### {status_icon} {pdir}（{len(entries)} 个：{same_eff} 一致 / {diff_eff} 差异 / {len(data_files_in_dir)} 数据）\n")
    for name, rel, st, diffs, side in entries:
        if name in DATA_FILES:
            total_data += 1
            out.append(f"- ℹ️ `{rel}` 运行时数据（玩家/交易/记录，两端独立属正常）")
        elif st == 'same':
            out.append(f"- ✅ `{rel}` 两端完全一致")
        elif st == 'cmp_missing':
            out.append(f"- ❌ `{rel}` Exa 端缺失（MCSM 有、Exaroton 无）")
        elif st == 'diff':
            out.append(f"- ❌ `{rel}` 差异 {len(diffs)} 处：")
            for k, vb, vc in diffs[:10]:
                out.append(f"  - `{label(k)}`：MCSM=`{vb}` Exa=`{vc}`")
            if len(diffs) > 10:
                out.append(f"  - …等共 {len(diffs)} 处")
    out.append("")

out.append("---\n## 三、汇总\n")
out.append("| 状态 | 核心 | 插件 | 合计 |")
out.append("|:--|:--|:--|:--|")
out.append(f"| ✅ 两端完全一致 | {core_same} | {total_same} | {core_same + total_same} |")
out.append(f"| ❌ 配置差异 | {core_diff} | {total_diff} | {core_diff + total_diff} |")
out.append(f"| ℹ️ 运行时数据差异（正常） | 0 | {total_data} | {total_data} |")
out.append(f"| **合计** | **{core_same + core_diff}** | **{total_same + total_diff + total_data}** | **{core_same + core_diff + total_same + total_diff + total_data}** |")
out.append("\n> 注：运行时数据文件 = 玩家家/死亡点/交易记录/审批记录等随玩家变化的内容，两端独立属预期，不算配置漂移。")

report = "\n".join(out)
open("/tmp/cmp3_report_latest.md", "w").write(report)
print(report)
