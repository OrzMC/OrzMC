# PluginTemplate 推进状态

> 更新时间：2026-11-27
> 代码仓库：[OrzMC/PluginTemplate](https://github.com/OrzMC/PluginTemplate)
> 父仓库集成路径：`tools/PluginTemplate`
> 当前子仓库 main：`0e46d36`

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
| P3.1 | Paper `--help` 有界探测、Java/启动参数/网络隔离配置写入验收报告 | [子仓库 PR #11](https://github.com/OrzMC/PluginTemplate/pull/11)，CI Run #58 success |
| P3.2 | Paper smoke EULA 双重 fail-closed 门禁：workflow job 与 Python runner 独立校验；报告准确标记 help probe 是否返回 | [子仓库 PR #12](https://github.com/OrzMC/PluginTemplate/pull/12)，CI Run #60 success，merge `6552f12` |
| P3.3 | Paper smoke artifact 仅保留 JSON 报告、server log、server.properties、eula.txt，排除临时世界和缓存 | [子仓库 PR #13](https://github.com/OrzMC/PluginTemplate/pull/13)，CI Run #62 success，artifact 从 217 MB 降至约 5.1 KB，merge `60a3fa4` |
| P3.4 | EULA fail-closed 负向回归测试：未授权时必须抛错，且不得写入 eula/server.properties 或启动 Paper 进程；纳入 CI | [子仓库 PR #14](https://github.com/OrzMC/PluginTemplate/pull/14)，CI Run #64/#65 success，merge `cdb5c41` |
| P3.5 | Daily Paper 26.3 latest-STABLE 兼容性工作流：解析最新 STABLE build、双重校验 SHA-256、EULA 门禁、隔离 smoke 和 evidence artifact | [子仓库 PR #15](https://github.com/OrzMC/PluginTemplate/pull/15)，CI Run #45962506274 success；main CI #45962677819 success，merge `997d68e` |
| P3.6 | 启动超时、命令响应超时、异常进程清理（stop → terminate → kill）回归测试纳入 CI | [子仓库 PR #15](https://github.com/OrzMC/PluginTemplate/pull/15)，CI Run #45962506274 success，merge `997d68e` |
| P3.7 | 更新质量路线、nightly 运维说明和 README；明确首次定时 nightly 运行仍待验证 | [子仓库 PR #16](https://github.com/OrzMC/PluginTemplate/pull/16)，CI Run #45962758422 success，merge `61dba0e` |
| P3.8 | Paper 26.3 MockBukkit listener lifecycle 集成测试；test-only API 版本对齐；skipped tests fail CI；JUnit 报告上传 | [子仓库 PR #17](https://github.com/OrzMC/PluginTemplate/pull/17)，CI #45963729927、main #45963913893 success，merge `3b07b7c` |
| P3.9 | MockBukkit 测试范围、Paper API build 对齐策略及真实 Paper 验收边界文档 | [子仓库 PR #18](https://github.com/OrzMC/PluginTemplate/pull/18)，CI #45963974109 success，merge `6d9a917` |
| P3.10 | Dependabot Gradle/Actions weekly updates、Gradle dependency graph submission workflow、SECURITY.md 和 security 操作指南 | [子仓库 PR #19](https://github.com/OrzMC/PluginTemplate/pull/19)，PR CI #45964267995、main CI #45964427338 success，merge `3911980`；Dependency Submission 因 GitHub Dependency Graph 未启用而失败 |
| P3.11 | CodeQL Java/Kotlin 高级配置：JDK 25 + Gradle manual build，PR/main/weekly 扫描，fork PR 分析与 SARIF 上传权限隔离 | [子仓库 PR #24](https://github.com/OrzMC/PluginTemplate/pull/24)，PR CI #45965508559、CodeQL #45965508460、main CI #45965755540、main CodeQL #45965755620 均 success，merge `d7b8e71`；main SARIF 上传成功 |
| P3.12 | 合并 Dependabot 首批 4 个更新：Actions download-artifact、JUnit、MockBukkit、Gradle Wrapper 9.9.2 | 子仓库 PR #20–#23，四个 PR 的 build 和真实 Paper smoke 均通过 |
| P3.13 | MockBukkit Paper YAML adapter 测试：标量/嵌套 Map/List 往返、时间戳备份、原子替换和临时文件清理；同步 MockBukkit 4.124.0 文档 | [子仓库 PR #25](https://github.com/OrzMC/PluginTemplate/pull/25)，CI #45966575091 build、Paper smoke、CodeQL 均 success；main CI #45966818241、CodeQL #45966817803 success |

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

Minecraft Java/Paper 没有标准 `--accept-eula` 启动参数。维护者已确认阅读并接受 EULA，并已在 OrzMC 组织级 Variables 设置 `MINECRAFT_EULA_ACCEPTED=true`。需确保该组织变量的 Repository access 覆盖 `OrzMC/PluginTemplate`。workflow job 与 `scripts/smoke-paper.py` 在写入 `eula.txt` 前分别执行严格 `true` 校验；任一校验失败都不得启动 Paper。真实 Paper smoke 已连续通过至少 20 次（CI Runs #61–#65、#45962506274、#45962677819、#45962758422、#45963729927、#45963913893、#45964267995、#45964427338）：Paper 26.3 build 263、Java 25、插件启用、`/template`、`/template reload`、干净关闭均通过，Paper 进程退出码为 0。

## 下一步

1. 管理员需在 GitHub Settings → Security & analysis 启用 Dependency graph、Dependabot alerts/security updates，并核对 Secret scanning/push protection；随后重新运行 Dependency Submission workflow。
2. 等待首次 nightly 定时运行（每日北京时间 10:23），验证最新 STABLE build 的解析、校验和真实 smoke 全链路。
3. CodeQL 已合并，PR 和 main 首次扫描均成功，main SARIF 已上传。
4. Paper YAML adapter 已有 MockBukkit 覆盖；继续评估 Paper Lifecycle API/Brigadier 命令可测边界；之后再评估 P2.5 Folia adapter，必须有独立 global/region/entity/async 实现、线程安全审查和真实 Folia smoke。

## 不变约束

- 不修改 `OrzMC/RealTime`、`OrzMC/OrzMCPlugin`。
- 不连接或修改生产服务器。
- PR CI 通过后可合并；不得把未实际运行的测试标记为通过。
