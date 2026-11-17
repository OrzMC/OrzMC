// DeathChest bug 复现 v4：最小化客户端依赖
// 方案：切生存 → give 物品 → 记录坐标 → /minecraft:kill → 立即 quit
// 不监听 death 事件（避免粒子崩溃），kill 后固定 1.5s 内断线
const mineflayer = require('mineflayer');
const fs = require('fs');

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

let loggedIn = false;
let step = 0;

bot.on('login', () => { bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')); });
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (t.includes('登录成功')) { loggedIn = true; console.log('[BUGTEST] ✅ 已登录'); }
});

bot.on('spawn', async () => {
  // spawn 已触发 = 已登录，无需等 message
  console.log('[BUGTEST] spawn, 位置:', bot.entity.position.x.toFixed(1), bot.entity.position.y.toFixed(1), bot.entity.position.z.toFixed(1));
  await new Promise(r => setTimeout(r, 1500));

  // 1. 切生存
  bot.chat('/minecraft:gamemode survival HermesBot');
  await new Promise(r => setTimeout(r, 1500));

  // 2. give 物品
  bot.chat('/minecraft:give HermesBot diamond 5');
  await new Promise(r => setTimeout(r, 2000));
  console.log('[BUGTEST] give 完成');

  // 3. 记录坐标
  const p = bot.entity.position;
  fs.writeFileSync('/tmp/death_pos.json', JSON.stringify({ x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z) }));
  console.log('[BUGTEST] 死亡点坐标已存:', Math.floor(p.x), Math.floor(p.y), Math.floor(p.z));

  // 4. kill（服务器日志会显示 Killed）+ 立即 quit
  console.log('[BUGTEST] 执行 kill + 立即下线...');
  bot.chat('/minecraft:kill');
  await new Promise(r => setTimeout(r, 800));  // 800ms 内断线（模拟"死亡瞬间下线"）
  bot.quit();
  console.log('[BUGTEST] ✅ 已下线（死亡后 800ms 断线）');
  setTimeout(() => process.exit(0), 500);
});

bot.on('kicked', (r) => { console.log('[BUGTEST] 被踢:', r.toString().slice(0, 80)); process.exit(1); });
setTimeout(() => { console.log('[BUGTEST] 超时'); process.exit(0); }, 20000);
