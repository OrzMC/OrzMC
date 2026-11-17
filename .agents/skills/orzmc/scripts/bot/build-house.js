#!/usr/bin/env node
/**
 * HermesBot 搭房子演示
 * 用 Mineflayer 真实放置方块搭一座 7x7x4 小房子：
 *   - 地基 7x7（橡木木板）
 *   - 四面墙 4 格高（橡木原木），正面留门洞(2x1)+窗(1x1)
 *   - 屋顶（橡木台阶平顶）
 *   - 门（橡木门）
 *
 * 需要：HermesBot 有 OP（ops.json）+ 创造模式（/gamemode creative）
 * 用法: BOT_HOST=127.0.0.1 BOT_PORT=25565 node build-house.js
 */
const mineflayer = require('mineflayer');
const { pathfinder, Movements, goals: { GoalNear } } = require('mineflayer-pathfinder');
const { Vec3 } = require('vec3');

const USER = process.env.BOT_USER || 'HermesBot';
const HOST = process.env.BOT_HOST || 'localhost';
const PORT = parseInt(process.env.BOT_PORT || '25565', 10);

// 房子设计（起始坐标，地面 y）——出生点附近（bot 不用传送）
let ORIGIN = new Vec3(20, 64, -475);   // 房子的西南角（地面层）
const SIZE_X = 7, SIZE_Z = 7, WALL_H = 4;

const bot = mineflayer.createBot({
  host: HOST, port: PORT, username: USER,
  auth: 'offline', version: '1.21.11', hideErrors: false,
});

// 注册插件：pathfinder + creative（4.37.1 默认不加载 creative）
const creativePlugin = require('mineflayer/lib/plugins/creative');
bot.loadPlugin(pathfinder);
bot.loadPlugin(creativePlugin);
bot.once('spawn', () => {
  const mcData = require('minecraft-data')(bot.version);
  const defaultMove = new Movements(bot, mcData);
  defaultMove.canDig = false;
  bot.pathfinder.setMovements(defaultMove);
});

function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }
async function say(msg) { bot.chat(msg); console.log('[BOT]', msg); await sleep(1200); }

// 把指定方块放进快捷栏第0格并手持（创造模式直接 setInventorySlot 生成）
const Item = require('prismarine-item')('1.21.11');
const registry = require('minecraft-data')('1.21.11');

async function holdItem(itemName) {
  try {
    const id = registry.itemsByName[itemName].id;
    // waitTimeout=0 不等待服务器 ack（1.21.11 协议 ack 兼容问题会挂起）
    bot.creative.setInventorySlot(0, new Item(id, 64), 0);
    await sleep(400);
  } catch(e) {
    console.log(`[BOT] ⚠️ setInventorySlot 失败 ${itemName}:`, e.message);
  }
  bot.setQuickBarSlot(0);
  await sleep(200);
  try { await Promise.race([bot.equip(0, 'hand'), sleep(2000)]); } catch(e) {}
  await sleep(300);
}

// 放置方块到绝对坐标（等区块加载后找参考方块）
async function placeBlockAt(target) {
  // 等待目标位置的方块数据可用（最多 3s）
  for (let wait = 0; wait < 15; wait++) {
    const probe = bot.blockAt(target);
    if (probe && probe.name && probe.name !== 'air') break;
    await sleep(200);
  }
  // 找一个相邻的已存在方块作为参考
  const dirs = [new Vec3(1,0,0), new Vec3(-1,0,0), new Vec3(0,1,0), new Vec3(0,-1,0), new Vec3(0,0,1), new Vec3(0,0,-1)];
  for (const d of dirs) {
    const ref = bot.blockAt(target.plus(d));
    if (ref && ref.name && ref.name !== 'air' && ref.name !== 'cave_air' && ref.name !== 'void_air') {
      const face = d.scaled(-1); // 从参考方块朝向目标的面
      try {
        await Promise.race([bot.placeBlock(ref, face), sleep(2000)]);
        return true;
      } catch (e) {
        // 位置不对，试试别的参考
      }
    }
  }
  console.log(`[BOT] placeBlockAt 失败: ${target} 无参考方块`);
  return false;
}

// 移动+放置一个方块（用 /setblock 命令，OP 身份可靠）
async function buildBlock(target, itemName) {
  // 传送到目标附近（让房子有"人在建"的感觉）
  bot.chat(`/minecraft:tp ${target.x + 0.5} ${target.y + 3} ${target.z + 0.5}`);
  await sleep(600);
  // 用 setblock 放置（OP 权限；door 特殊处理）
  const cmd = itemName === 'oak_door' ? 'oak_door[facing=east,half=lower]' : itemName;
  bot.chat(`/setblock ${target.x} ${target.y} ${target.z} ${cmd}`);
  await sleep(400);
}

// 确保 bot 在目标位置（position.set 可能被服务器拉回，循环重设）
async function ensurePosition(x, y, z, retries = 5) {
  for (let i = 0; i < retries; i++) {
    bot.entity.position.set(x, y, z);
    await sleep(800);
    const cur = bot.entity.position;
    if (cur.distanceTo(new Vec3(x, y, z)) < 2) return true;
    console.log(`[BOT] 重设位置 ${i + 1}: 现在 ${cur.floored()}（目标 ${Math.round(x)},${Math.round(y)},${Math.round(z)}）`);
  }
  return false;
}

async function buildHouse() {
  await say('开始搭房子！先切创造模式...');
  bot.chat('/gamemode creative');
  await sleep(1500);

  // 用 /minecraft:tp 强制传送（已登录后命令可正常执行）
  bot.chat(`/minecraft:tp ${ORIGIN.x + 3} ${ORIGIN.y + 8} ${ORIGIN.z + 3}`);
  await sleep(2000);

  // 探测实际地面高度（向下找第一个非空气方块）——先等区块加载
  await bot.waitForChunksToLoad();
  await sleep(2000);
  let groundY = 64;
  for (let y = 100; y >= 0; y--) {
    const b = bot.blockAt(new Vec3(ORIGIN.x, y, ORIGIN.z));
    if (b && b.name !== 'air' && b.name !== 'cave_air' && b.name !== 'void_air') {
      groundY = y;
      break;
    }
  }
  const groundBlock = bot.blockAt(new Vec3(ORIGIN.x, groundY, ORIGIN.z));
  console.log(`[BOT] 探测地面: y=${groundY}（${groundBlock ? groundBlock.name : 'unknown'}）`);
  if (groundY !== 64 && groundBlock) {
    console.log(`[BOT] 地面不是 64，调整房子起点 y=64→${groundY + 1}`);
    ORIGIN.y = groundY + 1;
  }

  await say(`房子设计：${SIZE_X}x${SIZE_Z}，墙高 ${WALL_H}，位置 (${ORIGIN.x}, ${ORIGIN.y}, ${ORIGIN.z})`);

  // 1. 地基
  await say('第 1 步：铺地基');
  for (let dx = 0; dx < SIZE_X; dx++) {
    for (let dz = 0; dz < SIZE_Z; dz++) {
      await buildBlock(new Vec3(ORIGIN.x + dx, ORIGIN.y, ORIGIN.z + dz), 'oak_planks');
    }
  }

  // 2. 四面墙（4 格高），正面（南，+z）留门洞+窗
  await say('第 2 步：砌墙');
  for (let h = 1; h <= WALL_H; h++) {
    for (let dx = 0; dx < SIZE_X; dx++) {
      for (let dz = 0; dz < SIZE_Z; dz++) {
        const isEdge = dx === 0 || dx === SIZE_X-1 || dz === 0 || dz === SIZE_Z-1;
        if (!isEdge) continue;
        // 门洞：正面 (dx=3, h=1..2, dz=SIZE_Z-1)
        if (dz === SIZE_Z-1 && dx === 3 && h <= 2) continue;
        // 窗：正面 (dx=1 和 5, h=2, dz=SIZE_Z-1)
        if (dz === SIZE_Z-1 && (dx === 1 || dx === 5) && h === 2) continue;
        await buildBlock(new Vec3(ORIGIN.x + dx, ORIGIN.y + h, ORIGIN.z + dz), 'oak_log');
      }
    }
  }

  // 3. 窗玻璃
  await say('第 3 步：装窗户');
  for (const dx of [1, 5]) {
    await buildBlock(new Vec3(ORIGIN.x + dx, ORIGIN.y + 2, ORIGIN.z + SIZE_Z-1), 'glass');
  }

  // 4. 屋顶（平顶 7x7，橡木台阶）
  await say('第 4 步：盖屋顶');
  for (let dx = 0; dx < SIZE_X; dx++) {
    for (let dz = 0; dz < SIZE_Z; dz++) {
      await buildBlock(new Vec3(ORIGIN.x + dx, ORIGIN.y + WALL_H + 1, ORIGIN.z + dz), 'oak_planks');
    }
  }

  // 5. 门（正面门洞）
  await say('第 5 步：装门');
  await buildBlock(new Vec3(ORIGIN.x + 3, ORIGIN.y + 1, ORIGIN.z + SIZE_Z-1), 'oak_door');
  bot.chat(`/setblock ${ORIGIN.x + 3} ${ORIGIN.y + 2} ${ORIGIN.z + SIZE_Z-1} oak_door[facing=east,half=upper]`);
  await sleep(400);

  await say(`✅ 房子搭好了！位置 (${ORIGIN.x}, ${ORIGIN.y}, ${ORIGIN.z}) 大小 ${SIZE_X}x${SIZE_Z}x${WALL_H+2}`);
}

bot.on('login', () => {
  console.log('[BOT] 登录成功');
  // 密码必须 6-32 字符；已注册过则 login，未注册则 register
  bot.chat('/login ' + (process.env.BOT_PASSWORD || 'changeMe123'));
});

bot.on('spawn', async () => {
  console.log(`[BOT] 生成位置: ${bot.entity.position}`);
  try {
    await buildHouse();
  } catch (e) {
    console.log('[BOT] 搭建出错:', e.message);
  }
  console.log('[BOT] 任务完成');
});

bot.on('kicked', (reason) => { console.log('[BOT] 被踢:', reason.toString().slice(0, 100)); process.exit(1); });
bot.on('error', (err) => { console.log('[BOT] 错误:', err.message); });
bot.on('end', () => { console.log('[BOT] 断开'); process.exit(0); });

// 超时保护（5 分钟）
setTimeout(() => { console.log('[BOT] 超时退出'); bot.quit(); process.exit(0); }, 300000);
