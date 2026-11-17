// 死亡点箱子回归验证（/execute if block 探测 3x3x3 范围）
// 用法: BOT_PASSWORD=xxx node check-death-chest.js [/tmp/death_pos.json]
// 死亡坐标文件格式: {"x":7,"y":65,"z":-465}（由 bugtest-precise/death3 等脚本写入）
// 判定: 命中数 ≥1 = 箱子存在（回归通过）；0 = 箱子未生成（bug 复现）
// ⚠️ 坑: 本服中文 locale 回显是 "Test passed"/"Test failed"（英文服才是 "Successfully"）——断言必须兼容两者，否则假阴性
const mineflayer = require('mineflayer');
const fs = require('fs');

const posFile = process.argv[2] || '/tmp/death_pos.json';
const pos = JSON.parse(fs.readFileSync(posFile, 'utf8'));
console.log('[CHECK] 检查死亡点:', pos.x, pos.y, pos.z);

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

let successCount = 0;
bot.on('login', () => { bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')); });
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  // /execute if block 回显：中文服 "Test passed" / "Test failed"；英文服 "Successfully"
  if (/Test passed|Successfully|成功/.test(t)) {
    successCount++;
    console.log('[CHECK] ✅ 命中:', t.slice(0, 80));
  }
});

bot.on('spawn', async () => {
  await new Promise(r => setTimeout(r, 3000)); // 等区块

  const blocks = ['minecraft:chest', 'minecraft:trapped_chest', 'minecraft:barrel'];
  for (const b of blocks)
    for (let dx = -1; dx <= 1; dx++)
      for (let dy = -1; dy <= 1; dy++)
        for (let dz = -1; dz <= 1; dz++) {
          bot.chat(`/execute if block ${pos.x+dx} ${pos.y+dy} ${pos.z+dz} ${b}`);
          await new Promise(r => setTimeout(r, 120));
        }
  await new Promise(r => setTimeout(r, 4000)); // 等回显

  console.log(`\n[CHECK] 结果: ${successCount} 个命中（≥1 = 箱子存在）`);
  bot.quit();
  process.exit(0);
});

setTimeout(() => { console.log(`[CHECK] 超时, 命中 ${successCount}`); bot.quit(); process.exit(0); }, 40000);
