# PluginTemplate 实施路线与验收标准

> 状态：P0 路线草案
> 最后更新：2026-11-27

## 阶段总览

| 阶段 | 范围 | 主要交付 | 退出条件 |
|---|---|---|---|
| P0 | 调研与架构决策 | 本目录四份方案、源文件映射、决策清单 | 关键设计决策评审完成 |
| P1 | 模板仓库与最小工程 | 独立仓库、Gradle wrapper、Core/Paper 模块、最小插件、README/AGENTS | 全新 clone 可构建；本地 Paper 启动并加载 |
| P2 | 通用运行时基础设施 | 生命周期、组合根、配置、命令、权限、事件、调度、日志、诊断 | 每个模块有单测/集成测试；Paper/Folia smoke 通过 |
| P3 | 研发质量体系 | JUnit、MockBukkit、真实服 smoke、CI、secret scan、JAR inspection | PR 必需门禁可在空白 fork/新仓库运行 |
| P4 | 发布与初始化 | GitHub Release、可选 Hangar/Modrinth、init-project 工具 | 初始化后包名/插件名/权限/命令/README/CI 无残留占位符 |
| P5 | 模板升级与真实验证 | manifest、upgrade notes、迁移检查；用 RealTime 作为验证对象 | 能生成新项目；能在隔离分支升级；不覆盖业务代码 |

## P0 验收清单

- [x] 已对比 RealTime 和 OrzMCPlugin 的工程结构、测试、CI 和发布实践。
- [x] 已归纳模板核心、可选能力和明确不抽取的业务代码。
- [x] 已形成目标模块结构和 Paper/Folia 运行时边界。
- [x] 已建立源文件映射初稿。
- [ ] 逐文件确认所有候选实现与当前 ref/commit。
- [ ] 确认 Java/Kotlin preset 策略。
- [ ] 确认 Paper/Folia 支持声明与验收门槛。
- [ ] 评审配置 API、命令 API、Gradle included build 决策。
- [ ] 维护者确认后创建独立模板仓库。

## P1 验收清单

- [ ] 新仓库在没有本地缓存的环境中执行 `./gradlew clean check build` 成功。
- [ ] Paper 测试服务器启动，插件被加载，默认命令可用。
- [ ] 插件禁用和服务端关闭时无遗留任务/监听器/线程。
- [ ] 默认 JAR 只包含预期依赖，不打包 Paper API 或可选插件 API。
- [ ] 模板中无 OrzMCPlugin/RealTime 的业务命令、包名、权限、数据文件或生产地址。
- [ ] README 清楚说明初始化、构建、测试、发布和支持范围。

## P2 验收清单

- [ ] 生命周期启动失败回滚和逆序关闭测试通过。
- [ ] 配置首次生成、非法值诊断、热重载失败保护和 schema 迁移测试通过。
- [ ] 命令权限、参数、Tab 补全和执行上下文测试通过。
- [ ] Scheduler global/region/entity/async 路由有 fake 测试。
- [ ] Folia 真实服 smoke 证明无启动异常及线程模型违规。
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
- [ ] RealTime 只作为兼容性验证对象；未评估迁移成本前不做全量重构。

## 风险与缓解

| 风险 | 缓解 |
|---|---|
| 模板过重 | 最小默认配置；可选 preset 延迟加载 |
| Paper/Folia API 演进 | 版本集中管理；CI 固定支持矩阵；升级时复测 |
| 过早抽 SDK | 先模板内复用；两个以上真实项目证明稳定后再外提 |
| Java/Kotlin 双维护成本 | 先 Java baseline；Kotlin preset 作为后续独立验证 |
| 模板升级覆盖业务代码 | 只生成升级 PR；冲突文件人工处理 |
| AI Agent 并发冲突 | 独立 Worktree + 文件所有权 + PR 审查 |
| 发布凭据泄露 | PR 不注入 secret；受保护 Environment + 最小权限 |
| 误宣称 Folia 兼容 | 元数据声明必须以真实 Folia smoke 和线程安全审查为前提 |
