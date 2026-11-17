# Local 后端：本机服务器操作

> 适用：本机目录部署的 PaperMC 服务器（`PAPER_BACKEND=local`，`PAPER_DIR` 指定目录）。
> 适配器：`scripts/adapters/local.sh`（create / upgrade / status / logs / command）。
>
> ⚠️ **2026-09-03 迁移标注**：本机 OrzMC 测试服（原 `~/minecraft-server`/`~/folia-test` 裸跑）已全部迁入 MCSM 本机栈 Docker 实例（mcs.{SERVER_NAME}.cn 面板管理），**不再用 local 后端启停**——本文档/local.sh 现仅适用于临时本机目录服（如一次性的 minecraft-server 实验目录）。MCSM 实例的数据仍在本机宿主（`/Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/<uuid>/`），jar 升级/插件部署可直接对实例目录操作后由面板重启实例（见 `testing.md`）。

## 版本获取（PaperMC 下载机制）

- ⚠️ **旧 API `api.papermc.io/v2` 已完全废弃（410 Gone / sunset）**——**不要再用 v2**
- **新下载机制（唯一正解）**：官网下载页 `https://papermc.io/downloads/paper` 内嵌每个构建的 sha256 → 直链 `https://fill-data.papermc.io/v1/objects/{sha256}/{jar名}` 下载
- `scripts/parse_papermc.py` 已封装：解析最新 STABLE 构建的 sha256 + 文件名
- **最新稳定版**（2026-08-15）：paper-26.2-112（111 与 112 行为可能不同；本地测试服 2026-08-15 已升 112）
- **Java 要求**：PaperMC 26.x 需要 Java 25

```bash
curl -s https://papermc.io/downloads/paper | python3 ~/.hermes/skills/gaming/orzmc/scripts/parse_papermc.py
# 输出: paper-26.2-111 ...（以实际输出为准，26.2-92 已过时）
```

## 创建服务器

```bash
PAPER_BACKEND=local PAPER_DIR=~/minecraft-server \
  ~/.hermes/skills/gaming/orzmc/scripts/adapters/local.sh create
```
创建动作：下载最新 jar → `eula.txt=true` → 生成 `server.properties`（参考配置）→ 生成启动脚本。

## 升级核心 jar

```bash
PAPER_BACKEND=local PAPER_DIR=~/minecraft-server \
  ~/.hermes/skills/gaming/orzmc/scripts/adapters/local.sh upgrade
```
升级动作：解析最新版 → 备份旧 jar（`backups/paper-{ver}-{build}.jar`）→ 下载新 jar（sha256 校验）→ 移除旧 jar → 同步 start.sh → 重启 → 验证日志出现 `Done`。已是最新时幂等处理（不删旧 jar）。

## 备份

```bash
PAPER_DIR=~/minecraft-server ~/.hermes/skills/gaming/orzmc/scripts/backup.sh
```
打包 world/ + plugins/ + server.properties 到 `backups/`，保留最近 24 份。

## 状态/日志/命令

```bash
PAPER_DIR=~/minecraft-server ~/.hermes/skills/gaming/orzmc/scripts/adapters/local.sh status
PAPER_DIR=~/minecraft-server ~/.hermes/skills/gaming/orzmc/scripts/adapters/local.sh logs 50
PAPER_DIR=~/minecraft-server ~/.hermes/skills/gaming/orzmc/scripts/adapters/local.sh command "say Hello"
```

## local 坑

- ⚠️ `local.sh command` 依赖 rcon/screen/tmux——**本机裸 java 进程（nohup）无控制台注入**，command 会提示「本机无 rcon 配置」。需要执行命令时：改配置文件后**重启**加载，或用其他方式（如直接改 whitelist.json + 重启）
- ⚠️ **运行时改 whitelist.json 不生效**（服务器缓存白名单）——必须重启或走 `whitelist` 命令
- ⚠️ macOS 无 `timeout` 命令（脚本/测试中不可用）
- ⚠️ macOS bash 3.2：`$var` 后接全角字符（如 `（`）会报 unbound variable，必须写 `${var}`

## 本机网络环境（Shadowrocket TUN，2026-08-13 实测）

- ⚠️ **本机装有 Shadowrocket（TUN 模式，虚拟网卡 utun3）接管全部流量**：`route get <ip>` 显示 interface=utun3
- ⚠️ **DNS 被 fake-ip 接管**：域名解析出 `198.18.0.x`（保留段）→ **真实 IP 必须公共 DNS 绕过**：`dig +short <host> @223.5.5.5` / `@8.8.8.8`
- ⚠️ **TUN 下 TCP/ICMP 延迟全是假象**：TCP 立即 ACK（0.4ms）、ICMP 本地响应（0.8ms）——测真实延迟需服务器在线后走 **MC 协议握手 RTT**（`scripts/mc_ping_probe.py`）
- ⚠️ **mc_ping_probe.py 已修 26.2 帧头兼容**（`data.find(b"{")` 定位 JSON 起点，勿再改回 `data[1:]`）；手写 status 脚本发 ping 包必须带长度前缀 `\x01\x00`（长度1+packet id 0），漏前缀服务器直接断连返回 0 字节（易误判服务器离线）
- ✅ **真实连通性验证法**：走实际数据流（MCSM API 列目录/下载文件成功 = 链路真实可用）；MC 握手 `JSONDecodeError` ≈ 服务器离线（TCP"通"是 TUN 假象）
- 系统 HTTP 代理端口 1082（scutil --proxy 可查）

## 性能参考（本机 i5-5257U）

- 1-3 人原版流畅；3-5 人可能掉 TPS
- 内存建议：`-Xms1G -Xmx2G`（1-3人）；view-distance=8，simulation-distance=6
- 启动参数模板见 `scripts/start-template.sh`
