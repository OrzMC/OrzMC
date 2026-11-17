// RCON 批量执行 lp 命令（Paper 协议：2 字节尾部 padding）
// 用法: node rcon_batch.js <密码> <命令文件>
// 命令文件：每行一条 lp 命令（# 开头为注释）
// 注意：Paper RCON 响应体可能为空（命令生效但输出不可见）——
//   验证用 lp group X perm info 等事后查询（群 $e 通道进 latest.log）
const net = require('net');
const fs = require('fs');

const HOST = process.env.RCON_HOST || '127.0.0.1';
const PORT = parseInt(process.env.RCON_PORT || '25575', 10);
const PASS = process.argv[2];
const FILE = process.argv[3];
const cmds = fs.readFileSync(FILE, 'utf8').split('\n').map(l => l.trim()).filter(l => l && !l.startsWith('#'));

let buf = Buffer.alloc(0);
let reqId = 0;
const pending = new Map();

const sock = net.connect(PORT, HOST);

function send(type, payload) {
    const id = ++reqId;
    const body = Buffer.from(payload, 'utf8');
    // Paper RCON: len = 4(id) + 4(type) + body + 2(padding) —— 注意是 2 字节不是 1
    const len = 4 + 4 + body.length + 2;
    const pkt = Buffer.alloc(len + 4);
    pkt.writeInt32LE(len, 0);
    pkt.writeInt32LE(id, 4);
    pkt.writeInt32LE(type, 8);
    body.copy(pkt, 12);
    pkt.writeInt16LE(0, 12 + body.length);
    sock.write(pkt);
    return id;
}

sock.on('data', d => {
    buf = Buffer.concat([buf, d]);
    while (buf.length >= 4) {
        const len = buf.readInt32LE(0);
        if (len <= 0 || buf.length < 4 + len) break;
        const id = buf.readInt32LE(4);
        const body = buf.slice(12, 4 + len - 2).toString('utf8');
        buf = buf.slice(4 + len);
        if (id === 0) continue; // server event
        const cb = pending.get(id);
        if (cb) { pending.delete(id); cb(body); }
    }
});

sock.on('error', e => { console.error('ERR', e.message); process.exit(1); });

let idx = 0, ok = 0, fail = 0;

function next() {
    if (idx >= cmds.length) {
        console.log(`\nDONE ok=${ok} fail=${fail} total=${cmds.length}`);
        sock.end();
        process.exit(0);
    }
    const c = cmds[idx++];
    const id = send(2, c);
    pending.set(id, body => {
        const t = body.trim();
        if (/unknown|错误|失败|not found|不存在|usage/i.test(t)) {
            fail++;
            console.log(`[FAIL] ${c} → ${t.slice(0, 100)}`);
        } else {
            ok++;
            console.log(`[OK] ${c}${t ? ' → ' + t.slice(0, 60) : ''}`);
        }
        setTimeout(next, 150);
    });
}

sock.on('connect', () => {
    const id = send(3, PASS);
    pending.set(id, body => {
        console.log('AUTH OK');
        next();
    });
});
