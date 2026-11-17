#!/usr/bin/env python3
"""OrzMC 插件权限/指令清单生成器（2026-08-30 任务1）

扫描插件目录所有 jar，提取 plugin.yml/paper-plugin.yml 的 commands + permissions，
生成全量 JSON（~/.hermes/state/plugin_inventory.json）+ 按插件分组的 Markdown 文档
（输出到 orzmc 技能 references/plugin-inventory.md）。

用法:
  python3 plugin_inventory.py [插件目录] [--out-md 输出路径] [--out-json 输出路径]

特点:
- 兼容 children 为 dict 或 list 的权限结构
- 动态权限插件（plugin.yml 无 permissions 段）从 EXTRA_PERMS 补充字典读取
- 指令用途取 plugin.yml description；权限默认值标准化（true/false/op/not op）
- 组分配标注从 EXTRA_GROUP_MAP 映射（维护来源 permission-groups.md）
"""
import zipfile, yaml, os, sys, json, datetime, argparse

DEFAULT_PLUGIN_DIR = os.path.expanduser("/Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/716c2fb712154c36ba5ab0f1480d3f87/plugins")
DEFAULT_JSON = os.path.expanduser("~/.hermes/state/plugin_inventory.json")
DEFAULT_MD = os.path.expanduser("~/.hermes/skills/gaming/orzmc/references/plugin-inventory.md")

# 动态权限插件补充字典（plugin.yml 无 permissions/commands 段，需人工维护，来源=官方 wiki/技能知识）
# 结构: {"文件名": {"commands": {cmd: {aliases, description, permission}}, "permissions": {node: {description, default}}}}
EXTRA_PERMS = {
    "worldedit": {
        "commands": {
            "//wand": {"description": "获取木斧选区工具", "permission": "worldedit.wand"},
            "//pos1": {"description": "设置选区点1", "permission": "worldedit.selection.pos"},
            "//pos2": {"description": "设置选区点2", "permission": "worldedit.selection.pos"},
            "//set": {"description": "填充选区", "permission": "worldedit.region.set"},
            "//copy": {"description": "复制选区到剪贴板", "permission": "worldedit.clipboard.copy"},
            "//paste": {"description": "粘贴剪贴板", "permission": "worldedit.clipboard.paste"},
            "//undo": {"description": "撤销上次编辑", "permission": "worldedit.history.undo"},
            "//redo": {"description": "重做", "permission": "worldedit.history.redo"},
            "//limit": {"description": "查看/设置单次编辑方块上限", "permission": "worldedit.limit"},
            "//schem": {"description": "原理图保存/加载/粘贴", "permission": "worldedit.schematic.*"},
            "//replace": {"description": "替换方块", "permission": "worldedit.region.replace"},
            "//fill": {"description": "填充", "permission": "worldedit.region.fill"},
            "//count": {"description": "统计方块", "permission": "worldedit.analysis.count"},
            "//unstuck": {"description": "脱困（当前命令未注册）", "permission": "worldedit.navigation.unstuck"},
            "//expand": {"description": "扩展选区", "permission": "worldedit.selection.expand"},
            "//contract": {"description": "收缩选区", "permission": "worldedit.selection.contract"},
            "//brush": {"description": "设置笔刷", "permission": "worldedit.brush.*"},
            "//tool": {"description": "绑定工具", "permission": "worldedit.tool.*"},
            "//gmask": {"description": "全局遮罩", "permission": "worldedit.global-mask"},
        },
        "permissions": {
            "worldedit.wand": {"description": "使用木斧", "default": "op"},
            "worldedit.selection.*": {"description": "选区操作（pos1/pos2/expand 等）", "default": "op"},
            "worldedit.selection.pos": {"description": "设置选区点", "default": "op"},
            "worldedit.region.*": {"description": "区域操作（set/replace/fill 等）", "default": "op"},
            "worldedit.region.set": {"description": "填充选区", "default": "op"},
            "worldedit.clipboard.*": {"description": "剪贴板（copy/paste）", "default": "op"},
            "worldedit.history.*": {"description": "历史（undo/redo）", "default": "op"},
            "worldedit.limit": {"description": "查看/设置编辑上限", "default": "op"},
            "worldedit.schematic.*": {"description": "原理图", "default": "op"},
            "worldedit.brush.*": {"description": "笔刷", "default": "op"},
            "worldedit.tool.*": {"description": "工具绑定", "default": "op"},
            "worldedit.utility.*": {"description": "实用命令（fill/drain）", "default": "op"},
            "worldedit.analysis.*": {"description": "分析统计", "default": "op"},
            "worldedit.navigation.*": {"description": "导航（unstuck 未注册）", "default": "op"},
            "worldedit.reload": {"description": "重载配置（管理）", "default": "op"},
            "worldedit.global-mask": {"description": "全局遮罩", "default": "op"},
            "worldedit.setnbt": {"description": "设置方块实体 NBT（容器/告示牌内容）", "default": "op"},
        },
    },
    "worldguard": {
        "commands": {
            "/rg": {"description": "领地管理（create/claim/define 等）", "permission": "worldguard.region.*"},
            "//claim": {"description": "选区圈地", "permission": "worldguard.region.claim"},
            "/rg info": {"description": "查看领地信息", "permission": "worldguard.region.info"},
            "/rg flag": {"description": "设置领地标志", "permission": "worldguard.region.flag.flag"},
            "/rg list": {"description": "列出领地", "permission": "worldguard.region.list"},
            "/rg addmember": {"description": "添加成员", "permission": "worldguard.region.addmember"},
            "/rg removemember": {"description": "移除成员", "permission": "worldguard.region.removemember"},
        },
        "permissions": {
            "worldguard.region.claim": {"description": "圈地", "default": "op"},
            "worldguard.region.info": {"description": "查看领地信息", "default": "op"},
            "worldguard.region.list": {"description": "列出领地", "default": "op"},
            "worldguard.region.addmember": {"description": "添加成员", "default": "op"},
            "worldguard.region.removemember": {"description": "移除成员", "default": "op"},
            "worldguard.region.flag.flag": {"description": "设置领地标志", "default": "op"},
            "worldguard.region.bypass": {"description": "绕过领地保护（管理，任何组不授）", "default": "op"},
            "worldguard.region.flag.*": {"description": "全部领地标志（管理）", "default": "op"},
        },
    },
    "luckperms": {
        "commands": {
            "/lp": {"description": "权限管理总命令（user/group/track）", "permission": "luckperms.*"},
        },
        "permissions": {
            "luckperms.*": {"description": "全部 LP 管理权限（仅 admin）", "default": "op"},
            "luckperms.user.info": {"description": "查看用户信息", "default": "op"},
            "luckperms.user.promote": {"description": "用户晋升", "default": "op"},
            "luckperms.user.demote": {"description": "用户降级", "default": "op"},
        },
    },
    "geyser": {
        "commands": {
            "/geyser": {"description": "Geyser 管理（status/version 等）", "permission": "geyser.command.*"},
        },
        "permissions": {
            "geyser.command.*": {"description": "Geyser 管理命令", "default": "op"},
        },
    },
    "skinsrestorer": {
        "commands": {
            "/skin": {"description": "设置皮肤", "permission": "skinsrestorer.command.skin"},
            "/skin set": {"description": "设置皮肤", "permission": "skinsrestorer.command.skin"},
            "/skin clear": {"description": "清除皮肤", "permission": "skinsrestorer.command.skin"},
        },
        "permissions": {
            "skinsrestorer.command.skin": {"description": "设置/清除皮肤（默认所有玩家）", "default": "true"},
            "skinsrestorer.command.skin.set": {"description": "设置皮肤", "default": "true"},
            "skinsrestorer.command.skin.clear": {"description": "清除皮肤", "default": "true"},
        },
    },
    "viaversion": {
        "commands": {"/viaversion": {"description": "ViaVersion 管理（版本兼容信息）", "permission": "viaversion.admin"}},
        "permissions": {"viaversion.admin": {"description": "ViaVersion 管理", "default": "op"}},
    },
    "packetevents": {
        "commands": {"/packetevents": {"description": "packetevents 调试/管理", "permission": "packetevents.*"}},
        "permissions": {"packetevents.*": {"description": "packetevents 管理（内部库，正常不授予）", "default": "op"}},
    },
    "orzmc": {
        "commands": {
            "/config": {"description": "OrzMC 配置管理（别名 /cfg）", "permission": "orzmc.admin"},
            "/apply": {"description": "申请晋升（member→builder）", "permission": "orzmc.apply"},
            "/review": {"description": "审核申请（管理）", "permission": "orzmc.review"},
            "/orzdebug": {"description": "模拟群管理员发 Bot 命令（测试）", "permission": "orzmc.admin"},
            "/portal": {"description": "跨服传送门管理", "permission": "orzmc.admin"},
        },
        "permissions": {
            "orzmc.admin": {"description": "OrzMC 管理命令", "default": "op"},
            "orzmc.tpbow.use": {"description": "使用传送弓", "default": "true"},
            "orzmc.apply": {"description": "提交晋升申请", "default": "true"},
            "orzmc.review": {"description": "审核申请（admin 或 op）", "default": "op"},
        },
    },
}

# 组分配映射（来源 permission-groups.md 唯一事实源；格式: 权限节点 → 组列表）
# L0=default L1=member L2=builder L3=admin
EXTRA_GROUP_MAP = {
    # OrzMC
    "orzmc.tpbow.use": ["default"], "orzmc.apply": ["default"], "orzmc.admin": ["admin"], "orzmc.review": ["admin"],
    # WorldEdit（builder L2）
    "worldedit.wand": ["builder"], "worldedit.selection.*": ["builder"], "worldedit.selection.pos": ["builder"],
    "worldedit.region.*": ["builder"], "worldedit.region.set": ["builder"], "worldedit.clipboard.*": ["builder"],
    "worldedit.history.*": ["builder"], "worldedit.brush.*": ["builder"], "worldedit.tool.*": ["builder"],
    "worldedit.utility.*": ["builder"], "worldedit.help": ["builder"], "worldedit.schematic.*": ["builder"],
    "worldedit.navigation.*": ["builder"], "worldedit.analysis.*": ["builder"],
    # WorldGuard（builder 圈地）
    "worldguard.region.claim": ["builder"], "worldguard.region.info": ["builder"], "worldguard.region.list": ["builder"],
    # LuckPerms
    "luckperms.*": ["admin"],
    # SkinsRestorer
    "skinsrestorer.command.skin": ["default"], "skinsrestorer.command.skin.set": ["default"], "skinsrestorer.command.skin.clear": ["default"],
}


def flatten_perms(perms, prefix="", out=None):
    """权限树扁平化，兼容 children 为 dict 或 list"""
    if out is None:
        out = {}
    for k, v in (perms or {}).items():
        node = k if not prefix else f"{prefix}.{k}"
        if isinstance(v, dict):
            out[node] = {
                "description": v.get("description", ""),
                "default": str(v.get("default", "")),
            }
            children = v.get("children", {})
            if children:
                if isinstance(children, dict):
                    flatten_perms(children, node, out)
                elif isinstance(children, list):
                    for c in children:
                        if isinstance(c, str):
                            out[f"{node}.{c}"] = {"description": "", "default": ""}
        elif isinstance(v, str):
            out[node] = {"description": v, "default": ""}
    return out


def extract_jar(path):
    """提取单个 jar 的 commands + permissions"""
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        meta = None
        meta_file = None
        for mf in ("paper-plugin.yml", "plugin.yml"):
            if mf in names:
                meta = yaml.safe_load(z.read(mf))
                meta_file = mf
                break
        if not meta:
            return None
    commands = {}
    for cname, cdata in (meta.get("commands") or {}).items():
        if isinstance(cdata, dict):
            commands[cname] = {
                "aliases": cdata.get("aliases", []),
                "description": cdata.get("description", ""),
                "permission": cdata.get("permission", ""),
            }
        else:
            commands[cname] = {"aliases": [], "description": "", "permission": ""}
    return {
        "meta_file": meta_file,
        "name": meta.get("name", os.path.basename(path)),
        "version": meta.get("version", "?"),
        "commands": commands,
        "permissions": flatten_perms(meta.get("permissions") or {}),
    }


def generate_md(inventory, group_map=None):
    """按插件分组的 Markdown 文档（指令全量 + 权限全量 + 组分配标注）"""
    group_map = group_map or EXTRA_GROUP_MAP
    lines = []
    lines.append("# OrzMC 插件权限/指令清单（按插件分组）")
    lines.append("")
    lines.append(f"> 生成时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("> 生成方式：`scripts/plugin_inventory.py`（自动提取 jar plugin.yml + 人工补充字典 EXTRA_PERMS）")
    lines.append("> 数据源：`/Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/716c2fb712154c36ba5ab0f1480d3f87/plugins/*.jar`（Paper 实例）；组分配标注来源 `permission-groups.md` 唯一事实源")
    lines.append("> 定时更新：重新运行 `python3 ~/.hermes/skills/gaming/orzmc/scripts/plugin_inventory.py` 即可（可挂 cron）")
    lines.append("")

    # 总览表
    lines.append("## 插件总览")
    lines.append("")
    lines.append("| 插件 | 版本 | 指令数 | 权限数 | 角色 |")
    lines.append("|:--|:--|--:|--:|:--|")
    role_map = {
        "orzmc": "核心（自研）", "essentials": "基础命令", "luckperms": "权限管理", "worldedit": "建筑编辑",
        "worldguard": "领地保护", "griefprevention": "领地/圈地", "ezshops": "商店经济", "loginsecurity": "登录保护",
        "geyser": "基岩互通", "grimac": "反作弊", "voicechat": "语音", "skinsrestorer": "皮肤",
        "getmehome": "家传送", "deathchest": "死亡箱", "backondeath": "死亡回点", "vault": "经济接口",
        "f3f4perms": "游戏模式热键", "viaversion": "版本兼容", "viabackwards": "版本兼容", "viarewind": "版本兼容",
        "packetevents": "内部库",
    }
    for fname, d in sorted(inventory.items()):
        if "error" in d:
            lines.append(f"| {fname} | ❌ {d['error']} | - | - | - |")
            continue
        key = d["name"].lower()
        role = next((v for k, v in role_map.items() if k in key), "辅助")
        lines.append(f"| {d['name']} | {d['version']} | {len(d['commands'])} | {len(d['permissions'])} | {role} |")
    lines.append("")

    # 每插件详表
    idx = 0
    for fname, d in sorted(inventory.items()):
        if "error" in d:
            continue
        idx += 1
        lines.append(f"## {idx}. {d['name']} v{d['version']}")
        lines.append("")
        lines.append(f"- 文件：`{fname}`（{d['meta_file']}）")
        lines.append(f"- 指令 {len(d['commands'])} 个 / 权限节点 {len(d['permissions'])} 个")
        lines.append("")
        # 指令表
        if d["commands"]:
            lines.append("### 指令")
            lines.append("")
            lines.append("| 指令 | 别名 | 用途 | 所需权限 |")
            lines.append("|:--|:--|:--|:--|")
            for cname, cdata in sorted(d["commands"].items()):
                aliases = ",".join(cdata.get("aliases") or []) or "-"
                desc = (cdata.get("description") or "").replace("|", "\\|") or "-"
                perm = cdata.get("permission") or "-"
                lines.append(f"| `{cname}` | {aliases} | {desc} | `{perm}` |")
            lines.append("")
        # 权限表
        if d["permissions"]:
            lines.append("### 权限节点")
            lines.append("")
            lines.append("| 权限节点 | 描述 | 默认 | 组分配 |")
            lines.append("|:--|:--|:--|:--|")
            for pname, pdata in sorted(d["permissions"].items()):
                desc = (pdata.get("description") or "").replace("|", "\\|") or "-"
                default = pdata.get("default") or "-"
                groups = ",".join(group_map.get(pname, [])) if pname in group_map else "-"
                # 通配父节点也查子节点组
                if groups == "-":
                    for gk, gv in group_map.items():
                        if pname.endswith(".*") and gk.startswith(pname[:-1]):
                            groups = ",".join(gv)
                            break
                lines.append(f"| `{pname}` | {desc} | {default} | {groups} |")
            lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="OrzMC 插件权限/指令清单生成器")
    ap.add_argument("plugin_dir", nargs="?", default=DEFAULT_PLUGIN_DIR)
    ap.add_argument("--out-md", default=DEFAULT_MD)
    ap.add_argument("--out-json", default=DEFAULT_JSON)
    args = ap.parse_args()

    inventory = {}
    for fname in sorted(os.listdir(args.plugin_dir)):
        if not fname.endswith(".jar"):
            continue
        try:
            data = extract_jar(os.path.join(args.plugin_dir, fname))
        except Exception as e:
            inventory[fname] = {"error": str(e)}
            continue
        if not data:
            inventory[fname] = {"error": "无 plugin.yml/paper-plugin.yml"}
            continue
        # 动态插件用补充字典覆盖/合并
        key = data["name"].lower().replace("-", "").replace("spigot", "").replace("bukkit", "")
        for extra_key, extra in EXTRA_PERMS.items():
            if extra_key in fname.lower() or extra_key in data["name"].lower():
                data["commands"].update(extra.get("commands", {}))
                data["permissions"].update(extra.get("permissions", {}))
                data["_extra_source"] = True
        inventory[fname] = data

    os.makedirs(os.path.dirname(args.out_json), exist_ok=True)
    with open(args.out_json, "w") as f:
        json.dump(inventory, f, ensure_ascii=False, indent=1)
    print(f"✅ JSON 已生成: {args.out_json} ({len(inventory)} 插件)")

    md = generate_md(inventory)
    os.makedirs(os.path.dirname(args.out_md), exist_ok=True)
    with open(args.out_md, "w") as f:
        f.write(md)
    print(f"✅ Markdown 已生成: {args.out_md} ({len(md.splitlines())} 行)")


if __name__ == "__main__":
    main()
