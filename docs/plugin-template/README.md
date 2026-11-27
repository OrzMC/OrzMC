# OrzMC PluginTemplate 方案

> 状态：P0/P1、P2.0–P2.4 已完成；P3 Paper smoke、MockBukkit、Dependabot、CodeQL 自动化已实现；真实 Paper smoke 已至少通过 20 次
> 最后更新：2026-11-27
> 目标仓库：`OrzMC/PluginTemplate`（已创建）
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

## 4. 代码来源与授权

- RealTime 与 OrzMCPlugin 均由维护者拥有，维护者可授权复用；许可证不是本方案的阻碍。
- 默认采用独立设计和实现，不为了省事直接抄代码。
- 如某个现有实现确有复用价值，先列出具体文件、复用范围、理由、替代方案和许可证/声明影响，再请求维护者明确授权。
- 获得授权后，逐文件登记来源 commit、源路径、目标路径、修改范围和测试。

## 5. 明确不做

不建设通用运行时 SDK，不把 RealTime 或 OrzMCPlugin 的业务模块迁入模板，不在第一版实现自动升级机器人，也不强制引入数据库、PlaceholderAPI、LuckPerms、自动更新、统计平台或 Mineflayer。

## 6. 文档导航

- [架构设计](architecture.md)
- [能力抽取矩阵](capability-matrix.md)
- [现有项目源文件映射](source-mapping.md)
- [P0 决策记录](decisions.md)
- [实施路线与验收标准](roadmap.md)
- [GitHub Actions 真实 Paper 服务器冒烟测试设计](github-actions-smoke.md)
- [MockBukkit 测试边界](../../tools/PluginTemplate/docs/mockbukkit.md)
- [依赖与密钥安全设置](../../tools/PluginTemplate/docs/security.md)

## 7. 状态与治理

- P0 已完成主要源文件路径、构建配置、插件元数据、调度器、生命周期、测试策略和许可证审计。
- P0 的 Java preset、传统 plugin.yml、生命周期、命令与 Folia 声明边界已在 P1 实现中落地；配置模型和构建约定仍需最终评审。
- P1 已通过 GitHub Actions 构建/JAR 检查及 Paper 26.3 build 263 隔离服务器验收。
- P2.0 架构设计已合并；P2.1 ResourceScope/lifecycle 已合并；P2.2 Typed config、校验、v0→v1 schema migration、Paper YAML adapter 与事务式 reload 已合并（子仓库 PR #6，CI Run #45 全绿）。
P3.0–P3.7 已完成 Paper smoke runner、双重 EULA 门禁、精简 evidence artifact、负向回归测试、daily latest-STABLE nightly workflow 和运维文档。P3.8/P3.9 增加 MockBukkit listener 生命周期集成测试、skipped-test fail-closed、JUnit reports 和测试范围说明（子仓库 PR #17/#18）。P3.10 增加 Dependabot weekly updates、SECURITY.md 和 Gradle dependency graph submission workflow（子仓库 PR #19，merge `3911980`）。P3.11 增加 CodeQL Java/Kotlin advanced analysis workflow（子仓库 PR #24，PR CI #45965508559、CodeQL #45965508460 success，merge `d7b8e71`）。P3.12 合并首批 4 个 Dependabot 更新 PR #20–#23，均通过构建和真实 Paper smoke。P3.13 增加 MockBukkit Paper YAML adapter 测试，PR #25 的构建、真实 Paper smoke 和 CodeQL 均通过。真实 Paper smoke 已累计至少 20 次通过；首次定时 nightly 执行仍待验证。Dependency Submission 仍因 GitHub Dependency Graph 设置关闭而失败，管理员需在 Settings → Security & analysis 启用后重跑。
- 本方案保存在父仓库 `docs/plugin-template/`；模板工程代码进入独立 `OrzMC/PluginTemplate`。
- 当前推进不修改 RealTime 或 OrzMCPlugin。任何源项目改造先提交详细评估，未经明确批准不执行。
- 未来若建设 PluginBuildLogic 或 PluginSDK，必须由至少两个独立插件的真实重复需求驱动。
