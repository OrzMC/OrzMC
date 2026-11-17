# 上游问题清单（交上游用）

> 完整版（含证据/复现/建议/实测数据）在站点目录：`E:/deploy/upstream-issues-20260911.md`。
> 本文只做索引与结论，避免技能与文档双维护。状态以 **2026-10-02** 回读为准。

## 状态总览

- 两个自研仓（OrzGeeker/OrzMusic、OrzMC/OrzMCDeploy）**全部 issue 已 CLOSED/COMPLETED**，本机在 0.0.10 / 0.0.4 上实测无回归。
- 第三方：MCSManager 新提 2 条（#2346/#2347）；EasyBot 根因由我们定位后上游**已修并合入**（[PR #122](https://github.com/EasyIndie/EasyBot/pull/122) + [PR #123](https://github.com/EasyIndie/EasyBot/pull/123) 均 MERGED，#121 已 CLOSED/COMPLETED），镜像已发 `:latest`（`sha256:1c02c337…`，含 #122+#123；`/api/v1/ready` 已出现 `message_storage` 字段且未就绪返 503）；本机 A/B 实测验证通过。
- **✅ 2026-10-02 本机已升级到 OrzMCDeploy v0.0.6**（跳 0.0.5：0.0.6 把 easybot 内存缺省 1G 回调 512M，ADR-024）：easybot 现为 **v0.0.41 `23a6eace`**、上限 512M、`restarts=0`，`/api/v1/ready` 全 ready、双 adapter 在线、公网 4 域名 200、Gatus 平台层全 OK。升级规程与验收清单见 `upgrade-playbook.md`。
- ✅ **2026-09-28 提交的两条内存 OOM issue 均已于 2026-09-30 / 10-01 修复关闭**：[EasyBot#139](https://github.com/EasyIndie/EasyBot/issues/139) CLOSED/COMPLETED + [OrzMCDeploy#16](https://github.com/OrzMC/OrzMCDeploy/issues/16) CLOSED（连 [OrzMCDeploy#14](https://github.com/OrzMC/OrzMCDeploy/issues/14) 一并由 PR #17 处理）。**根因**：easybot outbox 发布器每 250ms 轮询 `unpublished_outbound_events()`，`ORDER BY completed_at,id` 缺覆盖索引 → 每次查询物化 TEMP B-tree 且匿名内存不归还 → 空载也 ~0.3MB/min 增长直至 OOM；修法 = schema 迁移 v4 加三个覆盖索引（幂等 `CREATE INDEX IF NOT EXISTS`）。
- **EasyBot 版本现状（2026-10-02）**：最新正式 release = **v0.0.41**（10-01，修 #139）；历史版本 0.0.39 修 h2 空 DATA 帧内存放大（RUSTSEC-2026-0258）、0.0.40 修 openssl `CVE-2026-14456`（无界内存 DoS）。**本机跑 0.0.38（`cd0b4e44`）仍带该 CVE，务必随 0.0.5 一起升。**（EasyBot 内存上限 OOM）：[EasyBot#139](https://github.com/EasyIndie/EasyBot/issues/139)（OPEN）+ [OrzMCDeploy#16](https://github.com/OrzMC/OrzMCDeploy/issues/16)（OPEN），已双向交叉引用。**EasyBot 版本现状：本机 0.0.38（`cd0b4e44`），最新 release v0.0.40（09-04，镜像 `5a310e30`），`:latest` = `1c02c337`（含 0.0.40 之后的 #122/#123，无正式 release）→ 落后 2 个 release。** 0.0.39 修 h2 空 DATA 帧内存放大（RUSTSEC-2026-0258）、0.0.40 修 openssl `CVE-2026-14456`（同为无界内存 DoS）→ **本机 0.0.38 镜像仍带该 CVE**。

## 已提交 issue

| 编号 | 要点 | 状态 |
|---|---|---|
| [OrzMusic#2](https://github.com/OrzGeeker/OrzMusic/issues/2) | 所有服务 `restart` 默认 no → 重启不自愈（实测静默宕机 12h） | ✅ CLOSED（0.0.8 修） |
| [OrzMusic#3](https://github.com/OrzGeeker/OrzMusic/issues/3) | `ADMIN_API_TOKEN` 取值链含 macOS `~/.bash_history` → 跨平台静默取空 | ✅ CLOSED（0.0.8 修） |
| [OrzMusic#4](https://github.com/OrzGeeker/OrzMusic/issues/4) | `db` 5432 无条件暴露宿主 | ✅ CLOSED（0.0.8 修；0.0.10 实测宿主无 5432） |
| [OrzMusic#7](https://github.com/OrzGeeker/OrzMusic/issues/7) | `release-smoke.sh` 硬依赖 python3 且吞错 → health 假 FAIL | ✅ CLOSED（0.0.9 修） |
| [OrzMusic#8](https://github.com/OrzGeeker/OrzMusic/issues/8) | MSYS 路径转换毁 db-backup 容器内 /tmp → upgrade 第 3 步中止 | ✅ CLOSED（0.0.9 修） |
| [OrzMusic#10](https://github.com/OrzGeeker/OrzMusic/issues/10) | `release-smoke.sh` 用 `-o /dev/null` → MSYS curl 退出 23，3 项假 FAIL + 跳过 4/5 节 | ✅ CLOSED（0.0.10 修，14/14 PASS） |
| [OrzMCDeploy#9](https://github.com/OrzMC/OrzMCDeploy/issues/9) | `DAEMON_PORTS` 应自动忽略（docker 型实例） | ✅ CLOSED（0.0.4 修） |
| [OrzMCDeploy#10](https://github.com/OrzMC/OrzMCDeploy/issues/10) | daemon 512m 上限 vs 镜像 8192 堆上限 | ✅ CLOSED（0.0.4 修） |
| [OrzMCDeploy#11](https://github.com/OrzMC/OrzMCDeploy/issues/11) | 站点增量挂载点（`compose.site.yaml`） | ✅ CLOSED（0.0.4 修） |
| [OrzMCDeploy#12](https://github.com/OrzMC/OrzMCDeploy/issues/12) | 实例启停姿势 / `autoStart` 语义 docs | ✅ CLOSED（0.0.4 修） |
| [EasyBot#121](https://github.com/EasyIndie/EasyBot/issues/121) | DB 属主 root vs uid 10001 → `EPERM` 后静默降级内存库（非 bind mount 固有） | ✅ CLOSED/COMPLETED 2026-09-11：PR #122（核心修复）+ #123（内存回退不再静默）均 MERGED；镜像经 `:latest` 发布（`sha256:341ea707…`）；本机 A/B 实测通过（见站点文档末节）。本机绕过待升级后撤除 |
| [MCSManager#2346](https://github.com/MCSManager/MCSManager/issues/2346) | 运行中改 `InstanceConfig/*.json` 被内存回写覆盖（静默丢改动） | OPEN（本机：停 daemon→改→起） |
| [MCSManager#2347](https://github.com/MCSManager/MCSManager/issues/2347) | `autoStart`/`autoRestart` 语义与状态持久化无文档、两次重启行为不一致 | OPEN（实测摸清，见 docker-service-lifecycle.md §7） |
| [OrzMCDeploy#14](https://github.com/OrzMC/OrzMCDeploy/issues/14) | easybot digest bump 到含 #121 修复的构建（`cd0b4e44` → `1c02c337`） | ✅ CLOSED（0.0.5 一并处理，实际钉 **v0.0.41** `23a6eace`） |
| [EasyBot#139](https://github.com/EasyIndie/EasyBot/issues/139) | 近乎空载下 anon 内存（506MB）涨到容器上限 512MiB、被 cgroup OOM kill（dmesg 14 次、`RestartCount=76`） | ✅ CLOSED/COMPLETED 2026-09-30（v0.0.41 修） |
| [OrzMCDeploy#16](https://github.com/OrzMC/OrzMCDeploy/issues/16) | easybot 512M 上限过紧；建议提到 1G + 文档化各服务最小内存值 | ✅ CLOSED/COMPLETED 2026-10-01（v0.0.5：改 `.env` 的 `EASYBOT_MEMORY_LIMIT`，缺省 1G） |

### EasyBot 内存上限 OOM 取证法（2026-09-28，可复用）

```bash
docker inspect orzmc-easybot --format 'restarts={{.RestartCount}} up_since={{.State.StartedAt}}'
docker exec orzmc-easybot /bin/busybox sh -c \
  'cat /sys/fs/cgroup/memory.max; cat /sys/fs/cgroup/memory.current; \
   cat /sys/fs/cgroup/memory.peak; grep -E "^(anon|file) " /sys/fs/cgroup/memory.stat; \
   cat /sys/fs/cgroup/memory.events'
wsl -d docker-desktop -e dmesg | grep -c 'Killed process.*easybot'
```

- 镜像里**没有 `/bin/sh`**，读 cgroup 必须走 `/bin/busybox sh -c`。
- dmesg 的 `oom_memcg=/docker/<id>` 中 `<id>` **就是容器 ID**（`docker inspect -f '{{.Id}}'` 比对）→ 这是确认「谁被 OOM 杀」的硬证据。
- ⚠️ **容器重启会回收重建 cgroup → `memory.events` 的 `oom_kill` 归零**，别据此判断「没被杀过」；要看 dmesg + `RestartCount`。
- `memory.peak == memory.max` 且 `anon` ≫ `file` = 真实匿名内存顶到上限（非 page cache 假象）；`memory.events` 的 `max` 计数持续上涨 = 持续贴上限运行。
- 本机 512MiB 是**部署侧保险丝**（`compose.yaml` 的 memory 上限，可调项只有 daemon 的 `DAEMON_MEMORY_LIMIT`）——报上游时务必说明这一点，否则会被当成 EasyBot 默认值。

## 仍待上游（本机为临时绕过，换包/重建会复发）

| 仓库 | 问题 | 本机绕过 |
|---|---|---|
| EasyBot | ~~DB 初始化失败即静默降级内存库~~（#121） | ✅ **上游已修完毕**（PR #122+#123）；本机 `chown 10001:10001` 绕过**仍生效**（生产轮旧 digest），**升级镜像后再撤** |
| EasyBot | ~~`secure existing DB` 只 chmod 不纠属主，报错无指引~~ | ✅ 同 #122/#123 一并修 |
| MCSManager | 见 #2346 / #2347 | 停 daemon→改文件→起 daemon |

## 26.3 协议生态缺口（2026-09-20 实测，非我方 bug）

**现象**：26.3 客户端进服后，GrimAC 抛 `java.lang.IllegalStateException: Unknown entity metadata type id: 105 version V_26_2`（栈顶在 `grimac-bukkit-2.3.74.jar//ac.grim.grimac.shaded…packetevents.wrapper.PacketWrapper.readEntityMetadata`），随后 GrimAC 状态被污染 → **误报 BadPacketsN 并踢人**（本地测试服实测踢掉 joker）。

**归因链（实测数据）**：
- 26.3 是**今天（09-20）刚出的新 MC 版本**；26.3 新增了实体元数据类型（packetevents PR #1582「26.3 support」里 `EntityDataTypes.java +7`）。
- **packetevents**：26.3 支持 **2026-09-19 才合入 main**（PR #1582，`Bump dependencies to 26.3` 09-18），**尚未发版**（最新 release 仍 v2.13.0 / 06-22）→ Modrinth `packetevents` 只标到 26.2。
- **GrimAC**：最新 alpha `2.3.74-8eb5f28`（09-10，Modrinth）game_versions 仍只到 **26.2**；主分支最后提交 09-10；依赖 **GrimAPI v1.6.0.12（09-03）**早于 packetevents 的 26.3 合并 → **GrimAC 目前必然读不懂 26.3**。
- **GrimAC 用的是 shaded+relocated 的 packetevents**（`ac.grim.grimac.shaded.io.github.retrooper.packetevents`）→ **换外部 packetevents 插件无效**，必须等 GrimAC 自己 bump 依赖。
- Via 侧反而领先：ViaBackwards **5.12.0（09-18 发布）已支持 26.3** → 正是它让 26.3 客户端能进服，从而**暴露**了 GrimAC 的缺口（升级前 26.3 客户端因无 Via 支持**根本进不来**）。

**标准处置（本地已定方案，待老板拍板）**：
1. **干净拒绝**：`ViaVersion/config.yml` → `block-versions: ["26.3"]`（或 `block-protocols: [<26.3 协议号>]`）+ `block-disconnect-msg: "<自定义提示：请用 26.2 客户端>"`；改后 `/viaversion reload`。⚠️ Via 配置键位置：`block-versions` / `block-protocols` / `block-disconnect-msg`（在全局段，jar 内 `assets/viaversion/config.yml` 可查默认值）。
2. **不要**在生产照抄「升级 Via 三件套」：升级会让 26.3 客户端从「被干净拒绝」变成「进来后被 GrimAC 误踢」（体验更差）。要升就连同 ①的 block 配置一起上。
3. 上游适配后（packetevents 发版 + GrimAC/GrimAPI bump）→ 升级 GrimAC 即可解禁。

**盯梢点**：packetevents release（v2.13.1+/2.14）、GrimAPI tag（>1.6.0.12）、GrimAC Modrinth alpha 是否含 `26.3`。

### 🔄 2026-10-12 进展更新（周巡检补跑实测，**事实已变，旧结论作废**）

| 项 | 09-20 旧结论 | 2026-10-12 实测 |
|:--|:--|:--|
| packetevents | 26.3 支持仅 main，未发版（release 仍 v2.13.0） | ✅ **v2.14.0（09-23）已发版且支持 26.3**；本地双服已部署 2.14.0 |
| GrimAC | 主分支最后提交 09-10；「必然读不懂 26.3」 | ⚠️ **main 分支 2026-09-28 已合 `support 26.3 (#2888)`** —— 老板原话「**有开发版支持 26.3，不过不是稳定发行版**」。Modrinth alpha `2.3.74-f5bbe9c`（10-07）metadata 仍只标到 26.2 → **主干可用、无正式 release** |
| Paper 核心 | 26.3 = ALPHA 通道（老板拍板不采用） | ⚠️ **Paper 26.3-177 于 2026-10-12（build 时间 15:04Z）转入 STABLE 通道**，26.2 线最新 STABLE = **133**（10-09） |
| Via 三件套 | 5.12.0 已支持 26.3 | ✅ 最新 **5.12.1**（10-08）；测试服已升 5.12.1 |

**当前处置（老板 2026-10-12 认可）**：**三端核心维持 26.2 线**（paper 26.2-133）+ Via `block-versions: [">26.2"]` 干净拒绝 26.3 客户端。
**解禁条件**：GrimAC **发正式版**（含 26.3 支持）→ 届时再评估核心升 26.3。⚠️ 通道已不再是阻塞项（26.3 已 STABLE），**唯一阻塞 = GrimAC 无 release**。

## OOM 修复的落地验证（2026-10-02）

本机未升级也**先验证了修复方案有效**：`E:/orzmc/easybot/data/data/gateway.db` 里已手工建上 v4 的三个索引（`idx_outbound_deliveries_outbox` / `_actor` / `_session`）→ 自 2026-09-30T03:21 起容器连续运行 2 天 5 小时，`RestartCount=0`、`memory.current` 稳定在 72MB（此前贴顶 508MB/512MiB）、dmesg 无 OOM kill。

**升级到 v0.0.41 时无需先撤手工索引**：上游迁移是 `CREATE INDEX IF NOT EXISTS`，幂等，重复建不会报错也不会重复占用。

**升级清单（v0.0.4 → v0.0.5）**：全包仅 easybot 两处变化（`memory: "${EASYBOT_MEMORY_LIMIT:-1G}"` + digest `cd0b4e44` → `23a6eace`），其余 4 个镜像 digest 未动 → **只会重建 easybot 一个容器**。发布包 `orzmc-0.0.5.tar.gz` sha256 `cd102bae3030f964d40c845841688cfc6702eb284a7ee582a9ba7ddad68ddcaa`。

## 明确不提

- Docker Desktop：`docker system df` 把在用镜像算可回收（技能里已标"别信"）；json-file 无默认上限（已用全局 `log-opts` 兜底）。价值有限，不上报。

## 已确认修好（勿再提）

OrzMusic `#2`/`#3`/`#4`/`#7`/`#8`/`#10`；OrzMCDeploy `#4`（Windows daemon 缺 `MCSM_DOCKER_WORKSPACE_PATH`）、`#5`（`restore.sh` SIGPIPE）、`#6`（`DAEMON_PORTS` 冲突告警）、`#7`（MariaDB healthcheck 误报）、`#9`/`#10`/`#11`/`#12`。均实测无回归。

## 提交纪律与教训

- 三件套：**现象 + 原始日志证据 + 最小复现**，附"建议修法"而非吐槽；报前必查重（EasyBot #121 即查重后改为补评论）。
- **提 issue 只需 token 有 `repo` scope，不需要目标仓 push 权限**；先看 `has_issues`。别把 Docker Hub 发布者名当 GitHub 仓名——MCSManager 的正式仓是 `MCSManager/MCSManager`，`githubyumao` 只是镜像发布者（这条曾导致误判"无法上报"）。
- 断言"某功能不存在"前先查源码路由（D3 误判：`remote_service_instances` 早已存在）。
- 引用上游 issue 状态前**必须回读**：本次发现 EasyBot PR #122 在我们记录"未修"之后已被 MERGED。
- 用户偏好原版实现，**不要本地改上游脚本**；改动一律放站点增量（`E:/orzmc/compose.site.yaml`）或 `.env`。
