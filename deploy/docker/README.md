# OrzMC Docker 部署草案

这套目录用于承载 OrzMC 的最小容器化落地方案，目标是先跑通平台层：

- `Caddy` 作为统一入口和 HTTPS 终止
- `MCSManager Web`
- `MCSManager Daemon`
- `NapCat`

`PaperMC` 不直接写在 `compose.yaml` 中，而是在 `MCSManager` 面板里作为 Docker 实例创建和管理。

如果要继续推进当前部署方案，请优先阅读 `EXECUTION_PATH.md`：

- `EXECUTION_PATH.md`：从当前状态推进到最小可执行 MVP，再到生产化落地的执行路径与 checklist

## 目录说明

- `compose.yaml`：平台层容器编排
- `.env.example.minimal`：第一次部署优先使用的最小参数样例
- `.env.example.full`：完整模板参数样例，包含测试服和正式服的 `PaperMC` 参数
- `.env.local.example`：本地验证专用参数样例，适合 macOS / Docker Desktop
- `EXECUTION_PATH.md`：阶段执行路径、门禁规则和 checklist
- `local.sh`：本地验证统一入口，支持 `init/start/stop/status`
- `update-image-digests.sh`：刷新镜像 digest，配合 Git 做升级与回滚
- `caddy/Caddyfile`：反向代理和自动 HTTPS 配置
- `docs/papermc-template.md`：在 `MCSManager` 中录入 `PaperMC` 实例时的字段建议

## 推荐目录规划

宿主机建议统一使用一个根目录保存所有数据，例如 `/srv/orzmc`：

```text
/srv/orzmc/
  caddy/
    data/
    config/
  mcsmanager/
    web/
      data/
      logs/
    daemon/
      data/
      logs/
  napcat/
    qq/
    config/
    plugins/
  instances/
    papermc-main/
      server/
      backups/
    papermc-test/
      server/
      backups/
```

## 第一次部署

1. 复制最小参数文件

```bash
cd deploy/docker
cp .env.example.minimal .env
```

2. 至少修改这些变量

- `DATA_ROOT`
- `CADDY_EMAIL`
- `DOMAIN_QQBOT`
- `DOMAIN_QQBOT_API`
- `DOMAIN_QQBOT_WS`
- `DOMAIN_MCS_WEB`
- `DOMAIN_MCS_NODE`
- `QQBOT_APP_ID`
- `QQBOT_CLIENT_SECRET`

3. 初始化宿主机目录

```bash
mkdir -p \
  /srv/orzmc/caddy/data \
  /srv/orzmc/caddy/config \
  /srv/orzmc/mcsmanager/web/data \
  /srv/orzmc/mcsmanager/web/logs \
  /srv/orzmc/mcsmanager/daemon/data \
  /srv/orzmc/mcsmanager/daemon/logs \
  /srv/orzmc/napcat/qq \
  /srv/orzmc/napcat/config \
  /srv/orzmc/napcat/plugins \
  /srv/orzmc/instances/papermc-main/server \
  /srv/orzmc/instances/papermc-main/backups \
  /srv/orzmc/instances/papermc-test/server \
  /srv/orzmc/instances/papermc-test/backups
```

4. 启动平台层服务

```bash
docker compose up -d
```

5. 验证平台层

- 打开 `https://${DOMAIN_MCS_WEB}`，确认 `MCSManager Web` 可访问
- 打开 `https://${DOMAIN_QQBOT}`，确认 `NapCat WebUI` 可访问
- 在 `MCSManager` 中添加节点，使用 `https://${DOMAIN_MCS_NODE}` 对应的守护进程入口
- 进入 `mcsmanager-daemon` 数据目录读取节点密钥

## 本地验证模式

如果你是在 macOS 本机使用 Docker Desktop 做功能验证，建议不要直接使用 `.env.example.minimal`：

- `DATA_ROOT=/srv/orzmc` 默认不在 Docker Desktop 的 File Sharing 白名单内，卷挂载会失败
- `80/443` 可能已被本机其他程序占用
- 本地并不一定有真实公网域名和 DNS 解析

建议改用：

```bash
./local.sh start
```

`local.sh start` 会顺序执行：

- 生成 `.env.local`
- 初始化 `.local-data`
- `docker compose --env-file .env.local up -d`

如果你想看脚本内部做了什么，本质上就是：

```bash
REPO_ROOT="$(git rev-parse --show-toplevel)"
sed "s#<LOCAL_PROJECT_ROOT>#${REPO_ROOT}/deploy/docker#g" .env.local.example > .env.local
```

本地验证版默认做了这些调整：

- `DATA_ROOT` 指向你本机仓库目录下的 `.local-data`
- 对外端口改为 `18080/18443`
- 域名改为 `*.localhost`

如果你想手动创建目录，脚本内部等价于：

```bash
mkdir -p \
  .local-data/caddy/data \
  .local-data/caddy/config \
  .local-data/mcsmanager/web/data \
  .local-data/mcsmanager/web/logs \
  .local-data/mcsmanager/daemon/data \
  .local-data/mcsmanager/daemon/logs \
  .local-data/napcat/qq \
  .local-data/napcat/config \
  .local-data/napcat/plugins \
  .local-data/instances/papermc-main/server \
  .local-data/instances/papermc-main/backups
```

本地验证完成后可执行：

```bash
./local.sh stop
```

查看当前状态和访问地址：

```bash
./local.sh status
```

如果你只想初始化本地配置和目录，不启动容器：

```bash
./local.sh init
```

## PaperMC 的创建边界

`PaperMC` 不是这个 `compose.yaml` 的常驻服务，而是后续在 `MCSManager` 面板里新增的实例：

- 平台层由 `docker compose` 管理
- `PaperMC` 生命周期由 `MCSManager Daemon` 管理
- `PaperMC` 数据持久化在 `/srv/orzmc/instances/`

这样做的好处：

- 不会出现 `compose` 和 `MCSManager` 两套控制入口冲突
- 后续增加第二个 Minecraft 实例时，不需要改平台编排
- 更符合 `MCSManager` 的职责边界

## 端口约定

- `80/443`：`Caddy`
- `23333`：`MCSManager Web` 容器内部端口
- `24444`：`MCSManager Daemon` 容器内部端口
- `6099`：`NapCat WebUI`
- `3000`：`NapCat HTTP`
- `3001`：`NapCat WebSocket`
- `25565`：建议保留给 `PaperMC` 正式服
- `25566`：建议保留给 `PaperMC` 测试服

## 重要说明

- `mcsmanager-daemon` 挂载了 `/var/run/docker.sock`，这意味着它拥有管理宿主机 Docker 的能力，必须把该宿主机视为可信环境。
- `NapCat` 的登录态依赖 `qq` 数据目录持久化，目录挂载错误可能导致重复登录。
- `Caddy` 自动签发 HTTPS 证书依赖真实域名解析到宿主机，且 `80/443` 可从公网访问。
- `.env.example.full` 中的 `PAPERMC_*` 参数主要用于模板化管理和后续录入 `MCSManager`，当前不会直接被 `compose.yaml` 消费。

## 升级与回滚

当前 `compose.yaml` 使用镜像摘要锁定，这意味着升级过程建议分成两步：

1. 拉取指定来源 tag 的最新镜像并刷新 `compose.yaml` 中的 digest
2. 用 Git 审查变更并提交，之后再重建容器

可以直接使用脚本：

```bash
./update-image-digests.sh
```

如果只想更新部分服务，也可以传入服务名：

```bash
./update-image-digests.sh mcsmanager-web mcsmanager-daemon
./update-image-digests.sh napcat
```

可选服务名：

- `reverse-proxy`
- `mcsmanager-web`
- `mcsmanager-daemon`
- `napcat`

建议升级流程：

```bash
./update-image-digests.sh
git diff -- deploy/docker/compose.yaml
git add deploy/docker/compose.yaml
git commit -m "chore: update docker image digests"
./local.sh start
```

如果升级后需要回滚，直接回退包含 `compose.yaml` digest 变更的 Git 提交，再重新执行：

```bash
git revert <commit>
./local.sh start
```
