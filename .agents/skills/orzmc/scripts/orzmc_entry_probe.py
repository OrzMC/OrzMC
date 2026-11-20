#!/usr/bin/env python3
"""OrzMC 入口存活探针（no_agent watchdog，cron 每 30 分钟）。

拓扑（2026-11-12 起）：公网 25565/19132 由 orzmc-velocity（Velocity + Geyser-Velocity
+ EaglercraftXServer）独占，网页入口走 orzmc-caddy:18443，后端是 MCSM-716c2f(Paper)
与 MCSM-8A932D(Folia)。2026-11-19 起两台后端已关闭 RCON（enable-rcon=false，不再发布端口），
本探针按实例配置自动跳过 RCON 探测，只保留入口层校验。

检查项：入口容器、Java 状态包、NetherNet 信令 /v1/join、网页入口 TLS+404、
两口 RCON 认证。

输出纪律：全绿**不输出**（cron 静默）；故障只在「新故障 / 故障集合变化 / 每 6 小时
复述一次」时输出，避免每 30 分钟刷同一条。恢复时给一条 ✅ 收尾。
⚠️ 只报警，绝不自动重启容器（老板要求：入口处置必须人工拍板）。
"""
from __future__ import annotations
import sys
try:  # Windows console/pipe defaults to cp936: lock UTF-8 or emoji print raises
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

import json
import os
import re
import socket
import ssl
import struct
import subprocess
import time
import http.client

HERMES = os.path.join(os.environ.get("LOCALAPPDATA", ""), "hermes")
LOG = os.path.join(HERMES, "logs", "orzmc-entry-probe.log")
STATE = os.path.join(HERMES, "state", "orzmc_entry_probe.json")
DATA_ROOT = "E:/orzmc"
DOMAIN = "dev.{SERVER_NAME}.cn"
INSTANCES = [
    ("paper", "716c2fb712154c36ba5ab0f1480d3f87", 25575),
    ("folia", "8A932DD47F4D42AAAD6A6A9A5FAD2A91", 25576),
]
REALERT_SECONDS = 6 * 3600
DOCKER_TIMEOUT = 12
DOCKER_DOWN = "docker 调用失败"


def log(msg: str) -> None:
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except OSError:
        pass


def load_state() -> dict:
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def save_state(st: dict) -> None:
    try:
        os.makedirs(os.path.dirname(STATE), exist_ok=True)
        json.dump(st, open(STATE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    except OSError:
        pass


# ---------------------------------------------------------------- checks
def container_running(name: str) -> tuple[bool, str]:
    try:
        r = subprocess.run(
            ["docker", "inspect", "-f", "{{.State.Status}}", name],
            capture_output=True, text=True, timeout=DOCKER_TIMEOUT,
        )
        status = r.stdout.strip()
        if r.returncode != 0:
            return False, f"容器不存在（{r.stderr.strip()[:60]}）"
        return status == "running", f"{status}"
    except Exception as exc:  # noqa: BLE001
        return False, f"{DOCKER_DOWN}: {type(exc).__name__}"


def instance_containers() -> dict[str, str]:
    """实例容器的真实状态（running / exited / 缺失）。"""
    want = {"MCSM-716c2f": "paper", "MCSM-8A932D": "folia"}
    out = {v: "缺失" for v in want.values()}
    try:
        r = subprocess.run(
            ["docker", "ps", "-a", "--format", "{{.Names}}|{{.State}}"],
            capture_output=True, text=True, timeout=DOCKER_TIMEOUT,
        )
        if r.returncode != 0:
            return out
        for line in r.stdout.splitlines():
            name, _, state = line.partition("|")
            if name in want:
                out[want[name]] = state or "unknown"
    except Exception:  # noqa: BLE001
        pass
    return out


def _read_varint(sock) -> int:
    num = shift = 0
    while True:
        chunk = sock.recv(1)
        if not chunk:
            raise EOFError("连接中断")
        v = chunk[0]
        num |= (v & 0x7F) << shift
        if not v & 0x80:
            return num
        shift += 7


def java_status(host: str = "127.0.0.1", port: int = 25565, timeout: float = 6.0) -> tuple[bool, str]:
    """MC 状态握手：返回（通否，'版本 x/500 人'）。"""
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

            addr = host.encode()
            body = b"\x00" + varint(767) + varint(len(addr)) + addr + struct.pack(">H", port) + b"\x01"
            s.sendall(varint(len(body)) + body)
            s.sendall(b"\x01\x00")
            _read_varint(s)
            _read_varint(s)
            slen = _read_varint(s)
            data = b""
            while len(data) < slen:
                chunk = s.recv(slen - len(data))
                if not chunk:
                    break
                data += chunk
            d = json.loads(data.decode("utf-8", "replace"))
            ver = d.get("version", {}).get("name", "?")
            p = d.get("players", {})
            return True, f"{ver}，{p.get('online', 0)}/{p.get('max', 0)} 人"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def nethernet() -> tuple[bool, str]:
    """NetherNet 信令 GET /v1/join 必须 200（单端口模式 RakNet 本来就不应答，别去测）。"""
    try:
        c = http.client.HTTPConnection("127.0.0.1", 19132, timeout=8)
        c.request("GET", "/v1/join")
        r = c.getresponse()
        body = r.read(400).decode("utf-8", "replace")
        c.close()
        if r.status != 200:
            return False, f"HTTP {r.status}"
        try:
            d = json.loads(body)
            return True, f"{d.get('name')} protocol={d.get('protocol')} 玩家={d.get('players')}"
        except ValueError:
            return True, "200（响应非 JSON）"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def web_entry() -> tuple[bool, str]:
    """网页入口：TLS(SNI) 直连宿主 443，期望 404 + Server: EaglercraftXServer（101 才是升级，GET 永远 404）。"""
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    try:
        raw = socket.create_connection(("127.0.0.1", 443), timeout=8)
        s = ctx.wrap_socket(raw, server_hostname=DOMAIN)
        s.sendall(f"GET / HTTP/1.1\r\nHost: {DOMAIN}\r\nConnection: close\r\n\r\n".encode())
        head = s.recv(600).decode("latin-1", "replace")
        s.close()
        line = head.splitlines()[0] if head else ""
        server = ""
        m = re.search(r"(?im)^Server:\s*(.+)$", head)
        if m:
            server = m.group(1).strip()
        ok = "404" in line and "eaglercraft" in server.lower()
        return ok, f"{line.strip()} | Server: {server or '?'}"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


def rcon_password(uuid: str) -> str:
    try:
        txt = open(os.path.join(DATA_ROOT, "mcsmanager", "daemon", "data", "InstanceData", uuid, "server.properties"),
                   encoding="utf-8", errors="replace").read()
        m = re.search(r"(?m)^rcon\.password=(.+)$", txt)
        return m.group(1).strip() if m else ""
    except OSError:
        return ""


def rcon_enabled(uuid: str) -> bool:
    """server.properties 里 enable-rcon=false 时，不再拿 RCON 当选活信号（2026-11-19 关闭 RCON 后）。"""
    try:
        txt = open(os.path.join(DATA_ROOT, "mcsmanager", "daemon", "data", "InstanceData", uuid, "server.properties"),
                   encoding="utf-8", errors="replace").read()
    except OSError:
        return True  # 读不到就按老逻辑探测，别把真故障吞掉
    m = re.search(r"(?m)^enable-rcon=(.+)$", txt)
    return True if not m else m.group(1).strip().lower() == "true"


def rcon(port: int, password: str, command: str = "list", timeout: float = 8.0) -> tuple[bool, str]:
    if not password:
        return False, "读不到 rcon.password"

    def pkt(rid: int, ptype: int, body: str) -> bytes:
        payload = struct.pack("<ii", rid, ptype) + body.encode() + b"\x00\x00"
        return struct.pack("<i", len(payload)) + payload

    try:
        with socket.create_connection(("127.0.0.1", port), timeout=timeout) as s:
            s.sendall(pkt(1, 3, password))
            time.sleep(0.15)
            s.sendall(pkt(2, 2, command))
            buf = b""
            deadline = time.time() + timeout
            while time.time() < deadline:
                # 先把缓冲区里所有完整包解完，再决定要不要继续收（否则认证包会把命令包一起吞掉）
                while len(buf) >= 4:
                    (size,) = struct.unpack("<i", buf[:4])
                    if size < 10 or size > 65536:
                        return False, f"响应格式异常（size={size}）"
                    if len(buf) - 4 < size:
                        break
                    rid, ptype = struct.unpack("<ii", buf[4:12])
                    payload = buf[12:4 + size]
                    buf = buf[4 + size:]
                    if rid == 1 and ptype == -1:
                        return False, "认证失败（密码不匹配）"
                    if rid == 2:
                        body = payload.rstrip(b"\x00").decode("utf-8", "replace")
                        body = re.sub(r"§.", "", body).strip()
                        return True, (body[:400] if body else "（空响应）")
                chunk = s.recv(4096)
                if not chunk:
                    break
                buf += chunk
            return False, "无响应/超时"
    except Exception as exc:  # noqa: BLE001
        return False, f"{type(exc).__name__}: {exc}"


# ---------------------------------------------------------------- main
def main() -> int:
    results: list[tuple[str, bool, str]] = []
    # 提示项：不进告警集合、不进状态文件、不参与复述（老板 2026-11-16 决策）
    infos: list[tuple[str, str]] = []
    docker_alive = True
    for name in ("orzmc-velocity", "orzmc-caddy"):
        ok, detail = container_running(name)
        if detail.startswith(DOCKER_DOWN):
            docker_alive = False
        results.append((f"容器 {name}", ok, detail))

    if not docker_alive:
        # Docker 引擎本身不可用：端口探测必然全红，只报一条，别刷 7 行
        results = [(
            "Docker 引擎",
            False,
            "docker 命令超时/不可用 —— 容器与端口全部无法核实（Docker Desktop 或 WSL2 已挂），"
            "入口和网页此刻多半真的断了",
        )]
    else:
        ok, detail = java_status()
        results.append(("Java 入口 25565", ok, detail))
        ok, detail = nethernet()
        results.append(("NetherNet 信令 19132", ok, detail))
        ok, detail = web_entry()
        results.append(("网页入口 18443", ok, detail))

        states = instance_containers()
        for label, uuid, port in INSTANCES:
            state = states.get(label, "未知")
            if state != "running":
                # 后端容器没起 → RCON 必然不通。属于刻意保持停止 → 提示项：
                # 只写日志，不进告警、不复述、不发飞书
                infos.append((
                    f"后端 {label} 实例",
                    f"容器状态 {state}（刻意保持停止；面板手动启动，不自动拉起）",
                ))
                continue
            if not rcon_enabled(uuid):
                # 2026-11-19 起测试服关闭 RCON：端口不发布、server.properties enable-rcon=false，
                # 仅作提示项记录，不探测、不进告警。
                infos.append((f"后端 {label} RCON", "已关闭（enable-rcon=false，未发布端口），不探测"))
                continue
            ok, detail = rcon(port, rcon_password(uuid))
            results.append((f"RCON {label} :{port}", ok, detail))

    for n, d in infos:
        log(f"INFO {n}={d}")

    fails = [(n, d) for n, ok, d in results if not ok]
    st = load_state()
    prev = st.get("fails", [])
    now = time.time()
    sig = sorted(n for n, _ in fails)

    if not fails:
        if prev:
            print("✅ OrzMC 入口已恢复正常（本轮全部检查通过）。")
            log("恢复：" + ", ".join(prev))
        elif infos:
            log("OK 入口全绿（含 " + str(len(infos)) + " 条提示项，不计入告警）")
        else:
            log("OK 全绿")
        save_state({"fails": [], "last_alert": 0})
        return 0

    last_alert = float(st.get("last_alert", 0) or 0)
    changed = sig != sorted(prev)
    if changed or now - last_alert > REALERT_SECONDS:
        lines = [
            f"🔴 **OrzMC 入口异常**（{time.strftime('%m-%d %H:%M')}，共 {len(fails)} 项）",
            "",
        ]
        for n, d in fails:
            lines.append(f"- `{n}`：{d}")
        if not changed:
            lines.append("")
            lines.append("_同一批故障仍在持续（每 6 小时复述一次）。_")
        lines.append("")
        lines.append("未自动重启任何容器；需要处置请回我一句。")
        print("\n".join(lines))
        log("ALERT " + "; ".join(f"{n}={d}" for n, d in fails))
        st["last_alert"] = now
    else:
        log("FAIL(静默) " + "; ".join(f"{n}={d}" for n, d in fails))

    st["fails"] = sig
    save_state(st)
    # 检出故障不是任务失败：退出码 0，让 cron 保持绿色（真 bug 才返回 2）
    return 0


def guarded_main() -> int:
    try:
        return main()
    except Exception:  # noqa: BLE001
        import traceback
        tb = traceback.format_exc()
        print("⚠️ 探针自身崩了（不是服务器故障）：\n```\n" + tb[-800:] + "\n```")
        log("SCRIPT-CRASH\n" + tb[-1200:])
        return 2


if __name__ == "__main__":
    raise SystemExit(guarded_main())
