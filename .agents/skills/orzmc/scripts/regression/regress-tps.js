// 阶段4回归：查询 TPS + 插件列表（用服务器命令）
const mineflayer = require('mineflayer');

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

let started = false;
const lines = [];
bot.on('login', () => { bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')); });
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (/TPS|tps|Memory|记忆|插件|plugins|Paper|版本|perf|性能/.test(t)) {
    lines.push(t);
    console.log('[TPS]', t.slice(0, 120));
  }
});

bot.on('spawn', async () => {
  if (started) return;
  started = true;
  await new Promise(r => setTimeout(r, 3000));
  bot.chat('/tps');
  await new Promise(r => setTimeout(r, 1500));
  bot.chat('/paper tps');
  await new Promise(r => setTimeout(r, 1500));
  bot.chat('/plugins');
  await new Promise(r => setTimeout(r, 2000));
  console.log('--- 插件列表 ---');
  bot.chat('/plugman list');
  await new Promise(r => setTimeout(r, 2000));
  bot.quit();
  setTimeout(() => process.exit(0), 500);
});

setTimeout(() => { console.log('[TPS] 超时'); process.exit(0); }, 25000);
