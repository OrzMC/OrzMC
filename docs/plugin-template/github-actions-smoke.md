# GitHub Actions 真实 Paper 服务器冒烟测试设计

> 状态：首轮真实 Paper smoke 已通过（CI Run #61）；EULA 双重门禁与精简 evidence artifact 已落地
> 最后更新：2026-11-27
> 范围：仅验证由当前 PR 构建的插件；不连接 OrzMC 家庭服务器或任何生产实例。

## 1. 结论

GitHub Actions 可以承担模板的真实 Paper 服务器冒烟验收。推荐使用 GitHub-hosted Ubuntu runner 启动一次性的 Paper 进程，在 runner 本机安装当前构建的插件 JAR，通过标准输入向控制台发送命令，再检查日志和进程退出状态。

这不需要开放 Minecraft 端口、配置 RCON、连接家庭网络或使用长期运行的自托管 runner。每次 job 使用独立 runner，job 结束后环境销毁。

## 2. 测试分层

| 车道 | 触发时机 | 验证内容 | 是否阻断 PR |
|---|---|---|---|
| Build & unit | 每次 PR / push | Gradle clean check build、单元测试、JAR inspection | 是 |
| Paper smoke | 一次性 EULA 授权后，每次 PR | 下载固定 Paper 版本、启动插件、执行命令、正常关闭 | 是（启用后） |
| Nightly compatibility | 每晚 | 同一 Minecraft 版本最新 STABLE Paper build，发现 API/运行时漂移 | 否，失败告警 |
| Manual smoke | workflow_dispatch | 指定受支持的 Paper 版本/build，复现问题 | 否 |

PR 车道使用固定 Paper 26.3 build 263 和已知 SHA-256，以保证可复现；Nightly 车道查询 PaperMC Fill API v3，选择 26.3 的最新 STABLE build，并记录实际 build 与校验和。不要使用已退役的 PaperMC API v2。

## 3. 下载与完整性验证

使用 PaperMC 官方 Downloads Service（Fill API v3）：

1. 请求 `https://fill.papermc.io/v3/projects/paper/versions/26.3/builds`。
2. 使用明确标识项目和联系页面的 User-Agent。
3. 从 JSON 中选取指定 build，读取 `downloads."server:default".url` 与 `checksums.sha256`。
4. 通过 HTTPS 下载，使用 `sha256sum -c` 验证后才启动。
5. 把版本、build、下载 URL、SHA-256 记入测试摘要。

禁止构造旧式 `api.papermc.io/v2` 下载 URL；v2 已退役。官方说明见 [PaperMC Downloads Service](https://docs.papermc.io/misc/downloads-service/)。

## 4. 服务器启动与命令驱动

runner 工作目录：

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
3. 在门禁通过后自动生成 `eula.txt`，内容为 `eula=true`。
4. 使用 JDK 25 启动 Paper，重定向标准输出/错误到日志。
5. 由 Python subprocess 管理 Paper 进程，通过 stdin 向控制台发送 `template`，检查预期命令响应。
6. 发送 `stop`，等待 JVM 正常退出；超时则收集日志并终止进程。
7. 检查启动、命令、插件 disable 日志和退出码。
8. 无论成功失败都上传日志、版本信息和 JAR SHA-256；清理临时目录。

**不需要 RCON**：服务端与测试脚本运行在同一 runner，标准输入比开放远程控制端口更简单且攻击面更小。

## 5. Minecraft EULA 门禁

Minecraft Java/Paper 服务端没有标准的 `--accept-eula` 启动参数；实际读取的是服务器工作目录中的 `eula.txt` 文件。自动化可在启动前创建该文件，但不能把技术上的自动写文件误认为已获得法律授权。

采用一次性授权、后续全自动运行的方式：

- 维护者先阅读并接受 [Minecraft EULA](https://www.minecraft.net/eula)。
- 维护者已确认阅读并接受 EULA，并在 OrzMC 组织级 Variables 中设置 `MINECRAFT_EULA_ACCEPTED=true`；CI Run #61 已证实该变量可供 `OrzMC/PluginTemplate` 使用。
- Paper smoke workflow job 检查该变量必须严格等于 `true`；否则 job 显示为 skipped，Build & unit 仍正常运行。
- 门禁通过后，workflow 在临时 runner 目录自动写入 `eula.txt`（`eula=true`），无需每次运行人工处理或交互确认。
- `scripts/smoke-paper.py` 在写入 `eula.txt` 前再次独立检查 `MINECRAFT_EULA_ACCEPTED=true`；脚本被直接调用时也 fail closed。
- workflow 日志明确记录授权门禁结果；不得把 skipped 描述为 smoke passed。
- 对 fork PR 不使用 `pull_request_target`，不向不可信代码提供任何 secrets。

**授权开关是一次性维护者动作，不是每次 CI 的人工步骤。** 如果维护者未接受 EULA，不得通过默认变量、代码常量或 workflow 参数绕过门禁。

## 6. GitHub Actions 安全与稳定性

- 使用 GitHub-hosted runner（Ubuntu），不使用自托管 runner，也不触碰家庭服务器。
- workflow 使用 `pull_request`，不使用 `pull_request_target` 执行 PR 代码。
- 权限默认 `contents: read`；不需要 PAT、部署密钥、RCON 密码或发布 Token。
- 固定 Paper build 的 PR smoke 与 nightly latest-stable 分开，避免 PR 因上游新 build 漂移而不稳定。
- 设置 job timeout；启动等待使用有上限的轮询，不使用无限等待。
- 使用 Python `subprocess.Popen` 管理 stdin/stdout/stderr，避免 shell FIFO/pipeline 的进程生命周期不确定性。
- 使用 finally/cleanup 保证尽力发送 stop；即使失败也上传日志。
- 不上传整个 runner 环境或配置，只上传脱敏后的 server log、构建产物和测试摘要。
- 失败日志中避免打印环境变量、Token 或 runner 私有信息。

## 7. 后续扩展

- P2 Scheduler 完成后，新增独立 Folia smoke job；Paper 通过不能代替 Folia 证据。
- 只有真实 Folia smoke、线程访问审查、任务取消和关闭测试全部通过，才允许声明 `folia-supported: true`。
- MockBukkit 用于快速验证插件装配/命令/事件；不能替代真实 Paper/Folia 进程验收。
- 若某个新插件需要真实玩家登录、区块交互或多客户端协作，再按需添加 Mineflayer E2E；模板默认不引入。

## 8. Paper CLI 探测与验收报告

- 启动临时 Paper 前先执行 `java -jar paper.jar --help`，最多等待 20 秒，避免不支持该参数时无限挂起。
- 探测结果作为诊断证据写入 JSON 报告：命令、超时阈值、退出码、帮助文本识别结果及截断后的输出。
- 探测失败或未识别帮助文本只记录诊断，不单独阻断后续 smoke；Paper 实际启动与插件行为仍由独立验收步骤判定。
- 报告记录 Java 版本、实际 Paper 启动命令、loopback 绑定、`online-mode=false`、RCON/Query 关闭及 EULA 门禁后生成文件的状态。
- 该探测在生成 `eula.txt` 之前运行；即使帮助参数行为异常，也不会越过 EULA 门禁启动服务端。

## 9. 当前落地状态

- [x] P1 本地 Paper 26.3 build 263 验收通过。
- [x] 现有 GitHub Actions 执行 JDK 25 构建、JUnit 与 JAR inspection。
- [x] P2.1 ResourceScope/lifecycle 实现和测试合并。
- [x] P2.2 typed config、schema migration、Paper YAML adapter 与 Core tests 合并。
- [x] 实现可复用的 `scripts/smoke-paper.py`（子仓库 PR #10）。
- [x] 增加受 `MINECRAFT_EULA_ACCEPTED=true` 门禁控制的 Paper smoke workflow job（子仓库 PR #10）。
- [x] 增加 Paper CLI `--help` 有界探测及运行环境/启动参数报告（子仓库 PR #11，CI Run #58 success）。
- [x] 增加脚本级 EULA fail-closed 二次校验，避免绕过 workflow 直接生成 `eula=true`（子仓库 PR #12，CI Run #60 success，merge `6552f12`）。
- [ ] 增加 nightly latest-stable 兼容性 job。
- [x] 验证组织级变量已授权 `OrzMC/PluginTemplate`，首轮真实 Paper smoke 通过（CI Run #61；Paper 26.3 build 263；Java 25；命令、reload、clean shutdown 全部通过）。
- [x] 将 evidence artifact 限定为 JSON 报告、server log、server.properties、eula.txt（子仓库 PR #13，CI Run #62 success）；首次 artifact 217 MB，精简后 5.1 KB。\n- [ ] 观察至少 3 次成功运行和 1 次可控失败，确认 CLI 探测、日志、超时、清理与 artifact 行为。
