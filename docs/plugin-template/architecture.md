# PluginTemplate 架构设计

> 状态：P0 设计稿（待评审）
> 最后更新：2026-11-27

## 1. 设计原则

1. **业务代码不依赖 Paper API**：纯业务规则尽量放入 Core，可脱离服务端测试。
2. **平台 API 只能从 Adapter 进入**：Bukkit/Paper/Folia 对象不得穿过平台边界进入 Core。
3. **组合根显式装配**：依赖关系在一个地方可见，不使用隐式扫描或重量级 DI。
4. **生命周期成对管理**：注册的 Listener、Task、Command、资源句柄都必须有清理路径。
5. **Folia 安全优先于 Paper 便利性**：每项调度都表达所属线程/区域语义，禁止把「异步」当作通用解决方案。
6. **最小默认依赖**：模板生成的示例插件不依赖第三方插件，不包含网络更新器、数据库或消息平台。
7. **按需启用**：可选能力独立模块化，关闭时不影响插件启动。
8. **可测试、可诊断、可交接**：关键行为有测试，运行状态可诊断，Agent 可按文档继续工作。

## 2. Gradle 模块建议

第一版最小模块：

```text
plugin-template/
├── plugin-core/             # 纯 JVM 领域模型、用例、端口
├── plugin-paper/            # 插件入口、Paper 适配器、默认功能示例
├── plugin-testing/          # 测试辅助；仅在确有跨模块复用时启用
├── docs/
├── scripts/
├── .github/
└── ...
```

依赖方向：

```text
plugin-paper ───────► plugin-core
     │                     ▲
     ├──► Paper API         │
     └──► adapters ─────────┘

optional integrations ─► core ports / platform adapter contracts
tests ─────────────────► modules under test
```

说明：

- `plugin-core` 不得依赖 Bukkit、Paper、Folia、MockBukkit。
- `plugin-paper` 实现 Core 定义的端口，并负责插件元数据、命令、事件和调度适配。
- 可选集成（例如 PlaceholderAPI）采用独立 Gradle 子模块或明确隔离的 source set；不在默认产物中引入无用 API。
- `plugin-testing` 不应为了抽象而存在。若测试辅助只有少量 fixture，先放在测试源码集；跨插件/模块确有复用再抽模块。
- 首版不单独建立 SDK 仓库，也不引入 Gradle Convention Plugin 独立仓库。

## 3. 运行时装配与生命周期

建议的调用链：

```text
JavaPlugin.onEnable
  └── PluginBootstrap.create(plugin)
        ├── load and validate configuration
        ├── construct infrastructure adapters
        ├── construct feature modules
        ├── register commands and listeners
        └── start modules in dependency order

JavaPlugin.onDisable
  └── PluginApplication.stop()
        ├── stop accepting new work
        ├── cancel owned tasks
        ├── unregister listeners / close resources
        └── stop modules in reverse dependency order
```

接口命名可采用 `PluginModule.start()/stop()`，或沿用 OrzMCPlugin 的 `ServiceModule.setup()/tearDown()`。P1 实现前必须选定一套，避免双重生命周期协议。

必须覆盖：

- 某模块初始化失败时，已成功启动模块按逆序回滚；
- `onDisable` 可重复调用或在部分初始化后安全执行；
- 任务、监听器和资源句柄由创建它们的模块持有；
- 关闭阶段不能因一个模块失败而跳过其余模块清理；
- 关闭过程有结构化日志和失败摘要。

## 4. Core / Ports / Adapters

建议核心包：

```text
plugin-core/
└── src/main/java/<package>/core/
    ├── model/
    ├── usecase/
    ├── ports/
    └── validation/
```

平台实现：

```text
plugin-paper/
└── src/main/java/<package>/paper/
    ├── bootstrap/
    ├── commands/
    ├── events/
    ├── scheduler/
    ├── config/
    ├── logging/
    ├── storage/
    └── integrations/
```

边界约束：

- Core 接口使用 Java 类型、`java.time`、`CompletableFuture` 等平台无关类型。
- 不把 `Player`、`World`、`Location`、`Block`、`CommandSender` 放进 Core API。
- 需要玩家或世界操作时，定义窄接口端口，在 Paper Adapter 中实现。
- 异步任务结果若需要向玩家回消息，必须通过拥有者调度接口回到正确的 Entity/Region 上下文。

## 5. Folia 调度抽象

不能只提供一个含糊的 `runSync`。建议显式表达：

| 调度能力 | 适用语义 | 约束 |
|---|---|---|
| Global | 全服级状态、全局协调 | 不用于直接访问任意 Region-owned 世界对象 |
| Region | 指定位置/区块所属区域的操作 | 必须以世界和位置定位，不跨区域持有对象 |
| Entity | 指定实体所属区域的操作 | 实体迁移后遵循实体调度器语义 |
| Async | 网络、文件、纯计算 | 不直接访问 Bukkit/Paper 世界对象 |
| Owned task | 任务注册、取消、关闭时清理 | 任务所有权必须明确 |

模板应提供 Paper 与 Folia 的平台实现，并通过平台能力检测或构建/运行配置选择正确实现。禁止将 Folia 仅作为 `paper-plugin.yml` 的布尔声明。

首版最小要求：

- Scheduler API 对 Core 暴露窄接口；
- 每个调度方法在文档中说明线程/区域语义；
- 提供 task registry；
- 统一异常捕获与日志；
- 提供 fake scheduler 单元测试；
- 真实 Paper/Folia smoke 验证插件能加载、注册命令并干净关闭。

## 6. 配置与数据

默认目录：

```text
plugins/<PluginName>/
├── config.yml             # 稳定的全局配置入口
├── modules/               # 功能模块配置
├── messages/              # 可选：消息/语言文件
└── data/                  # 程序持久化数据，不与用户配置混用
```

配置服务职责：

- 默认资源复制和首次生成；
- 结构解析与类型化映射；
- 字段范围、枚举和跨字段校验；
- 未知字段/拼写错误策略；
- 版本号与迁移链；
- 热重载前先解析和校验，成功后原子替换运行配置；
- 写入采用临时文件 + 原子移动（文件系统支持时）；
- 诊断报告指出文件、路径、错误和建议；
- 用户配置与程序状态数据分开。

默认不强制 YAML 数据库化。复杂数据可通过 Storage Port 选择 YAML/SQLite/外部数据库。

## 7. 命令与事件

- 命令使用 Paper LifecycleEvents / Brigadier 注册适配器。
- 命令定义（参数、权限、执行用例）与 Bukkit 注册细节分离。
- 通用拦截器可提供 Permission、PlayerOnly、ConsoleOnly、Cooldown，但按需启用。
- 根命令、权限前缀和别名来自模板初始化参数，不硬编码为 `/example` 以外的组织标识。
- Listener 必须由模块生命周期持有并可注销。
- 高频事件应评估节流、聚合和线程安全；模板只提供策略接口与示例，不默认实现业务通知。

## 8. 测试结构

| 测试层 | 位置 | 目标 |
|---|---|---|
| Core unit | `plugin-core/src/test` | 领域规则、解析、状态机、迁移 |
| Adapter unit | `plugin-paper/src/test` | 命令解析、配置适配、调度路由、错误处理 |
| MockBukkit integration | `plugin-paper/src/integrationTest` | 插件装配、命令注册、事件监听、生命周期 |
| Runtime smoke | `scripts/smoke-*.sh` + CI | 下载固定版本 Paper/Folia、启动、检查插件加载/命令/关闭 |
| Full E2E | 可选 | Mineflayer、RCON、真实玩家、跨服场景 |

固定时间逻辑使用注入的 `Clock`；测试不得依赖主机当前时间、sleep 或随机时序。测试报告要区分 mock 证据和真实服务端证据。

## 9. 产物与发布

- 单一 shaded JAR，明确哪些依赖打包、哪些由服务端提供。
- 发布前检查 JAR 中的插件元数据、主类、版本、必需资源、重复类和禁止打包的 API。
- 生成 SHA-256。
- GitHub Release 为默认渠道；Hangar / Modrinth 由项目配置启用。
- PR 工作流只读权限，不注入发布 token。
- 发布工作流使用 GitHub Environment 审批和最小权限。
- 缺少外部平台 ID 或 token 时明确 skip，不应误报成功发布。

## 10. Agent Native 结构

```text
AGENTS.md
.agents/
├── policies/
│   ├── architecture.md
│   ├── security.md
│   ├── folia-threading.md
│   └── git-isolation.md
├── roles/
│   ├── architect.md
│   ├── developer.md
│   ├── qa.md
│   └── reviewer.md
└── workflows/
    ├── feature.md
    ├── bugfix.md
    ├── review.md
    └── release.md
```

AGENTS.md 是入口和单一事实源；细则拆分为可按任务读取的文件。模板必须提供独立 Worktree 工作流，但不得让 Agent 自动越权合并 PR、修改生产服务器或发布版本。

## 11. 尚待 P0 评审的决策

- Java 与 Kotlin：第一版是否只发布 Java preset，还是同时维护两个可运行 preset。
- Folia：默认启用 Folia 支持，还是通过初始化选项启用；无 Folia 验收证据时必须禁用元数据声明。
- 配置模型：纯 Java record + SnakeYAML，还是采用 Paper Configuration API 包装；需比较类型安全、迁移成本和依赖。
- 命令 API：是否首版只封装 LifecycleEvents / Brigadier 的最小能力。
- 测试服务端版本：固定版本 vs 最新版本矩阵。
- Gradle Convention Plugin：首版留在根构建脚本，还是直接采用 included build。


## 12. P0 实施门槛（源码审计后补充）

### 12.1 语言与构建

- 首版只生成 Java 业务代码；Gradle 使用 Kotlin DSL，JDK toolchain 默认 25。
- Kotlin preset 延后，不在首版混合 Java/Kotlin 源码。
- 首版只保留 `plugin-core` 与 `plugin-paper` 两个必要模块；测试 fixture 优先留在测试 source set，除非后续证明需要跨项目共享。

### 12.2 Paper 与 Folia 支持声明

- P1 先实现并验证 Paper 最小可运行插件。
- 在 Folia 调度适配、任务取消/所有权、线程访问审查和真实 Folia smoke 全部通过前，元数据不得声明 `folia-supported: true`。
- P2 再实现 global / region / entity / async 的显式调度接口；async 只执行不触碰 Bukkit/Paper 世界对象的工作。
- RealTime 的调度器可作为 global/region/entity 设计参考，但其当前类没有通用 async 入口。
- OrzMCPlugin 的 `SafeScheduler` 主要负责异常包装；其通用 sync/async/later 抽象不能替代 Folia 区域线程模型。

### 12.3 生命周期失败语义

组合根必须记录每个模块的启动状态。启动失败时，仅逆序停止已成功启动的模块；停止阶段逐模块捕获并汇总异常，确保一个模块清理失败不阻断其余模块。入口的 disable 回调必须能处理“尚未完成组装”的状态。

### 12.4 代码来源与许可证

RealTime 为 MIT，OrzMCPlugin 为 GPL-3.0。P1 默认独立实现并参考架构，不直接复制 OrzMCPlugin GPL 源码。若后续要复制或改写其实现，必须先确定模板和衍生项目的许可证/分发策略，并登记来源与声明要求。详见 [P0 决策记录](decisions.md) 与 [源文件映射](source-mapping.md)。

### 12.5 命令与插件元数据

OrzMCPlugin 当前采用 `paper-plugin.yml` 和 `LifecycleEvents.COMMANDS` + Brigadier；RealTime 当前使用传统 `plugin.yml`。模板首版建议采用 Paper plugin loader 路径，但必须针对目标 Paper API 版本编译和真实启动验证，不把两个项目的元数据格式混为一谈。
