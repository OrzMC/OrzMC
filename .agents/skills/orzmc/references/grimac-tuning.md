# GrimAC 反作弊配置调优（2026-09-12 由独立技能 grimac-config-tuning 合并入 orzmc）

> ⚠️ 本技能 **SKILL.md 内另有 GrimAC 大段**（三端版本、处罚梯度决策史、kick/alert/log 三通道实测、bot 误报豁免、`/grim history` 权限等）——两者互补：
> **SKILL.md = 部署现状与决策史**；**本文 = 配置语义 / 官方文档获取 / 误报源对照 / 工具坑**。

## When to Use

- 调 GrimAC 检测参数 `config.yml`、处罚组 `punishments.yml`、豁免权限（组级或 per-check）
- 排查玩家被 GrimAC 踢出/告警的**误报**（对照官方 mods 兼容清单与已实证误报源）
- 需要 GrimAC 官方文档/默认配置模板做核验或对比（网络受限环境的获取方法见下）
- 评估引入社区「调优包」或反作弊豁免策略

> 背景：OrzMC 三端部署 GrimAC 2.3.74（config-flavor V2 / config-version 11）。2026-09-02 完成官方推荐值核验（结论：`config.yml` 与官方模板**零漂移**，官方无惩罚推荐值，自建 `punishments.yml` 阈值表是实证沉淀）。

## 官方文档获取（网络受限/GFW 环境，2026-09-02 实测）

- ❌ `web_extract`/浏览器对 GitHub/wiki 站点常被 DNS 劫持拦截（`Blocked: URL targets a private or internal network address`）——**别在 web_extract 上耗轮次**
- ✅ **GitHub git/curl 443 直连可用**：
  ```bash
  git clone --depth 1 https://github.com/GrimAnticheat/Grim.wiki.git /tmp/grim-wiki
  # 官方完整配置模板（含每个参数的英文注释与默认值）：
  curl -sL "https://raw.githubusercontent.com/GrimAnticheat/Grim/2.0/common/src/main/resources/config/en.yml"
  ```
- Wiki 文档地图：`Configuration.md`（短，指 en.yml）/ `Punishments.md`（机制+示例）/ `Permissions.md`（豁免权限全表）/ `Checks.md` / `Commands.md` / `Known-incompatible-client-mods.md`（官方误报 mods 清单）
- 版本注意：en.yml 是 2.0 分支模板；本地运行版用 `plugins/GrimAC/config.yml`。核验漂移 = 去注释行后 diff 两者

## 配置三层体系（OrzMC 2026-09-02 现状）

1. **config.yml** = 官方默认（零手动改动）→ 调参面窄，默认已适配非竞技小服
2. **punishments.yml** = 自建处罚组：9 组窗口阈值（Simulation 100 / Knockback 15 / Post 30 / BadPackets 30 / Reach 5 / Hitboxes 15 / Misc 25 / Combat 40 / Autoclicker 40）+ TimerLimit 独立组**纯告警**（A 方案 2026-09-02：`1:1 [log]` + `100:20 [alert]` 无 kick —— TimerLimit 是防 TimerA 补偿滥用辅助，高延迟误报实证 joker 123 / mellkrin 166 / Askzyng 116）
3. **LP 豁免层**：运维 bot 用户级 `grim.exempt`；builder+admin 挖掘类 per-check（fastbreak/airliquidbreak）；admin 组授权有历史坑（joker 案例须用户级/builder 组）

## per-check 权限三兄弟（官方 Permissions.md）

| 权限 | 效果 | 用途 |
|:--|:--|:--|
| `grim.exempt.<check>` | 完全关闭该检测（免检测+计数+告警） | 确认误报的正当工具副作用（如挖掘类给 builder） |
| `grim.nosetback.<check>` | 免该检测 **setback 拉回**，检测/计数/告警照常 | 网络差玩家免被拉回打断，恶意仍记录可踢 —— **比全豁免精细的中间档** |
| `grim.nomodifypacket.<check>` | 免数据包取消/修改 | 罕见兼容场景 |

- check 名 = 类名（LP 大小写不敏感；`grim.exempt.fastbreak` 实测有效）
- 移除权限在线即时生效（wiki 注明）
- ⚠️ `grim.exempt`（全豁免）关掉一切检测连 alert 都不发 = 完全静默，授予前权衡「权限外恶意盲区」（加速跑图偷家/killaura/连点）

## punishments.yml 语法要点（官方 Punishments.md）

- 阈值 N = `remove-violations-after`(默认 300s) **窗口内违规次数**（反编译确认），**非 VL**；每次违规后各命令按「窗口计数≥阈值」逐条执行（不互斥）
- 命令格式 `"N:M 动作"`：N=窗口违规阈值、M=重复间隔防刷屏、0=无限制；`[alert]`/`[log]`/`[webhook]` 特殊动作，其余控制台执行
- **`!` 排除前缀**：`checks: ["BadPackets", "!BadPacketsA"]` = 类别内排除子检测（子检测误报时精确排除，不必拆整类）
- 移除某 check 于所有类别 = 禁用该检测
- 改后 `/grim reload` 热生效

## 误报源与官方 mods 兼容性（节选，2026-09-02）

| 客户端 mod | 官方标注 | 处置 |
|:--|:--|:--|
| **Inventory Profiles Next (IPN)** | Flags **MultiActionsC** | 若玩家 MultiActions 误报先问是否用 IPN；`!` 排除或玩家知会 |
| Toro's Auto Mine | FastBreak/MultiBreak | 挖掘类豁免覆盖 |
| ViaFabricPlus | Simulation/BadPackets | 客户端侧 via，旧协议误报源构成 |
| Anchor Optimizer | Simulation | 玩家知会 |
| **Tweakeroo（含 Fake Sneak Placement）** | **不在官方不兼容列表** | 官方认为不冲突；伪潜行理论可命中 Simulation 但需持续移动+不自洽才积累窗口，建筑党站立放置基本无感 |

- 其它已实证误报源（非 mod 类）：TimerLimit 高延迟（已降纯告警）、ViaVersion 降级 767 旧协议慢性 Simulation（Twiluomu 822 次分散不触发踢但污染告警）、高 ping + 客户端辅助 MultiActions/BadPacketsJ

## 工具坑

- **macOS `strings` 对 .class 报 "fat file truncated"**：class 文件被当 Mach-O 解析失败 → 用 python `re.findall(rb'[\x20-\x7e]{4,}', data)` 提取可打印串（找 check 类内部键如 `grim.timer.timer` / 显示名 `TimerA`）
- check 类在 jar 路径 `ac/grim/grimac/checks/impl/<类别>/<Check>.class`（timer 包：Timer=TimerA、TimerLimit、NegativeTimer、TickTimer、VehicleTimer）
- 阈值语义/处理判定走 `scripts/grim_history.py`；kick 判定 = 日志 ±10s 内 kick 记录

## 决策记录（2026-09-02）

- TimerLimit 独立组 + 纯告警降级（A 方案，本地已生效，Exa/MCSM 待同步）
- `config.yml` 官方默认**零改动建议**（核验报告 `~/grimac-config-verify-20260902.md`）
- 不引入社区整包调优（免费 SpigotMC/BuiltByBit 付费面向竞技大服，换包丢实证沉淀）
- builder 层全豁免反作弊：待老板拍板（权衡 = 创造/WE 已有合法路径 vs 权限外恶意盲区）；中间档 = 移动类 `grim.nosetback.*`（免除拉回不免疫踢出）
