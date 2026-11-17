# 两端配置漂移报告 · 2026-10-19（周巡检）

- 巡检端：MCSM({SERVER_NAME}.cn, Windows 栈) = 基准端 / Exaroton（生产）= 对比端
- 状态：MCSM `⏹️ 停止`（0 玩家）/ Exa `OFFLINE`
- 执行方式：⚠️ **降级巡检**。`orzmc_config_audit.sh` 全量递归扫描在 MCSM 目录扫描阶段卡死 14 分钟（SSL 读挂起、面板单次 list 延迟 5.6s+、随后 sign/stream 大量失败），已终止；改用「核心 7 件 + 6 个关键插件配置」定点拉取对比。
- 覆盖：核心 7/7；插件 4 个可比（OrzMC config/permission、Geyser、ViaVersion），另 MCSM 独有 GrimAC punishments、voicechat properties，Exa 独有 LuckPerms config。

## 一、核心配置

| 文件 | 结论 |
|:--|:--|
| bukkit.yml / spigot.yml / commands.yml / wepif.yml / config_paper-global.yml | ✅ 一致 |
| server.properties | ❌ 16 处值差异 + 2 个单端独有键 |
| config_paper-world-defaults.yml | ❌ 2 处值差异 + 7 个单端独有键 |

### server.properties 差异（均为环境/用途差异，非误配）
| key | MCSM（测试） | Exa（生产） | 判定 |
|:--|:--|:--|:--|
| enable-rcon | true | false | 测试服自动化需要；生产无 RCON 属刻意 |
| management-server-enabled / host / port | false / localhost / 0 | true / 0.0.0.0 / 9900 | Exa 面板管理端口，环境特性 |
| management-server-secret | (测试密钥) | (生产密钥) | 各自独立，正常 |
| management-server-tls-enabled | true | false | 环境特性 |
| max-players | 150 | 20 | 用途差异 |
| max-tick-time | 60000 | 600000 | 用途差异 |
| motd | 测试服-验证地图恢复状况 | 海外服宣传语 | 用途差异 |
| pause-when-empty-seconds | -1 | 60 | 用途差异 |
| rcon.password | {TEST_PASSWORD} | （空） | 与 enable-rcon 一致 |
| resource-pack-prompt | （空） | "" | 表示差异，无实质影响 |
| server-port | 25565 | 39742 | Exa 端口映射 |
| simulation-distance / view-distance | 3 / 6 | 5 / 10 | 性能策略差异（测试服更保守） |
| sync-chunk-writes | true | false | 用途差异 |
| 单端独有 | — | `previews-chat`, `pvp`（26.3 新键，测试服已有） | 生产核心较旧 |

### config_paper-world-defaults.yml
- `despawn-ranges.*.hard/soft`：MCSM=`default`（新 schema），Exa=`128/32`（旧 schema 显式值）；另有 7 个 Exa 独有的旧版 obfuscation/hide-itemmeta 键。
- 判定：**配置 schema 代差**（生产 Paper 26.2 旧配置未随版本重生成），非运行行为漂移。

## 二、插件配置

| 文件 | 结论 |
|:--|:--|
| ViaVersion/config.yml | ✅ 完全相同（81 键） |
| Geyser-Spigot/config.yml | ⚠️ config-version 9(MCSM) vs 7(Exa)；单端独有 14 键（新版键测试服已有） |
| OrzMC/config.yml | ⚠️ 5 处差异 + 5 个单端独有键 |
| OrzMC/permission.yml | ⚠️ MCSM 29 键 vs Exa 4 键（25 键仅测试服有） |
| GrimAC/punishments.yml | MCSM 独有（生产无 GrimAC，刻意） |
| voicechat/voicechat-server.properties | MCSM 独有（生产无 voicechat，刻意） |
| LuckPerms/config.yml | Exa 独有（本轮 MCSM 拉流失败，未比对） |

### OrzMC/config.yml 要点
- `config-version`: MCSM **15** vs Exa **12** → 生产配置落后 3 个 schema 版本（升级 jar 时必须同步迁移）。
- `prison.cell_location`: MCSM `world,-18,72,-75,0,0`（已配牢房）vs Exa `world,0,100,0,0,0`（**默认空中示例值，未配置**）。
- `channel`: beta(测试) vs release(生产) — 刻意。
- `qq_group_id`: 1082305302(测试) vs 1012877775(生产) — 刻意（不同群）。
- `discord_server_link`: 测试为空 vs 生产已填 — 刻意。

## 三、结论与建议（仅报告，未改任何配置）

1. **无意外漂移**：核心一致项 5/7；差异项都能用「测试 vs 生产」「新 vs 旧 schema」解释。
2. **需要跟进的真实缺口**：
   - Exa `OrzMC/config.yml` config-version 12（落后 3 版）+ `permission.yml` 仅 4 键 → 生产 OrzMC 插件仍 1.0.24，**升级 jar 时必须同步配置迁移**（见 `references/test-server-upgrade-sop.md`）。
   - Exa `prison.cell_location` 仍是默认空中坐标 → 若生产启用 `/prison`，玩家会被传到空中。
3. **面板健康**：本次全量扫描失败于 MCSM 面板限流/SSL 挂起（单次 list 5.6s，sign/stream 间歇失败）。建议检查 Windows 侧面板/cloudflared 隧道负载；巡检脚本可考虑「manifest 缓存优先 + 单次 list 超时 8s + 失败即降级核心集」以免整轮空转。
4. 工具缺陷：`cmp3_configs.py` 插件段 `b_path = BASE/plugins/{pdir}/{rel}` 与 `rel` 已含 `pdir` 重复拼接，导致插件配置恒判「基准缺失」。本次已用临时语义 diff 绕过；建议修脚本（rel 改为相对 `pdir_path`）。
