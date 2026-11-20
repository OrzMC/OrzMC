# Eaglercraft 网页客户端接入（给没有代理层的服加 wss 入口）

老板要「让网页客户端能进服」时用本文。核心口径：**这不是装一个插件的事**——网页客户端必须有一个 **wss://** 入口 + 后端能翻译 1.8 协议，缺一个都进不去。

## 先判现状：这台服有没有代理层

从外部对 25565 做状态包握手，看返回的版本串：

```bash
PYTHONPATH="" python "$LOCALAPPDATA/hermes/scripts/connectivity_check.py" --only <目标名>
# 目标名用 --list 查（如 prod-mcsm）；临时目标用 --host <域名> --java <端口> --bedrock <端口>
# ⚠️ --java / --bedrock 都必须带端口号，只写 --java 会报 "expected one argument"
# ⚠️ --external（check-host 外部探测）需先 export HTTPS_PROXY=http://127.0.0.1:7897，否则回 SSL EOF 假失败
# 回 "Paper 26.3"           → 无代理层，Paper 直占 25565
# 回 "Velocity 1.7.2-26.3"  → 已有代理层，只加 EaglerXServer 插件 + wss 反代即可
```

国内生产服实测（2026-11）：`{SERVER_HOST}:25565` 回 **Paper 26.3**（无 Velocity），Geyser-Spigot `both` 模式占 `19132/tcp+udp` + `19134/udp`，`online-mode=false`。

## 两条路线，先选再动手

| | **EaglerXPaper**（Paper 插件，无代理） | **Velocity + EaglerXServer**（补一层代理） |
|:--|:--|:--|
| 改动面 | 只加 1 个 jar（双栈复用原端口）+ 一个 wss 反代 | Paper 退到 `127.0.0.1:25566` + 转发密钥 + 代理进程 |
| 真实 IP | 直连 Paper，天然真实 | 配 `MODERN` 转发才真实，配错即全 `127.0.0.1` |
| 停服代价 | 一次重启（Paper 冷启动 90–110s） | 端口迁移，失败会让 Java 玩家全被拒 |
| Folia | ❌ 不支持 | ✅ |
| 维护风险 | 单人 fork，靠 NMS 反射名表，Paper 大改后可能失效 | 上游维护，稳定 |
| 只能面板手维（无 APIKey） | ✅ 回滚 = 删 jar | 多一个常驻进程 + 服务化 |

**选择口径**：无代理层 + 只有 Paper + 要最小改动 → EaglerXPaper；要覆盖 Folia，或需要转发真实 IP/多后端 → Velocity 方案。Velocity 方案留作 EaglerXPaper 失效后的备胎。

## EaglerXPaper 事实表（用前重新核对，别照抄）

```bash
# 仓库/README/依赖一律用 gh CLI 取原文
export HTTPS_PROXY=http://127.0.0.1:7897
gh api repos/PlanetDogeCodes/EaglerXPaper --jq '{pushed:.pushed_at,stars:.stargazers_count}'
gh api repos/PlanetDogeCodes/EaglerXPaper/readme -H "Accept: application/vnd.github.raw"
gh release download v1.1.1-S2 -R PlanetDogeCodes/EaglerXPaper -p '*.jar' -O eaglerxpaper.jar
PYTHONPATH="" python -c "import zipfile;print(zipfile.ZipFile('eaglerxpaper.jar').read('plugin.yml').decode())"  # 确认真实插件名/api-version
```

- jar 内 `plugin.yml` 的 `name` 是 **`EaglercraftXServer`**，所以配置目录是 `plugins/EaglercraftXServer/`；配置结构与上游 EaglerXServer 一致，可直接套用。
- **硬依赖 ViaVersion + ViaBackwards**（作者原文 "NEEDED for this plugin to function"）；要 1.8 客户端进来还需 **ViaRewind**。后端 26.3 时，1.8.8 网页客户端全靠这层翻译。
- 支持 **Paper 1.12.2 – 1.21.11+**，26.x 需 **Java 25+**，**不支持 Folia**。
- 与 Geyser/Floodgate 可共存；`online-mode=true` 的正版验证服不能开箱即用（离线服才行）。
- 它**不发客户端文件**：玩家得自己填 `wss://域名/`，或另装 EaglerWeb（上游标注未在 1.21+ 实测，不算承诺）。

## 双栈（同一端口同时吃 WebSocket 和原生 TCP）怎么配

机制：看每个连接的**首包**——HTTP 升级请求进 Eagler 的 WS 管线，原生 Minecraft 握手原样透传给 Paper。不需要第二个端口，Java 玩家无感。**`dual_stack` 默认就是 true。**

`plugins/EaglercraftXServer/listeners.toml`：

```toml
[[listener_list]]
	listener_name = "listener0"
	inject_address = "0.0.0.0:25565"      # 必须等于 Paper 实际监听；server-ip 留空就用 0.0.0.0
	dual_stack = true                      # 核心开关，默认 true
	forward_ip = false                     # 有反代时置 true
	forward_ip_header = "X-Real-IP"        # 与反代实际传的头名对齐
	spoof_player_address_forwarded = true  # 让 Paper 侧看到真 IP（IP 封禁/限流才有效）
	forward_secret = false                 # 25565 直接暴露公网时设 true，防伪造头绕过反代
	forward_secret_header = "X-Eagler-Secret"
	server_motd = ["&6OrzMC 网页版"]
```

协议窗口看 `settings.toml` 的 `[protocols]`（详见 `references/client-version-range.md`）。

## TLS 两种做法，**二选一，绝不能同时开**

**① 反代终结（推荐，证书轮换省心）** —— 插件侧 `tls_config.enable_tls = false`：

```
mc.example.com {
    reverse_proxy 127.0.0.1:25565 {
        flush_interval -1                 # 缺这行 = 长连接被缓冲，网页客户端连上即断
        header_up X-Real-IP {remote_host} # 头名要与 forward_ip_header 一致
    }
}
```

**② 插件自带 HTTPS**（不想引 Caddy）：

```toml
	[listener_list.tls_config]
	enable_tls = true
	require_tls = false                       # false = 同端口兼收 ws/wss（按首字节 0x16 区分 TLS）
	tls_public_chain_file = "fullchain.pem"   # 必须是含中间证书的完整链
	tls_private_key_file = "privatekey.pem"
	tls_auto_refresh_cert = true
```

证书走 **DNS-01**（国内机房/家宽 80 端口验证常不通，未备案 443 也可能被拦）；Cloudflare **橙云代理不了 25565**，只能当 DNS + 证书源，流量走自己的 443。

### 证书从哪来（只知道域名、无 APIKey、只能面板手维的生产服）

先按 **NS 归属**定证书来源，别再猜：

```bash
nslookup -type=NS <域名> 223.5.5.5
# hake.dnspod.net / five.dnspod.net → DNSPod（腾讯云）；dns*.hichina.com → 阿里云
```

两条路，按「能接受多久一次人工」选：

| | 手动签（控制台 DV） | 自动签（lego） |
|:--|:--|:--|
| 怎么做 | 云厂商免费 DV，DNS 验证加一条 `_dnsauth.<子域>` TXT，下载 **nginx 格式** → 改名 `fullchain.pem` / `privatekey.pem` | `lego --dns dnspod --domains <域名> --accept-tos run`，`DNSPOD_API_KEY` 只走环境变量 |
| 续期 | 免费 DV 通常 **90 天**，到期重签 = 每季一次人工（没有 APIKey 就必然落在人身上） | `lego renew --days 30 --renew-hook <复制脚本>` + `schtasks /create /tn lego-renew /sc daily /st 03:30` |
| 产物 | 注意别下成 IIS/PEM 包，nginx 格式才自带完整链 | `.crt` 已含完整链、`.key` 本身就是 PKCS#8，可直接用 |

落盘与格式三条硬检查：

- 证书放**服务器工作目录**（与 `server.properties` 同级），**不是** `plugins/EaglercraftXServer/`；`tls_public_chain_file` / `tls_private_key_file` 写相对工作目录的文件名。
- `fullchain.pem` 里必须有**两段** `BEGIN CERTIFICATE`（缺中间证书 = 部分客户端/手机浏览器握手失败，本机 curl 却看不出问题）。
- 私钥若是 PKCS#1（`BEGIN RSA PRIVATE KEY`）必须转 PKCS#8：`openssl pkcs8 -topk8 -nocrypt -in old.key -out privatekey.pem`。
- **不要用 Cloudflare Origin 证书**：只被 Cloudflare 信任，玩家浏览器直连到 25565 会报不受信。
- 走插件自带 TLS 时 `forward_ip` 必须 **false** —— 没有反代就不会有 `X-Real-IP` 头，置 true 会直接把连接拒掉。

签完的验证（**不加 `-k`**，加了等于没验）：

```bash
curl.exe -i https://<域名>:25565/          # 期望 404/101，而不是证书错误
openssl s_client -connect <域名>:25565 -servername <域名> </dev/null 2>&1 | grep -E '^subject=|^issuer='
# 必须打印证书 subject/issuer；只看到 `no peer certificate available` = 这个端口根本没有 TLS
```

⚠️ **绝对不要用 `grep 'Verify return code'` 判 TLS**：openssl 在**完全没有证书**的端口上也打印
`Verify return code: 0 (ok)`（“没有可验证的证书，所以无失败”），照这条验会把明文端口验成「已配 TLS」——
这正是「以为 wss 好了、玩家却连不上」的来源。同理，`http://…:25565/` 能回 404 插件页 + `ws://` 能拿到 `101`，
也只能证明**服务在跑且讲明文**，证明不了 wss 可用。

别忘端口：`25565/tcp` 要在防火墙/安全组单独放行，只开 443 是本机自测通、玩家进不来的经典假绿。

## 测试服 Caddy 的证书续期（不用管，但有哨兵）

`orzmc-caddy`（v2.11.7）走 ACME + **ARI**：向 Let's Encrypt 询问建议窗口后自动续，90 天证书通常在剩余约 1/3 寿命时完成，容器运行即生效、热切换不重启、不依赖入站 80/443（DNS-01 via Cloudflare）。**不要手工续期，也不要删 `E:/orzmc/caddy/data`**（删了触发 LE 重复证书配额，5 张/周）。

失败是静默的，因此挂了 cron `caddy-cert-watch`（每日 09:05，脚本 `%LOCALAPPDATA%/hermes/scripts/caddy_cert_watch.py`，no_agent 空输出=静默）：检查剩余天数 <21、期望子域缺证书、容器未运行、24h 内 `logger` 以 `tls` 开头的 error。注意过滤 ACME 错误时必须认 logger 名 —— `http.log.error.log0` 里的 404/EOF 是正常探测噪声，按“含 tls/acme 字样”过滤会天天误报。

## 测试服运行树：只认 Release 包（2026-11-20 定案）

- 程序树 = `E:\deploy\orzmc`（**单个固定目录**，release tarball 原地覆盖升级；老板明确反对多余一层，别再搞 `orzmc-current` junction 或保留多份 `orzmc-deploy-<ver>` 目录）。`up/stop/status` 只从这里执行。
- 目录职责三句话：程序 `E:\deploy\orzmc` / 数据 `E:\orzmc`（DATA_ROOT）/ 备份 `E:\orzmc-backups`（`backup.sh` 默认落点）。`E:\orzmc` 里混有 `tools/`(jdk25/gradle/hugo，JAVA_HOME 指向它) 与 `tmp/` 缓存，**不要**为「整洁」搬它们——代价是改环境变量 + 仓库多个脚本，而 `backup.sh` 根本没有任何排除项（`tar` 整个 DATA_ROOT），该改的是脚本的排除名单。
- `E:\orzmc\src\OrzMC` 已删除（曾既是开发克隆又被误当运行树，caddy 的 config_files 就指向过它）。开发克隆只保留 `E:\dev\OrzMC`。
- 验收命令：`docker ps --format '{{.Names}}' | while read -r c; do docker inspect "$c" --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}'; done` —— 五个 orzmc-* 容器必须全部指向 `E:\deploy\orzmc`。
- **端口拓扑（容易配反）**：运营商封的只是**外网** 443；内网 443 正常。所以 Caddy 固定发布**宿主 443**（`"443:443"`），公网入口由**路由器**做 `外网 18443 → 内网 192.168.0.33:443`。玩家地址写 `wss://dev.{SERVER_NAME}.cn:18443`——18443 是路由器外侧端口，宿主上根本没有这个端口。
- **坑**：`$DATA_ROOT/compose.site.yaml` 的 caddy 端口曾写 `18443:443`（把路由器侧和执行侧搞混），导致宿主 443 无人监听、路由器转发打到空端口。验证方法：宿主 `curl -sk --resolve dev.{SERVER_NAME}.cn:443:127.0.0.1 https://dev.{SERVER_NAME}.cn:443/` 应得 404 + `Via: 1.1 Caddy`；再从内网连**公网 IP:18443**（hairpin）应得同样结果（404 + 101）。注意 hairpin 下 `公网IP:443` 也会通，**不能**用它判断外网 443 是否被封，必须用外网节点。

## 家宽入口：入站 443 常被运营商封 → web 入口固定用高位端口

玩家反馈「外部设备打开网页客户端进不去」时，**先测入口端口的外部可达性，别先查插件**。
判据要三样并置才下结论：① 同 IP 的高位端口通不通（通 = IP/DDNS/NAT/防火墙都没问题）；② 80/443 的返回类型
（**timeout = 被静默丢弃**，`refused` = 包到了宿主但没监听）；③ **路由器上确实存在 `443→宿主:443` 这条规则**（让老板确认，
本机读不到转发表）—— 规则存在仍 8/8 timeout 才能锁定运营商；没这条规则时现象一模一样，别把一个没配的映射当成封锁证据。家宽入站 80/443 常被运营商
按策略静默丢弃，而同一 IP 的高位端口（18443 之类）正常：判据与三种返回的并置表见
`network-connectivity-diagnosis` 的「同一 IP 上高位端口通、80/443 全 timeout」一节。

- 确认封了之后，**不要再去路由器反复改映射**：把外部端口改成高位（如 `18443 → 宿主:443`），Caddy 内部继续听 443，
  **证书不用重签**，玩家地址写成 **`wss://<域名>:18443/`**（网页客户端支持带端口地址）。
- **`443→宿主:443` 与 `18443→宿主:443` 可以同时留着**：Caddy 内部只有一个 443 监听，两条映射只是两个外部入口，
  互不冲突、也不占额外资源。所以查证阶段让老板**两条都配上一次性测完**（判据见下），别为了「万一 443 能用」
  来回删改规则 —— 每次改映射都要重测一轮，而并存是零成本的。测完把「打不开的那个」留着也无害，
  公开地址只写实测能进的那个；等哪天运营商放开 443，地址改回不带端口的版本即可。
- 同类站点（面板/easybot/音乐站）同在一个 Caddy 443 上，一并变成 `https://<子域>:18443/` —— 这可以当作交叉验证：
  面板也打不开 ⇒ 入口问题，与网页客户端/插件无关。
- **改端口必须同步改对外公布地址的配置项**（`site/config/_default/params.toml` 的 `web_port`、文档、引导文案），
  否则站点给玩家复制的还是已封端口的 `wss://域名:443/`，故障会以「玩家说还是连不上」二次复发。
  注意**站点是 CI 发布产物**：本地改文件不生效，要 push 到 OrzMCSite 走 Pages 才会上线，
  验收必须去线上页面 grep 旧端口（应为 0），不能只看本地 diff。
  **发布链路两处卡点**：① 父仓（OrzMC/OrzMC）的 main 不能直推，要开 PR 等 `verify` 检查绿了再合；
  ② gh-pages 已更新、CDN 仍回旧值（max-age=600）→ 别写 `sleep 150` 类长轮询（会被 exit 124 杀掉），
  改用浏览器直接打开线上页面、点开「地址」眼睛按钮读 DOM（地址是延迟渲染的，grep 原始 HTML 可能看不到）。
- 真想要「不带端口的 443」只有一条路：Cloudflare 橙云代理 443 + 回源高位端口（多一层代理与延迟），别为了它把
  Eaglercraft 的 TLS 层拆成插件自带 TLS 去赌 443 能进。

**外部验证不必等玩家/手机**：`export HTTPS_PROXY=http://127.0.0.1:7897` 后用 `curl https://<域名>:<端口>/` 与 WS 升级请求
从公网绕一圈回来，一次同时验证 TLS 证书 + Caddy 按 Host 分流 + `101 Switching Protocols`（写法见同一 skill 的
「本机代理当外部观察点」）。`404 'Websocket Upgrade Failure'` + `Server: EaglercraftXServer/*` = 已打到正确后端。

## 上线验证（顺序固定）

```bash
# 1) WS 侧：期望 101 Switching Protocols
curl -i -H "Connection: Upgrade" -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" -H "Sec-WebSocket-Key: x3JJHMbDL1EzLkh9GBhXDw==" \
  http://127.0.0.1:25565/
# 2) 只有一个监听者（不是偷偷起了第二端口）
netstat -ano | findstr :25565
# 3) Java 侧没被弄坏
PYTHONPATH="" python "$LOCALAPPDATA/hermes/scripts/connectivity_check.py" --only <目标名>   # Java 侧没被弄坏（回原版本串）
# 4) 真跑：浏览器 wss://域名/ 进服 + 基岩 19132 仍通 + 三个 Java 客户端（1.8.8 / 中间版 / 服务端版本）各进一次
```

## 坑

- **`inject_address` 与 Paper 实际绑定不一致 → 静默失效**：日志不报错，WS 一律超时。改完先看启动日志有没有注入行。
- **`server.properties` 里 `server-ip=127.0.0.1`**：外网连 WS 也进不来，双栈绑定跟着变回环。
- **`forward_ip=true` 但反代没传对应头**：网页玩家 IP 全变 `127.0.0.1`，限流与 IP 封禁一起失效；`forward_secret` 不开又暴露 25565，别人可伪造该头绕过反代。
- **反代 + 插件自带 TLS 同时启用 = 双重 TLS**，握手必然失败。
- **Netty 管道会抢**：EaglerX 系靠注入 pipeline 工作，与同样改管道的插件（`packetevents`、`GrimAC` 内嵌 packetevents）叠加时，「登录后 Bad packet id」「偶发断连」是典型症状。**上生产前先在一份实例副本上灰度。**
- **核对作者实测过的核心版本**：README 写 "up to 26.x" 但列出的是 1.21.11–26.2；跑 26.3 属「大概率行、未验证」，出问题先怀疑反射名表，不是配置。
- **网页客户端只能 `wss://`**：https 页面里的 `ws://` 会被当混合内容拦掉，TLS 这层躲不掉。
- **给已有 Java 明文入口的端口开 TLS 前必须先灰度**：`require_tls=false` 声称按首字节 `0x16` 嗅探区分 ws/wss 并让原生握手透传，
  但这依赖嗅探零误判，一次误判就是全部 Java 玩家进不去。先在副本上验「`wss` 101 + Java 多版本握手」同时成立再动生产；
  拿不准就走「另开一个端口专供 wss」或「前置反代终结 TLS」，不去碰 Java 那根端口。
- **三端验收要分开下结论**：Java / 基岩 / 网页是三条独立链路，`connectivity_check.py --only <目标>` 一次能把
  Java（Paper 版本串）+ 基岩旧 RakNet Pong + 新 NetherNet 全验完；网页端要单独拿**证书块**证。
  基岩 `both` 模式下「旧协议 Pong 通 + `GET /v1/join` 200」才算新旧客户端都能进，只通一条就是单边可用。
- **容器 access log 的 `remote_ip` 全是网桥网关（如 `172.18.0.1`）不代表「没人从外网来过」**：Docker 发布端口会 SNAT，
  LAN 与 WAN 长得一样。判「外网到底通没通」只能靠外部探测/代理出口测，不能靠日志。

## 回滚

EaglerXPaper：停服 → 删 `plugins/EaglerXPaper*.jar`（配置目录可留）→ 启动，Java 入口零改动。
Velocity 方案：`velocity.toml` 恢复 + Paper 端口改回 + 转发密钥置空 → 重启，先备份实例目录。
