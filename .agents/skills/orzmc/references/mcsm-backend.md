# MCSM 后端（MCSManager 面板）

> 已适配：{SERVER_HOST}:23333（2026-08-03 实测）
> 实例：jockerhubMC服务器（daemonId + instanceId 存 `~/.hermes/.env`：`MCSM_DAEMON_ID` / `MCSM_INSTANCE_ID`）
> **2026-09-11 现状**：daemon 跑在**本机 Docker**（`orzmc-mcsmanager-daemon`，DATA_ROOT=`E:/orzmc`）；两个实例 PaperMC(25565)/FoliaMC(25566) 均为 docker 型（temurin:25-jre），**已改手动启停**（`autoStart=false`）——拓扑与操作见 `docker-service-lifecycle.md` §3/§7。旧 Windows 宿主（daemon 跑在 `C:\Users\Administrator\...`）已废弃，勿再引用。

## 端点表（全部实测 2026-08-06 全面复核）

| 动作 | 端点 | 实测 | 说明 |
|:----|:----|:----:|:----|
| 实例状态 | `GET /api/instance?daemonId={d}&uuid={i}` | ✅ 200 | 字段见下 |
| 日志 | `GET /api/protected_instance/outputlog?daemonId={d}&uuid={i}` | ✅ 200 | |
| 玩家列表 | 从日志「当前在线(n/max)」行解析 | ✅ | |
| 登录换 token | `POST /api/auth/login` {username,password} | ✅ 200 | |
| **start/stop/restart** | **`GET /api/protected_instance/open` / `stop` / `restart`** | ✅ 实测 | |
| **command** | **`GET /api/protected_instance/command?command={cmd}`** | ✅ 实测 | |
| **读文件** | `POST /api/files/download?file_name={路径}` → addr+password → `GET http://{addr}/download/{pwd}/{文件名}` | ✅ 实测 | **必须带 daemonId+uuid**（缺 → 403「参数不正确」）|
| **写文件** | **`PUT /api/files/?daemonId={d}&uuid={i}` body `{"target":"/路径","text":"内容"}`** | ✅ **200 实测** | ⚠️ **只能写已存在文件**（新文件 → 500 Illegal access path）；**必须带 daemonId+uuid**；body 字段是 `text` |
| **删除文件/目录** | **`DELETE /api/files/?daemonId={d}&uuid={i}` body `{"targets":["/路径1","/路径2"]}`** | ✅✅ **200 实测删文件+目录都成功** | 删后必须真实 GET 验证（daemon 偶发假 200）|
| **新建目录** | `POST /api/files/mkdir?daemonId={d}&uuid={i}` body `{"target":"/路径"}` | ✅ 200 实测 | |
| 上传 | `POST /api/files/upload?upload_dir={目录}&daemonId={d}&uuid={i}` → daemon `/upload/{pwd}` multipart | ✅ 实测 | |
| **列目录** | `GET /api/files/list?target={路径}&page=0&page_size=50&file_name={过滤词}` | ⚠️✅ **可用但需 fileName** | **必须带 `page`（从 0 开始！）+ `page_size` + `file_name` 三个参数**；`file_name` 是**过滤词**（不填 → total=0 items 空，daemon 全量列出 bug）；`type` 字段 0=目录 1=文件；偶发 `Remote end closed connection`（重试即可）。源码（MCSManager Daemon `system_file.ts` list 实现）实证 |
| **touch 新建文件** | `POST /api/files/touch` body `{"target":"/路径"}` | ✅ 200 实测 | 2026-08-06 新发现 |
| **copy 复制** | `POST /api/files/copy` body `{"targets":[["源","目标"],...]}` | ✅ 200 实测 | ⚠️ **targets 是二维数组** `[["源","目标"]]`（源码注释 `// [["a.txt","b.txt"],["cxz","zzz"]]`）——一维数组会 500 |
| **move 移动** | **`PUT /api/files/move`** body `{"targets":[["源","目标"],...]}` | ✅ 200 实测 | ⚠️ **方法必须是 PUT**（POST → 500）+ **targets 二维数组**（同 copy）——2026-08-06 修正「move 不可用」误判 |
| **compress 压缩** | `POST /api/files/compress` body `{"source":"/输出.zip","targets":[文件数组],"type":1,"code":"utf-8"}` | ✅ 200 实测 | **type=1 压缩**（promiseZip：source=zip输出路径, targets=文件数组）；**type=0 解压**（promiseUnzip：source=zip路径, targets=目标目录字符串）；异步任务（fileLock 计数） |
| **URL 下载** | `POST /api/files/download_from_url` body `{"url":"...","file_name":"/路径"}` | ✅ **200 实测** | 2026-08-06 实测：GitHub raw → 5s 下载 1493B 成功；异步任务返回 taskId；`download_from_url_stop` 可停止 |

⚠️ **操作端点全部是 GET + `/api/protected_instance/` 前缀**（不是 POST /api/instance/xxx！）——这是 MCSM 10 的坑，首次按 POST 调用全 404。

**认证**（必需头：`Content-Type: application/json; charset=utf-8` + `X-Requested-With: XMLHttpRequest`）：
- **apikey 方式**：`?apikey=$MCSM_API_KEY`（实测有效，**普通用户权限**）
- token 方式：`POST /api/auth/login` 返回 token（`?token=` 与 Bearer 均未验证通过，待测）

## 适配器脚本

`scripts/adapters/mcsm.sh`（status / players / logs 只读 ✅ 实测；start / stop / restart / command / kill 内置玩家检查，有玩家在线自动拒绝；**restart / command / kill 已实测通过**）：

```bash
# 只读
~/.hermes/skills/gaming/orzmc/scripts/adapters/mcsm.sh status
~/.hermes/skills/gaming/orzmc/scripts/adapters/mcsm.sh players
~/.hermes/skills/gaming/orzmc/scripts/adapters/mcsm.sh logs 50
# 破坏性（自动检查玩家数，有玩家时拒绝；restart 已验证 PID 变更生效）
~/.hermes/skills/gaming/orzmc/scripts/adapters/mcsm.sh start|stop|restart
~/.hermes/skills/gaming/orzmc/scripts/adapters/mcsm.sh kill   # 强制终止（崩溃循环恢复用）
~/.hermes/skills/gaming/orzmc/scripts/adapters/mcsm.sh command "list"
```

日志解析依赖 `scripts/parse_mcsm_players.py` / `scripts/parse_mcsm_logs.py`（剥离 ANSI 控制字符 + 提取「当前在线(n/max)」行，位于 scripts/ 根目录非 cmp3/）。

## 平台要点（2026-08-03 实测）

- ⚠️ **apikey 是普通用户权限**：管理员端点（`/api/overview`、`/api/service/remote_services_system`、`/api/auth/search`、`/api/service/remote_service_instances`）返回 403「密钥不正确/权限不足」；只能访问自己名下的 `/api/instance`（需正确 daemonId+uuid）
- ⚠️ **「未开启API密钥创建功能」= 面板系统设置开关被关（2026-08-30 实测）**：apikey 认证全部失效（status != 200 + data=该消息）——MCSM 面板 系统设置→安全设置→「允许创建 API 密钥」被关闭所致（非 key 无效，**key 本身没问题**；8-24 审查时仍正常，近期被改或面板更新默认）；需面板管理员（机主）在面板开启；**影响所有依赖 apikey 的 cron**（周一 9:15 三端配置审查）
- ⚠️ **查实例必须先有 daemonId + instanceId**：普通用户无法列出 daemon/实例清单，这两个 ID 从面板网页 URL 获取，存 `.env`
- ⚠️ **daemonId 稳定性**：日常运行/重启面板不变；但 **daemon 重装、迁移服务器、面板删除重绑** 会生成新 UUID（实例删除重建同理）——届时需从面板重新获取
- ✅ **实例状态字段**：`status`(-1=忙碌 0=停止 1=停止中 2=启动中 3=运行中)、`info.currentPlayers/maxPlayers`、`info.version`、`processInfo.pid/memory/elapsed`、`config.eventTask.autoStart/autoRestart`、`config.pingConfig.port`
- ✅ **日志含 ANSI 转义**：解析需先剥离 `\x1b[...` 控制字符
- ✅ **有玩家在线时只读安全**：状态/日志查询不干扰玩家，可用作运维监控
- ⚠️ **面板 23333 有路径防护**：根路径/未知路径返回 `{"status":500,"data":"Malicious Path"}`，属正常
- ⚠️ **静态资源全 SPA 回退**：`/api/overview` 等 GET 可能返回前端 HTML 而非 JSON（需要带必需头 + 正确路径才走 API 路由）
- ✅ **升级流程（2026-08-03 实测）**：上传新 paper jar 到实例根目录（`POST /api/files/upload?upload_dir=/` → daemon `/upload/{pwd}` multipart）→ `PUT /api/files/` body `{"target":"/Start.bat","text":"新内容"}` 更新 jar 引用 → restart。旧 jar 保留作回滚
- ⚠️ **MCSM 写文件（PUT /api/files/）四要点**：① **必须带 `daemonId`+`uuid` 参数**——只带 apikey → 403「参数不正确或非法访问实例」；② **只能写已存在的文件**——新文件路径 → 500 `Illegal access path`（改配置/Start.bat 都满足，无需新建文件）；③ **body 字段是 `text`**——用 `content` 返回 200 但实际不生效；④ 改配置后**需重启才生效**
- ✅✅ **MCSM 删除文件/目录可用（2026-08-06 推翻旧结论）**：`DELETE /api/files/?daemonId={d}&uuid={i}` body `{"targets":["/路径1",...]}` —— 实测删普通文件+目录都 200 成功。**旧结论「无 delete API、只能上传覆盖」是错的**（此前按 `DELETE /api/files/delete` 探测 404 误判；正确端点是 `DELETE /api/files/`）。删后必须真实 GET 验证（daemon 偶发假 200）
- ✅ **MCSM 列目录 API 可用（2026-08-06 深挖修正）**：`GET /api/files/list?target={路径}&page=0&page_size=50&file_name={过滤词}`——**必须带 `page`（从 0 开始）+`page_size`+`file_name`**；`file_name` 是过滤词（不填返回 total=0，daemon 全量列出有 bug）；`type`: 0=目录 1=文件。源码实证：MCSManager Daemon `system_file.ts`（`list(page, pageSize, searchFileName)` 实现）；面板 `filemananger_router.ts` 校验 query `{daemonId,uuid,target,page,page_size}`（page 默认 0、page_size 默认 10 上限 100）
- ⚠️ **MCSM download API 不校验文件存在性**：`POST /api/files/download` 对任何文件名都返回 200（不存在的文件也发凭证）！判断文件是否存在必须**真实 GET 下载**：500=不存在，`PK` 魔数开头=真实 jar
- ⚠️ **Paper 26.x 首次启动需下载 mojang_26.x.jar**：MCSM 服务器若下载失败会 `Hash check failed for downloaded file mojang_26.x.jar` 崩溃循环（每次自动重启重下）；**kill 恢复法**：`mcsm.sh kill` 终止 → `start` 重新启动，通常第二次下载即成功
- ⚠️ **daemon 文件操作**（2026-08-06 全面复核）：**list 需 fileName 过滤（不填空）、move 必须 PUT+二维数组、mkdir 只建单层（父目录不存在 500）、compress type=1 压缩/type=0 解压**；delete/mkdir/touch/copy 稳定可用；删后建议**真实 GET 验证**
- ✅ **server.properties 启动时重写（2026-08-12 实证）**：每次重启文件头时间戳更新、值原样保留（服务端读入内存后写回）→ 「PUT 改文件（保留 CRLF）→ 等无人窗口重启」流程安全，改动不会丢
- ✅ **command 编码**：中文命令用 `urllib.parse.quote`（空格变 %20）完全可行（2026-08-12 实测：含中文+括号的 say 广播正常执行）；空格原样（safe=' '）也可用。旧结论「空格不能 %20」过时——两种都通
- ⚠️ **命令长度限制**：过长命令被截断，日志出现 `<--[HERE]` 标记——长命令拆短

## 状态码映射（MCSM 实例，官方文档）

`-1`=忙碌 / `0`=停止 / `1`=停止中 / `2`=启动中 / `3`=运行中

## 调用姿势的三处硬坑（2026-11-10 实测，全部踩过）

写自动化脚本（升级/巡检）时按「直觉」拼参数会连环 400，正确姿势如下：

| 目标 | 错误写法（实测报错） | 正确写法 |
|:--|:--|:--|
| 查实例状态 | `GET /api/instance?apikey&daemonId` → `400 Validator failed: "uuid" is required!` | `GET /api/instance?apikey&daemonId&uuid=`（**uuid 必填**，返回单实例对象，`data.status` + `data.info.currentPlayers`） |
| 实例列表 | `GET /api/instance?apikey&daemonId&page=1&page_size=20` → 同上 400 | 列表走 **POST** `/api/instance`，`daemonId` 必须放在 **JSON body**（放 query 会报 `"daemonId" is required!`） |
| 发控制台命令 | `POST /api/protected_instance/command` body `{"command":"list"}` → `400 Validator failed: "command" is required!` | `POST /api/protected_instance/command?apikey&daemonId&uuid&command=list`（**command 拼在 query**，不是 body） |
| 状态查询专用端点 | `GET /api/protected_instance/status` → **404** | 该端点不存在；状态一律从 `GET /api/instance?uuid=` 的 `data.status` 读 |

补充实测（同轮）：

- `POST /api/protected_instance/stop` / `open` 带 `?apikey&daemonId&uuid`、body 给 `{}` 即 200；`status` 从 3 → 0 的实测耗时约 **20s**，启动到 3 约 **6s**（真正 `Done` 还要再等 90–110s 读日志）。
- 判定「实例真的停了」要用 `status == 0` 轮询，别用固定 sleep。
- 实例运行中日志可在 `GET /api/protected_instance/outputlog` 看，但**这是滚动缓冲区，会残留上一轮输出**（见 SKILL.md Pitfalls）——只适合粗看尾部。

## 面板「重启」卡死：服务停了不再起来（2026-10-26 实测定位）

**现象（老板报障）**：面板点「重启」→ 服务关闭 → 面板一直转圈/不响应，再点「启动」也不动 → **只有点「终止」才恢复**。

**实测证据（folia-test，0 玩家）**：
| 操作 | 结果 |
|:--|:--|
| `GET /api/protected_instance/restart` | **200，3.4s 返回**（异步受理） |
| 之后状态 | status **3(运行) → 1(停止中)**，停在 1 **≥130s**，最终才回 3 |
| `GET /api/protected_instance/stop` | **93.7s 后 SSL EOF**（`EOF occurred in violation of protocol`）→ **请求被掐断**，服务仍在 status=3 |
| 普通 `GET /api/instance` | 间歇 **120s 超时**；TLS 握手 1.7~5s、首字节 3~8s、总耗时常撞 30s 上限 |
| 实例配置 | `stopTimeout: 0`（**无强制终止超时**）、`stopCommand: stop`、`processType: docker` |

**根因（按证据排序）**：
1. **面板↔daemon 链路（Cloudflare Tunnel `mcs-node.{SERVER_NAME}.cn` wss:443）不稳**：长时间同步请求在 ~90~100s 被掐（与 Cloudflare 100s 请求窗口吻合）。「重启」= 停 → 等状态迁移 → 起，若中段连接被断，**服务已收到 stop 但 start 永远没发出去** → 停在停止态；「终止」是短请求，能把状态机复位，所以点它才"活"。
2. `stopTimeout: 0` 放大了问题：MCSM 不会在优雅停止超时后强制 kill，stop 一直等，必然撞穿 100s 窗口。

**处置（按推荐顺序）**：
1. **操作习惯**：面板里「重启」改为**两步**——① 终止（kill）② 等状态=0 ③ 启动。API 同样分两步：
   ```bash
   G=/api/protected_instance; Q="daemonId=$MCSM_LOCAL_DAEMON_ID&uuid=<实例>&apikey=$MCSM_LOCAL_API_KEY"
   curl -s "$BASE$G/kill?$Q"    # 短请求
   # 轮询 /api/instance 到 status=0
   curl -s "$BASE$G/open?$Q"
   ```
2. **实例设置 → 停止超时** 由 `0` 改为 **15~30s**（优雅停止失败时自动强制 kill，重启流程可控）。
3. **链路治理**：Windows 侧查 `cloudflared`（CPU/内存/重连日志、是否存在连接风暴）；面板/daemon 尽量走**局域网直连**（Mac↔Windows 同网）绕开 Cloudflare 100s 限制。
4. 长期：考虑升级 MCSM（新版有把重启/停止改为异步的实现）。

⚠️ **诊断纪律**：面板慢时**不要连打**——每次探测间隔 ≥10s，冷却 2~3 分钟；状态查询超时 ≠ 操作失败（本例 stop 报 SSL EOF，但服务实际没停，最终 status 仍为 3）。

## 并发下载实例文件 → 500 根因（2026-09-09 实测于本机 Docker 部署，web 10.18.0 / daemon 4.18.0）

**结论：不是"下载并发"上限，而是"签发凭据接口"的硬编码限流。下载链路由两步组成：**

1. **面板签发一次性凭据** `GET/POST /api/files/download`（带 daemonId+uuid+apikey）→ 返回 `{password}`
2. **客户端凭 password 直连 daemon 流式下载** `GET {daemon}/download/{password}/{文件名}`

- **第 2 步（真正文件流）本身无并发限制**——实测用多个不同 password 并行拉流全部 200 成功。**并发下载的瓶颈不在文件流。**
- **第 1 步（签发凭据）被硬编码限流** `speedLimit(3)`（面板 app.js，`/download` 路由）：3 秒窗口内**同一账号只放行 1 次**，再次调用直接 **HTTP 500**「此操作冷却中，约 2 秒后可继续操作！」；**仅对非管理员生效**（`if user.permission === ROLE.ADMIN return next()`，管理员完全绕过）。

**两个易混 500**（已分离）：
- 「此操作冷却中」= 签发接口被限流（真瓶颈）。
- 「下载出错: Access denied: No task found」= **用被限流拒签的 null/过期 password 去拉流**的连带结果，不是文件流错误。

**⚠️ 不需要特殊配置，也改不了**：`speedLimit(3)` 是写在路由里的常量，无 config 开关；面板设置里的 `maxDownload`（web）与 daemon `maxFileTask`/`fileLock`（默认 2）只守卫**压缩/解压**与**「URL 下载到实例」（download_from_url，daemon maxDownloadFromUrlFileCount=1）**两类任务，**与"下载实例文件到本机"无关，勿改动**。

**解决方向（用户 2026-09-09 决策：走方案 B）**：
- **方案 B（普通用户 joker，推荐/已采用）**：脚本里**签发凭据串行化或限速 ≥3s/次**（一次下载一个文件就签一次，for 循环串行），拿到全部 password 后**再并行拉流**。核心约束=「签发串行、下载并行」。⚠️ 别用签发失败返回的 password 去拉流（会得到第二个 500 误判）。
- **方案 A（提升并发）**：用**管理员账号的 apiKey** 调用——管理员跳过 speedLimit，可真正并发签发+并行下载，无需额外配置（需后台给账号升管理员并生成 apiKey）。

## 地图备份下载部署到本地（2026-08-13 实测流程）

- **备份位置**：`plugins/OrzMC/backup/`（OrzMC 插件自动备份，按日期命名 `YYYYMMDDHHMMSS.zip`，~1.4GB/份）；列目录 `GET /api/files/list?target=/plugins/OrzMC/backup&page=0&page_size=100&file_name=`（file_name 空串可列出全部）
- **下载三步**：① `POST /api/files/download?file_name=/plugins/OrzMC/backup/<名>.zip`（带 daemonId+uuid+apikey）→ 返回 `{password, addr}`；② addr 是 `localhost:24444` → **换面板主机名**（如 `{SERVER_HOST}:24444`）；③ `GET http://{addr}/download/{password}/{文件名}`（带 UA，curl 后台跑，~1.4GB 几分钟）
- ⚠️ **zip 内是 Windows 反斜杠路径**（`world\dimensions\...`）——macOS unzip 会创建**字面反斜杠文件名**！必须 python zipfile 处理：`name.replace("\\", "/")` 后解压（脚本法见下）
- **备份内容**：`world/` 完整（level.dat + `dimensions/minecraft/{overworld,the_nether,the_end}` 三维度 + players/ 玩家数据 + death-chests.yml 等插件数据文件）——**插件数据在世界内，换地图=换插件数据**
- **部署流程**：停服 → `mv world world.bak-test`（可回滚）→ python 解压 → 启动验证（`level-name=world` 匹配）
- **真实地图特征**：启动 261s（vs 测试世界 106s，2.1GB）；**首次玩家登录冷加载 TPS 崩 4.7**（一次性，预热后 19.7 稳定）——比测试世界更猛，强化「活动须预热」；空载 TPS 20

```bash
python3 - <<'EOF'   # 反斜杠路径安全解压（示例，落地为脚本更稳）
import zipfile, os
zf = zipfile.ZipFile('backup.zip')
for info in zf.infolist():
    name = info.filename.replace("\\", "/")
    if info.is_dir(): continue
    t = os.path.join(dst, name)
    os.makedirs(os.path.dirname(t), exist_ok=True)
    with zf.open(info) as fi, open(t, "wb") as fo: fo.write(fi.read())
EOF
```

## 插件更新（MCSM 端）

- ⚠️⚠️ **2026-10-05 更新：`/upload/{pwd}` 通道已不可用** —— `POST /api/files/upload` 取证后向 `{addr}/upload/{password}` multipart 推送**全线 403 Forbidden / Broken pipe**（addr 现为 `wss://mcs-node.{SERVER_NAME}.cn:443` 形态）。**统一改用 `POST /api/files/download_from_url`** body `{"url":官方直链,"file_name":"/plugins/update/<名>.jar"}`（2026-10-05 实测 7 文件含 47MB Geyser 全部一次成功）+ 投递后 sha256 回读验收。详见 `references/test-server-upgrade-sop.md` §1③
- ✅ **plugins/update 实测可用**（2026-08-03）：上传 jar 到 `/plugins/update` → restart → Paper 自动替换并清空 update/。**文件操作期间服务器运行中无碍**（jar 上传不触发锁定，仅读取被运行中 jar 锁定会 500）
- ⚠️ **`PUT /api/instance`（改实例配置/启动命令）对普通 apikey 返回 403「密钥不正确」** → 启动命令等实例配置**只能老板在面板改**；文件类 API（list/download/touch/PUT 文件/DELETE/move/mkdir/copy/download_from_url）普通 apikey 均可用
- ✅ **删除插件/文件用 `scripts/cmp3/mcsm_delete.py`**（2026-08-06 起标准方案）：`python3 mcsm_delete.py /plugins/xxx.jar` → DELETE /api/files/ + 自动删后验证（真实 GET 确认）。**旧方案「上传 0B 占位覆盖」已废弃**（Paper 会对无效 jar 报 `Directory 'plugins\xxx.jar' failed to update!` 启动 ERROR，不如直接删干净）
- 上传插件脚本：`scripts/cmp3/mcsm_upload_update.py deathchest.jar GriefPrevention.jar` + `mcsm_verify_update.py`
