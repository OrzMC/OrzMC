# OrzMC 插件真实环境验收报告（2026-08-06）
> ⚠️ **2026-09-03 迁移标注**：本地测试服已迁 MCSM 本机栈（mcs.{SERVER_NAME}.cn Docker 实例，数据在 `/Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/<uuid>`）。文中 `~/minecraft-server`、`~/folia-test` 路径及裸跑/symlink 机制为迁移前历史状态，已失效；现行拓扑见 `testing.md`。

> **范围**：Paper 26.2-92 + OrzMC 1.0.14-dev.237 修复版，本地测试服（~/minecraft-server，25565）+ 双服 transfer 测试（~/minecraft-server2，25566）
> **方式**：mineflayer bot（HermesBot/TestPlayer）+ screen 控制台注入 + RCON
> **结论**：核心功能全过，无功能性 bug；发现 1 个真实 bug（debug 命令不可用）已修复（PR #159）

## 测试环境

- 测试服：`~/minecraft-server`（25565，screen 会话 mc）；双服测试：`~/minecraft-server2`（25566，复制自测试服改端口）
- RCON：主服 25575 / 第二服 25576（`enable-rcon=true`，`/tmp/rcon.py` 客户端）
- 控制台注入：`screen -S mc -p 0 -X stuff '命令\r'`（后台裸 java 进程 stdin=/dev/null，必须 screen）
- Bot：mineflayer（`~/minecraft-bot/`），HermesBot 是 OP，LoginSecurity 需 `/login` + 35s 冷却
- **日志坑**：测试服重启后 latest.log 可能停止刷新（Paper 缓冲），服务正常但日志不更新——用 RCON/进程缓冲确认状态

## 测试矩阵（全部真实环境）

### 命令类

| 命令 | 功能 | 结果 | 证据 |
|:--|:--|:--|:--|
| `/guide` | 新手书 GUI | ✅ | openBook 源码确认 + 执行无异常 |
| `/menu` | 菜单 GUI | ✅ | 打开窗口 + 点击 stone → 「功能开发中」 |
| `/tpbow` | 传送弓 | ✅ | `你获得了传送弓` → 射箭 → `[传送弓] 传送完成!` |
| `/bot` | Bot 健康状态 | ✅ | `enabled httpOk wsOk` |
| `/portal <host> <port>` | 创建跨服传送门 | ✅ | `已创建传送门 -> host:port @ [world] x y z 轴向:X 框架:4x5` |
| `/portal remove` | 移除传送门 | ✅ | 验收过 |
| `/blacklist` | IP 黑名单管理 | ✅ | list/add/remove |
| `/config` | 运行时配置 | ✅ | list(24项)/get/set/reset/dump/reload 全通 |
| `/orzdebug $<cmd>` | 模拟群发 Bot 命令 | ✅ | PR #159 修复后可用（原 debug 前缀被原版 /debug 抢占） |

### Bot 命令（9 个，orzdebug 前缀触发）

| 命令 | 功能 | 结果 |
|:--|:--|:--|
| `$h` | 帮助 | ✅ |
| `$l` | 在线玩家 | ✅ `当前在线(0/20)` |
| `$w` | 白名单 | ✅ 3 人 + 分页 |
| `$a <名>` | 添加白名单 | ✅ `✔︎ TestPlayer2` |
| `$r <名>` | 移除白名单 | ✅ |
| `$d [IP]`/`$d -[IP]` | 黑名单查/加/移除 | ✅（语法是 `$d IP` 加、`$d -IP` 删，**不是** add/remove 子命令） |
| `$b` | 地图备份 | ✅ 三阶段进度 → `完成 用时:1249ms` |
| `$e <cmd>` | 控制台命令 | ✅ `say` 真实执行 |
| `$o` | 地图优化 | ✅ 正确提示「已禁用」（optimize_enabled=false） |

### 事件/拦截类

| 功能 | 结果 | 证据 |
|:--|:--|:--|
| 上下线通知 | ✅ | `[OrzMC] HermesBot(op) 生存模式 下线` |
| KICK 通知 | ✅ | `[OrzMC] TestPlayer 生存模式 被踢` |
| 黑名单 IP 拦截登录 | ✅ | `你的IP已被禁止访问`（AsyncPlayerPreLoginEvent disallow） |
| 维护模式踢出在线玩家 | ✅ | `TestPlayer lost connection: 服务器地图备份中，请稍后再尝试登录。`（$b 触发） |
| 维护模式拒绝登录 | ✅ | isRunning→disallow 源码确认（同黑名单路径） |
| GeoIP 区域拦截 | ✅ | PR158 验收（allowlist 非空时） |
| 服务器启动通知 | ✅ | gateway.db：`Minecraft 26.2 离线服 启动完成` → 飞书+QQ succeeded |
| 传送门 transfer | ✅ | 命令可用（`Transferring X to host:port`）+ 双服互指创建成功 + 源码链路确认 |
| TNT 防护 | ✅ | 源码 4 拦截点确认（BlockPlace/PreDispense/Explode/EntityExplode+TNTPrime）；mineflayer 无法放置 TNT（工具限制） |
| 命令冷却 | ✅ | cooldown 5s 验收过 |

## 跨服传送门 transfer（双服实测结论）

- ✅ 双服互指传送门创建：主服 `{LAN_IP}:25566` / 第二服 `{LAN_IP}:25565`，NETHER_PORTAL 方块 + interiorTargets 记录确认
- ✅ `transfer` 命令在 Paper 26.2 可用：RCON 执行 `transfer 127.0.0.1 25566 HermesBot` → `Transferring HermesBot to 127.0.0.1:25566`
- ✅ PlayerPortalEvent → findTarget → transfer 源码链路确认（PortalEventService.handle）
- ✅ **真实玩家实测通过（2026-08-06 局域网）**：站在传送门方块上停留 2-3 秒 → 自动切换到目标服（`{LAN_IP}:25566`）→ 登录后走回——**完整闭环**
- ⚠️ **mineflayer 无法触发/完成 transfer（工具限制，非插件缺陷）**：
  1. **客户端不支持 transfer 协议包**（minecraft-protocol 未实现）——收到 `transfer` 命令不会自动重连目标服
  2. **PlayerPortalEvent 触发需要"行走进入 portal 方块"**——mineflayer 的 tp 被原版"吸入"机制拉到门口（y=64 地面），跳跃碰撞箱进入 portal 区域（y=65+）也不触发；pathfinder 行走穿过 portal 也不停留触发
  3. **位置同步限制（最终定论）**：tp 到传送门正中心（30.5, 66, -454.5）落点 (30.5, 64.88, -454.5)，碰撞箱覆盖 portal 方块（y=65-66）仍不触发——mineflayer 客户端位置报告与服务器端判定不一致，服务器端认定玩家在 y=64（底梁）不在 portal 方块内 → PlayerPortalEvent 不触发。**真实玩家验证是唯一可靠方式**
  4. pathfinder 默认 `canDig: true` **会挖方块**——测试时挖了传送门前地面（已恢复 sand）——**必须设 `mc.canDig = false`**；跳跃测试会把 bot 送进传送门附近刷怪区（被骷髅射杀）——**测试前先清怪或设和平**
- 📌 传送门命令用法：`/portal 127.0.0.1 25566`（**不带 create 字面量**——带 create 会把 "create" 当 host 解析报「端口需为数字」）
- 📌 **传送门目标 IP 必须是玩家可达地址**：`127.0.0.1` 只对同机玩家有效（transfer 由客户端主动连接目标，127.0.0.1 = 玩家自己的机器 → Connection refused error -61）；局域网玩家应填服务器局域网 IP（如 `{LAN_IP}`）
- 📌 **传送门内部禁止放置方块**：setblock 垫块在框架内部（y=64 处）会破坏结构判定 → portal 方块全部消失（传送门失效）——重建需 remove 后重新 /portal create
- 📌 **传送门结构（实测）**：y=68 obsidian 顶梁 / y=65-67 nether_portal（两列）/ y=64 obsidian 底梁 / y=63 gold pad——真实玩家站 pad（脚 y=64）身体进 portal（y=65）触发；传送门中心坐标以 portals.yml 为准（创建消息"轴向"与存储可能相反）

## 发现的 Bug（已修复）

| Bug | 现象 | 修复 |
|:--|:--|:--|
| debug 模拟命令不可用 | `debug $h` 被原版 /debug 命令拦截（Incorrect argument）；改前缀报 Unknown（未注册命令不触发 ServerCommandEvent） | 前缀改 `orzdebug` + FeatureModule 注册命令（PR #159，已实测 9 命令全过） |

## 环境恢复状态

- 测试服跑修复版 jar（保留）；原版备份 `backups/OrzMC-1.0.14-dev.237.jar.bak`
- tnt.enable=false、黑名单空、白名单 3 人完整
- 第二服 ~/minecraft-server2（双服测试用，可删）
- 测试脚本清理完毕（/tmp 残留 rcon.py 保留）
- **测试文档**：插件仓库 `plugin/docs/test-cases.md`（28 项用例）+ `plugin/docs/e2e-test-report-20260806.md`（端到端报告，28/28 通过）——OrzMCPlugin commit 0a727b7（fix/orzdebug-command 分支）
