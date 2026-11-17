// EE 双事件测试：跳跃（PLAYER_JUMP_EVENT）+ 行走（PLAYER_WALK）
const mineflayer = require('mineflayer');
const PWD = process.env.BOT_TEST_PASSWORD || 'CHANGE_ME';
const bot = mineflayer.createBot({
  host: '127.0.0.1',
  port: 25565,
  username: 'HermesBot',
  auth: 'offline',
  version: '1.21.11'
});

bot.on('login', () => {
  setTimeout(() => bot.chat('/login ' + PWD), 500);
});
bot.on('spawn', () => {
  console.log('SPAWNED at', bot.entity.position);
  // 先 tp 到开阔地（出生点区域）
  setTimeout(() => { try { bot.chat('/minecraft:tp 164.5 73 157.5'); } catch(e){} }, 3000);
  // 跳跃 5 次（触发 PLAYER_JUMP_EVENT）
  setTimeout(() => {
    console.log('JUMPING...');
    for (let i = 0; i < 5; i++) {
      setTimeout(() => {
        bot.setControlState('jump', true);
        setTimeout(() => bot.setControlState('jump', false), 300);
      }, i * 700);
    }
  }, 6000);
  // 行走 6 秒（触发 PLAYER_WALK）
  setTimeout(() => {
    console.log('WALKING...');
    bot.setControlState('forward', true);
    setTimeout(() => bot.setControlState('forward', false), 6000);
  }, 11000);
  setTimeout(() => { console.log('DONE, pos:', bot.entity.position); bot.end(); process.exit(0); }, 24000);
});
bot.on('kicked', (r) => { console.log('KICKED:', typeof r === 'string' ? r : JSON.stringify(r)); process.exit(1); });
bot.on('error', (e) => { console.log('ERR:', e.message); process.exit(1); });
setTimeout(() => { console.log('TIMEOUT'); process.exit(1); }, 40000);
