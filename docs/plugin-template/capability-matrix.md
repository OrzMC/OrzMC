# PluginTemplate 能力抽取矩阵

> 状态：P0 盘点稿（待源文件复核）
> 最后更新：2026-11-27

## 1. 分类规则

- **模板核心**：新插件默认获得，且不需要第三方服务或凭据。
- **可选能力**：模板提供接入方式或 feature preset，但默认关闭。
- **参考而不复制**：属于特定产品行为，或实现与现有项目强耦合。
- **后续抽 SDK**：至少两个独立插件实际复用同一稳定实现后再评估。

## 2. 能力矩阵

| 能力 | RealTime 证据 | OrzMCPlugin 证据 | 处理结论 |
|---|---|---|---|
| Gradle Wrapper / Kotlin DSL | 根 Gradle、模块 Gradle、wrapper | 根 Gradle、wrapper | 模板核心 |
| JDK Toolchain / 版本集中管理 | `gradle.properties`、Gradle toolchain | `gradle.properties`、`plugin_jdk_min_version` | 模板核心；版本可配置 |
| Core / Platform 分离 | `realtime-core` + `realtime-paper` | `core/ports` + `infra` + `features` | 模板核心 |
| 显式依赖装配 | Paper 模块 bootstrap | `OrzServices.assemble()` | 模板核心 |
| 模块生命周期 | 模块服务及启动/关闭流程 | `ServiceModule`、`setupAll()`、`shutdownAll()` | 模板核心 |
| 配置默认值与加载 | 独立模块 YAML | `configs/` 类型化配置 | 模板核心 |
| 配置校验/健康诊断 | 配置解析、校验、诊断 | ConfigPath、类型化模型、启动健康检查 | 模板核心 |
| 配置迁移 | `devices.yml` schema v1→v3 | guide book 旧格式→新格式迁移 | 模板核心：迁移接口和示例 |
| 配置热重载 | 配置模块/命令路径 | `/orzmc config reload`、缓存失效 | 可选能力，提供安全接口 |
| 命令注册 | `/rtime` 命令实现 | Brigadier + 命令拦截器 | 模板核心 |
| 权限 | 命令权限声明与检查 | Permission 节点及拦截器 | 模板核心 |
| 事件注册 | Paper 事件适配 | `events/` | 模板核心 |
| Scheduler | Paper/Folia global/region/entity/async | `ServerFacade`、SafeScheduler 等 | 模板核心，必须明确线程语义 |
| Task Registry | 任务生命周期管理 | 服务与定时任务管理 | 模板核心 |
| 统一日志与异常处理 | 插件 logger、smoke 日志 | 模块日志、异常告警 | 模板核心 |
| 持久化接口 | 版本化 YAML repository | YAML repository、状态文件 | 模板核心：接口 + YAML adapter |
| MiniMessage / 多语言 | 视项目消息实现 | 消息模板、语言包 | 可选能力 |
| PlaceholderAPI | 内部 expansion | 当前项目可选集成 | 可选能力 |
| LuckPerms | 无需默认集成 | 软依赖 + 异步授权路径 | 可选能力 |
| 自动更新 | RealTime updater（HTTPS、allowlist、大小限制、hash） | 现有插件有发布链但非同一运行时更新实现 | 可选独立 feature；不进入默认模板 |
| Hangar / Modrinth | tag 发布、渠道元数据、页面同步 | beta/release 发布流程 | 可选发布 preset |
| GitHub Release / SHA256 | release workflow、校验和、制品检查 | 发布产物和安全工作流 | 模板核心 |
| JAR 检查 | `inspect-jar.sh` | ShadowJar、插件元数据检查 | 模板核心 |
| 单元测试 | JUnit + 纯 JVM 测试 | JUnit + Mockito | 模板核心 |
| MockBukkit | 适配器测试 | integrationTest + MockBukkit | 模板核心 |
| 真实 Paper/Folia smoke | smoke-server / cleanup / update | foliaSmoke / e2eLocal* | 模板核心入口，默认最小用例 |
| Mineflayer / RCON E2E | RCON smoke scripts | e2e bot + RCON + real player | 可选能力 |
| JaCoCo 覆盖率门禁 | 可选/按模块配置 | JaCoCo + 质量阈值 | 模板核心基础接线；阈值按项目定 |
| Secret scanning | 环境检查/凭据安全约束 | checkSecrets + 历史扫描 | 模板核心 |
| 依赖漂移 | 版本升级和验证 | nightly upstream drift | 可选 nightly 能力 |
| Agent 指南 | `AGENTS.md`、`.agents/`、worktree scripts | `AGENTS.md` 多 Agent 规范 | 模板核心 |
| 任务契约 / 验收标准 | tasks、workflows | feature/task/testing 文档 | 模板核心 |
| ADR | decisions/docs | 架构决策与开发文档 | 模板核心 |
| 模板升级 | 暂无统一机制 | 暂无统一机制 | 新建能力 |
| bStats / metrics | 非默认核心 | 非默认核心 | 可选能力 |
| 数据库 | 无 | 插件具体需求 | 可选能力 |
| 网络客户端 | updater HTTP client | EasyBot WebSocket / GeoIP 等业务客户端 | 不提供通用实现；按需接入 |
| 产品业务 | 现实时间、设备、清理 | 白名单、Bot、portal、TNT、传送弓等 | 不抽取 |

## 3. 抽取优先级

### P1：模板第一版必须有

- 最小多模块 Gradle 工程；
- 插件入口和生命周期；
- 显式组合根；
- Core/Platform 依赖边界；
- 默认配置加载、校验；
- 最小 Brigadier 命令和权限；
- Listener 生命周期管理；
- Paper/Folia 调度接口；
- 统一日志和任务清理；
- JUnit + MockBukkit；
- Paper/Folia 启动冒烟入口；
- CI、密钥扫描、JAR 检查；
- AGENTS.md、Worktree 和 PR 工作流；
- README、开发指南、测试策略、CHANGELOG、SECURITY。

### P2：第一版可选 preset

- 配置热重载；
- 多语言消息；
- PlaceholderAPI；
- LuckPerms；
- Hangar / Modrinth；
- Mineflayer / RCON E2E；
- 自动更新；
- bStats；
- SQLite。

### P3：满足复用证据后再抽取

- Gradle Convention Plugin 独立仓库；
- Plugin SDK；
- 通用消息总线；
- 通用数据库层；
- 通用自动更新器；
- 通用多平台通知系统。

## 4. 重要非目标

不能把 RealTime 的红石设备、时间快照、设备清理服务，或 OrzMCPlugin 的白名单、Bot、portal、TNT、teleport、prison、IM 路由等业务代码复制进模板。

模板可以提供扩展点，但不应预装一个大型业务框架。
