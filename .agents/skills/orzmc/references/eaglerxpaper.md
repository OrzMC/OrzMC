# Eaglercraft 接入的第二种形态：EaglerXPaper（Paper 插件，无需代理）

> 用于回答“生产能不能不加 Velocity 就支持网页客户端”。测试服是 Velocity + EaglerXServer（见 `nethernet.md` / `SKILL.md`）；生产定型走的是 EaglerXPaper。

## 1. 项目事实（2026-11-16 核实）

| 项 | 值 |
|:--|:--|
| 仓库 | `PlanetDogeCodes/EaglerXPaper`（BSD-3，单人维护，star 20+，2026-11 仍在提交） |
| 版本 | `v1.1.1-S2`，产物 `EaglerXPaper-v1.1.1-Stable2.jar`（8.7 MB） |
| 身份 | `plugin.yml` 里 `name: EaglercraftXServer`、`api-version: 1.13`、softdepend 仅 SkinsRestorer；配置目录 `plugins/EaglercraftXServer/`，与上游同名 |
| 支持 | Paper 1.12.2–1.21.11+；声称到 26.x，**实测只到 26.2**；26.x 需 Java 25+ |
| 硬依赖 | **ViaVersion + ViaBackwards 必须**；1.8 客户端另需 ViaRewind |
| 不支持 | Folia（所以测试服 survival 用不了）、作为 Velocity/Bungee 插件（那个用上游） |
| 机制 | 走 Paper 的 `ChannelInitializeListener` 注入 Netty 管道，按首包区分 HTTP/WS 升级与原生 MC 握手 |

## 2. 双栈配置语义（listeners.toml，与上游同结构）

```toml
inject_address = "0.0.0.0:25565"   # 必须等于 Paper 的 server-port（有代理时=代理 bind）
dual_stack = true                   # 默认 true；HTTP 首包→Eagler，其余→原生 Java
forward_ip = false                  # 无反代必须 false，否则缺 X-Real-IP 头直接拒连
forward_ip_header = "X-Real-IP"     # 有 Caddy 时 true 且头名要对上
spoof_player_address_forwarded = true
```

- **坑：`forward_ip=true` 时无 `X-Real-IP` 头的连接会被拒**。反代部署下本机 `curl http://127.0.0.1:25565/` 验不通属于预期，别当故障查。
- `inject_address` 与 Paper 实际绑定不一致 → 静默不生效（WS 一律超时，日志无报错）。
- `server.properties` 写 `server-ip=127.0.0.1` 会让双栈绑定退化成回环。

## 3. 没有 Caddy/nginx 时：插件自带 TLS

```toml
[listener_list.tls_config]
	enable_tls = true
	require_tls = true              # false = 同端口 ws 明文与 wss 并存（按首字节 0x16 判定 ClientHello）
	tls_public_chain_file = "fullchain.pem"   # 服务器证书 + 中间证书拼接，放在服务器工作目录
	tls_private_key_file = "privatekey.pem"   # 必须 PKCS#8（BEGIN PRIVATE KEY）
	tls_auto_refresh_cert = true              # 换证 60s 内自动重载
```

玩家地址 `wss://域名:25565/`，**不需要 443**，避开家宽/云主机 80/443 被封的问题。

证书来源排序：**云厂商免费 DV**（DNS 验证；腾讯云/阿里云免费证书现在**有效期只有 90 天**，不是一年）→ **lego/win-acme + DNS-01 自动续期** → LE HTTP-01（需 80 常驻）。三者都不需要开 80/443，DNS-01 只写 TXT 记录。

**先确认域名托管在哪**（决定用哪家的 DNS API）：`nslookup -type=NS <主域> 223.5.5.5` —— 回 `*.dnspod.net` = DNSPod/腾讯云（用 DNSPod 的 API 密钥，不是腾讯云 SecretId/Key）。

Windows 上最省心的自动续期是 **lego 单 exe + DNSPod 插件**（无依赖，产物本身就是可用的 PEM）：

```powershell
# DNSPOD_API_KEY = "<ID>,<Token>"（dnspod.cn 控制台 → 密钥管理）
$env:DNSPOD_API_KEY="..."
C:\mc\lego\lego.exe --path C:\mc\lego --email <邮箱> --dns dnspod --domains <子域名> --accept-tos run
# 产物：<子域名>.crt（已含完整链）+ <子域名>.key（PKCS#8）→ 直接当 fullchain.pem / privatekey.pem
# 续期：每天跑一次，剩 30 天内才真正续
C:\mc\lego\lego.exe --path C:\mc\lego renew --days 30 --renew-hook "<覆盖两个 pem 的命令>"
```

**两个格式坑**：① `fullchain.pem` 必须有两段 `BEGIN CERTIFICATE`（服务器证书 + 中间证书），云厂商 nginx 包通常已是完整链，打开确认一次；② 私钥必须是 PKCS#8（`BEGIN PRIVATE KEY`）。

**落地位置**：两个 pem 放**服务器工作目录**（与 `server.properties`、`plugins/` 同级，即 MCSM 实例根目录），不是 `plugins/EaglercraftXServer/` 里；`tls_auto_refresh_cert=true` 覆盖即生效。

**验签必须不带 `-k`**：`curl -i https://<域名>:25565/` 不报证书错误才算浏览器会认；`-k` 通只能证明「TLS 起来了」，不能证明信任链完整。

❌ 自签：网页客户端是 JS WebSocket，不能像打开网页那样点“继续访问”，基本连不上，只适合内网 `ws://` + `require_tls=false` 自测。
❌ Cloudflare **Origin** 证书：只有 CF 自己信任，浏览器不认（橙云代理也不支持 25565，Spectrum 才支持）。

```powershell
# 用云厂商 key 时的格式转换
openssl pkcs8 -topk8 -nocrypt -in old.key -out privatekey.pem
```

## 4. 与 Velocity 方案的取舍

| | EaglerXPaper | Velocity + EaglerXServer |
|:--|:--|:--|
| 改动面 | 1 个 jar（+可选证书） | Paper 挪内网端口 + MODERN 转发密钥 + 常驻代理进程 |
| 真实 IP | 直连天然真实 | MODERN 转发才有 |
| 维护风险 | 单人 fork、靠 NMS 反射名表，Paper 大改可能失效 | 上游 lax1dude 稳定 |
| Folia | ❌ | ✅ |

判断口径：生产只能人工维护（无 APIKey）时选 EaglerXPaper，回滚=删 jar 重启；一旦 fork 跟不上 Paper 升级，再切 Velocity 方案。

## 5. 生产（国内服）现状

- 主机 `{SERVER_HOST}`，Windows Server 2022 + MCSM，**API 长期 403，只能面板/远程桌面手动**。
- Paper 26.3 直连 25565（ping 版本串是 `Paper 26.3`，不是 `Velocity …` ⇒ 确实没有代理层），`online-mode=false`，Geyser-Spigot `both`（19132 tcp+udp + 19134 udp）。
- 2026-11-16 已于生产安装 EaglerXPaper，采用**插件自带 `tls_config`** 提供 `wss://域名:25565/`，不引入 Caddy/nginx。
- 风险点：生产同时装有 `packetevents 2.14.0` 与 `GrimAC`（内嵌 packetevents），与 EaglerXPaper 同抢 Netty 管道，是“登录后 Bad packet id / 偶发断连”的温床，升级 Paper 或插件前先灰度。
