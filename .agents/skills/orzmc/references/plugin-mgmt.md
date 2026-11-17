# 插件升级与配置迁移（plugin-mgmt）

> 合并自：minecraft-plugin-upgrade（2026-08-10 阶段一整合）
> 触发：升级自有/维护插件（OrzMC、EzShops 等）且新版本配置文件结构变化；「重建全部配置文件后再迁移旧配置字段」；三端插件配置有差异需分别处理。

## 核心流程（2026-08-09 用户确认的范式）

1. **打包产物**：OrzMC 用 git tag 检出打包（`git checkout <tag> && ./gradlew shadowJar`）；EzShops 用 tools/EzShops 本地仓库 mvn 打包
2. **升级顺序**：本地测试服 → Exaroton → MCSM（MCSM 必须无玩家窗口，有玩家严禁删配置/重启）
3. **每端步骤**：
   - a. **备份旧配置**（迁移依据）——本地 cp 到 /tmp；Exaroton GET files/data；MCSM 下载
      ⚠️ **新旧备份必须分目录**（`<端>/` 与 `<端>_new/`）——同一目录同名文件会被「拉取新配置」覆盖，旧值永久丢失（2026-08-09 MCSM 实测事故）
   - b. **删全部配置文件**（插件启动自动重建默认）——OrzMC：config/templates/easybot/permission/portals/ip_blacklist/guide_book；EzShops：config/messages
   - c. **升级 jar**（PaperMC update/ 机制——旧 jar 留 plugins/，新 jar 放 plugins/update/，重启自动替换）；上传时 jar 从**构建产物路径**读（`~/OrzMC/plugin/build/libs/`、`tools/EzShops/target/`），本地 plugins/update/ 重启后已清空别从那里读
   - d. **重启** → 配置自动重建
   - e. **diff 新旧配置** → 迁移**有差异的关键字段**（不是全量复制）
   - f. **写回 + 重启** → 验证（加载版本 + EasyBot 认证 + 健康检查）

## 迁移原则（用户明确）

- **三端单独迁移，不能简单全量同步**——每端旧配置值不同（easybot.yml 各平台段、EzShops language 本地 zh / Exaroton en）
- 新版本新增键保留默认不迁移；结构变化的配置（permission.yml 三段式→两段式）不迁移旧结构用新默认（bootstrap 幂等重建）
- ⚠️ 行级正则迁移只匹配第一个出现——多平台段（discord/qq/feishu 各有 enabled/admin_group/admin_dm）时只迁首段，其余段必须按段手动 patch
- ⚠️ 改配置文件前先 `yaml.safe_load` 校验格式 + 显示关键行，改后复验（用户明确要求「改前确认格式正确」）

## Exaroton 文件 API 实测（2026-08-09）

- **GET /files/data/{path}/ 可能返回裸文本或 JSON 包装**（`{"text":"..."}`，两种都实测过）——先 try `json.loads` + 检查 `text` 键解包；**PUT 回传必须传纯文本**（JSON 包装原样写回会损坏配置，实测翻车，修复脚本 scripts/fix_exaroton_cfg.py）
- **PUT /files/data/{path}/ body 裸文本**（Content-Type text/plain，body 原文即文件内容——切勿用 `{"text":...}` 包装）
- **文件端点必须带尾部斜杠**；上传 update/ 用 PUT 裸字节 + UA: Mozilla/5.0
- Exaroton 无玩家 3-4 分钟自动停——离线时可直接写文件，升级可免停服
- 高频调用触发 Cloudflare 风控（error 1010）——请求间隔 ≥5s

## MCSM API 实测（2026-08-09）

- **重启端点**：`GET /api/protected_instance/restart`（**不是** api/service/restart）；有玩家安全拦截，用户授权后直接 GET
- **删除端点**：`DELETE /api/files/` body `{"targets": [...]}` 数组（不是 target 单值）；删后自动 GET 验证（daemon 偶发假 200）——用 scripts/cmp3/mcsm_delete.py
- **有玩家在线**：脚本硬拦截 stop/restart/删配置——用户已通知玩家时用 mcsm_restart.py 绕过

## EzShops 存储配置（无 MySQL 报错排查）

- 症状：MCSM 玩家交易报 `StorageException: Failed to begin transaction` + `Communications link failure`（Connection refused）——每次交易一条，交易记录落不了库
- 根因（源码实证 CoreShopComponent.java）：`player-shops.storage.type: jaloquent` → 交易记录走 `JaloquentTransactionRepository`（顶层 database 段拼 jdbc:mysql）——**构造时不连接、交易时才连**，无 MySQL 则运行期报错
- 修复：`player-shops.storage.type: yaml` → 走 `YmlTransactionRepository` 完全不触碰数据库；重启后日志「Shop transactions: using YAML transaction repository」
- ⚠️ jar 无 sqlite JDBC 驱动（只有 SqliteDialect）——jdbc:sqlite 会 ClassNotFound，sqlite 方案不可行
- 本地服「Failed to initialise Jaloquent for player shops; falling back to YAML」= player-shops 正常降级；但**交易记录没有 YAML fallback**

## Geyser 基岩登录排查（InitialConnection-13 实战）

- 症状：基岩客户端 `Error Detail InitialConnection-13`（服务端日志无玩家连接记录——协议协商层失败）；或 Geyser 日志「下游数据包错误！(ClientboundLoginDisconnectPacket) Packet not found」+ 30s 后「Took too long to log in」
- 根因：**基岩客户端版本 > Geyser 稳定版支持的协议**。实测 Bedrock 26.40 + Geyser 2.11.1 全系列（b1206-b1210）均失败；**b1212 修复、b1214 为最新（2026-08-10 三端统一）**
- ⚠️ **构建号查询陷阱**：download.geysermc.org builds 列表滞后（升序、最新在尾部；当天新构建可能查不到）——拿不准直接问用户最新构建号
- 验证顺序：RakNet 握手（UDP 层通 ≠ 登录通）→ 真机登录（协议层）
- **域名 TCP 通而 UDP 不通** = 路由器只转发了 TCP，**Geyser UDP 19132 需单独转发规则**（公网 IP 真实可达时非 CGNAT）
- 端口差异：MCSM Geyser UDP 19132 / Exaroton Geyser UDP 39742

## 其他排查参考

- **村民过不了下界传送门**：Bukkit `EntityPortalEvent extends EntityTeleportEvent`（实体走 EntityTeleportEvent 监听被拦）；玩家 `PlayerPortalEvent extends PlayerTeleportEvent`（独立）
- **bot 断开 WARN**（Failed to deliver packet / Connection reset by peer）：mineflayer bot 主动断开时服务器仍在发消息的竞态，无害——bot.end() 前留 1-2s 收尾

## 验证

- 日志 `Loading server plugin OrzMC v<版本>` + `EzShops plugin enabled`
- EasyBot WebSocket 认证成功（迁移的连接配置生效）
- 健康检查仅剩 fallback 建议（whitelist.kick_message.qq_group_id 未配置→用 easybot.qq_group_id）为无害
- update/ 目录重启后自动清空 = 升级应用成功

## 支持文件

- `templates/migrate_keys.py`：单键行级迁移模板（多段需扩展）
- `scripts/fix_exaroton_cfg.py`：Exaroton JSON 包装配置修复
