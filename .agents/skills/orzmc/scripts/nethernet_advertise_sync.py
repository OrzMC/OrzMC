#!/usr/bin/env python3
"""NetherNet 公网地址守护（OrzMC 测试服）。

背景：基岩 26.60+ 走 NetherNet，客户端必须能直达服务端 advertise 的地址。
本机跑 Clash TUN，`stun-discovery` 会探到代理出口（不是家宽 IP），所以必须显式配置
`bedrock.signaling.advertise-addresses`；家宽 IP 动态（DDNS），所以要有人盯着。

本脚本不再依赖"域名自动生效"：本机/容器的 DNS 随时可能被 Clash fake-ip 劫持成
198.18.x（skill nethernet.md §5.5 的实测坑），所以 advertise 只写**数字 IP**：
  局域网 IP（给家里设备，保持原值） + 公网 IP:信令端口（由 DoH 解析域名得到）。

行为（ADR-036 之后入口 = orzmc-velocity 容器里的 Geyser-Velocity，旧拓扑回落 MCSM 实例）：
  1. 读当前在用的 Geyser 配置，算出 advertise 应是什么；
  2. 不一致：
     - 无人在线 → 改写配置 + 重启入口容器（Geyser 只在信令启动时读 advertise）
     - 有玩家在线 → 不改不重启，只报警，等人工挑空档
  3. 一致 → 静默退出。

用法：python nethernet_advertise_sync.py [--dry] [-v]
退出码：0 正常/无变化；3 需要人工处理；1 出错。
"""
from __future__ import annotations
try:  # Windows console/pipe defaults to cp936: lock UTF-8 or emoji print raises
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import argparse
import glob
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time
import urllib.parse
import urllib.request

DOMAIN = "dev.{SERVER_NAME}.cn"
DATA_ROOT = "E:/orzmc"
PROXY_GEYSER_GLOB = f"{DATA_ROOT}/eagler/proxy/plugins/Geyser-*/config.yml"
MCSM_INSTANCES = [
    ("papermc-test", "716c2fb712154c36ba5ab0f1480d3f87"),
    ("folia-test", "8A932DD47F4D42AAAD6A6A9A5FAD2A91"),
]
ENTRY_CONTAINER = "orzmc-velocity"   # Velocity + Geyser-Velocity 入口（ADR-036）
JAVA_STATUS = ("127.0.0.1", 25565)

HERMES_DIR = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes")
LOG = os.path.join(HERMES_DIR, "logs", "nethernet-advertise-sync.log")
STATE = os.path.join(HERMES_DIR, "state", "nethernet-advertise.json")

DRY = False
VERBOSE = False


def log(msg: str) -> None:
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except OSError:
        pass


def vlog(msg: str) -> None:
    if VERBOSE:
        log(msg)


# ---------------------------------------------------------------- DNS
def resolve_a(domain: str) -> str:
    """DoH 查 A 记录（不走系统解析器，避开 Clash TUN fake-ip）。"""
    endpoints = [
        ("https://dns.alidns.com/resolve", {"name": domain, "type": "1"}),
        ("https://1.1.1.1/dns-query", {"name": domain, "type": "A"}),
    ]
    last = ""
    for url, params in endpoints:
        try:
            req = urllib.request.Request(
                url + "?" + urllib.parse.urlencode(params),
                headers={"accept": "application/dns-json", "User-Agent": "nethernet-sync/4.0"},
            )
            with urllib.request.urlopen(req, timeout=12) as r:
                data = json.loads(r.read().decode())
            ips = [a["data"] for a in data.get("Answer", []) if a.get("type") == 1]
            ips = [ip for ip in ips if not ip.startswith("198.18.")]
            if ips:
                vlog(f"DoH {url} -> {ips[0]}")
                return ips[0]
            last = f"{url} 无 A 记录"
        except Exception as exc:  # noqa: BLE001
            last = f"{url}: {exc}"
    raise RuntimeError(f"DNS 解析失败：{last}")


# ---------------------------------------------------------------- config
def live_configs() -> list[tuple[str, str]]:
    env = ""
    try:
        env = open(f"{DATA_ROOT}/.env", encoding="utf-8", errors="replace").read()
    except OSError:
        pass
    proxy_cfgs = sorted(glob.glob(PROXY_GEYSER_GLOB))
    if re.search(r"(?m)^ENABLE_VELOCITY\s*=\s*true", env) and proxy_cfgs:
        return [("velocity", c) for c in proxy_cfgs]
    out: list[tuple[str, str]] = []
    for name, uuid in MCSM_INSTANCES:
        for c in sorted(glob.glob(f"{DATA_ROOT}/mcsmanager/daemon/data/InstanceData/{uuid}/plugins/Geyser-*/config.yml")):
            out.append((name, c))
    return out


def read_text(path: str) -> str:
    return open(path, encoding="utf-8", errors="replace").read()


def yaml_scalar(text: str, key: str, default: str = "") -> str:
    m = re.search(rf"(?m)^\s*{re.escape(key)}:\s*([^\s#]+)", text)
    return m.group(1).strip("\"'") if m else default


def signaling_port(text: str) -> int:
    """both/nethernet 下媒体端口 = webrtc-port（0 表示与 port 相同）。"""
    port = int(yaml_scalar(text, "port", "19132") or 19132)
    try:
        webrtc = int(yaml_scalar(text, "webrtc-port", "0") or 0)
    except ValueError:
        webrtc = 0
    return webrtc if webrtc > 0 else port


def parse_advertised(text: str) -> list[str]:
    m = re.search(r"(?m)^(\s*advertise-addresses:\s*)\[(.*?)\]", text, re.S)
    if not m:
        return []
    return [s.strip().strip("\"'") for s in m.group(2).split(",") if s.strip().strip("\"'")]


def is_ip(host: str) -> bool:
    return bool(re.fullmatch(r"\d{1,3}(\.\d{1,3}){3}", host))


def is_private(host: str) -> bool:
    return bool(re.fullmatch(r"(10|192\.168|172\.(1[6-9]|2\d|3[01]))\.\d+\.\d+", host))


def split_host(entry: str) -> str:
    m = re.match(r"^\[(.+)\](?::\d+)?$", entry)  # IPv6
    if m:
        return m.group(1)
    if entry.count(":") == 1:
        host, port = entry.rsplit(":", 1)
        if port.isdigit():
            return host
    return entry


def env_lan_ip() -> str:
    """宿主局域网地址以 .env 的 LAN_HOST_IP 为真值（DHCP 换 IP 后配置里的旧值会失效）。"""
    try:
        env = open(f"{DATA_ROOT}/.env", encoding="utf-8", errors="replace").read()
    except OSError:
        return ""
    m = re.search(r"(?m)^LAN_HOST_IP\s*=\s*([0-9.]+)", env)
    return m.group(1) if m and is_ip(m.group(1)) else ""


def desired_entries(text: str, public_ip: str) -> list[str]:
    """局域网条目取 .env 的 LAN_HOST_IP；公网/域名条目一律归一成 <IP>:<信令端口>。"""
    port = signaling_port(text)
    lan = env_lan_ip()
    if not lan:
        cur = [e for e in parse_advertised(text) if is_private(split_host(e))]
        lan = cur[0] if cur else ""
    return ([lan] if lan else []) + [f"{public_ip}:{port}"]


def rewrite_advertised(path: str, entries: list[str]) -> None:
    text = read_text(path)
    new = "advertise-addresses: [" + ", ".join(f'"{e}"' for e in entries) + "]"
    text2, n = re.subn(r"(?m)^\s*advertise-addresses:.*$", "    " + new, text, count=1)
    if n != 1:
        raise RuntimeError("找不到 advertise-addresses 行")
    if DRY:
        return
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text2)


# ---------------------------------------------------------------- state
def load_state() -> dict:
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2, sort_keys=True)


# ---------------------------------------------------------------- players
def java_players(host: str = JAVA_STATUS[0], port: int = JAVA_STATUS[1], timeout: float = 5.0) -> int | None:
    try:
        with socket.create_connection((host, port), timeout=timeout) as s:
            def varint(n: int) -> bytes:
                out = b""
                while True:
                    b = n & 0x7F
                    n >>= 7
                    out += bytes([b | (0x80 if n else 0)])
                    if not n:
                        return out

            def read_varint() -> int:
                num = shift = 0
                while True:
                    chunk = s.recv(1)
                    if not chunk:
                        raise EOFError("连接中断")
                    v = chunk[0]
                    num |= (v & 0x7F) << shift
                    if not v & 0x80:
                        return num
                    shift += 7

            addr = host.encode()
            body = b"\x00" + varint(767) + varint(len(addr)) + addr + struct.pack(">H", port) + b"\x01"
            s.sendall(varint(len(body)) + body)
            s.sendall(b"\x01\x00")
            read_varint()
            read_varint()
            slen = read_varint()
            data = b""
            while len(data) < slen:
                chunk = s.recv(slen - len(data))
                if not chunk:
                    break
                data += chunk
            return int(json.loads(data.decode("utf-8", "replace")).get("players", {}).get("online", 0))
    except Exception:  # noqa: BLE001
        return None


def restart_entry() -> str:
    try:
        r = subprocess.run(["docker", "restart", ENTRY_CONTAINER], capture_output=True, text=True, timeout=240)
        return f"docker restart {ENTRY_CONTAINER} rc={r.returncode}"
    except Exception as exc:  # noqa: BLE001
        return f"重启失败: {exc}"


# ---------------------------------------------------------------- main
def main() -> int:
    global DRY, VERBOSE
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    DRY, VERBOSE = args.dry, args.verbose

    state = load_state()
    targets = live_configs()
    if not targets:
        log("🔴 找不到任何在用 Geyser 配置")
        return 1
    vlog(f"目标配置：{[c for _, c in targets]}")

    try:
        public_ip = resolve_a(DOMAIN)
    except Exception as exc:  # noqa: BLE001
        log(f"🔴 {exc}")
        return 1
    vlog(f"{DOMAIN} → {public_ip}")

    changes: list[tuple[str, str, list[str], list[str]]] = []
    errors = 0
    for label, cfg in targets:
        try:
            text = read_text(cfg)
        except OSError as exc:
            log(f"🔴 {label}: 读配置失败 {cfg}: {exc}")
            errors += 1
            continue
        cur = parse_advertised(text)
        if not cur:
            log(f"🔴 {label}: advertise-addresses 为空 → STUN 会探到代理出口，新客户端拿不到可达地址")
            errors += 1
            continue
        want = desired_entries(text, public_ip)
        if cur == want:
            vlog(f"✅ {label}: {cur} 已是最新")
            continue
        log(f"🔁 {label}: advertise 需更新 {cur} → {want}")
        changes.append((label, cfg, cur, want))

    if not changes:
        if state.pop("pending_alert", None) is not None:
            save_state(state)
        return 0 if errors == 0 else 1

    players = java_players()
    if args.dry:
        log(f"🟡 dry-run：{len(changes)} 处待改，在线玩家 {players}")
        return 0
    if players is None:
        log("⚠️ 查不到在线人数，保守处理：不改不重启，请人工确认")
        return 3
    if players > 0:
        sig = "|".join(f"{label}:{','.join(want)}" for label, _cfg, _cur, want in changes)
        if state.get("pending_alert") == sig:
            vlog("（同一批待办已报过，静默）")
            return 0
        state["pending_alert"] = sig
        save_state(state)
        log(f"🔴 配置过期但当前有 {players} 人在线，未改动；等无人在线时脚本会自动修（或人工重启 {ENTRY_CONTAINER}）")
        return 3

    for label, cfg, _cur, want in changes:
        try:
            rewrite_advertised(cfg, want)
            log(f"✏️ {label}: 已写入 {want}")
        except Exception as exc:  # noqa: BLE001
            log(f"🔴 {label}: 写入失败 {exc}")
            errors += 1
    if errors == 0:
        state.pop("pending_alert", None)
        save_state(state)
        log(f"🔄 无人在线，重启入口让 Geyser 重新读取 advertise：{restart_entry()}")
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
