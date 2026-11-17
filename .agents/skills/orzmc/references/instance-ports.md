# 实例端口模型与审计（非默认端口 / 多实例并存）

> 结论先行：MCSManager 的 **docker 型实例端口必须逐条显式发布**（`docker.ports: ["宿主:容器/协议"]`），
> 且**判断依据是实例自己的配置，不是「默认 19132/25565」**。核心换 Folia/Purpur、Geyser 改 bedrock port、
> 多实例并存，都会让「文档里的默认端口」失效。审计脚本：`scripts/port-audit.py`。

## 1. 为什么不能照抄默认端口

* 容器端口由实例内配置决定：Java = `server.properties: server-port`；基岩 = `plugins/Geyser-*/config.yml: bedrock.port`；
  Query = `query.port`（`enable-query=true` 时）；RCON = `rcon.port`（`enable-rcon=true` 时）；SimpleVoiceChat = `24454/udp`（或插件 config 里的 port）。
* **宿主端口**由 `docker.ports` 左侧决定，可以和容器端口不同（本机 FoliaMC 就是 `25566:25565/tcp`）。
* 面板的 `pingConfig.port`、实例 `basePort` 都只是**容器端口**语义，不代表宿主可达端口。
* 只有 `docker.ports` 里写了的映射，宿主/局域网才可达；容器内监听通 ≠ 外部可达。

## 2. 审计脚本用法

```bash
python ~/AppData/Local/hermes/skills/gaming/orzmc/scripts/port-audit.py \
       E:/orzmc/mcsmanager/daemon/data [--probe] [--json]
```

行为：遍历 `InstanceConfig/*.json`（跳过 `.bak-*`、只取 `processType=docker`）→ 从 `server.properties`、
`plugins/Geyser-*/config.yml` 解析**期望端口**→ 与 `docker.ports` 逐条比对 → 分「必发布（java/bedrock）」与
「按需（query/rcon/voice）」列出，检测跨实例**宿主端口冲突**，`--probe` 再对宿主端口做真实协议探测
（Java 握手 Ping / RakNet Unconnected Ping）。退出码 1 = 有必发布缺口，可直接接进巡检。

## 3. 本机实测案例（2026-09-11）

```
PaperMC  [minecraft/java/paper]  已发布: 25565:25565/tcp, 19132:19132/udp
  ✓ java     tcp 容器 25565 -> 宿主 25565/tcp   probe OK Paper 26.2 | 0/150
  ✓ bedrock  udp 容器 19132 -> 宿主 19132/udp   probe OK MCPE;…;26.45;0;150;…;19132;19132;
FoliaMC  [minecraft/java/folia]  已发布: 25566:25565/tcp
  ✓ java     tcp 容器 25565 -> 宿主 25566/tcp   （实例未运行，probe 拒绝连接 = 正常）
  ✗ bedrock  udp 容器 19132 -> 宿主 —— 未发布   ← 基岩通道在容器外不可达
```

要点：FoliaMC 的 Java 宿主端口是 25566（非默认），说明「宿主端口 ≠ 容器端口」是常态；
它的 Geyser 仍是容器内 19132，但**一条 UDP 映射都没有** → 与修复前的 Paper 同一个病。

## 4. 多实例并存的端口分配

* 容器之间各有 netns，容器内都绑 19132 不冲突；**冲突只发生在宿主发布层**。
* 基岩客户端**不支持 SRV 记录**，玩家必须手填 `主机:端口` → 每个基岩服需要独立的宿主 UDP 端口。
* 建议按实例编号排块：

| 实例 | Java(tcp) | 基岩(udp) | Query(udp，按需) | 说明 |
|---|---|---|---|---|
| #1 PaperMC | 25565 | 19132 | 9898 | 主入口 |
| #2 FoliaMC | 25566 | 19133 | 9899 | 与 #1 并存，UDP 必须错开 |

**本机已落地（2026-09-11，两实例同宿主，audit 退出码 0）：**

| 实例 | `docker.ports` 实际值 | 玩家入口 |
|---|---|---|
| PaperMC（`716c2fb7`） | `["25565:25565/tcp","19132:19132/udp"]` | Java `192.168.0.33:25565`、基岩 `192.168.0.33:19132` |
| FoliaMC（`8A932DD4`） | `["25566:25565/tcp","19133:19132/udp"]` | Java `192.168.0.33:25566`、基岩 `192.168.0.33:19133` |

FoliaMC 走的是**方案 B**（Geyser `bedrock.port` 保持容器内 19132，只把宿主侧映射到 19133，`clone-remote-port: false`）——因此它的 RakNet pong 会回报 `19132`，那是容器内值，不是玩家端口。**两实例地图已独立、可同时运行**（2026-09-11 实测：同上在线，Paper Java `25565`+基岩 `19132`、Folia Java `25566`+基岩 `19133` 双通道全部 OK）。

两种改法（都能用，取舍在「可读性」）：

* **A（推荐）容器内也改成同号**：Geyser `bedrock.port: 19133` + `docker.ports: ["19133:19133/udp"]`。
  宿主与容器一致，RakNet pong 回报的端口就是玩家该填的端口，排查不会互相打脸。
* **B 不动插件配置**：`docker.ports: ["19133:19132/udp"]`。少改一个插件配置，但 pong 里回报 `19132`，
  肉眼看日志/抓包容易误判（`clone-remote-port` 仍须 `false`）。

⚠️ `clone-remote-port: true` 会让 bedrock port 跟随 Java 端口，在「宿主≠容器」的 docker 场景下必然错位，本机所有实例都保持 `false`。

## 5. 远程（非局域网）的边界

* Java 通道可以走 cloudflared（TCP）；**Cloudflare Tunnel 不支持 UDP**，基岩通道不能靠它。
* 基岩远程要另配 UDP 中继：playit.gg 之类的 UDP 隧道，或自建 VPS 上 `socat`/nginx stream 转发；
  也可以在前面放基岩代理（WaterdogPE 之类）用一个公网 UDP 端口聚合多个后端服。
* 同一宿主多实例用不同 UDP 端口是最省事、最稳的方案；只有当「玩家只能记一个端口」时才需要代理层。

## 6. 改端口的两条路（都能落地）

* 文档姿势：停 daemon 容器 → 改 `InstanceConfig/<uuid>.json` → 启 daemon → 面板启动实例（有停机窗口）。
* daemon socket.io：连 `http://<daemon>:24444`（`path=/socket.io`，key 取 `daemon/data/Config/global.json`）
  → `emit("auth", key)` → `emit("instance/detail",{instanceUuid})` → 改 config → `emit("instance/update",{instanceUuid,config})`。
  **无需停 daemon、无需 admin apiKey，改完即刻落盘**（面板 `PUT /api/instance` 要求 `ROLE.ADMIN`，普通 key 返回 403「密钥不正确」）。
  客户端脚本可用 web 容器现成的 socket.io-client：`docker exec -i orzmc-mcsmanager-web node -e '…require("/opt/mcsmanager/web/node_modules/socket.io-client")…'`。

## 7. 交付清单（动端口时逐条过）

1. 审计脚本跑一遍，确认「必发布」全 ✓、无宿主端口冲突。
2. 改完后**重新启动实例**（`docker.ports` 只在创建容器时生效，热改配置不会改已存在容器的映射）。
3. 实测双通道：`--probe`（或 `~/OrzMC/proxy/scripts/bedrock_host_check.sh` / `bedrock_ping.py`）——**本机自测 `192.168.x.x` 会 hairpin 假阴性，局域网可达须另一台设备实测**。
4. 端口若有变，同步通知玩家入口（基岩无 SRV，必须手填端口）与任何写死端口的脚本/文档（本机 Folia 插件配置里未写死 19132，已确认）。
