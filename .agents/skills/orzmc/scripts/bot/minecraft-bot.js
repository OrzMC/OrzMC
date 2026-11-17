#!/usr/bin/env node
/**
 * HermesBot - Mineflayer 机器人玩家
 * 用途: 玩家身份操作（/home、触发区块加载、模拟玩家、实体统计锚点）
 *
 * 用法:
 *   node minecraft-bot.js [用户名] [服务器IP] [端口]
 *
 * 环境变量:
 *   BOT_USER  BOT_HOST  BOT_PORT  BOT_PASSWORD（预设密码，跳过自动注册）
 */
const mineflayer = require('mineflayer');

// ===== 运行时 Patch：1.21.11 粒子映射补 26.x 新 ID =====
// 问题：26.2 服务器经 ViaVersion 转 1.21.11 客户端时，新粒子 ID (115/116 block_crumble/firefly)
//       在 1.21.11 的 Particle mappings 不存在 → protodef 解析错位 → f32 PartialReadError 崩溃
// 修复：把 115/116 映射到无数据粒子类型（null 定义 = 不读附加字节）
try {
  const fs = require('fs');
  const path = require('path');
  const protoPath = path.join(__dirname, 'node_modules', 'minecraft-data', 'minecraft-data', 'data', 'pc', '1.21.11', 'protocol.json');
  const raw = JSON.parse(fs.readFileSync(protoPath, 'utf8'));
  const mappings = raw.types.Particle[1][0].type[1].mappings;
  let patched = false;
  if (!mappings['115']) { mappings['115'] = 'block_crumble'; patched = true; }
  if (!mappings['116']) { mappings['116'] = 'firefly'; patched = true; }
  if (patched) {
    fs.writeFileSync(protoPath, JSON.stringify(raw));
    console.log('[BOT] ✅ 粒子映射已 patch（115/116 补入 1.21.11）');
  }
} catch (e) {
  console.log('[BOT] ⚠️ 粒子 patch 失败:', e.message);
}

const USER = process.env.BOT_USER || process.argv[2] || 'HermesBot';
const HOST = process.env.BOT_HOST || process.argv[3] || '{SERVER_HOST}';
const PORT = parseInt(process.env.BOT_PORT || process.argv[4] || '25565', 10);
const PASSWORD = process.env.BOT_PASSWORD || '{BOT_PASSWORD}';

// 随机密码（用于自动注册）
const genPwd = () => Array.from({length: 12}, () => 
  'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'[Math.floor(Math.random()*62)]
).join('');

let regPwd = PASSWORD || genPwd();
let registered = false;
let bot = null;
let manualQuit = false;

function createBot() {
  bot = mineflayer.createBot({
    host: HOST,
    port: PORT,
    username: USER,
    auth: 'offline',
    version: '1.21.11', // ViaVersion 转换到 26.2 服务器
    hideErrors: false,
  });

  bot.on('login', () => {
    console.log(`[BOT] ${USER} 已登录服务器 (${HOST}:${PORT})`);
    // 尝试注册（已注册则忽略）
    bot.chat('/register ' + regPwd + ' ' + regPwd);
  });

  bot.on('spawn', () => {
    console.log(`[BOT] 已生成，位置: ${Math.round(bot.entity.position.x)}, ${Math.round(bot.entity.position.y)}, ${Math.round(bot.entity.position.z)}`);
    registered = true;
  });

  // 处理踢出（未注册/未登录）
  bot.on('kicked', (reason) => {
    console.log('[BOT] 被踢出:', reason.toString().slice(0, 200));
    // 如果是注册问题，重连一次
    if (!registered && reason.toString().includes('register')) {
      console.log('[BOT] 需要注册，重连...');
      setTimeout(() => process.exit(0), 1000);
    }
  });

  bot.on('error', (err) => {
    console.log('[BOT] 错误:', err.message);
  });

  bot.on('end', (reason) => {
    console.log('[BOT] 连接断开:', reason);
    // 自动重连（除主动退出外）
    if (!manualQuit) {
      console.log('[BOT] 10s 后自动重连...');
      setTimeout(() => createBot(), 10000);
    }
  });

  // 聊天命令
  bot.on('chat', (username, message) => {
    if (username === bot.username) return;
    // !tp x y z - 传送到坐标
    const tp = message.match(/^!tp\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)/);
    if (tp) {
      const [x, y, z] = [parseInt(tp[1]), parseInt(tp[2]), parseInt(tp[3])];
      bot.chat(`正在传送到 ${x}, ${y}, ${z}`);
      bot.entity.position.set(x + 0.5, y, z + 0.5);
      return;
    }
    // !pos - 报告位置
    if (message === '!pos') {
      const p = bot.entity.position;
      bot.chat(`我在 ${Math.round(p.x)}, ${Math.round(p.y)}, ${Math.round(p.z)}`);
      return;
    }
    // !stats - 报告自身状态
    if (message === '!stats') {
      const p = bot.entity.position;
      bot.chat(`HermesBot | 位置 ${Math.round(p.x)},${Math.round(p.y)},${Math.round(p.z)} | HP ${bot.health}`);
      return;
    }
  });

  // 定期心跳
  setInterval(() => {
    if (bot && bot.entity) {
      console.log(`[BOT] 心跳: ${Math.round(bot.entity.position.x)},${Math.round(bot.entity.position.y)},${Math.round(bot.entity.position.z)} HP=${bot.health}`);
    }
  }, 60000);
}

// 粒子包解析错误（ViaVersion 26.2→1.21.11 边界）→ 自动重连
process.on('uncaughtException', (err) => {
  console.log('[BOT] 未捕获异常:', err.message);
  if (err.message && (err.message.includes('particles') || err.message.includes('PartialReadError'))) {
    console.log('[BOT] 协议解析错误，10s 后重连...');
    if (bot) { try { bot.end('reconnect'); } catch(e) {} }
    setTimeout(() => createBot(), 10000);
  } else {
    console.log('[BOT] 未知异常，进程退出');
    process.exit(1);
  }
});

// 优雅退出
process.on('SIGTERM', () => {
  manualQuit = true;
  if (bot) bot.quit();
  process.exit(0);
});

process.on('SIGINT', () => {
  manualQuit = true;
  if (bot) bot.quit();
  process.exit(0);
});

createBot();
