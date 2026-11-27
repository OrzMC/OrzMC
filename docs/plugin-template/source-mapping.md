# PluginTemplate 现有项目源文件映射

> 状态：P0 源文件映射初稿（需在 P1 抽取前逐项复核）
> 最后更新：2026-11-27
>
> 源码仓库：
> - [OrzMC/RealTime](https://github.com/OrzMC/RealTime)（`main`，本轮核对基线：`3395b49d1e7516aab0bb253be1f6fc6fdb248eed`）
> - [OrzMC/OrzMCPlugin](https://github.com/OrzMC/OrzMCPlugin)（`develop`，本轮核对基线：`a045757d92347ee8e60e28815232da4f6f36afc3`；父仓库生产组合指针可能指向 `main`，抽取前必须确认目标 ref）

## 1. RealTime 映射

| 模板能力 | 参考路径 | 复用方式 | 注意事项 |
|---|---|---|---|
| Gradle 多模块 | `settings.gradle.kts`、`build.gradle.kts`、`realtime-core/build.gradle.kts`、`realtime-paper/build.gradle.kts` | 重建最小模块骨架 | 不复制 RealTime 的产品依赖和版本策略 |
| Core 领域边界 | `realtime-core/src/main/kotlin/cn/orzmc/realtime/core/` | 参考纯 JVM 包组织和依赖边界 | Kotlin 实现需转换为 Java preset 或保留 Kotlin preset |
| Paper 入口与适配 | `realtime-paper/src/main/kotlin/cn/orzmc/realtime/paper/` | 参考插件启动、平台适配、命令/事件组织 | 只抽基础设施，不抽时间/设备业务 |
| 插件元数据 | `realtime-paper/src/main/resources/paper-plugin.yml` | 提取最小元数据模板 | name/main/version/api-version/folia-supported 必须由初始化参数生成 |
| 配置分层 | `realtime-paper/src/main/resources/` 中的默认配置与模块配置 | 提取 config/modules/data 分层 | 保留未知字段处理、校验和 schema 迁移策略 |
| Paper/Folia 调度 | `realtime-paper/src/main/kotlin/cn/orzmc/realtime/paper/scheduler/PaperFoliaScheduler.kt`、`TaskHandle.kt`、`TaskRegistry.kt` | 参考 global/region/entity/async 分工、任务所有权和关闭取消 | 不直接复制业务服务中的调度调用；逐项核对 API 和生命周期 |
| 命令目标线程 | `realtime-paper/src/main/kotlin/cn/orzmc/realtime/paper/command/` 下 `CommandTarget` 相关实现 | 参考异步命令结果回到玩家所属 Entity/Region 的模式 | 必须先复核当前文件名和完整调用链 |
| 测试策略 | `docs/testing/strategy.md` | 复用测试层次与真实服证据要求 | 不把 RealTime 特有 smoke 当作通用必需项 |
| 统一验证 | `scripts/verify.sh`、`scripts/test.sh`、`scripts/lint.sh`、`scripts/build.sh` | 重建统一脚本入口 | 删除业务专属 smoke 与发布版本假设 |
| JAR 检查 | `scripts/inspect-jar.sh`、`scripts/distribution-check.sh` | 提取通用检查 | 外部平台字段应可配置 |
| Agent 环境 | `AGENTS.md`、`.agents/`、`scripts/check-agent-environment.sh` | 复用结构和校验思路 | 项目身份、目录和角色内容重新生成 |
| Worktree | `scripts/new-agent-worktree.sh`、`scripts/list-agent-worktrees.sh` | 提取独立工作区流程 | 需要验证在模板新仓库和不同默认分支上可用 |
| 发布 | `.github/workflows/ci.yml`、`.github/workflows/release.yml`、`docs/release/process.md` | 提取最小安全发布链 | 保留 environment approval、最小权限和无凭据跳过 |
| 发布脚本测试 | `scripts/test-release-scripts.sh`、`scripts/validate-release.sh`、`scripts/extract-release-notes.sh` | 抽通用 SemVer/Changelog/制品校验 | 不复制项目专属版本和渠道声明 |

## 2. OrzMCPlugin 映射

| 模板能力 | 参考路径 | 复用方式 | 注意事项 |
|---|---|---|---|
| 插件入口 | `src/main/java/com/jokerhub/paper/plugin/orzmc/OrzMC.java` | 参考 onEnable/onDisable 轻量入口 | 初始化失败与部分启动回滚需加强 |
| 显式组合根 | `src/main/java/com/jokerhub/paper/plugin/orzmc/OrzServices.java`、`assembly/FeatureModule.java`、`assembly/PlatformModule.java` | 抽象 assemble/start/stop 模式和领域模块装配 | 去掉所有 OrzMC 业务依赖 |
| 六边形架构 | `src/main/java/com/jokerhub/paper/plugin/orzmc/core/ports/`、`features/`、`infra/` | 参考 ports/features/adapters 分层 | 只抽依赖规则和最小示例 |
| 模块生命周期 | `ServiceModule` 及 `OrzServices.setupAll()/shutdownAll()` | 提取接口和逆序关闭语义 | 具体源文件需沿目录树定位后复核 |
| 配置 | `src/main/java/com/jokerhub/paper/plugin/orzmc/infra/config/`、`src/main/resources/config.yml` | 参考类型化配置、ConfigPath、ConfigUpgrader 与健康检查 | 不存在顶层 `configs/` 包；配置模型需按模板语言与 Paper API 版本重新实现 |
| 命令 | `src/main/java/.../commands/`、Brigadier 注册相关类 | 提取命令参数、权限、拦截器模式 | 避免复制 OrzMC 命令树 |
| 事件 | `src/main/java/.../events/` | 提取 listener 组织与注册边界 | listener 必须随模块生命周期注销 |
| Folia/线程安全 | `src/main/java/com/jokerhub/paper/plugin/orzmc/infra/scheduler/SafeScheduler.java`、`Schedulers.java`、`core/ports/server/` | 提取线程约束、异步 future 和 owner scheduler 的经验 | 必须避免同步等待 LP future 等特定业务陷阱被误抽成通用逻辑 |
| 测试 | `src/test/`、`src/integrationTest/` | 复用 JUnit/Mockito/MockBukkit 测试分层 | 测试阈值按新插件实际复杂度设定 |
| 质量计划 | `docs/quality-testing-plan.md` | 复用测试金字塔、覆盖矩阵和真实证据规则 | 不复制 16 个业务领域的覆盖率基线 |
| CI | `.github/workflows/build.yml`、`.github/workflows/nightly.yml` | 提取 PR 门禁、Folia smoke、nightly 质量闭环 | OIDC、Codecov、自动 issue 等均为可选配置 |
| 密钥扫描 | Gradle `checkSecrets` task、`scripts/check-secrets.sh` | 提取扫描和提交前门禁 | 不将真实 secret 或平台 ID 写入测试夹具 |
| E2E | `e2e/`、Gradle `e2eLocal*` / `foliaSmoke` tasks | 提供可选真实玩家测试 preset | 默认模板只保留最小 Paper/Folia 启动冒烟 |

## 3. 抽取时必须重新验证的内容

1. 两个仓库当前默认分支和开发分支可能不同；抽取前记录 commit SHA。
2. 现有目录名不等于稳定 API；不能直接将内部类名作为模板公共 API。
3. Paper/Folia API 在 26.x 持续演进；抽取时必须对照当前官方文档与目标 API 版本编译验证。
4. 模板中所有组织名、作者、包名、命令、权限、URL、平台 ID、版本号必须占位化。
5. 第三方依赖的许可证、打包方式和运行时提供者必须逐项检查。
6. 不把 RealTime updater、OrzMCPlugin 的通知/IM/网络客户端直接当作通用基础设施。

## 4. 源码复核输出要求

P1 抽取任务开始前，为每个实际复制/改写的源文件记录：

- 来源仓库、ref、commit SHA、源路径；
- 目标模板路径；
- 选择复制、改写、接口化还是仅参考；
- 是否包含产品专属逻辑；
- 依赖与许可证；
- 对应测试；
- 复核人和复核日期。
