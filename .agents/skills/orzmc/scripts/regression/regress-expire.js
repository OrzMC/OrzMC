// 精确查指定坐标的箱子（绕过 check3 误报）
const mineflayer = require('mineflayer');
const fs = require('fs');

const pos = JSON.parse(fs.readFileSync('/tmp/death_pos.json', 'utf8'));
console.log('[EXPIRE] 目标死亡点:', pos.x, pos.y, pos.z);

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

let started = false;
bot.on('login', () => { bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')); });
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (/Test passed|Test failed/.test(t)) console.log('[EXPIRE]', t.slice(0, 40));
});

bot.on('spawn', async () => {
  if (started) return;
  started = true;
  await new Promise(r => setTimeout(r, 3000));
  // 查死亡点 3x3x3 所有 chest
  for (let dx = -1; dx <= 1; dx++)
    for (let dy = -1; dy <= 1; dy++)
      for (let dz = -1; dz <= 1; dz++) {
        bot.chat(`/execute if block ${pos.x+dx} ${pos.y+dy} ${pos.z+dz} minecraft:chest`);
        await new Promise(r => setTimeout(r, 250));
      }
  await new Promise(r => setTimeout(r, 2000));
  bot.quit();
  setTimeout(() => process.exit(0), 500);
});

setTimeout(() => { process.exit(0); }, 25000);
