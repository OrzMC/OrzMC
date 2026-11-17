// 验证房子 v4：门在南墙 z=-469（正面），屋顶在 y=68
const mineflayer = require('mineflayer');
const { Vec3 } = require('vec3');

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: false,
});

let loggedIn = false;
bot.on('login', () => { bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')); });
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (t.includes('登录成功')) { loggedIn = true; console.log('[TEST] ✅ 已登录'); }
});

bot.on('spawn', async () => {
  for (let i = 0; i < 20 && !loggedIn; i++) await new Promise(r => setTimeout(r, 500));
  bot.chat('/minecraft:tp 23 66 -472');
  await new Promise(r => setTimeout(r, 2500));
  await new Promise(r => setTimeout(r, 2000)); // 额外等区块

  const checks = [
    ['门(南墙z=-469) 下层', new Vec3(23, 65, -469), 'oak_door'],
    ['门上方(南墙z=-469)', new Vec3(23, 66, -469), 'oak_door'],
    ['南墙窗西', new Vec3(21, 66, -469), 'glass'],
    ['南墙窗东', new Vec3(25, 66, -469), 'glass'],
    ['屋顶中心(y=69)', new Vec3(23, 69, -472), 'oak_planks'],
    ['屋顶角落(y=69)', new Vec3(20, 69, -475), 'oak_planks'],
    ['屋内空气', new Vec3(22, 65, -473), 'air'],
  ];
  let ok = 0, fail = 0;
  for (const [label, pos, want] of checks) {
    let found = null;
    for (let retry = 0; retry < 15 && !found; retry++) {
      const b = bot.blockAt(pos);
      if (b && b.name && b.name !== 'air' && b.name !== 'cave_air') { found = b.name; break; }
      if (want === 'air' && b && b.name === 'air') { found = 'air'; break; }
      await new Promise(r => setTimeout(r, 300));
    }
    const good = found === want;
    console.log(`${good ? '✅' : '❌'} ${label} (${pos}) → ${found || 'NULL'} (期望 ${want})`);
    good ? ok++ : fail++;
  }
  console.log(`\n[TEST] 结果: ${ok}/7 通过`);
  bot.quit();
  process.exit(0);
});

setTimeout(() => { console.log('[TEST] 超时'); process.exit(0); }, 30000);
