# 两端配置漂移报告 · 2026-11-02（周巡检）

> 巡检端：**MCSM**（{SERVER_NAME}.cn，Windows 运行栈 = 测试服 papermc-test + folia-test）+ **Exaroton**（海外服线上）。
> 采集方式：⚠️ **面板 API 下载通道本轮全量失败**（`api/files/download` 签发 200，但 `GET https://mcs.{SERVER_NAME}.cn/download/<pwd>/<file>` 一律 **502 Bad Gateway**，59/59 拉流失败；面板 `/api/overview`、`remote_services_list`、`files/list` 均正常，daemon `available:true`）→ **降级为 SSH 直读 Windows 实例目录**（`ssh win` → `E:\orzmc\mcsmanager\daemon\data\InstanceData\716c2fb7…\`，`tar -cf - -T 清单` 66/66 秒级全取），与 2026-10-26 晚补跑同法。**结论有效，覆盖 66 件（核心 7 + 插件 59）。**
> 提示：`orzmc_config_audit.sh` 走面板 API 的路径目前**必然降级**（STATUS=❌ FAIL(MCSM 0 文件)），需修（见文末待决策 #1）。
> 敏感值（rcon/management-secret/easybot api_key/飞书 secret）已脱敏。

## 本轮差异速览（对比 2026-10-26）

| 维度 | 2026-10-26 | 2026-11-02 | 变化 |
|:--|:--|:--|:--|
| 覆盖件数 | 58（核心 7 + 插件 51） | 66（核心 7 + 插件 59） | 新增 8 件（插件配置增补，扫描清单 59 项） |
| 一致 | — | 31（核心 3 + 插件 28） | — |
| 差异 | 17 项插件差异 | 26（核心 2 + 插件 24） | — |
| 运行时数据（正常） | 8 | 8 | ＝ |

**仍未闭环的旧差异（与上周同一批，属"有意差异/待确认"）**：server.properties TCP/RCON/端口/motd/max-players 等 17 处、spigot `timeout-time` 60/180、EzShops `game-mode` smp/prison + `language` en/zh、GetMeHome `limit` 30/10、Geyser `transport` both/raknet + `webrtc-port` 19134/0 + `debug-mode`、OrzMC `channel` beta/release + `default_lang` en-US/zh-CN + `qq_group_id`、GrimAC **生产端整套缺失（有意：老板决策生产不加反作弊）**、CustomWorldHeight 生产缺失、WorldEdit 禁用方块 lava/bedrock、WorldGuard `use-pre-creature-spawn-event`、bStats 开关与 serverUuid。

**本周新增/值得注意**：
- `OrzMC/easybot.yml`：两端 **api_server / ws_server 不同宿主**（MCSM=`http://easybot:8080` 容器内网，Exa=`https://bot.{SERVER_NAME}.cn`）→ 桥接拓扑差异，属预期但建议登记白名单。
- `OrzMC/im.yml`：MCSM=`builtin`（内置直连，含飞书 app 凭据），Exa=`easybot` → **老板 2026-09-12 确认的刻意设计，勿统一**。
- `OrzMC/config.yml` `cell_location`：MCSM=`world,-18,72,-75`（真实牢房），Exa 仍默认空中示例值 `world,0,100,0` → 生产端 prison 牢房未配置（如生产启用 /prison 会把人传到空中）。

---

# 两端配置差异审计报告（2026-09-09 v3·迁移后两端模型）

> 巡检端：**MCSM**（{SERVER_NAME}.cn Windows 运行栈，原本地测试服迁移后） + **Exaroton**（海外服）。

## 审计范围：5 个核心 + 59 个插件配置文件

| 类别 | 数量 |
|:--|:--|
| 核心配置（服务端） | 5 |
| 插件配置 | 59 |
| **合计** | **64** |

判定口径：**交集语义**（两端共同 key 值同=完全一致；单端独有 key 另计）

---
## 一、核心配置（服务端）

### ✅ bukkit.yml — 两端完全一致

### ✅ commands.yml — 两端完全一致

### ❌ server.properties — 差异 17 处，另有单端独有 key 2 个

| key | MCSM({SERVER_NAME}) | Exa |
|:--|:--|:--|
| 0@enable-query | false | true |
| 0@enable-rcon | true | false |
| 0@management-server-enabled | false | true |
| 0@management-server-host | localhost | 0.0.0.0 |
| 0@management-server-port | 0 | 9900 |
| 0@management-server-secret | `***`（脱敏） | `***`（脱敏） |
| 0@management-server-tls-enabled | true | false |
| 0@max-players | 150 | 20 |
| 0@max-tick-time | 60000 | 600000 |
| 0@motd | §e[Paper] 测试服-验证地图恢复状况 | §b🗡 §7欢迎来到§a{SERVER_NAME}§7的§e海外§7服务器！§b⛏ |
| 0@pause-when-empty-seconds | -1 | 60 |
| 0@rcon.password | `***`（脱敏） | `***`（脱敏） |
| 0@resource-pack-prompt |  | "" |
| 0@server-port | 25565 | 39742 |
| 0@simulation-distance | 3 | 5 |
| 0@sync-chunk-writes | true | false |
| 0@view-distance | 6 | 10 |

### ❌ spigot.yml — 差异 1 处

| key | MCSM({SERVER_NAME}) | Exa |
|:--|:--|:--|
| 2@timeout-time | 60 | 180 |

### ✅ wepif.yml — 两端完全一致

---
## 二、插件配置（按插件分组）

### ✅ BackOnDeath（1 个：0 一致 / 0 差异 / 1 数据）

- ℹ️ `config.yml` 运行时数据（玩家/交易/记录，两端独立属正常）

### ❌ CustomWorldHeight（1 个：0 一致 / 1 差异 / 0 数据）

- ❌ `config.yml` Exa 端缺失（MCSM 有、Exaroton 无）

### ✅ DeathChest（2 个：2 一致 / 0 差异 / 0 数据）

- ✅ `blacklist.yml` 两端完全一致
- ✅ `config.yml` 两端完全一致

### ✅ Essentials（6 个：5 一致 / 0 差异 / 1 数据）

- ✅ `config.yml` 两端完全一致
- ✅ `custom_items.yml` 两端完全一致
- ✅ `kits.yml` 两端完全一致
- ✅ `tpr.yml` 两端完全一致
- ℹ️ `upgrades-done.yml` 运行时数据（玩家/交易/记录，两端独立属正常）
- ✅ `worth.yml` 两端完全一致

### ❌ EzShops（11 个：5 一致 / 3 差异 / 3 数据）

- ❌ `config.yml` 差异 2 处：
  - `0@game-mode`：MCSM=`smp` Exa=`prison`
  - `0@language`：MCSM=`en` Exa=`zh`
- ℹ️ `player-shops.yml` 运行时数据（玩家/交易/记录，两端独立属正常）
- ❌ `shop-dynamic.yml` Exa 端缺失（MCSM 有、Exaroton 无）
- ℹ️ `shop-rotations.yml` 运行时数据（玩家/交易/记录，两端独立属正常）
- ✅ `shop.yml` 两端完全一致
- ✅ `stock-gui.yml` 两端完全一致
- ✅ `stock-prices.yml` 两端完全一致
- ℹ️ `transactions.yml` 运行时数据（玩家/交易/记录，两端独立属正常）
- ✅ `shop/prison/menu.yml` 两端完全一致
- ✅ `shop/smp/menu.yml` 两端完全一致
- ❌ `daily-sells/3515325d-d738-39b0-a4d5-0d2f59ece1fe.yml` Exa 端缺失（MCSM 有、Exaroton 无）

### ❌ GetMeHome（4 个：2 一致 / 1 差异 / 1 数据）

- ✅ `config.yml` 两端完全一致
- ✅ `delay.yml` 两端完全一致
- ℹ️ `homes.yml` 运行时数据（玩家/交易/记录，两端独立属正常）
- ❌ `limit.yml` 差异 1 处：
  - `2@limit`：MCSM=`30` Exa=`10`

### ❌ Geyser-Spigot（1 个：0 一致 / 1 差异 / 0 数据）

- ❌ `config.yml` 差异 4 处：
  - `0@config-version`：MCSM=`11` Exa=`10`
  - `0@debug-mode`：MCSM=`true` Exa=`false`
  - `2@transport`：MCSM=`both` Exa=`raknet`
  - `2@webrtc-port`：MCSM=`19134` Exa=`0`

### ✅ GriefPreventionData（2 个：2 一致 / 0 差异 / 0 数据）

- ✅ `config.yml` 两端完全一致
- ✅ `messages.yml` 两端完全一致

### ❌ GrimAC（10 个：0 一致 / 10 差异 / 0 数据）

- ❌ `config.yml` Exa 端缺失（MCSM 有、Exaroton 无）
- ❌ `database.yml` Exa 端缺失（MCSM 有、Exaroton 无）
- ❌ `discord.yml` Exa 端缺失（MCSM 有、Exaroton 无）
- ❌ `messages.yml` Exa 端缺失（MCSM 有、Exaroton 无）
- ❌ `punishments.yml` Exa 端缺失（MCSM 有、Exaroton 无）
- ❌ `databases/mongo.yml` Exa 端缺失（MCSM 有、Exaroton 无）
- ❌ `databases/mysql.yml` Exa 端缺失（MCSM 有、Exaroton 无）
- ❌ `databases/postgres.yml` Exa 端缺失（MCSM 有、Exaroton 无）
- ❌ `databases/redis.yml` Exa 端缺失（MCSM 有、Exaroton 无）
- ❌ `databases/sqlite.yml` Exa 端缺失（MCSM 有、Exaroton 无）

### ✅ LoginSecurity（2 个：2 一致 / 0 差异 / 0 数据）

- ✅ `config.yml` 两端完全一致
- ✅ `database.yml` 两端完全一致

### ✅ LuckPerms（1 个：1 一致 / 0 差异 / 0 数据）

- ✅ `config.yml` 两端完全一致

### ❌ OrzMC（10 个：4 一致 / 5 差异 / 2 数据）

- ✅ `access_rules.yml` 两端完全一致
- ❌ `config.yml` 差异 5 处：
  - `2@cell_location`：MCSM=`world,-18,72,-75,0,0` Exa=`world,0,100,0,0,0`
  - `2@channel`：MCSM=`beta` Exa=`release`
  - `2@default_lang`：MCSM=`en-US` Exa=`zh-CN`
  - `2@discord_server_link`：MCSM=`''` Exa=`https://discord.gg/9JAb9vpvUE`
  - `2@qq_group_id`：MCSM=`'1082305302'` Exa=`'1012877775'`
- ❌ `easybot.yml` 差异 3 处：
  - `0@api_key`：MCSM=`***`（脱敏） Exa=`***`（脱敏）
  - `0@api_server`：MCSM=`http://easybot:8080` Exa=`https://bot.{SERVER_NAME}.cn`
  - `0@ws_server`：MCSM=`ws://easybot:8080` Exa=`wss://bot.{SERVER_NAME}.cn`
- ✅ `guide_book.yml` 两端完全一致
- ❌ `im.yml` 差异 5 处：
  - `0@backend`：MCSM=`builtin` Exa=`easybot`
  - `4@app_id`：MCSM=`***`（脱敏） Exa=`***`（脱敏）
  - `4@app_secret`：MCSM=`***`（脱敏） Exa=`***`（脱敏）
  - `4@client_secret`：MCSM=`***`（脱敏） Exa=`***`（脱敏）
  - `4@token`：MCSM=`''` Exa=`''             # Discord 开发者门户 Bot Token（长期有效；鉴权失败=配置错误）`
- ❌ `im_bindings.yml` 差异 1 处：
  - `0@sessions`：MCSM=`` Exa=`{}`
- ℹ️ `ip_blacklist.yml` 运行时数据（玩家/交易/记录，两端独立属正常）
- ℹ️ `permission.yml` 运行时数据（玩家/交易/记录，两端独立属正常）
- ✅ `portals.yml` 两端完全一致
- ✅ `templates.yml` 两端完全一致

### ✅ SkinsRestorer（1 个：1 一致 / 0 差异 / 0 数据）

- ✅ `config.yml` 两端完全一致

### ✅ Vault（1 个：1 一致 / 0 差异 / 0 数据）

- ✅ `config.yml` 两端完全一致

### ✅ ViaBackwards（1 个：1 一致 / 0 差异 / 0 数据）

- ✅ `config.yml` 两端完全一致

### ✅ ViaRewind（1 个：1 一致 / 0 差异 / 0 数据）

- ✅ `config.yml` 两端完全一致

### ✅ ViaVersion（1 个：1 一致 / 0 差异 / 0 数据）

- ✅ `config.yml` 两端完全一致

### ❌ WorldEdit（1 个：0 一致 / 1 差异 / 0 数据）

- ❌ `config.yml` 差异 1 处：
  - `4@-"minecraft`：MCSM=`lava"` Exa=`bedrock"`

### ❌ WorldGuard（1 个：0 一致 / 1 差异 / 0 数据）

- ❌ `config.yml` 差异 1 处：
  - `4@use-pre-creature-spawn-event`：MCSM=`true` Exa=`false`

### ❌ bStats（1 个：0 一致 / 1 差异 / 0 数据）

- ❌ `config.yml` 差异 2 处：
  - `0@enabled`：MCSM=`false` Exa=`true`
  - `0@serverUuid`：MCSM=`60e5974b-c66c-4c8b-931b-9384a86c271f` Exa=`02c94a29-7bc2-4ace-ae32-a071decbe58f`

---
## 三、汇总

| 状态 | 核心 | 插件 | 合计 |
|:--|:--|:--|:--|
| ✅ 两端完全一致 | 3 | 28 | 31 |
| ❌ 配置差异 | 2 | 24 | 26 |
| ℹ️ 运行时数据差异（正常） | 0 | 8 | 8 |
| **合计** | **5** | **60** | **65** |

> 注：运行时数据文件 = 玩家家/死亡点/交易记录/审批记录等随玩家变化的内容，两端独立属预期，不算配置漂移。

---

## 四、待决策事项（2026-11-02 巡检提出）

| # | 事项 | 证据 | 建议 |
|:--|:--|:--|:--|
| 1 | **巡检脚本 MCSM 拉取通道失效**：面板 `/download` 全量 502，`orzmc_config_audit.sh` 每周必降级（本轮已手工 SSH 兜底） | 签发 200 + 拉流 502 ×59；面板 API 其他端点正常、daemon available=true | 给 `fetch3_configs.fetch_mcsm` 加 **SSH 直读兜底**（tar -T 清单），面板通道保留为首选/次选 |
| 2 | 生产端 `prison.cell_location` 仍是空中示例值 `world,0,100,0` | OrzMC/config.yml 差异 | 生产若启用 /prison 需配真实牢房坐标，否则坐牢玩家被传到空中 |
| 3 | 生产端 `GetMeHome limit` 10 vs 测试 30、`EzShops language` zh/en、`game-mode` prison/smp | 同上周 | 确认是否统一或登记为有意差异白名单 |
| 4 | Geyser 三端 `transport`（MCSM=both / Exa=raknet）、`webrtc-port`、`debug-mode=true` | 测试服 NetherNet 双通道；生产仍 RakNet | 生产切 NetherNet 需 HTTPS 入口（见 references/nethernet.md），未切前保留 raknet |
