#!/usr/bin/env python3
"""Minecraft 服务器连通性 + 延迟探测（DNS/TCP/ICMP/MC 协议握手）
用法: python3 mc_ping_probe.py [host] [port]   默认 {SERVER_HOST}:25565
注意: 本机 Shadowrocket TUN 接管流量时 TCP/ICMP 延迟是虚拟网卡假象（0.x ms），
      MC 握手 JSONDecodeError = 服务器离线或代理转发异常；真实连通性以实际数据流为准
      （如 MCSM API 下载成功）。真实 IP 用公共 DNS: dig +short <host> @223.5.5.5
"""
import socket, struct, json, time, subprocess, sys

HOST = sys.argv[1] if len(sys.argv) > 1 else "{SERVER_HOST}"
PORT = int(sys.argv[2]) if len(sys.argv) > 2 else 25565

def dns_lookup(host):
    try:
        infos = socket.getaddrinfo(host, PORT, socket.AF_UNSPEC, socket.SOCK_STREAM)
        return sorted({i[4][0] for i in infos})
    except Exception as e:
        return f"DNS 解析失败: {e}"

def tcp_connect(host, port, timeout=5):
    t0 = time.time()
    try:
        s = socket.create_connection((host, port), timeout=timeout)
        rtt = (time.time() - t0) * 1000
        s.close()
        return True, rtt
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"

def varint(n):
    out = b""
    while True:
        b = n & 0x7F
        n >>= 7
        out += bytes([b | 0x80]) if n else bytes([b])
        if not n:
            return out

def send_packet(s, payload):
    s.sendall(varint(len(payload)) + payload)

def recv_packet(s):
    def read_varint():
        result, shift = 0, 0
        while True:
            b = s.recv(1)
            if not b:
                raise ConnectionError("连接被关闭")
            val = b[0]
            result |= (val & 0x7F) << shift
            if not (val & 0x80):
                return result
            shift += 7
    length = read_varint()
    data = b""
    while len(data) < length:
        chunk = s.recv(length - len(data))
        if not chunk:
            raise ConnectionError("连接被关闭")
        data += chunk
    return data

def mc_status(host, port, timeout=6):
    """Server List Ping: protocol=776 (MC 26.2)"""
    try:
        t0 = time.time()
        s = socket.create_connection((host, port), timeout=timeout)
        host_b = host.encode()
        hs = b"\x00" + varint(776) + varint(len(host_b)) + host_b + struct.pack(">H", port) + b"\x01"
        send_packet(s, hs)
        send_packet(s, b"\x00")
        data = recv_packet(s)
        rtt = (time.time() - t0) * 1000
        # 26.2+ status 响应可能带帧头（如 \xe9\x01\x00\xe6\x01），定位 { 起点解析
        i = data.find(b"{")
        if i < 0:
            raise ValueError(f"响应中无 JSON: {data[:40]!r}")
        info = json.loads(data[i:].decode("utf-8", errors="replace"))
        s.close()
        return True, rtt, info
    except Exception as e:
        return False, f"{type(e).__name__}: {e}", None

def icmp_ping(host, count=4):
    try:
        r = subprocess.run(["ping", "-c", str(count), "-t", "6", host], capture_output=True, text=True, timeout=20)
        out = r.stdout + r.stderr
        for line in out.splitlines():
            if "round-trip" in line or "min/avg/max" in line or "统计" in line:
                return line.strip()
        return out.strip().splitlines()[-1] if out.strip() else "(无输出)"
    except Exception as e:
        return f"ping 失败: {e}"

print(f"=== 探测 {HOST}:{PORT} ===")
print(f"[1] DNS: {dns_lookup(HOST)}")
print(f"[2] ICMP: {icmp_ping(HOST)}")
print("[3] TCP x3:")
for i in range(3):
    ok, rtt = tcp_connect(HOST, PORT)
    print(f"    {i+1}: {'✅ ' + f'{rtt:.1f}ms' if ok else '❌ ' + rtt}")
print("[4] MC 握手:")
ok, rtt, info = mc_status(HOST, PORT)
if ok:
    print(f"    ✅ 在线 {rtt:.1f}ms")
    v, p = info.get("version", {}), info.get("players", {})
    print(f"    版本 {v.get('name')} | 玩家 {p.get('online')}/{p.get('max')}")
    desc = info.get("description", {})
    print(f"    MOTD: {(desc.get('text') if isinstance(desc, dict) else str(desc))[:80]}")
else:
    print(f"    ❌ {rtt}  (JSONDecodeError ≈ 服务器离线/代理转发异常)")
