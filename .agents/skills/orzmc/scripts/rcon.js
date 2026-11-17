#!/usr/bin/env node
// 原生 node RCON 客户端 —— 测 Bot 命令（$ 前缀）自动化时用，shell/python 无法安全传 $v 这类参数
// 用法: node rcon.js <命令> [端口=25575] [密码]
//   node rcon.js "orzdebug $v l" 25575 orztest2026
// 背景（2026-08-07 实测）:
//   - execSync/spawnSync 传 shell 字符串时 $v 被 bash 展开为空 → 服务器收到 "orzdebug  l" 静默无效
//   - RCON 包 length 字段 = id(4) + type(4) + payload + 2 null 的总长（少算 8 字节 → 服务器立即断开）
//   - 本实现不经 shell，$ 原样传递；输出已剥 § 颜色码
const net = require('net');

const CMD = process.argv[2];
if (!CMD) { console.error('用法: node rcon.js <命令> [端口] [密码]'); process.exit(1); }
const PORT = parseInt(process.argv[3] || '25575');
const PASSWORD = process.argv[4] || process.env.RCON_PASSWORD || '';

const sock = net.connect(PORT, '127.0.0.1', () => {
  send(1, 3, PASSWORD);
});

let buffer = Buffer.alloc(0);

function send(id, type, payload) {
  const body = Buffer.alloc(payload.length + 2);
  body.write(payload, 0, 'utf8');
  const pkt = Buffer.alloc(4 + 4 + 4 + body.length);
  pkt.writeInt32LE(body.length + 8, 0); // length = id+type+payload+2null
  pkt.writeInt32LE(id, 4);
  pkt.writeInt32LE(type, 8);
  body.copy(pkt, 12);
  sock.write(pkt);
}

sock.on('data', (d) => {
  buffer = Buffer.concat([buffer, d]);
  while (buffer.length >= 4) {
    const len = buffer.readInt32LE(0);
    if (buffer.length < 4 + len) break;
    const id = buffer.readInt32LE(4);
    const type = buffer.readInt32LE(8);
    const payload = buffer.slice(12, 4 + len - 2).toString('utf8');
    buffer = buffer.slice(4 + len);
    if (id === -1) { console.error('AUTH FAIL'); sock.destroy(); process.exit(1); }
    if (type === 2 && id === 1) { setTimeout(() => send(2, 2, CMD), 100); }
    if (type === 0) { console.log(payload.replace(/§[0-9a-fk-or]/g, '')); sock.destroy(); process.exit(0); }
  }
});

sock.on('error', (e) => { console.error('RCON 错误:', e.message); process.exit(1); });
setTimeout(() => { console.error('TIMEOUT'); sock.destroy(); process.exit(1); }, 10000);
