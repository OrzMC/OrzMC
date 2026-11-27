# OrzMC PluginTemplate 方案

> 状态：P0 源码级审计已完成，关键决策待评审
> 最后更新：2026-11-27
> 目标仓库：计划新建 `OrzMC/PluginTemplate`
> 本文档归属：`OrzMC/OrzMC` 父仓库的伞级方案；模板代码最终进入独立仓库，不进入父仓库子模块目录。

## 1. 目标

建设一套可重复使用的 Paper 插件工程模板，并在通过真实 Folia 验收后扩展 Folia 支持。新插件从创建之日起具备：

- 独立构建、测试和发布能力；
- 清晰的 Core / Paper / Feature 分层；
- 生命周期、配置、命令、事件、调度、日志等基础设施；
- Paper/Folia 线程模型安全边界；
- 单元测试、MockBukkit 集成测试及真实服务端冒烟测试入口；
- GitHub Actions CI、受保护发布流程和制品检查；
- 面向 Pi Agent、Codex、Claude Code 的 Agent Native 开发规范；
- 项目初始化和模板版本升级机制。

模板不是 OrzMCPlugin 的精简复制品，也不是强制引入所有依赖的运行时框架。它是“可运行的最小插件骨架 + 按需启用的能力 + 可验证的研发流程”。

## 2. 现有项目作为证据来源

| 项目 | 当前分支 | 在本方案中的角色 |
|---|---|---|
| [OrzMC/RealTime](https://github.com/OrzMC/RealTime) | `main` | MIT；Kotlin、JDK 25、Gradle Kotlin DSL、多模块；参考 Core/Paper 分层、global/region/entity 调度、任务注册、验证脚本和发布 |
| [OrzMC/OrzMCPlugin](https://github.com/OrzMC/OrzMCPlugin) | `develop` | GPL-3.0；Java 为主、JDK 25、Gradle Kotlin DSL；参考组合根、模块生命周期、类型化配置、LifecycleEvents/Brigadier、MockBukkit、真实服 E2E 和质量门禁 |

当前项目版本是调研快照，不应永久写死。正式模板应集中管理 JDK、Gradle、Paper API、测试库和 GitHub Actions 版本。

## 3. P0 核心建议

| 主题 | 建议 | 理由 |
|---|---|---|
| 仓库 | 独立 `OrzMC/PluginTemplate` | 可独立使用、版本化；父仓库只保存方案和子模块指针 |
| 首个语言 preset | Java；Gradle 使用 Kotlin DSL | 避免首版同时维护 Java/Kotlin 两套模板 |
| JDK | 默认 JDK 25 | 与两个参考项目当前基线对齐，版本集中管理 |
| 模块 | `plugin-core` + `plugin-paper` | Core 不依赖 Bukkit；Paper 负责适配和装配 |
| DI | 显式组合根 + 构造器注入 | 不引入重量级 DI 框架 |
| 生命周期 | 统一 start/stop、启动回滚、逆序关闭、异常隔离 | 补强参考项目中尚未覆盖的部分启动失败路径 |
| 命令 | Paper LifecycleEvents + Brigadier | 命令注册与业务用例分离 |
| Folia | P1 暂不声明支持；P2 通过真实 Folia smoke 后再启用 | 不把通用 sync/async 包装误当成区域线程安全 |
| 测试 | JUnit + MockBukkit + 真实 Paper smoke；Folia smoke 在 P2 加入 | 证据按层次分开，避免 mock 冒充真实运行 |
| 发布 | GitHub Release 必备；Hangar/Modrinth 可选 | 无外部凭据时明确跳过 |
| Agent | `AGENTS.md` 为事实源，角色/工作流/策略按需加载 | 支持多 Agent 接手和 Worktree 隔离 |
| 模板升级 | manifest + upgrade notes + Agent 辅助 PR | 不覆盖用户业务代码 |
| SDK / Build Logic | 首版不拆独立仓库 | 至少两个独立插件证明重复需求后再抽取 |

## 4. 许可证边界

- RealTime 是 MIT；OrzMCPlugin 是 GPL-3.0。
- 源项目只作为架构和行为证据。P1 默认独立实现，不直接复制 OrzMCPlugin 的 GPL 代码。
- 若后续决定直接复用 GPL-3.0 实现，必须先确认模板及衍生项目的许可证和分发义务。
- 每个实际复用文件都登记来源、commit、许可证、目标路径和测试。

## 5. 明确不做

不建设通用运行时 SDK，不把 RealTime 或 OrzMCPlugin 的业务模块迁入模板，不在第一版实现自动升级机器人，也不强制引入数据库、PlaceholderAPI、LuckPerms、自动更新、统计平台或 Mineflayer。

## 6. 文档导航

- [架构设计](architecture.md)
- [能力抽取矩阵](capability-matrix.md)
- [现有项目源文件映射](source-mapping.md)
- [P0 决策记录](decisions.md)
- [实施路线与验收标准](roadmap.md)

## 7. 状态与治理

- P0 已完成主要源文件路径、构建配置、插件元数据、调度器、生命周期、测试策略和许可证审计。
- 仍待维护者确认 P0 决策，并手动创建独立模板仓库。
- 本方案保存在父仓库 `docs/plugin-template/`；模板工程代码进入独立 `OrzMC/PluginTemplate`。
- 当前推进不修改 RealTime 或 OrzMCPlugin。任何源项目改造先提交详细评估，未经明确批准不执行。
- 未来若建设 PluginBuildLogic 或 PluginSDK，必须由至少两个独立插件的真实重复需求驱动。
