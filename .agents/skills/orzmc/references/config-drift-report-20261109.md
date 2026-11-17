# 两端配置漂移报告 · 2026-11-09（周巡检）

> 巡检端：**MCSM**（{SERVER_NAME}.cn，Windows 运行栈 = 测试服 papermc-test / folia-test）+ **Exaroton**（海外服线上）。
> 采集方式：面板 `files/list` 正常（扫出 59 件插件配置清单），但 `files/download` 拉流 **本轮 100% 失败**（`/download/<pwd>/<file>` 7 件成功→其后全部 `HTTP 404` / `拉流失败`；`/api/overview`、`remote_services_list` 正常）→ `orzmc_config_audit.sh` 自动降级 **SSH 直读 Windows 实例目录**，`ssh win` → `E:\orzmc\mcsmanager\daemon\data\InstanceData\716c2fb7…\`，**66/66 秒级全取**（与 10-26 晚、11-02 同法）。**结论有效，覆盖 66 件（核心 7 + 插件 59）。**
> 敏感值（rcon / management-server-secret / easybot api_key / 飞书 app_secret / client_secret）已脱敏。

## 本轮差异速览（对比 2026-11-02）

| 维度 | 2026-11-02 | 2026-11-09 | 变化 |
|:--|:--|:--|:--|
| 覆盖件数 | 66（核心 7 + 插件 59） | 66（核心 7 + 插件 59） | ＝ |
| 两端完全一致 | 32 | 32（核心 4 + 插件 28） | ＝ |
| 配置差异 | 27 | 27（核心 3 + 插件 24） | ＝ |
| 运行时数据（正常） | 8 | 8 | ＝ |
| 采集通道 | 面板 502 → SSH 兜底 | 面板 404/拉流失败 → SSH 兜底 | 故障形态变化，兜底仍有效 |

**结论：配置漂移面与上周完全同批，无新增漂移项，也无旧项闭环。** 差异全部落在已知「有意差异 / 待决策」清单内。

## 一、核心配置（7 件：4 一致 / 3 差异）

| 文件 | 状态 | 要点 |
|:--|:--|:--|
| bukkit.yml / commands.yml / config_paper-global.yml / wepif.yml | ✅ | 完全一致 |
| server.properties | ❌ 17 处 | 定位类差异（motd/max-players/view-distance 6 vs 10/simulation-distance 3 vs 5/server-port 25565 vs 39742/pause-when-empty -1 vs 60/max-tick-time 60000 vs 600000/sync-chunk-writes）；**通道类**：测试服 `enable-rcon=true`、`management-server-*` 关闭；Exa `enable-query=true`、`management-server` 开启（9900） |
| config_paper-world-defaults.yml | ❌ 2 处 | 8@hard / 8@soft：测试服 `default` vs Exa `128/32` |
| spigot.yml | ❌ 1 处 | `timeout-time` 60 vs 180 |

## 二、插件配置（59 件：28 一致 / 24 差异 / 8 运行时）

| 插件 | 差异要点 |
|:--|:--|
| OrzMC | `channel` beta/release（豁免）、`default_lang` en-US/zh-CN（**刻意**）、`qq_group_id` 1082305302/1012877775（群宣）、`discord_server_link`、**`prison.cell_location`：测试服 `world,-18,72,-75`（已配真牢房）vs Exa `world,0,100,0`（仍是空中示例值 ← 旧问题未闭环）**；`easybot.yml` api_server/ws_server 容器内网 vs bot.{SERVER_NAME}.cn（拓扑差异，预期）；`im.yml` backend builtin/easybot（**刻意**，双 IM 通道并行） |
| Geyser-Spigot | `transport` both/nethernet、`webrtc-port` 19134/0、`debug-mode` true/false、`advertise-addresses`（见下「解析修正」） |
| EzShops | `game-mode` smp/prison、`language` en/zh；Exa 缺 `shop-dynamic.yml`、`daily-sells/*` |
| GetMeHome | `limit` 30 vs 10 |
| GrimAC | **Exa 整套 10 件缺失（有意：生产端不加反作弊）** |
| CustomWorldHeight | Exa 缺失（生产不用） |
| WorldEdit | 禁用方块列表 lava/bedrock（解析器把含引号的行切成 `-"minecraft`，属工具瑕疵，不影响结论） |
| WorldGuard | `use-pre-creature-spawn-event` true/false |
| bStats | `enabled` false/true、serverUuid 不同 |
| 其余（BackOnDeath/DeathChest/Essentials/GP/LoginSecurity/LuckPerms/SkinsRestorer/Vault/Via×3/voicechat） | ✅ 一致或仅运行时数据 |

### ⚠️ 解析修正：Geyser `advertise-addresses` 不是空的（工具假阴性）
审计报告把两端 `advertise-addresses` 都读成空（MCSM=``、Exa=`[]`）。**实测原文**（scp 直读）：

- `papermc-test`：`port 19132` / `webrtc-port 19134` / `transport both` / `advertise-addresses: ["<公网IP>:19134"]`
- `folia-test`：`port 19132` / `webrtc-port 19135` / `transport both` / `advertise-addresses: ["<公网IP>:19135"]`

两实例均为「数字公网 IP + 端口 = webrtc-port」的正确写法（宿主跑 Clash TUN，必须写 IP）。**这是 cmp3 多行 YAML（值在下一行）解析缺陷，需修**，否则每周都会误报「生产端 advertise 为空」并可能被误当成故障根因。

## 三、三端版本现状（本轮实查 jar + 面板 API）

| 对象 | 测试服 papermc-test | 测试服 folia-test | Exaroton（海外线上） | 判定 |
|:--|:--|:--|:--|:--|
| 核心 | Paper **26.3-237** | Folia **26.2-7** | Paper **26.3-244** | paper 有 **26.3-244 STABLE**（11-06 发布）可升；folia 26.3 仍 **ALPHA**（-6）→ 不动 |
| OrzMC | 1.0.30-dev.430（beta） | 1.0.29-dev.427（beta） | **1.0.29-Release** | 生产可用 **1.0.30 Release**（11-04）→ 可升 |
| Geyser | build 1280 | build 1280 | build 1280 | 最新 **1296（2.12.1）**（Geyser 只发快照=例外口径） |
| LuckPerms | 5.5.90 | 5.5.90 | 5.5.90 | 最新 **5.5.91** |
| WorldGuard | 7.0.20 | 7.0.19 | 7.0.20 | **7.0.21（metadata 仅 26.3）**：paper 可升，folia 保持 7.0.19 |
| Via 三件套 | 5.12.2 | 5.12.2 | 5.12.2 | ✅ 26.3 兼容线 |
| AxGraves / ExecutableEvents / SCore（folia 独有） | — | 1.32.1 / <公网IP> / <公网IP> | — | 1.32.2 / <公网IP> / <公网IP> |
| Exa 缺失项 | — | — | 无 voicechat / 无 GrimAC / 无 bStats | 历史有意差异 |

## 四、本周新发现（非配置漂移）

1. **🔴 国内服生产 `{SERVER_HOST}` 基岩入口不可用（外部节点证实）**
   - Java 正常：`✅ 279ms | Paper 26.3 | 协议 767 | 玩家 0/150`
   - RakNet(UDP 19132)：无应答；NetherNet 信令(TCP 19132)：本机 `OPEN_NO_HTTP`（TUN 不可信）
   - **外部节点复核**（check-host.net，ch1/hk1/nl2 三节点，直连真 IP <生产公网IP>）：`19132/tcp → Connection refused` ×3；对照 `25565/tcp → OK 0.23~0.30s` ×3
   - → 不是本机代理假象：**该端 19132 无监听/未转发，Geyser 基本可判为未运行**。生产基岩玩家目前进不来。
2. 测试服两实例自 2026-11-08 起处于**停止态**（paper 13:25 UTC 正常 `Stopping server`，folia 14:32 正常关停），非崩溃：paper `SEVERE` 0 条、无插件加载失败。
3. papermc-test 健康体检的「未见 `Done (` / 未见 Geyser `Started on UDP`」= **日志跨日轮转假阳性**（latest.log 从 `00:00:26` 起，属连续运行会话中段），非故障。folia 日志可见 `Started Geyser on UDP port 19132` + `Built-in signaling … NetherNet on UDP port 19135`。
4. 端口发布与 Geyser 配置自洽：paper `19134:19134/udp`、folia `19135:19135/udp` 均已发布，webrtc-port 与宿主端口一致，未发现端口缺口。

## 五、待决策（#N + ①②，请编号回复）

1. **#1 国内服生产基岩入口**：①立刻恢复（需面板/SSH 权限，我无该端凭据，远程 MCSM API 仍 403）②确认是否老板主动关闭基岩，仅记录 ③先查 19132 TCP/UDP 是否被路由器映射删除
2. **#2 测试服 paper 核心** 26.3-237 → **26.3-244（STABLE）**：①下周无常驻玩家窗口升 ②随下轮插件升级一起做 ③暂不升
3. **#3 Exa 插件 OrzMC** 1.0.29-Release → **1.0.30 Release**（release 纪律允许）：①纳入下轮 ②暂不升
4. **#4 常规可升**：Geyser 1280→1296、LuckPerms 5.5.90→5.5.91、paper 侧 WorldGuard 7.0.20→7.0.21（folia 保持 7.0.19）：①全部纳下轮 ②只升 WG/LP、Geyser 等有玩家窗口 ③都不动
5. **#5 Exa Geyser 形态**：现 `transport: nethernet` + `webrtc-port 0` + `advertise-addresses []`（STUN 猜地址）→ 老客户端（<26.40）进不来、动态 IP 下有踩空风险：①切 `both`（对齐测试服，webrtc-port 19134 + 显式 advertise）②维持 nethernet，仅补显式 advertise ③不动
6. **#6 旧漂移项是否本轮一次性收敛**：EzShops `game-mode` smp/prison、`language` en/zh；GetMeHome `limit` 30/10；bStats 开关；**OrzMC Exa `prison.cell_location` 仍是空中示例值（坐牢会回世界出生点）**：①按「定位类差异保留、功能类差异对齐」逐项处置（我出表格）②只修 prison 牢房坐标 ③全部维持
7. **#7 巡检工具三处缺陷**（只读巡检下未改脚本，等批准）：①`orzmc_config_audit.sh` L67 bash 3.2 `$MCSM_N` 后接全角括号 → `unbound variable`（不影响结果，但每次刷错误）②cmp3 多行 YAML 解析把 `advertise-addresses` 读空（假阴性）③`orzmc_quality_report.py` 在 jacoco XML 缺失时崩（`None - float`）且单测失败会连坐 `integrationTest` 统计口径
8. **#8 备份堆积**：papermc-test 有 3 份 `upgrade-bak`（136MB）：①清到留 1 份 ②保留 ③等磁盘水位再清

## 六、数据有效性

- 配置：MCSM **66** 件（经 SSH 直读；面板通道 7/59 后失败）+ Exa **52** 件（Exa 侧 14 件 404 = 该端确实无此文件）；对比 67 项（核心 7 + 插件 60）。
- 版本：比对 21 项（paper 侧）+ 8 项（folia 独有）+ 双核心；Exa 侧本轮**首次补齐 jar 盘点**（19 jar）。
- 健康：2 实例 + 2 份 latest.log（paper 86.6KB / folia 54.8KB）+ 实例配置 + 磁盘。
- 连通：4 目标 / FAIL 7 / WARN 7；DNS 被 TUN 劫持 2 处（dev→<公网IP>、prod→<生产公网IP> 已用 DoH 修正）。
