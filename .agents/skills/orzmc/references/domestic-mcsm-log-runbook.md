# 国内服 MCSM（线上）启动日志判读手册

> 适用：国内服线上实例（Windows Server 2022 + MCSM 面板托管，玩家域名入口）。
> 本端 **MCSM API 长期 403 → 助手无写权限**，一切改动需老板在面板操作；助手只能做「判读 + 外部实测 + 出操作单」。

## 0. 定位信息

| 项 | 值 |
|:--|:--|
| 面板运行目录 | `C:\Users\Administrator\Desktop\mcsm\mcsmanager\daemon\data\InstanceData\` |
| 实例目录 ID | `6f7a111dec74407891d65044e20a2501`（⚠️ **与测试服 716c2fb7… / 8A932DD4… 不同**，别照抄路径） |
| 运行身份 | `Administrator`（启动日志会告警，非故障） |
| 在线模式 | `online-mode=false`（离线服，靠 LoginSecurity 兜底） |
| 玩家数上限 | 150（`0/150` 为常态空服读数） |
| 助手权限 | 只读探测（外部连通性）；配置读写 **403，需老板手动** |

## 1. 启动日志：期望值（2026-11-10 实测基线，Paper 26.3-246）

按出现顺序核对，**任一缺失即为异常**：

| 日志片段 | 含义 |
|:--|:--|
| `Running Java 25 (25.0.3+9-LTS-195; Oracle Corporation)` | 运行时 OK（26.3 要求 Java 21+） |
| `Loading Paper 26.3-246-main@b31b4b5` | 核心 jar 已换新，`start.sh` 选中的是最新版本化 jar |
| `Initialized 22 plugins` → `Paper plugins (1): OrzMC (1.0.30)` + `Bukkit plugins (21): …` | 插件树完整（OrzMC 走 Paper 插件通道、其余 21 个走 Bukkit 通道） |
| `This server is running Paper version 26.3-246-main@… (Implementing API version 26.3.build.246-stable)` | 核心版本二次确认 |
| `[LuckPerms] Enabling LuckPerms v5.5.91` + `Successfully enabled. (took ~2.8s)` | 权限库 H2 正常 |
| `[WorldGuard] Loading server plugin WorldGuard v7.0.21+2424-da30a99` + 三个世界 `Loaded configuration for world` | 领地插件正常（world / world_nether / world_the_end 三段都要有） |
| `[OrzMC] Loading/Enabling OrzMC v1.0.30` | 自研主插件 |
| `[Geyser-Spigot] Loading Geyser version 2.12.1-b1298` | ⚠️ **build 号只在这行**；前面 `Geyser-Spigot (2.12.1-SNAPSHOT)` 是插件内嵌版本号，不能用来判断 build |
| `Started Geyser on UDP port 19132` | 基岩 UDP 监听 |
| `Built-in signaling started on http://0.0.0.0:19132, with NetherNet on UDP port 19134` | **`both` 模式生效的关键判据**（缺 `with NetherNet on UDP port` 半句即单端口模式） |
| `Done (94.1s)!` 量级 | 本端基线 90–110s；>150s 需查加载瓶颈 |

## 2. 常态告警：不用处理

| 日志 | 为什么是常态 |
|:--|:--|
| `YOU ARE RUNNING THIS SERVER AS AN ADMINISTRATIVE OR ROOT USER` | 面板以 Administrator 跑；整改要迁账号 + 停机窗口，属「待排期」而非故障 |
| `SERVER IS RUNNING IN OFFLINE/INSECURE MODE` | 离线服业务需要（国内玩家多为非正版），改 `online-mode=true` 会挡掉大部分玩家 |
| `[Essentials] You are running an unsupported server version!` | EssentialsX 2.22.0 无 26.x 适配版，功能可用，全端一致 |
| `[ViaVersion] The Vanilla protocol of Minecraft 1.20.5-1.21.4 is easily exploitable` | 已用 `block-versions` 堵掉这 4 段（见 SKILL.md Pitfall），堵完仍会打印一次 |
| `[Geyser-Spigot] You are using an outdated version of ViaVersion` | 上游最新只有 `5.12.3-SNAPSHOT`（beta），按 release-only 纪律保持 5.12.2 |

## 3. 需留意（记录在案，非阻塞）

| 现象 | 风险 | 处置 |
|:--|:--|:--|
| `LoginSecurity v3.3.2-SNAPSHOT` | **密码验证类插件跑预发布构建**，风险高于普通插件；离线服唯一身份防线就是它 | 待评估回退 release（上游不在 Modrinth，需核对 SpigotMC/GitHub 来源） |
| `packetevents (2.14.0)` 独立插件 + `GrimAC` 内嵌 `2.14.1+addb80e-SNAPSHOT` | 双实例并存属既有部署，目前无报错 | 观察；仅当出现 packet 相关异常再收敛 |
| `Paper: Using Java compression/cipher from Velocity` | 说明 `paper-global.yml` 启用了 Velocity 现代转发 | 基岩仍直连 19132（实测双协议通），不影响基岩；Java 侧转发模式须与代理一致 |
| `[WorldGuard] TNT ignition is PERMITTED / Fire spread is UNRESTRICTED` | 世界级保护策略较宽松 | 由领地规则兜底，非启动问题 |

## 4. 外部实测验收（无面板权限也能验）

```bash
python3 ~/.hermes/scripts/connectivity_check.py --only prod-mcsm --external
```

2026-11-10 基线（升级后）：

| 项 | 读数 |
|:--|:--|
| Java | ✅ 113ms，Paper 26.3，协议 767，0/150 |
| RakNet（旧基岩） | ✅ 148ms，基岩 26.63 / 协议 2225 |
| NetherNet（新基岩） | ✅ 174ms |
| 基岩模式 | **both ✅** |
| 公网 TCP | ✅ 3/3 节点 |
| DNS | 本机 TUN 假 IP `198.18.x` → DoH 真值自动修正（脚本内建） |

> 「RakNet 有应答 + NetherNet 有应答」= 双端口都放通，**不必等日志尾部**即可确认基岩通道正常。

## 5. 排障顺序（基岩连不上时）

1. 先跑上面的外部实测 —— 分清「服务端没起来」还是「网络/入口问题」。
2. 抓 `transport` / `webrtc-port` / `advertise-addresses` 三项配置（老板截图或面板读）。
3. 对照 `references/nethernet.md` §5.2 端口放行核对表与 §5.4 排障表。
4. 本端是 `both`：需 **TCP 19132 + UDP 19132 + UDP 19134** 三条放行；缺 TCP 会导致「Java 通、基岩加载卡住」。
