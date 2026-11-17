# OrzMCDeploy 版本升级规程（实战：0.0.3 → 0.0.4，0.0.4 → 0.0.6）

> **升级前先做包间 diff 定范围**：`diff -u 旧包/compose.yaml 新包/compose.yaml`。若只有 easybot 段变化（镜像
> digest / 内存参数）→ 其他服务不会重建、**站点增量无需迁移、daemon 也无需手动重建**（铁律 3 只在
> daemon 定义本身变了时才适用）；这种升级全程只需 `validate` → `up` → 验收，实测 0.0.4 → 0.0.6 就是这一档。

## 铁律

1. **升级前先做三方 diff**：`diff -rq 旧包目录 新包目录` 只能看出「上游改了什么 + 本站改了什么」的混合体，
   必须另取一份**官方原版旧包**（`gh release download` 或匿名 `curl -L` tarball）再 diff，才能把**本站站点改动**
   单独拎出来。否则站点改动会在换包时静默丢失。
2. **凭据只放两个地方，永不改包内文件**：
   - `.env` 在 **DATA_ROOT 内**（如 `E:/orzmc/.env`）→ 换包天然不受影响；
   - 站点增量写在 **`$DATA_ROOT/compose.site.yaml`**（v0.0.4+/ADR-022 官方挂载点，`compose_cmd` 自动 `-f`），
     或 `.env` 的 `COMPOSE_FILE_EXTRA`。
   典型丢失场景：EasyBot 的 `FEISHU_APP_ID/FEISHU_APP_SECRET`——旧版是**手工改包内 `compose.yaml`** 加的，
   换包即丢 → 表现为「升级后机器人不工作了」。
3. **daemon 只在自身定义变更时手工重建**：Windows 下 daemon 由 `win_daemon_run` 用 `docker run` 创建（ADR-016），
   函数**幂等**——容器已存在就跳过。所以只有本次升级改了 `DAEMON_PORTS` / `DAEMON_MEMORY_LIMIT` /
   `DAEMON_NODE_HEAP_MB` / healthcheck 时，才必须 `docker rm -f orzmc-mcsmanager-daemon` 再 `up`；
   仅改其他服务时 `up` 会打印「daemon 已存在，跳过创建（补别名）」，属正常。
4. **label 对齐需 `--force-recreate`**，且注意两点：服务名是 `mcsmanager-web`（**不是** `web`，写错 compose
   直接 abort，什么都不重建）；合并后配置**等价时 compose 不会重建**（站点增量把 env 补回来后 easybot 配置与
   旧容器一致 → 不重建，属正确行为）。
5. **保留旧版包目录做回滚**：回滚 = `cd 旧包目录 && ./orzmc.sh -d E:/orzmc up`；数据目录与 `.env` 全程不动。
6. 下载先 `sha256sum -c` 官方 `.sha256`；E 盘/仓库都是公开的，**匿名 curl 即可，不依赖 gh token**。

## 升级步骤（可直接照做）

```bash
# 0 备份 + 基线
BK=/e/deploy/upgrade-<日期>; mkdir -p $BK
cp /e/orzmc/.env $BK/env.before.bak && chmod 600 $BK/env.before.bak
docker ps -a --format '{{.Names}}\t{{.Status}}' > $BK/containers.before.txt
docker inspect orzmc-mcsmanager-daemon --format 'Restart={{.HostConfig.RestartPolicy.Name}} Memory={{.HostConfig.Memory}} Cmd={{json .Config.Cmd}}' > $BK/daemon.before.txt

# 1 下载校验落包
curl -sL -o /tmp/orzmc.tar.gz https://github.com/OrzMC/OrzMCDeploy/releases/download/vX.Y.Z/orzmc-X.Y.Z.tar.gz
curl -sL -o /tmp/orzmc.sha256  https://github.com/OrzMC/OrzMCDeploy/releases/download/vX.Y.Z/orzmc-X.Y.Z.tar.gz.sha256
sha256sum -c /tmp/orzmc.sha256        # 必须 OK
mkdir -p /e/deploy/orzmc-deploy-X.Y.Z && tar xzf /tmp/orzmc.tar.gz -C /e/deploy/orzmc-deploy-X.Y.Z

# 2 init + 站点增量（凭据迁移）
cd /e/deploy/orzmc-deploy-X.Y.Z && ./orzmc.sh -d E:/orzmc init    # 生成 $DATA_ROOT/compose.site.yaml
#    编辑 $DATA_ROOT/compose.site.yaml 把站点改动写进去（引用 .env 的变量，不写明文）
./orzmc.sh -d E:/orzmc validate                                   # 必需变量 + compose 解析

# 预检：确认站点增量真的并进去了（凭据不会丢）
docker compose --env-file E:/orzmc/.env -f compose.yaml -f compose.edge.cloudflare.yaml \
  -f E:/orzmc/compose.site.yaml --profile easybot --profile mariadb --profile status config \
  | grep -E 'FEISHU_APP_ID|FEISHU_APP_SECRET'   # 能列出即 ✓（注意别把值打进日志）

# 3 重建
docker rm -f orzmc-mcsmanager-daemon        # 不然 win_daemon_run 幂等跳过
./orzmc.sh -d E:/orzmc up
CFG=(--env-file E:/orzmc/.env -f compose.yaml -f compose.edge.cloudflare.yaml -f E:/orzmc/compose.site.yaml --profile easybot --profile mariadb --profile status)
docker compose "${CFG[@]}" up -d --force-recreate --no-deps --no-build mcsmanager-web status cloudflared easybot mariadb
```

## 验收清单

- [ ] `docker ps` 全绿；daemon `(healthy)`（v0.0.4 起有 TCP healthcheck）
- [ ] daemon `Memory=536870912` + `Cmd=[node, --max-old-space-size=<DAEMON_NODE_HEAP_MB>, app.js]`（旧版是 8192，与 512M 限额矛盾）
- [ ] 5 容器 label `com.docker.compose.project.working_dir` = 新包路径
- [ ] **重建后** easybot 仍有 `FEISHU_APP_ID/SECRET`（证明走站点增量而非旧容器残留）
- [ ] 4 端点 200：`mcs.{SERVER_NAME}.cn` / `mcs-node.{SERVER_NAME}.cn` / `easybot.{SERVER_NAME}.cn` / `orzmcs.{SERVER_NAME}.cn`
- [ ] 面板日志出现 `远程节点 … 密钥验证通过`（daemon 与新容器重连）
- [ ] 两个 MCSM 实例**未被拉起**（`docker ps --filter name=MCSM-` 为空）
- [ ] `docker port <daemon>` 无输出（docker 型实例场景下 DAEMON_PORTS 被自动忽略）

## 单元测试小技巧：验证 .env 驱动的函数（不碰生产）

`env_file()` = `$DATA_ROOT/.env`，`read_env_value` 只从那一个文件读。所以可以造**隔离 DATA_ROOT**：

```bash
T="$LOCALAPPDATA/Temp/dp-test"
mkdir -p "$T/mcsmanager/daemon/data"
cp -r /e/orzmc/mcsmanager/daemon/data/InstanceConfig "$T/mcsmanager/daemon/data/"   # 只拷实例配置，无凭证
printf 'DATA_ROOT=%s\nDAEMON_PORTS=25565:25565/tcp\n' "$T" > "$T/.env"            # 自己造的假 .env
cd /e/deploy/orzmc-deploy-X.Y.Z
DATA_ROOT="$T" bash -c 'source lib/common.sh; win_effective_daemon_ports "$DATA_ROOT"'
```

注意：函数内 `env_file()` 用的是 shell 全局 `DATA_ROOT`，所以 **`DATA_ROOT=... bash -c '...'` 的赋值必须在同一行**
（在 bash -c 里再读 `$1` 不行）。

## v0.0.4（2026-09-11）验收结果

上游 PR #13 / ADR-022 一次性处理 #9–#12：

| issue | 修复点 | 验收 |
|---|---|---|
| #9 | 新增 `win_effective_daemon_ports()` + `find_docker_instance()`：存在 docker 型实例时自动忽略 `DAEMON_PORTS` 并对已存在 daemon 打 warn | ✓ **正反例实测**：隔离 DATA_ROOT（临时 `.env` + 实例配置副本，不碰生产）下，场景 A（docker 型实例 + `DAEMON_PORTS=25565:25565/tcp`）→ 打印忽略提示且生效值**为空**；场景 B（仅进程模式实例）→ 生效值**保留** `25565:25565/tcp`（无过度忽略）。生产 daemon `docker port` 无输出 ✓ |
| #10 | `DAEMON_MEMORY_LIMIT`(默认 512M) / `DAEMON_NODE_HEAP_MB`(默认 384) + CMD 覆盖 + TCP healthcheck | ✓ 实测 `Memory=536870912`、`Cmd=[node,--max-old-space-size=384,app.js]`（原 8192）、`Health=healthy`、实占 54MiB |
| #11 | `ensure_site_override` 生成 `$DATA_ROOT/compose.site.yaml`，`compose_cmd` 自动 `-f`；`.env` 支持 `COMPOSE_FILE_EXTRA` | ✓ `init` 已生成；飞书凭据迁入后强制重建，easybot 凭据仍在 |
| #12 | `docs/usage.md` §6.5 改为「停 daemon → 改 JSON → 启 daemon」+ `autoStart/autoRestart` 语义 | ✓ 文档已含该节及排错表 |

升级后未发现新的上游问题（唯一故障是本站自己把服务名写成 `web`，compose 报 `no such service` 后 abort）。

## 本机 Windows 审批/命令坑（0.0.4 → 0.0.6 实测）

- **别用 `rm -rf` 清目录**：会触发审批拦截（未响应 = `BLOCKED`，白等十分钟）。铺包一律 `mkdir -p 新目录 && cp -a 解包目录/. 新目录/`，不要在解包前先删。
- `docker run --rm --network orzmc_default curlimages/curl …` 这类探测也会被审批系统**误判为递归删除**（命中一次已批准）；优先用已在运行的 `orzmc-mcsmanager-daemon` 做外部探测，它一定能出网：
  `docker exec orzmc-mcsmanager-daemon sh -c 'curl -s -o /dev/null -w "%{http_code}" --max-time 12 https://<host>/'`。
- 备份用 `cp -a` 到 `E:/deploy/backups/pre-upgrade-<版本>-<时间>/`（easybot DB 約 20MB），升级无风险后再清。

## v0.0.4 → v0.0.6（2026-10-02）实战与验收

范围（`diff -rq` + `compose.yaml` diff 定的）：与 0.0.4 相比只有 easybot 两处功能变化 —— 镜像 digest
`cd0b4e44`(0.0.38) → `23a6eace`(**v0.0.41**)，内存上限硬编码 `512M` → `"${EASYBOT_MEMORY_LIMIT:-512M}"`；
其余 4 个镜像 digest、`compose.edge.*.yaml`、全部脚本**未变**（只有 docs/CHANGELOG/templates/env.* 变）。
0.0.5 曾把缺省调到 1G，0.0.6 又回调 512M（ADR-024：上限保持紧，让未来的内存回归由 OOM 尽快暴露，
而不是被余量掩盖）——**升级 0.0.5+ 时不要自作主张把上限放大**。

```bash
gh release download v0.0.6 -R OrzMC/OrzMCDeploy -p 'orzmc-0.0.6.tar.gz*' -D <临时目录>
sha256sum -c orzmc-0.0.6.tar.gz.sha256          # 必须 OK
mkdir -p E:/deploy/orzmc-deploy-0.0.6 && tar xzf orzmc-0.0.6.tar.gz -C <解包目录>
cp -a <解包目录>/. E:/deploy/orzmc-deploy-0.0.6/ && chmod +x E:/deploy/orzmc-deploy-0.0.6/*.sh
cd E:/deploy/orzmc-deploy-0.0.6
./orzmc.sh -d E:/orzmc validate                 # ✓ 必需变量齐全，compose config 解析正常
./orzmc.sh -d E:/orzmc templates --diff         # 只看是否与 .env 漂移（模板占位符差异属正常）
./orzmc.sh -d E:/orzmc up                       # 只 recreate easybot，其余显示 Running
```

实测输出：`Container orzmc-easybot Recreated/Started`，其余 4 个 `Running`；中断约 25 秒。

验收（全通过）：

- [x] `docker inspect orzmc-easybot`：`image=…@sha256:23a6eace…`、`mem=536870912`(512M)、`restarts=0`、`oomkilled=false`
- [x] 启动日志出现 `v4: Cover outbound_deliveries ORDER BY queries to avoid per-tick temp B-trees` + `SQLite storage initialized`（**无** EPERM/降级告警 → 旧 `chown 10001:10001` 绕过已可弃）
- [x] `docker logs` 无 warn/error；`Started adapters: ["qq", "feishu"]`、`飞书适配器已连接`、`QQ adapter connected`
- [x] `/api/v1/live` → `version=0.0.41`；`/api/v1/ready` → `ready`、`auth_schema_version=4`、`message_storage=ready`、`unpublished_delivery_events=0`、`adapters_connected=2`
- [x] 内网 `easybot:8080` live/ready 200；公网 4 域名全 200（mcs / mcs-node / easybot / orzmcs）
- [x] Gatus 平台层 5 项全 OK（PaperMC 实例 FAIL 属设计如此，实例手动启停）
- [x] `gateway.db` 的 `outbound_deliveries` 三个 v4 索引齐备（`idx_outbound_deliveries_outbox/_actor/_session`）
- [x] 回滚可用：旧镜像 `cd0b4e44`(0.0.38) 与 `1c02c337` 仍在本地 `docker images`
- [x] **标签对齐（B 方案）**：`docker compose … --force-recreate` 把 web/status/cloudflared/mariadb 的
  `project.working_dir` 全部刷到 `E:\deploy\orzmc-deploy-0.0.6`（easybot 已是），之后才删旧包——**先对齐再删目录**，
  否则触发「旧路径复活为空目录」（docker-service-lifecycle.md §10）。⚠️ 拼这条命令**必须带** `-f $DATA_ROOT/compose.site.yaml`，
  否则飞书凭据丢失、只剩 QQ 适配器（见 §9 的 ❗❗）。

**手建索引与上游迁移共存**：升级前若已手工建过 v4 索引（本机 2026-09-30 为验证修复做过），
上游迁移是 `CREATE INDEX IF NOT EXISTS` → 幂等，**无需先撤**。

---

# OrzMusic 升级规程（实战：0.0.7 → 0.0.8）

OrzMusic 的工具链与 OrzMCDeploy **完全不同**，别照搬上面那套：

- **没有站点增量机制**（无 `compose.site.yaml`，`COMPOSE_FILE_EXTRA` 那套不适用）；
- 官方三脚本：`script/release-preflight.sh` → `release-upgrade.sh` → `release-smoke.sh`（+ `db-backup.sh`、`release-rollback.sh`、`release-scan.sh`），`Makefile` 只是包装 —— **本机 git-bash 没有 `make`，直接调 `./script/*.sh`**；
- `release-upgrade.sh` 顺序：预检 → 拉镜像 → DB 备份 → `compose stop app` → `compose run --rm migrate` → `up -d app`；
- 数据卷固定 `name: orzmusic` → **换包不丢库**；回滚 = 旧包目录 + `IMAGE_REF=<旧digest> ./script/release-rollback.sh`。

## 凭据迁移（本轮的关键坑）

`.env` 在**包目录内**（版本目录）→ 换包必丢，且官方要求 token 作为**环境变量**注入。正解：

- 单一真源放包外：`E:/deploy/site/orzmusic.env`（600），内含 `ADMIN_API_TOKEN`、`MUSIC_DIR`；
- 每次换包：`cp /e/deploy/site/orzmusic.env /e/deploy/orzmusic-deploy-<新版本>/.env`（600），
  运行命令时一律先 `set -a; . /e/deploy/site/orzmusic.env; set +a` 再导出 `IMAGE_REF`。
- `MUSIC_DIR` 必须设**绝对路径**（如 `E:/deploy/orzmusic-music`）：默认 `./keygenmusic` 相对包目录，换一版就多一个空目录，
  且 Docker 会按旧容器 bind 源自动补建幽灵目录（见 docker-service-lifecycle §10）。
- `IMAGE_REF` 必须显式导出：基础 `docker-compose.yml` 里的 `image: music-service:latest` 是占位，production 覆盖用 `${IMAGE_REF:?}`。

## 本机 Windows 三个坑（都会让官方脚本中止，预先处理）

1. **无头会话拉不了镜像**：Session 0 下 `docker pull` 必报 `A specified logon session does not exist`
   （`docker-credential-desktop.exe` 连不上凭据库；`DOCKER_CONFIG`/`--config`/`credsStore:""` 全都绕不过，`hello-world` 同样失败）。
   → 把官方脚本**整条投到交互会话**：`Register-ScheduledTask -LogonType Interactive -RunLevel Highest` + `Start-ScheduledTask`。
   **`.cmd` 必须纯 ASCII** —— 中文注释会让 `cmd.exe` 解析崩溃，任务静默 `LastTaskResult=1`、日志都不生成。
2. **MSYS 路径转换要分场景显式管**：
   - 跑官方脚本：`export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'`（否则容器内 `/tmp/x.dump` 被改写成 `C:/Users/.../Temp/x.dump` → `pg_dump` 失败、升级在第 3 步中止）；同时显式 `BACKUP_DIR=<绝对路径>`。
   - 跑 curl 冒烟：反过来 `env -u MSYS_NO_PATHCONV MSYS2_ARG_CONV_EXCL=` 开回转换（Hermes shell 全局关着转换时，原生 `curl.exe` 会把 `-o /dev/null` 当字面路径 → `exit 23`，冒烟静态节全 FAIL）。
3. **`python3` 垫片**：`release-smoke.sh` 11 处依赖 `python3` 且 `2>/dev/null || echo ""` 吞错，本机只有 `python`
   → 假 FAIL（health 字段全空，极易误读成“升级把服务搞坏了”）。垫片要点**三个都不能少**：
   - 文件名必须是 `python3.exe`：Windows 上 `python3` 会被**微软商店的 App Installer 别名**接管，执行它既不报错也无输出（排查陷阱）；
   - 内容必须是**真解释器**：`cp "$(python -c 'import sys;print(sys.base_prefix)')/python.exe" $SHIM/python3.exe`
     （venv 里的 `python.exe` 是启动器壳，直接 copy 跑不起来）；
   - 跑命令时用 **unix 风格 PATH 前缀**：`PATH="/c/Users/<user>/AppData/Local/Temp/shim:$PATH"`
     —— 写成 `C:\Users\...` 时 bash 搜不到，会静默回落到那个商店别名。

## 验收实测结果（0.0.7 → 0.0.8，2026-09-11）

- 官方 `release-upgrade.sh` `EXIT=0`；`release-smoke.sh` **14 项全 PASS**（`formats total=5533`、`search returned 8 results`）→ 换包不丢曲库。
- `#2` 自愈实测：**`docker kill` 不算数** —— 它是手动停止，属 `unless-stopped` 的例外，容器躺平不复活（实测 `exited` 40 秒、restarts=0）。
  正确姿势：让容器内 PID1 **异常退出** —— `docker exec orzmusic-app-1 sh -c 'kill -TERM 1'`
  （从**同一 PID 命名空间内**给 PID1 发信号：未装 handler 的信号会被内核忽略，故 `kill -9 1` 无效；SIGTERM 有 handler 才生效）。
  实测：`restarts 0→1`、`StartedAt` 更新、约 8 秒回到 `healthy` ✓。
- `#4` `docker port orzmusic-db-1` → 空；`#3` 正反例日志均命中（见 upstream-issues F0）。
- 反例容器（不带 token 的 `docker run`）会残留挂成 `unhealthy`，记得 `docker rm -f`。
- 两个 Windows 支持缺口已提上游：**#7**（冒烟脚本 python3 依赖假 FAIL）、**#8**（MSYS 下 db-backup 路径被改写）。

## 验收清单

- [ ] `/api/health` → `version=新版本`、`database/cas=healthy`、`adminApi=enabled`
- [ ] `docker inspect` app/db `RestartPolicy=unless-stopped`，且 `docker compose config`（**不带**本站覆盖）也解析出同值
- [ ] `docker port orzmusic-db-1` → **空**（production 覆盖不发布 5432）
- [ ] app 日志 `[NOTICE] ADMIN_API_TOKEN is set`；反例（一次性容器不带 token）出现 `[WARNING] ADMIN_API_TOKEN is not set … 503 admin_api_disabled`
- [ ] 容器 label `project.working_dir` = 新包路径；`cas-init` Exited(0)
- [ ] `Memory=536870912`、`OOMKilled=false`、实占远低于限额（0.0.8 实测 app 8.8MiB / db 40MiB）
- [ ] 清理一次性测试容器（反例容器会一直挂着 `unhealthy`）
