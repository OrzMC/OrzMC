// node 原生 RCON 客户端（正确 length 语义，可直接复用）
// 用法: node rcon-node.js '<命令>' [密码] [端口]
// 示例: node rcon-node.js 'orzdebug $v l' orztest2026 25575
// 关键点:
//   - 不经 shell（数组 spawn/直接 node 运行），$ 不会被展开 —— 避免 python 子进程环境差异
//   - length 字段 = id(4) + type(4) + payload + 2 null 的总长（payload.length + 10），
//     漏算 8 字节头部会导致服务器立即断连（struct.error: unpack requires a buffer of 4 bytes）
//   - 认证响应 type=2，命令响应 type=0
const net = require('net');

const CMD = process.argv[2] || 'list';
const PASSWORD = process.argv[3] || 'orztest2026';
const PORT = parseInt(process.argv[4] || '25575');

function send(sock, id, type, payload) {
  const body = Buffer.alloc(payload.length + 2);
  body.write(payload, 0, 'utf8');
  // RCON length = id(4) + type(4) + payload + 2 null 的总长
  const pkt = Buffer.alloc(4 + 4 + 4 + body.length);
  pkt.writeInt32LE(body.length + 8, 0);
  pkt.writeInt32LE(id, 4);
  pkt.writeInt32LE(type, 8);
  body.copy(pkt, 12);
  sock.write(pkt);
}

const sock = net.connect(PORT, '127.0.0.1', () => send(sock, 1, 3, PASSWORD));
let buffer = Buffer.alloc(0);

sock.on('data', (d) => {
  buffer = Buffer.concat([buffer, d]);
  while (buffer.length >= 4) {
    const len = buffer.readInt32LE(0);
    if (buffer.length < 4 + len) break;
    const id = buffer.readInt32LE(4);
    const type = buffer.readInt32LE(8);
    const payload = buffer.slice(12, 4 + len - 2).toString('utf8');
    buffer = buffer.slice(4 + len);
    if (id === -1) { console.error('AUTH FAIL'); process.exit(1); }
    if (type === 2 && id === 1) setTimeout(() => send(sock, 2, 2, CMD), 100);
    if (type === 0) { console.log(payload.replace(/§[0-9a-fk-or]/g, '').trim()); sock.destroy(); process.exit(0); }
  }
});
sock.on('error', (e) => { console.error('RCON error:', e.message); process.exit(1); });
setTimeout(() => { console.error('TIMEOUT'); process.exit(1); }, 10000);
