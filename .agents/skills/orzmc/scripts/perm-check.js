// 权限系统验证脚本：bot 进服（玩家身份）执行 LP 查询并捕获输出
// 用法: cd ~/minecraft-bot && node perm-check.js <端口> [密码]
// 背景: RCON 不回显 LuckPerms 命令输出（Adventure 组件），验证权限必须玩家身份
const mineflayer = require('mineflayer');
const path = require('path');

const PORT = parseInt(process.argv[2] || '25565');
const PASSWORD = process.argv[3] || '{BOT_PASSWORD}';
const HOST = '127.0.0.1';

// 粒子 patch（26.2→1.21.11 兼容）
const mcDataPath = path.join(require.resolve('minecraft-data'), '../..', 'minecraft-data', 'data', 'pc', '1.21.11', 'protocol.json');
try {
  const fs = require('fs');
  const proto = JSON.parse(fs.readFileSync(mcDataPath, 'utf8'));
  const mappings = proto.types.Particle[1][0].type[1].mappings;
  mappings['115'] = 'block_crumble';
  mappings['116'] = 'firefly';
  fs.writeFileSync(mcDataPath, JSON.stringify(proto));
} catch (e) {}

function log(msg) { console.log('[RESULT]', msg); }

const bot = mineflayer.createBot({
  host: HOST, port: PORT, username: 'HermesBot',
  version: '1.21.11', auth: 'offline', hideErrors: true,
});

bot.on('message', (msg) => {
  const text = msg.toString().replace(/§[0-9a-fk-or]/g, '');
  if (text.trim()) log(`[MSG] ${text}`);
});

bot.on('login', () => {
  setTimeout(() => bot.chat('/login ' + PASSWORD), 1500);
  // 默认验证：joker(builder) / TestPlayer(member) / Newbie(default)
  setTimeout(() => bot.chat('/lp user joker parent info'), 5000);
  setTimeout(() => bot.chat('/lp user joker permission check essentials.fly'), 7000);
  setTimeout(() => bot.chat('/lp user joker permission check minecraft.command.gamemode'), 9000);
  setTimeout(() => bot.chat('/lp user TestPlayer permission check essentials.fly'), 11000);
  setTimeout(() => bot.chat('/lp user Newbie permission check essentials.fly'), 13000);
  setTimeout(() => { bot.quit(); process.exit(0); }, 20000);
});

bot.on('error', (err) => { console.log('[BOT] 错误:', err.message); });
setTimeout(() => { console.log('[BOT] 超时'); process.exit(1); }, 40000);
