#!/usr/bin/env node
// 传送门 transfer 测试：node portal-transfer-test.js [端口] [中心x] [中心y] [中心z]
// 验证 bot 能否触发 PlayerPortalEvent → 插件 transfer
// ⚠️ 已知结论（2026-08-06 实测）：mineflayer 位置同步与服务器端不一致，
//    即使 tp 到传送门正中心也不触发 PlayerPortalEvent —— 真实玩家验证是唯一可靠方式。
//    本脚本仅用于"跳+前进穿过 portal 方块"场景的服务端链路观察（原版传送 vs 插件 transfer）。
const mineflayer = require('mineflayer');
const { pathfinder, Movements, goals } = require('mineflayer-pathfinder');

const PORT = parseInt(process.argv[2] || '25565');
const CX = parseFloat(process.argv[3] || '30.5');
const CY = parseFloat(process.argv[4] || '66');
const CZ = parseFloat(process.argv[5] || '-454.5');
const HOST = process.argv[6] || '{LAN_IP}';
const BOT_NAME = process.argv[7] || 'HermesBot';
const BOT_PASS = process.env.BOT_PASS || '{BOT_PASSWORD}';

const bot = mineflayer.createBot({
  host: HOST, port: PORT, username: BOT_NAME,
  auth: 'offline', version: '1.21.11', hideErrors: true,
});
bot.loadPlugin(pathfinder);

bot.on('message', (m) => {
  const t = m.toString().replace(/§[0-9a-fk-or]/g, '');
  if (t.includes('传送') || t.includes('transfer') || t.includes('Transfer')) {
    console.log('[CHAT]', t);
  }
});

let phase = 0;
bot.on('spawn', () => {
  phase++;
  console.log(`[SPAWN#${phase}] @`,
    bot.entity.position.x.toFixed(1), bot.entity.position.y.toFixed(1),
    bot.entity.position.z.toFixed(1), 'dim:', bot.game.dimension);
  if (phase === 1) {
    setTimeout(() => { bot.chat(`/login ${BOT_PASS}`); }, 2000);
    // tp 到传送门前 1 格，面向 portal 方向跳+前进（yaw=π → +z）
    setTimeout(() => { bot.chat(`/tp ${CX} ${CY - 2} ${CZ - 1}`); }, 5000);
    setTimeout(() => {
      const p = bot.entity.position;
      console.log('[TP] @', p.x.toFixed(2), p.y.toFixed(2), p.z.toFixed(2));
      bot.look(Math.PI, 0, true).then(() => {
        console.log('[JUMP+GO] 面向 +z 跳+前进...');
        bot.setControlState('jump', true);
        bot.setControlState('forward', true);
        setTimeout(() => {
          bot.setControlState('jump', false);
          bot.setControlState('forward', false);
          const p2 = bot.entity.position;
          console.log('[JUMP-END] @', p2.x.toFixed(2), p2.y.toFixed(2), p2.z.toFixed(2),
            'dim:', bot.game.dimension);
        }, 400);
      });
    }, 8000);
  }
});

bot.on('kicked', (r) => {
  console.log('[KICKED]', r.toString().replace(/§[0-9a-fk-or]/g, ''));
  process.exit(0);
});
bot.on('end', () => { console.log('[END] 断开'); process.exit(0); });
setTimeout(() => process.exit(1), 25000);
