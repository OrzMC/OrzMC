#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""orzmc 实例端口审计：核对「实例实际监听的端口」与「docker.ports 已发布映射」。

背景：MCSManager 的 docker 型实例不会自动发布容器端口；端口号必须逐条显式写
`宿主:容器/协议`。核心（Paper/Folia/Purpur）、Geyser 的 bedrock port 都可能不是默认值，
所以判断依据是「实例自己的配置」，不是「默认 25565/19132」。

用法:
  python port-audit.py [DATA_ROOT] [--probe] [--json]
    DATA_ROOT 默认 E:/orzmc/mcsmanager/daemon/data
    --probe   额外对宿主端口做实测（Java 握手 Ping / RakNet Unconnected Ping）
    --json    机器可读输出
退出码: 0 = 必发布端口齐全且无宿主端口冲突; 1 = 有缺口
"""
import glob
import json
import os
import re
import socket
import struct
import sys
import time

MAGIC = bytes([0x00, 0xFF, 0xFF, 0x00, 0xFE, 0xFE, 0xFE, 0xFE,
               0xFD, 0xFD, 0xFD, 0xFD, 0x12, 0x34, 0x56, 0x78])
CRIT = ("java", "bedrock")          # 必发布（玩家入口）
OPT = ("query", "rcon", "voice")    # 按需发布


def read(path):
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            return fh.read()
    except OSError:
        return ""


def props(path):
    out = {}
    for ln in read(path).splitlines():
        if "=" in ln and not ln.lstrip().startswith("#"):
            k, v = ln.split("=", 1)
            out[k.strip()] = v.strip()
    return out


def yml_block(text, block, keys):
    """取顶层 yml 块内的指定标量键（不依赖 pyyaml）"""
    out, inside = {}, False
    for ln in text.splitlines():
        if not inside:
            if re.match(r"^%s:\s*(#.*)?$" % re.escape(block), ln):
                inside = True
            continue
        if re.match(r"^\S", ln):
            break
        m = re.match(r"^\s+([A-Za-z0-9_-]+):\s*(\S+)", ln)
        if m and m.group(1) in keys:
            out[m.group(1)] = m.group(2).strip()
    return out


def parse_ports(lst):
    out = []
    for item in lst or []:
        m = re.match(r"^(\d+):(\d+)/(tcp|udp)$", str(item).strip())
        if m:
            out.append({"host": int(m.group(1)), "cont": int(m.group(2)), "proto": m.group(3), "raw": item})
    return out


def expected_ports(data_root, uuid):
    """返回 [(kind, 容器端口, 协议, 依据)]"""
    exp = []
    idir = os.path.join(data_root, "InstanceData", uuid)
    sp = props(os.path.join(idir, "server.properties"))
    jp = int(sp.get("server-port", 25565) or 25565)
    exp.append(("java", jp, "tcp", "server.properties server-port"))
    for gy in sorted(glob.glob(os.path.join(idir, "plugins", "Geyser-*", "config.yml"))):
        b = yml_block(read(gy), "bedrock", ("port", "clone-remote-port"))
        if b.get("port", "").isdigit():
            exp.append(("bedrock", int(b["port"]), "udp",
                        "Geyser bedrock.port (clone-remote-port=%s)" % b.get("clone-remote-port", "?")))
    if str(sp.get("enable-query", "false")).lower() == "true":
        exp.append(("query", int(sp.get("query.port", 25565) or 25565), "udp", "enable-query=true"))
    if str(sp.get("enable-rcon", "false")).lower() == "true":
        exp.append(("rcon", int(sp.get("rcon.port", 25575) or 25575), "tcp", "enable-rcon=true"))
    for vc in glob.glob(os.path.join(idir, "plugins", "voicechat", "*.yml")) + \
              glob.glob(os.path.join(idir, "plugins", "*oice*", "config.yml")):
        m = re.search(r"^\s*port:\s*(\d+)", read(vc), re.M)
        if m:
            exp.append(("voice", int(m.group(1)), "udp", "SimpleVoiceChat"))
            break
    return exp


def varint(n):
    out = b""
    while True:
        b = n & 0x7F
        n >>= 7
        out += bytes([b | 0x80]) if n else bytes([b])
        if not n:
            return out


def read_varint(sock):
    num = shift = 0
    while True:
        b = sock.recv(1)
        if not b:
            raise EOFError("eof")
        num |= (b[0] & 0x7F) << shift
        shift += 7
        if not b[0] & 0x80:
            return num


def probe_java(host, port, proto=765, timeout=6):
    try:
        s = socket.create_connection((host, port), timeout)
        s.settimeout(timeout)
    except OSError as exc:
        return "FAIL %s" % exc
    try:
        hb = host.encode()
        payload = varint(0) + varint(proto) + varint(len(hb)) + hb + struct.pack(">H", port) + varint(1)
        s.sendall(varint(len(payload)) + payload)
        s.sendall(varint(1) + varint(0))
        read_varint(s)
        read_varint(s)
        ln = read_varint(s)
        buf = b""
        while len(buf) < ln:
            chunk = s.recv(ln - len(buf))
            if not chunk:
                break
            buf += chunk
        j = json.loads(buf.decode("utf-8", "ignore"))
        desc = j.get("description")
        if isinstance(desc, dict):
            desc = desc.get("text", "")
        return "OK %s | %s/%s | %s" % (j["version"]["name"], j["players"]["online"], j["players"]["max"], desc)
    except Exception as exc:                                     # noqa: BLE001
        return "FAIL %s: %s" % (type(exc).__name__, exc)
    finally:
        s.close()


def probe_bedrock(host, port, timeout=5):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(timeout)
    pkt = b"\x01" + struct.pack(">Q", int(time.time() * 1000)) + MAGIC + b"\x00" * 8
    try:
        s.sendto(pkt, (host, port))
        data, _ = s.recvfrom(4096)
    except OSError as exc:
        return "FAIL %s" % exc
    finally:
        s.close()
    # 布局: [0]=0x1c [1:9]=时间戳 [9:17]=GUID [17:33]=magic(16B) [33:35]=字符串长度(2B) [35:]=字符串
    txt = data[35:].decode("utf-8", "ignore").strip().rstrip("\x00")
    if txt and not txt.startswith("MCPE"):
        i = txt.find("MCPE")
        if i > 0:
            txt = txt[i:]      # 容错：偏移不对时以 MCPE 锚点纠正，避免出现 `kMCPE` 这类假字节
    return "OK %s" % txt


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    data_root = args[0] if args else "E:/orzmc/mcsmanager/daemon/data"
    instance_dir = os.path.join(data_root, "InstanceConfig")
    if not os.path.isdir(instance_dir):
        print("找不到 InstanceConfig: %s" % instance_dir)
        return 2

    report, gaps, host_used = [], [], {}
    for path in sorted(glob.glob(os.path.join(instance_dir, "*.json"))):
        if ".bak-" in os.path.basename(path):
            continue
        try:
            cfg = json.loads(read(path)) or {}
        except ValueError:
            continue
        if cfg.get("processType") != "docker":
            continue
        uuid = os.path.splitext(os.path.basename(path))[0]
        pub = parse_ports((cfg.get("docker") or {}).get("ports"))
        exp = expected_ports(data_root, uuid)
        rows = []
        for kind, cport, proto, why in exp:
            hit = [p for p in pub if p["cont"] == cport and p["proto"] == proto]
            status = "OK" if hit else "MISSING"
            host_port = hit[0]["host"] if hit else None
            if host_port:
                host_used.setdefault((host_port, proto), []).append("%s/%s" % (cfg.get("nickname", uuid), kind))
            rows.append({"kind": kind, "cont": cport, "proto": proto, "host": host_port,
                         "status": status, "why": why, "need": "必发布" if kind in CRIT else "按需"})
            if status == "MISSING" and kind in CRIT:
                gaps.append("%s(%s) 缺 %s/%s 映射" % (cfg.get("nickname", uuid), uuid[:8], cport, proto))
        report.append({"uuid": uuid, "nickname": cfg.get("nickname", ""), "type": cfg.get("type", ""),
                       "net": (cfg.get("docker") or {}).get("networkMode", ""),
                       "published": pub, "ports": rows})

    for inst in report:
        print("=" * 78)
        print("%s  [%s]  net=%s  uuid=%s" % (inst["nickname"], inst["type"], inst["net"], inst["uuid"][:8]))
        print("  已发布: %s" % (", ".join(p["raw"] for p in inst["published"]) or "(无)"))
        for r in inst["ports"]:
            mark = "✓" if r["status"] == "OK" else ("✗" if r["need"] == "必发布" else "·")
            host = ("宿主 %s/%s" % (r["host"], r["proto"])) if r["host"] else "宿主 —— 未发布"
            print("  %s %-8s %-4s 容器 %-5s -> %-22s %s  | %s"
                  % (mark, r["kind"], r["proto"], r["cont"], host, r["need"], r["why"]))
        if flags and "--probe" in flags:
            for r in inst["ports"]:
                if r["status"] != "OK" or r["kind"] not in CRIT:
                    continue
                fn = probe_java if r["kind"] == "java" else probe_bedrock
                print("  probe %-8s 127.0.0.1:%-5s %s" % (r["kind"], r["host"], fn("127.0.0.1", r["host"])))

    print("=" * 78)
    for (port, proto), who in sorted(host_used.items()):
        if len(who) > 1:
            gaps.append("宿主 %s/%s 冲突: %s" % (port, proto, " vs ".join(who)))
    print("必发布缺口: %s" % ("; ".join(gaps) if gaps else "无 ✓"))
    print("提示: 基岩客户端不支持 SRV，宿主端口即玩家要填的端口；"
          "宿主端口≠容器端口时 Geyser 的 clone-remote-port 必须为 false，"
          "且 RakNet pong 里回报的端口是容器内配置值，不代表宿主端口。")
    if flags and "--json" in flags:
        print(json.dumps({"instances": report, "gaps": gaps}, ensure_ascii=False))
    return 1 if gaps else 0


if __name__ == "__main__":
    sys.exit(main())
