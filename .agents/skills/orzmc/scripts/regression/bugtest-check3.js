// DeathChest 复现检查 v3：登录后监听 /execute if block 回显
// 回显格式（英文服）: "Successfully executed ..." 或 "但找到了"（中文服）
// 目标：确认死亡点 3x3x3 是否 chest/trapped_chest/barrel
const mineflayer = require('mineflayer');
const fs = require('fs');

const pos = JSON.parse(fs.readFileSync('/tmp/death_pos.json', 'utf8'));
console.log('[CHECK3] 死亡点:', pos.x, pos.y, pos.z);

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

let loggedIn = false;
let successCount = 0;
let failures = [];

bot.on('login', () => { bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')); });
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (t.includes('登录成功')) { loggedIn = true; }
  // /execute if block 回显：中文服 "Test passed" / "Test failed"（英文服 "Successfully"）
  if (/Test passed|Successfully|成功/.test(t)) {
    successCount++;
    console.log('[CHECK3] ✅ 命中:', t.slice(0, 80));
  }
  if (/Test failed|没有找到|未找到|找不到/.test(t)) {
    failures.push(t.slice(0, 60));
  }
});

bot.on('spawn', async () => {
  await new Promise(r => setTimeout(r, 3000)); // 等区块

  const blocks = ['minecraft:chest', 'minecraft:trapped_chest', 'minecraft:barrel'];
  const checks = [];
  for (const b of blocks)
    for (let dx = -1; dx <= 1; dx++)
      for (let dy = -1; dy <= 1; dy++)
        for (let dz = -1; dz <= 1; dz++)
          checks.push([b, pos.x+dx, pos.y+dy, pos.z+dz]);

  console.log(`[CHECK3] 共 ${checks.length} 个查询，开始...`);
  for (const [b, x, y, z] of checks) {
    bot.chat(`/execute if block ${x} ${y} ${z} ${b}`);
    await new Promise(r => setTimeout(r, 120));
  }
  await new Promise(r => setTimeout(r, 4000)); // 等所有回显

  console.log(`\n[CHECK3] 结果: ${successCount} 个成功命中（箱子存在）`);
  if (successCount === 0) {
    console.log('[CHECK3] 🔴 死亡点 3x3x3 无任何箱子/木桶 → 箱子未生成！');
  }
  bot.quit();
  process.exit(0);
});

setTimeout(() => { console.log(`[CHECK3] 超时, 已命中 ${successCount}`); process.exit(0); }, 40000);
