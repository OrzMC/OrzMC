# 两端配置漂移报告 · 2026-10-26（周巡检 · 补跑全量版 20:20–22:05）

- 巡检端：**MCSM**（{SERVER_NAME}.cn，Windows 运行栈，实例 `papermc-test` 716c2fb7）= 基准端 / **Exaroton**（海外生产）= 对比端
- 执行方式：人工补跑。今晨 09:42 自动巡检因面板 apiKey 被轮换而降级（插件配置仅覆盖 3 件），**apiKey 已于今日 12:00 更新并验证**，本轮为有效数据重跑（晨报存档 `config-drift-report-20261026-0942-degraded.md`）。
- **数据有效性（硬证据）**：MCSM 端 **58/58 文件**（核心 7 + 插件配置 51）、Exaroton 端 **50 文件**（核心 7 + 插件 43）；清单扫描 **26 次 files/list 全部成功（0 失败）**，单次延迟 3.7 / 8.6 / 20.3s（min/中位/max）。**两端均 >0，本轮数据有效。**

## 一、数据获取方式（含工具性发现）

| 环节 | 结果 | 证据 |
|:--|:--|:--|
| MCSM `files/list` 递归扫描 | ✅ 26 次调用全成功 | 中位 8.6s、最长 20.3s → **8s 硬超时会砍掉约一半数据**，实际采用「8s 首档 + 50s 复审」 |
| MCSM `files/download` 签发 + 拉流 | ❌ 严重不稳（2/5 失败，单文件 111~135s） | 与 2026-10-19 / 10-26 晨同因（面板迟钝期） |
| **改用 SSH 直读 Windows 实例目录** | ✅ **58/58 全量取到（504KB tar，秒级）** | `ssh win`（192.168.0.33）→ `E:\orzmc\mcsmanager\daemon\data\InstanceData\<uuid>\`；Windows 侧 `tar -T 清单` 打包回传 |
| Exaroton 文件 API | ✅ 核心 7 全成功，插件配置 43 件取到（缺失 = 生产端未装该插件） | `exa_file.get_file` |

> 结论：**面板 files API 在慢响应状态下不可用于全量巡检**（签发/拉流比 list 更脆）。**SSH 直读 Windows 实例目录是当前最可靠、最快、最权威的 MCSM 侧数据源**，建议下周巡检默认走 SSH（见待决策 #6）。

## 二、核心配置（7 件，7/7 可比）

| 文件 | 结论 |
|:--|:--|
| bukkit.yml / commands.yml / wepif.yml / config_paper-global.yml | ✅ 一致 |
| spigot.yml | ❌ 1 处差异（`timeout-time` 60 vs 180）— 与 10-19 晨报一致，仍未拍板 |
| server.properties | ❌ 16 处值差异 + 2 单端独有键（全部环境/用途差异，见下） |
| config_paper-world-defaults.yml | ❌ 2 处值差异 + 5 单端独有键（schema 代差） |

### server.properties（延续 10-19 判定：均为环境/用途差异）
`enable-rcon` true/false · `management-server-enabled/host/port/secret/tls` 测试关闭 / 生产 0.0.0.0:9900（面板托管） · `max-players` 150/20 · `max-tick-time` 60000/600000 · `motd` 测试服/海外宣传 · `pause-when-empty-seconds` -1/60 · `rcon.password` 已设/空 · `resource-pack-prompt` 空/`""` · `server-port` 25565/39742 · `simulation-distance` 3/5 · `view-distance` 6/10 · `sync-chunk-writes` true/false；单端独有：`pvp=false`（测试）/ `previews-chat=false`（生产，旧核心）

### config_paper-world-defaults.yml
`despawn-ranges.*.hard/soft`：MCSM `default`（26.3 新 schema）vs Exa `128/32`（旧 schema 显式值）+ 5 个旧版独有键 → **schema 代差，非运行行为漂移**。

## 三、插件配置（51 件全可比；26 一致 / 17 差异（10 值差异 + 7 生产端缺插件）/ 8 运行时数据）

### 3.1 本轮新增差异（今晨 09:42 版未覆盖）

| 插件 | 文件 | 差异 | 判定 |
|:--|:--|:--|:--|
| Geyser-Spigot | config.yml | `debug-mode` true/false、`transport` **both/raknet**、`webrtc-port` 19134/0 | 测试服 NetherNet 迁移中（both 双通道），生产仍 RakNet → 预期，但需登记为有意差异 |
| EzShops | config.yml | `game-mode` **smp/prison**、`language` en/zh | 生产为 prison 经济模式、语言中文 → 未登记，需确认 |
| GetMeHome | limit.yml | `limit` **30 / 10** | 测试服家数量上限更宽 → 需确认 |
| bStats | config.yml | `enabled` **false / true**、serverUuid 各异 | 测试关统计、生产开 → 需确认口径 |
| WorldEdit | config.yml | 方块黑名单项 **lava（测试）/ bedrock（生产）** | ⚠️ 与「WorldEdit 防崩服方案」相关：生产禁 bedrock 但**未禁 lava**，测试反之 |
| WorldGuard | config.yml | `use-pre-creature-spawn-event` true/false | 低风险 |
| OrzMC | easybot.yml | `api_key` 各自密钥、`api_server`/`ws_server` 内网 easybot:8080 vs 公网 bot.{SERVER_NAME}.cn | 环境差异，正常 |
| OrzMC | im.yml | `backend` builtin/easybot，app_id/app_secret/client_secret 测试有值/生产空 | **刻意设计**（paper 测内置直连、生产走 EasyBot 网关，2026-09-12 老板确认） |
| OrzMC | im_bindings.yml | `sessions` 空 / `{}` | 表示差异，无实质影响 |
| EzShops | shop-dynamic.yml | Exa 端缺失 | 生产未启用动态定价 → 需确认 |
| OrzMC | ip_blacklist.yml | Exa 端缺失 | 生产未生成该文件（功能未用），无风险 |

### 3.2 延续既有判定

| 插件 | 结论 |
|:--|:--|
| OrzMC/config.yml | ❌ 5 处：`prison.cell_location` 测试 `world,-18,72,-75,0,0` / 生产仍**默认空中示例值** `world,0,100,0,0,0`；`channel` beta/release、`default_lang` en-US/zh-CN、`qq_group_id` 1082305302/1012877775、`discord_server_link` 空/已填 —— 后 4 项刻意，**cell_location 是真实待办** |
| GrimAC（5 件） | ❌ Exa 端全部缺失 = 生产端刻意不装反作弊（老板决策，登记在案） |
| CustomWorldHeight | ❌ Exa 端缺失（生产未用此插件，正常） |
| ✅ 完全一致 | DeathChest(2)、Essentials(5)、LoginSecurity(2)、**LuckPerms（今晨未覆盖，本轮补上：完全一致）**、SkinsRestorer、Vault、ViaVersion/ViaBackwards/ViaRewind、GriefPreventionData(2)、OrzMC access_rules/guide_book/portals/templates |
| ℹ️ 运行时数据（正常） | BackOnDeath/config、Essentials/upgrades-done、EzShops player-shops/shop-rotations/transactions、GetMeHome/homes、OrzMC permission/ip_blacklist |

## 四、与今晨 09:42 版逐项对比

| 项 | 09:42 降级版 | 本轮（补跑） | 变化 |
|:--|:--|:--|:--|
| 插件配置覆盖 | 3 件 | **52 件（+49）** | ✅ 修正 |
| Geyser config | ⚠️ 未覆盖 | ❌ 3 处差异（Transport / webrtc-port / debug） | **新增发现** |
| LuckPerms config | ⚠️ 未覆盖 | ✅ 完全一致 | **修正结论：无漂移** |
| GrimAC config | ⚠️ 未覆盖 | ❌ Exa 端整体缺失（= 刻意不装） | **修正结论：非配置漂移，是产品差异** |
| 其余 10 项新差异 | 未知 | 见 §3.1 | **新增发现** |
| `spigot.yml timeout-time` 60/180 | 已报 | 复核一致 | 延续 |

## 五、第三部分：版本巡检（部署版本 = SSH 直读两实例 jar 清单）

- **核心**：`papermc-test` = **Paper 26.3-223**（= fill 最新 STABLE ✅）；`folia-test` = **Folia 26.2-7**（最新 26.3-5 渠道 = **ALPHA**，按「只升 STABLE」纪律不动）
- **待升插件（MCSM paper 实例）**：Geyser-Spigot build 1265 → **1271（2.12.0）**；LuckPerms **5.5.87 → 5.5.88**；voicechat **2.6.24 → 2.6.25**
- **待升插件（folia-test）**：EssentialsC **4.3.4 → 4.3.5**；GriefPrevention3D **18.4.14 → 19.0.1（跨大版本）**；SCore **<公网IP> → <公网IP>**
- 未识别 jar：**0**（映射表无需补）
- ⚠️ **Exaroton 侧 jar 版本本轮仍无法自动盘点**：Exa v1 API 的 `/files`、`/files/list`、`/logs`、`/files/logs/latest.log` 全部 **403 Forbidden**（实测；只有已知路径的文件内容可读）→ **本节数据有效性 = MCSM 侧有效（SSH 实测 jar 清单）；Exa 侧无效/不可得**，仍属已知缺口（2026-10-12 首次记录），需面板 UI 人工盘点。
- 其余 20 项 ✅ 一致（OrzMC 1.0.29-dev.427、WE 7.4.6、WG 7.0.20、Via 5.12.1、packetevents 2.14.0、GrimAC 2.3.74、Essentials 2.22.0、F3F4Perms 1.3.0、SkinsRestorer 15.12.6、GriefPrevention 16.18.7、AxGraves 1.32.1、ExecutableEvents <公网IP>、SimpleLogin 1.16.7、VaultUnlocked 2.20.3 等）

## 六、第二部分：插件质量周报（gradle 全量测试）

commit `211c203` · 测试类 226 · **用例 2094 / 通过率 100% / 0 跳过 / 0 失败**；覆盖率 INSTRUCTION 82.0%、BRANCH 69.0%、METHOD 83.7%、CLASS 93.9%（与上期持平，无退化）。

## 七、待决策事项

1. **`spigot.yml → timeout-time`（测试 60 / 生产 180）** 连续两周分歧且未登记：① 统一 180 ② 统一 60 ③ 登记为有意差异
2. **`OrzMC/config.yml → prison.cell_location`**：生产仍为默认空中坐标 `world,0,100,0,0,0`（生产用 prison 会把人传到空中）：① 本周在 Exa 配真实牢房 ② 确认生产不用 prison（登记）
3. **WorldEdit 方块黑名单**：测试禁 lava、生产禁 bedrock：① 两端统一「lava+bedrock 都禁」（推荐）② 各自保留 ③ 仅生产补 lava
4. **EzShops `game-mode` smp/prison + `language` en/zh**：① 登记为刻意（生产 prison 经济）② 生产改回 smp/en
5. **测试服三插件升级**（Geyser 1271 / LuckPerms 5.5.88 / voicechat 2.6.25）：① 全部批准（按 SOP 升级并验证）② 只升 Geyser ③ 暂缓
6. **巡检数据源改 SSH 直读**（files API 已两次致降级/假阴性）：① 批准我改 `orzmc_config_audit.sh` + `mc_version_check.py` 的 MCSM 侧走 SSH（面板兜底）② 维持现状
7. **folia 三插件升级**（EssentialsC 4.3.5 / SCore <公网IP> / GriefPrevention3D 19.0.1 跨大版本）：① 全部批准（GP3D 先备份+回滚预案）② 只升前两项 ③ 暂缓

> 工具链：`cmp3_configs.py` + `cmp3_report.py`（基准 /tmp/mcsm_configs2 58 件 / 对比 /tmp/exa_configs2 50 件）；部署版本 = SSH 直读 jar 清单；质量 = `orzmc_quality_report.py`；证据 JSON `/tmp/scan_partial.json`（26 次 list 耗时）+ `/tmp/fetch_prio_ev.json`（签发/拉流失败清单）。
