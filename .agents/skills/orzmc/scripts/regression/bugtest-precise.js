// 精确验证：死亡+下线后箱子实际位置
// 流程：登录 → 切生存 → give → kill → 立即下线 → 输出死亡坐标
// 检查脚本改用 DeathChest hologram 日志位置查箱子
const mineflayer = require('mineflayer');
const fs = require('fs');

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
  console.log('[PRECISE] spawn:', bot.entity.position.x.toFixed(1), bot.entity.position.y.toFixed(1), bot.entity.position.z.toFixed(1));

  bot.chat('/minecraft:gamemode survival HermesBot');
  await new Promise(r => setTimeout(r, 1500));
  bot.chat('/minecraft:give HermesBot diamond 5');
  await new Promise(r => setTimeout(r, 2000));

  const p = bot.entity.position;
  console.log('[PRECISE] kill 前位置:', p.x.toFixed(1), p.y.toFixed(1), p.z.toFixed(1));
  fs.writeFileSync('/tmp/death_pos.json', JSON.stringify({ x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z) }));
  console.log('[PRECISE] 死亡坐标已存');

  bot.chat('/minecraft:kill');
  await new Promise(r => setTimeout(r, 2000));  // 等 kill 送达
  bot.quit();
  console.log('[PRECISE] 已下线（kill 后 2s）');
  setTimeout(() => process.exit(0), 500);
});

setTimeout(() => { console.log('[PRECISE] 超时'); process.exit(0); }, 20000);
