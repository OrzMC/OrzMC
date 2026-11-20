---
name: orzmc
description: "Minecraft 运维统一技能（唯一入口）：三端服务器运维/插件构建升级/性能诊断/权限体系/测试/基岩支持（含 NetherNet 迁移），74 份参考文档 + 170+ 脚本。"
version: 2.6.23
author: Hermes Agent
tags: [minecraft, papermc, server, maintenance, upgrade, plugin, exaroton, mcsm, luckperms, testing]
platforms: [macos, linux, windows]
required_commands: [java, curl, tar]
---

# OrzMC Minecraft 运维（统一技能）

> **技能治理（2026-08-11 用户决策，已合并）**：与 MC 运维强相关的技能一律**合并进本技能**维护迭代（references + scripts），不再单独立技能；新增强相关知识直接落这里。已合并：easybot-gateway-ops（→ references/easybot-gateway.md）、deployment-config-sync（→ references/config-sync.md）、git-submodule-sync（→ references/git-submodule-sync.md，OrzMC monorepo 子模块同步）、java-test-pitfalls（→ references/java-test-pitfalls.md，插件单测编译坑）、**ai-coding-agents（→ references/coding-agents.md，2026-08-29：编程交给 Claude Code 编排工作流 + 合并前一次 review 时机 + acceptEdits 坑）**、**grimac-config-tuning（→ references/grimac-tuning.md，2026-09-12：GrimAC 配置语义/官方文档获取/误报源对照/工具坑）**、**bukkit-plugin-testing（→ references/java-test-pitfalls.md，2026-09-12：Mockito 运行时陷阱/Bukkit mock 限制/Jacoco 覆盖率工作流）**、**paper-26-plugin-dev（→ references/plugin-build.md + references/papermc-tabcomplete-testing.md，2026-09-12：Brigadier 命令注册/迁移 8 坑/deprecation 清零）**；模组托管（minecraft-modpack-server）已清理，与原生 PaperMC 场景无关。

> **知识分类索引**：本 SKILL.md 只留决策路径；详细知识在 `references/`（后端 API 表 / Spark / 实体统计 / 机器人）：
>
> | 主题 | 文档 |
> |:--|:--|
> | 本机服务器操作（创建/升级/备份/状态） | `references/local-backend.md` |
> | Exaroton 云端（API 端点表 + 平台要点） | `references/exaroton-backend.md` |
> | MCSM 面板（API 端点表 + 平台要点 + 适配器；**启动实例/改 docker 端口/开启 RCON 见 `references/mcsm-start-rcon.md`**；**调用姿势三坑见 §「调用姿势的三处硬坑」**） | `references/mcsm-backend.md` |
> | **国内服 MCSM（线上，Windows Server 2022，API 403 只能人工）：启动日志期望值/常态告警/需留意项/外部实测验收/基岩排障顺序** | `references/domestic-mcsm-log-runbook.md` |
> | **EasyBot IM 网关运维（docker 容器/健康检查/QQ token/投递诊断 API 版 `scripts/easybot_deliveries.py`；0.0.33 起投递记录在 messages 表；原 easybot-gateway-ops 技能合并）** | `references/easybot-gateway.md` |
> | **部署配置同步（config drift 判定/fallback 判断/补键同步；原 deployment-config-sync 技能合并）** | `references/config-sync.md` |
> | **Git 子模块全量同步（OrzMC monorepo 20 子模块；默认分支探测/发布后指针/分支清理/独立 clone 去重；原 git-submodule-sync 技能合并）** | `references/git-submodule-sync.md` |
> | **部署分层职责边界（老板问「deploy 子模块管什么、哪些要部署后手工做」）：monorepo 子模块分类表 / deploy 自动做的四块（编排·orzmc.sh·Eagler 运行时·防火墙）/ 明确不做的四类（面板实例·paper-global secret·TLS+DDNS+路由器·密钥值）/ 站点增量只落 `compose.site.yaml` / 部署后手工清单 11 项（含「备份默认没排期」）/ 运行态核对法（`docker inspect` 的 `project.config_files` 标签反查容器由哪棵树起、两棵树漂移用 `diff --strip-trailing-cr` 排除 CRLF 假差异）/ **§7 统一运行树：只从 Release 产物起容器（单个固定目录 `E:/deploy/orzmc` 原地覆盖升级、回滚靠 `_dl` 里的旧 tarball；**不用 `orzmc-current` junction、不留多版本目录**——试过被老板否掉，多一层无收益；迁移前先 `tar` 解包 + `diff -r --strip-trailing-cr` + sha256 三件取证；删旧克隆前核引用面（含 `docker ps --format` 带 `\r` 导致 inspect 循环静默归零的假阴性）；破坏性命令的免审批替代）** | `references/deploy-layer-boundaries.md` |
> | **Java 测试编译陷阱 + 单测运行时陷阱（Mockito 泛型捕获/SuppressWarnings 位置/CI warnings 清零；**2026-09-12 并入 bukkit-plugin-testing**：Mockito UnfinishedStubbing/Stub 顺序/argThat null/异步进行中模拟、Bukkit API mock 限制（Material.isSolid 依赖注册表、Vector.clone 返回 null）、Jacoco 覆盖率缺口定位工作流）** | `references/java-test-pitfalls.md` |
> | **AI 编码智能体协作（编程交给 Claude Code + Hermes 编排；三模式/acceptEdits 坑/合并前一次 review；原 ai-coding-agents 技能合并）** | `references/coding-agents.md` |
> | Spark 性能分析（命令/JSON/判断/踩坑） | `references/spark-analysis.md` |
> | 快速实体统计（paper entity list / Spark / 计分板） | `references/entity-statistics.md` |
> | 机器人玩家 Mineflayer（运维视角；开发细节见独立技能 `minecraft-bot-mineflayer`；**挂机脚本 stay-with-joker.js：5 bot 跟随真人玩家 + IPv4/IPv6 分流绕 per-IP 限制**） | `references/mineflayer-bot.md` |
> | DeathChest 回归测试（死亡瞬间下线→物品丢失 ✅fix1；**动画 progress 越界卡服 ✅fix3 已合入 main 71d2571**；复现法见 ref） | `references/deathchest-regression.md` |
> | **NetherNet 迁移（基岩新传输层：TCP 信令 + WebRTC/UDP；2.12 配置结构反编译实证 / A-B-C 三方案 / HTTPS 三做法 / 官方错误对照表 / 本机 Clash TUN 假阳性验证法；⚠️ 2026-10-27 基岩客户端停用 RakNet）。**关键实测（版本相关，勿照抄）**：**域名入口不强制 HTTPS** —— Geyser 2.12.1（build 1280）+ Bedrock 26.60 实测「域名 + `signaling.builtin.https` 留空」可正常进服（仅弹一次 TOFU 信任）；对 19132 做 TLS 探测，两端都是 ClientHello 后 EOF。**基岩连不上的真因优先查三处**：① UDP 端口未转发（TCP 通只说明信令通）② `advertise-addresses: []` 交给 STUN 猜地址（主机出网 IP ≠ 域名 A 记录时必挂）③ `transport: nethernet` 挡掉 26.40 之前的老客户端。配 HTTPS 的收益仅「免掉信任弹窗」。2026-10-20 纯 IP 全链路（`GET /v1/join` 200 → `POST /v1/join/<id>` 200 → DTLS 建连）在测试服验证通过；动态公网 IP 由 `scripts/nethernet_advertise_sync.py` + cron `orzmc-nethernet-advertise-sync`（15 分钟，静默）自动跟进 `advertise-addresses` | `references/nethernet.md` + `~/OrzMC/proxy/scripts/nethernet_check.py`（已并入 OrzMCProxy main，v1.1.0，退出码 0=可用/1=不可达/2=用法/3=降级；`--signal-port` `--scheme https` `--json` `--self-test` `--no-emoji`）；**2.12.1 权威键名表 / 单端口 vs both 语义 / 双协议验证矩阵（RakNet Pong、`GET /v1/join`、`POST` 401 是预期、匿名 STUN 不可作凭据、日志线程名区分传输层）→ 该文 §3 / §6.1**） |
> | **Geyser 基岩支持（当前 offline 直连模式；floodgate 已回退 2026-08-05）** | `references/geyser-floodgate.md` |
> | **「客户端能进哪些版本」判定（老板/玩家问版本范围时）：范围由入口插件而非服务端核心决定；三通道各读哪份真值（Java=ViaVersion/ViaRewind 协议类 + 减掉 block-versions、基岩=Geyser jar 版本串表 + `/v1/join`、网页=listeners.toml `[protocols]`）；回答模板与「上限=服务端版本」铁律** | `references/client-version-range.md` |
> | **Eaglercraft 网页客户端接入（老板要「让网页版能进服」时）：先判有没有代理层（25565 回 Paper 还是 Velocity）；两路线 = EaglerXPaper（Paper 插件、双栈复用原端口、免代理）vs Velocity+EaglerXServer（退端口+转发）；双栈 `listeners.toml` 模板、TLS 两法二选一（Caddy `flush_interval -1` / 插件 `tls_config`）、101 验证、Netty 管道抢占与单人 fork 风险 **| `references/eagler-client-access.md` |
> | **服务器列表展示（MOTD / 人数 / 图标）：三端真源表（velocity.toml `motd` MiniMessage、Geyser passthrough 继承、EaglerX `server_motd` 数组 + `&` 码）、老板定案的文案口径（品牌+多版本在首行、官网标语在次行、不写域名）、`show-max-players` 与 `sample-players-in-ping` 语义、改完必须 `docker restart orzmc-velocity`、三端验收法（Java 探针 flatten / 基岩 `GET /v1/join` 一次验全 / 网页 18443 需 `--resolve` 走 SNI）、**官网状态卡经 `api.mcstatus.io` 转发带来的两处失真：渐变被量化成 16 色 legacy 码（跨词渐变必错位 → 会被官网展示的那一行用 `<gold>` 单色）、`version.protocol` 恒返回 47 不可信（前端不得把协议号拼进版本标签）；「游戏内正确 ≠ 官网卡片正确」，颜色错乱先怀疑 API 转发而非站点 CSS** | `references/server-list-motd.md` |
> | **入口探针 / 周巡检运行手册（本机 watchdog：引擎·入口·后端三层判定、退出码纪律、monkeypatch 三态自测、cron 结果核对、停机取证顺序）** | `references/entry-monitoring.md` |
> | **实例端口模型与审计（docker 实例必须逐条发布 `宿主:容器/协议`；端口以实例实际配置为准而非默认 25565/19132；多实例共享宿主时 UDP 错开 19132/19133；宿主≠容器 时 `clone-remote-port` 必须 false；Cloudflare Tunnel 不支持 UDP；脚本 `scripts/port-audit.py` 核对期望端口 vs 已发布 + 真实协议探测）** | `references/instance-ports.md` |
> | **对外端口暴露面最小化（老板问「哪些端口要路由器转发、哪些能清理」）：先分层再数端口（宿主监听 → 公网 DNS → 已挂在 Caddy 443 后的服务一律不需要自己的转发）；家宽最小集固定 4 条 = `443/tcp`（Caddy：面板/机器人/音乐/网页客户端全在它后面）+ `25565/tcp`（Velocity Java）+ `19132/udp` + `19132/tcp`（RakNet/NetherNet 两个独立协议），`24454/udp` 语音可选；面板 23333/18091/8080/3000、RCON 25575/25576、旧基岩 19133-19135、旧入口 18443 一律删；22/3389 不转；80 仍被封不用转。**2026-11-20 定案：家宽入站 443 被运营商封锁**（外网 8/8 节点对宿主 IP:443 SYN 超时，同 IP 的 25565/19132 全通；路由器已加 `443→宿主:443` 仍不通，加 `18443→宿主:443` 后外网实测 404 `Server: EaglercraftXServer` + WS `101`）→ 宿主只留 `443:443`，**对外入口固定 `18443`**，看板/面板/网页客户端地址一律带 `:18443`。11-19 那条「443 已可进」是回环/同网假阳性，已推翻，**勿再删 `:18443`****MC 协议无 SNI 不能复用到 443、UDP 不能走 HTTP 反代**，所以 4 条是下界；砍端口只能砍协议。**路由器转发表本机读不到（UPnP 关时 SSDP 无 IGD、公共探测只覆盖 TCP 且不稳）→ 结论必须写成「基于宿主监听+防火墙规则推导、请老板核对」，不得声称「你路由器现在开着 X」**；`netsh ... show rule` 按分隔线分块会让规则名与端口错位一格，只能信端口值 | `references/external-port-exposure.md` |
> | **公网入口排障（域名+路由器映射+防火墙都"配好了"外网仍连不上）：根因常是本机 Clash TUN 抢默认路由 → 入站应答源地址被定成 198.18.0.1/钻进隧道；修法 = WSL 内加通用策略路由 `ip rule add from <LAN IP> table 100`（任意端口零维护，脚本 `scripts/orzmc-mc-reply-route.sh` + Windows 计划任务 OrzMC-MC-Reply-Route 每 10min 自愈）；⚠️ 老板坚持防火墙/路由器逐端口配置，勿再提 DMZ/端口段；含「ICMP 通但 TCP 全超时」判定法与外部节点验证法（勿在本机测）；**2026-10-29：家宽入站 80/443 被运营商封 → web 入口改映射高位 18443，Caddy 直连 + DNS-01（mcs/dev 等显式入口已弃 Cloudflare Tunnel）；refused=无映射 / timeout=被封。⚠️ **「已弃隧道」不代表所有子域都走 Caddy**：`*.{SERVER_NAME}.cn` 的通配橙云记录（`CNAME <tunnel-id>.cfargotunnel.com` + `proxied=true`）仍在，任何**没单独写 Caddy site 块**的子域（如 orzmusic 的 `music.{SERVER_NAME}.cn`）会被通配静默接进隧道，比同机直连入口慢 30~80 倍（实测源站 0.01–0.03s / 局域网 0.003s / 隧道域名 1.9–3.1s / 同机 Caddy 18443 0.04–0.08s）。**判定先做同机直连入口对照，别先怀疑容器/前端/DB**——量法见 network-connectivity-diagnosis 技能《Cloudflare Tunnel 高延迟：定量归因与改善》§3d；修法 = 加一条**显式灰云 CNAME**（显式记录优先于通配，通配不必动）+ 在现有 18443 端口上加 Caddy site 块按 SNI 分流，**上游优先写 `reverse_proxy host.docker.internal:<宿主发布端口>`**：容器名反代需要先手工 `docker network connect orzmc_default <应用容器>`，而 vendor compose 一重建/升级就把这条网络连接丢掉（下次访问直接 502），走宿主发布端口与重建完全解耦，实测两者延迟差亚毫秒；仅当应用不发布宿主端口时才用「network connect + 容器名」），访问改走 `https://<子域>:18443/`，局域网直接用 `http://<LAN_HOST_IP>:<发布端口>`** | `references/public-ingress-clash-tun.md` |
> | **插件源码构建/开发（构建工具选择、Gradle/Maven 坑、PR 流程、发布规范；**2026-09-12 并入 paper-26-plugin-dev**：Paper 26.x Brigadier 命令注册（LifecycleEvents.COMMANDS）、幽灵命令/greedyString 参数类型等迁移 8 坑、deprecation 零警告清理）** | `references/plugin-build.md` |
> | **GrimAC 反作弊配置调优（配置三层体系/config.yml 官方模板零漂移/punishments 阈值=300s 窗口违规次数非 VL/per-check 豁免三兄弟/官方 mods 兼容表/误报源与工具坑；**2026-09-12 并入 grimac-config-tuning**；部署现状与决策史见本 SKILL.md 的 GrimAC 段）** | `references/grimac-tuning.md` |
> | **插件升级与配置迁移（三端范式、Exaroton/MCSM API 坑、EzShops 存储、Geyser 排查）** | `references/plugin-mgmt.md` |
> | **插件维护状态调研（丢来一堆 jar 问「还能不能维护 / 该换吗」）：三源交叉检索（Modrinth/Hangar/GitHub + Spigot 页）、jar 内 `plugin.yml` 才是检索主键、`archived`/`pushed_at`/发版日期的判档口径（活跃/停滞/半停更/弃用/平台查不到）、依赖链成组看、表格文件 + 聊天三层结论的交付形状**；**续问「和现有插件冲不冲突 / 哪些能加」→ 同文 §7**（先取三端现有插件真值，冲突三轴=命令命名空间/数据格式/玩法语义，三道硬门槛=MC 版本/Folia/三端入口，结论只给可加·需测试·不可加三档且必须带前置动作） | `references/plugin-eol-audit.md` |
> | **商店经济防刷（EzShops 实例：纯禁卖方案/漏洞分类学/审计脚本/bot 验收/结算取价机制/交易记录三层根因链；原 minecraft-shop-economy-hardening 技能 2026-08-30 合并）** | `references/shop-economy.md` + `scripts/shop_arbitrage_check.py` |
> | **WorldEdit 防崩服（Litematica 投影调研/崩服机制/限额+物理方块禁用方案 A+B/验证方法/三端同步状态）** | `references/worldedit-safety.md` |
> | **插件权限/指令清单（21 插件按组分组：指令全量+权限全量+组分配标注；脚本 `scripts/plugin_inventory.py` 可重复生成+定时更新；JSON 全量在 `~/.hermes/state/plugin_inventory.json`）** | `references/plugin-inventory.md` |
> | **三端配置差异审计（2026-08-11 三次全量对比；2026-08-12 起每周一 9:15 cron `ab06b886c39f`「三端配置审查」**v2：只审查不重启；**v3（2026-09-03 迁 MCSM 后）：本地端 = 本机 MCSM Paper 实例目录直读 + Exa + 远程 MCSM 三路并发**；脚本 `~/.hermes/scripts/orzmc_config_audit.sh`；保留最近两次报告；⚠️ 远程 MCSM 连续三周「未开启API密钥创建功能」= 远程面板 enableApiKey 未开，待老板远程修复；cmp3 工具链用法）** | `references/three-end-config-drift.md` |
> | **版本巡检脚本 `~/.hermes/scripts/mc_version_check.py`（查核心 + 插件各渠道最新版 vs 部署版 → 差异发飞书）**：~~独立 cron 每日 10:00~~ **已停用，并入周巡检 job `d81c8325fe8b` 第③部分** | 本 SKILL.md「版本巡检」段 |
> | **测试服 jar 升级 + 配置迁移 SOP（双实例 MCSM API 全流程；投递=scp 直投〔不传 upload/download_from_url〕、核心版本化命名、备份必须 Move 出目录、远端 sha256 回读；逐轮实录 §2d–§2j）** | `references/test-server-upgrade-sop.md` |
> | **Docker 服务清单 / 重启自愈 / MCSM 实例手动启停（autoStart 回写坑、自动登录断点）** | `references/docker-service-lifecycle.md` |
> | **交上游的问题清单（已修/待修索引）** | `references/upstream-issues.md` |
> | **性能诊断（Spark 五步法、实体审计、Aikar Flags、修复方案）** | `references/performance.md` |
> | **MCA 级世界工具链（槽位粒度合并 `scripts/merge_worlds.py` / 加速命令方块扫描 `scripts/mca_scan_fast.py` / 区块高度分析 `scripts/mca_height_scan.py`；上游 OrzMCBackup 权威实现对应关系）** | `references/mca-toolchain.md` |
> | **插件 Bug 排查（本地复现、命令/权限分离、实体事件、版本兼容）** | `references/plugin-debugging.md` |
> | **测试体系（分层原则 / 三大通道 / 跨服 transfer；**附：Bot 命令测试 + 机器人 E2E + Paper 26 踩坑明细**；迁 MCSM 本机栈后拓扑/五连坑/启停规范见该文头部）** | `references/testing.md` |
> | **LuckPerms 权限体系（API 集成、审计验收、三端同步、Bootstrap；四组增量规划与 gamemode 真值见 `permission-system.md`）** | `references/permission.md` + `references/permission-system.md` |
> | **实体/传送门行为（事件继承、原版规则、白名单策略）** | `references/entity-portal.md` |
> | OrzMC 统一代码仓库（submodule 资产地图：插件源码/配置库/备份工具/世界瘦身；**Bot 命令调试 orzdebug + $e 输出捕获机制 + Log4J 坑**） | `references/orzmc-repo.md` |
> | OrzMC 真实环境验收报告（2026-08-06：全功能测试矩阵 + 双服 transfer + 发现的 bug） | `references/orzmc-acceptance-20260806.md` |
> **玩家手册**：官方站 `orzmc.{SERVER_NAME}.cn/user/` = **OrzMCSite** 仓库 `content/user.md`（独立仓库；改手册 = 改 user.md → push main → CI 自动发布 Pages，主仓只 bump 指针）。要点：地址用 `server-status` shortcode + `params.toml` 的 `tags=` 分组（**勿用旧 `servers=` 参数**）、HTML 标签会被 Hugo 静默丢弃（排版用纯 Markdown）、本地 Hugo 用 brew 版。详见 `references/site-manual.md`
> | OrzMC 功能测试用例（28 项，玩家命令/Bot 命令/事件拦截，含前置条件/步骤/预期） | 插件仓库 `plugin/docs/test-cases.md`（OrzMCPlugin） |
> | OrzMC 端到端测试报告（2026-08-06：机器人+真实玩家，28/28 通过，transfer 闭环） | 插件仓库 `plugin/docs/e2e-test-report-20260806.md`（OrzMCPlugin） |
> | RCON 客户端（`scripts/rcon.py <命令> [端口]`，密码从环境变量 RCON_PASSWORD 读） | `scripts/rcon.py` |
> | **实例端口审计（`scripts/port-audit.py [DATA_ROOT] [--probe] [--json]`：解析 InstanceConfig docker.ports + server.properties + Geyser config.yml 得出期望端口，标出必发布缺口/宿主端口冲突，可实时探测 Java+基岩双通道；退出码 1=有缺口）** | `scripts/port-audit.py` |
> | **玩家入场监听（`scripts/conn_watch.py`：改完网络/Geyser 配置后验证“玩家到底能不能进”——同时采 **Java Status 在线人数** + **基岩 `/v1/join` 在线人数**双源，任一 >0 即证明进服成功；自动 DoH 绕本机 TUN；`--duration/--interval/--json`；退出码 0=命中/1=未命中/3=数据源不可用）** | `scripts/conn_watch.py` |
> | **统一连通性检查（`scripts/connectivity_check.py`：一次跑完 DNS（自动绕 Clash TUN fake-IP，DoH 取真值）→ Java 协议握手/版本/协议号/人数 → 基岩旧协议 RakNet Pong → 基岩新协议 NetherNet 信令 `GET /v1/join` → 基岩端口 HTTPS 信令 → `--external` 公网 TCP 外部节点（check-host.net 3 节点）；内置目标 paper/folia/paper-pub/prod-mcsm，可 `--host --java --bedrock` 自定义；`--json` 供 cron；退出码 0=全通/1=FAIL/3=仅WARN。**判读纪律：`RakNet 无应答` ≠ 故障**（`nethernet` 单端口模式本就不答 RakNet；只要 NetherNet 信令 200 就记 ℹ️，两条通道都挂才 FAIL）；**`HTTPS 信令不可用` 也只是 ℹ️**（当前版本域名连接仍可用，仅弹一次 TOFU 信任），不得据此判「域名入口必挂」） | `scripts/connectivity_check.py` |
> | **基岩版连通性诊断（`~/OrzMC/proxy/scripts/bedrock_host_check.sh` bash 跨平台 / `.ps1` Win）**：双模式——本机诊断（默认，RakNet 握手+端口监听+进程+防火墙五项）与远程探测（传 host 即可，端口默认 19132，纯数字第一参=端口）；用法 `bash bedrock_host_check.sh [host] [port]`、PS `.\bedrock_host_check.ps1 [-HostAddr x] [-Port n]`；-h/--help 帮助；**定位法：本机 PASS+监听✅ → 问题在外部 UDP 转发；FAIL → Geyser 本身**；使用说明/修复记录文档同目录（基岩诊断脚本_使用说明.md、脚本问题修复记录_平台注意事项.md，v1.1 含 7 条真机坑）；坑：macOS netstat `udp46 *.19132` 格式、BSD pgrep 只出 pid 不能二次 grep（统一 ps aux+grep）、Windows Store python3 stub 检测、PS 需 UTF-8 BOM+`${Var}:` 写法、RakNet Pong MOTD 从偏移 34 到包尾 UTF-8（长度字段不可靠）；**2026-10-19 新增 `nethernet_check.py`（NetherNet 信令探测：UDP RakNet 基线 + TCP 信令 HTTP 探测 + 结论 + 退出码 0/1，`python3 nethernet_check.py [host] [port]`）**；⚠️⚠️ **本机经 Clash TUN 测 TCP 必假阳性**——域名被 fake-IP 成 `198.18.x.x`，TCP 握手被 TUN 本地接管后「接受并立即关闭」（脚本显示 `OPEN_NO_HTTP`，误判为端口可达）→ **必须用真实公网 IP（DoH 查：`https://1.1.1.1/dns-query?name=<域名>&type=A`）+ 外部节点验证**（`check-host.net/check-tcp?host=IP:PORT` 取 request_id 后查 `check-result/<id>`；外部节点一律 `Connection timed out` = TCP 未转发/未监听，若已转发但无监听则为 refused）；UDP 侧 check-udp 无意义（普通 UDP 包 Geyser 不回，只有 RakNet 专有包才 Pong） | `~/OrzMC/proxy/`（OrzMCProxy 子模块） |
| LP 权限命令清单生成（`scripts/gen_perm_commands.py`：从仓库 `plugin/docs/permission-groups.md` 唯一权威文档解析生成 lp set 命令；方案① 2026-08-12） | `scripts/gen_perm_commands.py` |
> | LoginSecurity 注册状态查询（`scripts/check_lsdb.py [db路径] [玩家名]`） | `scripts/check_lsdb.py` |
> | **GrimAC 最近作弊记录查询（`scripts/grim_history.py [--limit N] [--player 名] [--hours N] [--kicked-only] [--config]`；数据源=history.v1.db grim_violations JOIN grim_players/grim_checks，处理方式判定=日志 ±10s 内 GrimAC kick 记录；2026-08-31 建）** | `scripts/grim_history.py` |
> | LoginSecurity→AuthMe 数据迁移（`scripts/migrate_loginsecurity_to_authme.py [--ls-db X --authme-db Y] [--dry-run]`；BCrypt 哈希直接复用，AuthMe 须改 passwordHash: BCRYPT） | `scripts/migrate_loginsecurity_to_authme.py` |
> | GetMeHome→EssentialsC 数据迁移（`scripts/migrate_getmehome_to_essentialsc.py [--yml X --db Y] [--dry-run]`；homes.yml YAML→homes.db SQLite，字段一一映射） | `scripts/migrate_getmehome_to_essentialsc.py` |
> | PaperMC 插件 E2E 测试方案调研（MockBukkit/WatchWolf/GameTest/真实环境/容器化 + 推荐组合） | `references/plugin-e2e-testing.md` |
> | **命令方块/方块实体扫描（2026-08-18 入库；2026-08-22 并入 mc_cb_scan.py 第三套工具）：`scripts/scan_cmdblocks.py <世界目录> <out.json> [workers=8] [min_size=0]` 流式 NBT 解析提取命令方块+block_entities（workers=1 串行最稳，内存紧张宿主勿用多进程）；`scripts/analyze_cmdblocks.py <json>` 输出分类统计（类型/auto/维度/命令词频/被禁命令依赖/区域分布）；`scripts/mc_cb_scan.py run --world <世界> --out-dir <dir>` 一体化扫描→CSV→自动 Markdown 报告（统计/集群/指令分类/异常/迁移要点，自带 Folia 禁用指令交叉核对，纯标准库零依赖）；三件套对比与用法见 `references/command-block-inventory.md`** | `scripts/scan_cmdblocks.py` + `scripts/analyze_cmdblocks.py` + `scripts/mc_cb_scan.py` |
> | **ExecutableEvents 实测**：~~2026-08-19 在 Folia 26.2-4 上事件监听不触发 → 判「不可行」~~ **已被推翻**：现 folia 跑 **EE 3.26.11.2 + SCore 5.26.11.2**（release）正常启用，事件可用；用前仍须注意 SCore 硬依赖、`events/` 一文件一事件、防重登限流=GP3D `Spam.LoginCooldownSeconds` | `references/folia-experiment.md` |
> | **群消息样式规范（2026-08-19 PR #197 统一）：表情标题+33 连字符分割线+版块式排版；四类消息模板键与格式表；聚合摘要空版块省略/单人无人数/多人(N)；改模板 4+1 联动清单（templates.yml+Templates.java+ReviewNotifierAdapter fallback+占位符白名单+测试）；存量服改键值须手动同步 templates.yml+reload；真实环境验证法（bot 触发+easybot 投递查询）；Folia 测试服操作坑（screen stuff stop 不可靠→RCON、防多实例、--rerun-tasks 强制重打）** | `references/group-message-style.md` |
> | ~~跨网互联/中转方案~~ **已废弃（2026-10-19 两台腾讯云中转机销毁，frps 不再运行）**：方案/脚本留作重建参考 | `references/cross-carrier-networking.md` |
> | **平台层迁移（orzmc-deploy 栈换机/Windows 全新部署：端口架构 8080 归属 easybot 只 expose、打包命令序列 + backup dump 竞态坑（先等 mariadb ping 再 backup）、Windows 旧独立 easybot 占 8080 冲突、macOS SMB 共享名中文坑 + 选项启用账户；Windows 还原两坑：restore.sh 大归档 SIGPIPE(exit 141，手工还原绕过)+ mariadb 冷数据 healthcheck 缺 `mysql@localhost` socket 账号(补建即 healthy)；2026-09-09 Mac→Windows 迁移实录，执行提示词 `~/hermes-windows-migration-prompt.md`；**末节 = OrzMusic 生产升级实操**（gh 下载包原生路径坑、Windows 无 make 直接调脚本、IMAGE_REF/BACKUP_DIR 必传、preflight 单跑假 FAIL、smoke 第 3 节 curl 23 假 FAIL））** | `references/platform-migration.md` |
> | **世界高度调整（1.18+ 高度是 worldgen 属性非服务器配置；CustomWorldHeight 插件方案 2026-08-15 本地实测通过 height=1088；硬限制 min_y≥-2032/height≤4064/min_y+height≤2032；RCON setblock 边界验证法）** | `references/world-height.md` |
> | **Folia 迁移实验（2026-08-17 本地双服实测：兼容矩阵 20 jar→18 全绿；9 不兼容插件平替方案含合并策略；LoginSecurity→AuthMe 359 账号 / GetMeHome→EssentialsC 879 home 数据迁移；❌ Hangar API 不能查 Folia（supportedPlatforms 只标 PAPER），检索用 Modrinth loaders 含 folia；Folia 26.2 目前仅 BETA；2026-08-18 全面接管原测试服（端口 25565/19132 + 地图 symlink + 配置/权限/白名单全量同步）；⚠️ ~~两服共享 world symlink（folia→paper），严禁同跑~~ → **2026-09-11 更正：容器化后两实例已是两套独立地图，可同时运行**（容器各挂自己的 `InstanceData/<uuid>`；同宿主并存时只需错开宿主端口，详见 `references/instance-ports.md`）；⚠️ 命令方块被 Folia 架构性禁用（#429/#485 not_planned）；⚠️⚠️ log4j2 自定义配置必须 start.sh JVM 参数 -Dlog4j2.configurationFile 指定（config/ 下不会自动加载）；CustomWorldHeight 已移除（全量扫描 0 高空数据，1088 格式区块随加载自然收敛 384）；Essentials tpa 漏配 tpaccept 已修复；**PlayerPortalEvent Folia 不触发已解决（PR #195 合并 b7d4b86：PlayerMoveEvent 补偿路径，几何=内部格脚底+1 起须身体两格匹配+水平精确命中，5s 双路径共享冷却，详见「传送门 transfer 补偿方案」小节）**）** | `references/folia-experiment.md` |

> **附录索引 · 其余参考文档（按主题分组）**：主索引已列常用文档，以下是专题/历史类文档，按需查阅：
>
> | 主题 | 文档 | 内容 |
> |:--|:--|:--|
> | 巡检报告与案例复盘 | `references/config-drift-report-20261116.md`、`references/config-drift-report-20261109.md`、`references/config-drift-report-20261102.md` | 周巡检漂移报告存档（最新 `-20261116`；历史版只作对比基线，只留最近 3 份） |
> | 巡检报告与案例复盘 | `references/config-drift-report-20261026.md`、`references/config-drift-report-20261026-0942-degraded.md`、`references/config-drift-report-20261019.md` | 更早的漂移报告存档（2026-11-16 从 Windows 端合并回来，补全历史链） |
> | 网页客户端 | `references/eaglerxpaper.md` | EaglerXPaper 后端接入要点（注入地址/forward_ip/X-Real-IP，2026-11-16 从 Windows 端合并） |
> | 巡检报告与案例复盘 | `references/context-trap-case-study.md` | 上下文脏数据根因链（joker / TestMember 案例实录） |
> | **运维端（Hermes 侧）落 Windows** | `references/hermes-ops-endpoint.md` | **职责边界 / 8 条 cron（含已退役）/ 本地适配器取代面板 API / 在 Windows 做脚本手术的 6 条纪律（编码、guard、编译、告警自测、误伤救援、PS 串行）/ 交付验收 / 回滚** |
> | 巡检报告与案例复盘 | `references/deathchest-fix.md` | DeathChest 3.0.1 修复案例（死亡瞬间下线 → 物品永久丢失） |
> | Rank 与权限体系 | `references/permission-impl.md` | 权限体系实现细节（LP Bootstrap 校正 / API 软依赖集成 / track 与权限链设计 / Rank 模块与幂等验证 / 权限组收敛 / 默认权限盘点 / 在线时长数据源 / 权限状态展示），**9 篇合并** |
> | Bot 与测试 | `references/easybot-delivery-verify.md` | 验证 EasyBot 通知发送（API，0.0.33+） |
> | 构建与升级 | `references/dependency-upgrade-audit.md` | 插件依赖升级核查（发版前审计，2026-08-07 实测方法） |
> | 构建与升级 | `references/ezshops-maven-build.md` | EzShops 本地构建与部署（2026-08-09） |
> | 构建与升级 | `references/loginsecurity-build.md` | LoginSecurity 构建与 AuthModeChangedEvent 排查（2026-08-10） |
> | 构建与升级 | `references/upgrade-playbook.md` | OrzMCDeploy 版本升级规程（实战：0.0.3 → 0.0.4，0.0.4 → 0.0.6） |
> | 实体 / 传送门 / 传送弓 | `references/entity-diagnostics.md` | 服务器侧实体统计与卡顿定位（配合 bot 使用，2026-08-04 实测） |
> | 实体 / 传送门 / 传送弓 | `references/orzmc-entity-teleport-tnt.md` | OrzMC 实体传送可配置化 + TNT 通知聚合（2026-08-09） |
> | 实体 / 传送门 / 传送弓 | `references/teleport-bow-chunk-analysis.md` | 传送弓「未加载区块无法传送」根因分析（2026-08-08 实测定案） |
> | 插件来源与发布 | `references/orzmc-plugin-hangar.md` | OrzMC 插件版本渠道与升级（2026-08-04 实测，本地测试服） |
> | 插件来源与发布 | `references/plugin-sources.md` | 插件发布渠道清单（Modrinth / Hangar 覆盖情况） |
> | 代码审查与验收 | `references/review-framework.md` | 审核框架 + 本地验收记录 + 插件 PR 审查清单，**3 篇合并** |
>
> | 版本 / 历史 | `references/version-baseline-history.md` | 逐轮版本基线快照（09-20→11-02）+ 协议生态演进；**历史快照，不作口径** |
> | 版本 / 历史 | `references/changelog-archive.md` | 技能变更记录存档（< 2.3.2） |
> | 版本 / 历史 | `references/version-check-pitfalls.md` | `mc_version_check.py` 10 条已知坑 + Exa 侧覆盖缺口 |
> | 插件行为 | `references/orzmc-plugin-features.md` | GeoIP / permission.yml 语义 / member-threshold / 维护文案模板 / prison / 耗时中文化 / 防刷阈值 / 权限四组 / BackOnDeath / Brigadier greedy |
> | 站点与手册 | `references/site-manual.md` | 玩家手册维护（OrzMCSite、`server-status tags=`、Hugo 静默丢 HTML） |
>
> **📁 脚本位置约定（找脚本前先看这里）**：
> - `scripts/…`（不带 `~/` 前缀）= **随本技能分发**的脚本，真实路径 `~/.hermes/skills/gaming/orzmc/scripts/`
> - `~/.hermes/scripts/…` = **主机级 cron 脚本**（版本巡检 `mc_version_check.py`、配置审查 `orzmc_config_audit.sh`、`grim_kick_ban.py` 等），不在技能目录内
> - `~/OrzMC/proxy/scripts/…` = **OrzMCProxy 仓库**脚本（`bedrock_host_check.sh/.ps1`、`bedrock_ping.py`、`nethernet_check.py`、`relay-monitor.sh` 等）
> - `~/minecraft-bot/…` = 机器人测试脚本（mineflayer）
> - `scripts/skill_self_check.py` = **本技能自检**（frontmatter / 死链 / 孤儿文档 / 超长行 / 私有信息计数），改完技能跑一次，期望 `结果: PASS`。**删/改名脚本或 reference 前先 `grep -rl "<名字>" SKILL.md references/`**，把所有引用改完再删（否则自检会把旧路径报成死链——而它报的只是症状，真因是引用面没扫完）
> - `scripts/fix_utf8_guard.py --dir <脚本目录>` = **给一批 Python 脚本补/修模块级 UTF-8 guard**（字节安全、幂等；`--check` 只体检，退出码 1=有不合格）——移植或修改 Windows 脚本后必跑，否则 emoji 告警会在 cp936 下变成 traceback
>
## 最近变更（v2.x）

| 版本 | 日期 | 变更 |
|:--|:--|:--|
| 2.6.23 | 2026-11-20 | **三目录铁律进 SKILL.md 正文（不再只放在 reference 里）**：程序 `E:/deploy/orzmc`（`up`/`stop`/`backup` 唯一执行处）/ 数据 `E:/orzmc`（DATA_ROOT）/ 备份 `E:/orzmc-backups`（唯一备份根）；升级=同目录原地覆盖、回滚=用 `_dl` 旧 tarball 覆盖回同路径，**禁止 junction / 版本目录 / 软链**；`tools/`、`reports/`、`deliver/` 留 DATA_ROOT；`backup.sh` 整份打包且默认无排期。**同时修正 `references/skill-publish-flow.md` 已过期的口径**：原文写「公网 IP 必须手工改」，实际已落 `{HOME_IP}`/`{CVM_IP}` 的 ENC_RULES → 改为「按 IP 网段前缀写正则规则，不靠手改文档」；新增《门禁中止了怎么办》四步（不改真源 → 认值归类 → 补 ENC 规则 → 发布后 grep 回证）与两条硬纪律：**已在 git 历史的真实值不会因新规则消失，清历史要改写+force push，只能告知老板拍板、不得默默强推或假装已清**；**发布后先做 `gh pr view` 回读 + `git pull --ff-only`，`git branch -D` 属审批门，别为删分支把整轮验证卡死** |
| 2.6.22 | 2026-11-20 | **推翻 2.6.21 的 junction 方案：统一运行树 = 单个固定目录 `E:/deploy/orzmc`（原地覆盖升级，回滚靠 `_dl` 里的旧 tarball），不再有 `orzmc-current`、不再留 `orzmc-deploy-<ver>` 多版本目录**——老板直接质疑「这不是把部署搞复杂了吗」，且 `install.sh` 本就支持固定目录覆盖升级。同时定三目录职责：程序 `E:/deploy/orzmc` / 数据 `E:/orzmc`(DATA_ROOT) / 备份 `E:/orzmc-backups`（唯一备份根，`E:/orzmc/backup`、`E:/deploy/backups` 已并入）。§7 与 SKILL.md 索引、`eagler-client-access.md` 同步订正；`tools/` 留在 DATA_ROOT（挪它要改 `JAVA_HOME` + 5 处引用，收益不足），备份排除项留 v0.3.0 由 `backup.sh` 解决 |
| 2.6.21 | 2026-11-20 | **`references/deploy-layer-boundaries.md` 新增 §7「统一运行树」**：老板定「部署必须走仓库 release 产物、开发克隆不参与运行」后，把目标形态固化成五层（`_dl` 下载缓存 / `orzmc-deploy-<ver>` **定版目录不可变** / `orzmc-current` junction 作唯一运行入口 / DATA_ROOT / `E:\dev\OrzMC` 只读）。三条可复用手法写进正文：① **换树前先证明产物可信** —— `tar` 解包到 scratch + `diff -r --strip-trailing-cr -q`（期望无输出）+ `sha256sum` 对 `.sha256`，三件全过才拿它当运行树；② **删旧克隆/退役目录前核引用面** —— 文件侧 `grep -rIl` 排除自身目录 + 容器侧一次 `docker ps -a --format '{{.Names}}{{"\t"}}{{.Label "com.docker.compose.project.config_files"}}'`；③ **迁移验收 = 五个容器 `config_files` 全指到定版目录 + `tests/acceptance_eagler.sh`**，面板/代理断 40–90 秒、实例容器不停、玩家会掉线故只选无人时段，回滚=junction 指回旧目录再 `stop && up`。同轮两条 Windows/git 坑：**`docker ps --format` 每行带 `\r`**，`while read c; do docker inspect "$c"; done` 会因 `orzmc-caddy\r` 全部 not found → 循环静默返回空（假阴性，据此删目录即埋雷），改用单命令带 label 或先 `tr -d '\r'`；**squash 合并后本地 main 与远端 diverged**（同一内容不同 hash）→ fast-forward 失败属正常，先 `fetch` 再重置；`reset --hard`/`rmdir /s /q` 属审批门（老板常不在），优先 `git branch -m main local-merged-<n>` + `git switch -c main origin/main` 的非破坏写法；**PR 是否真合并不看回显**（可能被截成 `1 lines output`），用 `gh pr view --json state,mergeCommit` 回读。 |
| 2.6.20 | 2026-11-20 | **新增 `references/deploy-layer-boundaries.md`（部署分层职责边界）**：老板问「测试服靠 deploy 子模块部署，主/子模块各负责什么、哪些要部署后额外处理」时按该文作答。口径：`deploy` = 平台层 + 代理层（compose 编排 / `orzmc.sh` 八条生命周期 / `lib/eagler.sh` 的 jar 下载校验·velocity.toml 渲染·`forwarding.secret` 不覆盖·拓扑切换挪 `disabled/`·`post_up` 自动改 listeners+settings+Geyser 三份配置 / `firewall apply` 五组限源规则），**实例（面板）、`paper-global.yml` 的 velocity secret、TLS·证书·DDNS·路由器、密钥值一律不做**；站点增量只写 `$DATA_ROOT/compose.site.yaml`（改包内文件换包即丢）。三条可复用手法：① `docker inspect <容器> --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}'` 反查容器由哪棵树起 —— 实测同一 project 被「发布 tarball 目录」与「仓库克隆」两棵树各管一半容器，光看容器名查不出；② 判两棵树是否真漂移必须 `diff --strip-trailing-cr`，Windows checkout 的 CRLF vs tarball 的 LF 会把每个文件都报成「完全不同」；③ 部署后手工清单固定 11 项，其中**备份默认没有排期**（`backup.sh` 只是命令），汇报「已部署完整」前先核计划任务。同轮补 Windows 坑：`schtasks /query` 输出 UTF-16LE，git-bash 里 `grep` 报 `binary file matches` → 改用 `Get-ScheduledTask`。 |
| 2.6.19 | 2026-11-18 | **`references/plugin-eol-audit.md` 新增 §7「这些插件能不能加进现有服」**：同一批 jar 的续问（功能 + 冲突 + 可加不可加）是**相对现有环境**的判定，与「插件自身是否健康」不同轴——上游再活跃、与现装体系撞车也是不可加。固化：① **先取三端现有插件真值**（两个后端实例的 `InstanceData/<uuid>/plugins/` + 代理 `eagler/proxy/plugins/` + 自研 jar 的 `plugin.yml`/class 包前缀反推命令面），不读这一步的评估全是空谈；② **冲突三轴** = 命令命名空间（与 EssentialsX/GP/WE/自研命令交集 → 关子模块或改别名）/ 存储与数据格式（同一功能各一套 yml·db 迟早分裂）/ 玩法规则改写（改掉落·物品·登录流程的框架类默认否）；③ **三道硬门槛任一不过直接不可加** —— MC 版本 `game_versions` 含 26.3、Folia `loaders` 含 folia（Hangar `supportedPlatforms` 只标 PAPER 不可信）、**三端入口**（要客户端资源包/客户端 mod 的 ItemsAdder·AllMusic·voicechat 类在 Java+基岩+网页拓扑下等于排除一半玩家）；④ **底层协议库只留一个**（packetevents vs ProtocolLib 同装互踩，GrimAC 依赖前者）；⑤ **结论只给三档且每档必须带前置动作**（无动作的「可加」等于没说）；⑥ 交付 = 主表 + 第二张 sheet「现有插件清单」+ 聊天三档表 + 单列「顺手发现的现有配置问题」（如同一实例同时装 AuthMe 与 SimpleLogin，抢 PlayerLoginEvent）；⑦ 「先只做评估」= 不写 `plugins/`、不改配置、不重启，结尾显式确认未改动。 |
| 2.6.18 | 2026-11-18 | **新增 `references/plugin-eol-audit.md`（插件维护状态调研）**：老板丢来 `plugins.zip` 要「各插件能不能在平台上搜到、有没有持续维护、功能和建议」——固定交付 = **xlsx 表格（插件名/包内版本/启用状态/平台可检索性/上游最新版与日期/维护状态/落后跨度/核心功能/建议，冻结首行+状态色）+ 聊天里三层结论（分档计数 / 最该注意的 3 件事 / 可执行建议）**，产物用 `MEDIA:` 发出而不是只在文字里描述表格。三条硬口径：① **检索主键是 jar 内 `plugin.yml` 的 name，不是文件名**（常见中文前缀 `[跨服传送]`、渠道前缀 `[bukkit_spigot_paper]`，`.jar.disabled` 照样是插件且要计入「启用状态」列）；② **维护判定必须多源交叉**——Spigot 原版停更≠插件已死（第三方 fork 接手很常见），反之只在 Spigot 发版的 GitHub 上是空的，只看一页会把活跃判成弃用；`archived=true` 是硬信号，`pushed_at` 新但两年无 release 记「发版停滞」不记「可升级」；四源皆无则判「自研/小圈子插件，无上游可依赖」。③ **依赖链成组看**（Vane 四件套必须同版本、ItemsAdder→LoneLibs 只是宿主依赖、ProtocolLib/PAPI 是底层被依赖项）。工具细节：解压用 `execute_code`+`zipfile`，不用终端 `rm -rf && unzip`（后者撞审批门）；平台无页时读 jar 的 `MANIFEST.MF`/顶层 package 反推来源；xlsx 在无 xlsx 库的解释器上用 `zipfile` 手写最小 OOXML（inlineStr + frozen pane + cellXfs 状态色）并回读校验。 |
| 2.6.17 | 2026-11-18 | **`references/public-ingress-clash-tun.md` 新增 §9「通配橙云把漏网子域静默接进隧道」**：orzmusic 访问慢的定案——容器发布 `8080` 源站 0.01–0.03s、局域网 0.003s、同机 Caddy 18443 0.04–0.08s，而 `music.{SERVER_NAME}.cn` 走通配橙云隧道 1.9–3.1s（慢 30~80 倍全在入口，与容器/前端/DB 无关）。固化三件事：① **入口阶梯量法**（五条路径同刻并排 `curl -w %{time_total}`，对照组必须是「同机已走 Caddy 的子域」）；② **DoH 三态判定表**（家宽 IP = 灰云直连 / CF 边缘 IP + CNAME 含 `cfargotunnel.com` = 隧道 / 仅 CF 边缘 IP = 橙云回源）；③ **修法两条缺一不可**（显式灰云记录优先于通配、通配别动 + Caddy 复用 18443 按 SNI 加 site 块，容器先 `docker network connect orzmc_default` 才能按服务名反代）。纪律：**新建任何子域后立刻 DoH 查一次它解析到哪**——通配把漏网子域静默接进隧道，等「感觉慢」再查要绕一大圈；「还有哪些服务受影响」按 Caddyfile site 块 + 容器端口 + DNS 子域三表并集逐个归类，**是不是受害者只看 DNS 记录，与业务是什么无关**（orzmusic / sticker 属同类）。`curl` 验 18443 必须 `--resolve`（`-H Host` 会 exit 35）。 |
| 2.6.16 | 2026-11-18 | **`references/server-list-motd.md` 补 §7「官网状态卡（mcstatus.io 转发）的显示一致性」**：官网 `OrzMCSite` 不直连服务器、走 `api.mcstatus.io` 转 JSON，该链路会弄丢两样东西——① **渐变被量化成 16 色 legacy 码**，平滑渐变塌成 `§e`+`§c` 两段且切点落在词中间（网页端永远还原不了），所以**会被官网展示的那行必须用 legacy 单色**（`<gold>`/`§6`），参考配置改为第一行渐变 + 第二行 `<gold>`；② **`version.protocol` 恒返回 47**（本服真实 762，Hypixel/Minville/国内服 Paper 同样 47）= 上游默认值，前端不得拼进版本标签。判定口诀：**「游戏内正确 ≠ 官网卡片正确」**——官网颜色错乱/冒出怪数字，先 `curl` 看 API 返回的实际色段与字段，不要先去改站点 CSS（信息在 API 层就已丢失）；站点侧改动 `node --check` 过语法、无 hugo 就只走 PR + CI，不假装本地预览过。 |
| 2.6.15 | 2026-11-18 | **新增 `references/server-list-motd.md`（服务器列表展示：MOTD / 人数 / 图标）**：代理拓扑下三端真源分开记清——Java 端 `velocity.toml` 的 `motd`（MiniMessage，`\n` 换行）、基岩端靠 `passthrough-motd`/`passthrough-player-counts` 继承不必单独配、网页端 `listeners.toml` 的 `server_motd` 是**字符串数组 + `&` 码**（两套语法不能混贴）。文案口径按老板定案固化：首行品牌+多版本+可连客户端、次行官网标语「一个人是冒险，一群人是传奇」、不写域名（与官网 `show_address=false` 一致）、`show-max-players` 只是展示值（500→30 免空服荒凉）、`sample-players-in-ping=true` 开悬停名单。改法用带 assert 的 Python 精确替换（`motd` 跨引号整行长串，sed/正则易截断），**改完必须 `docker restart orzmc-velocity`（无 reload）**，重启属审批门需老板点头。验收三端各异：Java 走 `mc_ping_probe.py`、**基岩 `GET /v1/join` 一次同时验 MOTD 两行与人数上限（最省事的验收）**、网页 18443 必须 `curl --resolve dev.{SERVER_NAME}.cn:18443:127.0.0.1`（`-H Host` 写法会 exit 35 SSL error，TLS 要看 SNI；期望 404 + `Server: EaglercraftXServer`）。同轮修掉真 bug：`mc_ping_probe.py` 只读 `description["text"]`，而渐变/多行组件的文本在 `extra` 子节点 → MOTD 打印为空、被误判成「配置没生效」白重启；已改为递归 `flatten_text()`（str/list/dict + `extra`/`with`）并用 `⏎` 标换行。教训：**看到「配置改了但探测为空」，先验证探针的解析面，再怀疑配置本身**。 |
| 2.6.14 | 2026-11-17 | **4 条高频守卫合并成 1 条 `orzmc-watchdog`（`330d431ac384`，每 5 分钟），cron 8 条 → 5 条**：合并 `orzmc-entry-probe`(30m)/`orzmc-route-guard`(10m)/`orzmc-nethernet-advertise-sync`(15m)/`gateway-session-guard`(5m)。**做法是薄包装 + tick 计数，不重写任何判定逻辑**：`%LOCALAPPDATA%\hermes\scripts\orzmc_watchdog.py` 用状态文件 `state\orzmc_watchdog.json` 记 tick（只增不减），每 tick 跑 advertise-sync + session-guard，`tick%2==0` 跑 route-guard，`tick%6==0` 跑 entry-probe；每段**独立子进程 + 独立 try/except**（venv python + 绝对路径，`PYTHONPATH=""` 防污染），一段崩不影响其余段；告警按段名分节聚合（`## entry-probe` + 原文，emoji 文案不改），**全绿 stdout 为空 + 退出码 0**（沿用四条旧 job 的既成约定）；任一段 exit≠0 → 退出码 1 且其余段仍跑完；日志 `logs\orzmc-watchdog.log` 每段一行。四个原脚本**保留不删**（watchdog 要调、也是回滚路径）。这条修改**取代** 2.6.13 前「高频看守一律不合并」的结论——那条结论防的是「合成一个会把三类监控一起吞掉」，本设计的段间隔离（子进程 + 独立告警分节）正是对这个风险的正面处理，不是无视它。三条实跑自证：① 连跑 6 次 → `route-guard` 只在 tick 2/4/6、`entry-probe` 只在 tick 6、其余每 tick 都跑，6 次 stdout 全空、退出码全 0；② 临时把 `orzmc_route_guard.py` 换成 `raise SystemExit(3)` → 输出 `## route-guard ⚠️ 退出码 3`、其余段照跑、退出码 1，还原后 sha256 与备份一致 + `py_compile` 通过；③ 用**假 `docker.exe`（PATH 前置 shim）**注入真故障 → watchdog 输出带 `## entry-probe` 分节且含 `🔴` 原文，其余段正常。教训：**cron 脚本只能放 `%LOCALAPPDATA%\hermes\scripts\`**（`cron/scheduler_script.py` 硬校验路径必须在该目录内，技能目录里的副本根本不会被解析）；**验证故障路径时优先注入环境故障（PATH shim），不要去改"已验证"的脚本**——本技能旧版 entry-probe 并没有 `PROBE_SELFTEST` 开关，别照抄不存在的开关。 |
| 2.6.13 | 2026-11-17 | **配置审查交付改成「latest 覆盖 + 快照滚动 3 份」**：原来每跑一次就落一份带时间戳报告，一天跑 6 次就积 6 份。改法：① `config-audit-latest.md` 每次运行**无条件覆盖**（latest 永远是最新结论，不会停在旧结论上）；② `config-audit-<yyyyMMdd-HHmm>.md` 快照**每次也写**（配置审查每次都有差异，不能像 selfcheck 那样只留告警那次），按文件名时间戳降序**只留最近 3 份**，第 4 份起删最旧；③ **两个落点各滚一遍** —— `E:/orzmc/reports/` 与 `deliver_dir()`（`S:` 优先；SSH/服务会话看不到 `S:` 时按 `orzmc_paths` 既有逻辑降级 `E:/orzmc/deliver`，不报错、不判失败）；④ 报告内容、比对逻辑、基线来源、`--no-save` 行为**一律不动**；⑤ 实跑自证：连跑两次 → `reports` 与 `S:` 各为 latest 1 份 + 快照 3 份，11-16/11-17 的 6 份历史副本已滚动删除，`head -6 config-audit-latest.md` 内容正常，`hermes cron list` 8 条 job 名称与 enabled 状态未变（全程未碰 cron、未启停任何容器/实例）。⑥ **顺手堵住一个真漏洞（硬约束「报告不许出现密钥」vs「报告内容不动」的冲突，取前者）**：差异表原本把「值」原样打出来，实测 latest 里出现过明文 `paper-global` 的 `secret`、easybot 的 `api_key`、`im.yml` 的 `app_id/app_secret` —— 落盘前加 `mask_secrets()`：按 key 名（`secret|api[_-]?key|token|passw|app[_-]?id`）把差异项的值替换成 `<已脱敏>`，**只动值不动 key 名与差异条数**（比对/基线/表格结构完全不变）。同时清掉历史明文副本：`reports/` 与 `S:` 各 1 份改前快照、`E:/orzmc/deliver/` 3 份旧副本。教训：**差异报告天然会泄漏密钥** —— 比对的是「值」，一打印就上报告，脱敏必须在落盘口做、不能指望源配置。教训：**「每次都有差异」的报告不能只留告警快照，但也不能无限累积** —— latest 固定名给人看，快照滚动 3 份给回溯，两件事一起做才既不误读也不爆目录。 |
| 2.6.12 | 2026-11-17 | **自检第 7 项假红灯修复（变量原文 vs 展开绝对路径）**：报「❌ 用户 Path 未见 `%JAVA_HOME%\bin`」而注册表里 `Path=%JAVA_HOME%\bin;…`、`JAVA_HOME=E:\orzmc\tools\jdk25` 两项都在 —— 根因是判定只按**展开后的绝对路径**（`E:\orzmc\tools\jdk25\bin`）去比对，注册表存的是**变量原文** `%JAVA_HOME%\bin`；本进程（网关/cron 宿主）没继承 `JAVA_HOME` 时 `os.path.expandvars` 展不开，绝对路径永远匹配不上 → 恒假红。改法：① 判定收敛成**三路任一命中即 ✅** —— (a) 注册表 Path 原文含 `%JAVA_HOME%\bin`（大小写不敏感）；(b) Path 用**注册表 JAVA_HOME 真值**手工展开后含 `jdk25\bin`（自带 `_expand_vars`，不依赖 `os.environ`）；(c) PATH 目录里能直接解析到 `java.exe`；② `JAVA_HOME` 已设但 Path 缺这条 → 只记 ℹ️「PATH 未含 JDK bin，建议补」，**不判 ❌**；③ 真 ❌ 只留给「JDK 目录不可用」= `JAVA_HOME` 已设但 `${JAVA_HOME}\bin\java.exe` 不存在（把值改成不存在的路径即可复现该红灯）。自证三点：全绿 → 临时把 `JAVA_HOME` 改成不存在路径后该项 ❌（exit=1）→ 改回后连跑两次全绿。教训：**比对环境变量要用「原文 + 按真值手工展开」两条腿走**，只比展开结果会在「本进程没继承」时把真配置报成缺。④ **git 假 ❌ 修复**：git 不在 HKCU/HKLM 的 `Path`（服务会话必 FileNotFoundError）→ `resolve_git()` 兜底：`shutil.which` → `C:\Program Files\Git\cmd` → `%LOCALAPPDATA%\hermes\git\cmd` → `…\git\bin`；打印来源+路径，全无才 ❌「git 不可用，git 相关自动化会失败」。自证：注册表 PATH 下全绿 exit=0；两条 exe 改名后 ❌ exit=1。⑤ 用户 `Path` 要变量形式得用 `Set-ItemProperty -Type ExpandString` —— `[Environment]::SetEnvironmentVariable(...,'User')` 会把 REG_EXPAND_SZ 降级成 REG_SZ（实测），写完回读 kind/原文/展开值。 |
| 2.6.11 | 2026-11-17 | **自检交付策略修正（latest 必须永远是最新结论）**：原实现「全绿不落盘」有个真坑——全绿后 `orzmc-selfcheck-latest.md` 会**停在旧的告警内容上**，人一看 latest 就误判当前仍有故障。改为三段口径：① latest **每次运行无条件覆盖**（只有 `--no-deliver` 跳过）；② 带时间戳快照 `orzmc-selfcheck-<yyyyMMdd-HHmm>.md` **只在有 ⚠️/❌ 时**写，滚动保留最近 3 份；③ 退出码规则不变（有 ❌ 才 1）。`--always-deliver` 保留为兼容 no-op。教训：**「静默」只能用在通知上，不能用在状态文件上** —— 状态文件一静默就变成陈旧告警的假象。④ **JAVA_HOME 全局口径落地**：老板已在 Windows 用户级全局设 `JAVA_HOME=E:\orzmc\tools\jdk25` 且用户 `Path` 含 `%JAVA_HOME%\bin`（注册表回读确认）→ 自检第 7 项由「提示全局未设」改为 **✅ 全局已配置**，真值读 `HKCU\Environment`（**不用本进程 `os.environ`**：已运行进程不继承新写的用户级变量，否则会把「全局已配」误报成没配），给 gradle 子进程仍显式注入；SKILL.md 对应坑条从 🟡「全局未设」改写为 🟢「全局已配但必须显式注入 + 已运行进程需重启才继承」；⑤ **MCSM 面板 API 403 口径定案**：老板定「属 API key 失效、不处理，测试服才是正式口径」→ 自检**不含任何面板 API 判定项**，全部结论只走本地直读 + 容器事实（`docker ps` / `docker exec`），面板 403 只以 ℹ️ 口径说明出现在第 4 项，不计告警、不影响退出码。 |
| 2.6.10 | 2026-11-17 | **全栈自检 ⑥ 落地**：新增 `scripts/orzmc_selfcheck.py`（8 项：技能/cron/交付/容器/入口端口/版本基线/工具链/报告新鲜度）+ cron `orzmc-selfcheck`（每天 08:30，`ca0e89c8579d`，异常才落 S:）。报告改为 `orzmc-selfcheck-latest.md` 固定名 + 带时间戳快照**只留 3 份**。两条真坑记在这：① **子进程输出解码 + 判定不能只看末行** —— Windows 上子进程没继承 `PYTHONUTF8` 时按 locale(cp936) 写管道，父进程硬解 UTF-8 得到 `���: PASS`，于是「实际 PASS」被报成 UNKNOWN/❌；正确做法是字节捕获后按 UTF-8→locale→mbcs 顺序解码，判定改为全输出里搜 `结果/RESULT: PASS`（`rc!=0` 才算失败），失败时打解码后的末 5 行；② **映射盘是会话级资源** —— `S:` 只在交互登录会话（Session 1）存在，SSH/服务会话（Session 0）看不到属正常现象，勿据此报交付失败（自检改为先判 `ProcessIdToSessionId`，非交互会话降级成 ℹ️，不计 ⚠️、不影响退出码；真正要盯的是「交互会话里也看不到 S:」） |
| 2.6.9 | 2026-11-17 | **L2 断言迁移收尾**：PR #609 已合并（squash `546f118e` 进 `develop`），`e2eLocalPerm`（21 条）/ `e2eLocalPortal`（7 条）成为仓库 CI 常跑检查；技能侧 `perm-tier-test.js` / `villager_portal_test.js` **删除**，凭本条记录即可回溯来源。本轮真实教训写进注释而非技能：① 日志守卫按实体名判定会被无关实体/大小写/命名空间差异搞成恒真或误红 → 宁可用行为断言；② 探针全局超时必须按各步最坏之和预算，清理放 `finally`；③ 下界换算只缩放 X/Z，Y 原样 |
| 2.6.8 | 2026-11-17 | **Windows 侧自查修复**：`scripts/skill_self_check.py` 原来写死 `~/.hermes/skills/gaming/orzmc`，在 Windows 上直接 `FileNotFoundError`（技能真源已迁 Windows，路径是 `%LOCALAPPDATA%\hermes\skills\...`）→ 改为按 `Path(__file__).parents[1]` 定位，跨平台通用。教训：**技能内脚本不许写死 home 路径**，一律相对自身位置解析 |
| 2.6.7 | 2026-11-17 | **真源与归属定案**：新增「技能真源与编辑纪律」一节——**MC 相关一切只在 Windows Hermes 做，Mac 不再处理 MC**；技能唯一真源 = Windows 侧，编辑只用 Windows 会话的 `skill_manage`（推翻 11-16「Windows 真源 + Mac 编辑后 tar 同步」，那套自相矛盾并造成 Mac 2.6.5/266 文件 vs Windows 2.6.4/269 文件的双端漂移）；Mac 副本移出 skills 树、Mac 两条 orzmc cron 删除、Mac 只保留接收交付文件；同步纪律写成「解压后回读 sha256 + 文件数 + 显式清理多余文件（tar 解压不删旧文件）」 |
| 2.6.6 | 2026-11-17 | **跨端核对与「完成」判据**：① 脚本双副本纪律补两条——只比文件总数会漏「一增一删相抵」，要对两端相对路径清单做**集合差集**并确认「仅对端有」为空；Windows 清单/JSON 带 **UTF-8 BOM**，Mac 端须按 `utf-8-sig` 解码，否则差集全是假差异；② Windows 专项坑新增 **PS 5.1 读 UTF-8（含中文）JSON 按 GBK 解码 → `ConvertFrom-Json 无效的 JSON`**，修法 `-Encoding UTF8` 或回 Mac 侧解析；③ cron 纪律补「新建周期 job 没有 `last_run_at` = 未验证」——汇报完成度必须分「已定义 / 已手动跑通 / 已自然触发」三档 |
| 2.6.5 | 2026-11-16 | **技能侧 L2 断言迁入仓库 CI + E2E 断言规则**：① 两条原本只在技能脚本里、且靠人眼看的断言迁成仓库自举 E2E——`e2eLocalPerm`（三档 LP 组权限矩阵，装真实 LuckPerms、只用插件自身节点）与 `e2eLocalPortal`（村民穿下界门：门框合法 / 内层 portal / 过门前村民在场 / 过门后原维度消失 / 确在地狱维度 / 产物清理），各配 CI job；② `references/plugin-e2e-testing.md` 新增 §CI 自举 E2E（迁移判断口径 + 四条硬规则 + 验证纪律），核心是**日志类断言必须限定到本次测试造的对象**（裸串会被全新世界里无关实体命中，真实断言全过却被日志守卫判红）、前置守卫防假绿、探针客户端版本天花板、异步写库用可数证据而非 sleep；③ 测试归属表把两条从「缺口候选」改为「已迁入」 |
| 2.6.4 | 2026-11-16 | **测试归属清点 + 单测不挂 cron**：① 新增「测试归属：仓库 vs 技能」一节（原则：产品行为断言只放仓库 CI，技能只留够不到 CI 的运维探针与第三方插件现场回归），逐脚本给出判定：`portal-transfer-test.js` **归档**（自述 mineflayer 无法可靠触发 PlayerPortalEvent + 仓库 `PortalIntegrationTest`/5 个 Portal 单测已覆盖）、`perm-tier-test.js`（三档 LP 组矩阵）与 `villager_portal_test.js`（实体过门 L2）**标为仓库缺口候选**，`check-death-chest.js`/`perm-check.js`/`portal-probe.js`/`check_lsdb.py`/`shop_arbitrage_check.py` 与全部运维探针保留；② `orzmc_quality_report.py` 改为**按需手动、不挂 cron**（老板决策：单测/构建回归由仓库自身 CI 保证）；③ `references/plugin-e2e-testing.md` 同步分工口径与归档原因 |
| 2.6.3 | 2026-11-16 | **单测与 cron 两处操作纪律**：① `references/java-test-pitfalls.md` 新增「跑单个测试类」——多模块工程 `--tests` 需限定任务 `:test`，否则子项目报 `No tests found for given includes` 误成 BUILD FAILED；并新增「跨平台断言」——不写死 `/` 分隔符，取最后路径段比名字，验证必须「原失败环境 + POSIX 端各跑一次 + 同 commit CI 绿」；② SKILL.md 新增两条 Windows 操作坑：跑构建/带环境变量命令一律落盘 `.bat` + `cmd /c`（`set VAR=value &&` 尾随空格会进值→假 “invalid directory”；嵌套引号被吃掉→假 “JAVA_HOME is not set”）；cron 停用/退役必须回读 `enabled/state`（字段不是 `paused`）并先停 job 再归档脚本 |
| 2.6.2 | 2026-11-16 | **收口与纠错**：① 新增 `scripts/fix_utf8_guard.py`（ast 定位 + 字节安全插入 + 自查，取代手搓 guard 插入器；Pitfalls 指向它）；② 入口探针口径落地为代码——**实例 stopped/missing 降为提示项**（只写 `INFO` 日志，不进告警集/状态/复述），只有「实例 running 但 RCON 失败」计故障；③ 修正三处过期口径：Windows cron **6 条→8 条**（+配置审查/版本巡检，bisync paused）、核心基线 26.3-246→**26.3-253**、§6 手动跑版本巡检改 Windows 路径；④ 旧名 `ops-migration-20261116`（当日经过）→ **`references/hermes-ops-endpoint.md`**（按主题命名，内容改写成 runbook：脚本手术纪律 + 交付验收 + 回滚，不再叙述当天经过） |
| 2.6.1 | 2026-11-16 | **巡检端整体迁 Windows Hermes + 交付闭环**：① 巡检/升级/配置审查/版本核对的主体脚本改为 Windows 本机直读（`mcsm_env.py`/`orzmc_paths.py`/`orzmc_config_audit.py` 新增，`connectivity_check`/`mc_version_check`/`orzmc_quality_report` 跨平台改造），Mac 端 cron 暂停、脚本归档；② 新增「Windows 宿主执行脚本的硬前提」与 **10 条 Windows 专项坑**（python Store stub、SMB `WinError 1326` ≠ session、pathlib `/` 优先于 `%`、控制台 GBK、PS 5.1 BOM/反引号、TUN 劫持自身 LAN IP、`subprocess text=True` 按 cp936 解码、起 `.bat` 必须绝对路径…）；③ 交付到 S: 盘**端到端实测通**（Windows cron 落盘 → 落点哈希一致），验收纪律写成「真实文件 + 两侧 sha256」，配套 `scripts/deliver_selftest.py`／`deliver_probe.py` |
| 2.6.0 | 2026-11-16 | **巡检口径对齐「统一代理入口」**：① 配置审查新增 `cmp3/fetch3_proxy.py`（读代理侧 Geyser-Velocity 生效配置、自动识别 proxy/direct 模式，取代已停用的实例内副本）⇒ Geyser 假差异从 4 条降到 3 条真实拓扑差异；② `connectivity_check.py` 自动识别运行模式（`detect_test_mode`：25565 通 + 25566 闭 = proxy），proxy 下目标集换成 `proxy`/`proxy-pub`/`prod-mcsm` 并**删掉 25566/19133 旧端口**，新增「后端存活」RCON 25575/25576 探测，`--json` 增 `test_mode` 字段，可用 `ORZMC_TEST_MODE` 强制；③ 基线升到第八轮（Paper 253 / Folia 26.3-8 / Geyser b1303 / Exa WG 7.0.21）；④ Pitfalls 新增两条：**运行中容器 bind mount 的 jar 写不进去（必须 stop→换→start）**、`powershell -File` 必须带 `-ExecutionPolicy Bypass`；⑤ 新增「在 Windows 宿主手动执行脚本的三条硬前提」（venv 解释器 / 映射盘会话隔离→用 UNC / `.env` 缺键静默变空）；⑥ SOP 新增 §2k：**实例保持停止时的文件层验收口径** + 代理侧 jar 换版顺序 + 跨大版本线回滚路径 + Exaroton PUT→回读→DELETE 定型流程 |
| 2.5.0 | 2026-11-10 | **专题文档合并（15 → 3）**：① 权限/LP/Rank 9 篇 → `permission-impl.md`（696 行，原文未改写，按 9 节分区）② 审核/PR 清单 3 篇 → `review-framework.md`（262 行）③ Bot 命令测试 + 机器人 E2E + Paper 26 踩坑 3 篇 → 并入 `testing.md`（552 行）；references **83 → 70 篇**，SKILL.md 索引行同步去重（9+3+3 行 → 3 行）；跨文件引用 15 处自动改指向；自检 70/70、0 死链 0 孤儿 PASS |
| 2.4.0 | 2026-11-10 | **技能整理（瘦身 + 去矛盾）**：SKILL.md **91KB/416 行 → 60KB/389 行**；外置 5 份新文档（`version-baseline-history`、`orzmc-plugin-features`、`version-check-pitfalls`、`site-manual`、`changelog-archive`）；删掉 6 条互相矛盾的「当前权威」历史基线、5 份漂移报告合并为 1 行；修正 4 处与现状冲突的口径：① 投递 `download_from_url` → **scp 直投** ② ExecutableEvents「Folia 不可行」→ **3.26.11.2 已正常运行** ③ 中转/FRP → **标废弃（中转机已销毁）** ④ 版本巡检 cron → **已并入周巡检**；自检 83/83 引用、0 死链 0 孤儿 0 超长行 |
| 2.3.4 | 2026-11-10 | **Minecraft 知识沉淀轮（文档为主）**：新增 `references/domestic-mcsm-log-runbook.md`（国内服启动日志期望值/常态告警/需留意项/Velocity 转发行/外部实测基线）；`mcsm-backend.md` 新增「调用姿势三处硬坑」（`/api/instance` 必带 uuid、列表走 POST body、command 拼 query、status 端点不存在）+ 启停耗时实测；`test-server-upgrade-sop.md` 新增 §2j 第七轮实录 + 6 条真踩过的坑（**备份必须 Move 不能 Copy**、Modrinth 无 sha256、报告版本号不可信、OrzMC 自更新、PowerShell 禁非 ASCII、Exa 不必重配 Geyser） |
| 2.3.3 | 2026-11-10 | **ViaVersion block-versions 安全基线落地**（堵 1.20.5～1.21.4 可利用协议）：测试服 paper/folia + Exa 已改并重启验证（`Done 108.7s / 102.4s`，Exa 无错），国内服 MCSM 待老板手动（含片段）；同轮新 Pitfalls：Geyser 报 ViaVersion outdated 不跟升（最新仅 beta）、PowerShell 下发禁非 ASCII |
| 2.3.2 | 2026-11-09 | **第七轮升级完成（三端）**：测试服 paper = Paper **26.3-246** + Geyser **b1298** + LuckPerms **5.5.91** + WorldGuard **7.0.21**；测试服 folia = Folia **26.2-7（不动）** + Geyser b1298 + LP 5.5.91（WG 保持 7.0.19）；Exa = Paper 26.3-246 + Geyser b1298 + LP 5.5.91 + OrzMC **1.0.30**（6/6 jar sha256 一致，三端 `Done` 无 SEVERE无效）；同轮二批：folia 独有 3 件升 AxGraves **1.32.2** / ExecutableEvents **3.26.11.2** / SCore **5.26.11.2**（均 Modrinth release；升级前实读旧 SCore 为 **5.26.10.20** 而非报告写的 10.17 —— **升前必须 ls 实读文件名，勿信报告**），`Done (99.0s)`；同轮另含：国内服基岩恢复实测 both 双通、paper 备份 135.9MB 清空、Exaroton 基岩入口机制定案（nethernet.md §5.6）；S: 交付包 `orzmc-upgrade-20261109`（8 jar / 111MB zip）|

> 📜 **更早变更记录（2.3.1 及以前）** → `references/changelog-archive.md`

## 版本纪律（2026-11-02 老板定，权威）

| 对象 | 规则 | 说明 |
|:--|:--|:--|
| **第三方插件** | **只跟 release 正式版** | beta / alpha / SNAPSHOT 一律不升；已装的预发布构建应**回退到正式版** |
| **MC 核心** | 只升 **STABLE / BETA** | ALPHA（如 Folia 26.3-6）不动，只记录 |
| **OrzMC 自研插件** | 豁免上述插件纪律 | 测试服刻意走 Hangar beta 通道验证功能 |
| 例外判定 | 上游**只发**一种构建（如 Geyser 只发 build 快照、GrimAC 的 alpha 曾为 26.3 支持）时 | 需逐个说明理由，并在巡检报告里标注 |

⚠️ **比对「最新版」必须先按 `version_type=release` 过滤，再比版本号**（2026-11-02 真实疏漏）：
ViaVersion 最新一条是 `5.12.3-SNAPSHOT`，只看「最新一条」会把整项误判为 SNAPSHOT 跳过，而 10-27 发布的 **5.12.2 正式版**就在下面。
`mc_version_check.py` 已按此改造：✅=最新正式版 / ⚠️=有正式版可升 / 🔵=部署为预发布或高于正式版（应回退）。

## 巡检体系（六部分）

| 部分 | 脚本 | 关键点 |
|:--|:--|:--|
| ① 配置审查 | **Windows** `%LOCALAPPDATA%\hermes\scripts\orzmc_config_audit.py`（cron `orzmc-config-audit`，周一 09:05） | **2026-11-16 迁 Windows 后改为本机直读**：基准 = `InstanceData/<paper uuid>/` 本地遍历，入口 Geyser 取代理侧 `Geyser-Velocity/config.yml`（存在即 proxy 模式），对比 = Exaroton API；报告落 `E:/orzmc/reports/` + 交付目录两处（公网 IP 自动脱敏），**交付口径 = `config-audit-latest.md` 每次无条件覆盖 + 带时间戳快照 `config-audit-<yyyyMMdd-HHmm>.md` 每次也写、滚动只留最近 3 份**（2.6.13，与 selfcheck 同策略）。旧 Mac 版 `orzmc_config_audit.sh + cmp3/fetch3_ssh.py` 已归档（`.archive-20261116/`），不再运行 |
| ② 插件质量 | **Windows** `orzmc_quality_report.py`（**按需手动，不挂 cron**） | 依赖 Windows 本机 Temurin JDK 25（`E:/orzmc/tools/jdk25`）+ 仓库克隆 `E:/orzmc/src/OrzMC/plugin`；gradle 走 `gradlew.bat`。**2026-11-16 老板决策：单测/构建不纳入周巡检**——回归由 OrzMCPlugin 仓库自身 CI（build + e2e-paper/player/lp/im + folia-smoke）保证，本脚本只在「想在本机看覆盖率/复现失败用例」时手动跑 |
| ③ 版本巡检 | **Windows** `mc_version_check.py`（cron `orzmc-version-check`，周一 09:10） | 部署侧读**本机实例 jar 文件名**（`mcsm_env.py` 本地适配器提供 `mcsm_list`），渠道侧仍查上游 release；release-only 语义不变 |
| ④ 健康体检 | `orzmc_weekly_patrol.py`（Windows，周一 09:15，cron `orzmc-weekly-patrol`） | 日志 SEVERE/加载失败、Geyser `Started on UDP`、NetherNet 警告、备份堆积/磁盘水位、TPS/在线人数；Mac 版 `orzmc_weekly_health.py` 未迁（与 patrol 重叠，已归档） |
| ⑤ **连通性体检** | **Windows** `connectivity_check.py` |**Java + 基岩双协议一次跑完**：DNS（自动绕本机 TUN fake-IP）/ Java 协议握手 / RakNet Pong（旧）/ NetherNet 信令 `GET /v1/join`（新）/ 基岩端口 HTTPS 信令 / 可选 `--external` 公网 TCP 外部节点。**自动识别测试服运行模式**：`proxy`（统一代理 Velocity）→ 只测入口 25565/19132 + 后端 RCON 25575/25576 可连性，**不再探测 25566/19133 旧端口**；`direct` → 旧双实例目标。`ORZMC_LAN_HOST` 在 Windows 上必须是 **127.0.0.1**（Windows 侧 Mihomo TUN 会劫持发往自身 LAN IP 的包，探测 192.168.0.33 会全线超时） |

| ⑥ **全栈自检** | **Windows** `skills/gaming/orzmc/scripts/orzmc_selfcheck.py`（cron `orzmc-selfcheck`，每天 08:30，`ca0e89c8579d`） | 8 项一次跑完：技能版本/文件数 + `skill_self_check` 结论、cron 全量 job（挑出 disabled / last_status≠ok）、交付目录可选级 + 真写测试、容器（velocity/caddy/easybot 应 Up）+ paper/folia 应 stopped、入口 25565/19132 **TCP 实连**、jar 文件名 vs 版本基线、jdk/gradle/node/git、`E:/orzmc/reports` 新鲜度。**每次运行都无条件覆盖 `orzmc-selfcheck-latest.md`**（latest 永远 = 最近一次真实结论，全绿后也必须变回全绿，不许停在旧告警上）；带时间戳快照 `orzmc-selfcheck-<yyyyMMdd-HHmm>.md` **只在有 ⚠️/❌ 时才写**，滚动**最多留 3 份**（第 4 份起删最旧的），全绿不产生新快照；19132 **只做 TCP 实连**，UDP 侧由 `orzmc-entry-probe` 的 `GET /v1/join` 覆盖（两处不重复探测）；SSH/服务会话（Session 0）看不到 `S:` 属正常——映射盘是会话级资源，该项降级为 ℹ️，不计 ⚠️、不影响退出码，真正该报的是「交互会话里也看不到 S:」；`--json` / `--no-deliver` 可选。cron 侧只放转发 stub（`%LOCALAPPDATA%\hermes\scripts\orzmc_selfcheck.py`），真源仍在本技能目录 |

> 🖥️ **巡检端归属（2026-11-16 老板决策 #1 全量迁移）**：orzmc 的巡检 / 升级 / 配置审查 / 版本核对 / 交付打包**全部在 Windows Hermes**（%LOCALAPPDATA%\hermes）执行，Mac 端 cron 已暂停、脚本已归档（只读）。Windows 端不需要 SSH、不需要面板 files API——实例目录与代理配置都在本机。

**TPS/玩家数取数纪律**：**从 `logs/latest.log` 读**，面板 `outputlog` 只做兜底（缓冲会截断，表现为「日志与面板都读不到 TPS」的假告警）。两种格式都要认：Paper `TPS from last 1m, 5m, 15m: a, b, c`；Folia 分区行 `at X.XX TPS`（多行，取 **min** = 最差分区，否则会拿平均值掩盖卡顿）。日志内容先剥 ANSI 色码再解析，否则数字前会粘色码。

## 技能真源与编辑纪律（2026-11-17 老板决策）

> **一句话**：**Minecraft 相关的一切只在 Windows Hermes 上做，Mac 端不再处理 MC。** 本技能的唯一真源是 Windows `C:\Users\WangA\AppData\Local\hermes\skills\gaming\orzmc\`。

- **编辑**：在 **Windows 侧**的 Hermes 会话里用 `skill_manage` 改；不要再在 Mac 上编辑本技能再同步（2026-11-16 的"Windows 唯一真源 + Mac 编辑后 tar 同步"是自相矛盾的，导致双端漂移：Mac 2.6.5/266 文件 vs Windows 2.6.4/269 文件）。
- **Mac 侧已退休**：本地技能副本移出 skills 树（`~/.hermes/skills/` 下不再有 orzmc），Mac 的两条 orzmc cron 已删除，Mac 端脚本归档在 `~/.hermes/scripts/.archive-20261116/`。Mac 只保留"接收交付文件"这一件事（`S:\` = Mac `~/Downloads`）。
- **同步纪律（若某天必须从他机同步）**：`tar -cf x.tar -C <skills>/gaming orzmc` → `scp` → **解压后必须回读 `SKILL.md` sha256 与文件数**；`tar` 解压**不会删除**目标侧多余文件，必须显式比对文件清单并清理（曾因此残留改名/归档前的旧文件）。
- 迁移/双端状态的完整来龙去脉见 `references/hermes-ops-endpoint.md`。

## 测试归属：仓库 vs 技能（2026-11-16 老板决策）

**原则**：**产品行为的断言只放仓库**（OrzMCPlugin 的 `src/test` / `src/integrationTest` / `e2e/`，由 CI 每次跑）；技能只留「够不到 CI 的运维探针」和「第三方插件的现场回归」。写新测试前先问一句「能不能进仓库 CI」，能就别写进技能 —— 技能里的"测试"没人跑，只会造成"有覆盖"的错觉。

| 技能脚本 | 测什么 | 判定 |
|:--|:--|:--|
| `portal-transfer-test.js` | 传送门 transfer 触发 | ❌ **已归档**（2026-11-16）：脚本自述「mineflayer 位置同步与服务器端不一致，tp 到门中心也不触发 PlayerPortalEvent」= 不能当断言；仓库已有 `PortalIntegrationTest` + `PortalServiceTest`/`PortalBuilderTest`/`PortalCleanerTest`/`PortalPersistenceTest`/`PortalLabelRendererTest` |
| ~~`perm-tier-test.js`~~ | 三档 LP 组权限矩阵（default/member/builder） | ✅ **已迁入仓库并删脚本**（PR #609 合并 `546f118e`）：`e2e/ci/perm-tiers-probe.js` + Gradle `e2eLocalPerm` + CI job `e2e-perm`，21 条断言、装真实 LuckPerms、只用插件自身节点；技能侧已删，**别在这里补同类断言** |
| ~~`villager_portal_test.js`~~ | 实体（村民）过真实传送门 | ✅ **已迁入仓库并删脚本**（PR #609 合并 `546f118e`）：`e2e/ci/entity-portal-probe.js` + Gradle `e2eLocalPortal` + CI job `e2e-portal`，7 条断言（门结构/过门前在场/落地维度/坐标清理）；技能侧已删 |
| `check-death-chest.js` | 死亡箱生成回归 | ✅ 保留：测的是第三方 `devcyntrix/death-chest`（本地修复版），不属 OrzMCPlugin 仓库 |
| `perm-check.js`、`portal-probe.js` | 玩家身份查 LP 输出 / 方块扫描 | ✅ 保留：纯观察探针（RCON 不回显 LuckPerms 输出，权限只能玩家身份查） |
| `check_lsdb.py`、`shop_arbitrage_check.py` | LoginSecurity 库 / EzShops 套利 | ✅ 保留：第三方插件数据核对 |
| `connectivity_check` / `orzmc_entry_probe` / `mc_version_check` / `deliver_*` / `skill_self_check` | 入口、连通、版本、交付、技能自身 | ✅ 保留：运维检查，不是产品测试 |

**仓库侧三层测试在哪**（以后找覆盖看这里）：`src/test`（单测，L0）· `src/integrationTest`（MockBukkit 集成，L1，17 个集成测试类）· `e2e/cases/01-06`（真实服 L2 手动套件）+ `e2e/ci/player-probe.js`（玩家侧自举，**CI 每次跑**，模式 = Gradle 任务自建服务端 + `node` 探针 + 控制台断言）。新增同类任务照这个模式（已落 `e2eLocalPerm` / `e2eLocalPortal`）。**写这类断言的规则 → `references/plugin-e2e-testing.md` §CI 自举 E2E**：日志类断言必须限定到本次测试造的对象（裸串会被全新世界里无关的自然实体命中→假红）、每个 PASS 前加前置守卫防假绿、探针客户端版本有协议天花板、异步写库的中间件用可数证据同步而不是 sleep。

**脚本双副本纪律**：cron 用的权威副本在 **Windows** `%LOCALAPPDATA%\hermes\scripts\`（Mac 端已归档 `~/.hermes/scripts/.archive-<日期>/`），技能 `scripts/` 下的同源副本仅供分发——**只改一边会导致下次巡检跑旧逻辑**；改完必须比对两份一致（Mac `shasum -a 256` / Windows `Get-FileHash -Algorithm SHA256`）。⚠️ Mac 上 `cp -f` 有 `-i` 别名会交互提示导致静默不覆盖 → 用 `\cp -f`。

⚠️ **`tar` 解包只覆盖、不删除：删/改名脚本后对端会留「幽灵副本」**。技能镜像同步用的 `tar -cf … | scp | extract` 流程不会清掉目标端已不存在的文件，**只比 `SKILL.md` 的 sha256 或只数 `SKILL.md` 一致就宣布同步完成，会漏掉**——Mac 上删掉的脚本在 Windows 技能目录里照样在，将来可能被 `skill_view`/脚本索引捡回来，或反过来被当成真源。纪律：① **增删脚本后按「文件计数」核对两端**（`tar -tzf x.tar | wc -l` vs 对端文件数），sha 只证明内容一致、不证明集合一致；② 删除脚本时先在源端归档（`~/.hermes/scripts/.archive-<日期>/`）再删，然后**在对端显式 remove 同一个文件**（Windows 用 `Remove-Item -LiteralPath <绝对路径>`），不要指望下一次同步替你清；③ **只比总数会漏「一增一删相抵」**：两端各导出相对路径清单（`find . -type f | sed 's|^\./||' | sort`）+ 做**集合差集**，必须看到「仅对端有」为空才算同步完；④ 两端清单常因编码对不上（Windows 侧带 **UTF-8 BOM**）→ Mac 端比较/解析一律按 `utf-8-sig` 解码，否则全行都判不同、差集全是假噪声。

> 巡检纪律：**只读**；每部分必须给「数据有效性证据」（文件数/条目数/实例数），数据源不可达时显式写「本次无效」，禁止输出假绿结论。
> **落盘前脱敏（2026-11-09 起强制）**：报告/脚本/docstring 里的公网 IP 一律写成 `<公网IP>` / `<生产公网IP>`（域名可写）；`secret_guard` 会在 bisync 前拦截，命中即中止推送 —— 先脱敏再推送，不要绕过门禁。

## 三端拓扑（2026-10-19 老板确认，权威）

| 端点 | 域名 | 托管方式 | 角色 / 说明 |
|:--|:--|:--|:--|
| **本地测试服** | `dev.{SERVER_NAME}.cn` | 本机 MCSM 面板（Win 宿主 `E:/orzmc`；实例 `papermc-test` + `folia-test`） | 升级/插件/基岩/NetherNet 的实测场；家宽动态 IP + DDNS；官网 `show_address=false`（地址隐藏） |
| **国内服（线上生产）** | `{SERVER_HOST}` | **MCSM 面板托管** | 国内玩家生产环境；运维走 MCSM API；基岩 **`transport: both`**（`webrtc-port: 19134`），`advertise-addresses` **必须显式写 `["<域名>:19134"]`（端口 = webrtc-port，不是 port）** —— 留空靠 STUN 会下发错地址（2026-11-02 实测的连不上真因）；放行 TCP 19132 + UDP 19132 + UDP 19134；新旧客户端都能进 |
| **海外服（线上生产）** | `paper.{SERVER_NAME}.cn` | **Exaroton 托管** | 海外玩家生产环境；核心由面板管理（不能上传核心 jar），插件走 `plugins/update/` |

**已下线**：腾讯云中转机 2 台（正式 + 试用，2026-10-19 老板确认销毁）→ **frps 中转链路不再运行**；`references/cross-carrier-networking.md` 中的方案/工具链仍可复用，重建时按该文顶部清单执行。
**已核实（2026-10-19，本机 Windows 宿主实查）**：无 frpc 计划任务（`schtasks` 无匹配）、无 frpc 服务（`sc query` 无匹配）、无 `~/OrzMC/proxy` 目录 → **该宿主未部署 frpc 客户端，不存在指向旧中转 IP 的残留配置**。

**查询现状的可靠方法**（本机 Clash TUN 会把域名解析成 `198.18.x` fake-IP，`ping`/`nslookup` 结果不可信）：
```bash
curl -s -H 'accept: application/dns-json' \
  'https://1.1.1.1/dns-query?name=<域名>&type=A'
```

## 使用时机
- 用户要创建新的 PaperMC 服务器（本机/Exaroton/MCSM）
- 用户要升级 PaperMC 服务端版本或构建
- 用户要安装/更新/卸载插件
- 用户要备份或查看服务器状态/日志
- 用户要排查性能/卡顿（→ `references/spark-analysis.md`）
- 用户要统计实体或定位 FPS 问题（→ `references/entity-statistics.md`）
- 用户要机器人玩家/自动操作（→ `references/mineflayer-bot.md`）

## 架构：一套动作，三种后端

```
统一动作: create / status / start / stop / restart / logs
         upgrade / plugin / backup / command
              │
    ┌─────────┼──────────┐
    ▼         ▼          ▼
  local    exaroton    mcsm
  本机目录   云端API    面板API
```

后端通过环境变量 `PAPER_BACKEND` 选择（默认 `local`）：
- `local` — 本机目录操作（`PAPER_DIR`）→ `references/local-backend.md`
- `exaroton` — Exaroton 云端（`EXAROTON_API_KEY` + `EXAROTON_SERVER_ID`）→ `references/exaroton-backend.md`
- `mcsm` — MCSManager 面板（`MCSM_URL` + `MCSM_API_KEY` + `MCSM_INSTANCE_ID`）→ `references/mcsm-backend.md`

## 关键事实（当前基线 2026-11-09）

> 🔄 **本地测试服拓扑 = MCSM 本机栈（2026-09-03 全量迁移完成）**：原裸跑 `~/minecraft-server`/`~/folia-test`（start.sh/screen 启动）已删除，测试服改由本机 MCSM 面板 **mcs.{SERVER_NAME}.cn** 管理——双 Docker 实例 **`papermc-test`**（uuid `716c2fb712154c36ba5ab0f1480d3f87`，Paper 26.2）与 **`folia-test`**（uuid `8A932DD47F4D42AAAD6A6A9A5FAD2A91`，Folia 26.2），**各自独立地图，可同时运行**（2026-09-11 核实：两容器各挂自己的 `InstanceData/<uuid>`，无共享 world 卷；`world` 目录 inode 不同、各 ~2.1G；实测 Paper 25565/19132 + Folia 25566/19133 同时在线双通道均通）。实例数据在宿主 `/Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/<uuid>/`（含 server.properties/plugins/logs 完整服务端，**宿主侧直接可见可操作**）。**本 SKILL 中所有「本地测试服/本地双服/本地已改+重启」如无特别说明均指这两个实例**（jar/插件部署 = 直接 cp 实例目录 + 面板重启实例；启停 = 面板操作）。五连坑/克隆实例法/详细路径见 `references/testing.md`「MCSM 本地栈 Docker 实例」节。

> 🆕 **2026-11-12 起本地测试服入口变成「统一代理」（ADR-036，Windows 端实测形状）**：容器 **`orzmc-velocity`**（Velocity + Geyser-Velocity 2.12.1 + EaglercraftXServer）持有公网 `25565/tcp`、`19132/tcp+udp`；两个 MCSM 实例**不再发布 Java 端口**（RCON 已于 2026-11-19 关闭并移除端口映射，只剩语音 `24454/udp`），代理按容器名 `MCSM-716c2f:25565`（lobby=Paper）、`MCSM-8A932D:25565`（survival=Folia）回源，`VELOCITY_TRY=lobby`。基岩走 `transport: nethernet` + `webrtc-port: 0`（单端口，**没有 19134**），网页客户端走 `https://dev.{SERVER_NAME}.cn`（宿主 443，Caddy `orzmc-caddy` 反代，101=活）。实例内 `Geyser-Spigot` 被自动停用（日志 `Geyser is disabled due to Velocity`），基岩 advertise 只在代理侧 `eagler/proxy/plugins/Geyser-Velocity/config.yml`。开关 `.env`：`ENABLE_VELOCITY` / `ENABLE_EAGLER` / `EAGLER_GEYSER_TRANSPORT` / `EAGLER_PUBLIC_HOST`。切换记录 `eagler/CUTOVER-20261112.md`，细节见另一技能 `devops/mcsm-instance-ops` 的 proxy-entry-mode 文档（跨技能引用，不在本技能 references 内）。
>
> ⚠️⚠️ **2026-09-12 拓扑更正：面板栈本体已迁 Windows（`E:/orzmc`，见 `references/platform-migration.md`）** —— `mcs.{SERVER_NAME}.cn` 现指向 Windows 上的 MCSM（web `10.18.0` / daemon `4.18.0`），Mac 上 `/Users/Shared/orzmc/...` 只是**迁移前的历史副本（勿直读、勿据此判断线上状态）**；Mac 已无 docker。**操作一律走 MCSM API**（凭据 `~/.hermes/.env` 的 `MCSM_LOCAL_*`）：`instance.status` 3=运行中 / `files/list|download|mkdir|copy|move|delete` / `files/download_from_url` / `files/upload` / `protected_instance/open|stop|command`。升级实测流程 + 配置迁移 + 备份清理 → `references/test-server-upgrade-sop.md`；配置补键工具 `scripts/config_merge_defaults.py`。
> ⚠️ **面板可达性依赖 Windows 侧 `cloudflared` 隧道**：2026-09-28 / 10-12 两次 `HTTP 530 + error 1033`（Argo Tunnel error）故障 → **周巡检静默空转**（配置拉取 0 文件、版本巡检部署侧全空，脚本仍报 `ok`）。**老板已于 2026-10-12 在 Windows 侧加自愈守护**。排查法：`curl -o /dev/null -w '%{http_code}' https://mcs.{SERVER_NAME}.cn/`（同域 `orzmc.{SERVER_NAME}.cn` 200 而 mcs 530 = 仅面板隧道故障）；⚠️ **巡检报告若出现「MCSM 端 0 文件 / 全部插件未部署」= 故障信号，须先探面板再下结论**。
> 🔑 **2026-10-26 新增同类假阴性：面板 apiKey 被轮换** —— `~/.hermes/.env` 的 `MCSM_LOCAL_API_KEY` 失效时表现与隧道故障相同（`mc_version_check.py` 全部「未部署」、审计扫描 0 清单项，均不报错）。**三秒判定法**：`GET /api/auth?apikey=<key>` → `403 {"data":"密钥不正确"}` 即密钥失效（vs 隧道故障是 curl 5xx/超时）。面板侧真值在 Windows `E:\orzmc\mcsmanager\web\data\User\<uuid>.json` 的 `apiKey` 字段（`ssh win` 可读，用户 joker=实例归属者 / admin=超管）；`.env` 在 cron 模式下被安全策略禁止写入，应急可用「环境变量 + `mcsm_env._load_env` 打补丁」在内存层覆盖跑一轮，但**必须请老板更新 .env**（否则下周继续盲飞）。⚠️ 同期面板 `files/list` 单次延迟 5.7~37s、`files/download` 签发大量失败 → 全量递归扫描（~70 次 list）跑不完，改定点拉取（核心 7 件 + 关键插件配置）。
> 🆕🔑 **2026-10-26 晚巡检实证：MCSM 配置/版本数据的首选源 = SSH 直读 Windows 实例目录，不是面板 API**。面板 `files/list` 实测 3.7~135s 抖动（26 次调用中位 8.6s），`files/download` 签发+拉流 2/5 失败、单文件 111~135s → 全量（58 件）拉不完；而 `ssh win`（192.168.0.33 / User WangA）→ `E:\orzmc\mcsmanager\daemon\data\InstanceData\<uuid>\` 直接 `tar -cf - -T <清单>` 打包回传 **58/58 秒级全取**。**纪律：① 「list 超时 8s」在慢响应期不成立（会砍掉约一半数据），实际用「8s 首档 + 50s 复审」；② 需要全量配置/部署版本时先试 SSH 直读，面板 API 仅作 SSH 不可用时兜底；③ jar 版本盘点也走 SSH `Get-ChildItem`（比签名单文件快 100 倍）。** 脚本化改造（审计 + 版本巡检默认走 SSH）列入待决策。
> 🔴 **2026-11-02 周巡检：面板 `/download` 数据通道整体 502（不再是"慢/偶发失败"，而是全量失败）**。症状：`api/files/download` 签发 **200 + password 正常**，但 `GET https://mcs.{SERVER_NAME}.cn/download/<password>/<file>` **一律 502 Bad Gateway**（59/59），http 直连则 `RemoteDisconnected`；同时 `/api/overview` 200、`service/remote_services_list` `available:true`、`files/list` 正常 → **不是密钥/隧道/daemon 故障，而是该下载路由打通不到 daemon**。`orzmc_config_audit.sh` 因此每周必然 `STATUS: ❌ FAIL(MCSM 0 文件)`（静默降级，报告里全是"基准端缺失"）。**处置：SSH 直读兜底已实战有效**（`scp` 清单文件到 `C:\Users\WangA\hermes-tmp\`，`ssh win` 里 `cd /d <实例目录> && tar -cf - -T <清单>` 重定向回本机解包，66/66 秒级），待给 `fetch3_configs.fetch_mcsm` 加 SSH fallback（待决策 #1，见 `references/config-drift-report-20261102.md`）。
> 🆕🆕 **2026-11-16 第八轮升级后基线（当前权威）**：**paper** = Paper **26.3-253（STABLE）** + Geyser-Spigot **b1303**（实例内、被 Velocity 自动停用）+ LP 5.5.91 + WG 7.0.21 + WE 7.4.6 + OrzMC 1.0.31-dev.435（beta 通道）；**folia** = Folia **26.3-8（STABLE，26.2 线 11-15 EOL → 首次跨线）** + Geyser **b1303** + EE **3.26.11.15** + SCore **5.26.11.15** + WG 7.0.19（元数据含 26.2/26.3，刻意不跟 7.0.21）+ OrzMC 1.0.29-dev.427；**入口代理** = Velocity 1.7.2-26.3 + Geyser-Velocity **b1303**（生效 Geyser）；**Exa** = Paper 26.3(253) + Geyser **b1303** + WG **7.0.21** + OrzMC 1.0.30。**两实例按老板决策保持停止**（启动验收/世界数据升级由老板自用触发）；升级件 sha256 测试服 6/6、Exa 回读 2/2 一致；旧件备份 `upgrade-bak-20261116`（paper 2 件 / folia 4 件，已清三个跨轮旧备份）；交付包 `~/Downloads/orzmc-upgrade-20261116`（8 jar / zip 246MB）。
> 📜 **2026-11-09 第七轮基线（历史）**：~~当前权威~~ →**paper** = Paper **26.3-246（STABLE）** + Geyser **2.12.1-b1298** + LuckPerms **5.5.91** + WorldGuard **7.0.21** + voicechat 2.6.25 + GriefPrevention 16.18.8 + Via 5.12.2 + GrimAC 2.3.74 + OrzMC **1.0.30**（启动自更新）；`Done (94.1s)`。**folia** = Folia **26.2-7（按纪律不动，26.3 仍 ALPHA）** + Geyser **b1298** + LuckPerms **5.5.91** + GP3D 19.0.5 + WorldEdit 7.4.6 + WorldGuard **7.0.19（保持）** + OrzMC 1.0.30 + AxGraves **1.32.2** + ExecutableEvents **3.26.11.2** + SCore **5.26.11.2**（后三件均 release，且 **SCore↔ExecutableEvents 必须成对升**）；`Done (99.0s)`。**Exa（海外生产）** = Paper **26.3-246** + Geyser **b1298** + LuckPerms **5.5.91** + OrzMC **1.0.30**（Release）；`Done (37.4s)`。升级件 sha256 6/6 远端=本地；旧件备份 `upgrade-bak-20261109`（测试服）/ `~/.hermes/tmp/exa-bak-20261109/`（Exa）。**国内服 MCSM 因 apikey 失效仍未同步，需人工**。
>
> 📚 **历史基线（09-20 / 10-12 / 10-19 / 10-26 / 11-02 逐轮快照 + 协议生态演进结论）** → `references/version-baseline-history.md`（仅演进参考，**不当口径用**）。
> 📚 **OrzMC 插件行为/配置语义（GeoIP、permission.yml reload 语义、member-threshold、维护文案模板、prison、耗时中文化、防刷阈值、权限四组、BackOnDeath/GetMeHome、Brigadier greedy）** → `references/orzmc-plugin-features.md`。
>
> ⚠️ **§ 通道纪律 + 双实例刻意差异**：核心只升 **STABLE**（现 26.3-253）；`block-versions` 的用途已从「拦 26.3 客户端」变为「堵 1.20.5–1.21.4 可利用协议」（见 Pitfalls），别照抄旧结论。paper 实例 `im.yml` = `backend: builtin` + `i18n.default_lang: en-US`；folia 实例 = `backend: easybot` + `zh-CN` —— **老板 2026-09-12 明确确认的刻意设计（paper 专测英文语言包 + 内置直连，folia 测 EasyBot 网关），两条 IM 通道并行保留：勿统一、勿改语言**。

- **旧 API `api.papermc.io/v2` 已完全废弃（410 Gone）**——用 fill-data 新机制（`parse_papermc.py` 封装）
- ⚠️ **PaperMC 通道判定（新）**：fill API 的 build 对象带 `channel` 字段（STABLE/BETA/ALPHA）——「最新版」不等于「可上线版」，升级前先看 channel；本会话脚本查询：`https://fill.papermc.io/v3/projects/paper/versions/26.2/builds/latest`
- **插件基线（历史快照 2026-08~09，完整版已外置）**：OrzMC 1.0.17→1.0.24 演进、EzShops 2.5.9（yaml 存储）、voicechat 2.6.21、**GrimAC 渠道/处罚阈值/VL 语义/误报源/6 分类 kick 实测**、LoginSecurity `ls.bypass` 事件、LuckPerms/SkinsRestorer/WE 限额等全部细节 → `references/plugin-baseline-legacy.md`；GrimAC 调优专项 → `references/grimac-tuning.md`。**当前版本一律以上方 2026-10-19 基线行为准。**

## 三目录铁律（程序 / 数据 / 备份）

| 层 | 路径 | 说明 |
|:--|:--|:--|
| 程序 | `E:\deploy\orzmc` | 单个固定 Release 目录，`orzmc.sh` 的唯一入口；`up` / `stop` / `backup` **只在这里执行** |
| 数据 | `E:\orzmc` | `DATA_ROOT`：MCSM 实例、eagler、caddy 证书、easybot、site、`.env`、`compose.site.yaml` |
| 备份 | `E:\orzmc-backups` | 唯一备份根（其它任何 `backup`/`backups` 目录一律并入这里后删除） |

- **升级 = 同一目录原地覆盖**（untar over `E:\deploy\orzmc`），回滚 = 用 `E:\deploy\_dl\` 里的旧 tarball 覆盖回同一目录。容器 `config_files` 因此永远指向同一路径，不需要重新指向。
- **不要**引入 junction（`orzmc-current`）、`orzmc-deploy-<ver>` 版本目录、软链——老板的原话是「这不是把部署搞复杂了吗」。多一层不带来任何收益，`install.sh` 本来就支持覆盖升级。
- **非运行数据不许写进 `DATA_ROOT`**。`tools/`（JDK/gradle/hugo）例外留在 `E:\orzmc\tools`：`JAVA_HOME` 与 5 处引用写死它，搬它要改环境变量 + 提 PR，收益不足；备份膨胀在 `backup.sh` 的排除项里解决，不靠搬家。`reports/`、`deliver/` 同理留原地（hermes 脚本 + cron 硬编码）。
- `backup.sh` 默认 `tar` 整份 `DATA_ROOT`、**不含任何排除项**，且**默认没有排期**——汇报「已部署完整」前先核计划任务，别把「命令存在」当「备份在做」。

## 操作步骤

### 1. 获取最新版本信息
```bash
curl -s https://papermc.io/downloads/paper | python3 ~/.hermes/skills/gaming/orzmc/scripts/parse_papermc.py
# 输出: paper-26.2-92 059d00bbce0fa1707739618b3276f5c80b9655dc0f964306fa799a9c7cb01cc2
```

### 2. 创建/升级/备份/状态（local）
> ⚠️ 2026-09-03 起：本机 OrzMC 测试服已迁 MCSM 面板管理（local 仅适用临时本机目录服，如 ~/minecraft-server）；MCSM 实例的 jar 升级 = 直接替换实例目录 jar（`InstanceData/<uuid>/`）+ 面板重启实例
```bash
# 创建
PAPER_BACKEND=local PAPER_DIR=~/minecraft-server \
  ~/.hermes/skills/gaming/orzmc/scripts/adapters/local.sh create
# 升级核心 jar（自动备份旧 jar 可回滚）
PAPER_BACKEND=local PAPER_DIR=~/minecraft-server \
  ~/.hermes/skills/gaming/orzmc/scripts/adapters/local.sh upgrade
# 备份 world + plugins + server.properties（保留 24 份）
PAPER_DIR=~/minecraft-server ~/.hermes/skills/gaming/orzmc/scripts/backup.sh
# 状态 / 日志 / 命令
PAPER_DIR=~/minecraft-server ~/.hermes/skills/gaming/orzmc/scripts/adapters/local.sh status
PAPER_DIR=~/minecraft-server ~/.hermes/skills/gaming/orzmc/scripts/adapters/local.sh logs 50
```
> 详细（含 local 坑：无 rcon、运行时改 whitelist 不生效、macOS 无 timeout）→ `references/local-backend.md`

### 3. 插件安装/更新/卸载
```bash
~/.hermes/skills/gaming/orzmc/scripts/plugin_manager.sh install essentialsx
~/.hermes/skills/gaming/orzmc/scripts/plugin_manager.sh install https://example.com/plugin.jar
~/.hermes/skills/gaming/orzmc/scripts/plugin_manager.sh update   # 全部更新
~/.hermes/skills/gaming/orzmc/scripts/plugin_manager.sh remove essentialsx.jar
```

**插件安装/升级机制（PaperMC 官方，两条路径要分清）**：
- 🆕 **新插件首次安装** → jar **直接放 `plugins/`**（重启时扫描加载；放 update/ 无效/非标准）
- 🔄 **已有插件升级** → 新 jar 放 `plugins/update/` → 重启时 PaperMC **按插件名（jar 内 plugin.yml 的 name）匹配**已加载插件并原子替换（update/ 自动清空）
- ✅ **update/ 按插件名匹配，不要求文件名一致**（2026-08-08 实测：plugins/OrzMC-1.0.15.jar + update/OrzMC-1.0.16-dev.jar 不同文件名，重启后替换成功、plugins/ 只剩新 jar、update/ 清空）
- ✅ **升级绝不动 plugins/ 下旧 jar**（官方文档原文：「do not remove or modify any plugins outside the update folder」）——**先删旧 jar 是错误做法**：删了旧 jar 后 update/ 匹配不到已加载插件 → 不应用 → 插件缺失（Exaroton 2026-08-08 实测翻车）
- ⚠️ Exaroton **运行中禁止写文件**，上传/升级必须先停服
- ✅ MCSM 端 plugins/update 实测可用（`mcsm_upload_update.py` 上传 → restart → 自动替换）
- ⚠️ **三端插件对齐必须对比 sha256**（文件名相同≠内容相同）；MCSM 运行中 jar 读取 500（锁定），对比用启动日志 `Enabling X vY` 行

### 3b. OrzMC 自定义插件升级（Hangar + update 机制）

```bash
# 1. 查最新版（Hangar API：dev=每日构建，pr=PR 构建）
curl -s "https://hangar.papermc.io/api/v1/projects/OrzMC/versions?limit=5" | jq -r '.result[] | .name'
# 2. 下载：curl -s ".../versions/<版本>" | jq -r '.downloads[].downloadUrl' → 校验
# 3. 新 jar 放 plugins/update/（按插件名 name=OrzMC 匹配，绝不动 plugins/ 旧 jar）→ 重启自动替换
```
⚠️ 三件套：① 新版本新增模板键 → jar 升级≠配置升级，三端 diff 后上传本地版覆盖；② 权限继承链须手动校正（`lp group member parent set default` / builder→member / admin→builder）；③ 完整流程见 `references/plugin-mgmt.md`

### 4. 三端配置对比与同步（scripts/cmp3/）

```bash
CMP=~/.hermes/skills/gaming/orzmc/scripts/cmp3
python3 $CMP/cmp3_configs.py <exa配置目录> <mcsm配置目录> <本地目录>   # 语义对比
python3 $CMP/cmp3_plugins_sha.py                                        # jar sha256 对齐
python3 $CMP/fetch3_ssh.py                                              # MCSM 侧配置 SSH 直读（面板 files API 慢/返回 0 文件时的兜底，tar 打包回传秒级）
python3 $CMP/fetch3_proxy.py                                            # 代理侧生效 Geyser 配置（proxy 模式自动替换实例内副本，direct 自动回退）
python3 $CMP/exa_apply_config.py && python3 $CMP/exa_verify_config.py   # Exaroton 改配置
python3 $CMP/mcsm_upload_update.py <jar名...>                           # MCSM 插件更新
```
**凭据约定**：全部从 `~/.hermes/.env` 读取（`mcsm_env.py` 共享模块），**禁止硬编码 API key**。

### 5. MCSM / Exaroton 日常操作

```bash
~/.hermes/skills/gaming/orzmc/scripts/adapters/mcsm.sh status|players|logs 50|start|stop|restart|command "list"
python3 $CMP/mcsm_delete.py /plugins/xxx.jar      # 删除（{"targets":[...]}）
python3 $CMP/mcsm_list_filter.py                  # 列目录（需 file_name 过滤）
python3 ~/.hermes/skills/gaming/orzmc/scripts/exa_sync_plugins.py --plan plan.json [--dry-run]
#   ↑ Exaroton 插件批量同步：上传 → 回读 sha256 比对 → 删旧 jar；服务器必须 OFFLINE；核心不能传只能面板选
```
> 端点表/认证/踩坑 → `references/mcsm-backend.md`、`references/exaroton-backend.md`

> 🔑 **API 密钥轮换（2026-10-19 实测）**：面板重新生成密钥后，**只改 `~/.hermes/.env` 的 `MCSM_LOCAL_API_KEY`**（32 位纯 hex），技能/脚本/仓库一律不存值（`secret_guard` 会把关）。
> - 验证鉴权：`GET /api/overview` 或 `GET /api/instance` 返回 200；**`/api/auth` 恒为 404（该端点不存在），别拿它判断 key 好坏**
> - 失败语义：`{"status":403,"data":"密钥不正确"}` → key 不对（或面板里新建后未保存/未启用）；用假 key 对照可确认报错确属鉴权而非网络
>
> 🔻 **`初始化失败，远程节点不存在！` = daemonId 与面板真实节点 uuid 不符**（2026-10-19 踩过：`.env` 写 `064118e0…`，面板实际是 `fbb3492c…`）
> ```bash
> # 查真实节点：返回字段是 uuid（不是 daemonId），本机节点备注 orzmc-local
> curl -s "https://mcs.{SERVER_NAME}.cn/api/service/remote_services_list?apikey=$MCSM_LOCAL_API_KEY"
> # 然后改 ~/.hermes/.env 的 MCSM_LOCAL_DAEMON_ID，再验一次 /api/instance
> ```
> ⚠️ 轮换 key 后若同时报「节点不存在」或面板极慢（TLS/首字节 3~8s、传输 30s 超时），先按限流纪律冷却 2~3 分钟再探测，别连打（MCSM 面板跑在 Windows + Cloudflare Tunnel 后面，负载高时会这样）。

### 6. 版本巡检（脚本可手动跑；定时已并入周巡检）

```bash
# 手动触发（2026-11-16 起跑在 Windows Hermes，Mac 副本已归档）
%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\python.exe %LOCALAPPDATA%\hermes\scripts\mc_version_check.py
```

- **调度**：Windows cron `orzmc-version-check`（`e9a7e185fbff`，周一 09:10，`deliver=origin`）；Mac 端旧 job `d81c8325fe8b` 已 paused
- **脚本逻辑**：**部署侧读本机实例 jar 文件名**（`mcsm_env.py` 本地适配器） + 21 插件各官方渠道最新版（Modrinth/Hangar/GitHub/metadata.luckperms.net/geysermc）（读 jar 内 plugin.yml/paper-plugin.yml）
- **输出**：对比表 + 状态（✅一致 / ⚠️有更新 / ➖本地构建 / ➖稳定 / ❓查询失败）+ 差异汇总
- **渠道映射**（CHANNEL dict）：OrzMC=hangar；EzShops/LoginSecurity/DeathChest/GetMeHome=**local**（本地打包，不提示升级）；BackOnDeath/Vault=**stable**（无渠道）；Essentials=github；Geyser-Spigot=geyser；CustomWorldHeight=**modrinth**（Hangar 无此插件，2026-08-15 修正）；**F3F4Perms=modrinth（slug: f3f4perms）；packetevents=modrinth（⚠️ CHANNEL key 必须小写 `packetevents`——jar 内 plugin.yml name 是小写，deploy dict 以 pname 为 key 会匹配不上大写 key）**；其余=modrinth
- **已知坑（10 条：build 号/license 映射/平台过滤/前缀漏报…）** → `references/version-check-pitfalls.md`

### 6b-2. ⚠️ MCSM 面板「账号级限流」与大文件投递（2026-09-19 实测血泪）

**限流事实**：面板 files API（list/download 签发/upload 签发）**账号级 ~3s/次**（管理员绕过）。高频脚本会把面板/daemon 拖到「签署 OK 但拉流 0 bytes、输出超时」的迟钝状态（实测：连续 30 分钟高频投递后，`outputlog`/`instance`/`files/list` 全部超时，`sign` 仍 200）。
- 对策：**一切 files 操作串行 + ≥3.5s 间隔**；大批量分阶段跑；出现迟钝立刻停手等几分钟，别重试风暴。
- 备用日志端点：`GET /api/protected_instance/outputlog?daemonId&uuid`（**绕开 daemon 拉流**，起服验证首选，比读 latest.log 稳）。

**URL 拼接坑（吃了 40 分钟）**：`cfg["url"].rstrip("/") + path` 时 **path 必须带前导 `/`**，否则拼成 `mcs.{SERVER_NAME}.cnapi/files/mkdir`（主机名非法）→ 报错却是 **`SSLEOFError: EOF occurred in violation of protocol`**（不是「域名不存在」！）→ 排查清单第一条：把 URL 打出来看斜杠。
```python
url = cfg["url"].rstrip("/") + "/" + path.lstrip("/") + "?" + urllib.parse.urlencode(params)
```
**写操作载荷位置**：`files/mkdir`、`files/copy`、`files/download_from_url` 的字段走 **JSON body**（仅 apikey/daemonId/uuid 在 query）；`files/upload` 的 `upload_dir` 走 **query**。写操作会偶发 SSL EOF/handshake timeout/BrokenPipe → **必须多重试 + 指数退避**（实测 6 次退避能穿过）。

**大文件别走 upload**：Cloudflare 对上传有 ~100s 上限 → 41MB Geyser 上传 `HTTPError 524`（**同一文件偶发成功**）；61MB 核心必超时。**大件一律用 daemon 侧直传**：
```python
post_json(cfg, "api/files/download_from_url", {"url": 官方直链(内容寻址更佳), "file_name": "/paper.jar"})
```
实测 paper 核心 61.5MB、Geyser 41MB 均一次成功（daemon 有外网），落盘后 `files/list` 看 size 即可初验。

**双实例交付次序**：先小件 upload → 再大件 URL 直传 → `files/list` 核 size → 启动（**启动后 update/ 被消费**，故 sha 回读要么启动前做、要么启动后按 `plugins/` 新名回读）。

### 6c. MC 定时任务清单（统一管理入口，2026-08-12 起）

| 任务 | job_id | 计划 | 脚本 | 模式 | 行为 |
|:--|:--|:--|:--|:--|:--|
| ~~MC 三端版本巡检~~ | ~~`0b4298821a86`~~ | ~~每日 10:00~~ | `~/.hermes/scripts/mc_version_check.py` | — | **已停用**（2026-11-06 确认不存在）；2026-11-16 起由 Windows 端 `orzmc-version-check`（`e9a7e185fbff`，周一 09:10）承担 |
| ~~三端配置审查~~ | ~~`ab06b886c39f`~~ | ~~每周一 9:15~~ | `~/.hermes/scripts/orzmc_config_audit.sh` | — | **已停用**；2026-11-16 起由 Windows 端 `orzmc-config-audit`（`836f72d6ad16`，周一 09:05）承担 |
| ~~orzmc MC 每周巡检（Mac 端）~~ | ~~`d81c8325fe8b`~~ | ~~每周一 9:00~~ | 五部分脚本（配置审查/插件质量/版本巡检/健康体检/连通性体检） | agent | **2026-11-16 老板决策 #4「立即停」→ 已 paused**；同轮 `89be8cc5d6a2`（技能双向同步）也已 paused。orzmc 运维整体迁 Windows，Mac 端只读 |
| ~~配置审查~~ | ~~`836f72d6ad16`~~（Windows） | ~~每周一 09:05~~ | `%LOCALAPPDATA%\hermes\scripts\orzmc_config_audit.py` | no_agent | **2026-11-17 paused → 20:13 删除 job 定义，并入 `orzmc-monday-report` 第一段**；脚本本身不变，仍可单独手动跑。原行为： 本机直读 99 件配置 vs Exaroton 79 件；报告落 `E:/orzmc/reports/` + 交付目录；proxy/direct 自动识别 |
| ~~版本巡检~~ | ~~`e9a7e185fbff`~~（Windows，2026-11-17 20:13 删除定义） | ~~每周一 09:10~~ | `%LOCALAPPDATA%\hermes\scripts\mc_version_check.py` | no_agent | **2026-11-17 paused → 删除，并入 `orzmc-monday-report` 第二段**。原行为： 部署侧读本机 jar 文件名，渠道侧查上游 release；Folia 只比非 ALPHA |
| **NetherNet advertise 同步**（现为 `orzmc-watchdog` 的一个段） | **`330d431ac384`**（~~`8582a0f31644`~~ 已于 2026-11-17 并入 watchdog 删除） | **每个 tick（5m）都跑**（原独立 job 为 15m；并入后 5m —— 只在 DoH 结果与现配置真不一致时才改写+重启 velocity，无变化静默，所以高频不会变吵） | `%LOCALAPPDATA%\hermes\scripts\nethernet_advertise_sync.py` | no_agent watchdog | DoH 查真 A 记录 → 与**当前入口**（`ENABLE_VELOCITY=true` 时为代理 `eagler/proxy/plugins/Geyser-Velocity/config.yml`，否则回落实例内 Geyser-Spigot）的 `advertise-addresses` 比对 → 变更时改写 + **`docker restart orzmc-velocity`**（有玩家在线只报警不重启；代理无 RCON，不能 `geyser reload`）；局域网条目取 `.env` 的 `LAN_HOST_IP`；无变化静默（日志 `%LOCALAPPDATA%\hermes\logs\nethernet-advertise-sync.log`） |
| **入口存活探针**（现为 `orzmc-watchdog` 的一个段） | **`330d431ac384`**（~~`f198dd2a7e95`~~ 已于 2026-11-17 并入 watchdog 删除） | 每 30 分钟（watchdog `tick%6==0`，即每 6 个 tick） | `%LOCALAPPDATA%\hermes\scripts\orzmc_entry_probe.py` | no_agent watchdog | 6 项：`orzmc-velocity`/`orzmc-caddy` 容器状态、Java 状态包 25565、NetherNet `GET /v1/join`、网页入口 443（TLS+SNI，期望 404 且 `Server: EaglercraftXServer`）；后端 RCON 已于 2026-11-19 关闭，按 `enable-rcon` 自动跳过不探测；**全绿静默**，故障仅在新增/集合变化/每 6 小时复述，恢复发一条 ✅。**只报警不重启**（老板要求入口处置人工拍板）；**退出码恒 0**（只有脚本自身崩溃才 2）；按「引擎 / 入口 / 后端」三层判定——Docker 不可用收敛成一条；**实例容器 stopped/missing 归「提示项」**（只写日志 `INFO 后端 x 实例=容器状态 stopped`，不进告警集/状态文件/复述，boss 明确要求实例刻意停止时别吵）；只有「实例 running 但 RCON 认证失败」才计故障。运行手册（分层判定/退出码/三态自测/cron 核对）→ `references/entry-monitoring.md`；日志 `%LOCALAPPDATA%\hermes\logs\orzmc-entry-probe.log` |
| ~~本机周巡检~~ | ~~`9d625c27db6d`~~（2026-11-17 20:13 删除定义） | ~~每周一 09:15~~ | `%LOCALAPPDATA%\hermes\scripts\orzmc_weekly_patrol.py` | no_agent | **2026-11-17 paused → 删除，并入 `orzmc-monday-report` 第三段**。原行为： 容器/三通道连通性/后端 TPS+人头/advertise 一致性/Paper·Folia·Geyser 版本 diff（Fill API + Modrinth）；**核心版本一律以实例目录 jar 文件名为准**——曾优先读 `logs/latest.log` 的 `Loading Paper 26.3-246@`，实例停着没重启时日志永远停在旧版，报出「Paper 落后 7 个 build」而磁盘上装的是 26.3-253（假告警）。日志只作兜底，`_ran` 记上次运行版本，与 jar 不一致时输出「上次运行 X，重启后才生效」/近 7 天 ERROR·WARN+Top/磁盘·世界体积·备份新鲜度 → 末尾「需要动手」清单；只读不重启 |

> ⚠️ **跨端查 cron 必须两端都看**：Windows 那台也跑着独立 Hermes（`gateway run` 进程 + `%LOCALAPPDATA%\hermes\cron\jobs.json`），Mac 端 `jobs.json` 里看不到它的任务。
> ⚠️ **停用/退役 job 必须回读状态才算停住**：① `pause` 调用返回成功**不等于**已暂停——回读 `jobs.json` 原始字段 `enabled: false` + `state: "paused"`（字段名**不是** `paused`，用 `j.get('paused')` 判断会把所有 job 都误报成 ACTIVE）；② 顺序是**先停 job、再归档/删除它的脚本**，否则 resume 时脚本已不在、或脚本还在却继续被旧 job 触发（技能双向同步这类 job 在「单一真源」后继续跑会直接把真源覆盖回去）；③ 两端都要核：一端以为停了、另一端还在跑，正是这类事故的常见形态；④ **cron 的写操作必须串行发，一次一个等结果**——同轮并行发多条 create/pause/update 会互相覆盖：`jobs.json` 是整份快照落盘（后写者拿走先写者的改动），实测出现过「三个 pause 全部回滚 + 新建的 job 从磁盘消失，而列表接口仍显示它在」的错位（列表读的是内存态）。所以每次写完都要**回读 `jobs.json` 确认「记录还在 + enabled/state 正确」**，只看工具返回的 `success:true` 不够；⑤ **同一台机器上的另一个会话同样是整份快照落盘**（实测：本会话新建的 `orzmc-monday-report` 被 20:04 那次 watchdog 合并写、以及 20:1x 的一次写连续吃掉两次，id 从 `686aa3ce8a13`→`3902dd9773a1`→`1404c6fc14f8`），所以**新建/改完 job 后隔几分钟再复读一次**；发现被吃掉先看 `created_at`/`origin` 判断是谁写的（`origin.platform=local` = 本机别的 CLI 会话），**不要在不知道对方在改什么的时候盲目重建第三次**，先跟对方（或老板）确认归属。
>
> ⚠️ **stub 转发脚本必须区分 `__main__` 与 import**：`scripts\*.py` 现在都是「转发到技能目录真源」的 19 行 stub；若 stub 在模块顶层无条件 `runpy.run_path(target, run_name="__main__")`，**任何 `import` 它的脚本都会被执行真源末尾的 `raise SystemExit(main())` 静默杀掉——症状是 rc=0 + stdout 空 + 无 stderr**（实测：`orzmc_weekly_patrol.py` import `orzmc_entry_probe` → 周巡检整段消失，聚合器仍显示「3/3 段完成」）。正确写法：`if __name__ == "__main__": runpy...` 否则用 `importlib.util.spec_from_file_location` 加载真源并 `globals().update(...)` 搬命名空间。**排查口诀：rc=0 但输出为空，先查 import 链，不要怀疑业务逻辑**；聚合器已把「rc=0 但解析无内容」计入段失败。判定「是不是对方做了重构」要读对方的脚本（如 `scripts\orzmc_watchdog.py` 的分段表）确认职责已被承接，**以新出现的 job/脚本为权威，别把自己删掉的 job 又加回来**（会造成双份触发）；要抓「谁在什么时候改的」就短采样：每 10s 取 `jobs.json` 的 md5 与 `"id"` 计数，变化时刻对照 `created_at` 即锁定写入者。

> ⚠️ **新建的周期 job 没有 `last_run_at` = 还没被真实验证过**：`enabled=True + state=scheduled` 只证明「已登记」。高频 job（5–30 分钟）几分钟内就能拿到 `last_run_at` 佐证；「每周/每月」job 必须等下一个窗口才会第一次真跑。所以汇报「迁移/交接完成」时把状态分三档说清——**已定义 / 已手动跑通 / 已自然触发**，别把前两档讲成第三档。
> ⚠️ **在 Windows 宿主上手动执行脚本的三条硬前提**（从 Mac 侧编排 Windows 任务时同样适用）：
> 1. **解释器**：Windows PATH 上的 `python` 可能是 0 字节的 Store stub（敲了才报错）—— 用 Hermes 自带 venv `%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\python.exe`（含 yaml/ruamel/requests），或干脆交 cron 托管执行。
> 2. **盘符/凭据**：映射盘（如指向 Mac SMB 共享的 `S:`）与 UNC 都需要 **SMB 凭据**；脚本内**优先写 UNC**（`\\<IP>\<共享名>\`，不依赖盘符映射）。写不进先读错误码：`WinError 1326 用户名或密码不正确` = 缺凭据（`cmdkey /list` 为空即证实），**与 Session 号无关**；凭据就绪后 `S:\` 与 UNC 都 `writable=True`。`WinError 5` 才是权限/路径问题。
> 3. **凭据**：Windows 侧 `.env` 只保证有它自己那几条键（Feishu/model）。用到 `MCSM_LOCAL_*` / `EXAROTON_*` / `RCON_PASSWORD` / `LAN_HOST_IP` 的脚本拷过去前先确认这些键存在，否则表现为「查询全空但不报错」。

- 本机（Windows）cron 现状（2026-11-17 20:15 实测 `jobs.json`，**共 3 条，全部 active**）：**active** —— `orzmc-watchdog` 每 5m（`330d431ac384`，2026-11-17 20:05 由 advertise 15m + 入口探针 30m + route-guard 10m + gateway-session-guard 5m **四条合并**，详见 2.6.14）、`orzmc-selfcheck` 每日 08:30（`ca0e89c8579d`）、`orzmc-monday-report` 周一 09:15（`1404c6fc14f8`）。原三条周一单任务（config-audit/version-check/weekly-patrol）的 **job 定义已于 20:13 全部删除**，脚本全留（聚合器正是调它们），要恢复单任务按脚本名重建即可，不必回滚历史 job。⚠️ 后三条的 pause 与 `orzmc-monday-report` 的创建**发生在 2026-11-17 20:02:43~45，由另一个 Feishu 会话完成**（`created_at`/`paused_at` 字段可查，origin=feishu），**不是 2.6.14 这轮 G1 的动作**；G1 全程只新建 watchdog + 删除上面四条，未读写这三条。回滚方式不是 `resume`（定义已删）：按脚本名重建三条 09:05/09:10/09:15 的 job，或先 `remove` 聚合器再重建。四个原脚本仍在 `%LOCALAPPDATA%\hermes\scripts\`，可单独手跑（watchdog 就是调它们）。
- **合并纪律（2026-11-17 定）**：只有「同节奏 + 同投递目标 + 互不依赖」的任务才合并出报告（周一周任务 3→1，实测串行 199s：配置 153s + 版本 32s + 巡检 14s）。**高频看守（advertise/route-guard/entry-probe）默认不合并**——它们分属「动作型」与「只报警型」，且各自有去重状态，合成一个会让一次异常同时吞掉三类监控；只有段间隔离成立（独立子进程 + 独立告警分节，见下条 G1）时才允许并成 watchdog。`gateway-session-guard` 更不并（救生员不能和要救的人绑一起）。聚合器 `scripts/orzmc_monday_report.py`：单段失败只标红该段、退出码恒 0。报告分两层——**正文只出浓缩摘要**（结论一览表 + 按优先级排的待办 + 运行态/版本/配置三张小表，约 1.2KB；老板要求「10 秒判断要不要动手」），三段完整输出落 `monday-full.md` 与三份 `<script>.txt`（目录 `E:/orzmc/reports/monday-YYYYMMDD/`）。新增异常类型记得同步 `build_todo()`，否则会静默不出现在待办里（正文结构、表格竖线清洗、数字重组的硬规则 → `references/entry-monitoring.md` §6）。 **2026-11-17 G1 补充**：老板批准把「高频看守」也合并时，合并的前提不是「节奏一致」，而是**段间隔离必须成立** —— `orzmc-watchdog` 用独立子进程 + 独立 try/except + 按段名分节聚合（`## entry-probe`）+ 任一段 exit≠0 只把该段标红，因此一次异常不会吞掉其余段；这条隔离是允许合并的前置条件，缺了它就该退回多条独立 job。
- ⚠️ **实例 `eventTask.autoStart=false` + `autoRestart=false`，但容器 policy 是 unless-stopped**：断电重启后代理会自己起来、Paper/Folia 不会 → 玩家进不去。2026-11-15 老板明确要求**不要**开自动拉起，靠探针报警 + 人工处置
- 两者脚本均读 `~/.hermes/.env` 凭据；cron 精简 PATH 实测通过（2026-08-12 全量体检）
- 脚本维护记录：audit 脚本 `Bearer ***` bug 已修（2026-08-12）；version_check Geyser build 号比较已修（2026-08-12）

## Pitfalls（跨后端通用）

### 🖥️ Windows 迁移专项坑（2026-11-16，迁移当场踩到的）

- 🔴 **Windows 上 `python` 是 Microsoft Store 的 0 字节 stub**：手敲 `python x.py` 直接失败（`where python` 指向 `WindowsApps\python.exe`，长度 0）。一律用 Hermes venv 解释器 `%LOCALAPPDATA%\hermes\hermes-agent\venv\Scripts\python.exe`（3.11.16，yaml/ruamel/requests 齐备），或交给 cron 托管执行。
- 🔴 **SMB 写不进先看错误码；凭据按「登录会话」生效**：`WinError 1326 用户名或密码不正确` = 该会话没有可用 SMB 凭据（`cmdkey /list` 在该会话为空即证实）；`WinError 5` 才是权限/路径问题。⚠️ **同一台机器不同会话结论可能不同**：2026-11-16 实测 Hermes cron（**Session 1**，老板交互登录会话）对 `S:\` 与 `\\{LAN_IP}\下载` 均 `writable=True`，而 `ssh win`（**Session 0**）同一时刻仍报 1326 → `deliver_dir()` 回退到 `E:/orzmc/deliver`。**所以交付验证必须由 cron（Session 1）跑**，在 SSH 里测出「不可写」不能代表 cron 不可写（反之亦然）。曾把这条误判成「Session 0 导致写不进、与凭据无关」，绕了半天 —— 正确顺序：先看错误码 → 再确认是哪个会话 → 再定结论。
- 🔴 **交付工具用 `deliver_file.py`（技能 `scripts/`）**：`python deliver_file.py <源文件> [--as 名] [--json]` → 自动走 `deliver_dir()`（`S:\` → UNC → 本机），打印两侧 sha256 与一致性。cron 里没有参数位，包一层 `_deliver_one.py` 之类的一次性脚本再挂 job。
- 🔴 **pathlib 的 `/` 优先级高于 `%`**：`p / "_probe_%s.txt" % os.getpid()` 等价于 `(p / "_probe_%s.txt") % int` → `TypeError: unsupported operand type(s) for %: 'WindowsPath' and 'int'`，会把**可写目录误报成不可写**。写 `p / ("_probe_%s.txt" % os.getpid())`。
- 🔴 **改别人的 Python 脚本前先确认文件编码，禁止 `read_text(utf-8, errors="replace")` 再写回**：非 UTF-8（GBK）脚本里的中文会被替换成 `U+FFFD`，写回后字符串字面量直接断裂（`SyntaxError: unterminated string literal`），一次搞坏 6 个脚本。正确姿势：`data.decode("utf-8", errors="surrogateescape")` → 改 → `text.encode("utf-8", errors="surrogateescape")`，非 UTF-8 字节原样往返。纯 ASCII 的插入（如 guard 代码块）可以直接在**字节流**上做，不碰解码。
- 🔴 **UTF-8 guard 必须落在「模块级」，且 `import sys` 要在模块级**：按「连续 import/注释/空行」扫头部插 guard 时，遇到跨多行的模块 docstring 会停在其**内部** → guard 成了字符串内容（外加一句假的 `import sys`）→ 模块级 `sys.stdout.reconfigure` 抛 `NameError` → 被自己的 `except Exception: pass` **静默吞掉** → 等于没加 guard。用 `ast` 取 docstring/`__future__` 的 `end_lineno` 定位插入点，并用 ast 复核「模块级有 import sys + 模块级 try 含 reconfigure」。**别手搓插入器** —— 直接跑 `scripts/fix_utf8_guard.py --dir <脚本目录>`（字节安全、幂等；`--check` 只体检，退出码 1=有不合格的；生成后会自动 py_compile）。
- 🔴 **告警脚本必须做「注入假故障」自测，光看平时静默不算通过**：入口探针因为上面的 guard 失效，平时全绿毫无异常，但**一旦真要告警**，`print("🔴 …")` 在 cp936 下抛 `UnicodeEncodeError` → cron 交付给老板的是一屏 traceback 而不是告警内容（等于告警通道一直是坏的）。自测法：复制脚本、注入一条假 fail（`PROBE_SELFTEST=1`），确认 stdout 出现预期的红字告警且 stderr 为空；随后删临时脚本 + 清 state 文件再跑生产版确认静默。
- 🔴 **`exa_file._load_env()` 原先硬编码 `~/.hermes/.env`** → Windows 上是 `C:\Users\WangA\.hermes\.env`（不存在）→ 报 **FileNotFoundError**，看起来像网络/权限问题。已改为「`%LOCALAPPDATA%\hermes\.env` → `~/.hermes/.env` 逐个尝试，都不在就返回空 dict」。
- 🔴 **Windows PowerShell 5.1 读非 ASCII 的 `.ps1` 要 UTF-8 BOM**：无 BOM 的 UTF-8 中文脚本按 GBK 解码，引号会被撑坏，报 `字符串缺少终止符`／`foreach 缺少变量名`，报错行号与真因无关。→ 含中文的 `.ps1` 一律 `utf-8-sig` 写盘；另外 **PS 的反引号是转义符不是续行符**，多行命令别用行尾 `` ` ``（会串行解析炸掉）。
- 🔴 **PowerShell 5.1 读 UTF-8（含中文）的 JSON / 清单会按 GBK 解码**：`Get-Content ... -Raw | ConvertFrom-Json` 报 `ConvertFrom-Json : 无效的 JSON ...`（还夹乱码），文件本身完全正常。修法二选一：`Get-Content -Encoding UTF8 -Raw` 再解析，或**直接把文件 `scp` 回 Mac 用 Python 解析**（跨端解析优先放在 Mac 侧）。反向同理：PS 的 `Set-Content -Encoding UTF8` 会**加 BOM**，Mac 端拿它做集合比较/逐行匹配前必须先剥 BOM。
- 🔴 **Windows 侧 Mihomo/Clash TUN 会劫持「发往自身 LAN IP」的连接**：探 `192.168.0.33:25565` 全线超时，但 `127.0.0.1:25565` 秒通。→ `.env` 里 `ORZMC_LAN_HOST=127.0.0.1`（局域网条目/广告地址仍用 `LAN_HOST_IP=192.168.0.33`，两者用途不同别混）。
- 🟡 **`mc_version_check.py` 的 `PARSE_PAPERMC` 路径要跨平台解析**：写死 `~/.hermes/skills/...` 在 Windows 上不存在 → `Paper核心 解析失败`。已抽 `_skill_scripts_dir()` 先试 `%LOCALAPPDATA%\hermes\skills...`。
- 🔴 **`subprocess.run(..., text=True)` 在 Windows 上默认按 cp936 解码子进程输出**：gradle / java / 中文日志里出现非 GBK 字节 → 读线程 `UnicodeDecodeError` → `r.stdout/r.stderr` 变 **None** → 下游 `TypeError: 'NoneType' object is not subscriptable`（报错位置远离真因）。→ 所有抓子进程输出的地方必须显式 `encoding="utf-8", errors="replace"`，并在拼接前 `(r.stdout or "")`。
- 🔴 **在 Windows 跑构建/带环境变量的命令：落盘 `.bat` 再 `cmd /c <文件>`，别在 SSH 一行里拼**：`.bat` 里 `set "JAVA_HOME=E:\...\jdk25"` 与 `call gradlew.bat <args>` **各占一行**。两个会伪装成「环境没装」的坑：① `cmd` 里写 `set VAR=value && ...` 时**尾随空格会算进变量值** → gradlew 报 `JAVA_HOME is set to an invalid directory: E:\...\jdk25 `（路径其实完全正确）；② `set "VAR=value"` 塞进 `ssh win "cmd /c \"...\""` 的多层引号会被 bash/SSH 吃掉 → 变成 `JAVA_HOME is not set`。看到这两种报错先怀疑拼法，不要去重装 JDK。**按项目跑单测/构建的坑（多模块 `--tests` 需模块限定、POSIX-only 断言）→ `references/java-test-pitfalls.md`**。
- 🔴 **Windows 上 `subprocess` 起 `.bat` 不能用相对名**：`cmd=["gradlew.bat"]` + `cwd=插件目录` → `FileNotFoundError [WinError 2]`（`CreateProcess` 不查子进程 cwd，只查 PATH）→ 必须传**绝对路径**（`<repo>/gradlew.bat`，兜底本机 `E:/orzmc/tools/gradle/bin/gradle.bat`）。
- 🔴 **`hermes cron create --script X.py` 只认 `%LOCALAPPDATA%\hermes\scripts\X.py`**，不查技能目录（直接报 `Script file not found: ...\hermes\scripts\X.py`）。真源留在技能目录时，主机侧放一个 5 行转发 stub（`sys.path.insert` 技能 scripts + `runpy.run_path(..., run_name="__main__")`），避免两份副本漂移。
- 🔴 **`schtasks /query` 的输出是 UTF-16LE，在 git-bash 里 `grep` 会报 `binary file matches` 或返回 0 行**（看起来像「没有任何匹配的计划任务」，极易误判成「这台机器没建过任务」）。查计划任务现状改用 PowerShell 结构化输出：`powershell.exe -NoProfile -Command "Get-ScheduledTask | Where-Object {$_.TaskName -match 'orzmc|backup'} | Select TaskName,State"`；确实要用 schtasks 就先 `iconv -f UTF-16LE -t UTF-8`。
- 🔴 **Docker Desktop(WSL2) 发布的端口不出现在 Windows `netstat` / `Get-NetTCPConnection`**（监听在网络命名空间/VM 内）：`netstat -ano | grep 25565` 空 = 假阳性。判定入口存活一律用 **TCP 实连 `127.0.0.1:<port>`**；且本机连自己的 LAN IP 会被 TUN 劫持超时（见上条），不能拿它当「端口没开」。
- 🔴 **`orzmc_paths.redact()` 会把四段版本号当公网 IP 打码**：`SCore-5.26.11.15` / `EE 3.26.11.15` 落盘后变成 `<公网IP>`，报告里的版本基线直接被毁。凡落盘内容含 `x.y.z.w` 形态的版本串，脱敏前先把已知版本标记成占位符、脱敏后再还原（`orzmc_selfcheck.py` 的 `_mask_versions()` 就是这层保护）。
- 🟢 **`gradle.bat` 硬依赖 `JAVA_HOME` —— 全局已配，仍然显式注入**：Windows 用户级全局已设 `JAVA_HOME=E:\orzmc\tools\jdk25` 且用户 `Path` 含 `%JAVA_HOME%\bin`（注册表 `HKCU\Environment` 回读确认），`java` 可直接跑了。但**已在运行的进程（Hermes 网关、长驻 cron 宿主）不会自动继承**新写的用户级变量，必须重启才拿到 → 脚本给子进程显式注入 `JAVA_HOME` 永远比赌继承更稳。自检第 7 项「全局是否配了」读**注册表真值**、不看本进程 `os.environ`，否则会因没继承而误报全局没配。**判定 Path 里有没有 JDK bin 必须「原文 + 手工展开」两条腿走**：注册表存的是变量原文 `%JAVA_HOME%\bin`，本进程没继承 `JAVA_HOME` 时 `os.path.expandvars` 展不开，只比展开后的绝对路径 `E:\orzmc\tools\jdk25\bin` 会恒假红（2.6.12 修过）→ 现口径三路任一命中即 ✅：(a) 原文含 `%JAVA_HOME%\bin`；(b) 用注册表 JAVA_HOME 真值手工展开后含 `jdk25\bin`；(c) PATH 里能直接找到 `java.exe`。Path 缺这条只记 ℹ️ 不判 ❌；真 ❌ 只留给「`JAVA_HOME` 已设但 `${JAVA_HOME}\bin\java.exe` 不存在」。


- ⚠️ **手写 RCON 客户端必须循环解析「所有完整包」，不能只取首包**：一次 `recv` 里常同时带回 auth 应答 + 命令应答，只读一包会拿到上一个响应；同时返回体长度要读满（截到 80 字会把 `tps` 这类长行截残 → 字段解析恒失败，误判成「服务器没响应」）。有 `scripts/rcon.py` 就别手搓。同理：`docker ps --format '{{.Ports}}'` 会把 `0.0.0.0:` 与 `[::]:` 各报一遍，展示/比对前先去重。**`docker ps --format` 的输出每行带 `\r`**：`docker ps --format '{{.Names}}' | while read c; do docker inspect "$c" …; done` 里 `"$c"` 是 `orzmc-caddy\r` → inspect 报 not found → 循环**静默返回空**，看起来像「没有容器引用该路径/该端口」（假阴性）；要拼命令先 `tr -d '\r'`，要批量取 label 就用单命令 `docker ps -a --format '{{.Names}}{{"\t"}}{{.Label "com.docker.compose.project.config_files"}}'`。
- ⚠️ **核心版本串只写在 `logs/latest.log` 头部**（`Loading Paper 26.3-246@...`）——服务跑久后日志尾部 grep 不到它，别因此判「版本读不出来」；读前 n 行再剥 ANSI。
- ⚠️ **版本比对端点会漂移，别用记忆里的 URL**：`api.papermc.io/v2` 已 sunset（返回非 JSON / exit 23）→ 用 `https://fill.papermc.io/v3/projects/{paper,folia,velocity}/versions/<ver>/builds` 并带 `User-Agent`；Geyser 不发 GitHub release（`api.github.com/repos/GeyserMC/Geyser/releases/latest` 恒 404）→ 走 `https://api.modrinth.com/v2/project/geyser/version?loaders=["velocity"]`。单源失败只在报告里标「查询失败」，不能让整份巡检挂掉。
- ⚠️ **探针/巡检脚本的输出纪律（老板定）**：全绿**静默**（空输出），故障靠状态文件去重（同一故障集合只在新增/变化或复述窗口到点时才说话，默认 6 小时），恢复发一条 ✅；**一律只报警、不自动重启容器/实例**——入口故障由老板人工拍板。写这类脚本时把 `REALERT_SECONDS` 和 `STATE` 文件路径做成常量，别在告警分支里塞重启命令。

- ⚠️ **no_agent 告警脚本：检出故障 ≠ 任务失败，退出码必须 0**：`orzmc_entry_probe.py` 最初在发现故障时 `return 1`，cron 把它记成 `last_status=error / Script exited with code 1` 并累加 `failure_streak`（实测连累到 4），真出故障时反而看不出「任务本身坏了」。正确做法：业务故障只走 stdout 告警 + 退出码 0；只有脚本自身异常才 `return 2`（`guarded_main()` 包一层 traceback）。
- ⚠️ **探针必须区分「入口挂」和「后端没起」两层**：Docker 引擎本身超时/不可用时，端口探测必然 6–7 项全红 —— 应当收敛成一条「Docker 引擎不可用，容器与端口无法核实」，别刷一屏；实例容器 `missing/stopped` 时 RCON 必然拒绝连接，应报「后端 xxx 实例 容器状态 stopped（面板手动启动）」，而不是把 RCON 的 ConnectionRefused 当成入口故障（2026-11-15 20:03 Docker Desktop 整体停机、22:13 恢复，代理自动回来、MC 实例按 `autoStart=false` 没起，正是这个场景）。
- ⚠️ **ViaVersion `block-versions` 安全基线（2026-11-10 定）**：ViaVersion 5.12.x 启动会警告「The Vanilla protocol of Minecraft 1.20.5-1.21.4 is easily exploitable」。正确解法 = 在 `plugins/ViaVersion/config.yml` 把 `block-versions: []` 改为块列表，4 个区间必须齐（缺一段等于没堵）：
  ```yaml
  block-versions:
    - "1.20.5-1.20.6"
    - "1.21-1.21.1"
    - "1.21.2-1.21.3"
    - "1.21.4"
  ```
  改完需**重启**（`/viaversion reload` 在装了 ProtocolLib 的服会踢人）。代价：这些版本的 Java 客户端会被踢（默认提示 `You are using an unsupported Minecraft version!`），**基岩不受影响**（走 Geyser 通道）。默认 `logging.log-blocked-joins: false`，要留痕得显式改 true。已落地：测试服 paper/folia + Exaroton；**国内服 MCSM 因 apikey 403 待老板手动**。
- ⚠️ **Geyser 报 `You are using an outdated version of ViaVersion` 时不要跟着升**：ViaVersion 目前最新只有 `5.12.3-SNAPSHOT`（beta，无正式版），按「只跟 release」纪律保持 **5.12.2**，该提示属正常噪音（测试服 folia 实测）。
- ⚠️ **PowerShell 脚本经 SSH 下发时禁止非 ASCII 字符（含 `…` `→` 中文标点）**：Windows 默认 GBK 读 UTF-8 文件 → 字符串引号失衡，报一串 `表达式或语句中包含意外的标记`，根因看起来毫无关联。脚本一律纯 ASCII + 单引号包双引号。
- ⚠️ **`ssh win "powershell -NoProfile -File X.ps1"` 会被执行策略拦下**（`未对文件 X.ps1 进行数字签名…无法在当前系统上运行`）→ 必须显式加 `-ExecutionPolicy Bypass`：`powershell -NoProfile -ExecutionPolicy Bypass -File E:/orzmc/tmp/x.ps1`。同一个坑也解释了「为什么不该把多行 PowerShell 塞进 `ssh win "powershell -Command ..."`」——`$u` / `$_.Name` 会被本地 bash 先吃掉，落盘 `.ps1` 再 `-File` 是唯一稳妥写法。
- ⚠️ **运行中容器的 bind mount jar 无法覆盖**（2026-11-16 实测）：代理容器 `orzmc-velocity` 持有 `E:/orzmc/eagler/proxy/plugins/Geyser-Velocity.jar`，`scp` 覆盖报 `dest open ... Failure`（文件被 JVM 锁）。`docker cp` 也写同一宿主文件，同样失败。**正解 = `docker stop <容器>` → 覆盖 → `docker start`**（无玩家时窗口 1–2 分钟；改前先备份旧 jar 到 `E:/orzmc/tmp/`）。实例内的 jar 因为实例本身是停止态，scp 直接覆盖即可。
- ⚠️ **插件备份必须「移出目录」（Move），不能只 Copy**：旧 jar 留在 `plugins/` 会与新 jar 同时被加载（Geyser/LuckPerms 这类同 plugin 名双份尤其危险，还可能让启动日志出现两份版本号）。正确顺序：`Move-Item` 到 `upgrade-bak-<日期>/` → 再投新版 → 校验目录里只剩新版。
- ⚠️ **Modrinth 只给 `sha512`/`sha1`，没有 `sha256`**：按 `hashes["sha256"]` 取会得 `None`，随后比对必然「不一致」，容易误判为下载损坏。用 API 返回的全部 hash 逐项 `hashlib.new(alg, data)` 比对。
- ⚠️ **「自建服务访问慢」先按入口分诊，不要从容器查起**：同一时刻同机并排测四条路径（源站 `127.0.0.1:<发布端口>` / 局域网 IP / 公网域名 / 同机另一条直连入口如 18443），量级差在哪段就归因在哪段。源站毫秒级 + 域名秒级 = 慢在入口（通配橙云隧道 / 代理绕行），此时查容器日志、CPU、DB 索引全是白费；静态资源命中 `cf-cache-status: HIT` 仍慢，也证明延迟在链路而非源站处理。**新建任何子域后先 DoH 查它解析到哪**（家宽 IP = 直连；Cloudflare 边缘 IP + CNAME 含 `cfargotunnel.com` = 被 `*.{SERVER_NAME}.cn` 通配橙云静默接进隧道）；回答「还有哪些服务受影响」= 把 Caddyfile site 块 + 容器宿主端口 + DNS 子域三份并起来逐个 DoH 归类——**是不是受害者只看 DNS 记录，与业务是什么无关**。量法/修法/验收 → `references/public-ingress-clash-tun.md` §9。
- ⚠️ **对比两端差异时，必须把同一探测也打到「已知可用」的一侧作对照**；两端探测结果一致 → 该维度**不是**根因，立刻换维度。只拿失败端的数据就下结论会把排查带向错误方向（例：把「没配 TLS 证书」当成基岩连不上的根因，实际两端探测行为一致，真因是 `advertise-addresses` 下发了错地址）。定性前先问一句：这个差异在「能用的那端」存在吗？
- ⚠️ **Geyser 切 `both` 模式：`advertise-addresses` 的端口必须等于 `webrtc-port`**（不是 `port`）。写错会变成「RakNet 老客户端能进、NetherNet 新客户端卡住」的半瘫，且两端日志都不报错 —— 只看日志永远找不到。
- ⚠️ **服务器主机跑着 Clash/代理（TUN 模式）时，`advertise-addresses` 只能写数字公网 IP**：系统 DNS 被劫持成 `198.18.x` 假 IP（连指定公共 DNS 也一样），`stun-discovery` 探到的是**代理出口地址**（实测返回代理机 IP + 随机源端口）→ 域名写法与留空都会把玩家导到死地址。自检：主机上 `Resolve-DnsName <域名>` 必须回真公网 IP、`curl -s https://ifconfig.me` 必须等于该域名 A 记录；任一不符 → 写 IP。动态 IP 变化交给 `nethernet_advertise_sync.py` 守护。

- ⚠️ **Git 不在任何 PATH 里（HKCU 与 HKLM Path 均无 git 目录），但本机确实有 Git**：`C:\Program Files\Git`（现只剩空壳 cmd/ 与 etc/）与 Hermes 自带 `%LOCALAPPDATA%\hermes\git\{cmd,bin}\git.exe` 都在 —— 交互 bash 里 `which git` 命中的 `hermes\git\mingw64\bin\git.EXE` 只是 MSYS 自己的 PATH。服务/SSH 会话按 PATH 找必然 `FileNotFoundError`，脚本里一律用 `resolve_git()` 四级兜底（`shutil.which` → `C:\Program Files\Git\cmd\git.exe` → `%LOCALAPPDATA%\hermes\git\cmd\git.exe` → `…\bin\git.exe`），禁止裸写 `["git", …]`。
- ⚠️ **`[Environment]::SetEnvironmentVariable('Path', $v, 'User')` 会把 REG_EXPAND_SZ 降级成 REG_SZ**（实测：写后 `GetValueKind` = `String`，`%JAVA_HOME%` 从此不展开，Path 变成死字面量）。要保留变量形式必须 `Set-ItemProperty -Path HKCU:\Environment -Name Path -Value $v -Type ExpandString`，改完回读三样确认：kind = `ExpandString`、原文含 `%JAVA_HOME%\bin`、`ExpandEnvironmentVariables(原文)` = 期望绝对路径。
- ⚠️ **配置重建升级（OrzMC/EzShops 等）备份必须隔离目录**：旧配置备份与"拉新配置"严禁写同一目录——拉新强制用 `*_new/` 独立目录（2026-08-09 实测教训：复用同一 outdir 导致旧备份被新默认配置覆盖，迁移依据永久丢失；/tmp 无 Time Machine/APFS 快照兜底）。备份后**立即打印内容摘要（key: value）核对**，并二次复制到 `~/backups/`；迁移前先 diff 新旧确认依据完整
- ⚠️ **破坏性升级（删配置重建）前**：先 `skill_view` 查技能已有脚本/端点结论（mcsm_delete.py 用 `{"targets":[...]}`、MCSM 重启用 `api/protected_instance/restart`、Exaroton 上传用 PUT+UA），不凭记忆手写；备份/迁移清单先列给用户确认（plan-first）
- ⚠️ **官网（OrzMCSite）改完配置怎么发布**：`E:/orzmc/src/OrzMC/site` → 提交并 `git push origin main` 即触发 `Publish Web Page` + `pages-build-deployment`（静态站 `https://orzmc.{SERVER_NAME}.cn`）；**子模块常是 detached HEAD，先 `git checkout main` 再 `git rebase origin/main` 后推**。父仓 `OrzMC/OrzMC` 的 `main` 有分支保护（必过 `verify` 状态检查、禁直推）→ 必须 `git checkout -b <branch>` + `git push -u` + `gh pr create --head <branch>`，`gh pr checks` 变 pass 后 `gh pr merge --squash --delete-branch`，最后本地 `git reset --hard origin/main`。**两个后续坑**：① squash 合并后本地 `main` 与远端 **diverged**（本地那笔内容已进远端但 hash 不同）→ `git switch main` fast-forward 失败属正常，先 `git fetch` 再重置，别当冲突处理；② `git reset --hard` / `rmdir /s /q` 在 Hermes 会弹审批、老板常不在跟前 → 先说明再执行，或走非破坏替代（`git branch -m main local-merged-<n>` + `git switch -c main origin/main` 效果等同且旧 commit 留作备份）；③ **判断 PR 是否真合并/推送是否真落地不看命令回显**（可被截成 `1 lines output`），用 `gh pr view <n> --json state,mergeCommit`、`git ls-remote origin main` 或 `git log --oneline -1` 回读。验证发布生效：抓线上页面 grep 旧端口为 0，或看 server_status JSON 里的 `web_port`。
- ⚠️ **测试服 RCON 已关闭（2026-11-19）**：`enable-rcon=false`、`rcon.password` 清空、实例不再发布 25575/25576；控制台操作改用面板 API（`protected_instance/stop|open`）+ 读 `logs/latest.log`，探针已自动跳过 RCON，勿再按老流程用 RCON 发命令；`grim_kick_ban.py` 因此不可用。
- ⚠️ **改 MCSM 实例的 `docker.ports` / `server.properties` 后必须重启 daemon 才重载**：`InstanceConfig/<uuid>.json` 被 daemon 常驻内存持有，**只改磁盘文件不生效**（面板/`docker ps` 里仍是旧映射，看起来像「改了没用」）；正确顺序 = 停实例 → 改 `server.properties`（服务端只在启动时读它）→ 改 `InstanceConfig/*.json` → `docker restart orzmc-mcsmanager-daemon` → 面板 `protected_instance/open` 起服，再逐项回读端口。改前把两份文件各 `.bak` 到 `tmp/<改动名>-<日期>/`。**关掉一个被探针依赖的服务（如 RCON）时，同轮把探针改成按配置自检**（读 `enable-rcon` 决定是否探测），否则连通性检查会长期误报「后端未启动」。
- ⚠️ **Modrinth 多 loader 项目取 jar 不能取 `files[0]`**：Chunky 这类项目同一版本号下并存 fabric/neoforge/forge/paper/folia/sponge/bukkit 多个 version 条目，`project/{slug}/version` 返回按时间排序，首条常是 Fabric —— 照抄 `files[0]` 会把 Fabric 版插件装到 Paper 上。正确姿势：先按 `version.loaders` 里含 `paper`（或 `folia`）筛出目标 version 条目，再取它的 file；Chunky-Paper 的 loaders 就是 `['folia','paper']`（同一 jar 双平台）。装完用 jar 内 `plugin.yml`/`paper-plugin.yml` 的 `folia-supported: true` 二次确认。
- ⚠️ 下载必须校验 sha256，防止损坏 jar（Modrinth 只给 sha512/sha1，按返回的全部 hash 逐项比）
- ⚠️ **备份分层**：插件升级无需备份 jar；服务器核心 jar 升级需备份旧 jar 回滚（upgrade 自动做）；**世界/玩家/LuckPerms H2/配置必须定期备份**
- ⚠️ 服务器运行中不要替换 jar（先 stop 再升级）
- ⚠️ 插件必须匹配 MC 版本（Modrinth API 用 `game_versions` 过滤）
- ⚠️ eula.txt 不写 `eula=true` 服务器拒绝启动
- ⚠️ Java 25 只能跑 26.x；老版本需要旧 JDK
- ⚠️ **经 `ssh win` 跑 PowerShell：复杂逻辑一律写成 `.ps1` 文件上传再 `-File` 执行**，不要把多行脚本塞进 `ssh win "powershell -Command ..."`——双层引号会把 `$var` 吃成空（报 `foreach 缺少变量名` / `=E:/... 无法识别`），排查十分钟才发现是转义。**`.ps1` 只写纯 ASCII**：含中文的脚本以 UTF-8 无 BOM 传过去，Windows PowerShell 5.1 按 GBK 解码 → 乱码 → ParserError（要中文就存 UTF-8 BOM，或改在 Mac 侧读文件）。
- ⚠️ macOS bash 3.2：`$var` 后接全角字符（如 `（`）会报 unbound variable，必须写 `${var}`
- ⚠️ MCSM 有玩家在线时严禁 stop/restart/command/文件操作（先查 `info.currentPlayers`）
- ⚠️ **MCSM 升级跨大版本（如 26.1→26.2）**：世界数据首次启动自动转换（日志 `Starting upgrade for world`），确认无玩家时段操作

## 验证
- **交付链路验收（写老板 S: 盘 / 任何远端共享）= 真实文件 + 落点回读 + 两侧 sha256 一致**，三步缺一不可：
  `scripts/deliver_selftest.py` 把真实报告按 `orzmc_paths.deliver_dir()` 落盘并打印两侧哈希（日志 `E:/orzmc/reports/deliver-selftest.log`）；`scripts/deliver_probe.py` 只做**目录级探活**。
  ⚠️ **目录可写 ≠ 交付成功**：探活脚本自己要是有 bug（如 `p / "x_%s" % pid` 的优先级错）会把可写目录报成不可写，反过来也可能假阳性 → 结论必须用真实文件哈希闭环。
- `curl -s localhost:25565` 返回 Minecraft 协议字节 = 服务器在线
- 日志出现 `Done (Xs)! For help, type "help"` = 启动成功
- `ls plugins/` 看到 jar = 插件已安装
- 三端对齐：插件 sha256 一致 + 版本号一致
