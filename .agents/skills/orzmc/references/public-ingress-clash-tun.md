# 公网入口排障：域名/端口映射都配好了，外网就是连不上

> 2026-09-11~12 本机（Windows + Clash TUN + Docker Desktop WSL2 mirrored + MCSM 实例）实测定论。
> 结论先行：**问题常不在路由器/运营商，而在本机 Clash 的 TUN 抢了默认路由，把「入站连接的应答包」送进了代理隧道。**

> **2026-11-19 现状变更**：家宽**入站 443 已可进**，公网入口回到标准 443
> （`compose.site.yaml` 只留 `443:443`，`80` 与 `18443` 映射已删除，访问地址不再带端口）。
> 文中「80/443 被封、只能用 18443」是 2026-10-29 那次的实测结论，作为历史排障思路保留；
> **端口可用性每次都要重新实测**，不要拿旧结论当现状。

## 1. 症状特征（一套组合拳就能判定）

| 现象 | 说明 |
|:--|:--|
| 局域网内直连 `192.168.0.33:25565` **通** | 服务本身没问题 |
| 外网（手机蜂窝/check-host/mcsrvstat）**全超时** | 卡在入站这一跳 |
| 外网 **ICMP ping 通**、**TCP/UDP 全挂** | 包能到公网 IP，但转发后的应答回不去 |
| 本机跑 **Clash TUN 模式**（有 `198.18.0.0/15` 假 IP 网段） | 头号嫌疑 |
| 同一公网 IP 下**另一台设备**的服务（映射到别的机器）**外网可通** | 反证路由器/运营商没问题 |

⚠️ 在**本机**上测域名/公网 IP 全是假结果（Clash DNS 劫持成 `198.18.x.x`、默认路由走 TUN、路由器不支持 hairpin）。
必须从**外部节点**测：check-host.net（TCP/UDP 全球节点）、api.mcsrvstat.us（Java+基岩真实协议）、api.mcstatus.io（基岩）。

## 2. 根因链

```
Clash TUN 网卡(198.18.0.1) 默认路由 metric=1  <  Wi-Fi(192.168.0.33) metric=45
        ↓ 所以「本机发出的包」（包括入站连接的应答）走 TUN
入站 SYN 到达 192.168.0.33:25565（抓包可见 eth4 In）
        ↓
应答包按默认路由进 TUN：Java 的 SYN-ACK 钻隧道、基岩 pong 源地址被定成 198.18.0.1
        ↓
客户端收不到正确来源的应答 → 超时（所以「内网通、外网不通」）
```

抓包定位（WSL 内，`tcpdump -n -i any`）：
```
eth4  In  IP <外网IP> > 192.168.0.33.25565: Flags [S]     ← 入站正常
eth0  Out IP 192.168.0.33.25565 > <外网IP>: Flags [S.]    ← 应答从 TUN(eth0) 走了 ✗
```

## 3. 修复：通用策略路由（按源地址，与端口无关）

原理：让应答包在**第一次查路**时就用 LAN 出口 + LAN 源地址，完全不依赖 NAT。

```bash
ip route replace default via 192.168.0.1 dev eth4 src 192.168.0.33 table 101
ip route replace 192.168.0.0/24 dev eth4 src 192.168.0.33 table 101
ip rule add from 192.168.0.33 table 101 pref 85          # 通用：任意端口
ip rule add ipproto tcp sport 25565 table 101 pref 90    # 兜底：已知端口
ip rule add ipproto udp sport 19132 table 101 pref 90
```

⚠️ **不要用 table 100**：WSL mirrored 栈自带 `100: from all fwmark 0x9 lookup 100`（非本脚本添加），该表归 WSL/HNS 管。用**私有表 101**（`ORZMC_TABLE` 可改）。

`from <LAN IP>` 的语义 = **所有监听在 LAN IP 上的服务（容器发布端口、宿主服务，任意端口）**的应答都走 Wi-Fi 正门；Clash 代理流量源地址是 `198.18.x` → 不受影响（实测：加规则后出站出口 IP 仍为 Clash 出口，代理未破坏）。**→ 以后新增任何自定义端口都不需要再改这一层。**

验证路由决策（不需要外部客户端）：`ip route get 1.1.1.1 from 192.168.0.33 ipproto tcp sport 40000` → 应 `via 192.168.0.1 dev eth4 table 101`。

⚠️ 区分：`from` 规则管的是**源地址**（服务应答），因此对 Windows 宿主服务同样适用（mirrored 共享网络栈）；而 `iptables -j MARK` 方案只能改出口、**改不了已被 TUN 定死的源地址**，UDP 会因此失效。

脚本（幂等、自带 `--check` 自愈）: `scripts/orzmc-mc-reply-route.sh`
部署位置（本机）: `/usr/local/bin/orzmc-mc-reply-route.sh`（WSL Ubuntu 内）+ 规范副本 `E:/orzmc/scripts/orzmc-mc-reply-route.sh`
持久化（v4，2026-10-04 重做）: **主力 = WSL 内事件驱动自愈守护** `orzmc-mc-reply-route-watch.sh`（`ip monitor route rule addr link` → 发现路由缺失立即调主脚本修复，**亚秒级**，见 3b/3e）；**兜底 = Hermes cron job `orzmc-route-guard`**（`every 10m`、`no_agent`，脚本 `%LOCALAPPDATA%\hermes\scripts\orzmc_route_guard.py`，以 `CREATE_NO_WINDOW` 调 `wsl -d Ubuntu -u root -- bash /usr/local/bin/orzmc-mc-reply-route.sh`；成功静默、失败投递飞书），作用退化为「WSL 重启后把守护拉起来 + 低频校验」（主脚本每次 apply 都会 `ensure_daemon`）。

> ⚠️ **原 Windows 计划任务 `OrzMC-MC-Reply-Route` 已停用（Disabled，定义保留未删，动作已还原为直接 wsl.exe）**：它以 `InteractiveToken` 直接启动 `wsl.exe`（`repeat=PT1M`），**每分钟在桌面弹一个黑色控制台窗口约 1 秒**（wsl.exe 启动到 bash 跑完 ≈1.3s，与用户描述完全吻合）。
> 改法试过 wscript + `WScript.Shell.Run(cmd,0,False)` 隐藏包装：wscript **挂在 Run 上不退出**，任务卡 RUNNING（`LastTaskResult=267009`）+ `MultipleInstancesPolicy=IgnoreNew` → 后续触发全被忽略，**自愈静默失效**（比闪窗更糟）。
> 最终修法 = 把兜底搬进 Hermes cron（走 `CREATE_NO_WINDOW`，无窗口）+ 停用原任务。完整排查套路见技能 `hermes-windows-background-service` 的「桌面周期性闪现控制台窗口」一节。systemd 单元 `orzmc-mc-reply-route.service` 已备在 `scripts/`（写 /etc 需审批，故当前用 `setsid nohup` 常驻）。日志 `/var/log/orzmc-mc-reply-route.log` + `/var/log/orzmc-mc-reply-route-watch.log`。

### ⚠️ 3b. 自愈会「静默失效」：ip rule 活着、策略路由被清掉（2026-10-04 三次复发，机制已定位）

**症状**：内网直连 25565/19132 正常，外网 Java/Bedrock 全部超时；计划任务 `LastTaskResult=0`（看起来一直在成功自愈）。

**根因**：`ip rule`（from/sport 规则）与 table 100 的路由**生命周期不同**——路由会丢、规则不会。旧脚本 `need_apply()` 虽能发现路由缺失，但**应用后不校验**：`ip route replace` 失败（网卡/命名空间瞬态异常）时 `ip rule add` 照样成功，脚本照旧 `exit 0` → 计划任务永远显示成功，自愈通道静默死亡。已用 `ORZMC_IFACE=eth9` 伪造场景复现出完全相同的「有规则、无路由」残局。

**一条命令判定**：`ip rule show | grep 'from <LAN IP> lookup 101'`（有）但 `ip route show table 101`（空）→ 就是这个。**再看守护日志 `tail -5 /var/log/orzmc-mc-reply-route-watch.log`：正常应能看到 `HEAL …校验通过`（每次抖动一条），若长时间空白说明守护没在跑。**

**根因（2026-10-04 v4 机制级定位，带时间戳 netlink 实证）**：宿主 **Hyper-V VmSwitch 在周期性重建 WSL 的虚拟网卡**（Windows 事件源 `Microsoft-Windows-Hyper-V-VmSwitch` 事件 ID 291，时间戳与每次抖动逐次对齐；由 Docker/HNS 端口活动驱动），客机 `eth4` 的地址被「删除 → 约 1 秒后重加」：

```
14:06:16  Deleted 7: eth4    inet 192.168.0.33/24 brd 192.168.0.255 scope global noprefixroute eth4
14:06:17  7: eth4    inet 192.168.0.33/24 ...                 ← 1 秒后重加
14:06:29  Deleted 7: eth4    inet 192.168.0.33/24 ...          ← 12 秒后第二次抖动
14:06:30  7: eth4    inet 192.168.0.33/24 ...
```

内核在地址被删时**连带清除所有引用该地址/网卡的策略路由**（实测 table 100 与 101 表现完全相同、**带不带 `src` 都照样死**），而 `ip rule` 不引用网卡 → 规则留存。抖动间隔 12 秒~2 分钟随机，**不可阻止**（WSL mirrored 的网卡同步是宿主驱动的）。→ **改表号、去掉 src、换网卡名都救不了；每分钟轮询也必然留下最长 60 秒的洞。**

**v4 修法：事件驱动自愈守护（亚秒级）**
- `scripts/orzmc-mc-reply-route-watch.sh`：`ip monitor route rule addr link | while read` → 每个 netlink 事件先跑 `--check`，缺了才修；修完 2 秒静默期防「修复动作自激」；启动即修一次；日志只记 `DETECT / APPLIED / HEAL / FAIL`（`/var/log/orzmc-mc-reply-route-watch.log`）。
- 部署：`E:/orzmc/scripts/*.sh` 三副本同步（E 盘源 → WSL `/usr/local/bin`（`cp`+`chmod +x`）→ Hermes 技能 `scripts/`）；启动 `setsid nohup /usr/local/bin/orzmc-mc-reply-route-watch.sh &`；主脚本 apply 路径 `ensure_daemon` 会自动拉起（`ORZMC_NO_DAEMON=1` 可禁用）。
  ⚠️ **存活判定必须用 pidfile + `kill -0`，不要用 `pgrep -f <脚本名>`**：任何命令行里含该字符串的进程都会被匹配（实测 `pkill -f` 会把自己的排查 shell 一起杀掉；`pgrep -cf` 会虚报 6 个"实例"）。watcher 用 `flock` 保证单实例，pidfile `/run/orzmc-mc-reply-route-watch.pid`（/run 随 distro 重启清空，天然避免陈旧 pid）。
  ⚠️ **`ensure_daemon` 必须排在「已就位就 `exit 0`」之前**：否则路由正常、守护已死时任务直接退出，永远拉不起来。
- 自检与排障工具（全在 `scripts/`）：`test-daemon-chain.sh`（四条链路验证：--check 不误启 / apply 拉起 / 不重复实例 / 清表后秒级修回）、`status-check.sh`（守护存活+HEAL 计数+表+规则一屏速查）、`cleanup-probe.sh`（清一次性探针进程）、`route-survive-probe.sh`、`netmon-arm.sh`。
- 实测效果（2026-10-04）：抖动于 14:06:16 / 14:06:29 两次，守护分别 **14:06:18 / 14:06:31** 修复（≤1 秒）；随后 14:10:55 / 14:11:41 / 14:12:35 外部探测 Java+Bedrock 连续 `online:true`。
- 复现/排查工具（**下次先看日志，别从零取证**）：`scripts/route-survive-probe.sh`（每 5 秒快照 表内容/eth4 地址/main metric → `/tmp/route-survive.log`）+ `scripts/netmon-arm.sh`（**带时间戳**武装 netlink → `/tmp/netmon2.log`）。

**v2 脚本修复（已部署 E:/orzmc/scripts → WSL /usr/local/bin 与 Hermes 技能副本，三处 md5 一致）**：
- 应用后**自校验**（table 100 含 `src <LAN IP>` + from 规则 + 每条 sport 规则），最多重试 3 次；失败 `exit 1` + 日志，计划任务 `LastTaskResult≠0` 可见。
- **自动探测** LAN 网卡/网关/本机 IP（从 main 表里排除 `198.18.0.0/15` 的默认路由取），不再硬编码 `eth4`/`192.168.0.33`——换 Wi-Fi/换网段/换机不再需要改脚本；`ORZMC_IFACE/ORZMC_GW/ORZMC_SIP` 仍可覆盖。
- 日志 `/var/log/orzmc-mc-reply-route.log`（`OK 已就位` / `DETECT 需要修复` / `APPLIED … 校验通过` / `FAIL …`）。
- 自测方法：`ip route flush table 100` → 跑脚本应打印 `DETECT`+`APPLIED …校验通过`；`--check` 此时应输出 `MISSING:` 并 `exit 1`。

### 3c. 排障顺序（2026-10-04 定稿，照这个走 10 分钟出结论）

1. **服务在不在**：`wsl -d Ubuntu -u root -- ss -lntup | grep -E '25565|19132'`（宿主 Windows `netstat` 在 mirrored 模式下**看不到**容器发布端口 → 别据此判「没监听」）。
2. **路由层有没有坏**：`ip rule show | grep 101` vs `ip route show table 101`；守护在不在：`pgrep -af orzmc-mc-reply-route-watch` + `tail -5 /var/log/orzmc-mc-reply-route-watch.log`（见 3b）。
3. **入站到没到**：WSL 内 `nohup timeout 60 tcpdump -n -i eth4 -l 'tcp port 25565 or udp port 19132' > /tmp/cap.txt &`，再从外部触发探测；看 `eth4 In` 有没有包、应答源地址是不是 `192.168.0.33` 且从 eth4 出。**入站有 + 应答正常 = 本机没问题**。
4. **外部多节点**：`check-host.net/check-tcp?host=域名:端口`（Node 命名空间直接看结果）+ `api.mcstatus.io`。
5. **DDNS/公网 IP**：`dev.{SERVER_NAME}.cn → CNAME home.{SERVER_NAME}.cn → CNAME wangzhizhou.kmdns.net → A <公网IP>`；用 DoH 取真实 IP（`223.5.5.5/resolve?name=dev.{SERVER_NAME}.cn&type=A`），本机 `ping/nslookup` 只会给 Clash 假 IP `198.18.x.x`。抓到入站包即证明 DDNS/路由器映射都正常。

### 3d. 防火墙三条规则已存在（核对用，别重复加）
`OrzMC Java 25565 TCP` / `Bedrock Geyser 19132 UDP`（另 25566/19133）均为 `Allow / Any`，`Get-NetFirewallRule -Direction Inbound -Enabled True` 可查。

### 3f. TUN 模式下的**长连接**故障：WebSocket 1006 / 登录反复掉线（2026-11-19）

**症状**：开了 Clash Verge，外部客户端能连上但很快断——日志里是 WebSocket `1006`（异常关闭，无关闭帧），面板/网页客户端表现为「反复掉线、重新登录」；关掉 Clash 即全部正常。短请求（HTTP GET）看不出问题，只有长连接发作。

**判定（30 秒）**：
1. `netsh interface show interface` 有 `Mihomo` 虚拟网卡 → TUN 开着。
2. `nslookup mcs.{SERVER_NAME}.cn` 返回 `198.18.x.x` → DNS 被 TUN/fake-ip 劫持（真实应是家宽公网 IP）。
3. 核心 API `GET /connections` 里出现形如 `{HOME_IP} <客户端源端口>` 的条目 → **入站连接也被塞进了 mihomo 的 gVisor 用户态栈**（`DIRECT` 也一样）：短请求能跑通，长连接在 gVisor TCP 代理里蹲不稳 → 1006。

**不要指望 `tun.route-exclude-address` 能救**：它按**目标地址**匹配，而入站应答的目标是任意外网客户端 IP，永远命中不到。Windows 也没有 `ip rule` 那种按源地址的策略路由，所以宿主侧没法「只把应答绕开 TUN」。

**正确修法（按优先级）**：
1. **这台机器不要用 TUN 模式**——它是公网入口宿主。日常浏览器/`gh`/`git` 用系统代理 + 规则模式（`127.0.0.1:7897`）就够了，做法见 3g。
   ⚠️ **改 `verge.yaml` 的 `enable_tun_mode` 不持久**：Verge 启动时会用内存里的状态重写该文件，实测改完 `false`、重启后又被写回 `true`。持久化只有两条路——**在 Verge 界面里手动关掉 TUN 开关**（唯一真正落盘的路径），或加一条守护每分钟检查并关回去。别只在文件里改一次就以为解决了。
2. 临时关 TUN **不需要管理员**：核心的控制接口在命名管道上（`\\.\pipe\verge-mihomo-production-<hash>`，用 `os.listdir("\\.\\pipe\\")` 找名字），直接发 HTTP：`PATCH /configs {"tun":{"enable":false}}` → `204`，3 秒内 `Mihomo` 网卡消失。`GET /version` 可先验通道（返回 `{"meta":true,"version":"v1.19.33"}`）。注意 `/connections` 是 chunked 响应，手写管道客户端要去掉 chunk 头。
3. **WSL 侧策略路由补上 443**：`scripts/orzmc-mc-reply-route.sh` 的 `TCP_PORTS` 默认值已改为 `25565 25566 25567 443`、`UDP_PORTS` 加 `24454`，即使 TUN 被重新打开，Caddy（容器内发布 443）的应答也优先走 `table 101` 从 Wi-Fi 正门出。三处副本要 md5 一致：`E:/orzmc/scripts` → WSL `/usr/local/bin` → Hermes 技能 `scripts/`；改完跑一次主脚本触发 `APPLIED`（守护会自行修复）。
4. 杀掉 `verge-mihomo.exe` 需要管理员（它以 `clash_verge_service` 服务身份运行，`taskkill /F` 报拒绝访问）；关 TUN 通常已经够用，不必提权。

### 3g. 关掉 TUN 后，如何保住浏览器 / gh / git 的外网访问

关 TUN 不损失代理能力：核心仍在 `127.0.0.1:7897` 监听（mixed 端口），只是不再接管系统路由。两条通道各自配置：

1. **浏览器 = 系统代理（WinINET）**：置 `ProxyEnable=1` + `ProxyServer=127.0.0.1:7897`，**再调一次刷新通知**已运行的进程（只写注册表不刷新，浏览器可能继续用旧设置）：
```python
import winreg, ctypes
k=winreg.OpenKey(winreg.HKEY_CURRENT_USER,r"Software\Microsoft\Windows\CurrentVersion\Internet Settings",0,winreg.KEY_ALL_ACCESS)
winreg.SetValueEx(k,"ProxyEnable",0,winreg.REG_DWORD,1)
winreg.SetValueEx(k,"ProxyServer",0,winreg.REG_SZ,"127.0.0.1:7897")
w=ctypes.WinDLL("wininet"); w.InternetSetOptionW(None,39,None,0); w.InternetSetOptionW(None,37,None,0)
```
2. **命令行 = 用户级环境变量**（`setx`，永久、免管理员）：`HTTPS_PROXY`/`HTTP_PROXY=http://127.0.0.1:7897`，`NO_PROXY=localhost,127.0.0.1,::1,192.168.0.0/16,.{SERVER_NAME}.cn,<公网IP>`——不排本地网段/自家域名会回环。libcurl/git/gh 认 `NO_PROXY`，所以**不要**再写 `git config --global http.proxy`（写了会绕过 NO_PROXY，把自家域名也送进代理）。`setx` 只对之后启动的进程生效，已开的终端要重开。

**验收三条**：`Invoke-WebRequest https://github.com` 200（这条走系统代理，等价浏览器路径）；`gh api user --jq .login` 返回账号；自家域名 `curl` 仍是 0.0x 秒级（证明 NO_PROXY/规则直连生效）。TUN 开着时同样域名是 0.5s 级——**这组延迟对比就是 TUN 开销的量化证据**，报障时直接给数字。

**坑**：
- 在 Verge 里关 TUN 时它常把**系统代理也一起关掉**（`ProxyEnable` 变 0，浏览器裸连），所以每次动过 Verge 设置都要复查这一项。
- 系统代理指向 7897 ⇒ **退出 Verge/核心 = 浏览器立刻 `ERR_PROXY_CONNECTION_FAILED`**；Verge 必须常驻（界面关掉、核心留着也行）。

## 4. 走过的弯路（别重复）

| 尝试 | 结果 |
|:--|:--|
| `iptables -t mangle -j MARK` + `ip rule fwmark` | 只改了出口网卡，**源地址仍被 TUN 定死**（源选择发生在打标前的首次查路）→ Java 能好、UDP 不行 |
| `-t nat POSTROUTING -j SNAT --to-source 192.168.0.33` | 计数在涨但包在内核里消失（nat 后无输出）→ 弃用 |
| 直接 `ip rule add sport 19132 ...` | 语法错，须写成 `ip rule add ipproto udp sport 19132 ...` |
| 在**本机**测公网域名/端口 | 全是假结果，必须用外部节点 |

## 5. 验证

```bash
# 外部实测（必做）
curl -s 'https://api.mcsrvstat.us/3/<域名或IP>:25565'        # Java → online:true + MOTD
curl -s 'https://api.mcsrvstat.us/bedrock/3/<IP>:19132'      # 基岩 → online:true
curl -s 'https://api.mcstatus.io/v2/status/bedrock/<域名>:19132'
# 抓包确认应答从 eth4 出去且源地址 = LAN IP
wsl -d Ubuntu -u root -- bash -c "tcpdump -n -i any 'tcp port 25565'"
```
⚠️ mcsrvstat 有缓存（30min 级）与偶发解析抖动：同一端口可能「域名形式 False / 裸 IP 形式 True」→ **至少两源交叉验证**（mcsrvstat 裸 IP + mcstatus.io）再下结论。

⚠️⚠️ **2026-10-04 实测：mcsrvstat.us 会误报 False，不能当首选判据**——同一时刻 `api.mcstatus.io` 双通道 `online:true`、`check-host.net` 6 个全球节点 TCP 全部 OK，而 mcsrvstat 的 java/bedrock 都报 False；同时在 WSL 抓包（`tcpdump -i eth4 'tcp port 25565 or udp port 19132'`）**看不到 mcsrvstat 的探测包到达**（只看到 mcstatus.io 的 RakNet ping/33B 与 SYN 到达，且我们的应答确实从 `192.168.0.33` 经 eth4 发出）。→ 结论：该源自身探测链路/缓存有问题。**判据优先级：本机抓包（入站+应答源地址）= 决定性的；其次 check-host.net TCP/ping 多节点 + mcstatus.io（Java/Bedrock 双协议）；mcsrvstat 仅作参考。**

## 6. 与端口映射的关系

- 路由器「虚拟服务器」规则 + Windows 防火墙 Allow 规则是**必要**的，但不是充分条件——本机 Clash TUN 不修，映射再对也连不上。
- 基岩无 SRV，玩家必须手填端口；`cloudflared` 隧道**不支持 UDP**，基岩没法走隧道（要走就用 frp/playit.gg）。

## 7. 老板决策（2026-09-12）：新端口要不要免配置

- **防火墙 / 路由器：坚持逐端口配置**（老板原话：「按单端口配置安全一些，需要时再加」）→ **不要再建议 DMZ 主机或端口段映射**（曾提议 A/B 方案被否）。
- **WSL 策略路由层：已用通用 `from <LAN IP>` 规则**，零维护（新增端口不用改这里）。
- 所以新增一个自定义端口的完整流程 = ①路由器加一条映射 ②Windows 防火墙加一条 Allow ③MCSM 实例 `docker.ports` 加一条 —— 共三处，路由层不用动。
- 验收记录：2026-09-12 老板手机蜂窝实连 Java 双实例（25565/25566）+ 基岩双实例（19132/19133）均连通 ✅。

## 8. 家宽入站 80/443 被运营商封锁 → 改用高位端口（2026-10-29 实测，OrzMC 现行架构）

**结论**：北京联通家宽**入站 80/443 被静默丢弃**（连路由器都收不到），高位的 18443 正常。
所以 web 面板不能走 443，只能映射高位端口到容器 443。

**现行拓扑**（已弃用 Cloudflare Tunnel，`orzmc-tunnel-guard` cron 已删）：

```
公网 114.x.x.x:18443 ──路由器映射──> 宿主 192.168.0.33:18443 ──> Caddy(容器 443)
                                                    ├─> mcsmanager-web:23333   (mcs.{SERVER_NAME}.cn)
                                                    └─> easybot:8080           (easybot.{SERVER_NAME}.cn)
```

- compose：`E:/orzmc/compose.site.yaml` 的 `caddy` 服务，ports `80:80` / `443:443`（保留但公网不可用）/ **`18443:443`（实际入口）**
- Caddyfile：`E:/orzmc/site/Caddyfile`；证书 Let's Encrypt **DNS-01**（镜像 `caddybuilds/caddy-cloudflare`，`.env` 的 `CF_DNS_API_TOKEN` 需 `Zone:DNS:Edit`）→ 不依赖入站 80 验证，端口被封也能签
- 防火墙：`OrzMC-Web-TLS` = 入站 TCP `80,443,18443` Allow，全 profile
- 面板 23333 只对 LAN 放行，公网只走 Caddy 一条入口
- 最终地址：**`https://mcs.{SERVER_NAME}.cn:18443/`**（证书对域名有效，与端口无关）

### 判据：refused 与 timeout 不是一回事

| 外部探测结果 | 含义 |
|:--|:--|
| `Connection refused` | 路由器直接 RST = **没有这条端口映射** |
| `Connection timed out` | 包被静默丢弃 = **运营商封锁**（80/443）或映射到了不响应的内网主机 |
| 连通 + 时间 < 1s | 正常 |

用这一对现象可以区分“映射没加”和“被运营商封”，比反复改路由器有效得多。

### 两个会让排查翻车的坑

1. **hairpin 假阳性**：在局域网内打开 `https://mcs.{SERVER_NAME}.cn` 会成功（路由器 NAT 回环），看起来像公网可达。Caddy 访问日志里**所有请求的 `remote_ip` 都是 `172.18.0.1`（Docker 网关）**，因此日志也无法区分 LAN 与公网来源。→ **判断公网可达只能靠外部节点**（check-host.net 多节点 + SSL Labs `api.ssllabs.com/api/v3/analyze?host=...`，后者报 `Unable to connect to the server` 即不可达）。
2. **家宽 IP 会随 PPPoE 重拨变化**（实例：`{HOME_IP}` → `{HOME_IP}`）。拿旧 IP 去测会得到“503/超时”这种完全误导的结论——**排查前先 `curl http://ip.3322.net/` 取当前 WAN IP**，并核对 `nslookup`/DoH 的 A 记录（本机解析被 Clash 劫持成 `198.18.x` 假 IP，要用 `https://1.1.1.1/dns-query` 取真值）。

### 延迟结论（取代旧 TTFB ≈ 3×RTT 模型）

直连 Caddy 只有一跳，TTFB ≈ 客户端到家的 RTT，不再有「TLS + 边缘 + 回源」三段叠加；国内访问 10–30ms 级，海外 150–300ms 级。原 Cloudflare Tunnel 的 0.7s 地板结构性问题已消除。

## 9. 「已弃隧道」≠ 已弃：通配橙云把漏网子域静默接进隧道

**症状**：同机自建服务（容器发布 `8080`）访问明显慢——首字节 2~3 秒、静态资源同样慢、`cf-cache-status: HIT` 也照样慢；同一容器走局域网直连毫秒级。

**根因**：`*.{SERVER_NAME}.cn` 在 Cloudflare 有一条**通配橙云记录**（`CNAME <tunnel-id>.cfargotunnel.com` + `proxied=true`）。凡是**没有单独写显式记录**的子域都命中通配 → 请求先进 Cloudflare 边缘 → 再经隧道回源，比同机直连多出「边缘排队 + 隧道 + 回源」三段。

### 9a. 入口阶梯量法（5 分钟定性，别从容器查起）

同一时刻并排测五条路径，量级差在哪段就归因在哪段：

| 路径 | 实测档位 | 含义 |
|:--|:--|:--|
| `127.0.0.1:<发布端口>`（宿主源站） | 0.01–0.03s | 容器/应用本身 |
| `http://<LAN_HOST_IP>:<发布端口>` | 0.003s 级 | 局域网一跳 |
| 同机已走 Caddy 的子域 `:18443` | 0.04–0.08s | Caddy 直连基线（对照组） |
| 出问题的域名（灰云直连后） | 同基线 | 期望值 |
| 出问题的域名（命中通配隧道） | **1.9–3.1s** | 慢在这里 = 入口 |

orzmusic 实测即上表（源站 0.01–0.03s / 局域网 0.003s / 隧道域名 1.9–3.1s / 同机 18443 0.04–0.08s）→ **慢 30~80 倍全在入口**，容器、前端、DB 一概无关。

```bash
# 一律带 -w 量化，别用「感觉慢」
for u in "http://127.0.0.1:8080/api/health" "http://<LAN_HOST_IP>:8080/api/health" \
         "https://mcs.{SERVER_NAME}.cn/" "https://music.{SERVER_NAME}.cn/api/health" \
         "https://music.{SERVER_NAME}.cn/api/health"; do
  curl -sk -o /dev/null -w "%{http_code} %{time_total}s  $u\n" "$u"
done
```

### 9b. 判定它在不在隧道里（DoH 取真值：本机解析被 Clash 劫持成 198.18.x）

```bash
curl -s -H 'accept: application/dns-json' 'https://cloudflare-dns.com/dns-query?name=<子域>&type=A'
```

| 解析结果 | 形态 | 结论 |
|:--|:--|:--|
| `A` = 家宽公网 IP（与 `curl http://ip.3322.net/` 一致） | 显式灰云 / 无代理 | ✅ 直连 |
| `A` = Cloudflare 边缘 IP（`104.x` / `172.67.x` 等）且 CNAME 链含 `cfargotunnel.com` | 橙云 + 隧道 | ❌ 最慢 |
| `A` = Cloudflare 边缘 IP、CNAME 无隧道 | 橙云回源（家宽 80/443 被封，多半 52x） | ❌ 也不通/慢 |

**审计「还有哪些服务受影响」的标准答法**：把 **Caddyfile 的 site 块清单 + 各容器宿主端口 + DNS 已知子域**三份并起来，逐个 DoH 查后按上表归类。不要凭「我们早就改直连了」下结论。实战里 orzmusic（`music.{SERVER_NAME}.cn`）与 sticker 这类**没有单独 site 块**的服务都是通配受害者 —— **是不是受害者只看 DNS 记录，与业务是什么无关**。

### 9c. 修法（两条，缺一不可）

1. **DNS 加显式灰云记录**：该子域建 `A`（或灰云 `CNAME`）指向家宽 IP，**关闭代理**。显式记录优先于通配，通配本身不必动（动了会牵连其它子域）。
2. **Caddy 加 site 块按 SNI 分流**，复用已映射的 `18443`（不要新开公网端口：家宽 80/443 被封，每多一个端口就多一条路由器映射 + 防火墙规则）：

```caddyfile
music.{SERVER_NAME}.cn:18443 {
    reverse_proxy orzmusic:8080
}
```

```bash
# 容器不在 Caddy 同一 docker 网络时先连上（按服务名反代的前提）
docker network connect orzmc_default <应用容器>
docker restart orzmc-caddy
```

访问改走 `https://<子域>:18443/`（证书对域名有效，与端口无关）；局域网内直接用 `http://<LAN_HOST_IP>:<发布端口>`。

### 9d. 验收

```bash
# 1) DNS 已是灰云：解出的是家宽 IP
curl -s -H 'accept: application/dns-json' 'https://1.1.1.1/dns-query?name=<子域>&type=A'
# 2) 本机 SNI 直连 18443（不能用 -H Host：TLS 看 SNI，会 exit 35）
curl -sk -o /dev/null -w '%{http_code} %{time_total}s\n' \
  --resolve <子域>:18443:127.0.0.1 https://<子域>:18443/api/health
# 3) 外网节点复核（本机测域名会被 Clash / hairpin 弄成假结果）
```

判据：`time_total` 落回 Caddy 直连档（0.0x 秒级）才算修好；仍 1s+ 说明 DNS 未生效（看 TTL、多解析器交叉）或仍命中通配。

### 9e. 纪律

- **新建任何自建服务子域后立刻 DoH 查一次**：通配橙云会把它静默接进隧道，等「感觉慢」再查要绕一大圈。
- **「慢」的第一分诊永远是入口阶梯，不是容器**：源站毫秒级 + 域名秒级 = 入口问题，此时查容器 CPU、日志、DB 索引全是白费；静态资源 `cf-cache-status: HIT` 仍慢同样证明延迟在链路。
- **别把「已弃隧道」当既成事实沿用**：弃的是**入口路由**（Caddy 接管 18443），DNS 层的通配橙云记录仍在，两者是两件事。
