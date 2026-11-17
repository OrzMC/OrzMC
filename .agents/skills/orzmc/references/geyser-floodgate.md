# Geyser 基岩支持运维笔记

> 用途：基岩版玩家（手机/PE/Win10 版）通过 Geyser 进 Java 服。
> ⚠️ **当前模式（2026-08-05 起）**：三端均为**离线服 + Geyser offline 直连**，**未装 floodgate**。基岩玩家以**无前缀名字**直连（Geyser 生成随机离线 UUID），行为与 Java 玩家一致。

## ⚠️ floodgate 回退记录（2026-08-05，勿再装）

**floodgate 与 LoginSecurity 冲突，三端已回退**：
- floodgate 给基岩玩家加 `.` 前缀 → LoginSecurity `filter-special-chars` 判非法字符**拒绝登录**
- 基岩玩家走 LoginSecurity 注册（无前缀名字），floodgate 无收益纯冲突
- 回退动作：**删 floodgate.jar** + Geyser `auth-type: offline`（离线服基岩玩家无前缀直连，与 Java 玩家一致）
- 回退后验证：floodgate 日志 0 行；Geyser 正常 Enabling + UDP 19132 监听

> 📌 若未来换掉 LoginSecurity 或改前缀方案，才考虑重新评估 floodgate。

## 渠道铁律：官方下载站优先（用户拍板 2026-08-05）

**Geyser 安装/更新一律走官方下载站 `download.geysermc.org`**——Hangar/Modrinth 平台相对更新更慢，可能落后多个版本/缺失 spigot 平台版。

| 组件 | 官方渠道 | Hangar | Modrinth |
|:--|:--|:--|:--|
| Geyser | ✅ `download.geysermc.org` | 有（但慢）| 有（但慢）|
| Floodgate | ✅ `download.geysermc.org`（唯一正确）| ⚠️ **2023-03 停更** | ❌ **只有 fabric/neoforge，无 spigot** |

**查最新版 + 下载（官方站 API）**：
```bash
# 1. 查最新版本/构建
curl -s https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest
# 2. 下载 spigot 平台版（= Paper 兼容）
curl -sL -o Geyser-Spigot.jar "https://download.geysermc.org/v2/projects/geyser/versions/<版本>/builds/<构建>/downloads/spigot"
```

## 当前版本（2026-08-22 更新）

| 组件 | 版本 | 部署方式 |
|:--|:--|:--|
| Geyser-Spigot | **2.11.2-b1230**（基岩 26.0-26.45） | 本地 Paper+Folia 已部署（2026-08-22）；Exaroton jar 已传 `plugins/update/` 待下次启动生效；MCSM 待查 |

- 版本号带 `-SNAPSHOT` 是 GeyserMC 下载站的正常命名（build 号才是关键）
- sha256 校验：Geyser-Spigot 2.11.2-b1230 = `b754bb257976549553239be82c4b1a8ca97bac997c8799fdee5a28a287e7fda6`（19,662,581 字节）
- 升级路径（PaperMC update 机制）：新 jar 放 `plugins/update/` → 重启原子替换，update/ 自动清空
- 升级方式差异：**在跑服**走 update/ + 重启（如本地 Paper）；**停服端**可直接替换 plugins/ jar（如本地 Folia）；**Exaroton** 运行中禁止写文件 → OFFLINE 时上传 update/（PUT 裸字节 + UA，>10MB 可能 524 重试即可）

## 升级后连通性测试（必做！2026-08-22 老板定：每次 Geyser 升级后自动执行）

升级 Geyser 后（任一端）必须跑**双通道连通性测试**，全部 PASS 才算升级完成：

1. **Java 通道**：`python3 ~/.hermes/skills/gaming/orzmc/scripts/mc_ping_probe.py <host> [port]`（默认 25565）
   - ✅ 判据：TCP 连通 + MC 握手返回版本/MOTD/在线人数
2. **基岩通道**：`bash ~/OrzMC/proxy/scripts/bedrock_host_check.sh [host] [port]`（远程探测传 host，端口默认 19132；本机模式省略参数）
   - ✅ 判据：RakNet Unconnected Pong (0x1c) + MOTD（MOTD 中协议号/版本 = 新版基岩支持证明，如 1230 返回 `2169;26.45`）
   - Exaroton 示例：`bash ~/OrzMC/proxy/scripts/bedrock_host_check.sh {SERVER_NAME}.exaroton.me 19132`
3. 双通道判据细节：基岩 MOTD 字段 `MCPE;名称;协议;版本;在线;上限;GUID;副标题;模式;1;端口`——协议号 2169 对应基岩 26.45；端口 19132 是 **UDP**（lsof 用 `lsof -iUDP:19132`）

## 验证流程

### 1. 加载验证
```bash
grep -iE "Enabling Geyser" <服务器>/logs/latest.log
# 期望: [Geyser-Spigot] Enabling Geyser-Spigot v2.11.1-SNAPSHOT
# 确认 auth-type: offline（Geyser/config.yml），floodgate 无加载行
```

### 2. UDP 端口验证
```bash
grep -iE "Geyser" logs/latest.log | grep -i "UDP"
# 期望: [Geyser-Spigot] 已在 UDP 端口 19132 上启动 Geyser
```

### 3. RakNet 握手测试（无需真机，脚本化）
推荐用 `~/OrzMC/proxy/scripts/bedrock_host_check.sh`（双模式：本机/远程，含端口监听+进程+防火墙检查，见 SKILL.md 索引「基岩版连通性诊断」）；简易版用 `scripts/regression/geyser_udp_test.py` —— 发 RakNet Unconnected Ping (0x01) 验证响应：
```bash
bash ~/OrzMC/proxy/scripts/bedrock_host_check.sh            # 本机五项检查
bash ~/OrzMC/proxy/scripts/bedrock_host_check.sh <host> [port]  # 远程探测
# ✅ 期望: 收到 Unconnected Pong (0x1c) + 服务器名
```
- 服务器名格式（RakNet MOTD）：`名称;协议;版本;在线数;上限;GUID;副标题;模式;1;端口`
- 端口 19132 是 **UDP**（不是 TCP）——lsof 查要用 `lsof -iUDP:19132`

## 三端部署差异

| 端 | Geyser 状态 | 升级方式 |
|:--|:--|:--|
| 本地测试服 | 2.11.2-b1230 ✅ UDP 19132 | 在跑服：update/ + 重启；停服端：直接替换 plugins/ jar |
| Exaroton | 2.11.2-b1230 ✅ UDP 19132（2026-08-22 已传 update/ 待下次启动生效；⚠️ config.yml bedrock port=19132，旧记录 39742 已过时） | **运行中禁止写文件**：OFFLINE 时 PUT 上传 update/ → 启动生效 |
| MCSM | 待查 | **运行中可写 update/**（上传不锁定）→ 重启生效 |

- ⚠️ MCSM 是 Windows 主机：日志路径反斜杠（`plugins\Geyser-Spigot.jar`），文件系统大小写不敏感
- ⚠️ 插件基线要求三端 sha256 一致（文件名相同≠内容相同）

## 联动效果（offline 直连模式）
- 基岩玩家以**无前缀名**进服（与 Java 玩家一致），LoginSecurity 可正常注册/登录
- Geyser 生成随机离线 UUID（跨会话稳定）
- LuckPerms 可按基岩玩家名授权限
- SkinsRestorer 正常服务基岩皮肤

## 坑
- **Hangar Floodgate 是旧版（2023）**——别从那下（官方站优先）
- **Modrinth 无 spigot 版**——别浪费时间（官方站优先）
- **更新勿等 Hangar/Modrinth 推送**——它们比官方站慢，Geyser 一律官方站查版本
- ⚠️ **勿装 floodgate**（2026-08-05 回退原因见顶部）——除非 LoginSecurity 方案变更
