# NetherNet（基岩新传输层）迁移知识库

> 状态（2026-11-02 最新）：**测试服 paper/folia = `both`（19134/19135）+ 写死公网 IP**（宿主机跑 Clash，域名/STUN 都不可用，见 §5.5）；**国内服生产 = `both`（`webrtc-port: 19134`）+ `advertise-addresses: ["<域名>:19134"]`，实测双通道均通**；海外服 Exaroton 仍 `raknet` 待切
> 来源：Geyser 官方 blog `/blog/preparing-for-nethernet`、官方 setup 文档 `geysermc.org/wiki/geyser/setup/`、**Geyser-Spigot 2.12.0-b1265 jar 反编译实证**（`GeyserConfig$BedrockConfig` / `$SignalingConfig$*`）+ **2.12.1（build 1280）实装 config.yml 字段核对**

## 1. 是什么 / 为什么必须处理

- **NetherNet** = Mojang 为基岩版引入的新传输层：**WebRTC（UDP）承载游戏流量 + HTTP/HTTPS 信令（TCP）做连接协商**。Mojang 自 **Bedrock 26.40** 起逐步推送。
- **2026-10-27 起**，基岩客户端**不再走 RakNet** → 未切换的服务器基岩玩家进不来。
- Geyser **build ≥1237** 已支持 NetherNet，但**默认仍是 RakNet**（`transport: raknet`），必须手动开启，否则启动日志会打：
  `WARNING! NetherNet support is NOT enabled. Players will not be able to connect to your server, starting October 27th`

## 2. 机制差异（这是迁移真正的坑）

> 🔴 **「域名入口必须 HTTPS」不成立（版本相关，别照抄旧结论）**
> 实测（Geyser 2.12.1 build 1280 + Bedrock 26.60）：`signaling.builtin.https.certificate` 留空时，客户端用**域名**（如 `dev.example.com:19132`）照样能进服，只弹一次「信任此服务器」；对测试服与生产端的 19132 做 `openssl s_client -servername <域名>`，**两端行为完全一致**（TCP 建连 → ClientHello → 服务端直接 EOF），`/v1/join` 字段与 `POST /v1/join/<nonce>` 的 401 也一致。
> → **TLS 不是两端可用性差异的分水岭**；Geyser 1265 / 更早客户端上曾观测到「域名强制 TLS、明文信令被 FIN」，属版本相关行为。
> 结论：**没证书不是连不上的原因**；配 `builtin.https` 的收益 = 免掉 TOFU 弹窗。基岩进不来先查 **UDP 转发 / `advertise-addresses` / `transport`** 三处（§5.4）。

| 维度 | RakNet（旧） | NetherNet（新） |
|:--|:--|:--|
| 连接流程 | 客户端 UDP 直连 | ① **TCP** 发 HTTP(S) 问「怎么连」→ ② 服务端回 WebRTC 参数 → ③ 游戏流量走 **UDP/WebRTC** |
| 端口 | 只需 UDP 19132 | **同一端口同时占 TCP + UDP** |
| 服务器列表 MOTD / 人数 | RakNet 查询 | **也走信令**（只开 UDP → 列表都刷不出来） |
| 兼容模式 `both` | — | 需**另开一个 UDP**（`webrtc-port`），两种传输不能共用同一 UDP 端口 |
| 公网转发 | 只转 UDP | **TCP + UDP 都要转** |
| 首次进服 | 无感 | 用 IP / 非 HTTPS 域名 → 弹「信任此服务器?」(trust on first use) |

- MOTD 透传：自带信令会把客户端最初 ping 的地址回传给 Java 端做 MOTD passthrough。
- 若 Geyser 与 Java 共用端口（`clone-remote-port: true`）→ **自带信令无法用**（TCP 被 Java 占了），Geyser 会**自动回退到外部信令 Warden**，控制台打印玩家应使用的地址。

## 3. 配置结构（以 **2.12.1 / build 1280 实装 config.yml** 为准）

> ⚠️ **改配置前先对照本节键名**：2.12.0 反编译出的 `signaling.port`、`signaling.builtin.advertise-addresses`、`bedrock.raknet-port` 在 2.12.1 里**已不是这些位置**——写错位置 Geyser 静默忽略，表现为「配置改了但不生效」。

```yaml
bedrock:
  address: 0.0.0.0
  port: 19132                 # 玩家连的端口；NetherNet 下同号还要占 TCP（信令）
  webrtc-port: 19134          # NetherNet/WebRTC 的 UDP；0 = 与上面同端口（单端口模式）
  transport: both             # raknet(默认) | nethernet | both；改动需重启
  clone-remote-port: false    # true 与内置信令不兼容（TCP 被 Java 占）

  signaling:
    mode: builtin             # builtin | hybrid | nxs | none
    # 对外公布地址；支持「域名/IP[:端口]」，缺省端口=NetherNet UDP 端口。留空则用本机地址 + stun-discovery
    advertise-addresses:
      ["mc.example.com:19134"]
    stun-discovery: true      # 设置了 advertise-addresses 时不生效
    builtin:
      https:                  # 同端口同时提供 HTTPS；配了玩家就看不到「信任此服务器」
        certificate: ''       # PEM 链 或 PKCS12（PKCS12 时 private-key 留空）
        private-key: ''
        password: ''          # 可用 file:/path/to/password
    nxs:                      # 外部信令（Warden 等），mode=nxs/hybrid 或内置信令起不来时用
      token: ''
      endpoint: https://agent.warden.cloud
```

**端口语义速查（回答「是不是单端口模式」就靠这张表）**：

| 模式 | 配置 | 实际占用 | 老客户端(<26.40) |
|:--|:--|:--|:--|
| RakNet（默认/生产现状） | `transport: raknet` | UDP port | ✅ |
| **both（测试服）** | `transport: both` + `webrtc-port: <另一 UDP>` | **TCP+UDP port** + **UDP webrtc-port** | ✅ |
| **nethernet 单端口** | `transport: nethernet` + `webrtc-port: 0` | **TCP+UDP 同一个 port** | ❌ |

> 「单端口」= TCP 与 UDP 同号（信令跑在 TCP 上），**不是只开 UDP**；只放 UDP → 服务器列表都刷不出来。

**系统属性覆盖**（优先级高于 config，托管方可直接写启动命令）：
`-DgeyserTransport=nethernet`、`-DgeyserUdpPort`、`-DgeyserSignalingPort`、`-DgeyserWebrtcPort`、`-DgeyserSignalingMode=nxs`

> ⚠️ **「单端口」的唯一判定标准 = `webrtc-port: 0`**（注释原文 `0 means the same port as above`）。此时 NetherNet 与 RakNet 共用 `bedrock.port`，但**信令 TCP 仍占该端口** → 「单端口」= TCP+UDP 同号，只转 UDP 时玩家列表都刷不出来。
> `webrtc-port` 填了另一个端口（如 19134）= `both` 双端口模式：UDP 19132(RakNet) + UDP 19134(WebRTC) + **TCP 19132(信令)**，共 3 条放行规则。测试服即此模式（paper 19134 / folia 19135）。
> 2026-11-02 核对：`transport: both` 的日志形态为 `Started Geyser on UDP port 19132` + `Built-in signaling started on http://0.0.0.0:19132, with NetherNet on UDP port 19134`；单端口模式日志里的 webrtc 端口号会与 bedrock 端口相同。
> ⚠️ **`both` 模式下 `advertise-addresses` 的端口必须写 `webrtc-port`**（如 `[<域名>:19134]`）；错写成 `port`(19132) 会出现「RakNet 老客户端能进、NetherNet 新客户端卡住」的半瘫，且两端日志都无报错 —— 切 both 时最易漏的一步。

## 4. 三种落地方案

| 方案 | 配置 | 需要开放的端口 | 优点 | 缺点 |
|:--|:--|:--|:--|:--|
| **A 最小** | `transport: nethernet` | TCP+UDP 同端口 | 最简单、端口最少 | 老客户端（<26.40）彻底进不来；26.40 的 MOTD/人数可能不显示 |
| **B 过渡（推荐）** | `transport: both` + `webrtc-port: <另一 UDP>` | TCP+UDP 主端口 + 一个 UDP webrtc | 新老客户端都能进 | 多开一个 UDP 端口 |
| **C 免 TCP/免证书** | 外部信令（Warden，免费、自带 HTTPS）| **不用开 TCP** | 不动路由器、无证书 | 玩家要用 Warden 显示的地址+端口（或注册自定义域名）；依赖第三方服务 |

> 26.60 发布、玩家全部更新后可收敛为 A，并关掉 RakNet 端口。

### HTTPS 三种做法
1. `signaling.builtin.https` 直接指向证书（Geyser 同端口提供 HTTPS）
2. 信令端口前挂反向代理（Nginx/Caddy）做 TLS
3. 外部信令服务（Warden 自带 HTTPS）
—— **不配 HTTPS 也能用（含域名入口）**：客户端回退明文 HTTP，首连弹一次「信任此服务器」即可进服（2.12.1 + 26.60 实测）。配 HTTPS 的唯一收益 = **不弹这个框**。⚠️ 别把「卡加载延迟」归因于缺证书，该症状更常见于 UDP 未转发或 `advertise-addresses` 下发错地址（§5.4）。

## 5. 本环境适配要点（OrzMC 现状）

### 5.0 三端现状速查（2026-11-02，一页看完）

| 端点 | transport | 端口（玩家填） | `advertise-addresses` | 外部实测 |
|:--|:--|:--|:--|:--|
| 测试服 paper | `both` | 19132 → webrtc **19134** | `["<公网IP>:19134"]`（写死，因宿主 Clash） | RakNet ✅ / NetherNet ✅ |
| 测试服 folia | `both` | 19132（宿主 19133）→ webrtc **19135** | `["<公网IP>:19135"]` | RakNet ✅ / NetherNet ✅ |
| 国内服生产 | `both` | 19132 → webrtc **19134** | `["<域名>:19134"]` | RakNet 39~66ms ✅ / NetherNet 80~116ms ✅ |
| 海外服 Exaroton | `nethernet`（平台强制） | **Java `{SERVER_NAME}.exaroton.me:39742` / 基岩 同域名:19132** | 平台环境变量注入（手改无效） | **已启动实测 2026-11-09**：`:19132/tcp` → 308 重定向到 `https://<域名>/v1/join` → 200（protocol 2225/26.60, transportLayer 2）；Java :39742 ✅。⚠️ 用 :39742 测基岩必失败（那是 Java 端口），详见 §5.6 |

**每次都要问的 3 个问题**：① `transport` 是啥（`nethernet` 时 RakNet 无应答属正常）② UDP 端口实际放行了哪些（TCP 通 ≠ 玩家能玩；`nethernet` 单端口只认 19132）③ `advertise-addresses` 下发的地址客户端真的能到吗（宿主机有代理时优先怀疑这里）。

> ⚠️ **上表是 2026-11-02 的双实例直连形态，已被 ADR-036 取代（2026-11-12 起）**：现在唯一入口是容器 **`orzmc-velocity`**（Velocity 4.3.1 + Geyser-Velocity + EaglerXServer），宿主只发布 **25565/tcp + 19132/tcp + 19132/udp**；paper/folia 变成后端，**不再发布游戏端口、也不再承担基岩**。后端保留 Geyser-Spigot 是**设计如此、不用处理**：Geyser 自检到 Velocity 会 `Enabling Geyser-Spigot` → 立刻 `Disabling Geyser-Spigot` 自我停用（2026-11-15 实测，两后端均如此），代理模式用 Geyser-Velocity、非代理模式用 Geyser-Spigot，同一套配置两种拓扑都能跑。**基岩定案：全量 `transport: nethernet` 单端口**（`webrtc-port: 0` → 信令与媒体都走 19132），**不再考虑 `both`**（已明确：不为 26.60 以下老客户端保留 RakNet）。advertise 的唯一权威文件 = `E:/orzmc/eagler/proxy/plugins/Geyser-Velocity/config.yml`。部署文档 `E:/OrzMCDeploy/docs/eaglercraft-deploy.md`、切回/回滚记录 `E:/orzmc/eagler/CUTOVER-20261112.md`。

### 5.1 已落地（2026-10-19，本地测试服 dev.{SERVER_NAME}.cn，both 模式）

| 项 | paper（716c2f…） | folia（8A932D…） |
|:--|:--|:--|
| `transport` | `both` ✅ | `both` ✅ |
| `bedrock.port` | 19132 | 19132（容器内） |
| `webrtc-port` | 19134 | 19135 |
| `signaling.advertise-addresses`（2.12.1 键位） | `["<公网IP>:19134"]` | `["<公网IP>:19135"]` |
| Docker 发布 | UDP 19132 + TCP 19132 + UDP 19134 | UDP 19132 + TCP 19132 + UDP 19135（宿主侧 19133/19135） |
| 玩家填的地址 | `dev.{SERVER_NAME}.cn:19132` | `dev.{SERVER_NAME}.cn:19133` |

启动日志确认（两个实例均出现，且**不再**出现 `NetherNet support is NOT enabled`）：

```
Started Geyser on 0.0.0.0:19132
Started built-in signaling server on http://0.0.0.0:19132
NetherNet WebRTC listening on UDP 19134 (or 19135 for folia)
```

> ⚠️ **`advertise-addresses` 必须写「玩家可达的公网地址」（容器内监听 172.x，webrtc 端口经 Docker NAT）。** 2.12.1 起**支持域名**（含端口，如 `["dev.example.com:19134"]`），域名在信令启动时解析，解析失败信令就不启动；留空则用本机地址 + `stun-discovery`（跨 NAT 时公布的很可能是错误 endpoint，表现为列表能刷、进不去）。
> ⚠️ 公网 IP 动态（kmdns.net）→ 用 `scripts/nethernet_advertise_sync.py`（技能脚本目录，运行时副本在 `%LOCALAPPDATA%\hermes\scripts\`）自动跟进：DoH 查 A 记录 → 与配置比对 → 变更时改写并 `geyser reload`（只重载 Geyser，不踢 Java 玩家）。已挂 cron `orzmc-nethernet-advertise-sync`（no_agent，每 15 分钟，包装脚本 `nethernet_advertise_cron.py`，无变化时静默）。

> ✅ **2026-10-20 全链路验证通过（纯 IP 直连）**：`GET /v1/join` → 200，`POST /v1/join/<id>` → 200（返回 SDP answer），随后 UDP 19134 上 DTLS/WebRTC 建立，玩家成功进服。说明 both 模式、advertise-addresses、Docker NAT、路由器端口转发、防火墙全部正确。

> ✅ **域名入口可用（实证）**：`dev.{SERVER_NAME}.cn:19132` 在 `builtin.https` 留空时实连正常（首连弹一次「信任此服务器」）。想免掉弹窗再配 HTTPS，**不是可用性前提**（见 §2 更正）。

### 5.2 端口放行核对表（2026-10-20 已全部放通，保留作逐项核对）

| 层 | 现状 | 需要 |
|:--|:--|:--|
| Windows 防火墙 | 仅 `Bedrock Geyser 19132/19133 UDP` 两条入站规则 | 加 **TCP 19132、TCP 19133、UDP 19134、UDP 19135**（需管理员；本机脚本 `%LOCALAPPDATA%\hermes\scripts\bedrock_nethernet_ports.ps1`，管理员 PowerShell 运行） |
| 路由器端口转发 | 只转发 UDP 19132/19133（TCP 25565 已转发，证明 TCP 转发功能可用） | 加 **TCP 19132、TCP 19133、UDP 19134、UDP 19135** → `192.168.0.33` |
| 外部验证 | check-host 4 节点对 TCP 19132/19133 全部 `Connection timed out` | 两层都放通后复测应能连上 |

> 这张表是「放通前」的缺口清单；2026-10-20 已按此全部放通（见 §5.1 全链路验证），后续新增实例/换宿主照此逐项核对即可。

### 5.3 关键操作经验

- MCSM 实例的 `docker.ports` 在 `daemon/data/InstanceConfig/<uuid>.json`；**普通 apikey（权限 1）不能改**（`PUT /api/instance` 需 ADMIN）。
- 本次做法：停实例（`POST /api/protected_instance/stop`）→ 改 JSON + Geyser 配置 → `docker restart orzmc-mcsmanager-daemon`（daemon 启动时从磁盘重载 `InstanceConfig`）→ 启实例（`POST /api/protected_instance/open`，不是 `/start`）。
- 启动/停止路由前缀是 **`/api/protected_instance/*`**（`/open` `/stop` `/restart` `/kill` `/command`）。
- 实例停掉后容器会被移除，重启时按新 `ports` 重建，端口变更才生效。

### 5.4 生产端「信令通、玩家仍连不上」排障法

典型现场（国内服）：`transport: nethernet` + `webrtc-port: 0`（单端口）+ `advertise-addresses: []` + `stun-discovery: true`，启动日志 `Built-in signaling started on http://0.0.0.0:19132`（**单端口模式不会打印 `with NetherNet on UDP port X` 那半句，属正常**），外部实测 TCP 19132 信令 200、Java 25565 正常、**UDP 探测无应答**。

判定顺序（照这个走，别先怀疑平台/版本）：

1. **`RakNet 无应答` 在 nethernet 模式下是正常现象**（该模式根本不监听 RakNet）→ 不能当故障证据，也不能当 UDP 通不通的证据。
2. **先核对 UDP 转发**：单端口模式要放行 **UDP 19132**；`both` 模式要 UDP 19132 + UDP `webrtc-port`。TCP 通了只说明信令通，玩家真正的游戏流量走 UDP——「信令成功 → 随后卡加载延迟」几乎都是 UDP 没转发。
3. **再核对 `advertise-addresses`**：`[]` + STUN 自动发现时，若主机**出网 IP ≠ 域名 A 记录**（双 WAN / 旁路由 / VPN 分流），会把错误地址下发给客户端 → 必挂。核对法：主机 `curl -s https://ifconfig.me` 与 `nslookup <域名> 223.5.5.5` 比对。
4. **加固做法**：显式写 `advertise-addresses: ["<域名>:<端口>"]`（单端口填 `19132`，both 填 `webrtc-port`），不再依赖 STUN。
5. **把 UDP 变成可测**：切成 `both` + `webrtc-port: 19134` 后，`connectivity_check.py` 的 RakNet 探测能直接判定 UDP 19132 是否放通（有 Pong = 通），不必等玩家试。
6. 需要更细证据时临时开 `advanced.nethernet-debug: true`（重启生效，日志很吵，看完改回）。

**本案定性（2026-11-02）**：两端都是「无证书 + 信令 200」却一好一坏 → 差异**不在 TLS，在地址下发**：测试服把 `advertise-addresses` 写死成「公网地址:webrtc 端口」，生产端留空交给 STUN 猜。修法 = 显式写（详见 §5.5）。

**同日切 `both` 后实测**：RakNet **39~66ms** / NetherNet **80~116ms** / `基岩模式 both ✅`。→ **RakNet 一应答就同时证明 UDP 19132 已放通**（both 模式最大的诊断价值：把单向 UDP 转发变成可外部验证）。最终验收用 `python3 scripts/conn_watch.py --host <域名>`（Java 在线数 或 基岩 `/v1/join` 在线数任一上升 = 玩家真进服，不依赖服务端日志权限）。

### 5.5 `advertise-addresses` 写 IP 还是写域名？（2026-11-02 实测）

官方语义：支持 `host` 或 `host:port`（端口省略则用 `webrtc-port`）；**域名在信令启动时解析，解析不了则信令根本不启动**；留空（`[]`）= 本机地址 + `stun-discovery` 探到的公网地址。

**关键陷阱：宿主机跑着 Clash/代理时，域名写法会废掉。** 测试服那台 Windows 实测：`dev.{SERVER_NAME}.cn` → **`198.18.1.7`（Clash TUN 假 IP）**，即使指定 `-Server 223.5.5.5` 仍是假 IP（TUN 劫持全部 DNS）；出口 IP 是**代理节点地址**而非家宽公网 IP。后果：域名解析成假 IP → advertise 玩家连不到的地址；`stun-discovery` 同样会探到代理出口 IP → 也错。该机**必须写死公网 IP**，且不能依赖 STUN。

| 写法 | 适用 | 风险 |
|:--|:--|:--|
|:--|:--|:--|
| `["<公网IP>:<webrtc端口>"]` | 宿主机无代理、IP 稳定（家宽 NAT） | IP 变了要改配置重启 |
| `["<域名>:<webrtc端口>"]` | 宿主机 DNS 干净、IP 常变 | 宿主机有代理/TUN → 解析成假 IP → 全挂；启动时解析失败 → 信令不起 |
| `[]`（留空） | 机器直接持有公网 IP | NAT 后靠 STUN 猜地址，**生产端就是这样挂的** |

**自检（在服务器主机上跑）**：`Resolve-DnsName <域名>` 必须回真实公网 IP；`curl -s https://ifconfig.me` 必须等于该域名的 A 记录。任一不符 → 用 IP 写法。

**测试服现有守护（勿重复造轮子）**：Windows 端 Hermes cron `8582a0f31644`（`orzmc-nethernet-advertise-sync`，**每 15 分钟**，no_agent watchdog，无变化静默）→ 跑 `%LOCALAPPDATA%\hermes\scripts\nethernet_advertise_sync.py`（**v4，2026-11-15 重写**）：
- **只认数字 IP**：`advertise-addresses` 归一成 `["<局域网IP>", "<公网IP>:<信令端口>"]`（信令端口 = `webrtc-port`>0 时取它，否则取 `port`；nethernet 单端口即 19132）。不写域名——理由见上（Clash fake-ip 随时可能回归，2026-11-15 实测容器内 `getent hosts dev.{SERVER_NAME}.cn` 目前回真 IP，但不能当契约）。
- **公网 IP 来源**：DoH（AliDNS 优先）解析 `dev.{SERVER_NAME}.cn`，绕开系统解析器。
- **config 路径自动判定**：`ENABLE_VELOCITY=true` → `E:/orzmc/eagler/proxy/plugins/Geyser-Velocity/config.yml`（ADR-036 后的真实入口，容器 `orzmc-velocity`）；否则回落 MCSM 实例的 `plugins/Geyser-Spigot/config.yml`。
- **生效方式**：Geyser 只在信令启动时读 advertise，Velocity 无 RCON → `docker restart orzmc-velocity`；**有玩家在线时不改不重启**，只报警（同一批待办只报一次，state 文件去重），等空档自动修。
- 日志 `%LOCALAPPDATA%\hermes\logs\nethernet-advertise-sync.log`；state `hermes\state\nethernet-advertise.json`。
- 注意：Windows 上也有独立 Hermes（gateway 进程 + `%LOCALAPPDATA%\hermes\cron\jobs.json`），跨端查 cron 不要只看 Mac。

### 5.6 Exaroton 平台特例（2026-11-09 启动实测）

Exaroton（Aternos 系）**自己托管 NetherNet**，会强制覆盖 Geyser 配置，手改 `advertise-addresses` / 端口无效：

| 启动日志（平台注入） | 含义 |
|:--|:--|
| `Config option [bedrock, signaling, advertise-addresses] set from environment variable GEYSER_BEDROCK_SIGNALING_ADVERTISE_ADDRESSES` | advertise 由平台下发 |
| `Transport set from system property: nethernet` | transport 强制 nethernet |
| `Port set from system property to match Java server` | bedrock 端口跟随 Java 端口 |
| `NetherNet (WebRTC) port set from system property: 19132` | WebRTC 固定在容器内 19132 |
| `Built-in signaling started on http://0.0.0.0:19132` | 信令容器内起在 19132 |
| `webrtc-proxy-protocol-relays` / `signaling-trusted-proxies` 也由环境变量注入 | 平台用 PROXY protocol 中继 |
| `Signaling response headers ... X-Aternos-WebRTC-Proxy-Protocol` | 信令应答带平台专用头 |

**玩家该填什么**：

| 版本 | 地址 | 实测 |
|:--|:--|:--|
| Java | `{SERVER_NAME}.exaroton.me:39742`（端口动态，以面板为准） | ✅ 协议握手正常 |
| **基岩** | **`{SERVER_NAME}.exaroton.me:19132`**（固定 19132，不是 Java 端口） | ✅ 308 → `https://<域名>/v1/join` → 200（2225/26.60） |

**判定口径**：
1. 用 Java 端口（39742）测基岩必定失败（TCP 只认 Minecraft 协议，HTTP 直接 0 字节断开；UDP 无 RakNet/STUN 应答）——**不要拿它当故障**。
2. 基岩正确探法：`TCP <公网IP>:19132` 发 `GET /v1/join` → 期待 **308 + Location: https://<域名>/v1/join**，跟随该 URL 应得 200 JSON。
3. 启动日志出现 `Geyser is configured to expect PROXY protocol on the WebRTC port` **属正常**（平台中继设计，不是配置错），别按官方提示去清空 `webrtc-proxy-protocol-relays`（那是自建服的建议）。
4. 服务器离线时改配置文件虽然成功（PUT 200），但**运行时仍以平台环境变量为准**。

## 6. 验证方法（含本机大坑）

### 6.0 一键体检（2026-11-02 起首选）

```bash
python3 ~/.hermes/skills/gaming/orzmc/scripts/connectivity_check.py            # 全部内置目标
python3 .../connectivity_check.py --only paper,prod-mcsm --external            # 指定 + 外部节点
python3 .../connectivity_check.py --host example.com --java 25565 --bedrock 19132  # 自定义
python3 .../connectivity_check.py --json                                       # 周巡检用
```

一次输出六层结论：DNS（**自动识别本机 Clash TUN 的 `198.18.x` fake-IP，并用 DoH 取真值**）→ Java 协议握手（版本/协议号/人数/MOTD）→ 基岩**旧协议 RakNet** Pong → 基岩**新协议 NetherNet** 信令 `GET /v1/join`（返回服务端支持的 Bedrock 协议号/版本/实时人数）→ 基岩端口 **HTTPS 信令**是否可用 → 可选公网 TCP 外部节点。

判读纪律（血泪）：
- **`RakNet 无应答` ≠ 故障**：`transport: nethernet` 单端口模式本来就不答 RakNet；UDP 未转发也一样表现为无应答 → 必须与配置里的 `transport` 对照再定性。
- **`HTTPS 信令不可用` ≠ 故障**：当前 Geyser/客户端版本下域名连接仍可用（弹一次 TOFU 信任）；脚本已把这项记 ℹ️。判「玩家能不能进」要用实连（§6.3 `conn_watch.py`）+ `advertise-addresses`/UDP 转发核对，而不是看有没有 TLS。
- 「信令 200 + RakNet 无应答」是 `nethernet` 单端口的**正常组合**；真正的失败信号是「信令 200 但玩家卡住」→ 查 UDP 转发与 `advertise-addresses`（§5.4）。
- **若确实要配 HTTPS（只为免弹窗）的硬约束**：家宽域 **80/443 对外通常关闭** → HTTP-01 不可用，**必须 DNS-01**；DNS 托管 DNSPod 时 acme.sh 用 `--dns dns_dp`（`DP_Id`/`DP_Key`）。证书放实例 `plugins/Geyser-Spigot/` 并重启，日志由 `http://` 变 `https://`。

### 6.1 单项工具

- 工具：`~/OrzMC/proxy/scripts/nethernet_check.py [host] [port]`（UDP RakNet 基线 + TCP 信令 HTTP 探测 + 结论 + 退出码 0/1，带 `-h`）
- **判定标准**：TCP 信令能返回 HTTP 应答（脚本显示 `HTTP 业务码`）= 可用；`TIMEOUT` = 未转发/被丢弃；`REFUSED` = 已转发但无监听
- ⚠️⚠️ **本机经 Clash TUN 测 TCP 必假阳性**：域名被 fake-IP 成 `198.18.x.x`，TCP 握手被 TUN 本地接管后「接受并立即关闭」→ 脚本会报 `OPEN_NO_HTTP`，误判成「端口可达」。**正确做法**：
  1. DoH 查真实公网 IP：`curl -H 'accept: application/dns-json' 'https://1.1.1.1/dns-query?name=<域名>&type=A'`
  2. 用外部节点验证 TCP：`check-host.net/check-tcp?host=<IP>:<port>` 拿 `request_id` → `check-host.net/check-result/<id>`（外部节点一律 `Connection timed out` = 未转发）
  3. UDP 侧 `check-host.net/check-udp` **无意义**（普通 UDP 包 Geyser 不回，只有 RakNet 专有包才 Pong）→ UDP 用本机 `bedrock_ping.py` 拿到真实 PONG 即为通
### 6.2 双协议连通性验证矩阵（无真实客户端也能判定到哪一层）

| 层 | 探法 | 判据 |
|:--|:--|:--|
| 旧协议 RakNet | `nethernet_check.py <host> <port>` 第 [1] 步（UDP ping） | 回 Pong + MOTD = RakNet 通 |
| 新协议信令（TCP） | `curl http://<host>:<port>/v1/join` | **200 + JSON**（`dataVersion/protocol/version/players`）= 信令服务在线且能读实时人数 |
| 新协议根路径 | `curl http://<host>:<port>/` | **404 是正常的**（根路径无 handler），不要当故障 |
| 新协议 join 握手 | `POST /v1/join/<id>` | 未带客户端流程时 **401 属预期**，不能据此判「服务坏了」 |
| 新协议真实会话 | latest.log 线程名 | `[NetherNet Built-in Signaling-N-x] Player connected with username X (2225)` = 真客户端走新传输进服成功 |
| 外网 TCP 可达 | DoH 取公网 IP → `check-host.net/check-tcp` 3 节点 | 有连接耗时 = 已转发；全 `timed out` = 未转发/被封 |
| UDP/WebRTC 端口 | ⚠️ **不要用匿名 STUN 判定** | ICE 服务忽略未认证 Binding Request，**无应答 ≠ 端口不通**；改用「docker/面板端口发布清单 + 真实会话日志」作证 |

- **两条协议不能互相替代地证明**：RakNet Pong 只证明 UDP 老通道；`/v1/join` 只证明 TCP 信令；真正进服由日志线程名区分（`localSession-*` vs `NetherNet Built-in Signaling-*`）。
- **无法自测的部分**：旧版本客户端实际登录（需客户端本体）；协议版本上限取自 `/v1/join` 的 `protocol/version`（如 2225 / 26.60），低于 Geyser 支持范围的客户端会被要求升级，与传输层无关。
- 判定纪律：结论要写清「验到哪一层」，不要用「信令通」等价于「玩家能进服」。

- 官方自检：用 **Bedrock 26.40+** 客户端实连；失败先看 Geyser 控制台。

### 6.3 玩家入场监听（改完配置后的终极验收）

```bash
python3 ~/.hermes/scripts/conn_watch.py --host <域名> [--duration 600]
```

基岩玩家经 Geyser 进服后 **Java 侧在线人数也会 +1**，所以脚本同时采 **Java Status 人数 + 基岩 `/v1/join` 人数**，任一上升即证明进服成功。**不需要服务端日志权限**（面板 apikey 失效也能验）—— 这是「配置改完到底有没有修好」唯一免依赖的实连证据；「信令 200」不算。

## 7. 官方错误对照表

| 控制台现象 | 原因 | 处置 |
|:--|:--|:--|
| `Built-in signaling cannot use port … because the Java server already uses it` | 基岩与 Java 共用端口（`clone-remote-port`）| 要独立端口，或继续用外部信令（Geyser 自动回退）|
| `RakNet and NetherNet each need their own UDP port` | `both` 但 `webrtc-port` = 基岩端口 | 设成另一个空闲 UDP |
| `… is a loopback address` | `bedrock.address` 是 127.0.0.1 | 改 `0.0.0.0` |
| 玩家弹「trust on first use」 | 信令走明文 HTTP（纯 IP 直连） | 配 HTTPS 或外部信令 |
| 域名连接卡「加载延迟」、服务端无日志 | 多为 **UDP 未转发**（信令走 TCP 所以能 200）或 **`advertise-addresses` 下发了客户端到不了的地址**（`[]` + STUN 猜错，主机出网 IP ≠ 域名 A 记录时必现）；旧版 Geyser/客户端上也曾因「域名强制 TLS」出现 | 先核对 UDP 转发与 `advertise-addresses`（§5.4）；确属 TLS 时代的旧版本再配 HTTPS |
| `Error while getting Paper ping passthrough: java.lang.reflect.InvocationTargetException` | Geyser 2.12.x 的 `integrated-ping-passthrough` 在 Paper 26.3 上反射失败 → 基岩看到的是 Geyser 自己的 MOTD（`motd.primary/secondary`）而不是 Java 服 MOTD | 要么 `integrated-ping-passthrough: false`（改走 `ping-passthrough-interval` 轮询），要么 `passthrough-motd: false` + 自定 `motd.*`；不影响连接 |

## 8. 备选路线：GeyserNetherNet 扩展（不推荐用于生产）

- 仓库 `GeyserMC/GeyserNetherNet`：以**扩展**形式加 NetherNet（HTTP 信令），README 自述 **work in progress / 未达生产可用**；需要额外依赖 **NetworkCompatible 1.8.0+**，且要自备 `https.p12`（客户端信任的证书）+ `identity.p12`（CN 会成为玩家看到的身份域名）。
- **2.12 起 Geyser 已内置 NetherNet，无需该扩展**；仅在老版本（1237 之前）或特殊需求时考虑。

## 9. 时间线备忘

| 时间 | 事件 |
|:--|:--|
| Bedrock 26.40+ | Mojang 开始推送 NetherNet 客户端 |
| **2026-10-27** | 基岩客户端停用 RakNet → 未切换服务器基岩玩家无法连接 |
| **2026-11-02** | 生产端基岩连不上→真因：`advertise-addresses: []` 交给 STUN 猜地址（出网 IP ≠ 域名 A 记录）；修 = 显式写域名/端口 → 恢复；同日再切 `both` + `webrtc-port: 19134`，新旧客户端均可进 |
| Bedrock 26.60 | 可关掉 RakNet（收敛为纯 nethernet）；同时移除 26.30 支持 |
