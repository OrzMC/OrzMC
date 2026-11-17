# 插件测试体系（testing）

> 合并自：papermc-plugin-e2e-testing + papermc-cross-server-testing（2026-08-10 阶段二整合）
> 触发：本地测试服对插件做 E2E 自动化验证；跨服传送门 transfer / 双服行为验证。

## 测试策略分层原则（用户规范）

> **「哪些逻辑可以用单元测试和集成测试保证的，优先使用单元测试和集成测试；其他情况必须要真实验收的，再使用机器人做端到端真实测试。」**

> **⚠️ 当前测试服拓扑（2026-09-03 起全部迁 MCSM 本机栈）**：双 Docker 实例 **`papermc-test`**（uuid 716c2fb7，LoginSecurity）与 **`folia-test`**（uuid 8A932DD4）由本机 MCSM 面板 **mcs.{SERVER_NAME}.cn** 管理（节点 orzmc-local），启停走面板（实例配置/数据在宿主 `/Users/Shared/orzmc/mcsmanager/daemon/data/`，目录 `InstanceData/<uuid>/` 含 server.properties/plugins/ 完整服务端）。旧裸跑目录 `~/minecraft-server`/`~/folia-test` 与 start.sh/screen 启动**已废弃删除**。详见下文「MCSM 本地栈 Docker 实例」节（2026-09-03 迁移实测 + 五连坑）。
> **✅ 地图已拆分，可同时运行（2026-09-11 更正）**：容器化后两实例**不再共享 world** —— 各自挂载 `InstanceData/<uuid>/` 到容器 `/server`（`docker inspect` 可验，无共享 world 卷），两边 `world` 目录 inode 不同、各 ~2.1G（Paper 侧 = 测试服验证图，Folia 侧 = `[Folia] OrzMC Test`）。实测两实例同时在线：Paper Java `25565` + 基岩 `19132`、Folia Java `25566` + 基岩 `19133`（Folia 的 UDP 宿主映射见 `references/instance-ports.md`，方案 B：`19133:19132/udp`）。
>
> 仍然成立的约束：**宿主端口必须错开**（同宿主多实例不能重复发布同一个 UDP/TCP 端口）；实例启停一律走面板（daemon 软关闭不自动停 docker 实例）。
>
> （历史）此前 `worlds/test` + extraVolumes 共享地图的“严禁同跑”规则已废止。
> **E2E 套件 = 插件仓库 `plugin/e2e/`**（2026-08-19 建立）：`bash e2e/run-all.sh [-c NN] [-r]` 一键跑；**双核心支持**：`ORZMC_CORE=folia|paper` 显式指定 + 测试服目录/日志/备份路径环境变量注入（run-all.sh 不再自动检测核心——Docker 实例 java 进程在容器内，宿主 ps 不可见；MCSM 对接层由技能 wrapper 脚本 `scripts/e2e-mcsm-wrapper.sh` 负责：确认实例状态 + 注入全部环境变量 + 调仓库 run-all.sh，2026-09-03 起）——**05-groupmsg.js 群消息场景**（2026-08-19 加入，PR #201）：whitelist_block 拦截/player_join 上线/player_digest 双 bot 下线聚合/player_quit 单发/ip_blacklist_block——**日志断言**（Notifier.routeEvent 统一 `[群消息:<key>]` 日志 + ⏎ 转义换行，JUL→log4j 只输出首行）+ 占位符残留检查（防 {online_list} 类模板回归）；Folia 11/11 + Paper 11/11 双绿；**06-permission-msg.js 权限/审核消息**（2026-08-19 加入，PR #202）：review_submitted 申请发起 / review_approved 审核通过（含审核人）/ rank_promoted 晋升（🎉「建造者」中文显示名）/ review_rejected 拒绝 / review_cancelled 撤回——**关键坑**：LP 设组须**先建后设**（parent set 对不存在用户创建的虚拟用户会被首登覆盖：先进服建用户→quit→parent+group set→重进）；**登录节流 20s**（login_rate_limit 5/min + LoginSecurity 冷却 13s+，Folia SimpleLogin 无此坑）；/review 仅玩家可用 + isOp/orzmc.admin（自建 op 审核人 RCON op+deop 还原）；异常路径 try/finally quit（防残留 bot 触发 per-IP 限流）；Folia 19/19 + Paper 19/19 双绿；`lib/rcon.js`（Promise RCON + waitLog tail 3000 防刷屏挤出）+ `lib/bot.js`（spawnBot 自适应 SimpleLogin/LoginSecurity 登录：probeLogin 先发 /login 探测、未注册转 /register；⚠️ 成功判定只认「登录成功/注册成功」，勿匹配「Welcome! just joined」首登广播否则过早 resolve 命令被拦）；用例自包含（专用账号自动注册+清理白名单）。测试账号密码：SimpleLogin 版 E2E 专用 E2EPass123（旧 LoginSecurity 版 TestNewbie/NewbiePass123 已不适用）。
> **BUG-E2E-001（✅ 已修复并双核心验证 2026-08-19）**：`$w` 白名单分页在 Folia 上抛 `IllegalArgumentException: Delay ticks may not be <= 0`——Paginator.paginatePages L71 `i * delayTicks` 在 i=0 时 delay=0，Paper BukkitScheduler 允许 0 tick、**Folia FoliaGlobalRegionScheduler.runDelayed 要求 ≥1**（`delayTicks<=0?5L` 保护只覆盖配置值不覆盖 i=0 首页）→ $w 分页 Folia 完全不可用。**修复**：Paginator 两处 `Math.max(1L, (long) i * ...)` + ServerFacade.runLater 钳位 ≥1 + PaginatorTest 回归护栏（首页 delay≥1）。验证：Folia `$w` 输出 123 人 ✅、Paper 01 用例 8/8 ✅。记录：`plugin/e2e/buglog.md`。
> **BUG-E2E-002（✅ 已修复并端到端验证 2026-08-19，backup-core v0.2.2 = PR #46+#47）**：大世界（Paper 服 317 万 chunk）`$b` 备份极慢+失败误报——**不是新压缩格式**！三层坑：①compression byte 非法（如 49）②**长度字段荒谬但 compression 合法**（如 0x789c=ZLIB 但长度 20 亿 → dataBytes 读 20 亿字节卡死）③**offset 越过文件末尾 → BufferedRafAccess readFully avail<=0 死循环（CPU 100% 无进度）**。修复：McaEntry `UNKNOWN` 枚举 + 长度 >8MB 短路 + readFully EOF 保护 + pattern 异常安全保留。插件侧 errorHandler 聚合（Pattern/Write-损坏不报失败，Done 汇总）。**验证：Paper 服 $b 14分21秒完成 + zip 2.03GB + 「264 个损坏区块已安全保留」**。E2E 04 备份断言用「阶段进度 + .zip 落盘」（大世界全量备份 ~15min）。
> **BUG-E2E-003（✅ 已修复验证 2026-08-19）**：CommandGuard「危险命令放行」WARN 刷屏（命令方块循环 20 条/tick → 21 万条/53MB）→ `ThrottledNotifier` WARN 日志 5s 限频（其余降 fine）+ BLOCK 通知 10s 限频；验证 4 分钟 13 条（修复前 4800+）。**备份并行化**：WorldMaintenanceService `RuntimeOptions(0)`（单线程）→ `RuntimeOptions(CPU 核数)`——Paper 服 $b **14分21秒→5分59秒**（速率 5 倍）。
> **BUG-E2E-004（✅ 修复 PR 已提 2026-08-20，backup-core #50 main/#51 0.2.x）**：symlink 世界 $b 备份**空跑假完成**——Folia 测试服 world 是 symlink（→papermc-test/world），backup-core `RealFileSystem.walk` 用 `Files.walk` 不跟随符号链接 → `dimensions/*/region/*.mca` 全不可见 → 0 chunk、431ms "完成"、zip 22 字节、进度 2/2（zip 固定项）**无任何报错**。修复=`Files.walk(path, FOLLOW_LINKS)`+`RealFileSystemSymlinkTest`。验证：修复版 Folia $b 3170460/3170460、6分16秒、zip 1.42GB。**连带**：walk 跟随链接后 worldContainer 内备份残留目录（旧布局 plugins/OrzMC/backup/tempDir）会被扫入备份源 → 保持 worldContainer 内无备份中间目录。
> **⚠️ 备份=优化式备份（设计语义，非缺陷）**：backup-core 对备份也应用 InhabitedTime 阈值过滤（插件传 optimizeTickTimeThreshold 默认 300 秒，剔除活跃 ≤15 秒 chunk）→ 17G 世界备份 zip 仅 ~1.4G（region 946/6380）。features.md 已如实标注。**完整备份磁盘硬约束**：全量保留需 ~17G+ 临时空间，本机 13Gi 不够 → 本机只能验证备份功能链路；线上磁盘充足。
> **备份收尾期登录被拒**：$b 维护模式踢人+拒登，E2E 05/06 在备份收尾期跑会零输出 exit 0（汇总假绿）——等「地图备份 完成」+ zip 落盘后补跑 `-c 05 -c 06`。
> **⚠️ 备份完成判定陷阱（2026-08-20 复验踩坑）**：**zip 出现 ≠ 备份完成**——backup-core zip 边写边落盘，进行中 zip 可能只有 64M（完成时 1.1G），tempDir 也在场；判定「备份完成」必须等日志「地图备份 完成」（或 zip mtime 稳定 + tempDir 消失），勿用「新 zip 出现」提前 break（会误判未完成/误判失败）。
> **发布闭环（2026-08-20 1.0.19 经验）**：代码 PR 合并后 → 更新 CHANGELOG（1.0.19 条目：修复/新功能/依赖/⚠️升级注意）+ 清理陈旧文档（验收报告版本表 sha256、世界大小、备份目录描述）→ docs PR（CI 绿后文档直接合并）→ `git tag 1.0.19`（**严格 SemVer 无 v 前缀**）+ push → Publish workflow（GitHub Release + Hangar + Modrinth）自动触发，`gh run list` 看 headBranch=tag 的 Publish run=success 即发布完成。
> **测试服世界裁剪（磁盘空间管理，2026-08-20）**：本机磁盘 13Gi 可用，17G 测试世界完整备份放不下 → 用 backup-core CLI 优化裁剪：`java -jar backup.jar -t 300 --parallelism=4 --report --report-file=/tmp/opt.json <world_dir> <output_dir>`（**v0.2.x CLI 无 `optimize` 子命令**——"optimize" 会被当 WORLD_DIR 静默零输出，直接 `backup.jar <WORLD_DIR> [OUTPUT_DIR]`；jar 构建：`cd OrzMCBackup && ./gradlew :app:shadowJar`，产物 `app/build/libs/backup.jar`）。阈值 300 秒 → 17G → ~2G（剔除低活跃 chunk，**破坏性操作**，测试服可接受）。切换：验证新 world → 删旧 → rename。优化只写 ~2G 临时输出（峰值额外 +2G），磁盘够；完整备份要复制全部 17G → 不够（O5）。
> **backup-core 0.3.1 + 备份目录最终方案（✅ 2026-08-20 插件 1.0.19 已发布）**：插件适配要点——① `IOOptions(fs, ioFactory, syncOnFinalize=true)` 三参（0.3.0+ API，第三参=跳过 fsync，非 zipOutput）；② 0.3.x overlap 校验：input/output 不得重叠 → **input 用世界目录**（`getWorldFolder()`，优先含 dimensions/region 的真实世界目录，防 getWorlds 顺序把非主世界排前），output=`backup/tempDir`（`backup/` 是世界目录的兄弟路径，天然不重叠）；③ zip 直接落 `backup/`（output 父目录），无移动环节；④ 备份成功判定=最新 zip mtime 变化（同名覆盖不误判）；⑤ 崩溃/断电残留 `backup/tempDir` 由 MaintenanceModule.setup **异步启动清理**；⑥ `$o` 优化需 `maintenance.optimize_enabled=true`（默认 false），实测 31s/190526 chunk；⑦ 备份目录=服务器核心根目录 `backup/`（非插件数据目录），E2E 04 BACKUP_DIR 与 run-all.sh ORZMC_BACKUP_DIR=`$TEST_DIR/backup` 同步；阈值保持原逻辑 300 不动。
> **质量周报 cron（2026-08-19 建立，job `079c34424888` 每周一 9:30）**：`~/.hermes/scripts/orzmc_quality_report.py` 跑 gradlew test/integrationTest/jacoco → 解析用例数/通过率/四类覆盖率 → 对比上周基线（`~/.hermes/state/orzmc_quality.json`）→ Markdown 表格发飞书。基线（2026-08-19 补测后）：1317 用例 / INSTRUCTION 85.4% / BRANCH 74.3% / METHOD 87.4%+ / CLASS 96.6%+；薄弱模块已全部达标：maintenance 66.9%、paging 80.8%、ws 59.0%、review 86.2%、teleport 96.5%。

| 逻辑类型 | 手段 |
|:--|:--|
| 业务状态机 / 纯逻辑 | 单测（JUnit+Mockito，mock 端口） |
| 命令分发 / 权限校验 | 单测（mock 依赖服务） |
| YAML 持久化 | 单测 |
| 平台行为（Paper 26 命令事件、LP 真实授权、EasyBot 网关、RCON 链路） | **必须真实验收**（MockBukkit 模拟不了） |

验收顺序：先 `./gradlew test` 全绿 → 再 bot E2E 覆盖平台行为层。

## 三大测试通道

| 通道 | 用途 | 入口 |
|:--|:--|:--|
| **RCON** | 控制台命令 | `scripts/rcon.py '<cmd>' <mc-port> <rcon-pw>`；node 原生 `scripts/rcon-node.js` |
| **orzdebug** | 模拟群管理员发 Bot 命令（isAdmin=true） | **游戏内**（Mineflayer bot 执行 `/orzdebug <bot命令>`）——Paper 26 Brigadier 命令不触发 RCON 事件 |
| **Mineflayer bot** | 真实玩家身份执行游戏内命令 | `~/minecraft-bot/` 下 bot 脚本 |

## 关键陷阱（Paper 26 + 异步链路）

- **Brigadier 注册的命令【不触发】ServerCommandEvent**：`/orzdebug` 的 `.executes()` 正常执行但监听器收不到事件——修复：`.executes()` 里直接调 `botInboundHandler().handleMessage(...)`
- **LP 命令必须主线程 dispatch**：异步线程抛 `IllegalStateException: Asynchronous Command Dispatched Async`——`scheduler.runSync` 回主线程；runSync 吞异常需 `CompletableFuture.join()` 传播
- **RCON 包 length** = id(4)+type(4)+payload+2 null 总长（payload.length+10）；node 实现漏算 8 字节服务器立即断连
- **`$` 防 shell 展开**：`$v l` 经双引号被 bash 展开成空——node spawnSync 数组参数/原生 net；bash 单引号
- **测试环境配置漂移掩盖生产 bug**：E2E 前先 diff 测试服配置与仓库默认资源（`diff /Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/<运行实例uuid>/plugins/OrzMC/templates.yml src/main/resources/templates.yml`）——**2026-08-19 实测踩坑**：Paper 服 templates.yml 是 #197 群消息样式统一前的旧版（player_join 含 `{online_list}`），新代码渲染不传该变量 → 群消息出现 `{online_list}` 字面量（Folia 新版模板正常）→ 修复：`cp src/main/resources/templates.yml <服>/plugins/OrzMC/` + RCON `/config reload`（templates 热重载）。**已自动化（PR #200/#213）**：run-all.sh 前置模板一致性检查（ORZMC_CORE 显式指定 > 环境注入路径；日志/备份/模板路径全部环境变量注入——PR #213 2026-08-20，2026-09-03 迁 MCSM 后不再进程检测）+ diff 拦截，`ORZMC_SKIP_TEMPLATE_CHECK=1` 临时跳过；**群消息模板变更后仍须同步所有测试服**（检查只拦截不自动修复）
- **部署后必验**：`ls -la build/libs/*.jar` 与 plugins/ jar 时间戳一致 + `grep "Enabling X"` 确认版本；时间戳一致仍不够——python zipfile 读 .class 字节搜修复符号
- **测试账号密码重置（LoginSecurity）**：`lc/lac unregister` 不可靠——直接 `sqlite3 plugins/LoginSecurity/LoginSecurity.db "DELETE FROM ls_players WHERE last_name='X';"`（表 ls_players）→ 重进服 `/register <pw> <pw>`
- **mockStatic 泄漏**：@BeforeEach 开不关 → 后续测试污染——每个测试 try-with-resources 包住
- **登录冷却**：bukkit.yml `settings.connection-throttle` 改 0 + 重启可关；LoginSecurity「此用户已经在线」是会话残留时序（等 2-3s 再重连）
- **⚠️ vanilla per-IP 在线限制（压测天花板，2026-08-13 实测）**：同 IP 已登录玩家 ≥5 时第 6+ 被踢（`Sorry, there are too many players logged in with your IP address`）→ **单出口 IP 压测上限 = 5 bot 真实在线**（40 bot 尝试全成功但峰值在线仅 3-6）。**macOS 禁 bind 127.0.0.x**（Errno 49，lo0 虽 /8 掩码但内核只认 127.0.0.1；Linux 可行）→ 多回环 IP 方案 macOS 死路（无 sudo 加不了 lo0 alias）。真实玩家各 IP 不同，此限制不影响线上容量
- **⚠️ 压测在线数统计**：mineflayer `spawn` 事件计数只增不减会虚高（被踢也算"进入"）——用 Set 维护真实在线（spawn 增 / end 减），采样打 `在线=N/总数`
- **⚠️ 登录风暴：冷区块首登崩、热世界不崩**（2026-08-13 实测）：冷启动后首轮登录加载全冷 chunk → 10 bot 就 TPS 4.2；预热后（同轮测试后半程）40 bot 登录风暴 TPS 最低 16.1 稳定 18+，0 次 Can't keep up → **活动当天必须预热 spawn 区域**（提前登录/加载），登录风暴本身不是杀手，冷 chunk 生成才是
- **LP check true ≠ 命令可用（子权限陷阱）**：`/mail send` 需 `essentials.mail.send`、`/warp` 需 `essentials.warp.list`、`/time set` 需 `essentials.time.set`——最终验收必须 bot 实测命令
- **RCON 发 LP 命令偶发丢失 + mtime 验证不可靠（2026-08-30 沉淀）**：LP 命令经 RCON 偶发不生效；且**文件 mtime 变化 ≠ 命令成功**（插件后台定时保存/玩家数据写入也会写库写盘，mtime 被刷新是假阳性）——验证必须以 bot 实测（权限/命令真值）为准，必要时重复执行命令
- **测试服启停规范（2026-09-03 MCSM 版，替代裸跑流程）**：实例启停一律走面板（docker 实例 daemon 软关闭不自动停，停服/重启仍要手动操作面板）；启动成功判定 = 日志 `Done (` + 端口监听（`docker ps --filter name=MCSM-` 确认容器名）+ **jar mtime 变化**（换 jar 升级后）；重启/切换前检查共享 world `session.lock` 残留（异常崩溃遗留锁会拒启，需清）。⚠️ 裸跑期流程（RCON stop → kill -0 → 删锁）已废弃，仅适用于旧裸跑/进程模式实例

## 跨服/双服测试（transfer）

### 双服搭建（复制法）
```bash
cd /Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/<源实例uuid> && tar --exclude='logs' --exclude='cache' --exclude='world/session.lock' -cf - . | (mkdir -p ~/tmp-second-server && cd ~/tmp-second-server && tar -xf -)
# ⚠️ 必改：server.properties（server-port=25566、rcon.port=25576、motd）；第二服 world 须独立（勿指向共享 world）
```
- **✅ 测完即删（2026-08-15 老板决策）**：双服测试是临时动作，完成后必须清理防占磁盘（先确认无进程、无 cron 引用）
- 坑：~~两服严禁同跑共享 world~~（2026-09-11 起各自独立地图，可同时跑，但**宿主端口必须错开**）；第二服复制 Geyser 配置会端口冲突（无害）；easybot 连同一网关 409（无害）
- ⚠️ **MCSM 环境推荐克隆实例法**：双服测试目标服用「手工克隆实例」（见「MCSM 本地栈」节坑 5：uuidgen → rsync InstanceData → cp 实例 JSON 改 nickname/端口/独立 world 目录 → 重启 daemon），比目录复制 + 裸跑更贴合当前栈

### transfer 机制（核心认知）
- OrzMC `PlayerPortalEvent` → `findTarget` → `transfer <host> <port> <player>`——**由玩家客户端主动去连目标**
- ⚠️⚠️ **目标 IP 必须是玩家可达地址**：`127.0.0.1` 只有本机客户端能通（远程玩家收到会连自己电脑 → `finishConnect failed Connection refused`）；局域网玩家用服务器局域网 IP；公网玩家用公网 IP/域名
- **mineflayer 无法完成 transfer**：不支持 transfer 协议包；跳跃+前进能触发 PlayerPortalEvent 但插件 findTarget 未命中（位置同步差 1-2 格）→ 原版传送接管。**transfer 端到端只有真实玩家能完整验证**；bot 只能做部分链路
- mineflayer yaw 映射：`yaw=0 → -z`、`yaw=π → +z`（与直觉相反）
- pathfinder 默认 `canDig: true` 会挖方块——必须 `mc.canDig = false; mc.allow1by1towers = false;`
- bot 跳跃进门可能掉刷怪区被打死——先清怪或临时和平模式

### 传送门结构（实测）
```
y=68 obsidian（顶梁）/ y=65-67 nether_portal / y=64 obsidian（底梁）/ y=63 gold_block（pad）
```
- **传送门内部（框架内）禁止放置方块**：setblock 会触发结构有效性判定 → 所有 NETHER_PORTAL 方块消失只剩框架
- /portal 命令：`portal <host> <port>`（**不带 create 字面量**）；必须玩家执行（RCON 报 requirePlayerTip）
- **portals.yml 会被覆盖**：手写后只要再执行任何 /portal 命令就被内存状态覆盖——正确改法：命令操作（remove+create）或手写后重启前不再执行 /portal 命令
- 判断门有效：RCON `testforblock <x> <y> <z> minecraft:nether_portal`（比 bot blockAt 可靠）

### LoginSecurity 干扰（未登录玩家）
- 未登录玩家站传送门：插件 `isAuthenticated=false` → 取消传送（设计正确）；**测试流程必须先 `/login` 再进传送门**
- LoginSecurity 3.3.2 `SessionManager` 没有 `isAuthenticated(Player)`（只有 getPlayerSession + isLoggedIn）——反射回退失败则 fail-open 放行

## MCSM 本地栈 Docker 实例（2026-09-03 迁移实测，五连坑）

本地测试服（Paper/Folia）已迁入本机 MCSM 栈（mcs.{SERVER_NAME}.cn）管理，**双 Docker 实例（2026-09-11 起各自独立地图，可同时运行）**：
- 实例 `papermc-test`（uuid 716c2fb7）/ `folia-test`（uuid 8A932DD4），共享 world `/Users/Shared/orzmc/worlds/test`（extraVolumes 挂两实例容器 `/server/world`），**严禁同跑**（同 25565 + world 双写毁档；daemon 软关闭 skip docker 实例——切实例前必须面板手动停另一台）
- 面板 UI 建实例默认**进程模式**（模板误导）；改 Docker 走 InstanceConfig JSON：停实例 → 改 `daemon/data/InstanceConfig/<uuid>.json` → 重启 daemon 容器 → 面板启动
- **五连坑**：
  1. `extraVolumes` 元素分隔符是 **`|`（竖线）**：`"宿主路径|容器路径"`（daemon 源码 `item.split("|")` 实证；用 `:` 或加 `:rw` 报"额外挂载路径配置长度不正确"）
  2. daemon 容器必须设 env **`MCSM_DOCKER_WORKSPACE_PATH=<宿主 InstanceData 绝对路径>`**，否则 docker 实例 cwd bind 用容器内路径（`/opt/mcsmanager/daemon/data/...`）→ 宿主引擎报 `bind source path does not exist`（ADR-019 移除旧 instances 时把此 env 一起删了，macOS/Linux compose 也需；已补进 kit compose.yaml daemon environment）
  3. 容器 `memory`（MB）必须 **> Xmx + JVM overhead**：Xmx2G + limit 2048MB → JVM 无内存余量跑 ~2min 后 SIGSEGV 崩溃（`hs_err_pid1.log` 的 `method_hash` 崩溃实证）→ 2G 堆配 4096
  4. `docker.ports` 字符串数组 `["25565:25565/tcp"]`、memory 单位 MB、`pty:true` 防日志乱码（papermc-template.md 已有）；UI 建完手工改 JSON 字段：processType=docker、image、ports、memory、networkMode=orzmc_default、workingDir=/server、changeWorkdir=true、extraVolumes
  5. **手工克隆实例**：uuidgen → mkdir InstanceData/<uuid> → rsync 数据（排除 world/logs/cache/backups）→ cp 现有实例 JSON 改 nickname/cwd/startCommand/jar 名 → 重启 daemon 即注册（面板出现，无需 UI 建）
- 迁移数据注意：jar 复制成固定名（paper.jar/folia.jar，升级换 jar 不动命令）；各实例 `plugins/OrzMC/easybot.yml` 是**独立拷贝**——逐个核对 api_server 指向（Folia 曾残留旧 `test-bot.{SERVER_NAME}.cn` → 502，改 `easybot.{SERVER_NAME}.cn` + 重启实例生效）
- **eventTask.autoRestart 实测语义（2026-09-05，papermc-test 实证）**：控制台 `restart` 命令/进程崩溃退出 → daemon `stopped()` 检测退出且 `!ignore && autoRestart` → 自动 `execPreset("start")` 重建容器（实例 API `data.autoRestarted` 计数 +1）。⚠️ 控制台 `restart` 之前「只停不启」根因 = 默认 `autoRestart: false`——Paper restart 命令本质是**退出 JVM**（保存世界后进程结束，Docker 容器主进程退出），重启必须靠外部守护（MCSM autoRestart / wrapper 循环），命令自身不含拉起逻辑；右上角重启按钮 = daemon 主动 stop+start 与服务器内部命令无关所以必成。**⚠️⚠️ 2026-09-05 连环坑（面板 stop 的真实机制 + 三个陷阱）**：① **面板/API stop 会调 `ignoreEventTaskOnce()` 置 `eventTask.ignore=true` 并持久化到磁盘**（防 stop 后被 autoRestart 拉起）——所以「面板 stop 不触发重启」不是 daemon 区分主动停止，而是 ignore 开关！**副作用：ignore=true 残留磁盘 → autoRestart 名存实亡**（`stopped()` 里 `!ignore && autoRestart` 才重启）→ 开 autoRestart 后如遇"不自动重启了"先查磁盘 JSON `ignore` 是否被 stop 置 true；daemon 加载实例时虽内存复位 false（`instanceConfig.eventTask.ignore = false`）但**磁盘不更新**直到下次 store，手动改 JSON 才是持久修复。② **`InstanceConfig/` 目录禁放备份/杂项 json**（同 web/data 子目录坑）：`storage.list()` 不去扩展名，备份文件 `xxx.json.bak-YYYYMMDD` 被当实例 uuid → load 拼 `.json.json` 不存在 → 加载失败 `初始化实例失败，唯一标识符或配置参数为空`（daemon 启动日志 ERROR + 「总计 N 个」少 1）——备份放 `~/backups/`，勿放数据目录。③ **daemon 重启会接管运行中的孤儿容器**：stop 流程被打断（如 stop 后立刻 restart daemon）容器残留 → daemon 每次重启发现 label `mcsmanager.instance.uuid` 容器在跑 → 自动接管并打「实例启动成功」日志（非 autoStart/autoRestart 触发！autoStart:false 也会）→ 反复"自动启动"假象。**停带 autoRestart 实例的干净姿势**：临时改 JSON `autoRestart:false` → restart daemon → API stop 或 docker stop 孤儿容器（AutoRemove 自动删）→ 确认无容器+状态 0 → 改回 `autoRestart:true` → 再 restart daemon（实例停止无容器则不会自动启动）。启用姿势：备份 JSON（到 ~/backups/ 非 InstanceConfig/）→ `eventTask.autoRestart: true`（`autoRestartMaxTimes: -1`=无限次可设限防崩溃死循环；**`ignore: true` 即使 autoRestart=true 也禁用**）→ `docker restart orzmc-mcsmanager-daemon` 重载 → API 验证 `config.eventTask.autoRestart` 且 `ignore:false`。已启用：papermc-test(716c2f)；未启用：folia-test(8A932)

## 支持文件

- `references/testing.md`：Paper 26 测试踩坑明细
- `references/permission-impl.md`：LP track API 原生钳位语义 + 权限链设计决策链
- `references/review-framework.md`：插件 PR 代码审查清单
- `references/dependency-upgrade-audit.md`：发版前依赖升级核查
- `references/easybot-delivery-verify.md`：EasyBot 通知送达验证
- `references/entity-diagnostics.md`：实体统计与卡顿定位
- `scripts/rcon-node.js` / `rcon.py`：RCON 客户端
- 验收交付物：`~/OrzMC/plugin/docs/test-cases.md`（28 项用例）+ `e2e-test-report-20260806.md`

---

## 附：Bot 命令测试 / 机器人 E2E / Paper 26 踩坑（2026-11-10 合并）

### 附.1 OrzMC Bot 命令测试 & 控制台注入（2026-08-06 实测）
> 来源：原 `references/testing.md`（2026-11-10 并入，内容未改写）

## 群指令帮助系统（2026-08-13 改版，PR OrzGeeker/OrzMC#12，源码 1.0.17 起）

**老板定稿样式（改版后，别再用下面的旧输出做断言）**：
- **`$h` 总帮助**：`🤖 OrzMC 群指令帮助` + `发送「$x ?」可查看单个指令的用法示例` + ASCII 虚线分隔（`-----------------------------------------`，与其他消息一致）+ emoji 分组标题 `👨‍💼 管理员指令` / `👨🏻‍💻 通用指令`（**无中文方括号、无冒号尾缀**）+ 命令列表（10 半角空格对齐，如 `$a          添加玩家到白名单`）
- **`$x ?` 单命令帮助**：统一三段式模板（`BotCommandFeedbackService.usageBlock()` 单一生成器）：
  ```
  🎯 $v 审核申请
  -----------------------------------------
  📚 用法：
  $v l [页码]       查看待审列表
  $v y <玩家>       通过申请
  $v n <玩家>       拒绝申请
  -----------------------------------------
  🚀 示例：
  $v l
  $v l 2
  $v y Steve
  ```
- **参数标记语义**：必选 `<玩家>`/`<控制台命令>`，可选 `[页码]`/`[IP]`（`$d` 无参=查看，`[IP]` 属可选操作数）
- **11 命令全有 usageTip**（含 `$l/$w/$h/$b/$o`），`$cmd ?` 永不降级执行

**`$cmd ?` 拦截语义（源码 BotCommandService.parse，防误触核心）**：
- **前缀匹配**：`$b ?x`/`$b ??`/`$b ? 2` 均视为帮助请求（`rawArgs.startsWith("?")`）——因 `handleBackup`/`handleOptimize` 忽略 rawArgs 直接执行，精确匹配会让 `?` 后缀变体误触发重量级操作
- **`$e` 特判精确匹配**：控制台命令本身可能以 `?` 开头（`$e ?list` 合法）→ 仅 `$e ?`/`$e ？` 是帮助
- **U+3000 全角空格归一化**：`extractArgs(...).replace('\u3000', ' ').trim()`——Java `String.trim()` 不去全角空格，`$b　?`（全角空格分隔）会绕过拦截直接触发备份（Claude Code 审查 M1 发现，已修）
- **fallback 收敛原则**：无参数/参数不完整（`$p` 空参/缺玩家/非法子命令、`$v` 空参/非法、`$a` 空名、`$e` 空参）一律 `emitUsage(usageTip(...))` 与 `$x ?` 同源，**绝不降级为执行命令**
- **非管理员 `$b ?`**：拦截先于 `guardAdminCommand`，非管理员也先拿帮助（信息面略扩大，有意为之）

**回归测试**：`BotCommandServiceTest` 有 10 个 parse 层用例（`$b ?`/`$o ?` 零执行 backup/optimize、fallback 文本 == usageTip、`$e ?list` 正常执行）；`BotCommandFeedbackServiceTest.usageTip_forEveryCommand_usesUnifiedTemplate` 双前缀（`$`/`!`）断言。

## 🔧 扩展新群指令的框架（2026-08-07 权限系统方向调研）
用户问「权限指令能否走群指令执行」→ 答案：**完全可以**，OrzUserCmd 枚举 + handler map 是现成扩展点（EasyBot 网关已接 QQ/飞书）。扩展一个群指令三步：
1. **`OrzUserCmd.java` 加枚举**：`NEW_CMD("x", "描述", needAdminPermission)` —— 第三个参数 `true`=仅群管理员（isAdmin，来自 EasyBot 群角色）可执行
2. **`BotCommandService` 注册 handler**：`handlers.put(OrzUserCmd.NEW_CMD, this::handleNewCmd)`，handler 签名 `(OrzUserCmd cmd, boolean isAdmin, Consumer<MessageEnvelope> callback, String rawArgs)`；`rawArgs` = 去掉 `$x` 前缀后的参数
3. **`BotCommandFeedbackService.usageTip` 加提示**（支持 `$x ?` 查询）
关键设计点：**群 isAdmin 与游戏内 LP admin 组是两套身份体系**——群审核类命令（如 `$approve`）用群管理员身份即可，无需绑定游戏 UUID。`$e`（执行控制台命令）已能间接操作 LP（`$e lp user X parent add builder`）但无校验、易出错——专用群指令（如 `$rank <名>` 查询 / `$approve <名>` / `$reject <名>` 审核）是更优交互。注意：`$d` 黑名单用 `-` 前缀表移除（`rawArgs.startsWith("-")`），设计新命令避免撞此约定。

## 背景
OrzMC 插件的 Bot 命令（`$l/$w/$h/$a/$r/$b/$o/$e/$d`）正常由**真实群消息**触发（EasyBot WS 推送 message.inbound → `BotInboundDispatcher.dispatch` → `BotInboundHandler.handleMessage`）。插件另提供 `debug <cmd>` 控制台命令模拟群里用户发命令（`OrzDebugEvent.cmdDebugHandler` → `ServerCommandEvent` → 异步 `handleMessage`）。

## ⚠️ Bug：debug 命令在 Paper 26.2 完全不可用（✅ 已修复，PR #159）
**现象**：控制台输入 `debug $h` → `Incorrect argument for command`；改任意其他前缀（如 `debugx`）→ `Unknown command`。
**根因（两层）**：
1. Paper 1.20+ 有**原版 `/debug` 命令**抢占 `debug` 前缀 → 参数解析在事件前失败
2. **未注册的命令根本不触发 `ServerCommandEvent`**（RCON/玩家通道也一样）——事件只在已注册命令执行时触发
**修复（源码级，两处）**：
1. `OrzDebugEvent.java`：前缀 `"debug"` → `"orzdebug"`（避开原版命令）
2. `FeatureModule.java` setupCommandHandlers：**注册 `orzdebug` 命令**（Brigadier，greedyString 参数）——否则命令解析器不放行，事件不触发
3. `OrzDebugEventTest.java`：断言同步改 `orzdebug`（旧前缀测试会挂——`spotlessApply test` 全绿是提 PR 前的必过门禁）
**教训**：`OrzDebugEventTest` 单元测试用 Mockito mock 直接调 handler，**绕过了真实命令解析**，掩盖了此问题——源码 bug 修完必须真实环境验证（控制台注入实测），单元测试通过≠可用。PR 已提：github.com/OrzMC/OrzMCPlugin/pull/159（分支 fix/orzdebug-command）。

## 🔧 控制台注入技术（测 ServerCommandEvent / 控制台命令）
**关键事实**：`ServerCommandEvent` **只对真实控制台 stdin 输入触发**：
- ❌ RCON 命令：不触发（Essentials 记录的 "Rcon issued server command" 是 Essentials 自己监听，非 Bukkit 事件）
- ❌ 玩家 `/cmd`：走 PlayerCommandPreprocessEvent，不触发
- ❌ Hermes 后台进程 stdin：`/dev/null`（`lsof -p <pid> | grep 0u` 可见），`process write` 报 "stdin not available"
- ✅ **screen 会话**：`screen -S mc` 起服 + `screen -S mc -p 0 -X stuff '命令\n'` 模拟真实控制台输入（实测 `say`/`orzdebug` 均生效）

**命令**：
```bash
# 2026-09-03 迁 MCSM 后：起服 = 面板启动实例（无 screen/start.sh）
# orzdebug 注入 = bot 玩家游戏内执行 /orzdebug（Paper 26 Brigadier 命令不触发 RCON 事件；RCON 直连见 scripts/rcon.py）
```
注意：`screen -X hardcopy` 在 detached 模式下可能输出空文件；判断命令生效看 `logs/latest.log`（如 `[OrzMC] cmd debug:`）。

## RCON 辅助（远程查询用）
测试服默认 `enable-rcon=false`。需要时：server.properties 改 `enable-rcon=true` + 设 password + 重启。macOS 无 mcrcon → 用 Python 原生 RCON 协议（**必须完整读响应包**：先 recv(4) 长度 → 循环读满；RCON 会先发空包再发响应，v1 只 recv 一次会漏输出）。`say`/`list`/`bot` 等已注册命令可经 RCON 执行（但**不触发** ServerCommandEvent——见上）。

## OrzMC Bot 命令测试矩阵（via `orzdebug <cmd>`，9/9 实测通过 2026-08-06）
| 命令 | 用途 | 实测输出 |
|:--|:--|:--|
| `$h` | 帮助 | ✅ `🤖 OrzMC 群指令帮助` + `发送「$x ?」可查看单个指令的用法示例`（2026-08-13 改版后样式，见上「群指令帮助系统」节） |
| `$l` | 在线玩家 | ✅ `------当前在线(0/20)------` |
| `$w` | 白名单 | ✅ `------当前白名单玩家(N)------` + 分页 |
| `$a <名>` | 加白 | ✅ `✔︎ <名>`（写操作，测完必须 `$r` 还原）|
| `$r <名>` | 移白 | ✅ 移除确认 |
| `$d` | IP 黑名单 | ✅ 查/加/移除全通 |
| `$b` | 地图备份 | ✅ 三阶段进度（CopyMiscProgress→Compress→Cleanup）→ `地图备份 完成 用时:1249ms` |
| `$e <cmd>` | 控制台命令 | ✅ `命令已执行: say 群测命令` + 服务器实际广播 `[Server] 群测命令` |
| `$o` | 地图优化 | ✅ `地图优化功能已禁用`（optimize_enabled=false 时正确提示）|

⚠️ **`$d` 语法坑**：**不是 `add/remove` 子命令**——`$d IP` = 添加、`$d -IP` = 移除、`$d`（空参）= 查询。实测 `$d add 9.9.9.9` 会被当作「添加名为 'add 9.9.9.9' 的黑名单项」（输出 `已添加: add 9.9.9.9`，产生脏数据），需用 `$d -add 9.9.9.9` 清理。源码：BotCommandService.handleBlacklist——`rawArgs.startsWith("-")` 走移除，否则走添加。

调试输出在 `logs/latest.log` 的 `[OrzMC] cmd debug:` 行（env.message() 内容，多行）。

## 相关链路（EasyBot WS）
- `ws_server` 连不上时 `/bot` 显示 `wsNotOk`；连上后 `wsOk`。`/bot http` `/bot ws` 看详情
- `httpUnknown` = HTTP 健康检查异步未完成（设计状态，非 bug）
- 群通知发送失败看投递诊断（`scripts/easybot_deliveries.py`，0.0.33 起走 API 查 `messages` 表；勿再用 docker cp 查 `outbound_deliveries`——已停止写入）——`11244 token not exist or expire` = QQ token 2h 过期（0.0.33 CachedTokenStore 发送时自动刷新，通常自愈；仍失败可重启 adapter `POST /api/v1/adapters/qq/start`）

## 其他命令补测（同批 2026-08-06，均通过）
- **`/config`**（控制台可测，screen 注入）：`list`（24 项可运行时配置）/ `get <路径>`（值+类型+默认+说明）/ `set <路径> <值>`（持久化，输出 `已设置: ...`）/ `reset <路径>`（恢复默认，输出 `已恢复默认: ...`）/ `dump`（完整配置树含默认值）/ `reload`（`所有配置文件已重新加载`）/ 无参数（用法帮助）。⚠️ 改 `tnt.enable` 等运行时配置**即时生效无需重启**（`currentPolicy()` 每次实时读 configs）——测完必须 set 回原值
- **`/guide`**：打开书 GUI（`GuideService.openGuide` → `player.openBook`），玩家命令（RCON 会 ClassCastException，因为 `(Player) sender` 强转）——mineflayer 看不到书内容，判定看无异常+源码
- **`/menu`**：打开菜单 GUI（`MenuCommandService.handle` → `openMenu`），同样必须玩家身份执行
- **mineflayer 放置方块受限**：`placeBlock` 对 TNT 和对照 dirt 均失败（blockUpdate 超时，出生点区域无领地 claim 但工具仍失败）——TNT 放置保护实测受限，判定靠源码 4 拦截点（BlockPlace/BlockPreDispense/BlockExplode/EntityExplode）+ TNTPrime；`summon tnt` 也不触发通知链。工具限制非插件问题

## 第二批补充真实测试（同批 2026-08-06，全部通过）

第一批覆盖 Bot 命令/命令类；本批补登录拦截链 + 通知链路 + 菜单交互（全部真实环境实测）：

| 测试项 | 方法 | 结果 |
|:--|:--|:--|
| **黑名单 IP 拦截登录** | `orzdebug $d 127.0.0.1` 加黑 → 新 bot 登录 | ✅ 被踢，reason JSON 逐字 = `你的IP已被禁止访问`（AsyncPlayerPreLoginEvent disallow，与源码 `styles.error` 一致）。测完 `$d -127.0.0.1` 移除 |
| **维护模式踢出在线玩家** | bot 在线时触发 `orzdebug $b` | ✅ 日志 `TestPlayer lost connection: 服务器地图备份中，请稍后再尝试登录。` + `[OrzMC] TestPlayer 生存模式 被踢`（KICK 通知）→ `下线`（QUIT 通知）|
| **server_load 启动通知** | 查 gateway.db | ✅ 每次重启后飞书群+QQ 群均收到 `Minecraft 26.2 离线服\n------\n启动完成\n\n发送 "$h" 查看支持的命令消息`，state=succeeded |
| **菜单点击交互** | mineflayer `/menu` → `windowOpen` → `clickWindow(i,0,0)` 点 stone | ✅ 收到 `功能开发中`（MenuEventService.handleClick → InventoryClickEvent 取消默认 + onClick 链路）|

**维护模式机制**（`WorldMaintenanceService.runExclusive`）：`running` AtomicBoolean 置位 → **踢出所有在线玩家**（`p.kick("服务器地图备份中...")`）→ `save-off` + `save-all flush` → 异步执行备份/优化 → `save-on` + 复位。登录拒绝走 `OrzPlayerEvent.onPlayerPreLogin` 的 `isRunning() → disallow`（与黑名单同路径）。无手动开关、无 config 开关——只能靠 `$b`/`$o` 触发窗口（备份 ~1-2s，抓窗口需 bot 提前在线等踢，登录窗口几乎抓不到，用踢出分支验证即可）。

**通知送达验证（0.0.33+）**：投递记录在 `messages` 表（`outbound_deliveries` 已停止写入）；且 SQLite WAL 下 `docker cp` 单文件漏最近提交 → **用 API**：`POST /admin/login {password}` → `GET /api/v1/messages?limit=30`（`raw_data.result.success` 判定成败；`role=Assistant` 出站）。现成脚本 `scripts/easybot_deliveries.py`。内嵌 python heredoc 会被守卫拦，写脚本文件执行。

**mineflayer 射箭坑（传送弓）**：`activateItem()` 单独调用**不触发完整射箭**（EntityShootBowEvent/ProjectileHitEvent 不触发，位置不变、日志无痕迹）——需要完整拉弓充能时序。传送弓完整链路（`/tpbow` → `你获得了传送弓` → 射箭 → `[传送弓] 传送完成!`）此前验收已过，重测射箭失败是工具时序问题非插件问题。

**测试顺序建议**：写操作（`$a`/`$d add`/`$b`）按「测前记录原值 → 测 → 立即还原」执行；`$d` 还原用 `$d -<ip>`；黑名单测试用 127.0.0.1（本机 bot 的 IP）不会误伤线上。

### 附.2 OrzMC 权限审核框架 · 机器人自动化 E2E 测试（2026-08-07）
> 来源：原 `references/testing.md`（2026-11-10 并入，内容未改写）

> 场景：用户要求「用机器人自动化的做测试」——验证通用审核框架全链路：
> 玩家 `/apply` 提交 → 群通知 → `$v l` 待审列表 → `$v y` 通过 → LP 授权 → 玩家游戏内收到结果。

## 通道选择（EasyBot 无模拟入站 API，两条真实通道）

| 通道 | 身份 | 用途 | 实现 |
|:--|:--|:--|:--|
| RCON + orzdebug | 群管理员（isAdmin=true） | 测群指令 `$v l/y/n` | `python3 rcon.py 'orzdebug $v l'` 或 `node scripts/rcon.js "orzdebug $v l"` |
| Mineflayer bot | 真实玩家 | 测玩家命令 `/apply /rank /apply status` | `~/minecraft-bot/review-e2e.js`（模板，见下） |

- EasyBot `/api/v1/messages/ingest|inject|emit` 均 404——无法 API 伪造群消息（见 easybot-gateway-ops 技能）
- **OrzDebugEvent 需已修复 RCON 支持**（2026-08-07）：双事件监听 `ServerCommandEvent` + `RemoteServerCommandEvent` + 剥前导斜杠；否则 RCON 的 orzdebug 只走 Brigadier 分支（回显「debug 已受理」）不触发 Bot 模拟
- 测试服 easybot.yml 连 test-bot 测试网关（飞书测试群），不会打扰生产群——自动化测试前先确认目标群

## 测试账号（本地测试服）

| 账号 | 密码 | LP 组 | 用途 |
|:--|:--|:--|:--|
| TestNewbie | NewbiePass123 | default（本地 promoted 标记=member 资格） | 提交 builder 申请 |
| TestMember | MemberPass123 | member | 补充测试 |
| TestAdmin | AdminPass123 | admin | — |

- 资格预检基于**本地状态**（permission.yml promoted 标记 / APPROVED 记录），不是 LP 实际组——测试前确认玩家在 permission.yml 有 member 资格
- 通过审核后玩家变 builder → 无法再申请（资格预检拦截），重测需重置：停服 → 清 permission.yml reviews 节 + LP 移除 builder 组 → 重启

## 自动化脚本模式（review-e2e.js）

```js
// 关键结构：async 主流程 + 原生 node RCON（不经 shell，$ 安全）
const net = require('net');
function rcon(cmd) { /* 见 scripts/rcon.js 实现，返回 Promise */ }
(async () => {
  console.log(await rcon('orzdebug $v l'));        // 阶段0：待审列表
  const bot = mineflayer.createBot({...});          // 阶段1：bot 进服 + /login
  bot.on('message', m => { if (/请输入 \/login/.test(m)) bot.chat('/login ...'); });
  await spawn; bot.chat('/apply builder 想用WorldEdit建造');
  await sleep(6000);
  console.log(await rcon('orzdebug $v y TestNewbie'));  // 阶段3：管理员通过
  bot.chat('/apply status'); bot.chat('/rank');     // 阶段4/5：玩家查结果
})();
```

- bot 进服会被出生点怪物杀（spawn 重复触发）——主流程用 async/await 顺序控制，别依赖 spawn 事件驱动阶段
- 阶段判定看**游戏内消息**（bot.on('message')）+ **服务器日志**（grep `cmd debug`）+ **LP 日志**（`[LP] xxx 繼承 builder 的權限` = 授权真实生效）

## 验证闭环（按此顺序取证）

1. **玩家侧**：bot 收到「申请已提交」→ `/apply status` 显示 `⏳ 待审核` → `/rank` 显示当前组+进度+下一步可申请
2. **管理员侧**：`$v l` 列表含 `[晋升建造者] 玩家（当前组：member）：申请晋升 builder：理由（X分钟前 提交）`
3. **结果通知**：`$v y` 后 bot 收到「你的「晋升建造者」申请已通过！」→ `/apply status` 变 `✅ 已通过（群管理员）`
4. **LP 真实授权**：服务器日志 `[luckperms-command-executor/INFO]: [LP] testnewbie 現在從環境 global 中繼承 builder 的權限`（LP 命令回显中文 locale）
5. **群通知**：EasyBot gateway.db deliveries 全 succeeded（outbound 链路）

## 踩坑记录（本会话实测）

1. **OrzDebugEvent 不响应 RCON**：Paper 26 RCON 命令触发 `RemoteServerCommandEvent`（ServerCommandEvent 子类），但原监听只有父类且 `startsWith("orzdebug")` 遇前导 `/` 失配 → 修复双事件 + 剥斜杠（已合入插件）
2. **异步 dispatchCommand 崩溃**：`$v y` 走 runTaskAsynchronously → handler 调 LP 命令抛 `IllegalStateException: Asynchronous Command Dispatched Async`，**审核状态已 APPROVED 但 LP 未授权**（状态与权限不一致的隐蔽 bug）→ 修复注入 ServerScheduler 回主线程
3. **shell 展开 $v**：`execSync("python3 rcon.py 'orzdebug $v l'")` → bash 把 `$v` 展开为空，服务器收到 `orzdebug  l` 静默无效 → 用 spawnSync 数组参数或原生 net
4. **node RCON length 字段**：`writeInt32LE(payload.length)` 少算 8 字节（id+type 头）→ 服务器立即断开 `read_packet: unpack requires 4 bytes` → 必须 `payload.length + 8`（含 2 null 共 +10）
5. **markAlwaysSave 覆盖**：运行中清 permission.yml reviews 节 → 重启后数据回来（关服保存内存态）→ 必须先停服再改文件
6. **python 子进程环境差异**：node spawnSync 调系统 python3 与 shell 直跑结果不同（PATH/环境）——测试脚本内用原生实现最稳，别依赖子进程

## 复用

- `scripts/rcon.js` — 通用 node RCON 客户端（`$` 安全），任何测 Bot 命令场景直接用
- `~/minecraft-bot/review-e2e.js` — 完整审核链路 E2E 模板（改 BOT_NAME/密码/命令即可适配新审核类型）

### 附.3 Paper 26 测试踩坑明细（2026-08-07 权限系统二期 E2E 实测）
> 来源：原 `references/testing.md`（2026-11-10 并入，内容未改写）

> ⚠️ **2026-09-03 迁移标注**：本地测试服已迁 MCSM 本机栈（mcs.{SERVER_NAME}.cn Docker 实例，数据在 `/Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/<uuid>`）。文中 `~/minecraft-server`、`~/folia-test` 路径及裸跑/symlink 机制为迁移前历史状态，已失效；现行拓扑见 `testing.md`。

本文件记录在本地测试服（Paper 26.2-92, papermc-test）做插件 E2E 时遇到的全部非平凡问题与证据链。

## 1. Brigadier 命令不触发 ServerCommandEvent（OrzDebugEvent 彻底失效）

**现象**：`orzdebug $v l` 执行只输出 Brigadier 分支的「debug 已受理」，Bot 模拟分支（`cmd debug:` 日志）永远不触发。

**根因（2026-08-07 二次实测修正）**：`OrzDebugEvent.cmdDebugHandler` 监听 `ServerCommandEvent`/`RemoteServerCommandEvent`，但 **Paper 26 中 Brigadier 注册的命令（`literal("orzdebug")`）根本不派发这两个事件**——Brigadier 命令有自己的分发路径。「X issued server command」日志是 Bukkit 通用命令日志，**不代表**事件触发。用分层日志实测确认：事件监听器入口日志（`ServerCommandEvent 触发`）从未出现，而 `.executes()` 内「已受理」正常输出。

**早期错误修复（已废弃）**：双事件注册 + 剥斜杠（`cmdDebugHandler(ServerCommandEvent)` + `rconDebugHandler(RemoteServerCommandEvent)`）。无效——事件根本没触发。

**正确修复**：直接在 Brigadier `.executes()` 里调用 BotInboundHandler：
```java
literal("orzdebug")
    .then(argument("cmd", StringArgumentType.greedyString())
        .executes(ctx -> {
            String cmd = ctx.getArgument("cmd", String.class);
            ctx.getSource().getSender().sendMessage("debug 已受理（模拟 Bot 入站命令）");
            var inbound = botModule.botInboundHandler();   // FeatureModule 字段
            plugin.getServer().getScheduler().runTaskAsynchronously(plugin, () -> {
                try {
                    inbound.handleMessage(cmd, true,
                        env -> { if (env != null) plugin.getLogger().info("cmd debug: \n" + env.message()); });
                } catch (Exception e) {
                    plugin.getLogger().log(Level.SEVERE, "debug 命令异步执行异常", e);
                }
            });
            return 1;
        }))
```
**验证**：日志出现完整链路 `parse 匹配: cmd=v ... → handleReview 进入 → emit → cmd debug:`。

**通用教训**：事件监听器依赖 `ServerCommandEvent` 捕获命令的调试桥在 Paper 26 不可靠；需要「命令 → 代码」直连时在 Brigadier 注册点直接接线，别绕事件。

## 1b. 断链分层调试法（定位"受理了但无效果"）

群指令/异步链路出现「入口有反应、业务无效果」时，**从入口到出口每层加一行日志，一次部署一次实测**：
```
事件监听器/executes 入口 → parse 匹配（cmd=xxx rawArgs=yyy）→ handler 进入 → emit（templateKey/fallback/env）
```
本例正是靠 `[OrzMC-debug]` 分层日志发现断点在第 0 层（事件监听器），从而避免继续误修 review 业务逻辑。**纯单测禁用 `Bukkit.getLogger()`**（无 MockBukkit 时 `Bukkit.server` 为 null → NPE），调试日志用 `java.util.logging.Logger.getLogger("OrzMC.Xxx")`。

## 1c. `$v y <玩家>` 离线玩家名解析

**现象**：群指令 `$v y TestNewbie` 受理但「找不到待审申请」，而游戏内 `/review approve TestNewbie` 成功——两者定位代码不同：
- 游戏内 `reviewByApplicantName` 用 `lookup.resolve(name)`（usercache，离线可解析）✅
- 群指令旧实现用 `Bukkit.getOfflinePlayer(uuid).getName()` → 离线玩家返回 null → 匹配失败 ❌

**修复**：群指令决策统一走 `reviewByApplicantName`（或 PlayerLookup 端口），不要用 `getOfflinePlayer().getName()`。

## 1d. 部署 jar 版本名变更 → 静默拷旧 jar

构建产物名带版本（`OrzMC-1.0.15-dev.jar` → bump 后 `OrzMC-1.0.16-dev.jar`）。部署命令若写死旧名：`cp build/libs/OrzMC-1.0.15-dev.jar plugins/` → 源不存在，**旧 jar 残留，改动完全不生效**，表现为「改了代码重测还是老行为」。**部署后必验**：
- `ls -la build/libs/*.jar plugins/OrzMC*.jar` 时间戳一致
- `grep "Enabling OrzMC" logs/latest.log` 确认版本号
- `ls plugins/OrzMC*.jar` 确认无残留旧名 jar（同名覆盖原则）

## 2. LP 命令异步 dispatch 崩溃

**现象**：`$v y TestNewbie`（经 orzdebug，异步线程）→ 日志：
```
java.lang.IllegalStateException: Asynchronous Command Dispatched Async: lp user TestNewbie parent add builder!
	at LuckPermsPromoter.dispatch(LuckPermsPromoter.java:76)
```
审核状态流转其实已成功（记录 APPROVED），但 LP 授权命令没执行。

**根因**：Paper 禁止在异步线程 dispatch 命令。群指令/orzdebug 链路走 `runTaskAsynchronously`。

**修复**：Promoter 注入 `ServerScheduler` 端口，非主线程回主线程：
```java
if (Bukkit.isPrimaryThread() || scheduler == null) {
    server.dispatchCommand(Bukkit.getConsoleSender(), command);
} else {
    scheduler.runSync(() -> server.dispatchCommand(Bukkit.getConsoleSender(), command));
}
```
构造重载（`(ServerAccess, PlayerNameResolver)` 不带 scheduler）保持单测兼容（mock 环境 isPrimaryThread=false → 走同步直发分支）。

**⚠️ 进阶坑：runSync 异常被吞**。`runSync` 内部是 `Bukkit.getScheduler().runTask(...)`，任务抛出的异常**只打印日志、不传播回调用方**。若业务需要感知授权成败（如「审核通过但 LP 授权失败 → 状态回滚」），必须显式等待并传播：
```java
CompletableFuture<Void> done = new CompletableFuture<>();
scheduler.runSync(() -> {
    try {
        server.dispatchCommand(Bukkit.getConsoleSender(), command);
        done.complete(null);
    } catch (Throwable t) {
        done.completeExceptionally(t);
    }
});
done.join(); // 阻塞异步线程直到主线程派发完成，异常以 CompletionException 抛出
```
**审核状态一致性顺序**：`review()` 必须**先执行 handler（LP 授权）再落状态**（save APPROVED），授权失败时申请保持 PENDING 并返回失败——否则出现「玩家看到已通过、实际无权限」的永久不一致。对应测试断言：`verify(store, never()).save(argThat(APPROVED))`。

**验证**：修复后日志出现 `[LP] testnewbie 已經從環境 global 中繼承了 builder.`（玩家离线也成功 → OfflinePlayer 解析生效）。

## 3. RCON 包 length 字段语义

**错误写法**（服务器立即断连，python 报 `struct.error: unpack requires a buffer of 4 bytes`）：
```js
pkt.writeInt32LE(body.length, 0);  // 漏算 id+type 8 字节
```
**正确**：`length = id(4) + type(4) + payload + 2 null` 总长 = `body.length + 8`（其中 body = payload + 2 null）。
认证响应 `id=1 type=2`，命令响应 `type=0`，失败 `id=-1`。

## 4. `$` 命令被 shell 展开

`execSync('python3 rcon.py "orzdebug $v l" ...')` → bash 把 `$v` 展开为空 → 命令变成 `orzdebug  l`。
- bash 里：用单引号包裹 `'orzdebug $v l'`
- node 里：spawnSync 数组参数（不经 shell）或原生 net 实现
- **注意**：`node -e "..."` 嵌套时 bash 先展开外层 `$`，调试要看实际执行的 argv

## 5. node 子进程 python 环境差异

`spawnSync('python3', ...)` 在 node 里失败、terminal 里成功，且服务器日志无连接记录。
原因复杂（PATH/python 版本/shell 差异），**结论：node 脚本内做 RCON 直接用原生 net 实现**（`scripts/rcon-node.js`），不要调 python 子进程。

## 6. markAlwaysSave 配置覆盖陷阱

**现象**：停服前改了 `permission.yml` 清空 reviews，重启后数据还在（/apply status 仍显示已通过）。

**根因**：插件 markAlwaysSave 配置在服务器关闭时用**内存态**覆盖写回文件。运行中改文件无效。

**正确流程**：**停服 → 改文件 → 再启服**。或利用「关闭时写回」——先停服（触发写回）再改。

## 7. 其他

- **bot 快速重连限流**：同一账号退出后立刻重进 → `进服超时`。两次进服间 sleep 8-10s。
- **Minecraft 协议 25565 状态查询**：TCP 可连但响应超时（socket.timeout），不可靠；RCON 才是可靠控制通道。
- **LP 状态查询**：`lp user X info` RCON 无回显、audit 日志存 H2（服务器运行中 DB 被占用不可读）。验证 LP 授权真实性 → 用玩家侧组专属命令实测（builder 组 `//wand` → WE 木斧提示）。
- **测试脚本模板**（沉淀于 `~/minecraft-bot/`）：`review-e2e.js`（提交→列表→通过→status→rank）、`review-e2e-2.js`（预检拒绝→$v n 拒绝→重申请→cancel 撤回）、`review-real.js`（真实玩家场景：提交→下线→离线审核→重连验证）。

## 9. $v 群指令全链路验收证据模板（2026-08-07 实测通过）

修复 orzdebug 链路后，`$v l/y/n` 全链路验收的标准输出对照：

```
# $v l（待审列表，含类型/玩家/当前组/内容摘要/相对时间）
------待审核申请------
第1/1页
[晋升建造者] TestMember（当前组：member）：申请晋升 builder：验收 $v 列表功能（刚刚 提交）

# $v n <玩家>（拒绝）→ 日志 cmd debug + 记录 REJECTED + reviewer=群管理员
已拒绝 TestMember 的「晋升建造者」申请。
      status: REJECTED
      reviewed-at: <epoch-ms>
      reviewer: 群管理员

# $v y <玩家>（通过）→ 日志先出现 LP 授权再落状态
[LP] LOG > (Console) [U] (testmember)
[LP] LOG > parent add builder
      status: APPROVED
      reviewer: 群管理员
# LP 组确认：builder + member（叠加，不替换原组）
```

**关键顺序**：`$v y` 的 LP 授权（`parent add builder`）**先于**状态落盘（APPROVED），若授权失败记录保持 PENDING（review() 先 handler 后 save 的设计）。拒绝/通过后**玩家可立即重新申请**（REJECTED/APPROVED 都不阻塞新申请，只有 PENDING 防重）。

**群指令结果输出**：orzdebug 模拟时结果打到服务器日志（`cmd debug:` 前缀）；真实 EasyBot 群连接时走 sink 发回群聊（本地无真实群则只见日志，且可能报 `EasyBot 批量发送失败 status=409`——**那是通知发送失败，不是审核失败**，别误判）。


**现象**：`ReviewNotifierAdapter.groupEvent()` 传 vars `{player, type, summary, reviewer}`，但仓库默认模板是 `review_submitted: "{message}"`（vars 里**没有 message 键**）→ 渲染结果就是字面 `{message}`。fallback 参数里有正确中文文案，但 `TemplateRenderer.resolveTemplate` **优先命中模板文件**（有 `{message}` 就用它），fallback 只在模板缺失/为空时生效。

**根因**：默认模板占位符与调用方传入的 vars 键集不匹配；测试服因手工改过模板（中文文案）才没暴露，**新部署必现**。

**验证脚本**（模拟 render 行为）：
```python
tpl = "{message}"; vars_ = {"player":"P","type":"T","summary":"S"}
out = tpl
for k, v in vars_.items(): out = out.replace("{"+k+"}", v)
print(out)  # '{message}' ← 字面残留
```

**修复模式**：默认模板必须用与 vars 一致的占位符（`{player}/{summary}/{reviewer}`），或调用方补一个 `message` 键。**review 检查点**：凡 `renderTemplate(key, vars, fallback)` 调用，核对 vars 键 ⊇ 模板占位符键；`command_review_list` 类传了 `message` 键所以没事，`review_*` 四键没传所以坏。

**同类检查点（Paper 插件 review 通用）**：
- `handler.onApproved()` 抛异常时状态已存 APPROVED 但 LP 未授权 → 玩家看到「已通过」实际无权限；应先 handler 后落状态或 try-catch 告警。
- `newRequestId()` 用 `UUID.hashCode()` 可能为负且碰撞概率存在 → 用完整 UUID。
- `cancel()` 的 reviewer 字段存申请人 UUID（语义错误，应存名字或 null）。
- 迁移循环内每次 `save()` 全量落盘 → 批量迁移应攒批一次保存。
- **坏记录容错**：YAML 存储读记录时 `UUID.fromString`/`Status.valueOf` 对损坏配置直接抛异常，单条坏记录会拖垮整个 list 功能 → 读取方法返回 `Optional`，解析失败 catch 后跳过 + warning 日志（不中断全表）。
- **迁移脏 key 容错**：遗留文件循环内 `UUID.fromString(key)` 对非 UUID key 抛异常中断迁移 → try-catch 跳过 + warning。
- **权限命令测试要验证「真实生效」而非仅日志/状态**：LP 命令 RCON 无回显、audit 存 H2 不可读 → 用组专属命令实测（builder 组 `//wand` → WE 木斧提示）。

## 10. LP track API 原生钳位（2026-08-07 反编译证伪「绕圈」假设）

**早期假设（已证伪）**：LP track 是循环的，`promote` 在链尾（admin）会绕回 default、`demote` 在链首（default）会绕回 admin，因此必须用显式 `parent add/remove` + 本地状态推断当前组实现钳位。

**反编译证据（LP API 5.4 jar，`javap -p`）**：
- `PromotionResult$Status`：`SUCCESS` / `ADDED_TO_FIRST_GROUP`（不在 track 上 → 加入首组）/ `MALFORMED_TRACK` / **`END_OF_TRACK`（链顶再 promote = 失败，不绕回）** / `AMBIGUOUS_CALL` / `UNDEFINED_FAILURE`
- `DemotionResult$Status`：`SUCCESS` / **`REMOVED_FROM_FIRST_GROUP`（链底 demote = 移除首组回 default）** / `MALFORMED_TRACK` / **`NOT_ON_TRACK`（不在 track = 已是 default）** / `AMBIGUOUS_CALL` / `UNDEFINED_FAILURE`
- `Track` 接口：`getGroups()`（链定义）、`promote(User, ContextSet)` / `demote(User, ContextSet)`（原生钳位）、`getNext/getPrevious`、`containsGroup`
- `UserManager`：`getUser(uuid)` 同步查缓存（在线）、`loadUser(uuid)` 异步加载（离线）、`getPrimaryGroup()` 查当前主组

**正确设计（最简版）**：track 定义 `default→member→builder→admin`（首组=default，`ADDED_TO_FIRST_GROUP` 语义让 default 玩家 promote 自然进 member）。插件侧：
```java
// 升级（自动钳位，无需自己判断当前组）
PromotionResult r = track.promote(user, ctx);
// r.getStatus() == END_OF_TRACK → 提示「已在最高等级（管理员）」
// 降级（同样钳位）
DemotionResult r = track.demote(user, ctx);
// REMOVED_FROM_FIRST_GROUP / NOT_ON_TRACK → 提示「已在最低等级（访客）」
```
**连带简化**：本地 `promoted`/`demoted`/`admin` 标记全删（LP 为唯一事实源），permission.yml 只留 config + reviews 两段。无 LP 时回退本地推断（reviews 的 APPROVED 记录 → builder，否则 default）。

**验证 Java API 语义的通用方法**（web 搜索被墙/污染时）：`curl -L -o /tmp/lp-api.jar https://repo1.maven.org/maven2/net/luckperms/api/<v>/api-<v>.jar` → `unzip -o -q` → `javap -p`（反编译接口/枚举，`javap -p 'net/luckperms/api/track/PromotionResult$Status.class' | grep "public static final"`）。比查博客/问答可靠，一次 1 分钟。

## 11. demoted 标记：降级后抑制历史 APPROVED 判定

**现象**：currentGroup 判定「有 APPROVED builder 记录 → builder」，但 builder→member 降级后该记录仍在 → 玩家仍被判为 builder，降级"无效"。

**修复**：降级时写 `demoted: true`（permission.yml ranks 节），currentGroup 的 builder 判定加 `&& !hasDemoted`；**重新 approve（重新晋升）时 clearDemoted** 恢复 builder 判定。降级语义：每次降一级（builder→member→default），链底 no-op。

**测试**：`RankServiceTest.demote_builder_removesBuilderAndMarksDemoted` / `demote_default_noOpReturnsNull` / `currentGroup_demotedBuilder_returnsMember`。

## 13. Paper 26 jar 三层结构 + 反编译法（2026-08-13 实测）

- `paper-26.2-111.jar` = **paperclip 启动器壳**（thin，只有 libraries），**不是服务端**
- 真实服务端嵌套：`cache/mojang_26.2.jar` → `META-INF/versions/26.2/server-26.2.jar`（内层 jar）
- **反编译服务端类路径**：
```bash
cd /tmp && mkdir paperx && cd paperx
unzip -o -q ~/minecraft-server/cache/mojang_26.2.jar 'META-INF/versions/26.2/server-26.2.jar'
unzip -o -q META-INF/versions/26.2/server-26.2.jar 'net/minecraft/server/players/PlayerList.class'
javap -c -p net/minecraft/server/players/PlayerList.class   # 字节码
```
- ⚠️ **macOS `strings` 不兼容 class 文件**（报 `fat file: ... truncated or malformed`）→ 用 python 提取：
```python
import re; data = open('X.class','rb').read()
[str(s.decode()) for s in re.findall(rb'[\x20-\x7e]{5,}', data) if b'keyword' in s.lower()]
```
- **per-IP 5 在线限制**：`PlayerList.class` 字符串表**没有** `ip_limit`/`too many` key（被 Paper 重构，语言 key 移到别处），但**行为实测存在**（同 IP 第 6+ 被踢 `Sorry, there are too many players logged in with your IP address`）——验证行为用实测，别依赖反编译字符串

## 14. 审核命令 vs 管理命令职责边界（用户设计评审）

`$v` 本是 review 审核命令（l/y/n 裁决玩家申请），若混入 `$v d`（管理员主动降级，无申请流程）职责模糊。用户明确指出：**审核（对申请的裁决）与管理（管理员主动操作）语义不同**。设计取舍：① `$v` 扩展为完整权限管理（l/y/n + d + u 对称钳位）；② 审核与管理分命令；③ 管理操作只留游戏内命令。**先和用户确认方案再实现**，不要默认混在一起。
