# GitHub Actions 真实 Paper 服务器冒烟测试设计

> 状态：P2.0 设计基线；尚未启用自动服务器验收
> 最后更新：2026-11-27
> 范围：仅验证由当前 PR 构建的插件；不连接 OrzMC 家庭服务器或任何生产实例。

## 1. 结论

GitHub Actions 可以承担模板的真实 Paper 服务器冒烟验收。推荐使用 GitHub-hosted Ubuntu runner 启动一次性的 Paper 进程，在 runner 本机安装当前构建的插件 JAR，通过标准输入向控制台发送命令，再检查日志和进程退出状态。

这不需要开放 Minecraft 端口、配置 RCON、连接家庭网络或使用长期运行的自托管 runner。每次 job 使用独立 runner，job 结束后环境销毁。

## 2. 测试分层

| 车道 | 触发时机 | 验证内容 | 是否阻断 PR |
|---|---|---|---|
| Build & unit | 每次 PR / push | Gradle clean check build、单元测试、JAR inspection | 是 |
| Paper smoke | EULA 门禁开启后，每次 PR | 下载固定 Paper 版本、启动插件、执行命令、正常关闭 | 是（启用后） |
| Nightly compatibility | 每晚 | 同一 Minecraft 版本最新 STABLE Paper build，发现 API/运行时漂移 | 否，失败告警 |
| Manual smoke | workflow_dispatch | 指定受支持的 Paper 版本/build，复现问题 | 否 |

PR 车道应使用固定的 Paper 26.3 build 263 和已知 SHA-256，以保证可复现；Nightly 车道可查询 PaperMC Fill API v3，选择 26.3 的最新 STABLE build，并记录实际 build 与校验和。不要使用已退役的 PaperMC API v2。

## 3. 下载与完整性验证

使用 PaperMC 官方 Downloads Service（Fill API v3）：

1. 请求 `https://fill.papermc.io/v3/projects/paper/versions/26.3/builds`。
2. 使用明确标识项目和联系页面的 User-Agent。
3. 从 JSON 中选取指定 build，读取 `downloads."server:default".url` 与 `checksums.sha256`。
4. 通过 HTTPS 下载，使用 `sha256sum -c` 验证后才启动。
5. 把版本、build、下载 URL、SHA-256 记入测试摘要。

禁止构造旧式 `api.papermc.io/v2` 下载 URL；v2 已退役。官方说明见 [PaperMC Downloads Service](https://docs.papermc.io/misc/downloads-service/)。

## 4. 服务器启动与命令驱动

建议的 runner 工作目录：

```text
$RUNNER_TEMP/paper-smoke/
├── paper.jar
├── eula.txt
├── server.properties
├── plugins/
│   └── <current-build>.jar
└── logs/
    └── server.log
```

执行步骤：

1. 创建全新临时目录，设置独立随机端口或关闭 query/RCON；不需要对 runner 外部开放端口。
2. 将待测 JAR 复制到临时目录的 `plugins/`。
3. 使用 JDK 25 启动 Paper，重定向标准输出/错误到日志。
4. 通过 FIFO/标准输入向服务端控制台发送 `template`，检查预期命令响应。
5. 发送 `stop`，等待 JVM 正常退出；超时则收集日志并终止进程。
6. 检查启动、命令、插件 disable 日志和退出码。
7. 无论成功失败都上传日志、版本信息和 JAR SHA-256；清理临时目录。

**不需要 RCON**：服务端与测试脚本运行在同一 runner，标准输入比开放远程控制端口更简单且攻击面更小。若未来需要真实玩家协议交互，再单独评估 Mineflayer 或 RCON。

## 5. Minecraft EULA 门禁

CI 不得静默替维护者接受 Minecraft EULA，也不得在仓库中直接默认写入 `eula=true`。

推荐门禁：

- workflow 仅在仓库变量 `MINECRAFT_EULA_ACCEPTED=true` 时执行 Paper smoke。
- 该变量必须由仓库维护者在阅读并接受 Minecraft EULA 后手动设置。
- 未设置时 smoke job 显示为 skipped；Build & unit 仍正常运行。
- workflow 日志不得把 skipped 描述为 smoke passed。
- 对 fork PR 不使用 `pull_request_target`，不向不可信代码提供任何 secrets。

这将“构建验证”和“需要 EULA 的真实服务器验证”分开，避免自动化绕过许可确认。

## 6. GitHub Actions 安全与稳定性

- 使用 GitHub-hosted runner（Ubuntu），不使用自托管 runner，也不触碰家庭服务器。
- workflow 使用 `pull_request`，不使用 `pull_request_target` 执行 PR 代码。
- 权限默认 `contents: read`；不需要 PAT、部署密钥、RCON 密码或发布 Token。
- 固定 Paper build 的 PR smoke 与 nightly latest-stable 分开，避免 PR 因上游新 build 漂移而不稳定。
- 设置 job timeout；启动等待使用有上限的轮询，不使用无限等待。
- 使用 trap 保证尽力发送 stop；即使失败也上传日志。
- 不上传整个 runner 环境或配置，只上传脱敏后的 server log、构建产物和测试摘要。
- 失败日志中避免打印环境变量、Token 或 runner 私有信息。

## 7. 后续扩展

- P2 Scheduler 完成后，新增独立 Folia smoke job；Paper 通过不能代替 Folia 证据。
- 只有真实 Folia smoke、线程访问审查、任务取消和关闭测试全部通过，才允许声明 `folia-supported: true`。
- MockBukkit 用于快速验证插件装配/命令/事件；不能替代真实 Paper/Folia 进程验收。
- 若某个新插件需要真实玩家登录、区块交互或多客户端协作，再按需添加 Mineflayer E2E；模板默认不引入。

## 8. 当前落地状态

- [x] P1 本地 Paper 26.3 build 263 验收通过。
- [x] 现有 GitHub Actions 执行 JDK 25 构建、JUnit 与 JAR inspection。
- [ ] 实现可复用的 `scripts/smoke-paper.sh`。
- [ ] 增加受 EULA 门禁控制的 Paper smoke workflow job。
- [ ] 增加 nightly latest-stable 兼容性 job。
- [ ] 观察至少 3 次成功运行和 1 次可控失败，确认日志、超时、清理与 artifact 行为。
