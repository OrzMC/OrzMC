// 用 /data get block 读箱子 NBT 验证物品（绕开开箱保护）
const mineflayer = require('mineflayer');
const fs = require('fs');

const pos = JSON.parse(fs.readFileSync('/tmp/death_pos.json', 'utf8'));
console.log('[DATA] 检查箱子 @', pos.x, pos.y, pos.z);

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

let started = false;
let foundChest = null;

bot.on('login', () => { bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')); });
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (/diamond|Diamond|钻石/.test(t)) console.log('[DATA] 📦 物品回显:', t.slice(0, 120));
  if (/has the following block data|方块数据/.test(t)) console.log('[DATA] 方块数据:', t.slice(0, 200));
});

bot.on('spawn', async () => {
  if (started) return;
  started = true;
  await new Promise(r => setTimeout(r, 3000));

  const { Vec3 } = require('vec3');
  for (let dx = -1; dx <= 1 && !foundChest; dx++)
    for (let dy = -1; dy <= 1 && !foundChest; dy++)
      for (let dz = -1; dz <= 1 && !foundChest; dz++) {
        const b = bot.blockAt(new Vec3(pos.x + dx, pos.y + dy, pos.z + dz));
        if (b && b.name === 'chest') foundChest = { x: pos.x + dx, y: pos.y + dy, z: pos.z + dz };
      }

  if (!foundChest) { console.log('[DATA] ❌ 无箱子'); bot.quit(); process.exit(0); return; }
  console.log('[DATA] ✅ 箱子在', foundChest);

  // 读箱子 NBT（items 列表）
  bot.chat(`/minecraft:data get block ${foundChest.x} ${foundChest.y} ${foundChest.z} Items`);
  await new Promise(r => setTimeout(r, 2500));
  console.log('[DATA] 查询完成');
  bot.quit();
  process.exit(0);
});

setTimeout(() => { console.log('[DATA] 超时'); bot.quit(); process.exit(0); }, 25000);
