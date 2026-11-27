# PluginTemplate 现有项目源文件映射

> 状态：P0 源文件级审计（已核对主要入口；非模板代码复制授权）
> 最后更新：2026-11-27
>
> 审计范围：
> - [OrzMC/RealTime](https://github.com/OrzMC/RealTime)，默认分支 `main`
> - [OrzMC/OrzMCPlugin](https://github.com/OrzMC/OrzMCPlugin)，默认分支 `develop`
>
> 注意：GitHub 文件内容接口返回的是文件 blob SHA，不等于仓库 HEAD commit SHA。下表的路径已逐项按当前分支核对；正式 P1 抽取时仍须锁定 commit SHA，并重新检查文件内容和依赖。

## 1. RealTime（MIT）映射

| 模板能力 | 已核对路径 | 复用方式 | 注意事项 |
|---|---|---|---|
| Gradle 多模块 | `settings.gradle.kts`、`build.gradle.kts`、`realtime-core/build.gradle.kts`、`realtime-paper/build.gradle.kts` | 重建最小模块骨架 | Kotlin JVM 插件、Shadow、Hangar、Spotless 等按模板实际需求选择；不要复制产品版本策略 |
| Core 领域边界 | `realtime-core/src/main/kotlin/cn/orzmc/realtime/core/` | 参考纯 JVM 包组织和依赖边界 | 当前实现是 Kotlin；Java preset 应独立实现，不把 Kotlin runtime 无意引入 Java 模板 |
| Paper 入口与适配 | `realtime-paper/src/main/kotlin/cn/orzmc/realtime/paper/` | 参考平台入口、适配器和服务组织 | 不抽取时间/设备业务 |
| 插件元数据 | `realtime-paper/src/main/resources/plugin.yml` | 只参考字段和资源处理 | **已纠正：不是 paper-plugin.yml**。RealTime 当前用传统 `plugin.yml`；模板若选 Paper 26 的 Paper plugin loader，应单独采用并验证 `paper-plugin.yml` |
| Paper/Folia 调度 | `realtime-paper/src/main/kotlin/cn/orzmc/realtime/paper/scheduler/PaperFoliaScheduler.kt`、`TaskHandle.kt`、`TaskRegistry.kt` | 参考 global/region/entity 调度、任务所有权、取消与释放 | 该调度器不暴露通用 async 调度入口；模板必须明确补充异步执行器，并重新实现/测试，不照搬即宣称 Folia-safe |
| 命令 | `realtime-paper/src/main/kotlin/cn/orzmc/realtime/paper/command/` | 参考命令解析和执行上下文 | 尚未确认 `CommandTarget` 精确类名；不再把该名称作为已核实事实。P1 前需定位完整调用链 |
| 测试策略 | `docs/testing/strategy.md` | 复用纯 JVM、平台测试、真实服 smoke 分层思想 | RealTime 特有设备清理、更新器、PlaceholderAPI 测试不作为模板默认要求 |
| 统一验证 | `scripts/verify.sh`、`test.sh`、`lint.sh`、`build.sh` | 重建统一脚本入口 | 删除产品专属 smoke 和版本假设 |
| JAR 检查 | `scripts/inspect-jar.sh`、`scripts/distribution-check.sh` | 提取通用检查 | 外部平台字段和包名需参数化 |
| Agent / Worktree | `AGENTS.md`、`.agents/`、`scripts/check-agent-environment.sh`、`scripts/new-agent-worktree.sh`、`scripts/list-agent-worktrees.sh` | 复用入口、环境检查和隔离工作区流程 | 必须在模板生成的新仓库和不同默认分支上验证 |
| 发布 | `.github/workflows/ci.yml`、`.github/workflows/release.yml`、`docs/release/process.md` | 重建安全发布链 | 保留最小权限、无凭据时跳过外部平台发布；不得复制项目 token/ID |

RealTime 当前 `build.gradle.kts` 使用 Kotlin 2.4.21、Shadow 9.2.2、Spotless 7.2.1；Paper 模块使用 Paper API 26.3 构建版本、PlaceholderAPI compileOnly 和 Hangar 发布插件。它们是当前项目事实，不是模板必须依赖。

## 2. OrzMCPlugin（GPL-3.0）映射

| 模板能力 | 已核对路径 | 复用方式 | 注意事项 |
|---|---|---|---|
| 插件入口 | `src/main/java/com/jokerhub/paper/plugin/orzmc/OrzMC.java` | 参考轻量 `onEnable/onDisable` 入口 | 当前入口在 `assemble()` 完成前若异常，`services` 仍为 null；模板应设计显式部分启动回滚 |
| 显式组合根 | `src/main/java/com/jokerhub/paper/plugin/orzmc/OrzServices.java` | 参考显式装配和依赖顺序 | 该类包含 Bot、Portal、Maintenance、Update、Feature 等产品模块，不能复制 |
| 模块装配 | `src/main/java/com/jokerhub/paper/plugin/orzmc/assembly/FeatureModule.java`、`PlatformModule.java` | 参考平台设施与功能模块分组 | 两者含大量 OrzMC 业务服务，仅参考装配边界 |
| 生命周期契约 | `orzmc-api/src/main/java/com/jokerhub/paper/plugin/orzmc/assembly/ServiceModule.java` | 参考 `setup/tearDown` 契约 | 位于 `orzmc-api` 子模块，不在主模块 assembly 目录 |
| Core API | `orzmc-api/src/main/java/com/jokerhub/paper/plugin/orzmc/core/ports/server/ServerScheduler.java` 等 | 参考无 Bukkit 依赖的端口模块 | 该调度接口是通用 sync/async/later 语义，不足以单独证明 Folia 区域安全 |
| 六边形架构 | `orzmc-api/src/main/java/com/jokerhub/paper/plugin/orzmc/core/ports/`、`src/main/java/com/jokerhub/paper/plugin/orzmc/core/ports/`、`features/`、`infra/` | 参考 ports / features / adapters 分层 | 只抽依赖方向和最小示例 |
| 配置 | `src/main/java/com/jokerhub/paper/plugin/orzmc/infra/config/`、`src/main/resources/config.yml` | 参考类型化配置、ConfigPath、升级和健康检查思想 | 不存在顶层 `configs/` 包；配置模型需按模板重新设计 |
| 命令 | `src/main/java/com/jokerhub/paper/plugin/orzmc/assembly/FeatureCommandRegistrar.java`、`CommandGroup.java` | 参考 Paper LifecycleEvents + Brigadier 注册编排 | 不复制 OrzMC 命令树、权限节点或拦截器业务规则 |
| 事件 | `src/main/java/com/jokerhub/paper/plugin/orzmc/events/`、`infra/binding/EventBinder.java` | 参考 listener 组织与注册边界 | listener 必须有生命周期注销策略 |
| 调度异常处理 | `src/main/java/com/jokerhub/paper/plugin/orzmc/infra/scheduler/SafeScheduler.java`、`Schedulers.java` | 仅参考异常捕获和 facade 的经验 | 不作为 Folia scheduler 实现参考；其底层端口仍是通用 sync/async/later |
| 测试 | `src/test/`、`src/integrationTest/` | 参考 JUnit/Mockito/MockBukkit 分层 | 规模和覆盖率门槛按新插件实际复杂度设定 |
| 质量计划 | `docs/quality-testing-plan.md` | 参考测试金字塔、真实证据要求 | 不复制业务领域覆盖率指标 |
| CI / E2E | `.github/workflows/build.yml`、`.github/workflows/nightly.yml`、`e2e/`、Gradle `e2eLocal*` / `foliaSmoke` tasks | 提供可选真实服务端 smoke preset | 默认模板只保留低成本构建/测试；玩家 E2E 和夜间质量闭环按需启用 |

OrzMCPlugin 当前 `build.gradle.kts` 以 `orzmc-api` 为项目依赖，并使用 Paper API、LuckPerms compileOnly、JUnit、MockBukkit 等依赖。它的 `paper-plugin.yml` 位于 `src/main/resources/paper-plugin.yml`，命令通过 `LifecycleEvents.COMMANDS` + Brigadier 注册。

## 3. 许可证与代码来源约束

- RealTime 仓库根目录为 MIT License。
- OrzMCPlugin 仓库根目录为 GNU GPL v3。
- **本方案和源文件映射不构成复制授权，也不表示模板代码已经抽取。**
- 若模板直接复制或改写 OrzMCPlugin 的 GPL-3.0 代码，模板及其分发必须按 GPL-3.0 义务处理，不能在未审查前默认采用 MIT。
- 建议 P1 优先采用“参考架构、独立实现”的方式；在许可证决策明确前，不复制 OrzMCPlugin 的实现代码。若未来确需复用其代码，先由维护者确认目标许可证与分发策略。
- RealTime 的 MIT 代码可在遵守 MIT 版权和许可声明条件下复用；每个复制文件仍需登记来源和保留声明。

## 4. 抽取前必须重新验证

1. 对两个仓库锁定确切 commit SHA；不要把文件 blob SHA 当成 commit SHA。
2. 检查目标文件当前内容、依赖、许可证、打包方式和运行时提供者。
3. 不把内部类名直接升级为模板公共 API。
4. Paper/Folia API 必须对照目标版本官方文档并在目标服务端编译/运行验证。
5. 组织名、作者、包名、命令、权限、URL、平台 ID、版本号必须参数化。
6. 不把 RealTime updater、设备管理、OrzMCPlugin 通知/IM/网络客户端作为通用基础设施。
7. 源项目只读；任何源项目改造需求必须另行提交理由和影响评估，获得维护者明确批准后才能实施。

## 5. P1 抽取登记要求

每个实际复制/改写的文件都要登记：

- 来源仓库、ref、commit SHA、源路径；
- 目标模板路径；
- 复制、改写、独立实现还是仅参考；
- 是否含产品专属逻辑；
- 许可证及保留声明要求；
- 依赖与打包方式；
- 对应测试；
- 复核人和复核日期。
