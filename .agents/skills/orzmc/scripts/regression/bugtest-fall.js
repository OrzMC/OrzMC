// DeathChest 触发确认：用【坠落】死亡（真实死亡，非 kill 命令）
// 捕获 player-notification "put into a chest" 消息 + 检查箱子
// 流程：切生存 → give → tp 高空坠落 → 保持在线 → 听通知 + 查箱子
const mineflayer = require('mineflayer');
const fs = require('fs');

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

let loggedIn = false;
let started = false;
let died = false;
let notified = false;
let successCount = 0;

bot.on('login', () => { bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')); });
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (t.includes('登录成功')) { loggedIn = true; }
  if (/chest|箱子|put into/.test(t)) {
    notified = true;
    console.log('[FALL] 📦 收到箱子通知:', t.slice(0, 100));
  }
  if (/Successfully|成功/.test(t)) { successCount++; console.log('[FALL] ✅ 命中:', t.slice(0, 60)); }
  if (/你死了|fell from|died/.test(t)) console.log('[FALL] 死亡消息:', t.slice(0, 80));
});

bot.on('spawn', async () => {
  if (started) return;  // 防止 respawn 重复执行
  started = true;
  await new Promise(r => setTimeout(r, 1500));
  console.log('[FALL] spawn:', bot.entity.position.x.toFixed(1), bot.entity.position.y.toFixed(1), bot.entity.position.z.toFixed(1));

  bot.chat('/minecraft:gamemode survival HermesBot');
  await new Promise(r => setTimeout(r, 1500));
  bot.chat('/minecraft:give HermesBot diamond 5');
  await new Promise(r => setTimeout(r, 2000));
  console.log('[FALL] give 完成');

  const sx = Math.floor(bot.entity.position.x), sz = Math.floor(bot.entity.position.z);
  console.log(`[FALL] tp 到高空 (${sx}, 200, ${sz}) 坠落...`);
  bot.chat(`/minecraft:tp ${sx} 200 ${sz}`);
  await new Promise(r => setTimeout(r, 1500));

  // 等坠落+死亡（约 5-8s）
  console.log('[FALL] 等待坠落死亡 + 保持在线...');
  await new Promise(r => setTimeout(r, 10000));

  const p = bot.entity.position;
  fs.writeFileSync('/tmp/death_pos.json', JSON.stringify({ x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z) }));
  console.log(`[FALL] 当前坐标: ${Math.floor(p.x)} ${Math.floor(p.y)} ${Math.floor(p.z)}`);

  // 查询箱子
  const blocks = ['minecraft:chest', 'minecraft:trapped_chest', 'minecraft:barrel'];
  for (const b of blocks)
    for (let dx = -1; dx <= 1; dx++)
      for (let dy = -1; dy <= 1; dy++)
        for (let dz = -1; dz <= 1; dz++) {
          bot.chat(`/execute if block ${Math.floor(p.x)+dx} ${Math.floor(p.y)+dy} ${Math.floor(p.z)+dz} ${b}`);
          await new Promise(r => setTimeout(r, 100));
        }
  await new Promise(r => setTimeout(r, 4000));
  console.log(`\n[FALL] 总结: 收到箱子通知=${notified}, 箱子命中=${successCount}`);
  bot.quit();
  process.exit(0);
});

setTimeout(() => { console.log(`[FALL] 超时, 通知=${notified}, 命中=${successCount}`); process.exit(0); }, 45000);
