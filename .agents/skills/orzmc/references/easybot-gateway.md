# EasyBot IM 网关运维（2026-08-11 从 easybot-gateway-ops 技能合并）

> 场景：排查/运维 EasyBot IM 网关（本机 docker，OrzMC 机器人接入）。所有 IM 网关相关问题先查本节。

## 概述
EasyBot（`ghcr.io/easyindie/easybot`）是统一 IM 网关：OrzMC 插件通过它接入 QQ/飞书/Telegram/Discord/微信。**2026-09-03 起迁移进 OrzMCDeploy compose 生产栈**（`~/Services/orzmc-deploy-0.0.3-dev/`，DATA_ROOT=`/Users/Shared/orzmc`）：容器 `orzmc-easybot`（EASYBOT_HOME=/var/lib/easybot → `$DATA_ROOT/easybot/data`），QQ+飞书 双 adapter，微信经 `$DATA_ROOT/easybot/data/gateway.local.yaml` 显式禁用；镜像 digest 锁定（≥0.0.35，schema v3 同旧版）。**旧独立容器 `easybot`（9090→8080，卷 easybot-data）已停删**（2026-09-03），其 gateway.db（17MB，api_keys/sessions/messages 9614 条）已迁移进新栈——插件旧 api_key 继续有效。栈管理用 `./orzmc.sh -d /Users/Shared/orzmc up|stop|status`；容器日志 `docker logs orzmc-easybot`。**（现状 2026-09-11：栈已迁本机 Windows，部署包 `/e/deploy/orzmc-deploy-0.0.3`，`./orzmc.sh -d E:/orzmc …`）**

**架构链路（2026-09-03 后）**：
```
OrzMC 插件 (easybot.yml) → https://easybot.{SERVER_NAME}.cn (Cloudflare Tunnel 5087fc61 → 容器) → 平台 adapter (QQ wss://api.sgroup.qq.com 等)
```
- 插件 easybot.yml：api_server `https://easybot.{SERVER_NAME}.cn` / ws_server `wss://easybot.{SERVER_NAME}.cn`（旧 `test-bot.{SERVER_NAME}.cn` 反代指向已删旧容器，2026-09-03 已全部切新入口）
- 新版本 API 变更（0.0.35+）：发送端点 `POST /api/v1/messages/send`（旧 `/api/v1/messages` 仅 GET 只读，POST 405）；插件 HttpSender 已适配 ✅
- easybot 容器只 expose 不发布宿主端口——**宿主 8080 是 orzmusic-app**！验证 API 走公网 `https://easybot.{SERVER_NAME}.cn`（带浏览器 UA）或 `docker exec`

## 快速健康检查
```bash
docker ps --filter name=orzmc-easybot          # Up (healthy)
curl -s https://easybot.{SERVER_NAME}.cn/api/v1/health   # 200（公网隧道链路；带浏览器 UA 防 CF 拦截）
docker logs orzmc-easybot --since 10m | tail    # 看 adapter 状态
# 插件侧：
# ⚠️ 2026-09-03 迁 MCSM 后：实例日志 = /Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/<uuid>/logs/latest.log（716c2fb7=Paper、8A932DD4=Folia）
grep -E "WebSocket|认证|重连" /Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/716c2fb712154c36ba5ab0f1480d3f87/logs/latest.log | tail
```
- 插件 `/bot` 输出 `enabled httpUnknown wsNotOk`：`httpUnknown` = HTTP 健康检查异步未完成（设计态黄色警示，**非 bug**）
- WS 正常 = 日志 `WebSocket连接建立` + `EasyBot WebSocket 认证成功`
- adapter 状态 API：admin login（`POST /admin/login {password}` → `key`）→ `GET /api/v1/adapters`（Bearer）；qq 应为 Connected+Healthy；飞书 Connected（无事件签名验证时 health=Degraded 属正常降级标记，发送验证为准）

## 机器重启后恢复清单（Mac 重启后按序执行）
```bash
open -a Docker                                   # 1. 启动 Docker Desktop
for i in $(seq 1 6); do docker info >/dev/null 2>&1 && break || sleep 2; done
cd /e/deploy/orzmc-deploy-0.0.3 && ./orzmc.sh -d E:/orzmc up   # 2. 起整个 orzmc 栈（幂等；容器 restart: unless-stopped 也会自启）——Windows 现役路径；旧 Mac: ~/Services/orzmc-deploy-0.0.3-dev + /Users/Shared/orzmc
docker ps --filter name=orzmc-easybot            # 3. 确认 orzmc-easybot Up
curl -s https://easybot.{SERVER_NAME}.cn/api/v1/health      # 4. 期望 200 + QQ/飞书 adapter connected
```
- ⚠️ Docker daemon 自启后容器通常能自启（restart: unless-stopped）；仍异常时 `docker start orzmc-easybot`
- 测试服：启动前 `rm -f world/session.lock`（异常退出残留锁）→ `./start.sh` → grep `Done (`
- 最终验证闭环：插件日志 `WebSocket连接建立` + `认证成功` + 投递诊断（`scripts/easybot_deliveries.py`）最近记录全 ✅
- Shadowrocket 由用户手动开；确认直连规则：`ifconfig utun3` 存在（UP）+ `curl https://www.baidu.com` 快（~0.1s，直连）+ `curl https://www.google.com` 通（~2s，代理）+ `dig test-bot.{SERVER_NAME}.cn` 返 **198.18.x.x fake-IP 是正常**（隧道在工作），不是服务故障
- 测试服：启动前 `rm -f world/session.lock`（异常退出残留锁）→ `./start.sh` → grep `Done (`
- 最终验证闭环：插件日志 `WebSocket连接建立` + `认证成功` + 投递诊断（`scripts/easybot_deliveries.py`）最近记录全 ✅

## 发送失败诊断（核心：gateway.db / API）
> ⚠️ **0.0.33 变更（2026-08-12 实测）**：投递记录从 `outbound_deliveries` 迁移到 **`messages` 表**（`outbound_deliveries` 停止写入，仅留历史）；且 SQLite WAL 模式下 `docker cp` 单文件**漏最近提交**（-wal 未合并）→ **不要再用 docker cp+sqlite 查投递**。诊断用脚本（已更新为 API 版）：`python3 scripts/easybot_deliveries.py`（自动 admin login → `GET /api/v1/messages`，出站标 [出]/入站标 [入]，失败显示 error）
```bash
python3 scripts/easybot_deliveries.py   # 最近投递状态（API 版，0.0.33+）
# 手动查：POST /admin/login {password} → GET /api/v1/messages?limit=30
```
关键表（0.0.33，仅 docker cp 全量备份时用）：
- `messages`：**当前投递/消息记录**（platform/chat_id/role/text/raw_data.result.success/timestamp）
- `sessions`：会话 key ↔ chat_type（**Group=群 / Dm=私聊**）——判断 target 配错类型
- `api_keys`：key 权限（插件 key 仅 `messagessend`+`websocketconnect`；面板 admin key 权限全）
- 容器日志被面板 `/api/v1/logs` 每秒轮询刷屏 → 用 grep 过滤具体路径

## QQ token 生命周期
- QQ access token 有效期 **7200s (2h)**，过期后发送报 **11244 "token not exist or expire"**
- **刷新**：`POST /api/v1/adapters/qq/start`（需 API key）→ 日志依次出现 `QQ access token refreshed` → `QQ adapter connected` → `QQ Gateway ready`；面板操作等效
- **拿全权限 key**：`POST /admin/login {"password":"<EASYBOT_ADMIN_PASSWORD>"}` → **响应体是 `{"key":"eb_..."}`（字段名 `key`，不是 `data.token`）**（2026-08-16 实测：按 data.token 取恒空 → AUTH_FAILED；`key` 才是全权限 API Key，面板密码登录短时管理 Session，权限全——插件 key 只有 messagessend+websocketconnect，查 sessions/adapters 会 403）
- **查各平台 adapter 状态**：`GET /api/v1/adapters`（Bearer 全权限 key）→ `{adapters:[{platform, display_name, status: Connected|Connecting|Failed, health, connected, last_error, retry_attempt}]}`（2026-08-16 实测）；QQ/飞书/微信 Connected+Healthy，Telegram 连不上 `api.telegram.org`（网络/代理）、Discord 连不上 `discord.com/api` 都自动重试（20 次，10s 间隔）；**health 端点 adapters.connected 只有总数**（如 3/5），要定位哪个平台挂必须查 `/api/v1/adapters`
- ⚠️ **Docker daemon 未启动症状**（2026-08-16 实测）：`docker ps` 报 `Cannot connect to the Docker daemon` + health 端点无响应 + 测试服 OrzMC 日志 `WebSocket连接关闭: code: 1002, reason: Invalid status code received: 502` 反复重连——**Mac 重启后 Docker Desktop 不会自启容器**（daemon 起来后 easybot 容器停在 Exited(255)），必须 `docker start easybot`；恢复后 QQ/微信 adapter 数秒内重连成功
- ⚠️⚠️ **Docker daemon 卡死恢复流程**（2026-08-17 实测）：症状 = `docker ps`/`docker info` 超时无响应（非「Cannot connect」报错）、`curl health` EXIT 56（connection reset）、插件 WS 报 502 反复重连。恢复三步曲：① **只杀 backend 系进程，勿连 GUI 一起 pkill**——`pkill -9 -f "com.docker"` 即可（2026-08-17 教训：`pkill -f "Docker"` 连 GUI 一起杀 → backend 残留半死、Linux VM 永不启动，daemon 永远不就绪；残留只剩 vmnetd(296) = 正常）② `open -a Docker` + 轮询 `docker info` 直到就绪（首次 ~5s，卡死后重启约 1-3 分钟）③ `docker start easybot` + health 验证 5/5（daemon 自启不带容器）
- ⚠️⚠️ **插件 WS 重连有最大次数上限**（2026-08-17 实测）：OrzMC 插件默认重试 10 次、指数退避（~2 分钟耗尽），日志 `达到最大重试次数，停止重连` + `WS reconnect exhausted` 后**永久停止**——此时网关已恢复也**不会自动重连**，必须**重启测试服**（RCON stop → start.sh）触发重新握手；验证日志 `WebSocket连接建立` + `EasyBot WebSocket 认证成功`
- **API 文档**：`GET /openapi.json`（89KB 完整 OpenAPI，所有端点+权限清单）——探索 EasyBot 能力先拉这个，别盲探端点
- **11255 "invalid request"**：token 刷新瞬间的暂时性错误，或 target 类型错（把 Dm openid 当群 id 发 `/v2/groups/`）
- 恢复确认：deliveries 最近记录全部 `succeeded`

## 会话 target 格式
- `qq:XXX` / `feishu:XXX` / `telegram:conv_XXX` / `discord:conv_XXX` / `wechat:conv_XXX`
- QQ 的 key 语义：群 = Group chat_id；私聊 = Dm openid —— 用 `sessions.chat_type` 区分
- 插件 easybot.yml 三目标：`admin_group` / `player_group`（PUBLIC 默认目标，空则降级 admin_group）/ `admin_dm`（私聊）

## 坑
1. **域名可能被 Shadowrocket VPN 劫持**：`dig test-bot.{SERVER_NAME}.cn` 返回 198.18.0.188（fake-IP 保留段）≠ 真实反代地址 —— 先 dig 再判断"服务挂了"
2. **反代不在本机**：本机 nginx 没有 test-bot 配置是正常的（反代在另一台设备）——别在本机 nginx 里找
3. 容器 env 含敏感项（QQ_CLIENT_SECRET / FEISHU_APP_SECRET / EASYBOT_ADMIN_PASSWORD / 各平台 token）——输出/入库前脱敏
4. 诊断用 db 副本用完即删，不留 /tmp 残留
5. **没有"模拟入站消息"的 API**：`/api/v1/messages/ingest|inject|emit` 均 404/405（未定义路径伪装），openapi.json 也无此端点——**无法用 API 伪造群消息触发插件 Bot 命令**；`/admin` 面板的 Debug 面板只是 API Key 权限验证器（验证 target + 发 probe），不是消息注入。要测 Bot 命令用测试服控制台 `orzdebug $<cmd>` 或真实群消息
6. 405 可能是"未定义路径"的默认响应——探测前先拉 `/openapi.json` 确认端点真实存在，别被 405/404 误导
7. **反代 Cloudflare 按 UA 拦截**（2026-08-12 实测）：urllib/python 默认 UA 请求 https://test-bot.{SERVER_NAME}.cn 返回 **403 + error code: 1010**；curl 带浏览器 UA 正常 200。手动测 API 走反代必须带浏览器 UA；本机 9090 直连无此限制

## 验证闭环
改完/刷新后：bot 上线触发通知 → 插件日志无 `失败目标` → gateway.db deliveries 最新记录全 `succeeded` → 以表格汇报（平台/目标/状态）
