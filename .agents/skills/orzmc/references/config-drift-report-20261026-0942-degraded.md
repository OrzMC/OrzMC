# 两端配置漂移报告 · 2026-10-26（周巡检）

- 巡检端：MCSM（{SERVER_NAME}.cn，Windows 栈，paper-test/folia-test）= 基准端 / Exaroton（海外生产）= 对比端
- 实例状态：paper-test `status=3 运行中（0 玩家）` / folia-test `status=3 运行中（0 玩家）` / Exa `OFFLINE`
- 执行方式：⚠️ **降级巡检 + 凭据修复**（详见第四节）

## 一、本轮两处平台故障（先说明，影响覆盖面）

1. **面板 API 密钥被轮换**：`~/.hermes/.env` 的 `MCSM_LOCAL_API_KEY` 在面板侧已失效（`api/auth` → `403 密钥不正确`）。
   Windows 面板 `E:\orzmc\mcsmanager\web\data\User\5c045d64….json`（用户 `joker`）的 `apiKey` 与 .env 不一致。
   影响：`mc_version_check.py` 静默输出「全部未部署」、`orzmc_config_audit.sh` MCSM 侧扫描到 0 个清单项（两者都不报错，只表现为空结果 = 假阴性）。
   → 本轮用**内存层密钥覆盖**（环境变量 → `mcsm_env._load_env` 打补丁）恢复巡检；**`.env` 未改**（cron 模式下写 .env 被安全策略拦截，待老板授权）。
2. **面板 files API 极慢**：单次 `files/list` 延迟 5.7s / 31s / 37s（实测三发），全量递归扫描（~70 次 list）在 12 分钟内无法完成 → 与 2026-10-19 同因。
   另：`files/download` 签发阶段大量失败/超时。→ 本轮改为**定点拉取**：核心 7 件全部取到，插件配置 7 件取到 4 件（Geyser-Spigot / LuckPerms / GrimAC 三件签发失败，三次重试均超时）。

## 二、核心配置

| 文件 | 结论 |
|:--|:--|
| bukkit.yml / commands.yml / wepif.yml / config_paper-global.yml | ✅ 一致 |
| spigot.yml | ❌ 1 处差异（**本轮新增**） |
| server.properties | ❌ 16 处值差异 + 2 个单端独有键 |
| config_paper-world-defaults.yml | ❌ 2 处值差异 + 5 个单端独有键 |

### spigot.yml（本轮新增差异）
| key | MCSM（测试） | Exa（生产） | 判定 |
|:--|:--|:--|:--|
| timeout-time | 60 | 180 | ⚠️ **需确认**：10-19 巡检时该项为一致，本周出现分歧。测试服 60s（快速判定卡死重启）vs 生产 180s（容忍尖峰）都算合理策略，但**不是记录在案的刻意差异**，建议明确口径后统一或登记为有意差异 |

### server.properties 差异（与 10-19 一致，均为环境/用途差异）

| key | MCSM（测试） | Exa（生产） | 判定 |
|:--|:--|:--|:--|
| enable-rcon | true | false | 测试自动化需要 |
| management-server-enabled / host / port | false / localhost / 0 | true / 0.0.0.0 / 9900 | Exa 面板管理端口 |
| management-server-secret | (各自密钥) | (各自密钥) | 正常，已脱敏 |
| management-server-tls-enabled | true | false | 环境特性 |
| max-players | 150 | 20 | 用途差异 |
| max-tick-time | 60000 | 600000 | 用途差异 |
| motd | 测试服-验证地图恢复状况 | 海外服宣传语 | 用途差异 |
| pause-when-empty-seconds | -1 | 60 | 用途差异 |
| rcon.password | (已设置) | (空) | 与 enable-rcon 一致 |
| resource-pack-prompt | (空) | `""` | 表示差异，无实质影响 |
| server-port | 25565 | 39742 | Exa 端口映射 |
| simulation-distance / view-distance | 3 / 6 | 5 / 10 | 性能策略差异 |
| sync-chunk-writes | true | false | 用途差异 |
| 单端独有 | pvp=false | previews-chat=false | 26.3 新键；生产核心较旧 |

### config_paper-world-defaults.yml
- `despawn-ranges.*.hard/soft`：MCSM=`default`（新 schema）vs Exa=`128/32`（旧 schema 显式值）；另 Exa 独有 5 个旧版 obfuscation/hide-itemmeta 键。
- 判定：**配置 schema 代差**（生产 Paper 未随版本重生成默认文件），非运行行为漂移。

## 三、插件配置

| 文件 | 结论 |
|:--|:--|
| ViaVersion/config.yml | ✅ 完全相同 |
| OrzMC/config.yml | ❌ 5 处差异（下文） |
| OrzMC/permission.yml | ℹ️ 运行时数据（两端独立，正常） |
| Geyser-Spigot/config.yml / LuckPerms/config.yml / GrimAC/punishments.yml | ⚠️ 本轮未覆盖（面板 files API 签发失败，三次重试均超时；10-19 已比对过，结论见该报告） |
| voicechat-server.properties | ⚠️ 未比对（cmp3 只比 .yml/.yaml；Exa 无此插件属刻意） |

### OrzMC/config.yml 5 处差异（均为刻意设计或待跟进）
- `prison.cell_location`：MCSM `world,-18,72,-75,0,0`（已配牢房）vs Exa `world,0,100,0,0,0`（**默认空中示例值**）
- `channel`：beta（测试）vs release（生产）— 刻意
- `default_lang`：en-US（paper 测英文语言包）vs zh-CN — 老板 2026-09-12 确认的刻意设计
- `qq_group_id`：1082305302 vs 1012877775 — 刻意（不同群）
- `discord_server_link`：空 vs 已填 — 刻意

## 四、工具与覆盖

- **修复**：`cmp3_configs.py` 插件段路径重复拼接 bug（`b_path = BASE/plugins/{pdir}/{rel}`，`rel` 已含 `pdir` → 恒判「基准缺失」）。2026-10-19 报告已记录，本轮修复并实测插件段恢复比对。
- **仍待修**：① 全量递归扫描在面板慢响应下无超时/降级策略（建议 list 超时 8s + 失败即降级核心集）；② `mcsm_list` 失败返回空列表而不抛错 → 上层表现为「全部未部署」假阴性，建议返回 None 由调用方判定；③ `mc_version_check.py` 不查 Exaroton 侧 jar（Exa 无目录列表 API，`files/logs/latest.log` 也 403 → 只能面板 UI 人工盘点）。
- 覆盖：核心 7 件中 **6 件可比**（spigot/commands 已补到）；插件配置 3 件可比（应为 7 件，Geyser/LuckPerms/GrimAC 三件拉取失败）。

## 五、结论

1. **一处新增漂移需确认**：`spigot.yml → timeout-time`（MCSM 60 / Exa 180），10-19 时一致，本周分歧且未登记为刻意差异。其余差异延续 10-19 判定（测试 vs 生产、新 vs 旧 schema、刻意设计）。
2. 真实待办仍是老三条：Exa `OrzMC/config.yml` schema 落后（config-version 12）、Exa `prison.cell_location` 仍为默认空中坐标、Exa 插件/核心版本整体落后（本轮未能量化）。
3. **本周新增风险**：面板 API 密钥失效未经通报 → 若未修，后续巡检将持续「静默空转」（脚本仍报 ok）。建议加一道断言：`/plugins` list 结果为空即判 FAIL。
