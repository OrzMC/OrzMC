# 平台层迁移（orzmc-deploy 栈换机 / Windows 全新部署）

> 2026-09-09 Mac→Windows 迁移实录。触发：把 orzmc-deploy 平台栈（MCSM web/daemon + EasyBot + cloudflared 隧道 + MariaDB + Gatus）+ orzmusic 迁到新机。
> 数据权威源 = 迁移包；**本机无历史数据时 = 全新安装**（Docker Desktop/WSL/部署包全要从零）。

## 资产关系（迁移前必读）

- **DATA_ROOT**（Mac `/Users/Shared/orzmc`，Win `E:/orzmc`）：含 `.env`（全部密钥）、mcsmanager 数据+双实例、worlds、easybot 数据、cloudflared 凭据、mariadb 数据、status 配置。**备份=打包 DATA_ROOT**
- **部署包**（运行时非数据，镜像 digest 锁定 compose 自拉）：**Windows 现落点 `E:/deploy/`**（2026-09-11 由 `E:/migration/` 改名，以反映用途=部署包目录）——orzmc-deploy-**0.0.4** + orzmusic-deploy-**0.0.10**（2026-09-11 确认新版无问题、上游 issue 全关后**旧版本目录/包/旧镜像/旧 DB dump 已全部清理**，目录内只留这两个生产包 + `site/` + 问题清单）；Mac 侧原路径 `~/Services/<svc>-deploy-<ver>`
- orzmusic 数据在 **Docker 命名卷**（orzmusic_cas_data/orzmusic_db_data），不在 DATA_ROOT → 单独卷导出

## 端口架构（关键，防 AI 误解）

| 服务 | 容器内端口 | 宿主发布 |
|---|---|---|
| easybot | 8080（EASYBOT_PORT） | **不发布**（仅 expose，cloudflare/local 档） |
| status/Gatus | 8080（STATUS_PORT） | 不发布 |
| mcsmanager-web | 23333 | 不发布 |
| mcsmanager-daemon | 24444 | 不发布 |
| **orzmusic** | 8080 | **`8080:8080`（宿主 8080 唯一占用者）** |

- cloudflare 档（生产，EDGE=cloudflare）全部服务**只 expose 不发布宿主端口**，cloudflared 出站隧道内网直达；lan 档才发布宿主端口且 easybot 用 `LAN_EASYBOT_PORT`（默认 **18091**）特意避开 8080（ADR-012）
- ⚠️ **"插件直连 http://easybot:8080" = 容器内网地址（orzmc_default 网络），不是宿主映射**——AI 智能体易误解成要 -p 8080:8080
- Mac 共存方案：宿主 8080 整个让给 orzmusic

## ⚠️ Windows 端口冲突坑（2026-09-09 实测）

Windows 全新部署报「orzmusic 8080 与 easybot 8080 冲突」根因：**Windows 上残留独立部署的旧 easybot 服务（8 月验收遗留，容器体系外）占宿主 8080**。解决：清掉独立服务/进程（Windows 服务+计划任务一并移除防自启），用容器内 easybot（数据来自迁移包还原）。修复验证：
```powershell
netstat -ano | findstr :8080     # 应无 LISTEN 残留
docker ps --format "{{.Names}} {{.Ports}}" | grep easybot   # Ports 应为空（不发布）
```

## 打包步骤（源机，栈已停状态）

```bash
# 1. 起引擎等就绪
open -a Docker; for i in $(seq 1 90); do docker info >/dev/null 2>&1 && break; sleep 2; done

# 2. orzmusic 双卷导出（容器静止 = 最一致，无需 up 服务）
docker run --rm -v orzmusic_cas_data:/d -v ~/orzmc-migration:/out alpine sh -c "tar czf /out/orzmusic-cas.tgz -C /d ."
docker run --rm -v orzmusic_db_data:/d  -v ~/orzmc-migration:/out alpine sh -c "tar czf /out/orzmusic-db.tgz -C /d ."

# 3. orzmc 一致性备份（必须等 mariadb READY，见坑）
./orzmc.sh -d /Users/Shared/orzmc up
for i in $(seq 1 60); do docker exec orzmc-mariadb mariadb-admin ping >/dev/null 2>&1 && break; sleep 2; done
./orzmc.sh -d /Users/Shared/orzmc backup --stop   # down→打包→自动 up；产物 $(dirname DATA_ROOT)/orzmc-backups/

# 4. 停栈恢复原状 + 可选 quit Docker Desktop（pkill -9 -f /Applications/Docker.app 清残留）

# 5. 组装迁移包：mv 归档 + cp 部署包目录 → 外层 tar 不带顶层目录前缀
tar -cf ~/Downloads/orzmc-migration-<date>.tar -C ~/orzmc-migration <归档> <tgz...> -C /e/deploy orzmc-deploy-0.0.3 orzmusic-deploy-0.0.7
```

## ⚠️ backup.sh dump 竞态坑（2026-09-08 实测）

- `dump_db_logical`：mariadb **未运行**时（--stop 模式）会自己拉起并 `wait_for_mariadb`；但**容器已在跑时不等待就绪直接 dump**
- 若刚 `up` 完立刻 backup，mariadb 还在冷启动 → dump 连接失败 → `rm -f dump_file` + warn（**warn 常被输出截断不易察觉**），归档只剩冷数据目录
- **必须等 mariadb ping 通再 backup**（`docker exec orzmc-mariadb mariadb-admin ping`——ping 不需要认证）
- 验证归档含 dump：`tar tzf <归档> | grep -E "database/dumps/mariadb-all|^<root>/.env$"`
- dump 失败不致命（mariadb 数据目录 = 权威冷数据，down 时干净停机即一致），但 Windows 还原多一层保险更稳

## Windows 全新环境还原步骤

```bash
# 0. 环境（全新）：Docker Desktop + WSL2（Windows 功能→wsl --update→WSL Integration）；.wslconfig networkingMode=mirrored + wsl --shutdown；vhdx 建议迁数据盘
# 1. orzmc 还原（部署包内 Git Bash/MSYS 跑 .sh）
bash restore.sh -d E:/orzmc <orzmc-backup-*.tar.gz> --force   # 自动改 .env DATA_ROOT
./orzmc.sh -d E:/orzmc validate && ./orzmc.sh -d E:/orzmc up  # Windows 下 daemon 由脚本 win_daemon_run 自动 docker run（ADR-016）
# 2. orzmusic（Windows 无 bash_history，ADMIN_API_TOKEN 留空 = adminApi disabled，与 Mac 现状一致）
docker volume create orzmusic_cas_data; docker volume create orzmusic_db_data
docker run --rm -v orzmusic_cas_data:/d -v /e/deploy:/in alpine sh -c "tar xzf /in/orzmusic-cas.tgz -C /d"
docker run --rm -v orzmusic_db_data:/d  -v /e/deploy:/in alpine sh -c "tar xzf /in/orzmusic-db.tgz -C /d"
cd /e/deploy/orzmusic-deploy-0.0.7
IMAGE_REF="ghcr.io/orzgeeker/orzmusic@sha256:a74ad4d62b4bfb1638fc916281cd1119856d412a6b4fb225fa748a00ae201dd3" \
  docker compose -f docker-compose.yml -f docker-compose.production.yml up -d
# 3. 验证：8 容器 Up/healthy + 4 端点 200（mcs/easybot/orzmcs/mcs-node.{SERVER_NAME}.cn）+ curl 127.0.0.1:8080/api/health
```

### ⚠️ Windows 还原实测补充（2026-09-09 全流程跑通，勿跳过）

**坑 A：`restore.sh` 在大归档上必崩（SIGPIPE / exit 141）——上面第 1 行别直接跑。**
`restore.sh` 第 56 行 `top="$(tar tzf "$ARCHIVE" | head -n1)"` 对 >~2G 归档必触发：`tar` 持续写列表、`head -n1` 读一行即退关闭管道 → tar 收 SIGPIPE；配脚本顶部 `set -euo pipefail` → 整脚本退出 141（后台/前台均现）。Mac 小归档不触发、**2.36G 必触发**。未改仓库脚本，改为等价的受控手工还原：
```bash
python -c "import tarfile;print(tarfile.open('E:/deploy/<归档>.tar.gz','r:gz').getnames()[0])"  # 看顶层目录(应=orzmc)
cd /e && tar -xzf E:/deploy/<归档>.tar.gz    # 顶层=orzmc → 直接落 E:/orzmc（无 head 管道，不 SIGPIPE）
cd /e/orzmc && cp .env .env.bak-restore && sed 's#^DATA_ROOT=.*#DATA_ROOT=E:/orzmc#' .env.bak-restore > .env  # 改 DATA_ROOT(留备份)
grep -E "^(DATA_ROOT|EDGE=)" .env               # 校验: DATA_ROOT=E:/orzmc、EDGE=cloudflare、无 /Users/Shared 残留
cd /e/deploy/orzmc-deploy-0.0.3 && ./orzmc.sh -d E:/orzmc validate
```
> 建议报上游：OrzMCDeploy `restore.sh` 的 `tar tzf | head -n1` 应改成不 SIGPIPE 的取顶层方式（大归档迁移是 restore.sh 的既定用途）。
> ✅ **已报并已修（官方 0.0.3 / 2026-09-10，CHANGELOG #5）**：官方包改成 `top="$( { tar tzf "$ARCHIVE" | head -n1; } || true )"`。**用 `E:/deploy/orzmc-deploy-0.0.3/restore.sh` 可直接跑，上面这套手工还原步骤仅在用旧包时保留**。

**坑 B：mariadb 还原冷数据后 healthcheck 报 unhealthy（`Access denied for user 'mysql'` no password）。**
还原自 Mac 的 `database/mariadb` 冷数据目录**缺镜像首次 init 才创建的 `mysql@localhost` unix_socket 账号**；compose healthcheck `healthcheck.sh --su-mysql` 走 socket 以该用户连 → 失败。**库本身经 TCP 用 root / mc 凭据完全正常，仅 healthcheck 误报**（web 面板/节点不受影响）。修复 = 补该账号（等价镜像 init，不动 compose）：
```bash
docker exec orzmc-mariadb sh -c 'mariadb -uroot -p"$MARIADB_ROOT_PASSWORD" -e "CREATE USER IF NOT EXISTS \"mysql\"@\"localhost\" IDENTIFIED VIA unix_socket; GRANT ALL PRIVILEGES ON *.* TO \"mysql\"@\"localhost\" WITH GRANT OPTION; FLUSH PRIVILEGES;"'
docker inspect --format '{{.Name}} {{.State.Health.Status}}' orzmc-mariadb   # → healthy
```
> ✅ **已报并已修（官方 0.0.3 CHANGELOG #7）**：healthcheck 改 root 经 unix socket + `MARIADB_ROOT_PASSWORD` 做 innodb 就绪查询。本机已手工补过 `mysql@localhost` 账号且现为 healthy，无需回退。

**还原验证结果（Windows 实测）**：8 容器全 Up（orzmc web/daemon/easybot/mariadb/status/cloudflared + orzmusic app/db）全 healthy；4 公网端点 `mcs/easybot/orzmcs/mcs-node.{SERVER_NAME}.cn` 全 200；orzmusic `curl 127.0.0.1:8080/api/health` → `{"status":"ready","database":"healthy","cas":"healthy","adminApi":"disabled",...}`；daemon 加载双实例、世界数据就位、保持停止。

## 传输：macOS SMB 共享（2026-09-09 实测坑）

- macOS 共享名 = **目录显示名（中文系统 = 「下载」）**，不是路径名 Downloads → Windows 访问 `\\<IP>\下载`（或浏览根目录找共享）
- SMB 认证被拒（密码正确也拒）根因：文件共享「选项」里**没启用 SMB 账户**——系统设置→通用→共享→文件共享→选项→勾「使用 SMB 共享文件」+ 勾选账户 + 输入账户密码启用
- 排障定位法：Mac 本地 `smbutil view //bot@<IP>`（密码交互，pty+submit）；能 sudo 不能 SMB = 共享配置问题非密码问题
- 局域网兜底：python3 -m http.server <port> --directory <dir>（只暴露迁移文件目录，用后即关）

## 当前状态（2026-09-09 迁移完成）

- Mac：源机已停（容器 0 / 引擎停 / 隧道无）；迁移归档（orzmc-backup-*.tar.gz + cas/db tgz，~2.9G）**已随 E 盘清理删除**，双部署包现于 `E:/deploy/`
- Windows `E:/orzmc`：还原完成，8 容器健康运行（orzmc web/daemon/easybot/mariadb/status/cloudflared + orzmusic app/db），4 公网端点 200；容器 easybot 接管 `easybot.{SERVER_NAME}.cn`，隧道由本机 cloudflared **单点**接管
- orzmusic `adminApi: disabled`（与 Mac 一致）；测试服双实例（papermc-test/folia-test）**保持停止**（世界数据就位于 daemon `InstanceData/`）
- 遗留：`E:/orzmc/.env.bak-restore`（DATA_ROOT 改写前备份，2026-09-11 已删）；旧宿主 easybot 残留 `~/.easybot`（已脱离服务，可删）；`E:/migration` 迁移归档 ~2.9G **已删**，目录已改名为 `E:/deploy`
- **运维包版本（2026-09-11）**：生产包 = `orzmc-deploy-0.0.4`（旧 0.0.3 目录已删；容器标签 `com.docker.compose.project.working_dir` 实测均为 `E:\deploy\orzmc-deploy-0.0.4`）；OrzMusic = `orzmusic-deploy-0.0.10`。**站点增量（官方 tarball 不含，升级勿丢）：`E:/orzmc/compose.site.yaml`**（飞书凭据等，官方 override 挂载点，ADR-022/issue #11）——不再往包内 compose.yaml 写增量
- **清理记录（2026-09-11）**：删 `orzmc-deploy-0.0.3`、`orzmusic-deploy-0.0.{7,8,9}`、两个旧 `.tar.gz`、`upgrade-20260911/`（含带凭据的 `.bak`）、`site/`（含 `orzmusic.env` 与 `backups/`）、`/e/orzmc/database/dumps/mariadb-all-20260908-*.sql`、3 个旧 orzmusic 镜像（~3.4GB）、`E:/e/`（gh 下载 MSYS 路径坑留下的野生目录）。清理后 `E:/deploy` 只剩两个生产包 + 问题文档。**凭据真源自此=当前生产包内 `.env`**（删 `site/orzmusic.env` 前已哈希比对与包内一致）。⚠️ **坑：`gh release download --dir /e/deploy` 在 MSYS 下会失败但已在盘上留下字面路径 `E:\e\deploy\`（包体写进去了，exit 2 只是后续 ls 报错）——用 `--dir 'E:/deploy'` 后记得查有没有生野生目录。注意：Docker 镜像回收只在 VM 内生效，`docker_data.vhdx` 不会自动缩，E 盘可用空间不一定立即变
- 隧道单点铁律：源机停 + 目标机 cloudflared 接管 {SERVER_NAME}.cn，**严禁双跑串流量**

## OrzMusic 生产升级（Windows 实操，2026-09-11 起）

站点现状（2026-09-11 清理后）：生产包 `E:/deploy/orzmusic-deploy-<ver>/`；**凭据真源 = 当前生产包内的 `.env`**（只有 `ADMIN_API_TOKEN` + `MUSIC_DIR` 两键，新包靠从上一个包目录拷 `.env` 继承；`site/orzmusic.env` 已于 2026-09-11 删除）；DB 备份落点 `E:/deploy/site/backups`（**目录无需预建**：`db-backup.sh` / `release-preflight.sh` 都自带 `mkdir -p`；2026-09-11 已把 `E:/deploy/site` 整个删除）。数据在 Docker 命名卷 `orzmusic_cas_data` / `orzmusic_db_data`（`docker-compose.yml` 钉死 `name: orzmusic`，按版本目录切换不新建空库）。

```bash
# 1. 取包（gh 是原生程序：--dir 写不出 MSYS 路径，必须用 E:/… 原生路径）
gh release download v<ver> --repo OrzGeeker/OrzMusic \
  --pattern 'orzmusic-deploy-<ver>.tar.gz' --dir 'E:/deploy' --clobber
cd /e/deploy && tar -xzf orzmusic-deploy-<ver>.tar.gz
cp orzmusic-deploy-<上一个版本>/.env orzmusic-deploy-<ver>/.env   # 凭据从上一生产包搬入（唯一真源）

# 2. 升级（Windows 没有 make，直接调脚本；三变量必须显式传）
cd orzmusic-deploy-<ver>
set -a && . ./.env && set +a                              # 拿到 ADMIN_API_TOKEN（避免手抄密钥）
export IMAGE_REF='ghcr.io/orzgeeker/orzmusic@sha256:<digest>'
export BACKUP_DIR='E:/deploy/site/backups'
bash ./script/release-upgrade.sh                           # preflight→pull→backup→stop→migrate→start
EXPECTED_VERSION=<ver> SERVICE_URL=http://localhost:8080 bash ./script/release-smoke.sh
```

⚠️ **preflight 单独先跑必假 FAIL「Database is not reachable」**：`IMAGE_REF` 未导出时 compose 无法插值，`exec db pg_isready` 直接报错 → 必须带 `IMAGE_REF` 跑（upgrade 内部会自动带上）。

✅ **smoke 第 3 节假 FAIL 已在 0.0.10 修掉**（上游 issue #10 CLOSED）：旧版脚本用 `-o /dev/null`，mingw curl 写 `/dev/null` 报 `curl: (23) client returned ERROR on write` → 被 `||` 判成「读不到响应头」且 `PASS=false` 后第 4/5 节静默无输出。**0.0.10 起按平台选空设备（MSYS 用 `NUL`）、第 4/5 节无条件执行，实测 14/14 PASS / exit 0**。排查时如遇同类「脚本失败但服务正常」，先手工 `-o NUL` / `-I` 复核再下结论；定位到脚本自身问题→不改上游脚本，提 issue（用户偏好原版实现）。

升级后必查：`/api/health` 的 `version` / `adminApi`（`adminApi=disabled` 说明 `ADMIN_API_TOKEN` 没进容器，升完功能静默缺失）+ 容器 `restart=unless-stopped` / `health=healthy`。
