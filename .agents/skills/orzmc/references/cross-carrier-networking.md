# 跨网互联：电信服务器 × 联通/移动玩家（延迟高/被拒绝）

> 🛑 **状态更新（2026-10-19）：两台腾讯云中转机已销毁，frps 中转链路当前不在运行。**
> - 已销毁：正式机 `{CVM_IP}`（上海 CVM 2C2G）+ 试用机 `{CVM_IP}`（上海轻量 3M）
> - 本文的**方案分析与工具链仍然有效**（OrzMCProxy 仓库的 frps/frpc 配置、PROXY protocol 透传、relay-monitor 监控、容量测算都可复用），但「生产部署流程」一节的 IP/主机信息属历史记录
> - **重建中转时**：装 frps → 安全组放行 TCP 7000/25565-25566 + UDP 19132 → Windows `install-frp.ps1 -Role frpc` 改 serverAddr → verify-tunnel + bedrock_ping → 三处 proxy-protocol 联动（paper-global.yml / Geyser haproxy / frpc v2）
> - ⚠️ 生产端当前玩家入口方式**待确认并回填本节**（直连家宽+DDNS？新中转？Cloudflare Tunnel？）

> **触发场景**：玩家报延迟高、连不上、"Connection throttled"、"Timed out"、掉线；服务器部署在单一运营商网络（如电信家宽），联通/移动玩家受害。2026-08-13 沉淀。
>
> **部署资产（完整工具链在 `OrzMC/proxy` 子模块 = OrzMCProxy 仓库，2026-08-15 纳入 monorepo；本地实验 100% 闭环）**：
> - 一键安装：`scripts/install-frp.sh`（Linux/macOS + systemd/launchd）、`scripts/install-frp.ps1`（Windows + 计划任务自愈）
> - 验证：`scripts/verify-tunnel.sh`（TCP+MC 握手）、`scripts/health-check.sh`、`scripts/bedrock_ping.py`（基岩入口，无需真客户端）、`scripts/mc_login.py`（完整协议登录验证：Handshake→Login Start→压缩协议→Login Success/白名单拒绝，可选手动 PROXY v2 头，实测 Paper 26.2）、**`scripts/relay-monitor.sh`（🆕 外部隧道监控：formal/temp 双档——正式档 Java 查 TCP+后端存活，临时档中转+直连双通道完整 MC ping/RakNet；状态转换才输出告警/恢复、稳定静默，适配 cron no_agent 看门狗；首次运行出基线；退出码恒 0）**
> - 配置模板：`configs/frps.toml.example`、`configs/frpc.toml.example`（含 `[proxies.transport] proxyProtocolVersion = "v2"`）、**`configs/frpc.production.toml.example`（生产双代理模板：Java TCP 25565 v2 透传 + 基岩 UDP 19132 中转，2026-08-14 真实联调验证后沉淀）**
> - 文档：`docs/architecture.md`（延迟链路/成本）、`docs/setup-guide.md`（部署+灰度+回滚）、`docs/manual-apply-windows.md`（MCSM 面板不可用时 2 文件手动改法+重启）、`docs/troubleshooting.md`
> - 档位选择：临时（一天活动，不开 proxy-protocol，`connection-throttle: 0`）/ 正式（proxy-protocol 真实 IP 透传，三处联动）

## 根因：三大运营商骨干网独立，跨网走"独木桥"

电信/联通/移动骨干网**各自独立、互不相通**，跨网流量必须经过少数国家级互联互通节点（北京/上海/广州/郑州等）。这些节点带宽远小于网内带宽，晚高峰（19:00–23:00）严重拥塞：

| 场景 | 典型 RTT | 丢包率 |
|:--|:--|:--|
| 同网（电信→电信） | 10–30ms | ≈0 |
| 跨网（联通→电信） | 60–200ms+ | 1–10% |
| 跨网（移动→电信） | 100–300ms+ | 5–30% |

**移动最严重**：跨网互联带宽最少 + 大量 CGNAT（运营商级 NAT，玩家共享出口 IP）+ 路由可能绕路。

## "被主动拒绝"的四个机制

1. **Paper `connection-throttle`（默认 4000ms）——最典型的"主动拒绝"**
   限制**同一 IP** 4 秒内只能建立一次连接（防登录洪水）。CGNAT 下多个玩家共享同一公网出口 IP → 服务器误判为攻击 → 日志出现 `Connection throttled! Please wait 4000 ms`，直接拒连。
2. **TCP 握手丢包**：跨网拥塞时 SYN 丢失 → 客户端重传多次后放弃 → 表现为"连接超时/连接被拒绝"。
3. **登录超时被踢**：`server.properties` 的 `connection-timeout` 默认 30 秒；跨网拥塞时「加密握手+正版认证+区块加载」超过 30 秒 → 服务端踢 `Timed out`。
4. **OS SYN backlog 耗尽**：慢速跨网握手占满半连接队列 → 内核直接丢弃新 SYN。

## 解法（按性价比）

| 方案 | 说明 | 效果 |
|:--|:--|:--|
| 多线 BGP 机房/云主机 | 阿里云/腾讯云轻量均为三网直连 | ⭐⭐⭐ 根治 |
| **中转机（家里服务器首选）** | 三线轻量云做中转（FRP / Tailscale / iptables 转发），玩家连中转 IP，中转再连家里服务器。**MCSM 电信家宽 50M 上行场景即此类** | ⭐⭐⭐ 根治级 |
| 玩家加速器 | 玩家自己走优化线路 | ⭐⭐ |
| 配置治标 | `connection-timeout` 调 60–120s；`connection-throttle` 谨慎放宽（有被刷风险）；Paper 1.19.3+ packet-limiter 放宽 | ⭐ 缓解 |

## 同源问题解法：PROXY protocol 真实 IP 透传（2026-08-13 本地实测 ✅）

中转后所有玩家同源 IP（中转机 IP）会误伤 connection-throttle 等按 IP 功能。解法 = PROXY protocol 透传真实 IP：

**配置（三处联动）**：
1. frpc 每个代理（frp ≥0.60 语法）：`[proxies.transport]` 子表配 `proxyProtocolVersion = "v2"`——⚠️ **不在 proxies 顶层**（顶层报 `unknown field "proxyProtocolVersion"`）
2. Paper：`config/paper-global.yml` → `proxies.proxy-protocol: true`——⚠️ **不是 spigot.yml 的 bungeecord**（bungeecord 模式解析 BungeeCord 转发数据 `\00IP\00UUID`，不认 PROXY 头；两者是独立机制）
3. Geyser（基岩）：`plugins/Geyser-Spigot/config.yml` java 段 `use-haproxy-protocol: true`——否则基岩玩家挂

**实测验证（本地测试服 paper-26.2-111 + frp v0.70.1）**：
- 手写 PROXY v2 头伪造 IP（203.0.113.5:40000）直连 → 服务器日志如实显示 `/203.0.113.5:40000`，IP+端口透传 100% 工作
- 开 proxy-protocol 后**直连（无 PROXY 头）被服务器静默拒绝/超时**（官方行为：normal clients 无法连接）→ 直连地址从此不可用
- frp 隧道全链路：握手→Login Start→白名单检查完整走通

**档位选择**：
| 档位 | 配置 | 适用 |
|:--|:--|:--|
| 临时（一天活动） | 不开 proxy-protocol，Paper `connection-throttle: 0` | 快速零风险，接受同源 IP |
| 正式（长期） | 开 proxy-protocol（frpc + paper-global.yml + Geyser haproxy） | 真实 IP，防误伤 |

**实验坑备注**：Paper 26.2 = MC 1.21.11 = 协议 **776**；1.21.11 的 Login Start（serverbound/minecraft:hello）含 **playerUUID** 字段。**⚠️ 1.21.1 (767) 的 Login Start 也有 playerUUID**（2026-08-14 查 minecraft-data 确认）——写离线登录测试脚本统一发 `name + UUID(16B)`；只发 name 必报 `Failed to decode packet 'serverbound/minecraft:hello'`（曾误判为 ViaVersion/proxy 问题，实为脚本格式 bug）。

**⚠️ 登录脚本两大坑（2026-08-14 真实联调踩坑，写协议脚本必看）**：
1. **必须先发 Handshake**（packet 0x00：protocolVersion + serverHost + serverPort + nextState=2），然后才 Login Start——直接发 Login Start 会被服务器按握手状态解析（0x00=Handshake）导致字段错乱静默断连（EOF，无日志）。mineflayer 源码 `setProtocol.js` 确认流程。
2. **压缩协议格式**：服务器发 Set Compression (0x03) 后，**所有包改为「帧格式」**：`VarInt(帧总长) + VarInt(解压后数据长度) + 数据`（数据 = zlib 压缩包 或 dataLength=0 时原始包）。⚠️ 帧长度 varint 与 dataLength varint 是**两个不同字段**，缺帧长度会被服务器报 `Badly compressed packet` / 解压失败。zlib 数据长度 = 帧长 - dataLength varint 字节数，用 zlib.decompress 全量解压。minecraft-protocol pipeline = Splitter(帧) → Decompressor(dataLength+zlib) → Serializer。参考 `~/OrzMC/proxy/scripts/mc_login.py`。

**真实公网联调（2026-08-14 ✅ 全链路验证通过，腾讯云轻量试用机 {CVM_IP} 上海）**：
- ⚠️ **云厂商安全组/防火墙默认只放 22/80/443/3389**——frp 控制端口 7000 + 游戏端口 25565 必须手动放行，否则 frpc 报 `session shutdown`（TUN 干扰是假象！）或 `i/o timeout`；放行后秒连
- 验证矩阵全绿：frpc login success → verify-tunnel TCP 通（⚠️ **2026-08-14 纠错：当时 MC ping 失败≠proxy-protocol 证据——verify-tunnel.sh 有历史 bug：Status Request 包 ID 写成 0x01（实为 0x00，0x01 是 Ping Request 需 8B payload 缺了必断连），已修复；proxy-protocol 生效的硬证据是 mc_login 完整登录链路 + 直连无头挂起**）→ mc_login 经中转 Login Success ✅ → 白名单外用户被 OrzMC 拒绝（`/{HOME_IP}:52021` = **frpc 自动透传玩家真实公网 IP**，铁证）→ 直连无头挂起（proxy-protocol 拦截）✅
- ⚠️ **verify-tunnel 修复后的正确行为（2026-08-14 本地双模式验收实测）**：正式档下**经中转 MC ping 成功**（frpc 自动加 PROXY v2 头，服务器正常响应，能看到版本/在线人数）——不再是「ping 失败」；只有**直连无头**才 timed out（proxy-protocol 拦截）。「经中转 ping 失败」是旧脚本 bug 的假象。**relay-monitor formal 档的正确判定**：Java 25565 用 backend_alive（TCP 连上 2s 无 EOF/RST = 后端存活）——正式档下此检测返回 OK，直连 MC ping 不可用作正式档监控指标
- 手写 PROXY 头 + 伪造 IP 直连 → 服务器日志显示伪造 IP:端口（Paper 侧解析验证）；**经 frpc 隧道时客户端必须 plain（frpc 自动加头，手动头会被当垃圾数据转发导致协议错乱）**
- 完整客户端验证：mineflayer（真实协议栈）经中转登录成功，服务器日志 `test[/{HOME_IP}:51669] logged in`

**ViaVersion 兼容性（2026-08-14 补测 ✅）**：proxy-protocol 模式下 767/768/770/775/776 全协议版本经隧道登录流程完整（ViaVersion 5.11.0 翻译正常）——老版本玩家无影响。

**Geyser 基岩入口验证法（2026-08-14 补测 ✅）**：无需基岩客户端——RakNet Unconnected Ping（UDP 19132，packet 0x01 + magic）→ 收 Pong(0x1c)+MOTD = Geyser 存活且 Geyser→Java 连接（haproxy 头）被 Paper 接受。工具：`~/OrzMC/proxy/scripts/bedrock_ping.py`。正式档配置生效标志：Geyser 启动日志 WARN「Geyser is configured to use proxy protocol when connecting to the Java server」。

**基岩 UDP 中转（2026-08-14 真机实测 ✅ 完整可行）**：
- frpc 加 `type = "udp"` proxy（localPort/remotePort 19132）；frps `allowPorts` 须加 19132（多行格式 `{ start = 19132, end = 19132 }`）；腾讯云防火墙放行 **UDP** 19132
- Geyser 配置 ⚠️ **只改 java 段（约 191 行）`use-haproxy-protocol: true`；bedrock 段（约 218 行）必须保持 false**——frp UDP 代理不支持 PROXY protocol，bedrock 段若开 true 基岩客户端连接会被拒（两个同名配置项极易改错，patch 时勿 replace_all）
- UDP 隧道稳定性：10/10 RakNet ping 成功（北京→上海中转 ~91ms）；45s 静默后自动恢复（frp UDP 会话超时无碍，RakNet 保活维持）
- 真机验证：基岩客户端连 `中转IP:19132` 正常进服游玩（LoginSecurity 对 Geyser 玩家自动跳过——微软 XUID 认证优于离线密码，属预期；Java 离线玩家仍受保护）
- ⚠️ 代价确认：UDP 中转**无真实 IP 透传**（Geyser 看到 127.0.0.1），基岩玩家 IP 级管控失效（XUID 管控不受影响）
- **卡顿排查教训（2026-08-14）**：玩家报「阶段性卡顿」先排除客户端/环境因素（手机低电量模式降频会周期性卡顿！充电后恢复），再归因隧道（UDP over TCP 队头阻塞等）——勿凭特征直接下结论，须对照实验验证

## 正式档连接拓扑与带宽容量（2026-08-14 定案）

**连接拓扑（正式档 = 全玩家走中转）**：
- **Java 玩家只有中转机一条路**——proxy-protocol 开启后直连家里 IP（无 PROXY 头）被服务器静默拒绝（官方行为），普通客户端不带头 → 直连失效。**代价≈0**：中转机同城（上海），电信玩家多一跳仅 +5-10ms（10-30ms→15-40ms 体感无差），联通/移动玩家 60-300ms→10-50ms 大赚
- **基岩玩家双通道**：直连家里 IP:19132（UDP）或走中转 19132 均可——proxy-protocol 只管 Geyser→Java 本地 TCP（Geyser 自带 haproxy 头），与玩家怎么连 Geyser 无关
- 若想保留电信玩家直连只有临时档（无真实 IP 透传），正式档不做

**中转机带宽容量**（MC 流量以服务器→玩家下行为主，恰好打在中转机出网方向）：
| 人数 | 体验 | 人均下行 |
|:--|:--|:--|
| ≤15 | ✅ 舒适 | ~200 Kbps |
| 20-30 | ⚠️ 日常流畅，高峰偶卡 | ~100-150 Kbps |
| 50 | ❌ 必卡（人均仅 60 Kbps） | — |

- 3M 舒适线 ≈ 15 人、硬顶 ≈ 30 人；50 人×8h ≈ 18GB ≈ 平均 5Mbps > 3M
- **50 人活动正日 → 按量 CVM（100Mbps 峰值，~18 元/天 + 流量 0.8 元/GB ≈ 14.4 元）**；试用机 3M 仅联调/压测/≤15 人小规模；切换 = frpc 配置只改 serverAddr 一行（5 分钟）
- 多中转机分摊（2×3M ≈ 30 人）性价比不如单台 100M 按量机

**⚠️ 链路瓶颈 = 家宽上行，中转机 100M 峰值不浪费（2026-08-14 容量规划沉淀）**：
- 链路：`玩家 ←→ 中转机(公网带宽) ←→ 家宽上行 50M ←→ 家里服务器`——MC 下行流量恰好打在家宽上行这一环，**家宽 50M 是链路最窄处**，中转机带宽超过 50M 的部分出网方向用不到
- **按量 CVM 100M 峰值 ≠ 浪费**：按流量计费（0.8 元/GB），峰值只是能力上限，实际跑 ~50M 就只付 50M 的钱；还能扛玩家→服务器的突发入站（指令/聊天/区块请求）。**固定带宽 100M 月付才是浪费**（为永远用不到的 50M 付月费）
- **家宽 50M 上行容量**：15 人≈3M(6%)、30 人≈4.5M(9%)、50 人≈10M(20% 舒适)、100 人≈20M(40% 仍可行)——**带宽不是 50 人活动瓶颈**（瓶颈在 MCSM 单服并发/插件/内存）；⚠️ 区块加载/传送瞬间峰值 2-3 倍均值（100 人峰值 20-30M 贴近 50M），活动前必须压测
- **规格推荐**：日常 ≤30 人 → 轻量 2C2G 6M（长期月付）；50 人活动正日 → 按量 CVM 100M 峰值（≈32 元/天，关机不收费）；100 人双服 → 必须按量 100M。**2C2G 所有场景都够**（frps 纯转发走内核，CPU/内存非瓶颈，瓶颈只有带宽）

**生产部署流程（2026-08-14 已交付，顺序铁律：先隧道通再改服）**：
0. **中转机运维入口**：
   - **正式机（已上线 2026-08-14）**：腾讯 CVM **{CVM_IP}**（2C2G/20G，上海），SSH ubuntu 密码登录；frps v0.70.1 systemd `frps@default` 已部署运行；配置 `/etc/orzmcproxy/frps-default.toml`（auth.token 从文件读，勿写死；allowPorts=[25565-25566, 19132]）；日志 `/var/log/orzmcproxy/frps-default.log`；云防火墙已放行 TCP 7000/25565/25566 + UDP 19132
   - **试用机**：{CVM_IP}（上海轻量 3M，仅联调/压测/≤15 人小规模）
   - ⚠️ **CVM 部署坑（2026-08-14 实测）**：腾讯云访问 GitHub 限速 ~200B/s（13MB 要 7 小时）→ **本地下载 frp linux_amd64 后 scp 上传**（本地 6 秒）；scp 路径参数勿带引号（会生成带引号字面量的文件名 `"file"`）；SSH 密码含反引号等特殊字符时**勿内联进远程命令**（远程 shell 会命令替换），用 expect 交互处理 sudo 密码提示
1. 中转机 frps 部署 + 云防火墙放行 TCP 7000/25565 + UDP 19132（allowPorts 含 25565+19132）
2. Windows 宿主机 `install-frp.ps1 -Role frpc` → 用 `frpc.production.toml.example` 全量替换配置（改 token + serverAddr={CVM_IP}）→ `Restart-ScheduledTask`
3. verify-tunnel 25565 + bedrock_ping 19132 确认隧道通
4. 老板按 `docs/manual-apply-windows.md` 改 2 文件（paper-global.yml proxy-protocol true + Geyser java 段 haproxy true，bedrock 段不动）→ 等玩家全下线重启（停机 3-5 分钟）
5. 验证矩阵：经中转登录 + 真实 IP + 基岩 ping + 直连对照
6. 群内公告玩家改连中转机 IP（{CVM_IP}）
7. relay-monitor.sh 接 cron（每 5 分钟，no_agent 看门狗）——frpc 上线后才有意义，之前接会持续误报 FAIL

**正式机验收记录（2026-08-14 ✅ 本地测试服实测全绿）**：relay-monitor formal 3/3 OK（frps 7000 / Java 后端存活 / 基岩 PONG）；verify-tunnel 经中转完整响应 Paper 26.2；mineflayer 完整登录 `test[/{HOME_IP}:64232] logged in`（真实 IP 透传铁证）；直连无头 timed out（拦截正常）——与试用机结论一致，正式机可直接生产

**隧道外部监控（2026-08-14 新增 `scripts/relay-monitor.sh`，生产上线后必须接 cron）**：
- **两档模式**：`--mode formal`（正式档：proxy-protocol 开，Java 25565 只能做 TCP 连通+后端存活 EOF 检测——MC ping 被服务器拒属预期不可用）+ `--mode temp --direct-host 家宽IP`（临时档：中转+直连双通道都做完整 MC ping + RakNet 探测，玩家两条路都通才算健康）
- **输出契约（适配 Hermes cron no_agent 看门狗）**：状态翻转才输出（`🔴 ALERT`/`🟢 RECOVERY`/`🆕 首次基线`），稳定静默（空 stdout=cron 不投递不刷屏）；退出码恒 0，健康性靠 stdout 表达
- **检查项**：frps 控制口 7000 TCP + Java 入口（按档位）+ 基岩 19132 RakNet（真实端到端 Geyser→Paper，与 proxy-protocol 无关两档通用）
- 状态文件 `/tmp/orzmcproxy-relay.state`（`--state-file` 可换）；cron 接线示例：每 5 分钟跑一次，`no_agent=true`，stdout 非空即投递
- **正式档判定细节**：frps 活着但 frpc 断开时，25565 TCP 能连但立即 EOF → `backend_alive` 判 FAIL（区别于 frps 全挂的 connect refused）；基岩 UDP 无响应 = frpc 未连或防火墙没放行 UDP

**本地双模式验收（2026-08-14 实测完成 ✅ relay-monitor.sh 双档判定 100% 正确）**：
- **临时档**（proxy-protocol off + 无头 frpc）：`--mode temp --direct-host 127.0.0.1` 全绿 5/5——frps 7000 / Java 中转 ping / Java 直连 ping / 基岩直连 PONG / 基岩中转 PONG（UDP 隧道端到端）；verify-tunnel + bedrock_ping 独立复核一致
- **正式档**（proxy-protocol on + v2 头 frpc）：`--mode formal` 全绿 3/3——frps 7000 / Java 后端存活 / 基岩中转 PONG；Geyser 日志出现「Geyser is configured to use proxy protocol」= haproxy 生效标志；直连无头 timed out（拦截 ✅）；mineflayer 完整登录 `test[/{HOME_IP}:61853] logged in`（真实公网 IP 透传铁证）
- **验收恢复**：改回 proxy-protocol false ×2 + 重启，verify-tunnel 直连恢复响应 = 原状复原（测前基线/测后恢复范式）

## 诊断

- 服务端日志 grep：`Connection throttled` / `Timed out` / `Lost connection`
- 玩家端对服务器 IP 做 ping/mtr，跨网 vs 同网对比 RTT 与丢包率，确认是否互联节点拥塞
- proxy-protocol 相关：frpc 日志 `unknown field` = 配置位置错；服务器日志无记录 + 客户端超时 = PROXY 头没到/没开 proxy-protocol
