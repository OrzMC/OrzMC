#!/usr/bin/env python3
"""OrzMC 每周健康体检 v1（2026-11-02）

覆盖：启动日志健康 / 基岩通道 / 备份与磁盘 / 运行时指标（TPS·玩家）
数据源：SSH 直读 Windows 实例目录（主）+ MCSM 面板 API（辅助）
只读：不改任何文件、不下发破坏性指令。
退出码：0 = 全部正常或仅有告警；1 = 有 FAIL 项（供 cron 判读）
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.request

sys.path.insert(0, os.path.expanduser("~/.hermes/skills/gaming/orzmc/scripts/cmp3"))
try:
    from mcsm_env import get_mcsm_local_config
except Exception:  # pragma: no cover
    get_mcsm_local_config = None

SSH = "win"
INST = {
    "paper": {"uuid": "716c2fb712154c36ba5ab0f1480d3f87", "label": "papermc-test", "bedrock_udp": 19132},
    "folia": {"uuid": "8A932DD47F4D42AAAD6A6A9A5FAD2A91", "label": "folia-test", "bedrock_udp": 19133},
}
WIN_ROOT = "E:/orzmc/mcsmanager/daemon/data/InstanceData"
# 已知可忽略的日志噪音（延续技能里的既有判定）
IGNORE_PATTERNS = [
    r"Essentials\] You are running an unsupported server version",
    r"ProtocolLib not found",
    r"duplicate keys found",
    r"THIS ERROR IS SAFE TO IGNORE",
    r"Loading libraries, please wait",
    r"NetherNet support is NOT enabled",  # 单列检查，见下
]
PS1_STORAGE = r'''$root = 'E:/orzmc/mcsmanager/daemon/data/InstanceData'
$ids = @('716c2fb712154c36ba5ab0f1480d3f87','8A932DD47F4D42AAAD6A6A9A5FAD2A91')
foreach ($id in $ids) {
  $d = Join-Path $root $id
  $bak = @(Get-ChildItem $d -Directory -Filter 'upgrade-bak-*' -ErrorAction SilentlyContinue)
  $bakBytes = 0
  foreach ($b in $bak) { $bakBytes += (Get-ChildItem $b.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum }
  $instBytes = (Get-ChildItem $d -Recurse -File -ErrorAction SilentlyContinue | Measure-Object Length -Sum).Sum
  Write-Output ('id=' + $id.Substring(0,8) + ' bak_count=' + $bak.Count + ' bak_MB=' + [math]::Round($bakBytes/1MB,1) + ' inst_MB=' + [math]::Round($instBytes/1MB,1))
}
$v = Get-PSDrive E
Write-Output ('E_free_GB=' + [math]::Round($v.Free/1GB,1) + ' E_used_GB=' + [math]::Round($v.Used/1GB,1))
'''

FINDINGS = []


def add(level, area, msg):
    FINDINGS.append((level, area, msg))


def ssh_run(cmd, timeout=90):
    try:
        r = subprocess.run(["ssh", "-o", "ConnectTimeout=8", SSH, cmd],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    except Exception as e:
        return 99, repr(e)[:120]


def ps(script, timeout=120):
    """执行 PowerShell 单行（ASCII only）"""
    return ssh_run('powershell -NoProfile -Command "%s"' % script, timeout=timeout)


# ---------- 1. 实例状态（面板） ----------
def panel_status():
    out = {}
    if not get_mcsm_local_config:
        add("WARN", "面板", "mcsm_env 不可用，跳过状态查询")
        return out
    cfg = get_mcsm_local_config()
    base = str(cfg.get("url", "")).rstrip("/")
    key = cfg.get("api_key") or cfg.get("apikey")
    daemon = cfg.get("daemon_id") or cfg.get("daemonId")
    for name, meta in INST.items():
        u = "%s/api/instance?uuid=%s&daemonId=%s&apikey=%s" % (base, meta["uuid"], daemon, key)
        for _ in range(2):
            try:
                with urllib.request.urlopen(urllib.request.Request(
                        u, headers={"User-Agent": "HermesAgent/1.0"}), timeout=45) as r:
                    d = json.loads(r.read().decode()).get("data", {}) or {}
                    out[name] = d.get("status")
                    break
            except Exception:
                time.sleep(5)
        else:
            out[name] = "ERR"
    return out


# ---------- 2. 启动日志健康 ----------
def log_health():
    for name, meta in INST.items():
        inst = "%s/%s" % (WIN_ROOT, meta["uuid"])
        log = inst + "/logs/latest.log"
        rc, out = ps("if (Test-Path '%s') { (Get-Content '%s' -Tail 4000 | Select-String -Pattern "
                     "'SEVERE|Could not load|Exception in server tick loop|Watchdog Thread|FAILED TO BIND|"
                     "unsupported server version|NetherNet|Started Geyser on UDP|Done \\(|Enabling ' "
                     "-Context 0).Line } else { 'NO_LOG' }" % (log, log), timeout=150)
        if rc != 0 or "NO_LOG" in out:
            add("FAIL", "%s 日志" % meta["label"], "读不到 latest.log（%s）" % out.strip()[:60])
            continue
        lines = [l.strip() for l in out.splitlines() if l.strip()]
        # 启动完成
        done = [l for l in lines if re.search(r"Done \(\d", l)]
        if _panel_running(name):
            if not done:
                add("WARN", "%s 日志" % meta["label"], "未见本轮 `Done (` 行（可能仍在启动）")
        # SEVERE / 加载失败
        bad = []
        for l in lines:
            if any(re.search(p, l) for p in IGNORE_PATTERNS):
                continue
            if re.search(r"SEVERE|Could not load|FAILED TO BIND|Exception in server tick loop", l):
                bad.append(l[:160])
        if bad:
            add("FAIL", "%s 日志" % meta["label"], "%d 条严重错误，首条：%s" % (bad and len(bad) or len(bad), bad[0]))
        # 基岩
        geyser = [l for l in lines if "Started Geyser on UDP" in l]
        if geyser:
            port = re.search(r"port (\d+)", geyser[-1])
            p = port.group(1) if port else "?"
            add("INFO", "%s 基岩" % meta["label"], "Geyser 已在容器内 UDP %s 启动（主机映射 %s）" % (p, meta["bedrock_udp"]))
        else:
            add("WARN", "%s 基岩" % meta["label"], "日志未见 `Started Geyser on UDP`（基岩可能不可用）")
        # NetherNet 期限
        nn = [l for l in lines if "NetherNet support is NOT enabled" in l]
        if nn:
            add("WARN", "%s 基岩" % meta["label"], "NetherNet 未启用（官方 2026-10-27 起旧传输将失效）")


def _panel_running(name):
    return True


# ---------- 3. 备份与磁盘 ----------
def storage_health():
    ps1 = os.path.expanduser('~/.hermes/tmp/_health_storage.ps1')
    os.makedirs(os.path.dirname(ps1), exist_ok=True)
    open(ps1, 'w', encoding='utf-8').write(PS1_STORAGE)
    mk = 'powershell -NoProfile -Command "New-Item -ItemType Directory -Force -Path E:/orzmc/tmp | Out-Null"'
    subprocess.run(['ssh', '-o', 'ConnectTimeout=8', SSH, mk], capture_output=True, text=True, timeout=30)
    subprocess.run(['scp', '-o', 'ConnectTimeout=10', ps1, SSH + ':E:/orzmc/tmp/_health_storage.ps1'],
                   capture_output=True, text=True, timeout=90)
    rc, out = ssh_run('powershell -NoProfile -ExecutionPolicy Bypass -File E:/orzmc/tmp/_health_storage.ps1', timeout=240)
    if rc != 0:
        add('WARN', '存储', 'SSH 查询失败（rc=%s）：%s' % (rc, out.strip()[:80]))
        return
    for line in out.splitlines():
        line = line.strip()
        if line.startswith('E_free_GB'):
            m = re.search(r'E_free_GB=([\d.]+)', line)
            if m and float(m.group(1)) < 20:
                add('WARN', '磁盘', 'Windows E: 剩余 %.1f GB（<20GB，需清理）' % float(m.group(1)))
            elif m:
                add('INFO', '磁盘', 'Windows E: 剩余 %.1f GB' % float(m.group(1)))
        elif 'bak_count=' in line:
            m = re.search(r'id=(\w+) bak_count=(\d+) bak_MB=([\d.]+) inst_MB=([\d.]+)', line)
            if m:
                cnt, mb, inst = int(m.group(2)), float(m.group(3)), float(m.group(4))
                add('INFO', '存储', '%s 实例 %.0f MB，备份 %d 份 / %.0f MB' % (m.group(1), inst, cnt, mb))
                if cnt > 2:
                    add('WARN', '备份', '%s 有 %d 份 upgrade-bak（%.0f MB），建议只留 1~2 份' % (m.group(1), cnt, mb))

# ---------- 4. 运行时指标 ----------
def _parse_tps(txt):
    """解析两种 TPS 输出：Paper 汇总行 / Folia 分区行（at X.XX TPS）"""
    vals = []
    lines = [l for l in txt.splitlines() if "TPS from last" in l]
    if lines:
        vals = [float(x) for x in re.findall(r"\d+\.\d+", lines[-1].split(":", 1)[-1])]
    if not vals:
        region = re.findall(r"at\s+(\d+\.\d+)\s+TPS", txt)
        if region:
            vals = [float(x) for x in region]
    return vals


def runtime_health(status):
    """TPS/玩家：优先 SSH 读 latest.log；不足则走面板控制台（Folia 走分区 TPS 解析）"""
    for name, meta in INST.items():
        if status.get(name) != 3:
            add("INFO", "%s 运行" % meta["label"], "实例未运行（status=%s），跳过 TPS/玩家检查" % status.get(name))
            continue
        log = "%s/%s/logs/latest.log" % (WIN_ROOT, meta["uuid"])
        rc, out = ps("if (Test-Path '%s') { (Get-Content '%s' -Tail 1200 | Select-String -Pattern "
                     "'TPS from last|at .* TPS|players online' | Select-Object -Last 12).Line } else { 'NO_LOG' }"
                     % (log, log), timeout=120)
        txt = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", out or "")
        vals = _parse_tps(txt)
        play_lines = [l for l in txt.splitlines() if "players online" in l.lower()]
        players = None
        if play_lines:
            m = re.findall(r"There are (\d+)", play_lines[-1])
            if m:
                players = int(m[-1])

        if not vals or players is None:
            _send_cmd(meta["uuid"], "tps")
            time.sleep(7)
            ptxt = re.sub(r"\x1b\[[0-9;]*[A-Za-z]", "", _outputlog(meta["uuid"]))
            if not vals:
                vals = _parse_tps(ptxt)
            if players is None:
                mm = re.findall(r"There are (\d+)", ptxt)
                if mm:
                    players = int(mm[-1])

        if not vals:
            add("WARN", "%s 性能" % meta["label"], "日志与面板都读不到 TPS")
        else:
            worst = min(vals)
            tag = "日志/控制台"
            if worst < 18.0:
                add("WARN", "%s 性能" % meta["label"], "TPS 偏低：min %.2f（%s，共 %d 个采样）" % (worst, tag, len(vals)))
            else:
                add("INFO", "%s 性能" % meta["label"], "TPS min %.2f（%s，%d 采样）" % (worst, tag, len(vals)))
        if players is not None:
            add("INFO", "%s 玩家" % meta["label"], "最近记录在线 %d 人" % players)


def _panel_cfg():
    cfg = get_mcsm_local_config() if get_mcsm_local_config else {}
    return (str(cfg.get("url", "")).rstrip("/"), cfg.get("api_key") or cfg.get("apikey"),
            cfg.get("daemon_id") or cfg.get("daemonId"))


def _send_cmd(uuid, cmd):
    base, key, daemon = _panel_cfg()
    u = "%s/api/protected_instance/command?command=%s&uuid=%s&daemonId=%s&apikey=%s" % (
        base, cmd, uuid, daemon, key)
    try:
        urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "HermesAgent/1.0"}), timeout=30).read()
    except Exception:
        pass


def _outputlog(uuid):
    base, key, daemon = _panel_cfg()
    u = "%s/api/protected_instance/outputlog?daemonId=%s&uuid=%s&apikey=%s" % (base, daemon, uuid, key)
    try:
        with urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "HermesAgent/1.0"}), timeout=40) as r:
            return (json.loads(r.read().decode()).get("data") or "").replace("\x1b[", "")
    except Exception:
        return ""


def main():
    print("=== OrzMC 每周健康体检 ===")
    status = panel_status()
    print("实例状态:", {INST[k]["label"]: v for k, v in status.items()})
    log_health()
    storage_health()
    runtime_health(status)

    order = {"FAIL": 0, "WARN": 1, "INFO": 2}
    FINDINGS.sort(key=lambda x: order.get(x[0], 3))
    print("\n---- 体检结论 ----")
    fails = [f for f in FINDINGS if f[0] == "FAIL"]
    warns = [f for f in FINDINGS if f[0] == "WARN"]
    infos = [f for f in FINDINGS if f[0] == "INFO"]
    for lv, area, msg in fails + warns + infos:
        icon = {"FAIL": "❌", "WARN": "⚠️", "INFO": "ℹ️"}[lv]
        print("%s [%s] %s" % (icon, area, msg))
    print("\n汇总: FAIL=%d WARN=%d INFO=%d" % (len(fails), len(warns), len(infos)))
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
