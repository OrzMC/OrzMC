# OrzMC Docker 执行路径与 Checklist

本文档用于把 `deploy/docker` 从“已完成平台层验证的部署草案”推进到“最小可执行 MVP”，并继续推进到生产化落地。

后续无论是人工继续执行，还是在多轮 AI 对话中继续推进，都应以本文档为单一执行基线，避免遗忘前置约束、当前状态和阶段目标。

## 1. 当前基线

当前已确认的状态如下：

- `deploy/docker` 已具备平台层编排能力，核心文件包括：
  - `compose.yaml`
  - `caddy/Caddyfile`
  - `.env.example.minimal`
  - `.env.example.full`
  - `.env.local.example`
  - `local.sh`
  - `update-image-digests.sh`
- 平台层边界已经确定：
  - `Caddy` 负责统一入口与 HTTPS
  - `MCSManager Web` 提供控制面板
  - `MCSManager Daemon` 管理实例
  - `NapCat` 提供 QQ 侧能力
  - `PaperMC` 不写入 `compose.yaml`，而是由 `MCSManager` 创建和管理
- 本地验证迹象已经存在：
  - `.local-data/caddy` 已生成本地证书
  - `.local-data/mcsmanager` 已生成面板和守护进程数据
  - `.local-data/napcat` 已生成运行数据
  - `MCSManager Web` 与 `MCSManager Daemon` 已有过成功连接记录
- 当前未完成事项：
  - 尚未创建真实的 `PaperMC Test` 实例
  - 尚未形成“从 clone 到可进服”的完整验收闭环
  - 尚未补齐生产化安全、运维和自动化校验
- 当前风险：
  - `deploy/docker` 已加入 Git 跟踪，但尚未提交
  - 运行态目录中已有真实私密数据，后续必须继续保持忽略，不得提交

## 2. 执行原则

后续推进必须遵守以下原则：

1. 先做 `MVP`，再做生产化。
2. 先验证 `PaperMC Test`，再考虑 `PaperMC Prod`。
3. `PaperMC` 继续由 `MCSManager` 管理，不回退成 `compose.yaml` 常驻服务。
4. 不提交运行态文件：
   - `.env`
   - `.env.local`
   - `.local-data/`
   - 任意包含真实 token、key、登录态、证书、密钥的文件
5. 每完成一个阶段，必须补“完成证据”，再进入下一阶段。
6. 如果发现实际状态与本文档不一致，先更新本文档的“状态记录”再继续执行。

## 3. 阶段划分

后续推进分为 4 个阶段：

- Phase 0：基线固化
- Phase 1：最小可执行 MVP
- Phase 2：生产化落地
- Phase 3：自动化与长期运维

### Phase 0 完成定义

目标：把当前已知结论沉淀成可持续执行的仓库文档和边界规则。

退出条件：

- 本文档已存在并可作为后续单一执行基线
- README 中有明确入口可跳转到本文档
- 团队对“平台层已验证，业务层未闭环”的判断一致

### Phase 1 完成定义

目标：从当前状态推进到最小可执行 MVP。

这里的 MVP 指：

- 平台层可通过 `local.sh` 或等效命令稳定拉起
- `MCSManager Web` 可访问
- `MCSManager Daemon` 已连接
- `NapCat WebUI` 可访问
- 成功创建并运行一个 `PaperMC Test` 实例
- 完成 `启动 / 停止 / 重启 / 数据持久化 / 插件目录 / 日志目录 / 端口暴露` 验证
- README 或附属文档里存在一条可复现的最短执行路径

### Phase 2 完成定义

目标：把 MVP 推进为可生产使用的部署方案。

退出条件：

- 生产 `.env` 模板使用方式明确
- DNS、端口、公网访问、HTTPS、备份、恢复、回滚有明确步骤
- `PaperMC Prod` 录入方式明确且经验证
- 管理员权限、token、节点 key 的保存与轮换规则明确

### Phase 3 完成定义

目标：把“手工操作经验”收束为“自动化检查和标准运维动作”。

退出条件：

- 至少存在一个环境自检脚本或验收脚本
- 至少存在一组基础自动化校验
- 升级与回滚流程可按文档重复执行

## 4. 当前推荐执行路径

严格按下面顺序推进，不建议跨阶段并行：

1. 固化基线与规则
2. 重放平台层本地启动验证
3. 创建并验证 `PaperMC Test`
4. 把 MVP 的最短执行路径写回文档
5. 再进入生产化准备

## 5. MVP Checklist

以下清单是当前阶段最重要的执行清单。

### A. 基线固化

- [x] 把 `deploy/docker` 纳入版本控制
- [x] 确认 `.gitignore` 继续忽略 `.env`、`.env.local`、`.local-data/`
- [x] 在 README 中增加执行路径入口
- [x] 明确当前架构边界：`PaperMC` 仍由 `MCSManager` 管理
- [x] 明确当前结论：平台层已验证，`PaperMC` 尚未落地

### B. 平台层重放验证

- [x] 执行 `./local.sh init`
- [x] 执行 `./local.sh start`
- [x] 执行 `docker compose --env-file .env.local -f compose.yaml ps`
- [x] 访问 `https://mcs.localhost:18443`，确认 `MCSManager Web` 可访问
- [x] 访问 `https://qqbot.localhost:18443`，确认 `NapCat WebUI` 可访问
- [x] 检查 `MCSManager Web` 中节点状态，确认 `local-daemon` 已连接
- [x] 执行 `./local.sh status`，记录访问地址和容器状态
- [x] 执行 `./local.sh stop`，确认可干净停止

### C. PaperMC Test 落地

- [x] 选定 `PaperMC Test` 使用的镜像来源与版本
- [x] 准备测试服目录：
  - `server/`
  - `backups/`
  - `import/`（如需）
- [x] 按 `docs/papermc-template.md` 在 `MCSManager` 中创建 `PaperMC Test`
- [x] 首次启动实例，确认 EULA、Jar、工作目录、挂载目录均正确
- [x] 验证能从 `MCSManager` 面板正常停止实例
- [x] 验证能从 `MCSManager` 面板正常重启实例
- [x] 验证世界数据在宿主机目录持久化
- [x] 验证 `plugins/` 目录可用
- [x] 验证 `logs/` 目录可用
- [x] 验证宿主机端口 `25566` 可访问

### D. MVP 验收

- [x] 输出一条“从本地拉起平台层到测试服可运行”的最短操作路径
- [x] 在文档中补充 `PaperMC Test` 的实际录入参数或最终模板
- [x] 补充已验证项与未验证项
- [x] 记录至少 1 份日志或截图证据的位置
- [x] 明确 MVP 已完成，允许进入 Phase 2

## 6. Phase 2 Checklist

当且仅当 MVP 完成后，再进入本阶段。

### A. 生产环境准备

- [ ] 选择生产宿主机路径，例如 `/srv/orzmc`
- [ ] 按最小模板准备 `.env`
- [ ] 明确公网域名与 DNS 解析
- [ ] 确认公网 `80/443` 可用
- [ ] 明确 `NapCat`、`MCSManager`、`PaperMC` 的资源预算
- [ ] 明确宿主机备份与监控责任边界

### B. 平台层生产验证

- [ ] 在生产环境执行目录初始化
- [ ] 启动平台层容器
- [ ] 验证 Caddy 自动 HTTPS
- [ ] 验证 MCSManager Web 可公网访问
- [ ] 验证 Daemon 节点连接
- [ ] 验证 NapCat 登录态持久化

### C. PaperMC Prod 落地

- [ ] 准备正式服目录
- [ ] 创建 `PaperMC Prod`
- [ ] 验证端口 `25565`
- [ ] 验证备份目录与保留策略
- [ ] 验证插件更新与回滚方式
- [ ] 验证升级窗口与停机流程

### D. 安全收口

- [ ] 明确 MCSManager 管理员账号创建与保管方式
- [ ] 明确 Daemon key 保存方式
- [ ] 明确 NapCat WebUI token 保存方式
- [ ] 明确哪些配置允许入库，哪些必须只保留在线下
- [ ] 明确 `docker.sock` 风险与宿主机可信边界

## 7. Phase 3 Checklist

### A. 自动化校验

- [ ] 增加 `docker compose config` 校验入口
- [ ] 增加 shell 脚本静态检查
- [ ] 增加环境变量缺失检查
- [ ] 增加目录存在性检查

### B. 运维动作标准化

- [ ] 固化升级步骤
- [ ] 固化回滚步骤
- [ ] 固化备份恢复演练步骤
- [ ] 固化常见故障排查步骤

### C. 文档持续维护

- [ ] 每次阶段性完成后更新本文档
- [ ] 每次新增实际限制后更新 README
- [ ] 每次新增脚本后更新“最短执行路径”

## 8. 完成证据要求

每完成一个阶段，至少留存以下证据之一：

- 一段实际执行命令记录
- 一份关键日志路径
- 一张访问成功的截图
- 一段最终生效配置
- 一条写回仓库文档的结论

没有证据，不视为完成。

## 9. 已验证的 MVP 最短路径

以下路径已在本地验证通过：

1. 执行 `./local.sh start`
2. 准备测试服目录：`.local-data/instances/papermc-test/{server,backups,import}`
3. 下载 `paper-1.21.1-133.jar` 到测试服 `server/` 目录，并重命名为 `paper.jar`
4. 在 `server/` 目录预置 `eula.txt` 和 `server.properties`
5. 在 `MCSManager` 中创建一个 Docker 实例：
   - 镜像：`eclipse-temurin:21-jre`
   - 工作目录：`/server`
   - 宿主机服务目录：`.../papermc-test/server`
   - 启动命令：`java -XX:+UseG1GC -XX:+ParallelRefProcEnabled -Xms2G -Xmx2G -jar paper.jar --nogui`
   - 端口映射：`25566:25566/tcp`
6. 启动实例，观察日志出现 `Done`
7. 验证 `25566` 端口、`plugins/`、`logs/latest.log`、`world/` 持久化目录
8. 通过 `MCSManager` 执行停止与重启

## 10. 当前最小下一步

从现在开始，优先按以下顺序推进：

1. 提交当前 `deploy/docker` 变更
2. 整理生产环境 `.env` 与目录规划
3. 准备 DNS、公网端口和 HTTPS 条件
4. 进入 Phase 2 的生产化验证

在 Phase 2 开始前，不要修改 `PaperMC` 的职责边界。

## 11. 状态记录模板

后续每完成一轮推进，都按以下模板追加记录：

```md
### YYYY-MM-DD

- 当前阶段：
- 已完成：
- 新发现问题：
- 下一步：
- 证据：
```

## 12. 状态记录

### 2026-04-25

- 当前阶段：Phase 1
- 已完成：
  - `deploy/docker` 下 11 个源码与文档文件已加入 Git 跟踪
  - 已确认 `.gitignore` 继续忽略 `.env`、`.env.local`、`.local-data/`
  - 已执行 `./local.sh init`
  - 已执行 `./local.sh start`
  - 已执行 `docker compose --env-file .env.local -f compose.yaml ps`
  - 已执行 `./local.sh status`
  - 已执行 `./local.sh stop`
  - 已通过 `curl -k -I` 验证 `MCSManager Web` 与 `NapCat WebUI` 反代入口可访问
  - 已通过 `MCSManager Web` 当前日志验证 `local-daemon` 节点连接成功且密钥验证通过
- 新发现问题：
  - 当前只是“已加入 Git 跟踪”，还没有形成 Git 提交
  - 平台层验证已完成，但 `PaperMC Test` 仍未创建，MVP 还差业务层闭环
- 下一步：
  - 选择 `PaperMC Test` 使用镜像与版本
  - 在 `MCSManager` 中创建 `PaperMC Test`
  - 验证启动、停止、重启、数据持久化、插件目录、日志目录、端口 `25566`
- 证据：
  - Git 跟踪结果：`git status --short -- deploy/docker`
  - 平台层状态：`docker compose --env-file .env.local -f compose.yaml ps`
  - 访问验证：`curl -k -I https://mcs.localhost:18443`
  - 访问验证：`curl -k -I https://qqbot.localhost:18443`
  - 节点日志：`.local-data/mcsmanager/web/logs/current.log`
  - 守护进程日志：`.local-data/mcsmanager/daemon/logs/current.log`

### 2026-04-25 PaperMC Test

- 当前阶段：Phase 1
- 已完成：
  - 已选定 `eclipse-temurin:21-jre` 作为本地验证使用的 Java 21 Docker 镜像
  - 已准备 `.local-data/instances/papermc-test/{server,backups,import}`
  - 已下载 `paper-1.21.1-133.jar` 并落盘为 `paper.jar`
  - 已预置 `eula.txt` 和 `server.properties`
  - 已通过 `MCSManager` 官方实例 API 创建 `PaperMC Test`
  - 已验证首次启动成功，日志出现 `Done`
  - 已验证宿主机端口 `25566` 可访问
  - 已验证世界目录、`plugins/`、`logs/latest.log` 已持久化到宿主机目录
  - 已验证通过 `MCSManager` 生命周期接口执行停止与重启
  - 已将可运行参数和踩坑记录写回 `docs/papermc-template.md`
- 新发现问题：
  - `cwd` 指向宿主机服务目录时，MCSManager 会自动挂载工作目录，不能再把同一目录通过 `extraVolumes` 重复挂到 `/server`
  - 当前本地测试管理员 `apiKey` 为临时调试用途，仅存在于 `.local-data`，不能进入版本控制，也不应复用于生产环境
- 下一步：
  - 提交当前 `deploy/docker` 变更
  - 进入 Phase 2，准备生产 `.env`、目录规划和公网访问条件
- 证据：
  - 实例 UUID：`773ce9e680074252938686a2d6185371`
  - 创建接口：`POST /api/instance`
  - 启动接口：`GET /api/protected_instance/open`
  - 停止接口：`GET /api/protected_instance/stop`
  - 重启接口：`GET /api/protected_instance/restart`
  - 输出日志接口：`GET /api/protected_instance/outputlog`
  - 实例配置文件：`.local-data/mcsmanager/daemon/data/InstanceConfig/773ce9e680074252938686a2d6185371.json`
  - 实例数据目录：`.local-data/instances/papermc-test/server`
