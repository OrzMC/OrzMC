#!/usr/bin/env node
// 传送门测试 - 方块探测器：node portal-probe.js [端口] [中心x] [中心y] [中心z]
// 用 bot blockAt 扫描传送门区域，列出 portal/obsidian/gold_block 方块位置
// 示例:
//   node portal-probe.js 25565 30 66 -454   # 主服传送门
//   node portal-probe.js 25566 30 66 -457   # 第二服传送门
const mineflayer = require('mineflayer');
const vec3 = require('vec3');

const PORT = parseInt(process.argv[2] || '25565');
const CX = parseInt(process.argv[3] || '30');
const CY = parseInt(process.argv[4] || '66');
const CZ = parseInt(process.argv[5] || '-454');
const HOST = process.argv[6] || '{LAN_IP}';
const BOT_NAME = process.argv[7] || 'HermesBot';
const BOT_PASS = process.env.BOT_PASS || '{BOT_PASSWORD}';

const bot = mineflayer.createBot({
  host: HOST, port: PORT, username: BOT_NAME,
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

bot.on('spawn', () => {
  setTimeout(() => { bot.chat(`/login ${BOT_PASS}`); }, 2000);
  setTimeout(() => { bot.chat(`/tp ${CX} ${CY} ${CZ}`); }, 5000);
  setTimeout(() => {
    console.log('[POS]', bot.entity.position.x.toFixed(1),
      bot.entity.position.y.toFixed(1), bot.entity.position.z.toFixed(1));
    // 扫描传送门区域（±3 格）
    let found = 0;
    for (let y = CY - 3; y <= CY + 3; y++) {
      for (let x = CX - 3; x <= CX + 3; x++) {
        for (let dz = -3; dz <= 3; dz++) {
          const b = bot.blockAt(vec3(x, y, CZ + dz));
          if (b && ['nether_portal', 'obsidian', 'gold_block'].includes(b.name)) {
            console.log(`[BLOCK] ${x} ${y} ${CZ + dz} = ${b.name}`);
            found++;
          }
        }
      }
    }
    console.log(`[FOUND] ${found} 个相关方块`);
    bot.end(); process.exit(0);
  }, 9000);
});

bot.on('kicked', (r) => {
  console.log('[KICKED]', r.toString().replace(/§[0-9a-fk-or]/g, ''));
  process.exit(0);
});
setTimeout(() => process.exit(1), 15000);
