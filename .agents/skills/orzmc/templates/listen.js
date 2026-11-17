// 验证：bot 能收到其它玩家的公屏消息 + 私信（/msg）
// 身份：HermesBot（已白名单+已注册）
const mineflayer = require('mineflayer');

const bot = mineflayer.createBot({
  host: '127.0.0.1', port: 25565, username: 'HermesBot',
  auth: 'offline', version: '1.21.11', hideErrors: false,
});

let loggedIn = false;
bot.on('login', () => { bot.chat('/login {BOT_PASSWORD}'); });

// 1. chat 事件：任何玩家说话（含私信）
bot.on('chat', (username, message) => {
  console.log(`[CHAT事件] ${username}: ${message}`);
});

// 2. message 事件：原始消息（可区分系统消息/私信）
bot.on('message', (msg) => {
  const t = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (t.includes('登录成功')) { loggedIn = true; console.log('[SYSTEM] ✅ 登录成功，开始监听...'); }
  if (t.includes('whisper') || t.includes('私信') || t.includes('msg')) console.log('[MSG]', t);
});

bot.on('spawn', () => {
  console.log('[BOT] 已进服，等待消息...');
  console.log('[BOT] 提示：另开一个 bot 或真人玩家发消息测试');
  // OP 权限给测试玩家加白名单
  bot.chat('/whitelist add TestPlayer');
});

bot.on('kicked', (r) => console.log('[KICKED]', r.toString()));
bot.on('error', (e) => console.log('[ERROR]', e.message));

// 10 分钟后自动退出
setTimeout(() => { console.log('[BOT] 监听超时退出'); bot.quit(); process.exit(0); }, 600000);
