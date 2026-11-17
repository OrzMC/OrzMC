#!/usr/bin/env python3
"""OrzMC 本机测试服周巡检（no_agent，每周一 09:15 出报告）。

覆盖（精简版，替代 Mac 端那套已失效的五连检）：
  1. 容器/进程存活        2. 三通道连通性（Java / NetherNet / 网页）
  3. 后端 TPS 与人数      4. advertise 与真实公网 IP 是否一致
  5. 核心与插件版本 diff   6. 近 7 天 ERROR/WARN 统计 + Top 错误
  7. 磁盘/世界体积/备份新鲜度
最后给出「需要动手」清单；没有可动手项就一行说明。

只读：不改配置、不重启任何东西。
"""
from __future__ import annotations
try:  # Windows console/pipe defaults to cp936: lock UTF-8 or emoji print raises
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import glob
import gzip
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.request

HERMES = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes")
SCRIPTS = os.path.join(HERMES, "scripts")
DATA_ROOT = "E:/orzmc"
INST = f"{DATA_ROOT}/mcsmanager/daemon/data/InstanceData"
PROXY = f"{DATA_ROOT}/eagler/proxy"
INSTANCES = [
    ("paper", "716c2fb712154c36ba5ab0f1480d3f87", 25575),
    ("folia", "8A932DD47F4D42AAAD6A6A9A5FAD2A91", 25576),
]
UA = {"User-Agent": "orzmc-patrol/1.0 (hermes cron)"}
sys.path.insert(0, SCRIPTS)
import orzmc_entry_probe as probe  # noqa: E402


def sh(cmd: list[str], timeout: int = 60) -> str:
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (r.stdout or r.stderr).strip()
    except Exception as exc:  # noqa: BLE001
        return f"失败: {exc}"


def get_json(url: str, timeout: float = 15.0):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def strip_ansi(t: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", t)


def tail_lines(path: str, n: int = 4000) -> list[str]:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            return strip_ansi(f.read()).splitlines()[-n:]
    except OSError:
        return []


def dir_size(path: str) -> int:
    total = 0
    for root, _dirs, files in os.walk(path):
        for f in files:
            try:
                total += os.path.getsize(os.path.join(root, f))
            except OSError:
                pass
    return total


def human(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024 or unit == "TB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


# ---------------------------------------------------------------- sections
def sec_containers() -> tuple[str, list[str]]:
    raw = sh(["docker", "ps", "--format", "{{.Names}}|{{.Status}}|{{.Ports}}"])
    rows, todos = [], []
    for line in raw.splitlines():
        parts = line.split("|")
        if not parts or not parts[0]:
            continue
        name = parts[0]
        if not (name.startswith("orzmc-") or name.startswith("MCSM-")):
            continue
        status = parts[1] if len(parts) > 1 else ""
        raw_ports = (parts[2] if len(parts) > 2 else "").replace("0.0.0.0:", "").replace("[::]:", "")
        seen: list[str] = []
        for item in raw_ports.split(", "):
            if item and item not in seen:
                seen.append(item)
        ports = ", ".join(seen)
        rows.append(f"| `{name}` | {status} | {ports[:70]} |")
        if "unhealthy" in status:
            todos.append(f"`{name}` 状态 unhealthy")
    missing = {"orzmc-velocity", "orzmc-caddy", "MCSM-716c2f", "MCSM-8A932D"} - {
        r.split("`")[1] for r in rows if r.startswith("| `")
    }
    for m in sorted(missing):
        todos.append(f"容器 `{m}` 没在运行")
    out = ["### 1. 容器", "", "| 容器 | 状态 | 端口 |", "|:--|:--|:--|"] + rows
    return "\n".join(out), todos


def sec_connectivity() -> tuple[str, list[str]]:
    items, todos = [], []
    ok, d = probe.java_status()
    items.append(f"- Java 25565：{'✅' if ok else '🔴'} {d}")
    if not ok:
        todos.append("Java 入口不可用")
    ok2, d2 = probe.nethernet()
    items.append(f"- NetherNet 信令：{'✅' if ok2 else '🔴'} {d2}")
    if not ok2:
        todos.append("基岩 NetherNet 信令不可用")
    ok3, d3 = probe.web_entry()
    items.append(f"- 网页入口 18443：{'✅' if ok3 else '🔴'} {d3}")
    if not ok3:
        todos.append("网页客户端入口不可用")
    items.append("- RakNet：ℹ️ `transport: nethernet` 单端口模式本就不应答，不作判据")
    return "### 2. 连通性\n\n" + "\n".join(items), todos


def sec_backend() -> tuple[str, list[str]]:
    lines, todos = [], []
    for label, uuid, port in INSTANCES:
        ok, body = probe.rcon(port, probe.rcon_password(uuid), "list")
        ok2, tps = probe.rcon(port, probe.rcon_password(uuid), "tps")
        if not ok:
            lines.append(f"- {label}：🔴 RCON 不通（{body}）")
            todos.append(f"{label} RCON 不通（实例可能没起）")
            continue
        tps_v = None
        m = re.search(r"Lowest Region TPS:\s*([\d.]+)", tps or "")
        if m:
            tps_v = float(m.group(1))
        else:
            m = re.search(r"TPS from last[^:]*:\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)", tps or "")
            if m:
                tps_v = min(float(x) for x in m.groups())
        if tps_v is not None and tps_v < 18:
            todos.append(f"{label} TPS 偏低（{tps_v}）")
        shown_tps = f"{tps_v}" if tps_v is not None else "未取到"
        lines.append(f"- {label}：{(body or '').splitlines()[0][:70]} ｜ TPS **{shown_tps}**")
    return "### 3. 后端\n\n" + "\n".join(lines), todos


def sec_advertise() -> tuple[str, list[str], str]:
    r = sh([sys.executable, os.path.join(SCRIPTS, "nethernet_advertise_sync.py"), "--dry", "-v"], timeout=60)
    ok = "已是最新" in r
    lines = [f"- 结论：{'✅ 与公网 IP 一致' if ok else '🔴 与真实公网 IP 不一致（等无人在线会自动修）'}"]
    for ln in r.splitlines()[-4:]:
        lines.append(f"  - `{ln.strip()}`")
    return "### 4. NetherNet advertise\n\n" + "\n".join(lines), ([] if ok else ["advertise 与公网 IP 不一致"]), r


def head_text(path: str, n: int = 40) -> str:
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= n:
                    break
                lines.append(line)
    except OSError:
        return ""
    return strip_ansi("".join(lines))


def installed_versions() -> dict[str, str]:
    # 已安装版本以实例目录里的 jar 文件名为准（决定下次启动加载什么）。
    # 曾优先读 logs/latest.log 的 "Loading Paper 26.3-246@"：实例停着没重启时日志永远停在旧版
    # → 报出「Paper 落后 7 个 build」，而磁盘上装的是 26.3-253（假告警）。日志只作兜底，
    # 并记进 _ran，两者不一致时 sec_versions 明说「上次运行 X，重启后生效」。
    v: dict[str, str] = {}
    ran: dict[str, str] = {}
    for label, uuid, _ in INSTANCES:
        jarver = ""
        for jar in glob.glob(f"{INST}/{uuid}/*.jar"):
            mm = re.match(r"(?:paper|folia)[-_]?(\d+\.\d+-\d+)\.jar$",
                          os.path.basename(jar), re.I)
            if mm:
                jarver = mm.group(1)
                break
        t = head_text(f"{INST}/{uuid}/logs/latest.log")
        m = re.search(r"Loading (Paper|Folia) (\S+?)@", t)
        if m:
            ran[label] = m.group(2)
        if jarver:
            v[label] = jarver
        elif m:
            v[label] = m.group(2)
    if ran:
        v["_ran"] = ran
    pt = "\n".join(tail_lines(f"{PROXY}/logs/latest.log", 300))
    m = re.search(r"Booting up Velocity (\S+?)\.\.\.", pt)
    if m:
        v["velocity"] = m.group(1)
    m = re.search(r"Loading Geyser version (\S+)", pt)
    if m:
        v["geyser"] = m.group(1)
    m = re.search(r"Loading EaglercraftXServer (\S+)\.\.\.", pt)
    if m:
        v["eagler"] = m.group(1)
    return v


def fill_latest(project: str, version: str) -> str:
    try:
        data = get_json(f"https://fill.papermc.io/v3/projects/{project}/versions/{version}/builds")
        builds = data if isinstance(data, list) else data.get("builds", [])
        stable = [b for b in builds if str(b.get("channel", "")).upper() == "STABLE"] or builds
        if not stable:
            return "?"
        return str(max(int(b["id"]) for b in stable))
    except Exception as exc:  # noqa: BLE001
        return f"查询失败({type(exc).__name__})"


def sec_versions() -> tuple[str, list[str]]:
    inst = installed_versions()
    lines, todos = [], []
    for core in ("paper", "folia"):
        if core not in inst:
            continue
        cur = inst[core]
        m = re.match(r"(\d+\.\d+)-(\d+)", cur)
        base, build = (m.group(1), int(m.group(2))) if m else (cur, None)
        latest = fill_latest(core, base)
        behind = None
        try:
            behind = int(latest) - build if build is not None else None
        except (TypeError, ValueError):
            pass
        suffix = f"（落后 {behind}）" if behind and behind > 0 else ""
        shown = f"{base}-{build}" if build is not None else cur
        ran = (inst.get("_ran") or {}).get(core)
        note = f"（上次运行 {ran}，重启后才生效）" if ran and ran != cur else ""
        lines.append(f"- {core.capitalize()} **{shown}** → 最新 STABLE build `{latest}`{suffix}{note}")
        if behind and behind > 0:
            todos.append(f"{core.capitalize()} 落后 {behind} 个 build（{shown} → build {latest}）")
    if "velocity" in inst:
        lines.append(f"- Velocity **{inst['velocity']}**")
    if "geyser" in inst:
        try:
            mv = get_json('https://api.modrinth.com/v2/project/geyser/version?loaders=%5B%22velocity%22%5D')
            newest = mv[0]["version_number"]
            lines.append(f"- Geyser **{inst['geyser']}** → Modrinth 最新 `{newest}`")
            if newest.split("-")[-1] != inst["geyser"].split("-")[-1]:
                todos.append(f"Geyser 有新版（{inst['geyser']} → {newest}）")
        except Exception as exc:  # noqa: BLE001
            lines.append(f"- Geyser **{inst['geyser']}**（Modrinth 查询失败 {type(exc).__name__}）")
    if "eagler" in inst:
        lines.append(f"- EaglercraftXServer **{inst['eagler']}**")
    lines.append("- 注：插件级 diff（ViaVersion/LuckPerms 等）未纳入，需要时单独跑升级评估")
    return "### 5. 版本\n\n" + "\n".join(lines), todos


def sec_logs() -> tuple[str, list[str]]:
    cutoff = time.time() - 7 * 86400
    total_err = total_warn = 0
    top: dict[str, int] = {}
    for label, uuid, _ in INSTANCES:
        for path in glob.glob(f"{INST}/{uuid}/logs/*.log*"):
            try:
                if os.path.getmtime(path) < cutoff:
                    continue
                if path.endswith(".gz"):
                    with gzip.open(path, "rt", encoding="utf-8", errors="replace") as f:
                        text = f.read()
                else:
                    text = open(path, encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for ln in strip_ansi(text).splitlines():
                if " ERROR " in ln or "FATAL" in ln:
                    total_err += 1
                    key = re.sub(r"^\[[^\]]*\]\s*", "", ln)
                    key = re.sub(r"\d+", "N", key)[:110]
                    top[key] = top.get(key, 0) + 1
                elif " WARN " in ln:
                    total_warn += 1
    lines = [f"- 两实例近 7 天：**ERROR {total_err}** 条 / WARN {total_warn} 条"]
    if top:
        for k, c in sorted(top.items(), key=lambda x: -x[1])[:5]:
            lines.append(f"  - ×{c} `{k}`")
    todos = []
    if total_err > 200:
        todos.append(f"近 7 天 ERROR {total_err} 条，需要看日志")
    return "### 6. 日志健康\n\n" + "\n".join(lines), todos


def sec_disk() -> tuple[str, list[str]]:
    lines, todos = [], []
    for drive in ("C:/", "E:/"):
        try:
            u = shutil.disk_usage(drive)
            pct = u.free / u.total * 100
            lines.append(f"- {drive[0]}: 剩余 **{human(u.free)} / {human(u.total)}**（{pct:.0f}%）")
            if drive.startswith("C") and pct < 15:
                todos.append(f"C 盘剩余仅 {pct:.0f}%，建议清理")
        except OSError as exc:
            lines.append(f"- {drive}: 读不到（{exc}）")
    for label, uuid, _ in INSTANCES:
        w = f"{INST}/{uuid}/world"
        if os.path.isdir(w):
            lines.append(f"- {label} world：{human(dir_size(w))}")
    bk = f"{DATA_ROOT}/backup"
    if os.path.isdir(bk):
        try:
            newest = max((os.path.getmtime(os.path.join(bk, x)) for x in os.listdir(bk)), default=0)
            age = (time.time() - newest) / 86400
            lines.append(f"- 最近备份：{time.strftime('%Y-%m-%d %H:%M', time.localtime(newest))}（{age:.1f} 天前）")
            if age > 10:
                todos.append(f"备份已 {age:.0f} 天没更新")
        except OSError:
            pass
    df = sh(["docker", "system", "df", "--format", "{{.Type}} {{.Size}} {{.Reclaimable}}"], timeout=60)
    if df and "失败" not in df:
        lines.append("- docker：\n" + "\n".join(f"  - `{x}`" for x in df.splitlines()[:5]))
    return "### 7. 磁盘与备份\n\n" + "\n".join(lines), todos


def main() -> int:
    t0 = time.time()
    out = [f"# OrzMC 本机测试服周巡检 · {time.strftime('%Y-%m-%d %H:%M')}", ""]
    todos: list[str] = []
    for fn in (sec_containers, sec_connectivity, sec_backend, sec_advertise, sec_versions, sec_logs, sec_disk):
        try:
            res = fn()
            block, td = res[0], res[1]
            out += [block, ""]
            todos += td
        except Exception as exc:  # noqa: BLE001
            out += [f"### {fn.__name__} 采集失败：{type(exc).__name__}: {exc}", ""]
            todos.append(f"{fn.__name__} 采集失败")

    out.append("## 需要动手")
    out.append("")
    if todos:
        out += [f"- {x}" for x in todos]
    else:
        out.append("没有需要动的事，一切正常。")
    out.append("")
    out.append(f"_耗时 {time.time() - t0:.0f}s · 脚本 `%LOCALAPPDATA%\\hermes\\scripts\\orzmc_weekly_patrol.py`_")
    print("\n".join(out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
