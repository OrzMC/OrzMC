# PaperMC 插件端到端测试方案调研

> **日期**：2026-08-06
> **来源**：web 调研（MockBukkit / WatchWolf / GameTest / Testcontainers）+ OrzMC 实战经验
> **结论**：PaperMC 插件 E2E 无"一键式"成熟方案；**MockBukkit 做底层逻辑 + 真实环境 E2E 做最终验收**是最实用组合。

## 方案总览（按层级）

| 层级 | 方案 | 核心思路 | 适合场景 |
|:--|:--|:--|:--|
| 单元测试 | MockBukkit | 内存 mock 整个 Bukkit API，无真实服务器 | 事件逻辑、命令解析、纯业务 |
| 服务器内集成 | WatchWolf | 启动真实服务器 + 连接真实客户端，编排测试 | 多服交互、协议级行为 |
| 原版测试框架 | GameTest Framework | Mojang 官方 `@GameTest`，结构内断言 | 方块/实体/世界交互 |
| 真实环境 E2E | 测试服 + 机器人/RCON | 生产同构环境，bot/RCON/真实玩家驱动 | 验收、插件互操作、跨服（OrzMC 采用） |
| 容器化 | Docker 测试服 | 一次性容器起服跑测试，CI 集成 | 持续集成、可重复回归 |

## 各方案详解

### 1. MockBukkit（最主流）
- **定位**：mocking 框架，JUnit + Hamcrest，**秒级跑完测试套件**
- **能力**：mock 服务器/玩家/世界，测事件、命令、玩家交互
- **资源**：github.com/MockBukkit/MockBukkit、docs.mockbukkit.org、mockbukkit.org
- **局限**：非真实服务器——调度器、网络、真实方块引擎是 mock 的；**协议层/跨服/性能相关测不了**
- **实战**：OrzMC 已有 `integrationTest`（MockBukkit，`./gradlew integrationTest` 需要 Java 25），但 transfer/传送门等真实服务器行为必须真机测

### 2. WatchWolf（集成测试框架）
- **定位**：Spigot 插件**集成测试**，一键拉起多服务器 + 自动连接客户端
- **能力**：编排 client + server 双向控制，测跨服/多玩家场景
- **资源**：github.com/watch-wolf/WatchWolf、spigotmc.org/resources/watchwolf.107051、watchwolf.dev/docs/testing
- **局限**：文档少、社区小（2023 年后活跃度低）、学习曲线陡
- **适配度**：概念上正是"双服 transfer 自动化测试"，但生态不活跃，OrzMC 用手动 E2E 达成同等目标

### 3. GameTest Framework（原版）
- **定位**：Mojang 官方，`@GameTest` 注解 + `GameTestHelper` 断言，**结构内**测试（方块/实体/世界）
- **局限**：**Paper 上不完整支持**（Paper 移除了部分 vanilla 测试钩子，主要面向 mod 平台 Forge/Fabric）；插件 API 交互（玩家、GUI、命令）覆盖弱
- **适合**：纯世界交互类插件（如 TNT 结构、传送门方块）

### 4. 真实环境 E2E（✅ OrzMC 采用，已实战）
- **架构**：测试服（production 同构）→ 驱动层（mineflayer bot + RCON + screen 注入 + 真实玩家）
- **实战成果**：28 项用例全过 + 双服 transfer 闭环 + 发现并修复 1 个 bug（详见 orzmc-acceptance-20260806.md）
- **优势**：**最真实**——插件互操作（LoginSecurity/Essentials/Geyser）、协议层行为（transfer）、性能影响全部覆盖
- **代价**：手动/半自动，需要运维脚本沉淀（已做：rcon.py / portal-cmd.js / portal-probe.js）
- **关键脚本**：
  - `scripts/rcon.py` — RCON 控制台命令
  - `scripts/bot/portal-cmd.js` — bot 玩家身份执行 `/portal` 系列命令
  - `scripts/bot/portal-probe.js` — blockAt 扫描传送门方块（观察探针，不做断言）
- **⚠️ 分工（2026-11-16 定）**：**产品行为的断言一律归仓库测试**，技能只留「够不到 CI 的运维探针」。
  - 传送门逻辑：仓库已覆盖 → `PortalIntegrationTest`（集成）+ `PortalServiceTest` / `PortalBuilderTest` / `PortalCleanerTest` / `PortalPersistenceTest` / `PortalLabelRendererTest`（单测）
  - 原技能脚本 `portal-transfer-test.js` 已归档：它自身注明「mineflayer 位置同步与服务器端不一致，tp 到门中心也不触发 PlayerPortalEvent，真实玩家验证是唯一可靠方式」= **不能作为回归断言**，留着只会造成"有测试"的错觉

- **验证通道**：主服日志可能停更（Paper 缓冲）→ 用 RCON 确认状态 + 第二服日志实时写入可查 transfer 痕迹

### 5. Docker 容器化（CI 友好）
- **定位**：Testcontainers 风格，CI 里起一次性 Paper 容器跑测试
- **局限**：Minecraft 插件生态**无成熟封装**（无官方 Testcontainers 模块），需自建 Dockerfile + 端口映射 + 等待就绪；资源占用高
- **适合**：有 CI 的团队项目做回归基线

## CI 自举 E2E（仓库现行做法：Gradle 起服 + node 探针）

「真实环境 E2E」的**可自动跑版本**：Gradle 任务自己下载核心、起一次性服务端（`runHeadlessServerSmoke`，隔离 run 目录 + 独立端口）→ 跑 `node` 探针（mineflayer 客户端 / 控制台断言）→ 收尾停服。范本是 `e2eLocalPlayer`；新增同类任务照搬它的结构（`dependsOn` 下载任务 + `extraPlugins` + `preChecks` + `afterReady` 里拉探针）。CI job 照 `e2e-player`（jdk25 + node 22 + `./gradlew <task> --stacktrace`）。

**迁移判断：一条断言该不该从技能侧脚本迁进这里？**
- 测的是**插件自身行为**（命令/权限/事件/实体策略）→ 迁，且**只用插件自己的节点与命令做断言**。CI 里没装 Essentials/WorldEdit/Geyser，拿它们的权限名或命令做断言，只会得到一个永远 `Unknown` 的假测试。
- 测的是**第三方插件**（DeathChest/EzShops/LoginSecurity）或纯环境探活 → 留在技能侧。
- 原脚本「只打印日志让人肉眼看、没有 pass/fail」→ 那不算测试，迁移时是**重写断言**，不是搬运代码。

**写这类任务/探针的五条硬规则**（每条都踩过）：
1. **别把「日志里不得出现 X」当失败判据——先问行为断言是否已覆盖**。日志守卫有三种死法：① 全新 CI 世界里同一句日志由**无关实体/背景事件**打印（实测：实体传送策略拦下世界自带的 `Crimson Roots`，7 条真实断言全过却判红）；② 缩小到实体名仍不可靠——名字形态可能是 `Villager` / `VILLAGER` / `minecraft:villager`，大小写敏感的裸串**永远匹配不上 = 恒绿**；③ 扫描起点是 offset 0，复用 run 目录时把上一轮的历史日志算进本轮，无端变红。**行为证据够（如「实体确实跨了维度」）就删掉守卫**；确要保留必须同时满足：探针启动前取日志 offset 只扫本窗口、正则 `(?i)` 且覆盖名字形态、并对「该命中的」与「不该命中的」样本各跑一次证明它既能命中也会放过。
2. **每个 PASS 前面加一条前置守卫**，防「因为前置步骤没生效而假绿」：例如断言「村民已过门」之前，先断言「过门**前**村民确实在门槛内」，否则 summon 失败时「原维度没有村民」也会被当成成功。
3. **客户端探针有协议天花板**：mineflayer 经 ViaBackwards 连新版服务端时，1.21.x 会被判 `Invalid move player packet` 踢人且拿不到区块数据 → 探针固定一个确定能连的客户端版本（如 1.20.4），且**不要在探针里 tp 客户端**。
4. **异步写库的中间件（如 LuckPerms）不能靠固定 sleep 同步**：LP 只按名字解析**登录过**的玩家 → 流程必须是「各账号先登录一轮登记 → 再下发 `lp user ... parent set` → 再跑断言」；等待条件用「本次发出的 N 条 `[LP]` 输出落地」这类可数证据，而不是 sleep。⚠️ 只等「行数到齐」不够——报错行同样计数，要再断言「非白名单错误行 == 0」（白名单仅限 `already exists` 这类幂等预期）。
5. **超时预算必须覆盖各步最坏耗时之和，清理放 `finally`**：全局 `setTimeout` 若小于「spawn + 建场景 + 等待 + 断言 + 清理」之和，慢 runner 上会以「总超时」退出——**既报不出哪条断言失败，又跳过清理**，下一轮靠残留状态碰运气。做法：收紧单步上限（本机 Paper spawn 30s 足够）、全局 = 各步之和 ×1.5 + 余量、Gradle 侧 `timeoutMs` 再大一级；`kill` / `fill air` / `quit` 全进 `finally`；超时信息要带「卡在第几步」。

**验证纪律**：新任务必须在**本机**先跑通（`./gradlew <task>`），CI 只当复核；顺手故意破坏一条断言确认能非 0 失败再改回，否则「永远绿的任务」比没有任务更糟。注意本机绿 ≠ CI 绿（世界/插件版本/时序都可能不同）——CI 红了先 `gh run view <run-id> --log-failed` 定位到具体断言，别重跑碰运气。

**探针的域事实（踩过才知道，写断言前先看）**：

| 事实 | 后果 |
|:--|:--|
| 下界换算：原版只缩放 **X/Z（÷8）**，**Y 原样带过去** | 算传送后锚点时把 Y 也 ÷8 → 锚点偏几十格，必然假红 |
| 实体/位置判定要 `execute positioned <x> <y> <z> ...` 锚定绝对坐标 | 用 `distance=..N` 隐含假设「命令源 = 世界出生点」，出生点一变就永远等不到目标 |
| 宽 token 不是放行证据：`/HTTP/` 对任何错误回显（`HTTP 403`、`HTTP timeout`）都命中 | 正向断言要么用稳定状态词，要么降级为「未收到拒绝文案」，并在注释写明它不是放行证据；放行证据由同 run 的正向控制（组名回显、命令用法回显）成对兜住 |

## 推荐组合（OrzMC 现状）

| 层 | 工具 | 作用 | 状态 |
|:--|:--|:--|:--|
| 单元/集成 | MockBukkit（integrationTest） | 业务逻辑快测 | ✅ 已有，Java 25 |
| 验收 | 真实环境 E2E（bot+RCON+真实玩家） | 上线前最终把关 | ✅ 28 项 + 文档化 |
| 自动化双服 | WatchWolf（可选项） | 跨服场景自动化 | ⚠️ 生态不活跃，暂不引入 |

## 测试文档索引

- 功能测试用例（28 项）：插件仓库 `plugin/docs/test-cases.md`
- 端到端测试报告：插件仓库 `plugin/docs/e2e-test-report-20260806.md`
- 验收报告（技能内）：`references/orzmc-acceptance-20260806.md`
