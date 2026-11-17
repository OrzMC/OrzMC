#!/usr/bin/env python3
"""OrzMC 两端配置审查（Windows 本机版，2026-11-16 迁移）

与 Mac 版 `orzmc_config_audit.sh + cmp3/fetch3_*` 的等价实现，但**零 SSH、零面板 API**：

  基准端（测试服） = 本机 MCSM 实例目录直读
      E:/orzmc/mcsmanager/daemon/data/InstanceData/<paper uuid>/
  生效 Geyser 配置 = 代理侧 E:/orzmc/eagler/proxy/plugins/Geyser-Velocity/config.yml
      （ADR-036 后实例内 Geyser-Spigot 已被 Velocity 停用；存在代理配置即判 proxy 模式，
       不存在则回退实例内副本 = direct 模式）
  对比端（Exaroton） = 平台 API（需要 EXAROTON_API_KEY，走技能里的 exa_file.get_file）

输出：* `config-audit-latest.md` —— 每次运行无条件覆盖（永远是最新一次结论）
      * `config-audit-<yyyyMMdd-HHmm>.md` —— 每次也写快照，滚动只保留最近 3 份
      * 两个落点都执行：E:/orzmc/reports/ + 交付目录（S: 盘优先，不可见时降级本机 deliver，不报错）
stdout：结构化摘要（cron 直接投递）+ 末行 STATUS_LINE
退出码：0=SUCCESS / 1=数据源异常 / 3=仅告警

用法：
    python orzmc_config_audit.py            # 全量两端审查
    python orzmc_config_audit.py --local    # 只审测试服本地（跳过 Exa）
    python orzmc_config_audit.py --no-save  # 不落盘（调试）
"""
from __future__ import annotations

try:  # Windows 控制台默认 GBK：统一转 UTF-8，避免 emoji/中文触发 UnicodeEncodeError 中断巡检
    import sys as _sys
    _sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    _sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import os
import pathlib
import re
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from mcsm_env import get_mcsm_local_config, mcsm_scan_plugin_configs  # noqa: E402
from orzmc_paths import deliver_dir, env, redact, reports_dir  # noqa: E402

HERMES_HOME = pathlib.Path(os.environ.get("LOCALAPPDATA", "")) / "hermes"
if not HERMES_HOME.is_dir():
    HERMES_HOME = pathlib.Path.home() / ".hermes"
SKILL_SCRIPTS = HERMES_HOME / "skills" / "gaming" / "orzmc" / "scripts"
sys.path.insert(0, str(SKILL_SCRIPTS))
sys.path.insert(0, str(SKILL_SCRIPTS / "cmp3"))

PROXY_GEYSER = pathlib.Path("E:/orzmc/eagler/proxy/plugins/Geyser-Velocity/config.yml")

CORE = ["server.properties", "bukkit.yml", "spigot.yml", "commands.yml", "wepif.yml"]
CORE_MAP = {
    "config/paper-global.yml": "config_paper-global.yml",
    "config/paper-world-defaults.yml": "config_paper-world-defaults.yml",
}
EQ_STYLE = {"server.properties"}

SKIP_DIRS = {"userdata", "homes", "data", "players", "backups", "logs", "cache", "worlds", "messages"}
SKIP_FILES = {"ops.json", "whitelist.json", "banned-players.json", "banned-ips.json",
              "usercache.json", "permissions.yml", "help.yml"}


# ---------------- 对比引擎（与 Mac cmp3_configs.py 同语义） ----------------
def read(p: pathlib.Path):
    try:
        return p.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return None


def key_lines(lines, eq_style=False):
    out = []
    for l in lines:
        s = l.strip()
        if not s or s.startswith("#"):
            continue
        if eq_style:
            if "=" in l:
                k, v = l.split("=", 1)
                out.append((0, k.strip(), v.strip()))
        elif ":" in l:
            k, v = l.split(":", 1)
            out.append((len(l) - len(l.lstrip()), k.strip(), v.strip()))
    return out


def semantic_map(lines, eq_style=False):
    return {f"{ind}|{k}": v for ind, k, v in key_lines(lines, eq_style)}


def _norm(s):
    try:
        return ("num", float(s))
    except Exception:
        return ("str", s)


def diff_pair(base_lines, cmp_lines, eq_style=False):
    db = semantic_map(base_lines, eq_style)
    dc = semantic_map(cmp_lines or [], eq_style)
    diffs = []
    for k in sorted(set(db) & set(dc)):
        if db[k] == dc[k] or _norm(db[k]) == _norm(dc[k]):
            continue
        diffs.append((k, db[k], dc[k]))
    side = sum(1 for k in set(db) | set(dc) if (k in db) != (k in dc))
    return diffs, side


# ---------------- 数据源 ----------------
def local_snapshot():
    """测试服本地配置快照 → {相对路径: 文本行}"""
    cfg = get_mcsm_local_config()
    inst = pathlib.Path(cfg["base"]) / cfg["instance_id"]
    snap = {}
    if not inst.is_dir():
        return snap, None, "实例目录不存在: %s" % inst
    for cloud, flat in CORE_MAP.items():
        p = inst / cloud
        lines = read(p)
        if lines is not None:
            snap[flat] = lines
    for f in CORE:
        lines = read(inst / f)
        if lines is not None:
            snap[f] = lines
    plugin_cfgs = mcsm_scan_plugin_configs(cfg)
    for rel in plugin_cfgs:
        lines = read(inst / "plugins" / rel)
        if lines is not None:
            snap[f"plugins/{rel}"] = lines
    # 代理模式：用生效的 Geyser 配置覆盖实例内副本（对齐 Exa 同名路径便于比对）
    mode = "direct"
    if PROXY_GEYSER.is_file():
        lines = read(PROXY_GEYSER)
        if lines is not None:
            snap["plugins/Geyser-Spigot/config.yml"] = lines
            mode = "proxy"
    return snap, inst, mode


def exa_snapshot(plugin_cfgs):
    """Exaroton 配置快照 → {相对路径: 文本行}"""
    try:
        from exa_file import get_file
    except Exception as e:
        return {}, "exa_file 导入失败: %s" % e
    api_key, sid = env("EXAROTON_API_KEY"), env("EXAROTON_SERVER_ID")
    if not api_key or not sid:
        return {}, "缺少 EXAROTON_API_KEY / EXAROTON_SERVER_ID"
    snap, fails = {}, []
    for cloud, flat in CORE_MAP.items():
        try:
            snap[flat] = get_file(cloud, api_key, sid).splitlines()
        except Exception as e:
            fails.append(f"{cloud}({type(e).__name__})")
        time.sleep(0.4)
    for f in CORE:
        try:
            snap[f] = get_file(f, api_key, sid).splitlines()
        except Exception as e:
            fails.append(f"{f}({type(e).__name__})")
        time.sleep(0.4)
    for rel in plugin_cfgs:
        try:
            snap[f"plugins/{rel}"] = get_file(f"plugins/{rel}", api_key, sid).splitlines()
        except Exception:
            pass
        time.sleep(0.15)
    return snap, ("；".join(fails) if fails else "")


# ---------------- 落盘（latest 覆盖 + 快照滚动 3 份） ----------------
LATEST_NAME = "config-audit-latest.md"
# 落盘前必做的密钥脱敏：差异表会把「值」原样打出来，secret/api_key/app_secret 这类必须盖掉
SECRET_KEY_RX = re.compile(r"secret|api[_-]?key|token|passw|app[_-]?id", re.I)
DIFF_ITEM_RX = re.compile(r"`([^`]+)`[^`；|｜]*(?:→[^`；|｜]*)?")


def mask_secrets(text):
    """把差异表里密钥类 key 的值替换成 <已脱敏>（只动值，不动 key 名/差异条数）"""
    def fix_line(line):
        def sub(m):
            if SECRET_KEY_RX.search(m.group(1)):
                return "`%s` <已脱敏>" % m.group(1)
            return m.group(0)
        return DIFF_ITEM_RX.sub(sub, line)
    return "\n".join(fix_line(l) for l in text.split("\n"))
SNAPSHOT_RX = re.compile(r"^config-audit-\d{8}-\d{4}\.md$")
KEEP_SNAPSHOTS = 3


def save_rolling(text):
    """落盘策略（老板定，与 orzmc_selfcheck 同口径）：

      * `config-audit-latest.md` —— 每次运行**无条件覆盖**，latest 永远是最新一次结论；
      * `config-audit-<yyyyMMdd-HHmm>.md` —— 配置审查每次都有差异，所以每次也写快照，
        但按文件名时间戳排序**只保留最近 3 份**，第 4 份起删最旧的；
      * 两个落点都做：E:/orzmc/reports/ + deliver_dir()（S: 不可见时降级本机 deliver，不报错）。

    返回 (写入路径列表, 说明列表)。
    """
    clean = redact(text) if redact else text
    clean = mask_secrets(clean)
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    snap_name = "config-audit-%s.md" % stamp
    written, notes = [], []

    dirs = [("reports", reports_dir())]
    d, note = deliver_dir()
    notes.append("交付目录：%s（%s）" % (d, note))
    if d.resolve() != dirs[0][1].resolve():
        dirs.append(("交付", d))

    for tag, d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            latest = d / LATEST_NAME
            latest.write_text(clean, encoding="utf-8")
            written.append(str(latest))
            snap = d / snap_name
            snap.write_text(clean, encoding="utf-8")
            written.append(str(snap))
            # 滚动：文件名 yyyyMMdd-HHmm 字典序 = 时间序，降序保留前 3 份
            snaps = sorted((p for p in d.glob("config-audit-*.md")
                            if SNAPSHOT_RX.match(p.name)),
                           key=lambda p: p.name, reverse=True)
            removed = []
            for old in snaps[KEEP_SNAPSHOTS:]:
                try:
                    old.unlink()
                    removed.append(old.name)
                except OSError as e:
                    notes.append("%s 滚动删除失败 %s: %s" % (tag, old.name, e))
            notes.append("%s：latest 已覆盖；快照 %d 份（上限 %d）%s"
                         % (tag, min(len(snaps), KEEP_SNAPSHOTS), KEEP_SNAPSHOTS,
                            ("；滚动删除 " + ", ".join(removed)) if removed else ""))
        except Exception as e:
            notes.append("%s 落盘失败（已忽略）: %s: %s" % (tag, type(e).__name__, e))
    return written, notes


# ---------------- 报告 ----------------
def build_report(base, cmp_snap, inst, mode, exa_fail, started):
    lines = []
    add = lines.append
    add("# 两端配置审查报告（Windows 本机巡检端）")
    add("")
    add(f"> 生成时间：{started}｜巡检端 = **Windows Hermes（本机直读，无 SSH / 无面板 API）**")
    add(f"> 基准端：`{inst}`｜生效 Geyser 配置：{'代理侧 Geyser-Velocity（proxy 模式）' if mode == 'proxy' else '实例内副本（direct 模式）'}")
    add(f"> 对比端：Exaroton（平台 API）{('｜⚠️ 部分拉取失败：' + exa_fail) if exa_fail else ''}")
    add("")
    core_names = list(CORE_MAP.values()) + CORE
    add("## 一、核心配置")
    add("")
    add("| 文件 | 状态 | 差异要点 |")
    add("|:--|:--|:--|")
    core_diff = 0
    for name in core_names:
        bl = base.get(name)
        if bl is None:
            add(f"| `{name}` | ℹ️ 基准端缺失 | — |")
            continue
        cl = cmp_snap.get(name)
        if cl is None:
            add(f"| `{name}` | ❌ 对比端缺失 | Exa 侧未取到 |")
            core_diff += 1
            continue
        diffs, side = diff_pair(bl, cl, eq_style=(name in EQ_STYLE))
        if not diffs:
            add(f"| `{name}` | ✅ 一致 | — |")
        else:
            core_diff += 1
            head = "；".join(f"`{k.replace('|', '@')}` {vb}→{vc}" for k, vb, vc in diffs[:4])
            more = f"（另 {len(diffs) - 4} 处）" if len(diffs) > 4 else ""
            add(f"| `{name}` | ❌ {len(diffs)} 处差异 | {head}{more}{('｜单端独有 key %d' % side) if side else ''} |")
    add("")
    add("## 二、插件配置")
    add("")
    add("| 插件配置 | 状态 | 差异要点 |")
    add("|:--|:--|:--|")
    plug_total = plug_diff = 0
    for rel in sorted(k for k in base if k.startswith("plugins/")):
        plug_total += 1
        bl = base[rel]
        cl = cmp_snap.get(rel)
        short = rel[len("plugins/"):]
        if cl is None:
            add(f"| `{short}` | ❌ 对比端缺失 | Exa 无此文件 |")
            plug_diff += 1
            continue
        diffs, side = diff_pair(bl, cl)
        if not diffs:
            continue
        plug_diff += 1
        head = "；".join(f"`{k.replace('|', '@')}` {vb}→{vc}" for k, vb, vc in diffs[:3])
        add(f"| `{short}` | ❌ {len(diffs)} 处差异 | {head}{('（单端独有 key %d）' % side) if side else ''} |")
    add("")
    add("## 三、汇总")
    add("")
    add("| 维度 | 数值 |")
    add("|:--|:--|")
    add(f"| 核心配置 | {len(core_names)} 件，差异 {core_diff} |")
    add(f"| 插件配置 | {plug_total} 件，差异 {plug_diff} |")
    add(f"| 数据源 | 基准端{'完整' if base else '缺失'}｜对比端 {len(cmp_snap)} 件 |")
    add("")
    add("> ⚠️ 已知刻意差异（非漂移）：`config_paper-global.yml` 的 Velocity 转发段（仅测试服有代理）、"
        "`server.properties` 定位/通道项、OrzMC `im.yml` 双通道与 `default_lang`、GrimAC 生产端不部署、"
        "EaglercraftX* 仅测试服。")
    return "\n".join(lines) + "\n", core_diff, plug_diff, plug_total


def main():
    local_only = "--local" in sys.argv
    no_save = "--no-save" in sys.argv
    started = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    base, inst, mode = local_snapshot()
    if not base:
        print(f"❌ 基准端数据不可用：{mode}")
        print("STATUS_LINE: ❌ FAIL(基准端 0 文件)")
        return 1
    plugin_cfgs = [k[len("plugins/"):] for k in base if k.startswith("plugins/")]
    exa, exa_fail = ({}, "跳过（--local）") if local_only else exa_snapshot(plugin_cfgs)

    report, core_diff, plug_diff, plug_total = build_report(base, exa, inst, mode, exa_fail, started)
    status = "✅ SUCCESS"
    if not local_only and len(exa) < 5:
        status = "❌ FAIL(Exa 拉取异常: %d 件)" % len(exa)

    paths, save_notes = [], []
    if not no_save:
        paths, save_notes = save_rolling(report)

    print("=== OrzMC 配置审查（Windows 本机）%s ===" % started)
    print("实例目录: %s" % inst)
    print("入口模式: %s（Geyser 生效配置来源 = %s）"
          % (mode, "代理侧 Geyser-Velocity" if mode == "proxy" else "实例内 Geyser-Spigot"))
    print("基准端: %d 件配置（核心 %d + 插件 %d）" % (len(base), len([k for k in base if not k.startswith('plugins/')]), plug_total))
    print("对比端: Exaroton %d 件%s" % (len(exa), ("｜拉取失败: " + exa_fail) if exa_fail else ""))
    print("差异: 核心 %d 件 / 插件 %d 件" % (core_diff, plug_diff))
    for p in paths:
        print("报告: %s" % p)
    for n in save_notes:
        print("落盘: %s" % n)
    print("STATUS: %s" % status)
    print("STATUS_LINE: %s" % status)
    return 0 if status.startswith("✅") else 1


if __name__ == "__main__":
    sys.exit(main())
