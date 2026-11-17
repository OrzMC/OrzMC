#!/usr/bin/env python3
"""orzmc_selfcheck.py —— OrzMC 全栈自检（Windows 侧唯一 MC 运维执行端）

一句话：把「检查与确认」从人肉变成可重复的一行命令 + 一个每天 08:30 的 cron。

用法：
    <venv python> orzmc_selfcheck.py               # 人读明细；latest 总是刷新，告警时另落快照
    <venv python> orzmc_selfcheck.py --json        # 机器可读（stdout 只有 JSON）
    <venv python> orzmc_selfcheck.py --no-deliver  # 只打印，不写交付文件

退出码：有 ❌ → 1，否则 0（⚠️ 不影响退出码，便于日巡检不吵人；ℹ️ 既不计 ⚠️ 也不影响退出码）。

告警落地（交付策略，老板定）：
    * `orzmc-selfcheck-latest.md` —— 每次运行**无条件覆盖**。latest 永远是「最近一次真实结论」，
      不会停在旧的告警内容上（全绿后 latest 必须自证是全绿）。
    * `orzmc-selfcheck-<yyyyMMdd-HHmm>.md` —— 快照**只在有 ⚠️/❌ 时**才写（留痕用），
      滚动保留最近 3 份（第 4 份起删最旧的），避免报告无上限累积。

检查项（8 项，每项输出 ✅/⚠️/❌ + 名称 + 证据）：
    1 技能          SKILL.md version / 技能文件数 / skill_self_check.py 结论
    2 cron          job 数、名称、enabled、last_status、next_run；挑出异常项
    3 交付目录      deliver_dir() 命中级别 + 真写一个临时文件再删（非交互会话看不到 S: → ℹ️ 不计告警）
    4 实例状态      velocity/caddy/easybot 应 running；paper/folia 应 stopped
    5 入口端口      25565 / 19132 真连（实例停止时由代理监听）
    6 版本基线      实例 jar 文件名 vs SKILL.md 记的基线（只比对，不改动）
    7 工具链        jdk25 java / gradle / node / git（JAVA_HOME 全局配置状态读注册表真值）
    8 报告新鲜度    E:/orzmc/reports 最近 3 个文件；>8 天无新报告 = ⚠️

判定口径（老板定）：
    * **MCSM 面板 API 403 = API key 失效，已按老板决定不处理** → 本脚本不含任何面板 API 判定项，
      全部结论只走「本地直读（E:/orzmc 文件系统）+ 容器事实（docker ps / docker exec）」，
      面板相关只作为 ℹ️ 口径说明出现，不计告警、不影响退出码。
    * **JAVA_HOME 已在 Windows 用户级全局配置**（`E:\orzmc\tools\jdk25`，用户 Path 含 `%JAVA_HOME%\bin`）
      → 第 7 项按 ✅ 报，真值读注册表（进程 env 可能是设置之前起的、没继承）；已运行进程需重启才继承，
      脚本内仍显式注入给子进程更稳。

Windows 专项纪律（见 SKILL.md「Windows 宿主执行脚本的硬前提」）：
    * 先 import sys 再 UTF-8 guard —— 否则中文/emoji 在 cp936 控制台 UnicodeEncodeError
    * subprocess 一律 encoding="utf-8", errors="replace" —— 否则 cp936 解码炸中文
    * .bat / .exe 用绝对路径（.bat 还要经 cmd /c，CreateProcess 不能直接起 .bat）
    * 系统 python 是 0 字节 Store stub，本脚本只能用 venv python 跑
"""
import sys

try:  # 必须在其他 import 之前：Windows 控制台默认 cp936
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import argparse
import json
import locale
import os
import pathlib
import re
import shutil
import socket
import subprocess
import time
from datetime import datetime, timedelta

HERMES_HOME = pathlib.Path(os.environ.get("LOCALAPPDATA", os.path.expanduser("~/AppData/Local"))) / "hermes"
HERMES_EXE = HERMES_HOME / "bin" / "hermes.exe"
SKILL_DIR = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
REPORTS_DIR = pathlib.Path("E:/orzmc/reports")
INSTANCE_ROOT = pathlib.Path("E:/orzmc/mcsmanager/daemon/data/InstanceData")
PAPER_UUID = "716c2fb712154c36ba5ab0f1480d3f87"
FOLIA_UUID = "8A932DD47F4D42AAAD6A6A9A5FAD2A91"
JDK_JAVA = pathlib.Path("E:/orzmc/tools/jdk25/bin/java.exe")
GRADLE_BAT = pathlib.Path("E:/orzmc/tools/gradle/bin/gradle.bat")

EXPECT_RUNNING = ["orzmc-velocity", "orzmc-caddy", "orzmc-easybot"]
DAEMON_CONTAINER = "orzmc-mcsmanager-daemon"
ENTRY_PORTS = [(25565, "Java 入口"), (19132, "基岩入口")]

# 版本基线：与 SKILL.md「第八轮升级后基线（当前权威）」一致。只比对，绝不改动实例文件。
# (实例, 说明, 文件名正则, 期望版本)
BASELINE = [
    ("paper", "Paper 核心", r"^paper-(.+)\.jar$", "26.3-253"),
    ("paper", "Geyser-Spigot", r"^Geyser-Spigot-b?(.+)\.jar$", "1303"),
    ("folia", "Folia 核心", r"^folia-(.+)\.jar$", "26.3-8"),
    ("folia", "ExecutableEvents", r"^ExecutableEvents-(.+)\.jar$", "3.26.11.15"),
    ("folia", "SCore", r"^SCore-(.+)\.jar$", "5.26.11.15"),
]
INSTANCE_UUIDS = {"paper": PAPER_UUID, "folia": FOLIA_UUID}

REPORT_STALE_DAYS = 8
LEVEL_ICON = {"ok": "✅", "warn": "⚠️", "fail": "❌", "info": "ℹ️"}

# 已知版本串：落盘前脱敏公网 IP 时必须保护，否则 redact() 会把「5.26.11.15」当 IP 打成占位符
_PROTECT = set()

sys.path.insert(0, str(SCRIPTS_DIR))
try:
    from orzmc_paths import deliver_dir, redact  # noqa: E402
except Exception as _e:  # 辅助模块缺失不能让自检崩
    deliver_dir = None
    redact = None
    _PATHS_ERR = str(_e)
else:
    _PATHS_ERR = ""


# ---------------------------------------------------------------- 基础工具
_ANSI_RX = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07|\x1b[@-_]")


def strip_ansi(text):
    return _ANSI_RX.sub("", text or "")


def decode_bytes(raw):
    """子进程字节 → 文本（Windows 编码坑的正解）。

    坑：Windows 上子进程若没继承 PYTHONUTF8 / PYTHONIOENCODING，写管道用的是 locale 编码
    （本机 cp936），父进程按 UTF-8 硬解就成了 `���: PASS` —— 于是「事实 PASS」被判成 UNKNOWN。
    顺序：UTF-8 严格 → locale.getpreferredencoding(False) → mbcs / gb18030 → UTF-8 兜底替换。
    """
    if not raw:
        return ""
    cands = []
    for enc in ("utf-8", locale.getpreferredencoding(False), "mbcs", "gb18030"):
        if enc and enc.lower() not in [c.lower() for c in cands]:
            cands.append(enc)
    for enc in cands:
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", errors="replace")


def run(cmd, timeout=120, cwd=None, env=None):
    """跑命令，字节捕获后智能解码（见 decode_bytes）。返回 (rc, 合并输出)。启动失败返回 (None, msg)。"""
    try:
        p = subprocess.run(cmd, capture_output=True,
                           timeout=timeout, cwd=str(cwd) if cwd else None,
                           env=dict(os.environ, **env) if env else None)
        out = (decode_bytes(p.stdout or b"") + decode_bytes(p.stderr or b"")).strip()
        return p.returncode, out
    except FileNotFoundError:
        return None, "命令不存在: %s" % cmd[0]
    except subprocess.TimeoutExpired:
        return None, "超时(%ss): %s" % (timeout, " ".join(str(c) for c in cmd))
    except Exception as e:
        return None, "启动异常: %s" % e


def first_line(text, limit=200):
    for line in (text or "").splitlines():
        line = line.strip()
        if line:
            return line[:limit]
    return ""


def tcp_open(port, host="127.0.0.1", timeout=3.0):
    """真连一次（Docker Desktop 发布端口不进 Windows netstat，只能实连判定）"""
    s = socket.socket()
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        return True, "connected"
    except Exception as e:
        return False, type(e).__name__ + (": " + str(e) if str(e) else "")
    finally:
        try:
            s.close()
        except Exception:
            pass


def check(check_id, name, fn):
    """跑单项检查：任何异常都收敛成 ❌ 运行异常，绝不中断后续项"""
    t0 = time.time()
    try:
        item = fn()
    except Exception as e:
        item = {"level": "fail", "name": name,
                "evidence": ["%s 运行异常: %s: %s" % (check_id, type(e).__name__, e)]}
    item.setdefault("level", "fail")
    item.setdefault("evidence", [])
    item["id"] = check_id
    item["name"] = item.get("name") or name
    item["elapsed_ms"] = int((time.time() - t0) * 1000)
    return item


# ---------------------------------------------------------------- 1 技能
def chk_skill():
    ev = []
    level = "ok"
    skill_md = SKILL_DIR / "SKILL.md"
    if not skill_md.is_file():
        return {"level": "fail", "evidence": ["SKILL.md 不存在: %s" % skill_md]}
    txt = skill_md.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^version:\s*(\S+)", txt, re.M)
    ver = m.group(1) if m else "(缺 version)"
    files = [p for p in SKILL_DIR.rglob("*")
             if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"]
    refs = [p for p in files if p.parent.name == "references"]
    scripts = [p for p in files if p.parent.name == "scripts"]
    ev.append("SKILL.md version = %s" % ver)
    ev.append("技能文件总数 = %d（references %d / scripts %d / 其他 %d）"
              % (len(files), len(refs), len(scripts), len(files) - len(refs) - len(scripts)))
    if not m:
        level = "warn"

    rc, out = run([sys.executable, str(SCRIPTS_DIR / "skill_self_check.py")], timeout=180, cwd=SCRIPTS_DIR)
    clean = strip_ansi(out)
    # 坑：不能用「末行严格匹配」判定。子进程末行可能是 `结果: PASS`，也可能被包在别的格式里，
    # 且 cp936/UTF-8 混解码后连字面都不对 → 改为全输出里搜 结果/RESULT: PASS（大小写不敏感）。
    hits = re.findall(r"(?:结果|RESULT)\s*[:：]\s*(PASS|FAIL)", clean, re.I)
    verdict = hits[-1].upper() if hits else "UNKNOWN"
    if rc != 0 and verdict == "PASS":  # rc 才是硬事实，PASS 字样不能盖掉非零退出码
        verdict = "FAIL"
    ev.append("skill_self_check.py → %s（rc=%s）" % (verdict, rc))
    detail = [l.strip() for l in clean.splitlines() if re.search(r"死链|孤儿|超长行|结果", l)]
    ev.extend(["  " + d for d in detail[:4]])
    if verdict != "PASS":
        level = "fail"
        tail = [l.rstrip() for l in clean.splitlines() if l.strip()][-5:]
        ev.append("  子进程输出末 5 行（解码后）:")
        ev.extend(["    " + t[:180] for t in tail] or ["    （无输出）"])
    return {"level": level, "evidence": ev, "version": ver, "files": len(files), "selfcheck": verdict}


# ---------------------------------------------------------------- 2 cron
def parse_cron_list(text):
    """解析 `hermes cron list` 的盒子文本 → [{id,state,name,schedule,next,last_status,script}]"""
    jobs, cur = [], None
    for raw in text.splitlines():
        line = raw.replace("\r", "")
        m = re.match(r"^\s{1,3}([0-9a-f]{12})\s*\[([^\]]+)\]\s*$", line)
        if m:
            cur = {"id": m.group(1), "state": m.group(2).strip(), "name": "", "schedule": "",
                   "next": "", "last_status": "", "script": "", "mode": ""}
            jobs.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"^\s+(Name|Schedule|Next run|Last run|Script|Mode|Deliver|Repeat|Dispatch|Execution):\s*(.*)$", line)
        if not m:
            continue
        k, v = m.group(1), m.group(2).strip()
        if k == "Name":
            cur["name"] = v
        elif k == "Schedule":
            cur["schedule"] = v
        elif k == "Next run":
            cur["next"] = v
        elif k == "Script":
            cur["script"] = v
        elif k == "Mode":
            cur["mode"] = v
        elif k == "Last run":
            # 形如 "2026-11-17T09:40:17+08:00  ok"
            cur["last_status"] = v.split()[-1] if v else ""
    return jobs


def chk_cron():
    ev = []
    level = "ok"
    if not HERMES_EXE.is_file():
        return {"level": "fail", "evidence": ["hermes.exe 不存在: %s" % HERMES_EXE]}
    rc, out = run([str(HERMES_EXE), "cron", "list", "--all"], timeout=120)
    if rc is None or rc != 0:
        return {"level": "fail", "evidence": ["hermes cron list 失败 rc=%s：%s" % (rc, first_line(out))]}
    jobs = parse_cron_list(out)
    if not jobs:
        return {"level": "fail", "evidence": ["hermes cron list 未解析出任何 job（输出格式变了？）"]}
    ev.append("job 总数 = %d" % len(jobs))
    bad = []
    never = []
    for j in jobs:
        enabled = "active" in j["state"].lower()
        ls = (j["last_status"] or "").lower()
        ev.append("  %-32s %-8s last=%-8s next=%s" % (
            j["name"] or j["id"], "enabled" if enabled else j["state"],
            ls or "(从未运行)", (j["next"][:19] or "-")))
        if not enabled:
            bad.append("%s（%s，enabled=false）" % (j["name"], j["id"]))
        elif ls and ls != "ok":
            bad.append("%s（%s，last_status=%s）" % (j["name"], j["id"], ls))
        elif not ls:
            never.append(j["name"])
    if bad:
        level = "warn"
        ev.append("异常 job：")
        ev.extend("  ✗ " + b for b in bad)
    if never:
        ev.append("从未运行过的 job（新建/周任务尚未到点，不计异常）：%s" % ", ".join(never))
    self_job = [j for j in jobs if j["name"] == "orzmc-selfcheck"]
    ev.append("本自检 job = %s" % ("存在（%s）" % self_job[0]["id"] if self_job else "未建"))
    return {"level": level, "evidence": ev, "count": len(jobs), "bad": bad, "jobs": jobs}


# ---------------------------------------------------------------- 3 交付目录
def _ctypes_session():
    """取 (本进程 SessionId, 活动控制台 SessionId)；取不到返回 (None, None)。"""
    if os.name != "nt":
        return None, None
    try:
        import ctypes
        from ctypes import wintypes

        sid = wintypes.DWORD()
        if not ctypes.windll.kernel32.ProcessIdToSessionId(os.getpid(), ctypes.byref(sid)):
            return None, None
        con = ctypes.windll.kernel32.WTSGetActiveConsoleSessionId()
        return int(sid.value), (None if con == 0xFFFFFFFF else int(con))
    except Exception:
        return None, None


def session_probe():
    """判断本进程是否跑在交互桌面会话（映射盘只在交互会话里存在）。

    坑（实测）：S: 是「登录会话级」资源，SSH/服务会话（Session 0）永远看不到；
    cron 跑在 Session 1 能看到。所以在非交互会话里「S: 不可用」是正常现象，不是交付故障。
    """
    sid, con = _ctypes_session()
    ssh = bool(os.environ.get("SSH_CONNECTION") or os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"))
    if sid is None:  # 拿不到会话号：只能按 SSH 环境变量保守判断
        interactive = not ssh
    else:
        interactive = (sid != 0) and not ssh
    return {"session_id": sid, "console_session": con, "ssh_env": ssh, "interactive": interactive}


def _latest_delivered_report():
    """交付目录里最近一份 orzmc-selfcheck-*.md（S: / UNC 能看到才记）。返回 (路径, 时间) 或 None。"""
    best = None
    for base in (pathlib.Path("S:/"), pathlib.Path(r"\\{LAN_IP}\下载")):
        try:
            if not base.is_dir():
                continue
            for p in base.glob("orzmc-selfcheck-*.md"):
                try:
                    mt = p.stat().st_mtime
                except OSError:
                    continue
                if best is None or mt > best[0]:
                    best = (mt, p)
        except Exception:
            continue
    if best is None:
        return None
    return str(best[1]), datetime.fromtimestamp(best[0]).strftime("%Y-%m-%d %H:%M")


def chk_deliver():
    ev = []
    if deliver_dir is None:
        return {"level": "fail", "evidence": ["orzmc_paths 导入失败: %s" % _PATHS_ERR]}
    d, note = deliver_dir()
    sess = session_probe()
    ev.append("deliver_dir() = %s" % d)
    ev.append("命中级别 = %s" % note)
    ev.append("本进程会话 = %s（控制台会话 = %s%s）→ %s"
              % (sess["session_id"], sess["console_session"],
                 "，存在 SSH 环境变量" if sess["ssh_env"] else "",
                 "交互会话" if sess["interactive"] else "非交互会话（SSH/服务）"))
    probe = None
    try:
        d.mkdir(parents=True, exist_ok=True)
        probe = d / ("_selfcheck_probe_%d.tmp" % os.getpid())
        probe.write_text("ok", encoding="utf-8")
        back = probe.read_text(encoding="utf-8")
        probe.unlink()
        writable = (back == "ok")
        ev.append("写测试 = 成功（写入 'ok' → 回读一致 → 已删除 %s）" % probe.name)
    except Exception as e:
        writable = False
        ev.append("写测试 = 失败: %s: %s" % (type(e).__name__, e))
        if probe is not None:
            try:
                probe.unlink()
            except Exception:
                pass
    fallback = ("兜底" in note) or ("不可写" in note)
    last = _latest_delivered_report()
    if last:
        ev.append("最近一次交付目录自检报告 = %s（%s）" % (last[0], last[1]))
    elif not fallback:
        ev.append("最近一次交付目录自检报告 = 未找到 orzmc-selfcheck-*.md")
    if not writable:
        level = "fail"
    elif fallback and sess["interactive"]:
        level = "warn"
        ev.append("提示：S: 与 UNC 都不可用，落到本机兜底目录（老板可能看不到）——交互会话下这就是交付断了")
    elif fallback:
        level = "info"
        ev.append("ℹ️ 本会话看不到 S: —— 映射盘是登录会话级资源，SSH/服务会话（Session 0）看不到属正常，不是交付故障")
        ev.append("ℹ️ 交付由交互会话的 cron（orzmc-selfcheck 每天 08:30，跑在 Session 1）负责；本项不计 ⚠️、不影响退出码")
        ev.append("ℹ️ 本会话兜底目录 %s 可写（要立刻给人看可手抄这个路径）" % d)
    else:
        level = "ok"
    return {"level": level, "evidence": ev, "dir": str(d), "writable": writable,
            "note": note, "fallback": fallback, "session": sess}


# ---------------------------------------------------------------- 4 实例状态
def chk_instances():
    ev = []
    level = "ok"
    ev.append("ℹ️ MCSM 面板 API 403：已按老板决定不处理（API key 失效）——本项判定只走本地直读 + 容器事实，"
              "不查面板 API、不计告警、不影响退出码")
    rc, out = run(["docker", "ps", "-a", "--format", "{{.Names}}\t{{.Status}}"], timeout=60)
    if rc is None or rc != 0:
        return {"level": "fail", "evidence": ["docker ps 失败 rc=%s：%s" % (rc, first_line(out))]}
    states = {}
    for line in out.splitlines():
        if "\t" in line:
            n, s = line.split("\t", 1)
            states[n.strip()] = s.strip()
    ev.append("期望 running：")
    for name in EXPECT_RUNNING:
        st = states.get(name)
        ok = bool(st) and st.startswith("Up")
        ev.append("  %s %-24s %s" % ("✅" if ok else "❌", name, st or "容器不存在"))
        if not ok:
            level = "fail"
    ev.append("daemon 容器：%s" % (states.get(DAEMON_CONTAINER) or "不存在"))

    # paper/folia 在 MCSM 里是 daemon 容器内的 java 进程，不是独立容器 → 用进程判活
    ev.append("期望 stopped（MCSM 实例，按老板决定保持停止）：")
    for label, uuid in INSTANCE_UUIDS.items():
        rc2, out2 = run(["docker", "exec", DAEMON_CONTAINER, "sh", "-c",
                         "ps -ef | grep -i '[j]ava' | grep -i '%s'" % uuid[:8]], timeout=60)
        if rc2 is None:
            ev.append("  ⚠️ %-6s 无法探测（daemon 容器不可 exec）：%s" % (label, first_line(out2, 120)))
            level = "warn" if level == "ok" else level
            continue
        running = bool([l for l in out2.splitlines() if "java" in l.lower()])
        ev.append("  %s %-6s %s" % ("⚠️" if running else "✅", label,
                                    "正在运行（预期停止，老板没同意不要自动拉起）" if running else "stopped"))
        if running and level == "ok":
            level = "warn"
    return {"level": level, "evidence": ev}


# ---------------------------------------------------------------- 5 入口端口
def chk_ports():
    ev = []
    down = 0
    for port, label in ENTRY_PORTS:
        ok, why = tcp_open(port)
        ev.append("%s %-6d 127.0.0.1:%d  %s" % ("✅" if ok else "❌", port, port
                                               , "LISTEN/可连" if ok else "连不上（%s）" % why))
        if not ok:
            down += 1
    ev.append("说明：Docker Desktop(WSL2) 发布的端口不出现在 Windows netstat/Get-NetTCPConnection，故用 TCP 实连判定；"
              "本机连自己 LAN IP 会被代理 TUN 劫持而超时，属已知现象，不作判定依据。")
    ev.append("说明：本项只做 TCP 实连。19132 的 UDP 侧（NetherNet/RakNet）由 cron `orzmc-entry-probe` 的 "
              "`GET /v1/join` 覆盖，避免两处口径重复、各测各的假阳性。")
    if down == len(ENTRY_PORTS):
        level = "fail"
        ev.append("两个入口端口都不通 = 入口挂了")
    elif down:
        level = "warn"
    else:
        level = "ok"
    return {"level": level, "evidence": ev, "down": down}


# ---------------------------------------------------------------- 6 版本基线
def chk_baseline():
    ev = []
    level = "ok"
    mismatches = []
    for inst, label, pattern, expect in BASELINE:
        root = INSTANCE_ROOT / INSTANCE_UUIDS[inst]
        if not root.is_dir():
            ev.append("❌ %-6s %-16s 实例目录不存在: %s" % (inst, label, root))
            mismatches.append("%s %s 目录缺失" % (inst, label))
            level = "warn"
            continue
        rx = re.compile(pattern)
        cands = []
        for p in list(root.glob("*.jar")) + list((root / "plugins").glob("*.jar")):
            m = rx.match(p.name)
            if m:
                cands.append((p.name, m.group(1)))
        if not cands:
            ev.append("⚠️ %-6s %-16s 未找到匹配文件（期望版本 %s）" % (inst, label, expect))
            mismatches.append("%s %s 文件缺失" % (inst, label))
            level = "warn"
            continue
        for fname, ver in cands:
            same = (ver == expect)
            _PROTECT.update({ver, expect, fname})
            ev.append("%s %-6s %-16s %-34s 实测 %-12s 基线 %s"
                      % ("✅" if same else "⚠️", inst, label, fname, ver, expect))
            if not same:
                mismatches.append("%s %s 实测 %s ≠ 基线 %s（%s）" % (inst, label, ver, expect, fname))
                level = "warn"
    ev.append("口径：只读文件名比对，不改动实例；基线来源 = SKILL.md「第八轮升级后基线」")
    if mismatches:
        ev.append("不一致清单：")
        ev.extend("  · " + m for m in mismatches)
    return {"level": level, "evidence": ev, "mismatches": mismatches}


# ---------------------------------------------------------------- 7 工具链
def _user_env(name, expand=True):
    """读 Windows 用户级环境变量（HKCU\\Environment）的真值；REG_EXPAND_SZ 默认展开。

    坑：全局设了 ≠ 当前进程看得到。已在运行的进程（Hermes 网关、长驻 cron 宿主）不会自动继承
    新写的用户级环境变量，必须重启才拿到。所以「全局是否真的配了」以注册表为真值，
    os.environ 只作兜底 —— 否则自检会因「本进程没继承」误报全局没配。
    expand=False 保留原始 `%JAVA_HOME%` 字面（判定 Path 里是否登记了这条引用时要用原文，
    展开后字面就没了，会误判「未见 %JAVA_HOME%\\bin」）。
    """
    if os.name != "nt":
        return ""
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            val, typ = winreg.QueryValueEx(k, name)
        val = str(val)
        if typ == winreg.REG_EXPAND_SZ and expand:
            val = os.path.expandvars(val)
        return val
    except Exception:
        return ""


def _expand_vars(value, mapping):
    """按给定映射展开 `%VAR%`（大小写不敏感），**不依赖本进程 os.environ**。

    为什么要自己展：注册表里存的是变量原文 `%JAVA_HOME%\\bin`，而本进程（网关 / cron 宿主）
    可能根本没继承 JAVA_HOME，`os.path.expandvars` 就展不开，于是「展开后是否含 jdk25\\bin」
    这类判定会漏，反而把真配置报成缺（假红灯）。这里用注册表 JAVA_HOME 的真值去替。
    """
    out = str(value or "")
    for k, v in mapping.items():
        if v:
            out = re.sub(re.escape(k), lambda _m, _v=v: _v, out, flags=re.I)
    return out


def _path_entries(*raw_values):
    """把 PATH 串拆成目录列表（去引号、去空项）。"""
    entries = []
    for v in raw_values:
        for d in str(v or "").split(";"):
            d = d.strip().strip('"')
            if d:
                entries.append(d)
    return entries


def _find_java_on_path(dirs):
    """在给定目录里直接找 java.exe —— 判定口径 (c)。"""
    for d in dirs:
        for exe in ("java.exe", "java"):
            p = os.path.join(d, exe)
            if os.path.isfile(p):
                return p
    return ""


def resolve_git():
    """多级兜底解析 git.exe。返回 (绝对路径, 命中来源)；全找不到返回 ("", "")。

    坑（真红过的）：本机 Git 装在 C:\\Program Files\\Git 与 Hermes 自带 %LOCALAPPDATA%\\hermes\\git，
    但 HKCU / HKLM 的 Path 里都没有 git 目录 → `subprocess.run(["git", ...])` 在 SSH / 服务会话里
    直接 FileNotFoundError，第 7 项假 ❌『git 命令不存在: git』。bash(MSYS) 里 which 能命中
    mingw64/bin/git，那只是交互 shell 的 PATH，服务会话没有。
    兜底顺序（找到即用，并回显实际路径）：
        1) shutil.which("git")
        2) C:\\Program Files\\Git\\cmd\\git.exe
        3) %LOCALAPPDATA%\\hermes\\git\\cmd\\git.exe
        4) %LOCALAPPDATA%\\hermes\\git\\bin\\git.exe
    """
    cands = []
    found = shutil.which("git")
    if found:
        cands.append((found, "shutil.which(git)"))
    prog = os.environ.get("ProgramFiles") or r"C:\Program Files"
    cands.append((os.path.join(prog, "Git", "cmd", "git.exe"), r"C:\Program Files\Git\cmd\git.exe"))
    localapp = os.environ.get("LOCALAPPDATA") or str(HERMES_HOME.parent)
    cands.append((os.path.join(localapp, "hermes", "git", "cmd", "git.exe"),
                  r"%LOCALAPPDATA%\hermes\git\cmd\git.exe"))
    cands.append((os.path.join(localapp, "hermes", "git", "bin", "git.exe"),
                  r"%LOCALAPPDATA%\hermes\git\bin\git.exe"))
    for path, src in cands:
        try:
            if path and os.path.isfile(path):
                return path, src
        except OSError:
            continue
    return "", ""


def chk_toolchain():
    ev = []
    level = "ok"
    # JAVA_HOME 口径（老板定，2026-11-17 / 2.6.12 修假红灯）：
    # 注册表存的是变量原文 `%JAVA_HOME%\\bin`，若只拿「展开后的绝对路径 E:\\orzmc\\tools\\jdk25\\bin」
    # 去比对，一旦展开失败（本进程没继承 JAVA_HOME）就永远匹配不上 → 假 ❌。
    # 现口径：三路任一命中即算「PATH 里有 JDK bin」——
    #   (a) Path 含 %JAVA_HOME%\\bin（原文，大小写不敏感）
    #   (b) Path 用注册表 JAVA_HOME 展开后含 jdk25\\bin（不用本进程 env 展开）
    #   (c) PATH 目录里能直接找到 java.exe
    # 且 JAVA_HOME 已设置而 Path 缺这条时只记 ℹ️「建议补」，不判 ❌（真 ❌ 只留给「JDK 目录不可用」）。
    jdk_home = str(JDK_JAVA.parent.parent)
    reg_home = _user_env("JAVA_HOME")
    proc_home = os.environ.get("JAVA_HOME", "")
    effective = reg_home or proc_home or jdk_home

    path_raw = _user_env("Path", expand=False)
    path_exp = _expand_vars(path_raw, {"%JAVA_HOME%": reg_home or proc_home})
    raw_u = (path_raw or "").upper()
    exp_u = (path_exp or "").upper()
    home_bin_u = os.path.normcase(effective).upper().rstrip("\\") + "\\BIN"
    java_on_path = _find_java_on_path(
        _path_entries(path_exp) + _path_entries(os.environ.get("PATH", "")))

    hits = []
    if "%JAVA_HOME%\\BIN" in raw_u:
        hits.append("(a) 变量原文命中 %JAVA_HOME%\\bin")
    if home_bin_u in exp_u or "JDK25\\BIN" in exp_u:
        hits.append("(b) 展开后命中 jdk25\\bin")
    if java_on_path:
        hits.append("(c) PATH 可解析到 %s" % java_on_path)
    path_has_bin = bool(hits)

    java_in_home = os.path.isfile(os.path.join(effective, "bin", "java.exe"))
    if not reg_home and not proc_home:
        level = "warn"
        ev.append("⚠️ 全局 JAVA_HOME 未配置（用户级注册表无此键）——gradle 仍能跑，因为本脚本显式注入 %s"
                  % jdk_home)
    elif not java_in_home:
        level = "fail"
        ev.append("❌ JAVA_HOME 已设置 = %s，但该目录下没有 bin\\java.exe —— 环境变量指向了不存在/不完整的 JDK"
                  % effective)
    else:
        ev.append("✅ JAVA_HOME 全局已配置 = %s（来源：%s；用户 Path %s）"
                  % (reg_home or proc_home,
                     "注册表 HKCU\\Environment" if reg_home else "本进程环境",
                     "；".join(hits) if path_has_bin else "未见 JDK bin 引用"))
        if not path_has_bin:
            ev.append("ℹ️ PATH 未含 JDK bin，建议补（注册表用户 Path 里加 %JAVA_HOME%\\bin 或等价绝对路径）"
                      "——不影响本项判定，脚本已显式注入，gradle 照跑")
        if reg_home and os.path.normcase(reg_home) != os.path.normcase(jdk_home):
            ev.append("⚠️ 全局 JAVA_HOME 与技能内固定 JDK 不一致（技能固定 %s）——构建/巡检以显式注入值为准"
                      % jdk_home)

    if proc_home and reg_home and os.path.normcase(proc_home) != os.path.normcase(reg_home):
        ev.append("ℹ️ 本进程 JAVA_HOME=%s，与全局不一致（进程继承的是旧值）" % proc_home)
    ev.append("说明：已在运行的进程（如 Hermes 网关）需重启后才会继承，脚本内仍显式注入更稳（本次注入 JAVA_HOME=%s）"
              % effective)

    git_exe, git_src = resolve_git()
    tools = [
        ("jdk25 java", [str(JDK_JAVA), "-version"], None),
        ("gradle", ["cmd", "/c", str(GRADLE_BAT), "--version"], {"JAVA_HOME": effective}),
        ("node", ["node", "-v"], None),
    ]
    for label, cmd, env in tools:
        rc, out = run(cmd, timeout=180, env=env)
        head = ""
        for line in out.splitlines():
            s = line.strip()
            if s.startswith("Gradle ") or s.startswith("git version") or re.match(r"^v\d", s) \
                    or ("version" in s.lower() and "openjdk" in s.lower()):
                head = s
                break
        head = head or first_line(out)
        ok = rc == 0 and bool(head) and "ERROR" not in head.upper()
        ev.append("%s %-12s %s" % ("✅" if ok else "❌", label, head or "无输出(rc=%s)" % rc))
        if not ok:
            level = "fail"

    # git 单独走多级兜底（见 resolve_git）：PATH 没有不代表本机没 Git
    if git_exe:
        rc, out = run([git_exe, "--version"], timeout=120)
        head = ""
        for line in out.splitlines():
            if line.strip().startswith("git version"):
                head = line.strip()
                break
        head = head or first_line(out)
        ok = rc == 0 and bool(head)
        ev.append("%s %-12s %s（解析来源：%s）"
                  % ("✅" if ok else "❌", "git", head or "无输出(rc=%s)" % rc, git_src))
        ev.append("   git 实际路径 = %s" % git_exe)
        if not ok:
            level = "fail"
    else:
        ev.append("❌ git 不可用，git 相关自动化会失败（PATH + 三条兜底路径均未找到 git.exe："
                  "C:\\Program Files\\Git\\cmd → %LOCALAPPDATA%\\hermes\\git\\cmd → %LOCALAPPDATA%\\hermes\\git\\bin）")
        level = "fail"
    ev.append("路径：java=%s gradle=%s git=%s" % (JDK_JAVA, GRADLE_BAT, git_exe or "(未找到)"))
    return {"level": level, "evidence": ev}


# ---------------------------------------------------------------- 8 报告新鲜度
def chk_reports():
    ev = []
    if not REPORTS_DIR.is_dir():
        return {"level": "warn", "evidence": ["报告目录不存在: %s" % REPORTS_DIR]}
    files = [p for p in REPORTS_DIR.iterdir() if p.is_file()]
    if not files:
        return {"level": "warn", "evidence": ["报告目录为空: %s" % REPORTS_DIR]}
    files.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    for p in files[:3]:
        ev.append("  %s  %s" % (datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"), p.name))
    newest = files[0].stat().st_mtime
    age = (time.time() - newest) / 86400.0
    ev.insert(0, "最近报告：%s（%.1f 天前）" % (files[0].name, age))
    if age > REPORT_STALE_DAYS:
        ev.append("⚠️ 超过 %d 天没有新报告 —— 周巡检/配置审查可能没在跑" % REPORT_STALE_DAYS)
        return {"level": "warn", "evidence": ev, "age_days": round(age, 1)}
    return {"level": "ok", "evidence": ev, "age_days": round(age, 1)}


CHECKS = [
    ("1", "技能", chk_skill),
    ("2", "cron", chk_cron),
    ("3", "交付目录", chk_deliver),
    ("4", "实例状态", chk_instances),
    ("5", "入口端口", chk_ports),
    ("6", "版本基线", chk_baseline),
    ("7", "工具链", chk_toolchain),
    ("8", "报告新鲜度", chk_reports),
]


# ---------------------------------------------------------------- 汇总 / 报告
def status_line(results):
    """汇总一行。info（如非交互会话看不到 S:）既不计 ⚠️ 也不影响退出码。"""
    warn = [r for r in results if r["level"] == "warn"]
    fail = [r for r in results if r["level"] == "fail"]
    info = [r for r in results if r["level"] == "info"]
    if not warn and not fail:
        extra = "，ℹ️ %d 项说明" % len(info) if info else ""
        return "✅ 全绿（❌ 0%s）" % extra, warn, fail
    return "⚠️ %d 项提示 / ❌ %d 项失败" % (len(warn), len(fail)), warn, fail


def render_md(results, sl, warn, fail):
    now = datetime.now()
    info = [r for r in results if r["level"] == "info"]
    lines = [
        "# OrzMC 全栈自检报告",
        "",
        "- 生成时间：%s" % now.strftime("%Y-%m-%d %H:%M:%S"),
        "- 主机：Windows 测试服宿主（Hermes 侧唯一 MC 执行端）",
        "- 结论：**%s**" % sl,
        "",
    ]
    if fail:
        lines.append("## ❌ 失败项")
        lines.append("")
        for r in fail:
            lines.append("- **%s %s**" % (r["id"], r["name"]))
            lines.extend("  - " + e for e in r["evidence"])
        lines.append("")
    if warn:
        lines.append("## ⚠️ 提示项")
        lines.append("")
        for r in warn:
            lines.append("- **%s %s**" % (r["id"], r["name"]))
            lines.extend("  - " + e for e in r["evidence"])
        lines.append("")
    if info:
        lines.append("## ℹ️ 说明项（不计告警、不影响退出码）")
        lines.append("")
        for r in info:
            lines.append("- **%s %s**" % (r["id"], r["name"]))
            lines.extend("  - " + e for e in r["evidence"])
        lines.append("")
    lines.append("## 全部明细")
    lines.append("")
    for r in results:
        lines.append("### %s %s %s（%dms）" % (LEVEL_ICON.get(r["level"], "?"), r["id"], r["name"], r["elapsed_ms"]))
        lines.append("")
        lines.append("```")
        lines.extend(r["evidence"])
        lines.append("```")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("STATUS_LINE: %s" % sl)
    return "\n".join(lines) + "\n"


def _mask_versions(text):
    """把已知版本串换成占位符（脱敏前保护），返回 (text, 还原函数)"""
    pairs = []
    for i, tok in enumerate(sorted((t for t in _PROTECT if t), key=len, reverse=True)):
        ph = "@@VER%d@@" % i
        if tok in text:
            text = text.replace(tok, ph)
            pairs.append((ph, tok))
    def unmask(s):
        for ph, tok in pairs:
            s = s.replace(ph, tok)
        return s
    return text, unmask


LATEST_NAME = "orzmc-selfcheck-latest.md"
SNAPSHOT_RX = re.compile(r"^orzmc-selfcheck-\d{8}-\d{4}\.md$")
KEEP_SNAPSHOTS = 3


def write_deliver(md_text, results, alert=True):
    """落盘：latest 每次无条件覆盖；带时间戳快照只在 alert(⚠️/❌) 时写，滚动只留最新 3 份。

    口径（老板定）：
      * latest 必须永远是「最近一次真实结论」→ 每次运行都覆盖，绝不因为全绿就不写，
        否则 latest 会停在旧的告警内容上，人一看就误判。
      * 快照只留痕用 → 只写告警那次；全绿不产生新快照，避免无上限累积。
    """
    if deliver_dir is None:
        return [], "orzmc_paths 不可用，未落盘"
    d, note = deliver_dir()
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    if redact:
        masked, unmask = _mask_versions(md_text)
        body = unmask(redact(masked))
    else:
        body = md_text
    written, notes = [], []
    try:
        d.mkdir(parents=True, exist_ok=True)
        latest = d / LATEST_NAME
        latest.write_text(body, encoding="utf-8")
        written.append(str(latest))
        if not alert:
            snaps = sorted((p for p in d.glob("orzmc-selfcheck-*.md")
                            if SNAPSHOT_RX.match(p.name)), key=lambda p: p.name, reverse=True)
            notes.append("全绿：latest 已覆盖，不写快照（现存快照 %d 份，未变动）" % len(snaps))
            return written, note + "；" + "；".join(notes)
        snap = d / ("orzmc-selfcheck-%s.md" % stamp)
        snap.write_text(body, encoding="utf-8")
        written.append(str(snap))
        # 滚动保留：按文件名（yyyyMMdd-HHmm 字典序 = 时间序）降序，超出的删最旧
        snaps = sorted((p for p in d.glob("orzmc-selfcheck-*.md")
                        if SNAPSHOT_RX.match(p.name)), key=lambda p: p.name, reverse=True)
        for old in snaps[KEEP_SNAPSHOTS:]:
            try:
                old.unlink()
                notes.append("滚动删除最旧副本 %s" % old.name)
            except OSError as e:
                notes.append("滚动删除失败 %s: %s" % (old.name, e))
        notes.insert(0, "告警快照已写；快照数 = %d（上限 %d）" % (min(len(snaps), KEEP_SNAPSHOTS), KEEP_SNAPSHOTS))
        return written, note + "；" + "；".join(notes)
    except Exception as e:
        return written, "写交付失败: %s: %s" % (type(e).__name__, e)


def main(argv=None):
    ap = argparse.ArgumentParser(description="OrzMC 全栈自检（8 项）")
    ap.add_argument("--json", action="store_true", help="输出机器可读 JSON（stdout 只有 JSON）")
    ap.add_argument("--no-deliver", action="store_true", help="不写交付目录 md")
    ap.add_argument("--always-deliver", action="store_true",
                    help="已废弃（兼容保留）：现在 latest 每次运行都会写，无需此开关")
    ap.add_argument("--quiet", action="store_true", help="只打印 STATUS_LINE（cron 输出用）")
    args = ap.parse_args(argv)

    results = [check(cid, name, fn) for cid, name, fn in CHECKS]
    sl, warn, fail = status_line(results)
    info = [r for r in results if r["level"] == "info"]

    delivered, deliver_note = [], ""
    # 交付策略：latest 无条件覆盖（只有 --no-deliver 才跳过）；时间戳快照由 alert(⚠️/❌) 决定
    should_write = not args.no_deliver
    alert = bool(warn or fail)
    if should_write:
        delivered, deliver_note = write_deliver(render_md(results, sl, warn, fail), results, alert=alert)

    if args.json:
        print(json.dumps({
            "generated_at": datetime.now().isoformat(timespec="seconds"),
            "status_line": sl,
            "summary": {"ok": len(results) - len(warn) - len(fail) - len(info),
                        "warn": len(warn), "fail": len(fail), "info": len(info)},
            "exit_code": 1 if fail else 0,
            "delivered": delivered[0] if delivered else None,
            "delivered_files": delivered,
            "deliver_note": deliver_note,
            "checks": [{"id": r["id"], "name": r["name"], "level": r["level"],
                        "elapsed_ms": r["elapsed_ms"], "evidence": r["evidence"]}
                       for r in results],
        }, ensure_ascii=False, indent=2))
    elif args.quiet:
        print(sl)
    else:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("=" * 78)
        print("OrzMC 全栈自检  %s" % now)
        print("=" * 78)
        for r in results:
            print("%s %s %s  (%dms)" % (LEVEL_ICON.get(r["level"], "?"), r["id"], r["name"], r["elapsed_ms"]))
            for e in r["evidence"]:
                print("     " + e)
            print()
        print("-" * 78)
        print("STATUS_LINE: %s" % sl)
        if delivered:
            print("交付报告：")
            for p in delivered:
                print("  %s" % p)
            print("  说明：%s" % deliver_note)
        elif should_write:
            print("交付报告：写入失败（%s）" % deliver_note)
        else:
            print("交付报告：未写（--no-deliver，latest 未刷新）")
    return 1 if fail else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit:
        raise
    except Exception as e:  # 顶层兜底：自检自己不许崩
        print("❌ 自检脚本本身异常: %s: %s" % (type(e).__name__, e))
        print("STATUS_LINE: ❌ 1 项失败")
        sys.exit(1)
