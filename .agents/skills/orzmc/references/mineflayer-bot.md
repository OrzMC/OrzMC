# 机器人玩家（Mineflayer）——运维视角

> **用途**：玩家身份操作（/home、/tps）、触发区块加载、模拟玩家活动、实体统计锚点（无需真人客户端）。
> ⚠️ **bot 测不了 FPS**——headless 无渲染，FPS 是客户端指标；服务端实体统计见 `entity-statistics.md`。
> 📌 **bot 开发细节（mineflayer API、坑链、脚本模板）→ 独立技能 `minecraft-bot-mineflayer`**——本文件只保留运维需要的部分。
> 项目位置：`~/minecraft-bot/`（含 start.sh / stop.sh / minecraft-bot.js）

## 启动（运维视角）

```bash
# 线上（默认连 {SERVER_HOST}:25565）
cd ~/minecraft-bot && ./start.sh HermesBot
# 本地测试服
BOT_HOST=127.0.0.1 BOT_PORT=25565 node minecraft-bot.js
```

- 协议：**`version: '1.21.11'`** 连 MC 26.2 服（ViaVersion 自动转换）；直接写 `26.2` 报 unsupported
- 白名单：原版 whitelist（OrzMC force_whitelist 也认）；MCSM 用 command `whitelist add`，本地改 whitelist.json + 重启
- 登录：LoginSecurity 密码 **6-32 字符**；已注册账户须 `/login`（未登录时所有命令静默失败）
- 验证：服务器日志 `HermesBot issued server command: /tps`（玩家身份，非 CONSOLE）

## 运维要点

- ⚠️ **MCSM command API 转发丢玩家上下文**：`execute as HermesBot run tp ...` 会被 MCSM 当 CONSOLE 命令简化执行（日志 `CONSOLE issued server command: /tp`，玩家位置不变）——**需要玩家身份的操作必须由 bot 自己通过 mineflayer 执行**（`bot.chat('/home')`），不走 MCSM command API
- ⚠️ **有 Essentials 时原版命令加 `minecraft:` 域**：`/minecraft:tp`（绕 teleport-safety）、`/minecraft:whitelist add`、`/minecraft:tell`（私信）——详细见独立技能
- ✅ **本地测试服（MCSM paper 实例 716c2fb7）验证价值**：本地出生点有苦力怕等实体，能暴露线上不常触发的崩溃路径（粒子/实体交互），改 bot 后先本地验证再上生产
- ⚠️ **临时验证脚本必须放 `~/minecraft-bot/` 内运行**（Node 模块解析从脚本所在目录向上找 node_modules；放 /tmp 报 `Cannot find module 'mineflayer'`）——一次性验证脚本（如经中转登录）直接 `cp` 进项目目录再 `node` 跑
- ⚠️ **登录验证脚本要素**（2026-08-14 OrzMCProxy 正式档验收实测）：`auth: 'offline'`（离线服）+ `version: '1.21.11'`（26.2 服）；监听 `spawn`（进入游戏=登录成功铁证）、`kicked`（含拒绝原因，如白名单）、`error`；30s 超时兜底；登录成功后 `bot.end()` + `process.exit(0)` 防挂死——服务器日志对应行 `test[/真实IP:port] logged in with entity id N at (...)` 就是**真实 IP 透传验证的终极铁证**（frpc PROXY v2 头场景下显示玩家真实公网 IP）
- ⚠️ bot 项目持久化在 `~/minecraft-bot/`（勿放 /tmp）

## 挂机脚本（stay-with-joker.js，2026-08-16 新增）

```bash
cd ~/minecraft-bot && BOT_COUNT=5 node stay-with-joker.js [分钟=60] [前缀=Test] [目标玩家=joker]
# 5 bot（Test01-05）登录 → RCON /minecraft:tp 到目标玩家身边 → 原地跳跃挂机
# 内置 IPv4+IPv6 分流：Test01-03 走 127.0.0.1，Test04-05 走 ::1（绕 per-IP 5 限制）
# 每 60s 报告在线数；时长到自动 quit
```

- **用途**：多 bot 挂机在指定玩家位置（如 joker 身边），模拟多人在线
- **前置**：Test01-05 已加白名单（`whitelist add`）；**已注册过的 bot 只 `/login` 不 `/register`**（重复 register 可能触发会话重建 → 被踢）
- **验证**：`rc list` 看到 Test01-05 在线 + 服务器日志 `[Rcon: Teleported Test01 to 悅咪丿 - joker]`
- 2026-08-16 实测：5/5 稳定在线 2 分钟零掉线（IPv4 3 + IPv6 2 分流）

## bot 测试插件事件（2026-08-19 ExecutableEvents 实测沉淀）

- ⚠️ **防重登限制坑**：连续快速登录被踢 `You must wait X seconds before logging-in again`——来源是 **GriefPrevention3D 的 `Spam.LoginCooldownSeconds`（默认 60）**，不是登录插件；改 0 + 重启解除（SimpleLogin 无此限制）
- ⚠️ **SimpleLogin 密码重置**（忘记 bot 密码时）：直改 `plugins/SimpleLogin/passwords.db` 的 `users` 表（uuid→password BCrypt $2a$10$）；Python bcrypt 生成的是 `$2b$` 前缀，Java BCrypt 不认 → **必须替换为 `$2a$`**
- ⚠️ **mineflayer `setControlState('forward')` 不稳定**：同一脚本有时移动有时不动（疑似物理/时序问题）；**RCON `minecraft:tp <bot>` 移动可靠**（触发 PlayerMoveEvent）但**不触发 sevents 自定义事件**（如 PLAYER_WALK 只认真实行走）
- ✅ **玩家位置持久化**：bot 下线位置 = 下次重进 spawn 位置（离线服）——测试位置敏感场景先 `/minecraft:tp` 到开阔地
- ✅ **事件类插件测试套路**：bot 驻留脚本（登录后保持在线 N 秒）→ RCON tp 或 bot 跳跃/行走 → 服务端日志/插件 debug 模式看触发；`version: '1.21.11'` + `/login <pwd>`（SimpleLogin）后 OrzMC 日志「上线」= 登录成功铁证
- 参考脚本：`scripts/bot/ee-event-test.js`（双事件测试：PLAYER_JUMP_EVENT + PLAYER_WALK）

## 频繁上下线测试（freq-relog.js，2026-08-19 实测沉淀）

```bash
cd ~/minecraft-bot && BOT_COUNT=6 node freq-relog.js [轮数=8] [在线秒=3] [离线秒=5]
# 6 bot 循环 登录→保持→退出→等待→再登录；输出 /tmp/freq_relog_result.json（每 bot 每轮时间线）
```

- **用途**：验证 player_notify 聚合防刷屏（JOIN/QUIT/KICK 窗口聚合）+ 观察群消息行为
- **前置**：bot 必须已加**原版白名单**（OrzMC force_whitelist=true 时启动会把原版白名单打开，ProfileWhitelistVerifyEvent 拦截未在白名单的玩家，`whitelist add <name>` 实时生效；改 config 的 force_whitelist 不改变运行时原版开关，需重启才生效）；离线间隔 ≥5s 绕 bukkit connection-throttle 4000ms（4s 内重连被拒）；IPv4+IPv6 分流绕 per-IP 5 限制
- **实测结论（2026-08-19，6 bot × 8 轮 = 96 事件/85s）**：聚合生效——96 事件 → **14 条群消息**（85% 削减），3s 窗口内多条合并为 player_digest（`🟢 +4 上线：Fq04、Fq02...⏎🔴 -4 下线：...`），max_list_items=6 截断（`等1人`），窗口内单事件延迟一窗口单发；QQ+飞书全部投递成功
- 🚨 **whitelist_block（白名单拦截通知）不走聚合/无限频**：`Notifier.event → routeEvent` 直接发送，每次被拦尝试逐条双发（QQ+飞书）→ 48 次被拦尝试即打爆 QQ 频控（`40034100 主动消息发送超过频控限制`）导致消息失败；飞书无此频控正常。**高频触发面 = 恶意脚本反复尝试未在白名单的玩家名**。修复方向：复用 ThrottledNotifier 按 key 限频，或并入聚合器
- ⚠️ login_rate_limit（5 次/分钟/IP）会挡住高频登录测试——测纯聚合效果需临时 `enabled: false`（改 config.yml + `/config reload` 即生效，Supplier 实时读取），测完恢复
- 实测 96 事件 Folia 零 Can't keep up（region TPS 15-17 为 BETA 常态）

## 命令执行 bot（exec-cmds.js / stay-for-kick.js，2026-08-19 样式审计沉淀）

```bash
cd ~/minecraft-bot
node exec-cmds.js <玩家名> <命令1> [命令2...]   # 登录→/login→依次执行游戏内命令→退出（chat 响应打印）
node stay-for-kick.js <玩家名>                  # 登录后驻留 60s（供 RCON kick 测试）
```

- ⚠️ **必须等 AuthMe /login 成功后再执行命令**：mineflayer spawn 事件早于 AuthMe 登录完成，未登录时命令被**静默拦截**（无输出、无通知）——exec-cmds.js 在 spawn 后固定等 3s
- ⚠️ **/review approve 在 Folia 上曾卡死服务器**（2026-08-19 发现并修复）：根因=LP 异步 future（loadUser/saveUser）完成回调调度回服务器同步线程，而 promote 在 global/region 线程同步 `.get()` 等它 → 自锁 3s 超时（修复前是死锁 132s+）；修复=ReviewHandler 异步化（CompletableFuture<Boolean>，LP 操作在自己管理的异步线程执行，审核框架异步等待后落状态，杜绝漂移）。⚠️ 通用教训：**Folia 上任何服务器调度线程（global/region）绝不能同步等待 LP 异步 future**（回调排在自己后面必自锁）；已修提交 f0fbe1b/8000f2f/bf2f588（分支 fix/folia-review-deadlock-and-notify）
- ⚠️ **/apply builder 需要先成为 member**：ReviewType 资格预检 `isEligible`（builder 申请要求当前组 member）；default 组玩家 `/apply` 返回「当前没有可申请的审核类型」——测试前先 `lp user X parent set member`
- ⚠️ **login_rate_limit 干扰高频 bot 测试**：恢复 enabled:true 后同 IP 每分钟 5 次登录尝试被踢（"登录过于频繁"）；测试分流 IPv4+IPv6 或临时关闭
- ✅ **群消息样式审计经验**：orzdebug 只回显日志**不发群**（callback 写死 logger.info）；要真实发群必须 bot 游戏内触发事件（/apply、/review、上下线、kick）或真实群消息；easybot_deliveries.py 拉投递记录看实际渲染

## 压测脚本（stress-stay.js，2026-08-12/13 实测沉淀）```bash
cd ~/minecraft-bot && BOT_COUNT=10 node stress-stay.js 2   # N bot 驻留 2 分钟 + RCON 每 5s 采样 TPS
# 输出 /tmp/stress_stay_result.json（采样数组 + joined/peakOnline/avgTps/minTps）
# 环境变量：BOT_HOST/BOT_PORT/BOT_PASSWORD/RCON_PORT/RCON_PASSWORD（默认本地服）
```

- **mineflayer 选项原样透传 minecraft-protocol**（`bot._client = mc.createClient(options)`）→ 可用自定义 `connect: (client) => { client.setSocket(net.connect({host, port, localAddress: srcIp})); client.emit('connect'); }` 绑定源 IP
- ⚠️ **macOS 禁 bind 127.0.0.2+**（`OSError: [Errno 49] Can't assign requested address`；lo0 虽是 /8 掩码但内核只认 127.0.0.1，与 Linux 不同）→ 多回环 IP 模拟多玩家 **macOS 死路**（无 sudo 也加不了 lo0 alias）
- ⚠️ **vanilla per-IP 5 在线限制**：同 IP 已登录 ≥5 时第 6+ 被踢（`Sorry, there are too many players logged in with your IP address`）→ **单出口 IP 压测天花板 = 5 bot 真实在线**（40 bot 尝试全成功但峰值在线 3-6）；真实玩家各 IP 不同不受影响
- ⚠️⚠️ **同 IP 5 bot 全登录后稳定只能 3 个**（2026-08-16 实测）：5 个全走 127.0.0.1 时**后 2 个在登录成功+tp 后 3-5s 被踢**（`too many players`），Test01-03 稳定——不是登录时检查，是延迟踢出（疑似 register/login 会话重建触发计数）
- ✅✅ **IPv4+IPv6 混合绕开 per-IP 限制（2026-08-16 实测成功）**：服务器 `tcp46` 双栈监听时，**127.0.0.1 与 ::1 是不同 IP 各自 5 上限** → 5 bot 分流（Test01-03 走 `127.0.0.1`、Test04-05 走 `::1`）可**全部稳定在线**（实测 5/5 保持 2 分钟零掉线）。mineflayer `createBot({host: '::1'})` 直接可用；服务器日志显示 `[0:0:0:0:0:0:0:1]` 即 ::1 玩家。⚠️ 前提：服务器监听 `tcp46`（`netstat -an | grep 25565` 查）；若只监听 tcp4 则 ::1 不可连
- ⚠️ **tp 到真人玩家身边用 `/minecraft:tp`**（RCON 执行）：`tp <bot名> <玩家名>` 会被 Essentials 拦截（日志 `[Essentials] Rcon issued server command` 但无实际传送、RCON 无输出）；`minecraft:tp <bot名> <玩家名>` 正常（日志 `[Rcon: Teleported Test01 to 悅咪丿 - joker]`，RCON 返回 `Teleported X to Y`）
- ⚠️ **spawn 事件计数只增不减会虚高**（被踢 bot 也算"进入"）——维护 `Set` 真实在线（spawn 增 / end 减），采样打 `在线=N/总数`
- ⚠️ 压测脚本总时长 = 登录风暴（40 bot ≈ 60-90s）+ 采样 → 前台 200s 上限会超时被杀丢结果 → **用 background=true + notify_on_complete**
- 登录风暴：冷启动首登崩（TPS 4.2）、热世界不崩（40 bot 最低 16.1）→ 详见 testing.md

## 常用操作（bot 侧聊天命令，minecraft-bot.js 内置）

```bash
!tp x y z   # 传送（bot.entity.position.set）
!pos        # 报位置
!stats      # 位置+HP
```

> 机器人作为运维工具：用 bot 位置做实体统计锚点（玩家身份上下文正确）。bot 开发/坑链/模板（build-house.js 搭房子、listen.js 收消息、粒子 patch、自动重连）→ `minecraft-bot-mineflayer` 技能。
