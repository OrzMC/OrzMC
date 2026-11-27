# PluginTemplate 推进状态

> 更新时间：2026-11-27
> 代码仓库：[OrzMC/PluginTemplate](https://github.com/OrzMC/PluginTemplate)
> 父仓库集成路径：`tools/PluginTemplate`

## 已完成

| 阶段 | 内容 | 证据 |
|---|---|---|
| P0 | 架构/能力审计、边界与路线 | 父仓库 docs/plugin-template |
| P1 | Java 25、Gradle 多模块、Paper plugin.yml、命令、基础生命周期 | 子仓库 real-server-acceptance：Paper 26.3 build 263 |
| P2.0 | Runtime 架构设计 | 子仓库 PR #3 |
| P2.1 | ResourceScope、模块资源逆序清理、启动失败回滚 | 子仓库 PR #4、CI Run #41 |
| P2.2 | Typed config、校验、schema v0→v1 migration、Paper YAML adapter、事务式加载/reload | [子仓库 PR #6](https://github.com/OrzMC/PluginTemplate/pull/6)，CI Run #45 success，merge commit `a21fe30` |

## 当前配置约定

- Core 仅依赖普通 Java 类型与 `Map<String,Object>`；不引用 Bukkit/Paper。
- Paper adapter 负责 YAML 读写、迁移备份与原子文件替换。
- schema 当前为 v1：`enabled`、`message`。
- reload 校验或持久化失败时不发布候选配置，active settings 保持不变。
- 未知 key 输出 warning；未来 schema version 拒绝加载。
- 目前提供 ConfigService API；尚未添加玩家/管理员 reload 命令，也不做文件监听。

## EULA 自动化约定

Minecraft Java/Paper 不提供标准 `--accept-eula` 参数。维护者一次性阅读并接受 EULA 后设置仓库变量 `MINECRAFT_EULA_ACCEPTED=true`；workflow 在每次临时服务器启动前自动生成 `eula.txt`，不再要求每次人工处理。未授权时 smoke job 必须 skipped，普通构建和单元测试继续执行。

## 下一步

1. P2.3：Listener ownership + command/permission helpers，确保监听器注册绑定 ResourceScope。
2. P2.4：Paper scheduler adapter；明确 global/region/entity/async 语义，任务句柄归属 ResourceScope。
3. GitHub Actions：实现 Python 驱动的 Paper smoke runner、EULA 门禁 workflow、固定 build PR smoke 和 nightly latest STABLE。
4. Paper smoke 稳定后再考虑 MockBukkit 扩展；Folia 需独立 adapter 和真实服务器证据，未完成前不声明支持。

## 不变约束

- 不修改 `OrzMC/RealTime`、`OrzMC/OrzMCPlugin`。
- 不连接或修改生产服务器。
- PR CI 通过后可合并；不得把未实际运行的测试标记为通过。
