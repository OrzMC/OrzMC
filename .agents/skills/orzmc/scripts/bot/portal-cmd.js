#!/usr/bin/env node
// 传送门测试 - 通用命令执行器：node portal-cmd.js <端口> <命令>
// 用 bot 玩家身份执行命令（RCON 无玩家身份的命令如 /portal 必须 bot 执行）
// 示例:
//   node portal-cmd.js 25565 "/portal {LAN_IP} 25566"
//   node portal-cmd.js 25565 "/portal remove {LAN_IP} 25566"
// 注意: mineflayer 需要 version '1.21.11'（服务器装 ViaVersion 转换到 26.2）
const mineflayer = require('mineflayer');

const PORT = process.argv[2] || '25565';
const CMD = process.argv[3] || '/portal {LAN_IP} 25566';
const HOST = process.argv[4] || '{LAN_IP}';
const BOT_NAME = process.argv[5] || 'HermesBot';
const BOT_PASS = process.env.BOT_PASS || '{BOT_PASSWORD}'; // 从环境变量读密码

const bot = mineflayer.createBot({
  host: HOST, port: parseInt(PORT), username: BOT_NAME,
  auth: 'offline', version: '1.21.11', hideErrors: true,
});

bot.on('message', (m) => {
  const t = m.toString().replace(/§[0-9a-fk-or]/g, '');
  if (t.includes('传送门') || t.includes('已创建') || t.includes('已移除')
      || t.includes('没有匹配') || t.includes('端口') || t.includes('用法')
      || t.includes('登录') || t.includes('注册')) {
    console.log('[CHAT]', t);
  }
});

bot.on('spawn', () => {
  setTimeout(() => { bot.chat(`/login ${BOT_PASS}`); }, 2000);
  setTimeout(() => {
    console.log('>>>', CMD);
    bot.chat(CMD);
  }, 6000);
  setTimeout(() => { bot.end(); process.exit(0); }, 12000);
});

bot.on('kicked', (r) => {
  console.log('[KICKED]', r.toString().replace(/§[0-9a-fk-or]/g, ''));
  process.exit(0);
});
setTimeout(() => process.exit(1), 18000);
