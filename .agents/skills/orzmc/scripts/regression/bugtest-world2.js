// 跨世界验证：用 /execute in <world> run data get 或直接查各世界箱子
// 简单方式：进入下界再 kill（用 setblock 传送门? 太复杂）
// 直接验证：命令 `execute in minecraft:the_nether run data get ...` 
const mineflayer = require('mineflayer');
const fs = require('fs');

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

let started = false;
const results = [];
bot.on('login', () => { bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')); });
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (/Test passed|Test failed|world/.test(t)) { results.push(t.slice(0, 80)); console.log('[WORLD2]', t.slice(0, 80)); }
});

bot.on('spawn', async () => {
  if (started) return;
  started = true;
  await new Promise(r => setTimeout(r, 3000));

  // 用 /execute in 查箱子（跨世界检测）
  bot.chat('/execute in minecraft:the_nether run execute if block 100 61 100 minecraft:chest');
  await new Promise(r => setTimeout(r, 2000));
  bot.chat('/execute in minecraft:overworld run execute if block 100 61 100 minecraft:chest');
  await new Promise(r => setTimeout(r, 2000));
  console.log('[WORLD2] 查询完成, 结果数:', results.length);
  bot.quit();
  setTimeout(() => process.exit(0), 500);
});

setTimeout(() => { process.exit(0); }, 20000);
