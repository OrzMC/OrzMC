# 两端配置漂移报告 · 2026-11-16（周巡检）

> 巡检端：**MCSM**（{SERVER_NAME}.cn，Windows 运行栈 = 测试服 papermc-test / folia-test）+ **Exaroton**（海外服线上）。
> 采集方式：面板 API 通道本轮**又只返回 0 个文件**（未报错），脚本自动降级 **SSH 直读** Windows 实例目录 → **72/72 秒级全取**（核心 7 + 插件 65）。**结论有效。**
> 敏感值（rcon / management-server-secret / easybot api_key / 飞书 app_secret / client_secret / 公网 IP）已脱敏。

## 本轮差异速览（对比 2026-11-09）

| 维度 | 2026-11-09 | 2026-11-16 | 变化 |
|:--|:--|:--|:--|
| 覆盖件数 | 66（核心 7 + 插件 59） | **72（核心 7 + 插件 65）** | ▲+6 = 新增 Eaglercraft 网页客户端 6 件配置 |
| 两端完全一致 | 32 | 30（核心 3 + 插件 27） | ▼-2 |
| 配置差异 | 27 | 35（核心 4 + 插件 31） | ▲+8 |
| 运行时数据（正常） | 8 | 8 | ＝ |
| 采集通道 | 面板 502/404 → SSH 兜底 | 面板 0 文件 → SSH 兜底 | 兜底仍有效 |

**结论：差异增量 100% 来自 2026-11-12 的统一代理改造（ADR-036），无意外漂移。** 唯一新增的「真差异」是 `config/paper-global.yml` 的 Velocity 转发段（仅测试服有 = 代理架构必然结果）。EaglercraftX* 6 件仅测试服存在（网页客户端只部署在测试服入口）。

## 一、核心配置（7 件：3 一致 / 4 差异）

| 文件 | 状态 | 要点 |
|:--|:--|:--|
| bukkit.yml / commands.yml / wepif.yml | ✅ | 完全一致 |
| config_paper-global.yml | ❌ 2 处 | `4@enabled` true/false、`4@secret` 仅测试服有值 → **Velocity 现代转发签名**（代理架构必需，Exa 无代理故关闭）。上轮为一致，本轮新增属预期 |
| server.properties | ❌ 17 处 | 已知定位/通道差异：motd、max-players 150 vs 20、view-distance 6 vs 10、simulation-distance 3 vs 5、server-port 25565 vs 39742（Exa 平台）、max-tick-time 60000 vs 600000、pause-when-empty -1 vs 60、sync-chunk-writes；测试服 `enable-rcon=true` + `management-server-*` 关闭，Exa `enable-query=true` + management 9900 开启 |
| config_paper-world-defaults.yml | ❌ 2 处 | `hard/soft`：测试服 `default` vs Exa `128/32` |
| spigot.yml | ❌ 1 处 | `timeout-time` 60 vs 180 |

## 二、插件配置（65 件：27 一致 / 31 差异 / 8 运行时）

| 插件 | 差异要点 | 判定 |
|:--|:--|:--|
| EaglercraftXServer（4 件）/ EaglercraftXBackendRPC（2 件） | Exa 端缺失 | ✅ 预期（网页客户端只在测试服入口） |
| Geyser-Spigot | `transport` both vs nethernet、`webrtc-port` 19134 vs 0、`advertise-addresses` 域名:19134 vs `{SERVER_NAME}.exaroton.me:19132`、`clone-remote-port` false/true | ✅ **2026-11-16 已闭环**：配置审查改为**读代理侧生效配置**（`orzmc-velocity` 容器 bind mount `E:/orzmc/eagler/proxy/plugins/Geyser-Velocity/config.yml`，落到与 Exa 同名的 `Geyser-Spigot/config.yml` 位置对齐比对，脚本 `cmp3/fetch3_proxy.py`，自动识别 proxy/direct 模式）。改造后仅剩 3 处**真实拓扑差异**：`clone-remote-port`（代理下必须 false）、`advertise-addresses`（LAN+公网 IP:19132 vs Exa 平台域名）、`stun-discovery`（false vs true）；`transport`/`webrtc-port` 不再作为「测试服配置陈旧」误报 |
| OrzMC | `channel` beta/release（豁免）、`default_lang` en-US/zh-CN（刻意）、`qq_group_id`/`discord_server_link`（群宣）、`prison.cell_location` 测试服真值 vs Exa 空中示例值（旧问题未闭环）、`im.yml` backend builtin/easybot（**刻意双通道**）、easybot api_server 容器内网 vs 公网域名（拓扑差异） | 已知 |
| EzShops | `game-mode` smp/prison、`language` en/zh；Exa 缺 `shop-dynamic.yml`、`daily-sells/*` | 已知定位差异 |
| GrimAC | **Exa 整套 10 件缺失** | 有意（生产端不加反作弊） |
| CustomWorldHeight | Exa 缺失 | 有意 |
| GetMeHome | `limit` 30 vs 10 | 已知 |
| LoginSecurity | `session-timeout` 600 vs 60、`hide-inventory` true/false | 已知 |
| WorldEdit | 禁用方块列表 lava/bedrock 顺序差异（解析器把 `-"minecraft` 切碎，属工具瑕疵） | 工具假阳性 |
| WorldGuard | `use-pre-creature-spawn-event` true vs false | 版本默认值差异（7.0.21 vs 7.0.20 默认不同），非人为配置 |
| bStats | `enabled` false/true、serverUuid 不同 | 预期 |
| 其余（BackOnDeath/DeathChest/Essentials/GP/LuckPerms/SkinsRestorer/Vault/Via×3/voicechat 等） | ✅ 一致或仅运行时数据 | — |

## 三、版本现状（本轮实查：jar 文件名 + 代理容器 + Exa API）

| 对象 | papermc-test | folia-test | orzmc-velocity（入口） | Exaroton | 判定 |
|:--|:--|:--|:--|:--|:--|
| 核心 | Paper **26.3-246** | Folia **26.2-7** | Velocity 1.7.2-26.3 | Paper **26.3(253)** | ⚠️ MCSM paper 落后 7 个 build（最新 STABLE **26.3-253**）；⚠️ **Folia 26.3-8 已转 STABLE**（此前为 ALPHA）→ 按纪律已可升，待决策 |
| Geyser | b1298（实例内已因 Velocity 自动停用） | b1298（同上） | **b1300** | b1298 | ⚠️ 最新 build **1303**；实际生效的是代理 b1300 |
| OrzMC | 1.0.31-dev.435（beta，豁免） | 1.0.29-dev.427（beta） | — | 1.0.30 Release | ℹ️ 最新 Release = 1.0.30（11-04），Exa 已最新；folia 落后一个 Release |
| LuckPerms | 5.5.91 | 5.5.91 | — | 5.5.91 | ✅ |
| WorldGuard | 7.0.21 | 7.0.19（26.2 线保持） | — | **7.0.20** | ⚠️ Exa 有 7.0.21 release（仅 26.3）可升；folia 按纪律留 7.0.19 |
| WorldEdit | 7.4.6 | 7.4.6 | — | 7.4.6 | ✅ |
| ExecutableEvents / SCore | — | **3.26.11.2 / 5.26.11.2** | — | — | ⚠️ 双双有 **3.26.11.15 / 5.26.11.15（release，11-15 发）**，必须成对升 |
| Via 三件套 | 5.12.2 | 5.12.2 | — | 5.12.2 | ✅（`block-versions` 安全基线已生效） |

## 四、运行面观察（非配置）

- 两个测试服实例 **11-15 08:03 起处于停止状态**（面板 `status=0`），入口代理容器正常（Up，06:31 启动，`Done (5.59s)`）→ 玩家连代理能握手，但后端不可达；代理日志 08:37 有 `popiiumaa connected → disconnected` 的秒断记录，与后端未启动一致。
- 代理侧 `advertise-addresses` = LAN IP + 公网 IP:19132，与 DoH 真值一致，`stun-discovery: false` → 动态 IP 漂移由 `nethernet_advertise_sync.py`（5 分钟）守护。

## 五、可升级项整理（老板批复前的决策表）

| 类别 | 对象 | 部署版 | 最新可用 | 通道 | 建议 |
|:--|:--|:--|:--|:--|:--|
| 代理 | Velocity / Geyser-Velocity | Velocity 1.7.2-26.3 / Geyser b1300 | Velocity 同版 / Geyser **b1303** | PaperMC / GeyserMC | Velocity 不动；Geyser 升 1303 |
| 核心 | Paper（papermc-test） | 26.3-246 | **26.3-253（STABLE）** | STABLE | 升 |
| 核心 | Folia（folia-test） | 26.2-7 | **26.3-8（STABLE）** | STABLE | 升（26.2 线已于 2026-11-15 EOL） |
| 核心 | Paper（Exaroton） | 26.3(253) | 同 | 平台 | 不动 |
| 插件 | Geyser-Spigot（两实例 + Exa） | b1298 | **b1303** | GeyserMC | 三处一起升 |
| 插件 | ExecutableEvents / SCore（folia） | 3.26.11.2 / 5.26.11.2 | **3.26.11.15 / 5.26.11.15** | Modrinth release | 成对升 |
| 插件 | WorldGuard（Exa） | 7.0.20 | **7.0.21** | Modrinth release | 升 |
| 插件 | WorldGuard（folia） | 7.0.19 | 7.0.21 | Modrinth release | 保持（7.0.19 元数据含 26.2+26.3，回滚友好） |
| 插件 | OrzMC（folia） | 1.0.29-dev.427 | 1.0.30 Release | Hangar | 测试服 beta 通道刻意，未列入本轮 |
| 插件 | LuckPerms / WorldEdit / Via 三件套 / 其余 17 件 | — | 同 | — | 已最新或本地打包，不升 |

## 六、本轮执行结果（2026-11-16，老板批复 #1–#8 后）

| 端 | 升级项 | 验证 |
|:--|:--|:--|
| papermc-test（**保持停止**） | Paper 26.3-246 → **26.3-253**、Geyser-Spigot 1298 → **1303** | 远端 sha256 = 本地 2/2；根目录只剩 `paper-26.3-253.jar` |
| folia-test（**保持停止**） | Folia 26.2-7 → **26.3-8**、Geyser-Spigot 1298 → **1303**、EE → **3.26.11.15**、SCore → **5.26.11.15** | 远端 sha256 = 本地 4/4；根目录只剩 `folia-26.3-8.jar` |
| orzmc-velocity（运行中） | Geyser-Velocity b1300 → **b1303** | sha256 `32b5dae5…`；日志 `Loaded plugin geyser 2.12.1-b1303`、`Built-in signaling started on http://0.0.0.0:19132`、`Done (6.15s)` |
| Exaroton（OFFLINE） | Geyser-Spigot 1298 → **b1303**、WorldGuard 7.0.20 → **7.0.21** | PUT 回读 sha256 2/2 一致；旧 jar DELETE 200 且目录内无残留 |
| 备份 | 两实例 `upgrade-bak-20261116`（旧核心 + 旧插件，Move 出 `plugins/`） | paper 2 件 / folia 4 件；已清理 folia 三个跨轮旧备份（62+28+8 MB） |
| 交付 | `~/Downloads/orzmc-upgrade-20261116/` + 同名 zip（246MB） | `SHA256SUMS.txt` 8/8 校验 OK、`unzip -t` 无错、内层路径全 ASCII |

**未做**：测试服两实例按老板决策**保持停止**；启动验收（含 Folia 26.2→26.3 世界数据升级）由老板自用时执行，检查清单见交付包 `SYNC-GUIDE.md`。

## 七、巡检脚本改造（老板批复 #7，两个都改）

| 脚本 | 改造内容 | 验证 |
|:--|:--|:--|
| `orzmc_config_audit.sh` + 新增 `cmp3/fetch3_proxy.py` | 配置审查**改读代理侧生效配置**：SSH 直读 `E:/orzmc/eagler/proxy/plugins/Geyser-Velocity/config.yml` → base64 传回（避开 Windows GBK 控制台）→ 落到与 Exa 同名的 `plugins/Geyser-Spigot/config.yml`；**自动识别** proxy/direct 模式（代理配置文件存在 = proxy），direct 时回退实例内副本；汇总新增「测试服入口模式 / 生效 Geyser 配置来源」 | 实跑一轮：`STATUS: ✅ SUCCESS`、`PROXY_MODE=proxy`、Exa 52 / MCSM 72 文件、报告 9282B |
| `connectivity_check.py`（cron 副本 + 技能副本 md5 一致） | **自动识别测试服运行模式**（`detect_test_mode`：LAN 25565 可连 + 25566 关闭 = proxy）；proxy 模式下目标集换成 `proxy`/`proxy-pub`/`prod-mcsm`，**删掉 25566、19133 旧端口**；新增「后端存活」检查（paper/folia RCON 25575/25576 TCP 可连性）；`--json` 输出新增 `test_mode` 字段；可用 `ORZMC_TEST_MODE=proxy|direct` 强制 | 实跑：识别 `proxy`，入口 Java `Velocity 1.7.2-26.3` + NetherNet `/v1/join` 200 + 后端双 ❌（实例停止属预期），退出码 0 |
