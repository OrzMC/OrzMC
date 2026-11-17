// 并发压力测试：3 个 bot 同时死亡+下线（间隔错开但重叠）
// 每 bot: 登录 → 生存 → give → kill → 2s 下线 → 记录坐标
const mineflayer = require('mineflayer');
const fs = require('fs');

const NAMES = ['HermesBot', 'joker', 'TestPlayer'];
const results = [];
const deathPositions = [];

function spawnBot(name, index) {
  return new Promise((resolve) => {
    const bot = mineflayer.createBot({
      host: '127.0.0.1', port: 25565, username: name,
      auth: 'offline', version: '1.21.11', hideErrors: true,
    });
    let started = false;

    bot.on('login', () => {
      // 首次登录需注册+登录
      bot.chat('/register ' + (process.env.BOT_PASSWORD || 'changeMe123') + ' ' + (process.env.BOT_PASSWORD || 'changeMe123'));
      setTimeout(() => bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')), 1500);
    });

    bot.on('message', (msg) => {
      const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
      if (/登录成功|registered|注册成功/.test(t)) console.log(`[${name}] 登录成功`);
      if (/已经登录|already logged in/.test(t)) console.log(`[${name}] 已登录`);
    });

    bot.on('spawn', async () => {
      if (started) return;
      started = true;
      await new Promise(r => setTimeout(r, 1000 + index * 300)); // 错开 300ms
      bot.chat('/minecraft:gamemode survival ' + name);
      await new Promise(r => setTimeout(r, 1200));
      bot.chat('/minecraft:give ' + name + ' diamond 5');
      await new Promise(r => setTimeout(r, 1500));

      const p = bot.entity.position;
      const dp = { x: Math.floor(p.x), y: Math.floor(p.y), z: Math.floor(p.z), bot: name };
      deathPositions.push(dp);
      console.log(`[${name}] 死亡坐标: ${dp.x},${dp.y},${dp.z}`);

      bot.chat('/minecraft:kill');
      await new Promise(r => setTimeout(r, 2000));
      bot.quit();
      console.log(`[${name}] 已下线`);
      resolve(dp);
    });

    bot.on('end', () => {
      if (!started) resolve(null);
    });

    setTimeout(() => {
      if (!started) { console.log(`[${name}] 超时`); bot.quit(); resolve(null); }
    }, 25000);
  });
}

async function main() {
  console.log('=== 并发压力测试：3 bot 同时死亡+下线 ===');
  // 全部同时启动
  const all = await Promise.all(NAMES.map((n, i) => spawnBot(n, i)));
  const ok = all.filter(x => x !== null);
  console.log(`\n=== 完成：${ok.length}/3 bot 成功死亡下线 ===`);
  fs.writeFileSync('/tmp/stress_positions.json', JSON.stringify(deathPositions, null, 2));
  console.log('死亡坐标已存 /tmp/stress_positions.json');
  process.exit(0);
}

main();
