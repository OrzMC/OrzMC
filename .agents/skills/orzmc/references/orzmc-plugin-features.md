# OrzMC 插件功能事实库（行为/配置语义，源码实证）

> 从 `SKILL.md` 外置（2026-11-10 整理）。这些都是**插件内部行为与配置语义**，改动前先读；SKILL.md 只留索引。
> 相关：`plugin-baseline-legacy.md`（历史版本演进）、`permission-system` 细节见 `permission.md`、`permission-impl.md`。

## 1. GeoIP 内网误拦截（2026-08-06 修复，OrzMC 1.0.15）

MCSM `allow_country_code=[CN,JP,TW]` 时内网玩家（192.168.x/10.x）被拦截——geojs.io 无法解析私有段返回未知国家码。1.0.15 加内网 IP 短路（RFC1918/环回/CGNAT 直接放行，公网仍检查）。

- OrzMC 配置读取为实时（改 config.yml 后 **`/config reload` 即生效**，无需重启）。
- ⚠️ 2026-08-11 修正：命令是 **`/config reload`**（根命令 `config`，别名 `cfg`；源码 `FeatureModule.java` `commands.register(node, "配置管理", List.of("cfg"))`）——技能旧写 `/orzconfig reload` 是错的（返回 Unknown）。
- 临时缓解 = `allow_country_code` 改 `[]`。
- ⚠️ **`/config set` 改不了国家限制（2026-08-13 源码实证）**：`geoip.allow_country_code` 未注册进 `ConfigPath` 注册表（22 项只覆盖 whitelist/maintenance/tnt/command_policies/easybot/templates），且 `OrzConfigCommand.parseValue` 只支持 Boolean/Integer/Long/Double/String **不支持 List** → 只能改 config.yml + `/config reload`。

## 2. `permission.yml` 的 reload/重启语义（2026-08-15 源码实证）

- `permission.yml` 的 `config.member-threshold-hours`（default→member 自动晋升阈值，默认 10 小时）**改不了 `/config set`**（未注册），且是**构造注入**（`FeatureModule` 装配时 `RankService(permissionStore, ..., memberThresholdHours(), ...)` final 字段）→ 改文件后**必须重启**才生效（reload 无效）。
- 时长数据源 = 服务器原生 stats（`world/players/stats/<uuid>.json` 的 `minecraft:play_time`，tick÷1200=分钟）。
- `command_policies.tpbow.admin_only`（Boolean）是**唯一能 `/config set` 的注册路径**（`/config set command_policies.tpbow.admin_only true` = 普通玩家禁用传送弓），但拦截器链装配时固定 → 同样**需重启生效**。
- ⚠️⚠️ **改 `permission.yml` 必须「先 reload 再重启」，否则修改被回写覆盖**：该配置在 `ConfigService.setup()` 被 `markAlwaysSave("permission")`；停止时 `onDisable→tearDown→configService.tearDown→saveDirtyConfigs()` 会用**内存快照整体写回磁盘**，而快照是启动时加载的旧值 → 运行中手改不 reload，重启即被旧值覆盖。**且运行中 `PermissionStore.save()`（玩家提交审核）也会 `saveConfig` 同理会覆盖**。
  正确流程：① 改 permission.yml → ② `/config reload permission`（磁盘新值进内存）→ ③ 重启（写回新值 + 装配生效）。验证：重启后 grep 日志或 `/config dump` 确认新值。

## 3. `member-threshold-hours` 的隐藏语义（2026-08-15 源码实证，OrzMC 1.0.17）

- **0 值 = 进服秒升 member**：`checkPromotion()`（玩家上线异步触发，`OrzRankEvent.onPlayerJoin`）判定 `playtime < memberThresholdMinutes()`（=0×60=0）永远 false，新玩家（无 stats 文件返回 0）也满足 → 只要当前组是 default 立即 `promote()`。LP track 幂等（已是 member+ 不重复升），一次性不回退。
- **不支持小数**：`PermissionStore.memberThresholdHours()` 返回 `int`（`cfg.getInt`），YAML 写 `2.5` 被 Bukkit **静默截断**为 `2`；写 `"2.5"`（字符串）parseInt 失败**回退默认 10**；`0.5` 截断成 `0` = 秒升。要半小时级粒度须改源码（`RankService` L28 `final int` → double + L86 `* 60L`）。
- 判定链路：`RankService.checkPromotion` L65-77 → `OrzRankEvent.onPlayerJoin`（异步，不阻塞主线程）→ stats 时长源 `world/players/stats/<uuid>.json`。

## 4. 维护 MOTD 文案模板化（2026-09-02，#236 已合，OrzMC 1.0.24-dev）

- 维护 MOTD 文案从 config.yml `maintenance` 段迁到 **templates.yml**（`maintenance_motd_backup/optimize/manual` 场景文案 + `maintenance_motd_progress_line` 进度行，占位符 `{stage}/{percent}/{eta}`）。
- **MOTD/登录拦截/踢人 4 处统一走 `MaintenanceModeService.renderMotdText`**：无进度时占位符自动清空防字面量；场景模板含占位符则不追加独立进度行；未写占位符且 backup/optimize 有进度自动追加 progress_line；默认值带场景词（backup=「服务器地图备份中，请稍后再试」）。
- **改文案 = 编辑 templates.yml 4 键 → `/config reload` 热生效**（不再支持 `/config set`）。
- ⚠️ 升级时旧 config.yml `maintenance.*_maintenance_motd` 自定义值须手动搬到 templates.yml；模板缺失走代码 fallback 零告警（同 prison 键策略，不入 `TemplateKeys.ALL`）。

## 5. prison 坐牢权限组（2026-09-02，#235 已合，OrzMC 1.0.24-dev）

作弊玩家过渡手段——坐牢 = 全禁权限（仅聊天 + 牢房传送），不封号。

- **操作**：`/prison <玩家> on|off`（管理员；恢复原组 + 原位置）。
- **配置**：config.yml `prison.cell_location: world,x,y,z[,yaw,pitch]`（各服独立，改后 `/config reload`；**默认 `world,0,100,0` 是空中示例值，正式须配封闭牢房**；未配置/世界未加载/坐标非法 → 回退玩家世界出生点）。
- **特性**：坐牢玩家走 LuckPerms `prison` 组（独立 track，重进**不自动回四级**——`RankService.checkPromotion` 跳过 prison 玩家；原组存 meta 键 `prisoner_original_group`）。
- **守卫/拦截（review 加固）**：`LuckPermsPromoter` promote/demote 对坐牢玩家拒绝（防手动升降级删节点放出牢房）；`PrisonDenyInterceptor` 拦截 tpbow/guide/menu/portal/apply/rank 等移动工具命令；LP 落库失败内存回滚；join 延迟 tp 兜底。
- **群消息**：`prison_imprisoned` / `prison_released` 模板键（templates.yml，排除 `TemplateKeys.ALL` 缺失走代码 fallback 零告警）。
- ⚠️ 管理员升降级坐牢玩家须先 `/prison off` 释放。

## 6. 备份/优化完成消息耗时中文化（2026-08-13，PR #171，OrzMC 1.0.17-dev）

`WorldMaintenanceService.formatDuration(ms)` 毫秒→中文分级（<1 秒=`854毫秒`、<1 分=`35秒`、<1 小时=`2分35秒`、≥1 小时=`1小时2分3秒`；秒四舍五入、负值按 0、小时级补 0 分占位）。

- done/error 模板新增变量 `duration_human`（**保留 `duration_ms` 兼容旧模板**）。
- 模板键 = 4 处联动：`templates.yml` 默认值 + `Templates.java` fallback + `TemplatePlaceholderValidator` 白名单 + `WorldMaintenanceService` 传参（⚠️ **漏注册白名单 → ConfigHealthCheck 测试挂**，报「模板变量未知: templates.maintenance_backup_done {duration_human}」）。

## 7. MC 26.2 原生命令/聊天防刷（2026-08-12 反编译实证）

- server.properties：`command-spam-threshold-seconds` / `chat-spam-threshold-seconds`（26.2-pre1 起，默认 10）。
- **真实机制（勿被名字误导）**：不是「每秒 N 条」，而是**爆发计数器**——`TickThrottler(20, 20×N)`：每条命令计数 +20，每 tick 衰减 -1（排水≈1 命令/秒），计数 ≥20×N 时踢出 `Kicked for spamming`。→ 任何持续 >1 条/秒的命令流迟早踢；45 条/秒时阈值 100 也只撑 ~2.3s。
- **OP/单人房主豁免**（bytecode：isOp 检查跳过踢出）→ 管理员永远遇不到。
- ⚠️ **设 0 反而每条命令都被踢**（`TickThrottler.isIncrementAndUnderThreshold` 缺 0 保护，GitHub issue #14114）→ 要放宽用大数值，别设 0。
- 触发实例：Litematica 粘贴原理图默认走 `pasteUseFillCommand`（/fill 流 45-104 条/秒）→ 反复被踢（阈值 100 只撑 ~2.3s，治标不治本）。
- **配置解法（2026-08-12 已落地三端）**：踢出时间 t=N/(R−1) 秒，要解决需 **N > 峰值速率 × 最长连续粘贴秒数**；三端 server.properties 已统一设 **100000**（104 条/秒时连续 ~16 分钟才触发）。替代解：WorldEdit `//paste`（一条命令）、关 `pasteUseFillCommand` 改逐方块放置、或给玩家 OP（豁免）。
- 另：server 启动会重写 server.properties 头部时间戳但保留值（PUT 改文件 → 重启流程安全）。

## 8. 权限系统四组（2026-08-06 实施，LuckPerms）

`default`（新手生存）→ `member`（进阶飞行）→ `builder`（创造+WE）→ `admin`（全权限）。

- 坑：RCON 不回显 LP 命令输出（用 bot 玩家身份验证）、default 勿显式设 false 覆盖子组 true、Essentials 权限默认拒绝。
- **2026-08-29 实测补**：gamemode 权限真值（`essentials.gamemode` 子权限独立）+ admin 补 `essentials.gamemode.spectator`（PR#229）+ builder/admin 降级后 gamemode 矫正方案立项。
- **2026-08-30 实测补**：builder 组无 `worldedit.limit` 权限（`//limit` 显示 Unknown/被隐藏）→ 单次编辑 100 万方块为硬上限（配合 WE 限额方案 A）。
- **2026-08-30 重规划（老板审核通过）**：四组增量 L0 23 / L1 19 / L2 35 / L3 37——L0 +10 生存工具（rules/motd/list/depth/compass/getpos/recipe/hat/near/seen）、L1 +5（tpdeny/tpacancel/ptime/pweather/abandonclaim，**tpdeny 原缺失**）、L2 +2（speed/f3f4perms.use）、L3 +4 运营工具（mute/tempban/banip/unbanip）；`/nick` 不开放、`/kit` 维持 member、siege/GetMeHome 保持默认。
- ⚠️ **Essentials IP 封禁命令是 `/banip`（无连字符，不是 `/ban-ip`）**。
- 测试服已落地 + bot 四组实测全通过；Exaroton/MCSM 21 条待同步。详见 `permission.md`。

## 9. force-gamemode 三端统一 false（2026-08-06）

MCSM 原为 true（玩家每次登录被强制回 survival，切创造后退出重登丢失模式），已改 false 与本地/Exaroton 对齐；改 server.properties 用 `PUT /api/files/`（保留 CRLF），重启生效，不影响在线玩家。

## 10. 死亡位置传送覆盖关系（2026-08-05 反编译实证）

- **Essentials `/back` 不能覆盖 BackOnDeath**：`/back` 目标是 `LastLocation`（只在 `PlayerTeleportEvent` PLUGIN/COMMAND 原因时更新），**死亡事件不更新 LastLocation** → `/back` 回的是「最后传送点」**不是死亡点**。BackOnDeath 监听死亡事件记录死亡位置。
- **线上依赖 BackOnDeath 回死亡点功能 → 保留**（仅 SpigotMC 渠道，无 Hangar/Modrinth）。同理 GetMeHome 保留（线上 60+ 玩家使用，迁移 Essentials 需脚本转换 + 多 home 权限，方案未成熟前不动）。
- **GetMeHome Tab 补全冲突（2026-08-31 最终修复）**：Paper 26.x 上执行走 Bukkit 命令表（正常）但**补全走 Brigadier 树被 Essentials 抢占**（Essentials 2.22 SyncCommands 注册 /home）→ `/home` Tab 显示 Essentials 内容而非家名。
  - 两段式根因：3.0.0 旧 api（1.21.7）补全完全不生效 → 升 3.0.1 后补全恢复但被 Essentials 抢。
  - **最终修复（源码，PR #7 已合，3.0.2）**：① api 升 26.2（`gradle.properties` `paper_api_version=26.2.build.119-stable` + `plugin.yml` `api-version: '26.2'`）；② 命令注册改 Brigadier（`CommandRegistrar.java`：`LifecycleEvents.COMMANDS` + `event.registrar().register(...)`，6 命令含别名 h/homes，`.requires()` 权限 + `.suggests()` 补全）；③ **删 plugin.yml `commands:` 段**（Paper 26.x 下 Bukkit CommandMap 声明会生成**无 executor 的幽灵命令**，执行返回 false → 打印 plugin.yml usage，且与 Brigadier 树冲突）；④ Essentials `disabled-commands` 保留（双保险）。
  - ⚠️⚠️ **Brigadier 参数类型大坑**：`word()`/`string()` 的 unquoted 字符集**不含中文和 `:`**（只允许 `[0-9A-Za-z._+-/<>^=]`）——`/sethome 验收点`、`/home 测试:家` 报 `Expected whitespace to end one argument, but found trailing data`（原版 Bukkit 按空格 split 中文家名完全可用 = 行为回归）→ **全部参数必须用 `greedyString()`**；greedy 模式下**补全建议绝不能加引号**（引号会被吞进参数值）。
  - 验证（本地测试服 1.21.10/协议 776）：`/home ` Tab → `["test1","验收点"]`、`/homes ` → `["-global"]`、中文/冒号家名 sethome/home/delhome 全通过。
  - ⚠️ mineflayer 协议验证 tab_complete 的坑：1.21 包格式是 `{transactionId, text}`（旧 `assumeCommand` 已移除），用同协议版本测（高版本 ViaVersion 降级可能不通），脚本 `~/minecraft-bot/tab-single-1210.js`。
