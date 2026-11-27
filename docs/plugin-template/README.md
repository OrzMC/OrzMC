# OrzMC PluginTemplate 方案

> 状态：P0 架构与能力抽取方案（待评审）
> 最后更新：2026-11-27
> 目标仓库：计划新建 `OrzMC/PluginTemplate`
> 本文档归属：`OrzMC/OrzMC` 父仓库的伞级方案；模板代码最终进入独立仓库，不进入父仓库子模块目录。

## 1. 目标

建设一套可重复使用的 Paper/Folia 插件工程模板，使新插件从创建之日起具备：

- 独立构建、测试和发布能力；
- 清晰的 Core / Platform / Feature 分层；
- 生命周期、配置、命令、事件、调度、日志等基础设施；
- Paper/Folia 线程模型安全边界；
- 单元测试、MockBukkit 集成测试及真实服务端冒烟测试入口；
- GitHub Actions CI、受保护发布流程和制品检查；
- 面向 Pi Agent、Codex、Claude Code 的 Agent Native 开发规范；
- 项目初始化和模板版本升级机制。

模板不是 OrzMCPlugin 的精简复制品，也不是一个强制引入所有依赖的运行时框架。它是「可运行的最小插件骨架 + 按需启用的能力 + 可验证的研发流程」。

## 2. 现有项目作为证据来源

| 项目 | 当前基线 | 在本方案中的角色 |
|---|---|---|
| [OrzMC/RealTime](https://github.com/OrzMC/RealTime) | Kotlin、JDK 25、Gradle 9.2.1、Paper/Folia 26.3、多模块 | 独立插件工程、Core/Platform 分离、Paper/Folia 调度、独立配置、脚本化验证和受保护发布的主要参考 |
| [OrzMC/OrzMCPlugin](https://github.com/OrzMC/OrzMCPlugin) | Java/Kotlin 混合、JDK 25、Gradle Kotlin DSL、Paper/Folia 26.3 | 大型插件模块装配、六边形架构、类型化配置、命令拦截器、MockBukkit、真实服 E2E、安全与质量门禁的主要参考 |

版本信息是当前项目快照，不应被永久写死在模板规范中。正式模板应通过集中版本配置管理 JDK、Gradle、Paper API、Kotlin、测试库和 GitHub Actions 版本。

## 3. 核心决策

| 主题 | P0 建议决策 | 理由 / 约束 |
|---|---|---|
| 仓库形态 | 独立仓库 `OrzMC/PluginTemplate` | 模板必须能独立使用、独立版本化；父仓库只登记子模块指针 |
| 初始平台 | Paper API，提供 Folia-safe 适配层和兼容声明 | Paper 是基础平台；Folia 能力必须有明确实现和运行证据，不能只设置元数据 |
| JDK | 默认 JDK 25，版本集中管理 | 与两个现有项目当前基线对齐；升级由模板维护者统一评估 |
| 构建 | Gradle Kotlin DSL | 两项目一致；Kotlin DSL 不等于业务代码必须使用 Kotlin |
| 业务语言 | Java 作为首个可运行默认配置；Kotlin 作为独立 preset 后续验证 | 避免同一初始工程混合两种业务语言；保留 RealTime 的 Kotlin 实践 |
| 架构 | 单插件多模块：core + paper + optional integrations | 保持可测试和边界清晰，避免一开始拆成多个发布仓库 |
| DI | 显式组合根 + 构造器注入 | 继承 OrzMCPlugin 的可读性与可控性，不引入 DI 框架 |
| 生命周期 | 模块接口统一 start/stop（或 setup/teardown） | 初始化顺序、失败回滚和关闭顺序需要集中管理 |
| 配置 | 默认 config.yml + 按功能独立模块配置 + data 独立目录 | 继承 RealTime 配置隔离与 OrzMCPlugin 类型化配置经验 |
| 命令 | Paper LifecycleEvents / Brigadier 适配器，命令业务与平台注册分离 | 不将命令注册细节散落在业务服务中 |
| 调度 | 明确 global / region / entity / async 调度语义 | Folia 安全是运行时约束，不是简单的 BukkitScheduler 包装 |
| 测试 | JUnit 单测 + MockBukkit 集成 + 可选真实 Paper/Folia smoke | 以测试金字塔为默认，复杂玩家 E2E 按需启用 |
| 发布 | GitHub Release 必备；Hangar / Modrinth 可选 | 凭据只注入受保护的发布 Job；PR 不接触发布凭据 |
| Agent | AGENTS.md 为事实源，角色/工作流/策略按需加载 | 让不同 Agent 可直接接手，且不把角色提示词强塞进所有上下文 |
| 模板升级 | manifest + 模板版本 + 变更说明 + Agent 辅助升级 PR | 不覆盖用户代码；升级必须可审查、可回滚 |

## 4. 明确不做

P0 不建设通用运行时 SDK，不把 RealTime 或 OrzMCPlugin 的业务模块迁入模板，不在第一版实现完整的模板自动升级机器人，也不强制引入数据库、PlaceholderAPI、LuckPerms、自动更新、统计平台或 Mineflayer。

## 5. 文档导航

- [架构设计](architecture.md)
- [能力抽取矩阵](capability-matrix.md)
- [现有项目源文件映射](source-mapping.md)
- [实施路线与验收标准](roadmap.md)

## 6. 状态

当前完成：两个项目的主要结构、构建、测试、发布和 Agent 工程实践盘点；形成第一版抽取边界与目标架构。

待完成：源文件级复核、决策评审、模板仓库创建、最小模板落地和真实项目验证。

## 7. 仓库治理

- 本方案保存在父仓库 `docs/plugin-template/`，仅用于跨仓协调与决策记录。
- 模板工程代码进入独立的 `OrzMC/PluginTemplate` 仓库。
- 未来若建设 `PluginBuildLogic` 或 `PluginSDK`，必须由至少两个独立插件的真实重复需求驱动。
- 父仓库只在模板仓库建成后按既有子模块规则登记模板仓库；不把模板源码复制进父仓库。
