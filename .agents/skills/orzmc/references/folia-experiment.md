# Folia 迁移实验（2026-08-17，本地双服实测）
> ⚠️ **2026-09-03 迁移标注**：本地测试服已迁 MCSM 本机栈（mcs.{SERVER_NAME}.cn Docker 实例，数据在 `/Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/<uuid>`）。文中 `~/minecraft-server`、`~/folia-test` 路径及裸跑/symlink 机制为迁移前历史状态，已失效；现行拓扑见 `testing.md`。

> **双核心插件全景对比表（Paper vs Folia：核心差异/插件对应/渠道/功能/启用状态）已沉淀为官网文章**：OrzMCSite `content/posts/2.server/27.paper-vs-folia.md`（公开版，无内部路径/密码；版本号仅参考）。内部细节仍以本文件为准。
> 场景：评估本地测试服插件迁移 PaperMC Folia 核心的兼容性，并完成平替替换 + 数据迁移。
> 结论先行：**9 个不兼容插件全部解决（8 平替 + OrzMC 升级 Folia 版 1.0.18-dev.296 后自身支持），18 插件全绿；2026-08-18 起 Folia 服全面接管原测试服（端口 25565/19132 + Paper 地图 symlink + 全量配置/权限/白名单同步）。**

## 迁移全流程（总览，按序执行）

```
阶段 1 兼容性评估 → 阶段 2 平替选型 → 阶段 3 数据迁移 → 阶段 4 配置同步 → 阶段 5 全面接管 → 阶段 6 已知限制
```

| 阶段 | 关键动作 | 产物/结论 |
|:--|:--|:--|
| **1. 兼容性评估** | 复制全部 jar 到 Folia 服启动，看拒载清单 | 20 jar → 🟢12/🔴8；拒载=加载期错误（无标记即拒） |
| **2. 平替选型** | Modrinth `loaders=folia` 检索 + 功能覆盖验证 | 8 平替定稿（见插件矩阵）；OrzMC 等官方 Folia 版 |
| **3. 数据迁移** | 账号（BCrypt 复用）+ home（YAML→SQLite） | 359 账号 + 879 home，脚本化可复用 |
| **4. 配置同步** | 全量 diff → 定制值合并 + 关键文件复制 | paper-global/world-defaults/ops/封禁/usercache 等 |
| **5. 全面接管** | 端口换 Paper 的 + 地图 symlink | 25565/25575/19132 + 17G 世界零拷贝共享 |
| **6. 已知限制** | 命令方块被 Folia 架构性禁用 | 需插件/数据包替代（见下文） |

## 环境（2026-08-18 更新：Folia 已接管原测试服端口）

| 项目 | 原测试服 | Folia 测试服 |
|:--|:--|:--|
| 核心 | Paper 26.2-112（**已停运**） | Folia 26.2-4 BETA（2026-08-11） |
| 路径 | `~/minecraft-server` | `~/folia-test` |
| Java 端口 | ~~25565~~（已让出） | **25565**（接管 Paper 的） |
| RCON | ~~25575~~ | **25575**（接管，密码 orztest2026） |
| Geyser UDP | ~~19132~~ | **19132**（接管 Paper 的） |
| Geyser auth-type | offline | offline（2026-08-18 对齐 Paper；原 online 会触发 `MinecraftProfileNotFoundException 404`，offline 直连不查 XBL） |
| MOTD | `§e[Paper] 测试服-验证地图恢复状况` | `§e[Folia] OrzMC Test`（保留区分标识） |
| SkinsRestorer 警告 | `offlineModeWarning.enabled: false` | false（2026-08-18 对齐 Paper：屏蔽离线玩家「第三方启动器可能覆盖皮肤」警告，纯噪音；原 true 每次登录都发） |
| 白名单 | 开 | 开关**关**（`white-list=false` `enforce-whitelist=false`），但**列表已同步 139 玩家**（whitelist.json 复制） |
| 世界 | `~/minecraft-server/world`（17G） | **symlink → Paper 世界**（`~/folia-test/world → ~/minecraft-server/world`，零拷贝，2026-08-18） |
| 启动 | `./start.sh`（java -Xms2G -Xmx2G **-Dlog4j2.configurationFile="config/log4j2.xml"** -jar folia-26.2-4.jar nogui） | 同左（Paper start.sh 也已加同参数） |
| CustomWorldHeight | **已移除（2026-08-18 两端）**，jar 在 `plugins/.disabled/` | 已移除（同左） |

- ⚠️ **两服共享同一份世界（symlink）**：**绝不允许两服同时启动**（会损坏地图）；Paper 服若再启动需先删 `world/session.lock`，且 Paper 服端口已让出需另行规划
- Folia 核心下载：`https://papermc.io/downloads/folia` 页面内嵌 JSON（fill-data 直链，sha256 校验）
- ⚠️ Folia 26.2 目前只有 **BETA**（26.1.2 才是 STABLE）；Folia 版本节奏比 Paper 慢

## Folia 兼容机制（实测验证）

- **无 `folia-supported: true` 标记 → 直接被拒载**（连加载都不尝试）：
  `DirectoryProviderSource Error loading plugin: Could not load plugin 'X' as it is not marked as supporting Folia!`
- **标记 true ≠ 真兼容**：PaperMC 文档明示「声明标记不足以保证支持」——WorldGuard 官方承认 experimental
- **连带依赖效应**：依赖插件被拒载 → 依赖方也无法加载
  （实测：Vault 被拒载 → EzShops `UnknownDependencyException: [Vault]` 连带挂）
- **检索 Folia 插件必须用 Modrinth `loaders` 含 folia**；❌ Hangar API `supportedPlatforms` 只标 PAPER（WorldEdit 支持 Folia 也只显示 PAPER），不可用作 Folia 检索依据

## 插件兼容矩阵（20 jar → Folia 实测）

### 🟢 原声明支持（10）→ 保留
WorldEdit 7.4.5 / WorldGuard 7.0.18（experimental）/ LuckPerms 5.5.77 / Geyser 2.11.1 / ViaVersion / ViaBackwards / ViaRewind（5.11.0）/ SkinsRestorer 15.12.5 / EzShops 2.5.9（依赖 Vault，平替后恢复）/ CustomWorldHeight 2.2.0

### 🔴 不兼容（9）→ 平替方案

| 原插件 | 平替 | 版本 | 合并策略 |
|:--|:--|:--|:--|
| EssentialsX 2.22.0 | **EssentialsC** | 4.2.8 | 🔀 吸收 GetMeHome（自带 /home 多 home） |
| Vault 1.7.3 | **VaultUnlocked** | 2.20.2 | ✅ drop-in 平替，顺带恢复 EzShops |
| GriefPrevention 16.18.7 | **GriefPrevention3D** | 18.3.4 | ✅ GP 官方 fork + Folia fix + 3D 分区 |
| LoginSecurity 3.3.2 | **SimpleLogin** | 1.16.7 | ✅ Modrinth loaders 含 folia；2026-08-18 实际部署（AuthMe-6.0.0-Folia.jar 在 .disabled/） |
| DeathChest 3.0.1 | **AxGraves** | 1.29.0 | 🔀 吸收 BackOnDeath（死亡箱 + 回死亡点） |
| BackOnDeath 0.4 | ↑ 并入 AxGraves | — | /axgraves tp 回死亡点 |
| GetMeHome 3.0.0 | ↑ 并入 EssentialsC | — | /home 多 home |
| EzShops（连带） | VaultUnlocked 后恢复 | — | 依赖链修复验证 ✅ |
| **OrzMC 1.0.18** | **升级 1.0.18-dev.296**（2026-08-17 发布，PR #191 Folia CI smoke） | — | jar 内 `folia-supported: true` 确认；**Folia 服已加载运行**（创建默认配置 + 权限组自动初始化） |

**最终**：20 jar → 18 全绿（无拒载）。

### 平替关键细节
- EssentialsC：`Successfully hooked into Vault`；home/tpa/warp/kits 全套；数据在 `databases/homes.db`（SQLite）
- VaultUnlocked：`Registered Vault permission & chat hook`（LuckPerms 桥接）
- AuthMe：首次启动经 SpigotLibraryLoader 下载 MySQL/BCrypt 等库；`passwordHash` 默认 SHA256 **必须改 BCRYPT**（见迁移）；GeoLite 下载失败=可选 GeoIP 无 MaxMind 凭据，无害
- AxGraves：`/axgraves tp` 无参=传送回最近坟墓

## 数据迁移（2 项已完成，其余无数据）

| 源插件 → 目标 | 数据量 | 方法 |
|:--|:--|:--|
| LoginSecurity → SimpleLogin | 359 账号 | BCrypt 哈希直接复用（LS 算法 7=`$2a$10$`）；2026-08-18 部署 SimpleLogin 1.16.7 后接入（AuthMe 中间方案已弃用，jar 在 .disabled/） |
| GetMeHome → EssentialsC | 186 玩家 / 879 home | homes.yml (YAML) → homes.db (SQLite)，字段一一映射，同名冲突跳过 |

**无需迁移**：Vault（纯 API）/ DeathChest（临时容器+审计）/ BackOnDeath（内存态）/ EssentialsX（原服从未真正用起来，userdata 0 homes）/ GriefPrevention（ClaimData 空，无领地）。
**OrzMC 配置**：2026-08-18 已迁移（config 定制值合并 + easybot.yml 完整复制，见「全面接管」章节）。

### 迁移脚本（技能 scripts/，均已参数化 + --dry-run）
```bash
python3 ~/.hermes/skills/gaming/orzmc/scripts/migrate_loginsecurity_to_authme.py [--ls-db X --authme-db Y] [--dry-run]
python3 ~/.hermes/skills/gaming/orzmc/scripts/migrate_getmehome_to_essentialsc.py [--yml X --db Y] [--dry-run]
```

### 迁移后验证
- AuthMe：日志 `AuthMe 6.0.0 successfully enabled!` + `SELECT COUNT(*) FROM authme` = 359（⚠️ 2026-08-18 后实际部署改用 SimpleLogin 1.16.7，AuthMe jar 在 .disabled/；SimpleLogin 数据经 Modrinth 渠道，登录接入后须实测密码校验）
- 密码校验需真实登录测试（迁移工具无法验证 BCrypt 密码本身）
- EssentialsC：`SELECT COUNT(*) FROM homes` = 879；坐标样本与原 yml 一致

## 全面接管原测试服（2026-08-18）

Folia 服实验成功后全面接管原测试服（两服停运 → 单服运行）。

### 1. 地图（磁盘不足方案：symlink 零拷贝）
- 磁盘仅剩 7.9G < 17G 地图 → **不能复制**，用符号链接：`~/folia-test/world → ~/minecraft-server/world`
- Folia 原有全新世界备份为 `world.orig-newgen`（14M，可删）
- 启动前必须删 `world/session.lock`
- ⚠️ **两服共享地图，绝不同时启动**；Paper 服再启动需先让出端口

### 2. 端口接管（Folia 改用原 Paper 端口）
`server.properties`: `server-port=25565`、`rcon.port=25575`；Geyser `port: 19132`（改后 Java/Bedrock/RCON 三端口均与原 Paper 一致）

### 3. LuckPerms 四档权限系统（H2 数据库替换）
- 两服同版 LuckPerms 5.5.77 → **停服后直接复制** `plugins/LuckPerms/luckperms-h2-v2.mv.db`（229KB）
- 备份原 Folia db 为 `.folia-orig`；删除 `luckperms-h2-v2.trace.db`（锁文件）
- 验证：启动后 OrzMC **无「已创建组」日志** = 四档组（default→member→builder→admin + rank track）已从 Paper 库加载，未重复创建；Vault/F3F4Perms/AuthMe 均成功 hook
- ⚠️ LP 命令经 RCON 不回显（异步 dispatch），验证靠日志

### 4. OrzMC 配置迁移（新版模板为基底合并）
- **config.yml**：Folia 新版模板（含 guard/chat/login_rate_limit/player_notify 等新键）为基底，应用 Paper 定制值：`backup_retention_count: 1`、`entity_teleport_enabled: false`（Paper 旧版模板缺新键，不能整文件覆盖）
- **easybot.yml**：完整复制（网关 api_server/ws_server/api_key、QQ 群、飞书/QQ 平台会话）→ Folia 直连 EasyBot 认证成功
- guide_book/ip_blacklist/permission/portals/templates：0 差异或新版已含旧版内容，不动
- ⚠️ 两服同时连同一 EasyBot 网关，消息互通（测试期可接受）
- ⚠️ `whitelist.kick_message.qq_group_id` 未配置警告无害（easybot.qq_group_id 兜底，Paper 同样）

### 5. 服务端配置全量同步
| 文件 | 处理 |
|:--|:--|
| ops.json | **合并**（Paper 24 OP + joker = 25，勿覆盖） |
| banned-players.json / banned-ips.json | 复制（3 玩家 + 4 IP） |
| usercache.json | 复制（356 条） |
| help.yml | 复制 |
| config/paper-world-defaults.yml | 4 处对齐：anti-xray（enabled/engine-mode=2）、tracking-range-y.enabled、prevent-moving-into-unloaded-chunks、enderpearl exploit |
| config/paper-global.yml | proxies 段对齐：bungee-cord online-mode **true**（Paper 实值）、velocity false；`threaded-regions` 是 Folia 特有段**必须保留** |
| spigot.yml / bukkit.yml / wepif.yml | 语义一致，不动（仅 YAML 数值格式 -1 vs -1.0） |
| server.properties | 仅 MOTD 保留 `[Folia]` 标识 |

- ⚠️ **坑：`paper-global.yml` 的 `online-mode` 是 proxies（Bungee/Velocity）认证，≠ server.properties 的 online-mode**——前者 Paper 实值 true（默认），曾误改成 false，后修正
- ⚠️ `banlist` 命令被 EssentialsC 接管（显示 EssC 自己的存储），原版封禁文件已由 Bukkit 启动时加载生效，验证看文件格式 + 日志

## Folia 线程模型红线（2026-08-19 /review approve 死锁实战，OrzMC PR #196 已修）

> **任何插件开发/修复在 Folia 上遇到「卡服/超时/状态不一致」先读本节。** 完整案例见插件仓库 `docs/dev/folia-luckperms-gotchas.md`。

### 核心红线（最高优先级）

1. **服务器调度线程（global/region）绝不能同步等待 LuckPerms 的异步 future**（`loadUser`/`saveUser`/`track.promote` 的 `.get()/.join()`）：LP 的 future 完成回调**调度回服务器同步线程执行**——在 global/region 线程上同步等待 = 回调排在自己后面，必自锁（实测三阶段：修复前 132s 死锁卡服 → 转 global 线程后 3s 必超时 → 异步化才根治）。
2. **授权/晋升类操作必须异步化**：`ReviewHandler` 返回 `CompletableFuture<Boolean>`，LP 操作在**自己管理的异步线程**（`Bukkit.getAsyncScheduler().runNow`）执行，框架异步等待结果后再落状态。
3. **状态一致性**：授权结果与业务状态必须原子一致（LP 已晋升 + 申请仍 PENDING = 漂移 → 重复 approve 会把 member 再 promote 到 admin 越级）。
4. **并发防越级**：异步授权后两个管理员同时 approve 同一申请会并发操作同一 LP User → `normalizeSingleGroup` 时序交错 → 跳过中间档越级。必须 **in-flight 去重**（`ConcurrentHashMap.newKeySet()` requestId 粒度占位，处理完 `whenComplete` 释放）；授权在途时 reject/cancel 也要互斥（占位前置）。
5. **线程判定**：`Bukkit.isGlobalTickThread()` 只判 global，**region 线程不命中**——离线读（`loadUser` 同步等待）在 region 线程同样会卡住该 region 所有玩家 tick。判定「任意服务器调度线程」需补 `isRegionOwnedByCurrentThread()`（Folia 独有 API，paper-api 编译期无此方法 → **反射调用**，Paper 上 null → false）。任意调度线程离线缓存未命中一律降级返回 null（离线读留给 bot/异步线程）。
6. **调度工具**：用 `ServerFacade.runSync`（Folia GlobalRegionScheduler / Paper 主线程），勿用 removed 的 BukkitScheduler；嵌套 runSync 在同步线程直接内联；`done.join()` 必须带超时（`done.get(3s)`）防调度器停摆永久挂起。
7. **读路径**：查当前组等优先 `um.getUser(uuid)` 在线缓存（不阻塞不调度），仅离线才异步加载。

### 修复演进（四轮，每轮都是教训）

| 轮次 | 方案 | 结果 |
|:--|:--|:--|
| ① | LP 操作转 global 线程 | 死锁→自锁 3s 超时 + **状态漂移**（promote SUCCESS 但申请 PENDING） |
| ② | runSync 超时 + 读路径免 G 往返 | 仍超时（global 上等 LP future 本质自锁） |
| ③ | **异步化**：ReviewHandler → CompletableFuture，LP 在异步线程执行 | 真机 approve 全流程通过，零超时零漂移 ✅ |
| ④ | 合并前审查加固：in-flight 去重、region 线程离线读降级、写盘加锁 | 并发/阻塞面收口 ✅ |

**教训**：修线程问题第一问是「这里能不能不等」，而不是「换个线程等」。

## 传送门 transfer 补偿方案（PR #195，2026-08-18 合并 b7d4b86）

> PlayerPortalEvent 在 Folia 不触发 → PlayerMoveEvent 区域检测补偿跨服 transfer。以下为实施沉淀（评审 5 轮迭代验证），改 portal 相关代码前必读。

### 传送门几何（触发判定的地基，实测+源码实证）
- `PortalBuilder`：`baseY = 建造者脚方块`，框架底黑曜石行在 `baseY`，金块垫层 `baseY-1`，**`cy = baseY + 2`** → `rehydrateInterior` 写入的内部格 y ∈ **{baseY+1, baseY+2, baseY+3}**（3 格高，x/z 按轴 2 格宽）
- **玩家脚底 `getTo()` 在 baseY，永远比内部格低 1 格** → 只查脚底格 = 永不触发（R4 评审抓出的严重几何回归）
- ✅ 正确匹配：**身体两格**——脚底格 `findTargetExact(to)` 未命中再查躯干格 `(x, blockY+1, z)`；水平方向**精确命中**（`findTargetExact` 无邻域），垂直方向身体两格兜底

### 精确 vs 邻域容差（误触发面）
- `findTarget`（3×3×3 邻域容差）只用于 **Paper 路径**（玩家已站在门内，容差兜对齐偏差）
- **move 路径必须 `findTargetExact`**（水平精确）：邻域容差会把触发区膨胀为「门 + 四周 1 格」，密集建筑/走廊路过玩家会被反复误拉走（G-A）
- 躯干格扩展不产生可达误触发面：内部格正下方恰是框架底黑曜石行，站立/行走玩家无法占用

### 双路径与事件语义
- **5s 冷却双路径共享**：权威判断在 `transfer()` 内（`isOnCooldown` + `lastTransfer` CHM，UUID→时间戳）；`handleMove` 前置快速跳过省 findTarget/auth 开销
- **冷却前置**：`handle()`（Paper 路径）在 setCancelled 前先查冷却——冷却内不接管事件（不取消原版传送），保证「取消 ⇔ transfer」自洽，避免「取消了但没传」卡门状态；副作用：5s 内二次激活会放行原版传送（已文档化接受）
- **事件优先级 HIGHEST**：反作弊/区域防护（Grim/Vulcan）多在 HIGHEST 取消移动，默认 NORMAL 看不到取消态 → `@EventHandler(priority = EventPriority.HIGHEST)` + `handleMove` 开头 `if (event.isCancelled()) return`
- **认证 fail-open**：LoginSecurity 反射检查失败默认放行（`PlayerAuthenticationService` catch → true）+ WARNING 日志；认证决策注入 `Predicate<Player>` 以便单测覆盖未认证分支（测试环境无 LoginSecurity 恒 true）

### transfer 命令派发
- Folia 上必须 **global region 线程**派发（`server.runSync`）；用 `executeConsoleCommand`（捕获 `ConsoleCommandResult.dispatched`）而非 `executeConsoleCommands`（无结果回调）——**失败打 WARNING**（目标服不可达时不再静默，玩家被取消一次后第二次放行原版进下界至少日志有痕）

### 评审教训（流程价值）
- 本地 claude review 把关流程有效：R4 抓出 findTargetExact 几何回归（测试 mock 掉 portalService 掩盖了真实几何）→ **测试必须覆盖真实几何**（脚底 null + 躯干命中 → transfer 的回归用例），不能只 mock 返回值
- 补偿路径固有差异（已文档化接受）：无法取消原版下界传送（transfer 失败玩家进下界）、触发时机=踏入内部格当 tick（远早于 Paper 4s 激活）

## 坑与经验

1. **Folia 拒载是加载期错误**，非运行时错误——`plugins` 列表红色 = 未启用，jar 可以留在目录
2. **改 Folia 服配置后必须重启**（MOTD/白名单/Geyser 端口同理）
3. **Geyser 双服共存要改 UDP 端口**（19132→19133），否则 bind Address already in use
4. **AuthMe 是库重插件**：首次启动要下 maven 库（mysql/argon2/bcrypt 等 20+ jar），启动时间显著变长
5. **SQLite 迁移时目标服可在线**（WAL 模式），但保险起见迁移后重启一次让插件重载
6. F3F4Perms 依赖 **packetevents**（硬依赖 depend），两者都支持 Folia；权限 `f3f4perms.use` 默认 op，让有 /gamemode 权限的玩家用 F3+F4/F3+N 热键
7. ⚠️ **CustomWorldHeight 配置必须同步**：Folia 若沿用默认模板（example-world-name）→ 世界按 384 高度解析 Paper 的 1088 世界 → `Ignoring heightmap data ... expected: 37, got: 52` 错误 + 命令方块传送等跨区块操作异常。同步后错误方向反转（expected: 52, got: 37）= 世界内新旧区块高度图混存（CustomWorldHeight 2026-08-15 才启用，旧区块 384 生成）——**无害**（高度图只是缓存，忽略后自动重算，Paper 服同样存在）
   - **⚠️⚠️ log4j2 过滤最大坑（2026-08-18 实测修正）**：`config/log4j2.xml` **不会自动加载**！光放文件重启无效（日志格式无 [%logger] 即未加载）。**必须 start.sh JVM 参数显式指定**：`-Dlog4j2.configurationFile="config/log4j2.xml"`。此前「放 config/ 重启即可」的结论是假象（当时 CustomWorldHeight 在位警告本来就少/方向匹配，并非过滤生效）
   - **⚠️⚠️⚠️ paperclip 必须绝对路径（2026-08-18 实测）**：Folia 是 paperclip bootstrap（`folia-26.2-4.jar` 下载/解包真实 jar 到 `versions/26.2/` 后另起子进程），`-Dlog4j2.configurationFile="config/log4j2.xml"` **相对路径在子进程下解析失败 → 回退内置配置 → 过滤无效**（实测 976 条警告刷屏）。**必须绝对路径**：`-Dlog4j2.configurationFile="/Users/bot/folia-test/config/log4j2.xml"`（Paper 是普通 jar 直接加载，相对路径可用；但两服统一用绝对路径最稳）。验证法：召唤实体到 1088 格式 region（如 r.-5.-54）强制加载 → 警告数仍 0 = 生效
   - **根治（日志层，2026-08-18 实测归零）**：`config/log4j2.xml` 用 **Paper 官方模板**（GitHub master `paper-server/src/main/resources/log4j2.xml`）+ Root 级 `RegexFilter regex="Ignoring heightmap data for chunk" onMatch="DENY" onMismatch="NEUTRAL"` → 警告归零（加 JVM 参数后实测 9108 → 0）
   - **易踩坑**：① 必须 JVM 参数加载（见上）；② **Logger level 挡不住具体消息**，必须 RegexFilter（放 Root `<filters>` 段，官方模板的 MarkerFilter 旁）；③ 改配置后必须重启
   - 警告反复刷的机制：磁盘旧格式高度图加载时被忽略 → 内存重算 → **不写回磁盘**（除非区块 dirty）→ 每次重启/新区块加载都重新警告
   - **✅ CustomWorldHeight 已移除（2026-08-18 两端 Paper+Folia）**：全量扫描（nbtlib 解析 6380 region / 1,471,866 区块，scan_final.py）实证 **0 个区块含高空方块数据**（Y>319 的 section 有壳无 block_states=纯空气）→ 去掉零数据丢失。1088 格式区块 17,296（1%，83 个 region，玩家新探索区+出生点重载）**不会自动恢复也不会消失**——随玩家活动「加载→保存」循环自然收敛为 384 格式；未加载的保持 1088 文件但读取按 384 解析，游戏无影响
   - ⚠️ 扫描脚本坑（2026-08-18）：字节解析 sections 定位偏移 **idx+11**（1+2+8，idx+10 会指到名字末字符 's' 0x73 全失败）；`sections` 只存非空 section 且空 section 无 block_states 字段（「有 section」≠「有方块」）；可靠方案用 `nbtlib.File.parse(io.BytesIO(raw))` 全量解析（慢但准，6380 region 约 48 分钟，8 进程）
8. ⚠️⚠️ **命令方块在 Folia 被架构性禁用**（2026-08-18 实证）：官方 issue #429「fundamentally disabled」+ #485 请求加 `force-enable-command-blocks` 开关被关 `not_planned`。**无论 `enable-command-block` 怎么配，命令方块都不会执行任何命令**（含传送）——迁移后命令方块传送失效是此原因，非配置问题。本地复现（2026-08-18）：setblock 放置 `repeating_command_block{Command:"say ...",auto:1b}` 成功（无报错）但 8s+ 零输出；`execute if block` 经 RCON 触发 NPE（`Level.getCurrentWorldData()` null，Folia 26.2-4 RCON 上下文 bug，游戏内是否同样待验证）。**⚠️ 替代路线收窄（官方 FAQ 2025-08 + RCON 实证）：Folia 共禁用 24 个命令——bossbar/clone/data/datapack/debug/function/item/loot/reload/return/ride/rotate/schedule/scoreboard/spectate/spreadplayers/tag/team/teammsg/tick/trigger/perf/saveall/restart**——命令方块地图核心依赖（scoreboard 任务/tag 标记/trigger 按钮/schedule 定时/function 数据包）**全断**，`/function`+`/datapack` 被禁 = **数据包函数替代路线不通**（早前记录的「数据包函数替代（触发机制受限）」作废）。可用命令实测：execute/tp/give/effect/setblock/fill/summon/say/tellraw/title/playsound/advancement/worldborder/time 正常；⚠️ `gamerule` 在 26.2-4 注册了但任何参数都报 Incorrect argument（疑似 BETA bug，待查）。无现成 Folia 命令方块模拟插件（Modrinth 检索 2026-08-18：commandblocks 插件无 folia loader；CraftBook Folia 支持 PR #1315 未合）。⚠️ 世界命令方块现状（2026-08-18 修正，此前「0 命令方块」结论是我扫描脚本 bug，作废）：**测试服世界有 1262 个命令方块**（overworld 1252 / the_end 9 / the_nether 1，全为普通 command_block，auto=1 保持激活 246 个）。分布热区：r.-1.-2（303 个，主活动区 x-482~-432/z-561~-519）、r.0.-1（267）、r.-6.-55（226，传送目标主基地 -2767 70 -28039）、r.39006.39006（116，x~1997 万超远区）、r.-1.-1（95）、r.0.0（58，出生点冒险地图：附魔台密室/幻丝迷宫/机关/kill 陷阱/give 奖励/NPC 牌子）、r.-1.0（51）。命令分类：kill 239 / title 176 / tp 162 / 空 156 / execute 85 / give 80 / say 59 / effect 52 / spawnpoint 51 / playsound 41 / **scoreboard 35 / tag 22 / team 2（59 个依赖 Folia 被禁命令，模拟方案也无法恢复）** / gamemode 24 等。✅ **Folia 只禁执行不删数据**（加载保存多次后磁盘 NBT 完好）→ 回退 Paper 100% 恢复。**扫描脚本坑（2026-08-18 实测教训）**：① NBT list 中 compound 元素**无 type 字节**（直接以 entries 开始），流式解析多跳 1 字节 = block_entities 全漏（误报 0）；② `find -name "*.mca"` 会把 1.14+ 的 entities/poi 目录也算进去（region 实际 10713 个，非 21689）；③ 16G 内存宿主多进程扫描 worker 会被系统杀（OOM 边缘），**单进程串行最稳**（~19 region/s 小文件，大 region 慢）。**ExecutableEvents 实测（2026-08-19，3.26.8.10 + SCore 5.26.8.10 on Folia 26.2-4）**：✅ 加载成功（SCore 硬依赖必须装，plugin.yml 注释了 depend 但代码需要 com.ssomar.score API 类；首次启动 SpigotLibraryLoader 下载 maven 库）；✅ 配置加载正常（**events/ 目录一个 .yml 文件 = 一个事件**，`events: {name: {type, world, actions: [{type: COMMAND, command}]}}`，`/ee reload` 生效）；❌ **事件监听不触发**——PLAYER_WALK（bot 真实行走 8 格）/ PLAYER_JUMP_EVENT（跳跃 5 次）/ `/ee debug` 全零输出（debug 已开），判定事件系统与 Folia 分区线程模型不兼容 → **当前版本在 Folia 26.2 上不可用，插件替代方案整体不可行**（WarZ 系列等 1.21+ 插件同理存疑）。⚠️ 防重登限制来源=**GriefPrevention3D 的 Spam.LoginCooldownSeconds（默认 60）**，踢出消息 "You must wait X seconds before logging-in again"，改 0 解除（2026-08-19 已改，重启生效）。方案矩阵：A 回退 Paper=100% 恢复（插件矩阵反向回退）；B Folia 主服+Paper 地图子服；C 自研模拟插件=仅覆盖简单命令（tp/give/effect/say 等，依赖被禁命令的逻辑无法恢复）；D 接受限制按需替代（传送→OrzMC 传送门/传送弓、EssentialsC warp；公告→EasyBot；奖励→kit/商店）
9. ⚠️ **`paper-global.yml` 的 `online-mode` ≠ server.properties 的 online-mode**：前者是 proxies（Bungee/Velocity）段认证，Paper 实值 true（默认）；曾误把 Folia 改成 false 造成不一致，已修正
10. ⚠️ **迁移服务端 JSON 文件看语义不看字节**：ops.json 要**合并**（Paper 24 OP + joker = 25，直接覆盖会丢 joker）；banned-* 直接复制（Bukkit 启动时加载，`banlist` 命令被 EssentialsC 接管显示其自身存储，验证看文件 + 日志）
11. **磁盘不足时地图用 symlink 零拷贝**：`ln -s paper/world folia/world`（17G 无法复制时唯一方案）；⚠️ 两服共享地图绝不同时启动（session.lock + 数据损坏风险）
12. **Folia 启动前必须删 `world/session.lock`**（symlink 共享场景下尤其重要，Paper 停服会残留）
13. ⚠️ **Essentials tpa「没有授受传送请求的权限」（2026-08-18 修复）**：现象 = 玩家 `/tpa <玩家>` 后提示「没有授受传送请求的权限」（Essentials 消息 `teleportNoAcceptPermission`）。根因 = **OrzMC 权威权限文档 `plugin/docs/permission-groups.md` member 组漏配 `essentials.tpaccept`**（只有 tpa/tpahere 发请求/邀请，无接受权限；Essentials 权限无默认值=非 op 默认拒绝；与 OrzMC 实体传送拦截 `entity_teleport_enabled: false` 无关）。修复 = 文档补行 + `gen_perm_commands.py` 重新生成 + RCON 执行 `lp group member permission set essentials.tpaccept true`（H2 落库验证）。⚠️ 三端同步

## 已知限制（Folia 架构性，无法配置解决）

| 限制 | 官方依据 | 影响 | 替代方案 |
|:--|:--|:--|:--|
| **命令方块被禁用** | issue #429「fundamentally disabled」+ #485 `not_planned` | 所有命令方块不执行（含传送/红石触发逻辑）；**连带 24 命令被禁**（含 /function /datapack /scoreboard /tag /schedule，数据包函数路线不通） | 回退 Paper（100%）/ Paper 地图子服 / 自研模拟插件（仅简单命令）/ 接受限制按需替代 |
| **PlayerPortalEvent 不触发**（2026-08-18 实测+反编译实证；✅ 已解决 = OrzMC PR #195 合并 b7d4b86，2026-08-18） | 下界传送门走 `portalAsync` 新路径，`callPlayerPortalEvent` 无任何调用者 | 依赖该事件的跨服 transfer 完全失效（玩家踩传送门只触发原版维度传送） | OrzMC PR #195 已合并：PlayerMoveEvent 补偿路径（方块坐标变化+interiorTargets 命中→transfer 命令+5s 冷却；仅 Folia 生效，Paper 保持原路径）。`EntityPortalReadyEvent` 语义不符（只能改目标世界不能替换 transfer） |
| EssentialsC Scoreboard 不支持 | Folia 分区线程模型 | 计分板功能不可用（启动 WARN） | 其他计分板插件 |
| OrzMC 需 Folia 版 | 旧版无 `folia-supported` 标记 | 1.0.18-dev.296 起已解决 | ✅ 已升级 |

## 相关文档
- 兼容性调研方法论 + 替代品清单 → 本文件
- 三端配置对比 → `three-end-config-drift.md`
- EasyBot 网关（Folia 服无 OrzMC 时无机器人链路）→ `easybot-gateway.md`
