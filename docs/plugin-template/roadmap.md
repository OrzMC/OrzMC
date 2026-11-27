# PluginTemplate 实施路线与验收标准

> 状态：P0 源码审计完成；P1 最小工程已建立，CI/真实服验收进行中
> 最后更新：2026-11-27

## 阶段总览

| 阶段 | 范围 | 主要交付 | 退出条件 |
|---|---|---|---|
| P0 | 调研与架构决策 | 架构、能力矩阵、源码映射、决策记录 | 关键设计决策评审完成 |
| P1 | 模板仓库与最小工程 | 独立仓库、Gradle wrapper、Core/Paper 模块、最小插件、README/AGENTS | 全新 clone 可构建；Paper 启动并加载 |
| P2 | 通用运行时基础设施 | 生命周期、组合根、配置、命令、权限、事件、调度、日志、诊断 | 模块测试通过；Paper/Folia smoke 通过后才声明对应支持 |
| P3 | 研发质量体系 | JUnit、MockBukkit、真实服 smoke、CI、secret scan、JAR inspection | PR 门禁可在新仓库/fork 运行 |
| P4 | 发布与初始化 | GitHub Release、可选 Hangar/Modrinth、init-project 工具 | 初始化后无残留占位符 |
| P5 | 模板升级与真实验证 | manifest、upgrade notes、迁移检查；以 RealTime 作为只读兼容性评估对象 | 可生成新项目并在隔离分支演练升级 |

## P0 已完成

- [x] 对比 RealTime 和 OrzMCPlugin 的工程结构、测试、CI、发布和 Agent 实践。
- [x] 归纳模板核心、可选能力和不抽取的业务代码。
- [x] 建立目标模块结构与线程模型边界。
- [x] 核对关键源文件路径、Gradle 配置、插件元数据、调度器、生命周期、测试策略和许可证。
- [x] 记录源文件复用边界与许可证约束。
- [x] 建立 P0 决策记录（Java preset、Folia 门槛、生命周期、命令、许可证、不过早拆 SDK）。
- [ ] 维护者评审并确认 P0 决策。
- [x] 维护者创建独立 `OrzMC/PluginTemplate` 仓库。

## P1 验收清单

- [ ] 新仓库在无本地缓存环境执行 `./gradlew clean check build` 成功。
- [ ] Paper 测试服务器启动，插件被加载，默认命令可用。
- [ ] 插件禁用和服务端关闭时无遗留任务/监听器/线程。
- [ ] 默认 JAR 只包含预期依赖，不打包 Paper API 或可选插件 API。
- [ ] 模板中无 OrzMCPlugin/RealTime 业务命令、包名、权限、数据文件或生产地址。
- [ ] README 清楚说明初始化、构建、测试、发布和支持范围。
- [ ] 由维护者确认模板仓库 LICENSE。

## P2 验收清单

- [ ] 生命周期启动失败回滚、逆序关闭、stop 幂等和异常隔离测试通过。
- [ ] 配置首次生成、非法值诊断、热重载失败保护和 schema 迁移测试通过。
- [ ] 命令权限、参数、Tab 补全和执行上下文测试通过。
- [ ] Scheduler global/region/entity/async 路由有 fake 测试。
- [ ] Folia 真实服 smoke 证明无启动异常及线程模型违规。
- [ ] 只有 P2 Folia 证据全部通过，才允许设置 `folia-supported: true`。
- [ ] optional integration 缺失时不会阻断插件启动。

## P3 验收清单

- [ ] PR workflow 仅有必要的只读权限。
- [ ] secret scan 对常见 token/private key 样式有正反例。
- [ ] JAR inspection 检查元数据、主类、依赖和重复类。
- [ ] CI 测试产物和失败日志可下载。
- [ ] Nightly 任务与 PR 快速门禁分离。
- [ ] workflow 不依赖只有 OrzMC 组织才有的 secret、环境或第三方 App。

## P4 验收清单

- [ ] 初始化工具支持项目名、包名、作者、命令根节点、权限前缀和平台版本。
- [ ] 重命名覆盖源码目录、资源文件、Gradle 坐标、README、工作流和 Agent 身份。
- [ ] 支持 dry-run，显示变更文件和残留占位符。
- [ ] 初始化完成后自动执行验证。
- [ ] GitHub Release 默认可用；Hangar/Modrinth 未配置时明确跳过。

## P5 验收清单

- [ ] manifest 记录模板版本、模块开关、语言 preset、平台和 API 版本。
- [ ] 升级工具先生成计划/PR，不直接覆盖项目工作区。
- [ ] 冲突文件标记为人工处理，不静默覆盖。
- [ ] 至少在一个从模板创建的测试插件中完成升级演练。
- [ ] RealTime 只作为只读兼容性评估对象；任何迁移/改造均需单独批准。

## 风险与缓解

| 风险 | 缓解 |
|---|---|
| 模板过重 | 最小默认配置；可选 preset 延迟加载 |
| Paper/Folia API 演进 | 版本集中管理；CI 固定支持矩阵；升级时复测 |
| 过早抽 SDK | 先模板内复用；两个以上真实项目证明稳定后再外提 |
| Java/Kotlin 双维护成本 | 先 Java baseline；Kotlin preset 后续独立验证 |
| GPL 源码复用导致许可证义务 | P1 前明确模板许可证；默认不复制 GPL 源码 |
| 模板升级覆盖业务代码 | 只生成升级 PR；冲突文件人工处理 |
| AI Agent 并发冲突 | 独立 Worktree + 文件所有权 + PR 审查 |
| 发布凭据泄露 | PR 不注入 secret；受保护 Environment + 最小权限 |
| 误宣称 Folia 兼容 | 元数据声明必须以真实 Folia smoke 和线程安全审查为前提 |
