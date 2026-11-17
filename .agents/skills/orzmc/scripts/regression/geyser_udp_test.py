#!/usr/bin/env python3
"""Geyser UDP 握手测试：发送 RakNet Unconnected Ping (0x01) 验证服务响应
RakNet 协议：magic 0x00ffff00fefefefefdfdfdfd12345678 + ping time (8 bytes) + client GUID (8 bytes)
"""
import socket
import struct
import time

HOST = '127.0.0.1'
PORT = 19132

MAGIC = bytes.fromhex('00ffff00fefefefefdfdfdfd12345678')

def raknet_ping():
    # 构建 Unconnected Ping 包
    packet = b'\x01' + struct.pack('>q', int(time.time() * 1000)) + MAGIC + struct.pack('>q', 0x1234567890ABCDEF)
    
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(5)
    try:
        s.sendto(packet, (HOST, PORT))
        data, addr = s.recvfrom(4096)
        print(f"✅ 收到响应 ({len(data)} bytes) from {addr}")
        
        # 解析响应
        if data[0] == 0x1c:  # Unconnected Pong
            print("✅ 包类型: Unconnected Pong (0x1c)")
            # 找到 MAGIC 位置
            idx = data.find(MAGIC)
            if idx != -1:
                # 服务器 GUID (8 bytes after magic)
                server_guid = struct.unpack('>q', data[idx+16:idx+24])[0]
                # 剩余是 server name 字符串（长度前缀）
                name_len = data[idx+24]
                server_name = data[idx+25:idx+25+name_len].decode('utf-8', errors='replace')
                print(f"✅ 服务器 GUID: {server_guid:#x}")
                print(f"✅ 服务器名: {server_name}")
                return True
        else:
            print(f"⚠️ 响应包类型: 0x{data[0]:02x}（非预期）")
            print(f"   原始数据: {data[:60].hex()}")
    except socket.timeout:
        print("❌ 超时：UDP 19132 无响应")
    except Exception as e:
        print(f"❌ 错误: {e}")
    finally:
        s.close()
    return False

if __name__ == '__main__':
    print(f"=== RakNet UDP 握手测试 {HOST}:{PORT} ===")
    ok = raknet_ping()
    print("\n结论:", "🟢 基岩入口正常" if ok else "🔴 无响应，需排查")
