# 对外端口暴露面最小化（「哪些端口要路由器转发、哪些能清理」）

> 老板问「测试服结构里哪些端口需要我在路由器上做转发、哪些可以清掉，把对外暴露压到最少」时按本文答。
> 先分层再数端口：**同一台宿主上监听的端口 ≠ 需要对公网开放的端口**。

## 1. 推理顺序（先判定，再列表）

1. **谁在宿主上监听**：`docker ps` 的 `Ports` 列 + `compose.*.yaml` 的 `ports:`（`expose:` 不算，只对内网可达）+ `netstat -ano -p tcp`（Docker Desktop/WSL2 的监听在 VM 内，netstat 看不全，以 `docker ps` 为主）。
2. **谁有公网 DNS 记录**：`curl -H 'accept: application/dns-json' 'https://1.1.1.1/dns-query?name=<子域>&type=A'`（本机 Clash TUN 会把域名解成 `198.18.x`，别用 ping/nslookup）。
3. **谁已经在 Caddy 443 后面**：读 `site/Caddyfile` 的 site 块。**凡是经 Caddy 按 SNI 反代的内部服务，一律不需要自己的转发规则** —— 这是压缩端口数的唯一有效手段。
4. 剩下的 = 必须单独占一个公网端口的协议。

## 2. 决策表（家宽 + Velocity 统一入口拓扑）

| 端口/协议 | 判定 | 理由 |
|---|---|---|
| `443/tcp` | **必须转发** | Caddy 唯一公网 Web 入口：面板 `mcs.` / 机器人 `easybot.` / 音乐站 `music.` / 网页客户端 `dev.` 全部在这一个口后面（2026-11-19 起家宽入站 443 已可进，原 18443 入口与映射已删除） |
| `25565/tcp` | **必须转发** | Velocity Java 入口 |
| `19132/udp` + `19132/tcp` | **必须转发（要基岩就要两条）** | UDP = RakNet 老客户端/Realms 信令，TCP = NetherNet 信令，两个独立协议 |
| `24454/udp` | **可选** | Simple Voice Chat。`voice_host` 为空时插件广播「域名:24454」，公网玩家要用语音才转，否则删 |
| 面板 `23333` / easybot `18091` / orzmusic `8080` / sticker `3000` | **删** | 全部已在 443 后面，直连暴露只是多开一个口（且面板密钥会裸奔） |
| 后端 RCON `25575/25576`、旧基岩 `19133-19135` | **删** | 已被 nethernet 单端口取代 / 服务已关，转发=开洞给不存在的服务 |
| `18443/tcp` | **删** | 2026-11-19 入口改回 443 后，18443 宿主映射已从 `compose.site.yaml` 删除，路由器上那条旧映射也要删 |
| `22/tcp` | **不转**（建议） | 公网暴破首选目标；远程运维走 RayLink/局域网 |
| `3389/tcp` | **绝不转** | RDP 走 RayLink |
| `80/tcp` | **不转** | 家宽入站 80 仍被封；证书走 DNS-01，不需要 80 校验 |

最小集 = **4 条**（+1 条语音可选）。多于 5 条就不是拓扑需要，而是内部服务被重复暴露。

## 3. 为什么压不下去 / 为什么不能合并

* MC Java 协议是自定义明文协议、**没有 SNI**，无法像 HTTP 那样按域名复用到 443；基岩是 UDP，任何 HTTP 反代都带不了 → 这两个必须各占端口。
* 入口用 443 而非高位端口：2026-11-19 起家宽入站 443 已可进（旧结论「80/443 被封」仅适用于 2026-10-29 那次实测）。判断端口是否被可用，用 refused（=无映射）而非 timeout（=被封）区分，并以**当次实测**为准，不要沿用旧结论。
* 想让端口更少的唯一方向：砍协议而不是搬家 —— 只留网页客户端可去掉 25565；公网不打语音可去掉 24454。

## 4. 结论的可信度边界（必须写进答复）

* **本机读不到路由器转发表**：UPnP 关闭时 SSDP `M-SEARCH` 拿不到 IGD 描述；check-host.net / yougetsignal 这类公共探测的输出不稳、且只覆盖 TCP（普通 UDP 包服务端不回）。
* 因此回复口径固定为「**基于宿主监听 + 防火墙规则推导**的建议清单」，请老板对着路由器页面核一遍；不要把推导写成「你路由器上现在开着 X」。

## 5. Windows 防火墙残留（`netsh advfirewall firewall show rule name=all dir=in` 的解析坑）

* 输出按「规则名 + 字段 + 分隔线」循环，**按 `------` 分块会把规则名与字段错位一格**（名落在上一块的尾部）→ 只可信「本地端口」值，不要相信「规则名 ↔ 端口」的配对；要配对就先落盘再按块首行重新切。
* 死规则会掩盖端口变化，清一遍：已下线服务的放行（旧基岩 19133-19135、RCON 25575/25576、`ollama.exe` 11434、`traefik.exe` 8080、预览端口 3002）。这些不影响路由器，但都是本地多余开口。
* **2026-11-19 已清理完**（406 → 389 条）：删掉 `OrzMC-RCON`、`OrzMC-MC-TCP`/`OrzMC-MC-UDP`（与 `OrzMC-MC-Public-*` 重复）、`Bedrock Geyser 19132/19133`、`Bedrock NetherNet 19134/19135`、`Ollama LAN Access` + `ollama.exe`×2、`traefik.exe`×2、`HyperFrames-3002`/`HyperFrames Preview`/`HyperFrames Preview 3002`，并把 `OrzMC-Web-TLS` 从 `80,443,18443` 重建为**只放 443**。剩下 5 条 = `OrzMC-Web-TLS`(443)、`OrzMC-MC-Public-TCP`(25565,19132)、`OrzMC-MC-Public-UDP`(19132,24454)、`OrzMC-Panel`(23333，**远程 IP 限 192.168.0.0/24**)、`OrzMC-EasyBot`(18091，同样限 LAN)。
* 改防火墙必须提权：当前 Shell 是**非管理员**，`netsh advfirewall delete` 会失败。做法：把命令写成 `.cmd` 落盘，`powershell -NoProfile -Command "Start-Process cmd.exe -ArgumentList '/c','<path>.cmd' -Verb RunAs -Wait"` 弹 UAC（要老板点「是」），日志重定向到文件后回读确认；`netsh` 按 `name` 删除会把同名多条（如 `ollama.exe` 的 TCP/UDP）一起删。
* 防火墙/路由器一律按老板偏好逐端口配置，**不要提议 DMZ 或端口段映射**。

## 6. 宿主侧还能收口的三件事（附带代价）

1. ~~删 Caddy 的 `80:80` / `443:443` 宿主映射~~ → **2026-11-19 已完成**：`compose.site.yaml` 只留 `443:443`，`80` 与 `18443` 映射均已删除（重建 caddy 用 `docker compose --env-file .env -f src/OrzMC/deploy/compose.yaml -f compose.site.yaml up -d --no-deps caddy`；只带 `-f compose.site.yaml` 会报 `service "velocity" has neither an image nor a build context`）。
2. 清防火墙死规则 → 需管理员权限，会弹批准。
3. 内部服务从 `0.0.0.0` 改绑 LAN IP（`.env` 的 `LAN_BIND_ADDR`）—— **orzmusic 例外**：Caddy 用 `host.docker.internal:8080` 反代它，绑 `127.0.0.1` 直接 502。
