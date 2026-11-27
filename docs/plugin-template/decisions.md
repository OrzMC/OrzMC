# PluginTemplate P0 决策记录

> 状态：建议稿，待维护者评审
> 日期：2026-11-27
> 范围：只决定新模板的设计；不授权修改 RealTime 或 OrzMCPlugin。

## ADR-001：首个 preset 使用 Java

**建议：** 首版只维护 Java 业务代码 preset；Gradle 仍使用 Kotlin DSL，JDK toolchain 默认 25。Kotlin preset 延后到 Java 模板稳定后单独验证。

**依据：**
- OrzMCPlugin 的主体是 Java，具备更丰富的 Paper 插件装配、配置、测试和 CI 经验。
- RealTime 是 Kotlin 多模块工程；若首版同时维护两套语言，会增加模板生成、重命名、CI、测试和升级的组合复杂度。
- Gradle Kotlin DSL 与业务源码语言独立，不需要为了使用 Kotlin DSL 引入 Kotlin runtime。

**不做：** 不把两个项目混成 Java/Kotlin 混合模板。

## ADR-002：Folia 支持必须分阶段开放

**建议：**
- P1 最小模板先保证 Paper 可构建、可启动；在没有 Folia 运行证据前，插件元数据不得声明 Folia 支持。
- P2 独立实现 global / region / entity / async 调度适配、任务所有权与取消，并加入真实 Folia smoke。
- 只有 Folia smoke、线程访问审查和关闭/取消测试全部通过后，才将 `folia-supported: true` 纳入默认模板。

**依据：**
- RealTime 的 `PaperFoliaScheduler` 明确实现 global、region、entity 调度和任务注册，但没有提供通用 async 入口；模板仍需补齐异步边界。
- OrzMCPlugin 的 `SafeScheduler` 包装的是通用 sync/async/later 端口，重点是异常捕获，不能作为 Folia 区域线程安全的充分证据。
- Folia 支持元数据是兼容承诺，不应先于实现和真实验证。

## ADR-003：生命周期契约采用统一 start/stop 语义

**建议：** 模板内部采用 `PluginModule.start()/stop()`（或同义命名，但只保留一套），由组合根按依赖顺序启动、逆序停止。

**必须保证：**
- 启动失败时回滚所有已成功启动的模块；
- 关闭过程逐模块隔离异常，某个 stop 失败不能跳过其他模块；
- 任务、监听器、命令注册句柄和资源由模块持有；
- 部分启动状态下调用 stop 安全；
- stop 幂等，日志中能看出启动失败和清理失败。

**依据：** OrzMCPlugin 的显式组合根和模块契约值得借鉴；但当前入口在 assemble 失败时无法持有完整 services，模板应补强失败回滚，而不是照搬现状。

## ADR-004：命令采用 Paper LifecycleEvents + Brigadier

**建议：** 首版采用传统 `plugin.yml` + 主类 Lifecycle API + Brigadier。Paper 官方将 Paper plugin loader 标记为 Experimental，且当前项目搭建指南暂不推荐新项目默认使用；普通 `JavaPlugin` 主类同样可注册 LifecycleEvents 命令。未来可把 `paper-plugin.yml` 作为独立 preset，在真实兼容性验证后再加入。

**约束：** P1 先只提供一个可运行的示例根命令；不复制 OrzMC 的命令注册器、命令树和权限定义。Paper API 版本升级时必须跑编译和真实服务端 smoke。

## ADR-005：优先独立实现，必要时请求复用授权

**维护者授权说明：** RealTime 与 OrzMCPlugin 均由维护者拥有，维护者可以授权代码复用；许可证不作为架构抽取的先决阻碍。

**实现策略：** 默认独立设计和实现，不为追求速度直接复制现有代码。若确实存在值得复用的实现，先列明源文件、复用范围、必要性、替代方案及目标许可证/声明影响，再向维护者请求明确授权。未获得授权前不复制。模板仓库自身 LICENSE 仍由维护者决定。

## ADR-006：第一版不拆 SDK / Build Logic 仓库

**建议：** Core/Paper 模块、构建约定和脚本先放在模板仓库内。至少有两个独立插件实际复用并证明接口稳定后，再评估抽出 SDK 或 Gradle Convention Plugin。

## 维护边界

本决策记录只针对新模板。审计发现源项目可改进之处时，先写明问题、证据、理由、影响、替代方案和不改造的后果，提交维护者审查；未获明确批准，不对 RealTime 或 OrzMCPlugin 执行任何修改。
