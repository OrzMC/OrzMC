// 阶段4：跨世界死亡测试（下界/末地）→ 验证建箱+坐标记录
// 用法: node bugtest-world.js <nether|end>
const mineflayer = require('mineflayer');
const fs = require('fs');

const worldArg = process.argv[2] || 'nether';
const worldCmd = worldArg === 'end' ? 'minecraft:the_end' : 'minecraft:the_nether';
console.log('[WORLD] 目标世界:', worldArg);

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

let started = false;
bot.on('login', () => { bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')); });

bot.on('spawn', async () => {
  if (started) return;
  started = true;
  await new Promise(r => setTimeout(r, 1500));
  console.log('[WORLD] spawn:', bot.entity.position.x.toFixed(1), bot.entity.position.y.toFixed(1), bot.entity.position.z.toFixed(1), '| world:', bot.game.dimension);

  bot.chat('/minecraft:gamemode survival HermesBot');
  await new Promise(r => setTimeout(r, 1500));
  bot.chat('/minecraft:give HermesBot diamond 5');
  await new Promise(r => setTimeout(r, 2000));

  // tp 到目标世界
  bot.chat(`/minecraft:execute in ${worldCmd} run tp HermesBot 100 80 100`);
  await new Promise(r => setTimeout(r, 4000));
  console.log('[WORLD] 已传送, 当前位置:', bot.entity.position.x.toFixed(1), bot.entity.position.y.toFixed(1), bot.entity.position.z.toFixed(1), '| world:', bot.game.dimension);

  const p = bot.entity.position;
  fs.writeFileSync('/tmp/death_pos.json', JSON.stringify({ x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z), world: worldArg }));
  console.log('[WORLD] 死亡坐标已存 (', worldArg, ')');

  bot.chat('/minecraft:kill');
  await new Promise(r => setTimeout(r, 2000));
  bot.quit();
  console.log('[WORLD] 已下线');
  setTimeout(() => process.exit(0), 500);
});

setTimeout(() => { console.log('[WORLD] 超时'); process.exit(0); }, 25000);
