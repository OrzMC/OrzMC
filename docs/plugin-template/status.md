# PluginTemplate 推进状态

> 更新时间：2026-11-27
> 代码仓库：[OrzMC/PluginTemplate](https://github.com/OrzMC/PluginTemplate)
> 父仓库集成路径：`tools/PluginTemplate`
> 当前子仓库 main：`bd9f4a2`

## 已完成

| 阶段 | 内容 | 证据 |
|---|---|---|
| P0 | 架构/能力审计、边界与路线 | 父仓库 docs/plugin-template |
| P1 | Java 25、Gradle 多模块、Paper plugin.yml、命令、基础生命周期 | 子仓库 real-server-acceptance：Paper 26.3 build 263 |
| P2.0 | Runtime 架构设计 | 子仓库 PR #3 |
| P2.1 | ResourceScope、模块资源逆序清理、启动失败回滚 | 子仓库 PR #4、CI Run #41 |
| P2.2 | Typed config、校验、schema v0→v1 migration、Paper YAML adapter、事务式加载/reload | [子仓库 PR #6](https://github.com/OrzMC/PluginTemplate/pull/6)，CI Run #45，merge `a21fe30` |
| P2.3 | Paper listener ownership、权限节点、`/template reload` | [子仓库 PR #8](https://github.com/OrzMC/PluginTemplate/pull/8)，CI Run #49，merge `43dffe3` |
| P2.4 | Paper 主线程/异步 one-shot scheduler、TaskHandle 状态机、ResourceScope 自动取消 | [子仓库 PR #9](https://github.com/OrzMC/PluginTemplate/pull/9)，CI Run #53，merge `9c593fe` |
| P3.0 | 固定 Paper smoke runner、EULA 门禁和 CI job | [子仓库 PR #10](https://github.com/OrzMC/PluginTemplate/pull/10)，CI Run #56 build/JUnit/JAR/script syntax 全部通过；Paper smoke 因授权变量未设置而 skipped |
| P3.1 | Paper `--help` 有界探测、Java/启动参数/网络隔离配置写入验收报告 | [子仓库 PR #11](https://github.com/OrzMC/PluginTemplate/pull/11)，CI Run #58 success；Paper smoke 仍因 EULA 授权变量未设置而 skipped |

## 当前配置约定

- Core 仅依赖普通 Java 类型与 `Map<String,Object>`；不引用 Bukkit/Paper。
- Paper adapter 负责 YAML 读写、迁移备份与原子文件替换。
- schema 当前为 v1：`enabled`、`message`。
- reload 校验或持久化失败时不发布候选配置，active settings 保持不变。
- 未知 key 输出 warning；未来 schema version 拒绝加载。
- `ConfigService` 提供显式 reload API，并由 `/template reload` 使用；不做文件监听。

## Scheduler 边界

- Paper adapter 只提供主线程和 async one-shot 调度。
- 异步任务不得访问 Bukkit/Paper 世界、实体、背包或其他服务端状态。
- 待执行任务注册到所属模块 ResourceScope，模块停止时取消。
- 不模拟 region/entity scheduler，不声明 Folia 支持。

## EULA 自动化

Minecraft Java/Paper 没有标准 `--accept-eula` 启动参数。维护者一次性阅读并接受 EULA 后，在 GitHub 仓库 Variables 设置 `MINECRAFT_EULA_ACCEPTED=true`。之后每次 CI 启动临时 Paper 前都会自动生成 `eula.txt`（`eula=true`），无需逐次人工处理。变量缺失或不是 `true` 时 Paper smoke 必须 skipped，普通构建和单元测试照常执行。

## 下一步

1. 维护者完成一次 EULA 阅读/接受并设置 `MINECRAFT_EULA_ACCEPTED=true`，触发首轮真实 Paper smoke；检查报告和日志。
2. 完成至少 3 次成功运行和 1 次可控失败，确认 Paper `--help` 探测、启动超时、进程清理、失败报告与 artifact 上传。
3. 增加 nightly latest STABLE Paper 兼容性检查。
4. 之后再评估 P2.5 Folia adapter；必须有独立的 global/region/entity/async 实现、线程安全审查和真实 Folia smoke。

## 不变约束

- 不修改 `OrzMC/RealTime`、`OrzMC/OrzMCPlugin`。
- 不连接或修改生产服务器。
- PR CI 通过后可合并；不得把未实际运行的测试标记为通过。
