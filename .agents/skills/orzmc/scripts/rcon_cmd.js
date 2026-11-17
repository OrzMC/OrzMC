#!/usr/bin/env node
// 正确协议的 Minecraft RCON 客户端（本地测试服默认 25575/orztest2026）
// 用法: node rcon_cmd.js "<命令>" [port] [password]
// 例:   node rcon_cmd.js "lp group builder permission check worldedit.wand"
// 注意: LP 命令输出走 luckperms-command-executor logger（RCON 响应拿不到）——
//       LP 类命令请改用 bot 通道 /orzdebug $e + 查日志；本脚本适合 tp/save 等无输出命令
const net = require('net');
const [cmd, port = 25575, pwd = 'orztest2026'] = process.argv.slice(2);
function rcon(command) {
  return new Promise((resolve) => {
    const s = net.createConnection(port, '127.0.0.1');
    let buf = Buffer.alloc(0); let reqId = 1; let authed = false;
    s.on('connect', () => {
      const pl = Buffer.concat([Buffer.from(pwd), Buffer.from([0, 0])]);
      const b = Buffer.alloc(12 + pl.length);
      b.writeInt32LE(10 + pl.length, 0); b.writeInt32LE(reqId, 4); b.writeInt32LE(3, 8); pl.copy(b, 12);
      s.write(b); // auth 包: type=3（写死长度会 AUTH FAIL）
    });
    s.on('data', (d) => {
      buf = Buffer.concat([buf, d]);
      while (buf.length >= 4) {
        const len = buf.readInt32LE(0);
        if (buf.length < len + 4) break;
        const id = buf.readInt32LE(4); const type = buf.readInt32LE(8);
        const body = buf.slice(12, 12 + len - 10).toString();
        buf = buf.slice(len + 4);
        if (id === reqId && type === 2 && !authed) {
          authed = true;
          const payload = Buffer.concat([Buffer.from(command), Buffer.from([0, 0])]);
          const b2 = Buffer.alloc(12 + payload.length);
          b2.writeInt32LE(10 + payload.length, 0); b2.writeInt32LE(reqId, 4); b2.writeInt32LE(2, 8); payload.copy(b2, 12);
          s.write(b2); // 命令包: type=2
        } else if (id === reqId && type === 0) { resolve(body); s.end(); }
        else if (type === 2) { resolve('AUTH FAIL'); s.end(); }
      }
    });
    s.on('error', () => resolve('ERR'));
    setTimeout(() => { resolve('SENT(无输出命令)'); s.end(); }, 2500);
  });
}
rcon(cmd).then((r) => { console.log(r); process.exit(0); });
