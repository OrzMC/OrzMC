// 查询服务器白名单中的账号
const mineflayer = require('mineflayer');
const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: true,
});
let started = false;
bot.on('login', () => { setTimeout(() => bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123')), 1000); });
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (/whitelist|白名单|White|list|在线/.test(t)) console.log('[WL]', t.slice(0, 100));
});
bot.on('spawn', async () => {
  if (started) return;
  started = true;
  await new Promise(r => setTimeout(r, 3000));
  bot.chat('/whitelist list');
  await new Promise(r => setTimeout(r, 2500));
  bot.quit();
  setTimeout(() => process.exit(0), 500);
});
setTimeout(() => process.exit(0), 15000);
