#!/usr/bin/env python3
"""MC 两端版本巡检 v3（2026-09-09 迁移后：部署源 = MCSM {SERVER_NAME} Windows 栈）
核心 + 插件部署版本（MCSM 面板 API 列 jar 文件名解析）vs 各渠道最新版
精确匹配：jar 文件名 → 插件标准名映射表 + 构建后缀剥离 + 本地打包插件分类。
输出：对比表 + 差异汇总（stdout）。由 cron 调度，失败单项容错不中断。
"""
import json, os, re, subprocess, sys, urllib.request, urllib.parse

try:  # Windows 控制台默认 GBK：统一转 UTF-8，避免 emoji/中文触发 UnicodeEncodeError 中断巡检
    import sys as _sys
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

sys.path.insert(0, os.path.expanduser("~/.hermes/skills/gaming/orzmc/scripts/cmp3"))
from mcsm_env import get_mcsm_local_config, mcsm_list

UA = {"User-Agent": "Mozilla/5.0"}
def _skill_scripts_dir():
    """定位技能 scripts 目录（跨平台：Windows %LOCALAPPDATA%\\hermes 优先，回退 ~/.hermes）"""
    cands = []
    la = os.environ.get("LOCALAPPDATA")
    if la:
        cands.append(os.path.join(la, "hermes", "skills", "gaming", "orzmc", "scripts"))
    cands.append(os.path.expanduser("~/.hermes/skills/gaming/orzmc/scripts"))
    for c in cands:
        if os.path.isdir(c):
            return c
    return cands[-1]


PARSE_PAPERMC = os.path.join(_skill_scripts_dir(), "parse_papermc.py")
FOLIA_INSTANCE_ID = "8A932DD47F4D42AAAD6A6A9A5FAD2A91"  # folia-test 实例（同 daemon）

# jar 文件名 → 标准名（CHANNEL key）；扫描自迁移前本地目录 plugin.yml（2026-09-09 固化）
# 新增插件/改文件名时更新；未命中会走"未知"分支提示
FNAME_NAME = {
    "BackOnDeath.jar": "BackOnDeath", "EssentialsX-2.22.0.jar": "Essentials",
    "EzShops-2.5.9.jar": "EzShops", "F3F4Perms-1.3.0.jar": "F3F4Perms",
    "GetMeHome-3.0.2-dev.jar": "GetMeHome", "Geyser-Spigot-1235.jar": "Geyser-Spigot",
    "GriefPrevention.jar": "GriefPrevention", "LoginSecurity-3.3.2-SNAPSHOT.jar": "LoginSecurity",
    "LuckPerms-5.5.82.jar": "LuckPerms", "OrzMC-1.0.25-dev.416.jar": "OrzMC",
    "SkinsRestorer.jar": "SkinsRestorer", "Vault.jar": "Vault",
    "ViaBackwards-5.11.0.jar": "ViaBackwards", "ViaRewind-4.1.3.jar": "ViaRewind",
    "ViaVersion-5.11.0.jar": "ViaVersion", "deathchest.jar": "DeathChest",
    "grimac-bukkit-2.3.74.jar": "GrimAC", "packetevents-spigot-2.13.0.jar": "packetevents",
    "voicechat-bukkit-2.6.23.jar": "voicechat", "worldedit-bukkit-7.4.5.jar": "WorldEdit",
    "worldguard-bukkit-7.0.18.jar": "WorldGuard",
    # ---- folia-test 实例独有（2026-09-12 升 dev/beta 轨道后固化）----
    "AxGraves-1.31.0.jar": "AxGraves", "EssentialsC-4.3.0-all.jar": "EssentialsC",
    "ExecutableEvents-3.26.9.9.jar": "ExecutableEvents", "SCore-5.26.9.9.jar": "SCore",
    "GriefPrevention3D.jar": "GriefPrevention3D", "SimpleLogin-1.16.7.jar": "SimpleLogin",
    "VaultUnlocked-2.20.2.jar": "VaultUnlocked",
}
# 前缀兜底（2026-09-14）：文件名自带版本号的插件升级后文件名会变，
# 精确表未命中时按前缀解析，避免每次版本 bump 都要改 FNAME_NAME
PREFIX_NAME = {
    "OrzMC-": "OrzMC", "LuckPerms-": "LuckPerms", "EssentialsX-": "Essentials",
    "EzShops-": "EzShops", "GetMeHome-": "GetMeHome", "Geyser-Spigot-": "Geyser-Spigot",
    "LoginSecurity-": "LoginSecurity", "ViaBackwards-": "ViaBackwards",
    "ViaRewind-": "ViaRewind", "ViaVersion-": "ViaVersion",
    "AxGraves-": "AxGraves", "EssentialsC-": "EssentialsC",
    "ExecutableEvents-": "ExecutableEvents", "SCore-": "SCore", "SimpleLogin-": "SimpleLogin",
    "VaultUnlocked-": "VaultUnlocked", "grimac-bukkit-": "GrimAC",
    "packetevents-spigot-": "packetevents", "voicechat-bukkit-": "voicechat",
    "worldedit-bukkit-": "WorldEdit", "worldguard-bukkit-": "WorldGuard",
    "F3F4Perms-": "F3F4Perms",
    # 2026-10-12 补：这两个 jar 从「无版本号文件名」改成了「带版本号文件名」，
    # 精确表未命中 → 报「未识别 jar」+ SkinsRestorer 误报「未部署」
    # ⚠️ 前缀按长度降序匹配，故 GriefPrevention3D- 不会被 GriefPrevention- 抢走
    "GriefPrevention3D-": "GriefPrevention3D", "GriefPrevention-": "GriefPrevention",
    "SkinsRestorer-": "SkinsRestorer", "deathchest-": "DeathChest",
    "BackOnDeath-": "BackOnDeath", "Vault-": "Vault",
}

def resolve_name(fname):
    """jar 文件名 → 标准名：精确表优先，未命中走前缀兜底，仍未知返回 None"""
    std = FNAME_NAME.get(fname)
    if std:
        return std
    for pfx, name in sorted(PREFIX_NAME.items(), key=lambda kv: -len(kv[0])):
        if fname.startswith(pfx) and fname.endswith(".jar"):
            return name
    return None

# 扫描时填充：标准名 → 实际 jar 文件名（Geyser 等需从文件名取 build 号）
RAW_FNAME = {}
# 文件名无版本号 jar 的静态部署版本（扫描自 plugin.yml；升级时更新）
# ⚠️⚠️ 2026-10-05 教训：这张表**会静默过期**——SkinsRestorer 实为 15.12.6，表里写 15.12.5
#      导致巡检报「有更新可用」的**假阳性**（照它去"升级"其实是同版本空操作）。
#      凡「文件名不含版本号」的插件（SkinsRestorer/Vault/BackOnDeath/deathchest/GriefPrevention）
#      升级后必须同步改这里；更稳的做法是从实例 logs/latest.log 的 `Loading server plugin X vY` 反解。
FNAME_FALLBACK_VER = {
    "BackOnDeath": "0.4", "GriefPrevention": "16.18.7", "SkinsRestorer": "15.12.6",
    "Vault": "1.7.3-b131", "Geyser-Spigot": "2.11.2-SNAPSHOT", "DeathChest": "3.0.1",
    "GriefPrevention3D": "18.4.8", "VaultUnlocked": "2.20.3",
}
# 仅 folia-test 实例部署的插件（第二张表用；避免与 paper 表重复列同版本项）
FOLIA_ONLY = {"AxGraves", "EssentialsC", "ExecutableEvents", "SCore", "GriefPrevention3D",
              "SimpleLogin", "VaultUnlocked", "CustomWorldHeight"}

# plugin.yml name -> 展示名 / 渠道映射
CHANNEL = {
    "OrzMC": "hangar", "EzShops": "local", "LoginSecurity": "local",
    "DeathChest": "local", "GetMeHome": "local",
    "BackOnDeath": "stable", "Vault": "stable",
    "Essentials": "github", "Geyser-Spigot": "geyser",
    "CustomWorldHeight": "modrinth",
    "GriefPrevention": "modrinth", "LuckPerms": "luckperms",
    "SkinsRestorer": "modrinth", "ViaBackwards": "modrinth",
    "ViaRewind": "modrinth", "ViaVersion": "modrinth",
    "WorldEdit": "modrinth", "WorldGuard": "modrinth",
    "F3F4Perms": "modrinth", "packetevents": "modrinth",
    "GrimAC": "github", "voicechat": "modrinth",
    # folia-test 独有插件（2026-09-12 新增）
    "AxGraves": "modrinth", "EssentialsC": "modrinth", "ExecutableEvents": "modrinth",
    "SCore": "modrinth", "GriefPrevention3D": "modrinth", "SimpleLogin": "modrinth",
    "VaultUnlocked": "modrinth",
}

def get(url, timeout=15):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="replace")

def safe(fn, default="查询失败"):
    try:
        return fn()
    except Exception:
        return default

def paper_latest():
    out = subprocess.run([sys.executable, PARSE_PAPERMC], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
    line = (out.stdout or "").strip().splitlines()
    if line:
        m = re.match(r"(paper-\d+\.\d+-\d+)", line[0])
        if m:
            return m.group(1)
    return "解析失败"

def folia_latest():
    """最新**非 ALPHA** 的 Folia 构建（2026-11-02 起：ALPHA 不算可升，避免每周误报）"""
    try:
        d = json.loads(get("https://fill.papermc.io/v3/projects/folia/versions"))
        for v in d.get("versions", []):
            vid = v["version"]["id"]
            bs = json.loads(get("https://fill.papermc.io/v3/projects/folia/versions/%s/builds" % vid))
            if not bs:
                continue
            top = bs[0]
            if top.get("channel") in ("STABLE", "BETA"):
                return "folia-%s-%s(%s)" % (vid, top["id"], top["channel"])
        return "无 STABLE/BETA 构建"
    except Exception as e:
        return "解析失败(%s)" % str(e)[:20]

def mcsm_plugin_versions(cfg, instance_id=None):
    """MCSM({SERVER_NAME}) 实例 plugins/ 目录 jar 文件名 → {标准名: 版本串}
    返回 (deploy_dict, unknown_jars)；未知 jar（映射表未登记）进 unknown 由调用方提示
    副作用：填充全局 RAW_FNAME（标准名 → 实际 jar 文件名），供 Geyser build 号解析
    """
    import copy
    if instance_id:
        cfg = copy.copy(cfg)
        cfg["instance_id"] = instance_id
    out, unknown = {}, []
    try:
        items = mcsm_list(cfg, "/plugins")
    except Exception as e:
        print(f"⚠️ MCSM plugins 列取失败: {e}")
        return out, unknown
    for name, typ in items:
        if typ != 1 or not name.endswith(".jar"):
            continue
        std = resolve_name(name)
        if std is None:
            unknown.append(name)
            continue
        RAW_FNAME[std] = name
        # 文件名版本提取：Name-<ver>.jar（不匹配则静态 fallback / 不设（走未知提示））
        m = re.match(r"^[A-Za-z0-9_+-]+-([0-9][0-9A-Za-z._+-]*)\.jar$", name)
        ver = m.group(1) if m else FNAME_FALLBACK_VER.get(std)
        if ver:
            out[std] = ver
        else:
            unknown.append(name)
    return out, unknown

def folia_deployed(cfg):
    """MCSM folia-test 实例根目录 folia-*.jar 版本（API 列目录）
    固定名部署（folia.jar，版本只在启动日志里）→ 返回 '固定名部署'
    """
    import copy
    fcfg = copy.copy(cfg)
    fcfg["instance_id"] = FOLIA_INSTANCE_ID
    try:
        items = mcsm_list(fcfg, "/")
    except Exception:
        return "查询失败"
    vers, bare = [], False
    for name, typ in items:
        if typ == 1:
            m = re.match(r"folia-(\d+\.\d+-\d+)\.jar", name)
            if m:
                vers.append(m.group(1))
            elif name == "folia.jar":
                bare = True
    if vers:
        return max(vers, key=lambda v: tuple(int(x) for x in v.replace("-", ".").split(".")))
    return "固定名部署" if bare else "未部署"

def modrinth_latest(slug, loaders=None):
    d = json.loads(get(f"https://api.modrinth.com/v2/project/{slug}/version"))
    for v in d:
        if v.get("version_type") != "release":
            continue
        if loaders and not any(l in loaders for l in v.get("loaders", [])):
            continue
        return re.sub(r"^[a-z]+-(?=\d)", "", v["version_number"])
    return re.sub(r"^[a-z]+-(?=\d)", "", d[0]["version_number"]) if d else "无"

def strip_build(v):
    v = re.sub(r"\+.*$", "", str(v))
    v = re.sub(r"-(neoforge|forge|fabric|spigot|bukkit)$", "", v, flags=re.I)
    v = re.sub(r"-\w{6,8}$", "", v)
    return v

def ver_key(v):
    m = re.search(r"(\d+(?:\.\d+)*)", str(v))
    if m:
        try:
            return tuple(int(x) for x in m.group(1).split("."))
        except ValueError:
            pass
    return (0,)

# ---- 采集 ----
cfg = get_mcsm_local_config()
core_latest = safe(paper_latest)
deploy = {}
plugins, unknown_jars = mcsm_plugin_versions(cfg)
for std, ver in plugins.items():
    if std == "Geyser-Spigot":
        # 文件名 Geyser-Spigot-<build>.jar：plugin.yml 版本固定 SNAPSHOT → 用 fallback 版本 + 文件名 build
        fname = RAW_FNAME.get("Geyser-Spigot", "")
        m = re.search(r"-(\d+)\.jar$", fname)
        deploy["Geyser-Spigot"] = f"{FNAME_FALLBACK_VER['Geyser-Spigot']} (build {m.group(1)})" if m else FNAME_FALLBACK_VER["Geyser-Spigot"]
    else:
        deploy[std] = ver

latest = {}
latest["ViaVersion"] = safe(lambda: modrinth_latest("viaversion"))
latest["ViaBackwards"] = safe(lambda: modrinth_latest("viabackwards"))
latest["ViaRewind"] = safe(lambda: modrinth_latest("viarewind"))
latest["WorldEdit"] = safe(lambda: modrinth_latest("worldedit"))
latest["WorldGuard"] = safe(lambda: modrinth_latest("worldguard"))
latest["GriefPrevention"] = safe(lambda: modrinth_latest("griefprevention"))
latest["CustomWorldHeight"] = safe(lambda: modrinth_latest("customworldheight"))
latest["SkinsRestorer"] = safe(lambda: modrinth_latest("skinsrestorer", loaders=["paper", "spigot", "bukkit"]))
latest["F3F4Perms"] = safe(lambda: modrinth_latest("f3f4perms"))
latest["packetevents"] = safe(lambda: modrinth_latest("packetevents", loaders=["paper", "spigot", "bukkit", "folia"]))
latest["LuckPerms"] = safe(lambda: json.loads(get("https://metadata.luckperms.net/data/all"))["version"])
latest["Geyser-Spigot"] = safe(lambda: (lambda d: f"{d['version']} (build {d['build']})")(
    json.loads(get("https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest"))))
latest["Essentials"] = safe(lambda: json.loads(get("https://api.github.com/repos/EssentialsX/Essentials/releases/latest"))["tag_name"])
latest["GrimAC"] = safe(lambda: json.loads(get("https://api.github.com/repos/GrimAnticheat/Grim/releases/latest"))["tag_name"])
latest["voicechat"] = safe(lambda: modrinth_latest("simple-voice-chat", loaders=["paper", "spigot", "bukkit", "folia"]))
latest["OrzMC"] = safe(lambda: (lambda d: d["result"][0]["name"])(
    json.loads(get("https://hangar.papermc.io/api/v1/projects/OrzMC/versions?limit=5&channel=Release"))))
latest["OrzMC_beta"] = safe(lambda: (lambda d: d["result"][0]["name"])(
    json.loads(get("https://hangar.papermc.io/api/v1/projects/OrzMC/versions?limit=5&channel=Beta"))))
# folia-test 独有插件（modrinth，loaders 含 folia）
latest["AxGraves"] = safe(lambda: modrinth_latest("axgraves", loaders=["bukkit", "paper", "folia"]))
latest["EssentialsC"] = safe(lambda: modrinth_latest("essentialsc", loaders=["bukkit", "paper", "folia"]))
latest["ExecutableEvents"] = safe(lambda: modrinth_latest("executableevents", loaders=["bukkit", "paper", "folia"]))
latest["SCore"] = safe(lambda: modrinth_latest("score", loaders=["bukkit", "paper", "folia"]))
latest["GriefPrevention3D"] = safe(lambda: modrinth_latest("griefprevention-3d-subdivisions", loaders=["bukkit", "paper", "folia"]))
latest["SimpleLogin"] = safe(lambda: modrinth_latest("simple-login", loaders=["folia"]))
latest["VaultUnlocked"] = safe(lambda: modrinth_latest("vaultunlocked", loaders=["bukkit", "paper", "folia"]))

# ---- 输出 ----
print("=" * 66)
print(f"{'组件':<20} {'部署(MCSM {SERVER_NAME})':<22} {'最新':<20} 状态")
print("=" * 66)
diffs = []
notes = {}

for name in sorted(deploy.keys()):
    dep = deploy[name]
    chan = CHANNEL.get(name, "?")
    if chan == "?":
        lat_txt = "未登记渠道"
        st = "➖未知"
    elif chan == "local":
        lat = latest.get(name, "")
        lat_txt = f"本地构建 {lat}" if lat and not str(lat).startswith("查询失败") else "本地构建"
        st = "➖本地"
    elif chan == "stable":
        lat_txt = "无渠道/稳定"
        st = "➖稳定"
    elif chan == "hangar":
        # dev/beta 轨道实例只对比 Hangar Beta 渠道（2026-09-12 决策：测试服跟 dev/beta 验证插件功能）——
        # 否则每天误报「可升正式版」，而正式版在 dev 轨道机上等于降级
        is_dev = "-dev." in str(dep)
        lat = latest.get("OrzMC_beta" if is_dev else name, "查询失败")
        ch_txt = "Hangar beta" if is_dev else "Hangar release"
        lat_txt = f"{ch_txt} {lat}" if not str(lat).startswith("查询失败") else lat
        if str(lat).startswith("查询失败"):
            st = "❓"
        elif is_dev:
            same = str(dep) == str(lat) or ver_key(dep) > ver_key(lat)
            st = "✅" if same else "⚠️"
            if not same:
                diffs.append(f"OrzMC {dep} → {lat}")
        else:
            dep_main = re.sub(r"-dev.*$", "", dep)
            if dep_main != lat:
                st = "⚠️" if dep_main < lat else "✅"
                if st == "⚠️":
                    diffs.append(f"OrzMC {dep} → {lat}")
            else:
                st = "✅"
    else:
        lat = latest.get(name, "查询失败")
        lat_txt = str(lat)
        if str(lat).startswith("查询失败"):
            st = "❓"
        else:
            if name == "Geyser-Spigot":
                dep_b = re.search(r"build (\d+)", str(dep))
                lat_b = re.search(r"build (\d+)", lat)
                same = bool(dep_b and lat_b and dep_b.group(1) == lat_b.group(1))
            else:
                dep_v, lat_v = strip_build(dep), strip_build(lat)
                same = dep_v == lat_v or ver_key(dep_v) >= ver_key(lat_v)
            PRE_RE = re.compile(r"(dev\.|SNAPSHOT|snapshot|alpha|beta|-[0-9a-f]{7,}$)", re.I)
            dep_is_pre = bool(PRE_RE.search(str(dep)))
            if name == "Geyser-Spigot":
                dep_is_pre = False  # Geyser 官方只发这种构建，无 release/beta 之分
            if same:
                if dep_is_pre:
                    st = "🔵预发布"
                    notes[name] = "部署为预发布构建（上游正式版 %s）→ 按「只跟 release」纪律应回退" % lat
                elif ver_key(strip_build(dep)) > ver_key(strip_build(lat)):
                    st = "🔵高于正式版"
                    notes[name] = "部署 %s > 正式版 %s（原 beta 线）→ 按纪律应回退" % (dep, lat)
                else:
                    st = "✅"
            else:
                st = "⚠️"
                diffs.append(f"{name} {dep} → {lat}")
    print(f"{name:<20} {str(dep):<22} {lat_txt:<20} {st}")

for name in sorted(CHANNEL.keys()):
    if name in FOLIA_ONLY:
        continue  # folia 独有插件由下方第二张表覆盖
    if name not in deploy:
        print(f"{name:<20} {'未部署':<22} {'—':<20} ➖")

# ---- folia-test 实例独有插件（2026-09-12 新增；dev/beta 轨道验证机）----
folia_deploy, folia_unknown = mcsm_plugin_versions(cfg, FOLIA_INSTANCE_ID)
print()
print("=" * 66)
print("folia-test 独有插件")
print("=" * 66)
for name in sorted(FOLIA_ONLY):
    dep = folia_deploy.get(name, "未部署")
    if dep == "未部署":
        print(f"{name:<20} {'未部署':<22} {'—':<20} ➖")
        continue
    lat = latest.get(name, "查询失败")
    lat_txt = str(lat)
    if str(lat).startswith("查询失败"):
        st = "❓"
    else:
        dep_v, lat_v = strip_build(dep), strip_build(lat)
        same = dep_v == lat_v or ver_key(dep_v) >= ver_key(lat_v)
        st = "✅" if same else "⚠️"
        if not same:
            diffs.append(f"[folia] {name} {dep} → {lat}")
    print(f"{name:<20} {str(dep):<22} {lat_txt:<20} {st}")

if unknown_jars or folia_unknown:
    allunk = sorted(set(unknown_jars) | set(folia_unknown))
    print(f"\n⚠️ 未识别 jar（需更新 FNAME_NAME 映射表）: {', '.join(allunk)}")

print("=" * 66)
core_txt = f"Paper核心 {core_latest}" if not str(core_latest).startswith("查询失败") else "Paper核心(查询失败)"
print(f"核心: {core_txt}")
folia_txt = folia_latest()
folia_dep = folia_deployed(cfg)
if str(folia_txt).startswith("解析失败"):
    print("Folia核心: (查询失败)")
elif folia_dep == "未部署":
    print(f"Folia核心: {folia_txt}（MCSM 未部署）")
elif folia_dep == "固定名部署":
    print(f"Folia核心: {folia_txt}（folia.jar 固定名部署 → 实际版本以启动日志 This server is running Folia 行为准）")
elif folia_dep == "查询失败":
    print(f"Folia核心: {folia_txt}（MCSM 版本查询失败）")
else:
    _folia_norm = re.sub(r"\(.*\)$", "", re.sub(r"^folia-", "", folia_txt))
    folia_st = "✅" if folia_dep == _folia_norm else "⚠️"
    print(f"Folia核心: {folia_txt}（MCSM {folia_dep} {folia_st}）")
    if folia_st == "⚠️":
        diffs.append(f"Folia {folia_dep} → {folia_txt}")
if notes:
    print("🔵 预发布/超正式版（按「只跟 release」纪律处理）：")
    for k, v in notes.items():
        print(f"  • {k}: {v}")
if diffs:
    print("⚠️ 有更新可用：")
    for d in diffs:
        print("  • " + d)
else:
    print("✅ 已部署插件无新版本（本地打包版以本地构建为准）")
