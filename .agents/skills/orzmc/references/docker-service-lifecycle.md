# Docker 服务清单 / 重启自愈 / MCSM 实例手动启停

> 适用：本机（Windows + Docker Desktop/WSL2）托管 orzmc + orzmusic 两套栈。

## 1. 当前拓扑（9 容器 + 两个 MCSM 实例）

| 容器 | 镜像 | 宿主端口 | restart |
|---|---|---|---|
| orzmc-mcsmanager-web | githubyumao/mcsmanager-web | caddy 反代 | unless-stopped |
| orzmc-mcsmanager-daemon | githubyumao/mcsmanager-daemon | —（24444 仅内网） | unless-stopped |
| orzmc-easybot | easyindie/easybot | —（8080 仅内网） | unless-stopped |
| orzmc-mariadb | mariadb | — | unless-stopped |
| orzmc-status | twinproduction/gatus | — | unless-stopped |
| orzmc-cloudflared | cloudflare/cloudflared | — | unless-stopped |
| orzmusic-app-1 | orzgeeker/orzmusic (digest 钉死) | 8080:8080 | 官方 no → 站点补 unless-stopped |
| orzmusic-db-1 | postgres:16-alpine | 5432:5432 | 官方 no → 站点补 unless-stopped |
| orzmusic-cas-init-1 | orzmusic | — | no（一次性 chown 任务，正常）|

卷：`orzmusic_cas_data`、`orzmusic_db_data`；网络：`orzmc_default`、`orzmusic_default`。

## 2. ``restart: unless-stopped`` 的含义与常见误判

- `unless-stopped` = Docker 守护进程重启（含 Docker Desktop 重启、设备重启后 Docker 起来）时**自动拉起**；只有人工 `docker stop` / `compose down` 过的容器才保持停着。
- 因此「设备重启后服务能自己回来」= 容器 restart 策略 + Docker 守护进程本身能起来，两环都要通。

### OrzMusic 官方包故意/默认写成 restart: no
官方 `docker-compose.yml` 与 `docker-compose.production.yml` 里 app/db 都没写 restart（= no），只显式给 cas-init 写了 no。后果实测：`orzmusic-app-1` 曾 **Exited(255) 挂了 12 小时无人知**。

修复（两层，缺一不可）：
```bash
# ① 已存在容器：即刻生效
docker update --restart unless-stopped orzmusic-app-1 orzmusic-db-1
# ② 将来重建容器时生效：站点覆盖文件（放版本目录之外，如 E:/deploy/site/xxx.restart.yml）
cd /e/deploy/<包目录>
IMAGE_REF=<digest> docker compose \
  -f docker-compose.yml -f docker-compose.production.yml -f ../site/xxx.restart.yml up -d
```
站点覆盖文件放 `E:/deploy/site/`（版本目录外），升版本不会被冲掉。

> **当前状态（2026-09-11）**：orzmusic 自 v0.0.8 起**官方 compose 自带 `restart: unless-stopped`**（app/db），
> 上文的 `site/orzmusic.restart.yml` 与 `docker update --restart` 两处补丁已**全部删除/撤下**。
> 这套覆盖手法只当“上游又漏 restart”时的备用手段；验证 compose 是否真的自带时，
> **只带两个官方文件**跑 `docker compose … config`（带上自己的覆盖文件会自欺）。

## 3. MCSM 实例「手动启停」：**必须停 daemon 后再改文件**

> 两个实例的完整拓扑与当前配置见 §7。

实例配置：`E:/orzmc/mcsmanager/daemon/data/InstanceConfig/<uuid>.json` → `eventTask`
- `autoStart`：**daemon 启动时是否拉起该实例**。要「手动启停」→ 置 `false`。
- `autoRestart`：实例运行中**进程异常退出时自愈**。与 autoStart 正交，改 autoStart 别顺手改它。

❗ **坑（实测）**：daemon 在内存里持有实例配置，运行中直接改 JSON 时会被它回写覆盖——
改了 `716c…json` 的 autoStart=false，5 分钟后被回写成 true，且 daemon 启动时真的把 PaperMC 拉起来了（还带起 Folia，有 ~60s 延迟，别只等 20 秒就下结论）。

✅ 正确流程：
```bash
docker stop orzmc-mcsmanager-daemon        # 先停 daemon（面板会闪断几秒）
docker stop MCSM-716c2f MCSM-8A932D        # 需要时优雅停实例（SIGTERM，MC 会存档退出）
# 改 InstanceConfig/*.json："autoStart": true -> false（先备份到 %TEMP%\orzmc_instancecfg_bak）
docker start orzmc-mcsmanager-daemon
sleep 120 && docker ps -a --format '{{.Names}}' | grep MCSM- || echo '实例未被拉起 ✓'
```
改完 ping 一下磁盘值确认没被回写（`grep -o '"autoStart": *[a-z]*' InstanceConfig/*.json`）。

📌 **`docker stop MCSM-<id>` 后容器会被直接移除**（daemon 以 `--rm` 方式跑实例），`docker ps -a | grep MCSM-` 返回空是**正常结果**、不是误删；实例仍登记在 `InstanceConfig/<uuid>.json`，面板里点启动即可重新创建容器。关服验收看**宿主端口不再监听**（25565/25566/19132…），不要看容器是否残留。

## 4. 重启自愈链条与**断点：Windows 自动登录**

| 环 | 现状 | 依据 |
|---|---|---|
| 容器自启 | ✅ orzmc 6 + orzmusic 2 均 unless-stopped | `docker inspect -f '{{.HostConfig.RestartPolicy.Name}}'` |
| Docker Desktop 随登录启动 | ✅ `AutoStart=True` + HKCU\Run 项 `Docker Desktop.exe` | `%APPDATA%\Docker\settings-store.json` |
| 设备重启后能否有人登录 | ❌ `Winlogon\AutoAdminLogon` 未配置 | 重启后会停在登录界面 → Run 项不执行 → 整条链断 |

→ 想让「设备重启后全自动恢复」，只能二选一：配自动登录（需存密码，家庭 7×24 机器可接受），或重启后人为登录一次。不要指望以 SYSTEM 在 Session 0 启 Docker Desktop：GUI 进程落 Session 0 会白屏/GPU 崩（见 `windows-session-isolation`）。

### 4b. Docker Desktop 整体停机后的恢复层次（实测形状）

Docker VM 挂掉再恢复时，各层回来的方式不同，别看到域名 200 就以为「都好了」：

| 层 | 停机后 | 判据 |
|:--|:--|:--|
| 入口容器（`orzmc-velocity` / `orzmc-caddy`） | ✅ 自动回来（`unless-stopped`） | `docker ps` 有 Up |
| MCSM 实例（`MCSM-716c2f` / `MCSM-8A932D`） | ❌ 不回来，且 `docker ps -a` 里**连容器都没有**（daemon 以 `--rm` 跑实例） | 需人工在面板启动 |

- 「实例容器消失了」不是误删，见 §3 的 `--rm` 说明；但**别只看容器**——要确认实例到底停没停干净，看实例 `logs/latest.log` 尾部：`Saving all player data` → `All RegionFile I/O tasks to complete` → `Awaiting termination of worker pool` = **优雅停机、数据安全**；有栈/`OutOfMemory` 才是崩溃。
- Docker 停机时刻从 `%LOCALAPPDATA%/Docker/log/vm/init.log*` 的轮转时间反推；先用 `LastBootUpTime` 排除「整机重启」这个先入为主的假设（实测出现过整机未重启、只有 Docker 挂 2 小时的情况）。
- 恢复动作是**人工**的：实例 `autoStart=false`（见 §3/§7），代理起来 ≠ 玩家能进。告诉老板三件事：入口是否绿、实例是否在跑、数据是否完好。

## 5. easybot SQLite 降级坑（属主不对 → 内存库 → 报错风暴）

> **上游已修（2026-09-11）**：EasyBot #121 的 [PR #122](https://github.com/EasyIndie/EasyBot/pull/122)（chmod 失败只 warn、不再中止）与 [PR #123](https://github.com/EasyIndie/EasyBot/pull/123)（内存回退不再静默：`/ready` 报 `message_storage: ephemeral` + 503）均已合入并发布到 `:latest`。
> **验证方法（可复现）**：隔离临时目录 + `--user 0` 造一个 root 属主 `gateway.db`，用新旧镜像各起一个一次性容器对比——旧镜像复现 `EPERM` → 内存库 → `no such table`；新镜像只记一条 warn 即正常迁移建库。
> **处置**：生产已于 **2026-10-02** 升级到含修复的镜像（OrzMCDeploy 0.0.6 = EasyBot v0.0.41）→ `chown` 绕过**已正式退场**：
> 0.0.38 时代遗留的 `root:root 777` 侧车文件（`auth.db-shm`/`auth.db-wal`）已用
> `docker exec -u 0 orzmc-easybot /bin/busybox sh -c 'chown -R 10001:10001 /var/lib/easybot/data && chmod 600 /var/lib/easybot/data/*'`
> 归位（现全为 `easybot:easybot 600`）；冷启动无 EPERM/降级告警，`/ready` 仍 `adapters_connected=2`。本节下面的验尸/修复步骤仅作历史参考。
> **运维信号**：存储降级只在 `/api/v1/ready` 暴露（`message_storage: ephemeral` + HTTP 503），`/api/v1/health` 的 body **没有**该字段；容器内**无 `wget`**，探针用 `curl`。

**症状**：`docker logs orzmc-easybot` 每 250ms 刷 `ERROR ... no such table: outbound_deliveries`（累计可到 20 万+），兼 `no such table: messages`。

**根因**：easybot 容器以 uid 10001 跑，启动时要“secure”已有 DB（改权限），而 `gateway.db` 及 `-wal`/`-shm` 若是 **root:root 777**（被以 root 跑过/还原过程写入过就是），非属主 chmod → `Operation not permitted`：
```
WARN easybot: Failed to initialize SQLite (/var/lib/easybot/data/gateway.db), falling back to in-memory:
     Failed to secure existing SQLite database: Operation not permitted (os error 1)
```
→ 降级到内存库（空库无表）→ 报错风暴；同时 `Authentication database failed: disk I/O error`。

**验尸要点**：`docker exec orzmc-easybot id`（确认 uid 10001）与 `stat -c '%U:%G %a %n' /var/lib/easybot/data/*.db`（对比：正常的 `auth.db` 是 `easybot:easybot 600`）。

**修复**（数据不丢，不要重建库）：
```bash
cp /e/orzmc/easybot/data/data/gateway.db* "$LOCALAPPDATA/Temp/easybot_db_bak/"   # 先备份
docker exec -u 0 orzmc-easybot sh -c 'chown 10001:10001 /var/lib/easybot/data/gateway.db*; \
  chmod 600 /var/lib/easybot/data/gateway.db*; rm -f /var/lib/easybot/data/gateway.db-wal /var/lib/easybot/data/gateway.db-shm'
docker restart orzmc-easybot && sleep 30
docker logs orzmc-easybot --since 120s 2>&1 | grep -cE 'no such table|in-memory'   # 应为 0
```
✅ 判成功：日志出现 `SQLite maintenance task started`，且无 `falling back to in-memory`；`/var/lib/easybot/data/gateway.db-wal` 重建。
⚠️ 只要有任何环节以 root 跑 easybot 镜像，就会再造出 root 属主的 DB 文件——遇到“报错风暴”先查属主。

## 6. 排查命令速查

```bash
docker ps -a --format '{{.Names}}\t{{.Status}}\t{{.Ports}}'
for c in $(docker ps -aq --format '{{.Names}}'); do printf '%-26s %s\n' "$c" "$(docker inspect -f '{{.HostConfig.RestartPolicy.Name}}' $c)"; done
# 注意：docker inspect/ps 同时给 --format 和 --quiet 会忽略自定义格式，只剩 ID
docker inspect -f 'State={{.State.Status}} OOMKilled={{.State.OOMKilled}} Mem={{.HostConfig.Memory}}' <c>
curl -s http://127.0.0.1:8080/api/health   # orzmusic：adminApi=disabled 说明 ADMIN_API_TOKEN 为空
```

> ⚠️ orzmusic 的 `ADMIN_API_TOKEN` 在本机**为空**（health 报 `adminApi:disabled`）：官方 `start.sh` 的取值链是 `.env` → Mac 的 `~/.bash_history`，迁到 Windows 后两者都不存在。需要重扫/导入曲库时得先补上该 token（可用 `.env` 放在部署包目录，start.sh 会 source 它）。
>
> **2026-09-11 全盘复查（已完成）**：部署包目录里**不存在 `.env`**，全盘（`E:/deploy`、`E:/orzmc`、hermes 目录）也未搜到任何带值的 `ADMIN_API_TOKEN`；应用日志也不会打印它；`docker inspect` 显示 `ADMIN_API_TOKEN=`（空）。→ **token 不可恢复，只能重新生成**（官方方式：`make generate-admin-token`，或 `openssl rand -base64 32`），写入部署包目录的 `.env` 后重启 app 容器。另：`script/docker-install.sh` / `native-common.sh` 都对空 token 报错中止，**只有日常入口 `start.sh` 无校验**（已作为 OrzMusic#3 的补充评论）。
>
> ✅ **2026-09-11 已重新生成并启用**：token 写入 `E:/deploy/orzmusic-deploy-0.0.7/.env`（官方机制，未改脚本；`chmod 600`）→ `./start.sh` 重建 app 容器 → `adminApi:enabled`。验证：无令牌 `401`（不再是 `503 admin_api_disabled`）、正确令牌 `200`、错误令牌 `401`。❗两条纪律：① 重建后**必须** `docker update --restart unless-stopped orzmusic-app-1 orzmusic-db-1`（否则官方 compose 默认 `no` 把自愈策略弄丢，即 OrzMusic#2）；② `.env` 在**版本目录内**，换包升级（新版本目录）时需手工拷过去（即 OrzMCDeploy#11 的动机）。
> 另：`start.sh` 会报 `volume "orzmusic_db_data"/"orzmusic_cas_data" already exists but was not created by Docker Compose` —— 迁移期手工建的卷缺 compose 标签，仅告警、无功能影响，数据仍在（即 `app` 的 `database:healthy` 已证实）。

## 7. MCSM 双实例拓扑（2026-09-11 实测）

| 实例 | UUID | 进程类型 | 镜像 | 端口 宿主:容器 | 内存 | JVM | autoStart | autoRestart |
|---|---|---|---|---|---|---|---|---|
| PaperMC | `716c2fb712154c36ba5ab0f1480d3f87` | docker | eclipse-temurin:25-jre | 25565:25565/tcp | 6144 | `-Xms4G -Xmx4G -jar paper` | **false**（手动） | **false**（手动，09-11 由 true 改） |
| FoliaMC | `8A932DD47F4D42AAAD6A6A9A5FAD2A91` | docker | eclipse-temurin:25-jre | 25566:25565/tcp | 4096 | `-Xms2G -Xmx2G -jar folia` | **false**（手动） | **false**（手动） |

> 2026-09-11：两实例 `eventTask` 已统一 `autoStart=false / autoRestart=false`（等 100 秒验证无回写、实例未被拉起）；备份 `*.bak-autorestart-<ts>` 在 InstanceConfig 目录。注：FoliaMC 的 `eventTask.ignore` 为 `true`（PaperMC 为 `false`），该键语义上游无文档，待查。

- 世界数据：`<DATA_ROOT>/mcsmanager/daemon/data/InstanceData/<uuid>/world`（**无 external world 挂载**，换世界就是换这个目录）。
- 实例 `cwd` 记录的是**容器内路径**（`/opt/mcsmanager/daemon/data/InstanceData/<uuid>`）→ daemon 必须带宿主侧映射：`MCSM_DOCKER_WORKSPACE_PATH=E:/orzmc/mcsmanager/daemon/data/InstanceData`（上游 issue #4；**0.0.3 的 compose.yaml 第 68 行已内建**）。
- ❗ `DAEMON_PORTS` 语义**只针对进程模式实例**；本机两个实例都是 docker 型（端口靠实例自身发布），`.env` 里若留 `25565:25565/tcp,...`，**daemon 一重建就会抢走 Paper 的 25565**（上游 issue #6）。2026-09-11 已把 `E:/orzmc/.env` 的该键**置空并加注释**；改动后 `orzmc.sh -d E:/orzmc validate` 通过。
- **autoStart 变更史**：原始 `False` → 2026-09-09 12:15 人为改 `True`（当时为了 Docker 重启后自动拉起）→ 2026-09-11 按用户要求改回 `False`（手动启停）。当时留的 `*.bak-autostart-20260909-121553` 备份已在清理中删除。
- ✅ **daemon 是 `docker run` 容器，这是官方设计（ADR-016）不是漂移**：Windows 下实例自挂载 target 含盘符冒号，compose 建不了 → `orzmc.sh up` 在 Windows 走“compose 列服务刨除 daemon + `win_daemon_run`”分支，且 `win_daemon_run` 是**幂等**的（已存在则跳过、只补网络别名 `mcsmanager-daemon`）。
- **2026-09-11 已按官方路径重建 daemon**（`docker rm -f orzmc-mcsmanager-daemon` → `./orzmc.sh -d E:/orzmc up`）：新容器 `restart=unless-stopped`、`--memory 512m`、`MCSM_DOCKER_WORKSPACE_PATH` 就位、别名就位、无 DAEMON_PORTS。面板 23 秒内自动重连（`密钥验证通过`）；实例没被拉起。重建前务必确认：① compose 带 `MCSM_DOCKER_WORKSPACE_PATH`（0.0.3 ✅）；② `.env` 的 `DAEMON_PORTS` 为空（✅）。
- 注：`orzmc.sh up` = `init` + compose up，而 `init` **不会覆盖已有文件**（`ensure_env_file` 明写“绝不覆盖已有 .env”；cloudflared config 仅在与 .env 不一致时重生并留备份）→ 可以放心重跑。另：compose 只在**服务配置哈希变化**时才会重建容器（实测 mariadb 因 healthcheck 修复被自动重建；web/easybot/status/cloudflared 配置等价 → 未自动重建，label 仍指旧路径）。2026-09-11 已用 `--force-recreate` 把 5 个 compose 容器的 label 全部刷成 `E:\deploy\orzmc-deploy-0.0.3`（见 §9）。
- 容器日志里的 `MCSM-716c2f` / `MCSM-8A932D` 就是这两个实例的容器（MCSM 自动命名），`docker ps -a | grep MCSM-` 可查实例是否在跑。

## 8. 容器日志：VM 内截断 + 全局轮转

- 实测 easybot 报错风暴两天把 json 日志写到 **162MB**（路径 = `docker inspect -f '{{.LogPath}}' <c>`，在 VM 内）。
- **零停机清空**（不重建容器）：
```bash
# 先确认是哪个容器：docker inspect -f '{{.Name}} {{.LogPath}}' <id>
docker run --rm -v /var/lib/docker:/hd alpine sh -c 'f=$(ls /hd/containers/<id>*-json.log); du -h $f; truncate -s 0 $f; du -h $f'
```
⚠️ 三条纪律：① **单独跑、给足 timeout**（混在大批量命令里超时时会把整批 docker 调用拖挂，实测一次 300s 超时）；② 用 `:ro` 只读挂载做检视，只有真的要截断才用读写；③ 截断后 `docker logs --tail` 可能短暂读不到旧行，用 `docker logs <c> --since 5m | wc -l` 验证新日志在写。
- **全局轮转**已写入 `C:\Users\WangA\.docker\daemon.json`（`log-opts: {max-size: 10m, max-file: 3}` + `log-driver: json-file`）。该文件是 Docker Desktop 的守护进程配置，**只在守护进程启动时读**→ 下次 Docker Desktop 重启后新建的容器才带上限；已存在的容器不受影响。
- `alpine:latest`（13MB）**故意保留**：这是唯一能从容器内检视 VM `/var/lib/docker` 的工具（`docker run --rm -v /var/lib/docker:/hd:ro alpine du -sh /hd/*`）。
- `docker system df` 的「可回收」会**骗人**：实例停着时 `eclipse-temurin:25-jre`（478MB）被算成可回收，它其实是两个 MC 实例的 Java 运行时，**不能删**。

## 9. 容器 label 对齐官方包（`--force-recreate`）

`orzmc.sh` 没有 force-recreate 子命令；compose 又只在**服务配置哈希变化**时重建容器，所以换包后多数容器的 `com.docker.compose.project.working_dir` label 仍指着旧目录（如 `E:\migration\orzmc-deploy-0.0.3-dev`）。手动拼一次即可（与 `compose_cmd()` 同构）：

```bash
cd E:/deploy/orzmc-deploy-<ver>
docker compose --env-file "E:/orzmc/.env" \
  -f "E:/deploy/orzmc-deploy-<ver>/compose.yaml" \
  -f "E:/deploy/orzmc-deploy-<ver>/compose.edge.cloudflare.yaml" \
  -f "E:/orzmc/compose.site.yaml" \
  --profile easybot --profile mariadb --profile status \
  up -d --no-deps --force-recreate mcsmanager-web status cloudflared easybot mariadb
```

❗❗ **必须带上 `-f "$DATA_ROOT/compose.site.yaml"`**（2026-10-02 踩中）：`--env-file` 一旦显式给出，compose 就**不再自动加载**
默认 `.env`；而飞书凭据（`FEISHU_APP_ID/SECRET`）只在**站点增量文件**里注入 easybot 的 `environment`。漏掉它的后果是
容器能正常起来、`/ready` 也 200，但日志只显示 `Started adapters: ["qq"]` + `Skipping adapter 'feishu' — credentials not set`
——就是 compose.site.yaml 里写的那个「升级后机器人不工作了」。**判据：`/api/v1/ready` 的 `adapters_connected` 必须等于 2（qq+feishu）**，只看状态码会漏。
`orzmc.sh up` 不存在此问题（`compose_cmd()` 会自动 `collect_site_override_files` 追加）。

四条纪律：① 路径必须用**原生正斜杠 Windows 路径**（MSYS 的 `/e/...` 会让 compose 解析失败）；② `--no-deps` 避免连带重建 mariadb（要对齐 mariadb 就把服务名显式列上）；③ **不要把 `mcsmanager-daemon` 列进去**（Windows 下归 `win_daemon_run` 管，ADR-016；它是 `docker run` 容器，**本来就没有 compose 标签**，无需对齐）；④ 重建后逐个核对 label，并回查 `adapters_connected`。服务名用 `compose config --services` 取。

实测 2026-09-11：5 个 compose 容器全部刷成 `E:\deploy\orzmc-deploy-0.0.3`，重建后四端点仍 200、easybot `healthy` 且 0 条 SQLite 报错、两个 MCSM 实例未被拉起。

## 9b. ❗ cloudflared 隧道静默宕机：Clash TUN 劫持 UDP → QUIC 连不上边缘（2026-10-09 实测）

**症状**：`docker ps` 里 9 个容器全 `Up`、health 全绿，但 `https://mcs.{SERVER_NAME}.cn` / `easybot.` / `orzmcs.` 全部不可达（curl 000 / 浏览器 530）。
**判据**：`docker logs orzmc-cloudflared | grep -E 'Registered tunnel connection|ERR'` ——若最后一条 `Registered` 是几天前、之后每小时几十条
`Failed to dial a quic connection error="failed to dial to edge with quic: timeout: no recent network activity"` + `no free edge addresses left`，就是本故障。
容器自身看不出异常（`restart=unless-stopped`、进程活着、只是重连循环）。

**根因**：本机 Clash TUN（`fake-ip` + UDP 劫持，见 `bedrock-raknet-diagnosis` 技能）让**所有公网 UDP 出站收不到回包**。
cloudflared 默认走 **QUIC(UDP:7844)** → 控制连接超时；而 **TCP 出站正常**（容器内 `nc -z region1.v2.argotunnel.com 7844` OK，plain http 经代理 204）。
注意 compose 里的 `dns: [223.5.5.5, 1.1.1.1]` 覆盖**挡不住** TUN 的 `dns-hijack`——日志里边缘 IP 仍是 `198.18.x.x` 假 IP，这是正常现象，别据此判断 DNS 配置失效。

**修法（已落地）**：强制隧道走 TCP。写站点增量 `$DATA_ROOT/compose.site.yaml`（不改包内文件）：
```yaml
services:
  cloudflared:
    environment:
      TUNNEL_TRANSPORT_PROTOCOL: "http2"
```
→ `./orzmc.sh -d E:/orzmc validate && ./orzmc.sh -d E:/orzmc up`（只会 `Recreate` cloudflared，其余容器不动）
→ 日志出现 `Initial protocol http2` + `Registered tunnel connection … protocol=http2` 即恢复。
**隔离验证法**（不动生产）：同配置另起一个一次性容器 `docker run -d --name cf-http2-test --network orzmc_default \
 -e TUNNEL_TRANSPORT_PROTOCOL=http2 -v E:/orzmc/cloudflared:/etc/cloudflared:ro <同一 digest> tunnel --config … run` ——
同一 tunnel 允许两个连接，起来即等于临时恢复公网入口，验证完 `docker rm -f`。

**验证纪律**：① Windows 宿主 `curl https://<域名>` 会因 schannel `CRYPT_E_REVOCATION_OFFLINE` 假失败（本地证书吊销检查出不去），
用 `curl --ssl-no-revoke` 或 `docker run --rm alpine wget -S https://<域名>/` 复核；
② 隧道恢复后要回查 MCSM 节点：`docker logs orzmc-mcsmanager-web` 出现 `远程节点 … 密钥验证通过`；
③ `orzmusic.{SERVER_NAME}.cn` 返回 **404** 属正常——该域名不在本隧道 ingress（只有 mcs/easybot/mcs-node/orzmcs 四条），ccatch-all `http_status:404` 兜底。

## 9c. ❗ cloudflared 长跑僵死：容器 Up、边缘网络实测全通、隧道却持续重连（2026-10-12 实测）

**症状**：`mcs.{SERVER_NAME}.cn` / `easybot.{SERVER_NAME}.cn` / `orzmcs.{SERVER_NAME}.cn` 全部 **530**，
但 `docker ps` 里 9 个容器全 `Up`、health 全绿（与 §9b 表现一模一样，但根因不同）。

**判据**：`docker logs orzmc-cloudflared | grep -E 'Registered|ERR' | tail` —— 最后一条
`Registered tunnel connection` 停在几天前，之后是**持续重连循环**，错误形态会随时间演变：
`DialContext error: dial tcp <fake-ip>:7844: i/o timeout` → `TLS handshake with edge error: EOF`
→ `there are no free edge addresses left to resolve to`。

**必须先排除网络（否则会误改 Clash/防火墙）**：
```bash
# ① 宿主直测边缘（含 ALPN h2 与后量子曲线）——全 CONNECTED 即 TCP+TLS 通
S=region1.v2.argotunnel.com
for opt in "" "-alpn h2" "-groups X25519MLKEM768 -alpn h2"; do
  echo | timeout 20 openssl s_client -connect $S:7844 -servername $S $opt 2>&1 | grep -E "CONNECTED|error" ; done
# ② 容器内 TLS——报 certificate verify failed 就说明握手已经成功（Origin CA 不在信任库而已）
docker exec orzmc-easybot sh -c 'nc -z -w 6 region1.v2.argotunnel.com 7844 && echo TCP OK; wget -q -T 12 -O /dev/null https://region1.v2.argotunnel.com:7844/'
```
（cloudflared 镜像 distroless 无 shell，探针借用同网络的 easybot 容器；easybot 有 busybox
`nc`/`wget`，**没有 curl**。）

**根因**：不是网络、不是 Clash TUN、不是配置 —— 是 **cloudflared 进程长跑数日后内部状态陈旧**
（fake-ip/边缘地址解析与连接状态未自愈），隧道再怎么重连也起不来。

**修法（最小动作）**：`docker restart orzmc-cloudflared` → **25～45 秒内**日志出现
`Registered tunnel connection … protocol=http2`，三个域名立刻 200。不需要重建容器、不改配置。

**自愈（已落地 2026-10-12）**：cron job `b0621d7056c1`（`orzmc-tunnel-guard`，每 10 分钟，
no_agent watchdog）+ 脚本 `~/AppData/Local/hermes/scripts/orzmc_tunnel_guard.py`：
端到端探测 `https://mcs.{SERVER_NAME}.cn/`（宿主 `curl.exe --ssl-no-revoke` + 容器内 `wget` 双通道，
任一成功算健康；两者都失败再复测一次）→ 仍不可达则 `docker restart orzmc-cloudflared` →
45 秒后复测 → 恢复/失败都把文本投递到飞书；**健康时零输出、零打扰**。
15 分钟冷却（state `orzmc_tunnel_guard.json`）防重启风暴；状态日志 `orzmc_tunnel_guard.log`。
测试用 `ORZMC_TUNNEL_GUARD_DRYRUN=1|2` 模拟「重启后恢复 / 重启后仍失败」分支，不真重启。

> ⚠️ §9b 与 §9c 的区别：§9b = QUIC 被 TUN UDP 劫持（错误是 `no recent network activity`，
> 修法 = 强制 `TUNNEL_TRANSPORT_PROTOCOL=http2`）；§9c = http2 已配却仍失败
> （错误是 `TLS handshake with edge error: EOF`，修法 = 重启容器）。
> 两者都表现为「容器全绿但域名 530」，先看日志里的错误文本再决定动作。

## 10. 坑：移动/重命名部署包目录后，旧路径会“复活”为空目录

**现象**：`E:\migration` 被改名成 `E:\deploy` 后，隔一段时间又出现，里面只有空目录树（如 `migration/orzmusic-deploy-0.0.7/keygenmusic`，0 字节、无文件）。

**机制**：Docker **会为 bind mount 自动创建缺失的宿主源目录**。旧容器（改名前的 pack 路径创建的）在容器配置里死死记着旧源路径（Windows 上是 `/run/desktop/mnt/host/e/migration/...`）——只要它被 `docker start` 一次（哪怕只是为了修别的故障），Docker 就把那串旧目录**重新建出来**。orzmusic 的 `app` 服务挂载 `${MUSIC_DIR:-./keygenmusic}`，且包内真有个 `keygenmusic/` 目录 → 正是复活的路径形状。

**判定**：
```bash
for c in $(docker ps -a --format '{{.Names}}'); do docker inspect "$c" --format '{{.Name}} {{range .Mounts}}{{.Source}} {{end}}'; done | grep -i 旧路径
```

**处置**：先把引用旧路径的容器**重建**（让挂载源指向新路径），确认上面这条无输出后，再删旧目录——否则下次启动旧容器它又回来。本例中 `./start.sh` 重建 app 后彻底消失。

**纪律**：移动/重命名任何被容器 bind mount 的目录后，**当次就把相关容器重建**，不要留“以后再对齐”。
