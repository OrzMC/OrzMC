# 测试服 jar 升级 + 配置迁移 SOP（2026-09-12 实测沉淀）

> 适用：mcs.{SERVER_NAME}.cn 上的两个测试实例 **`papermc-test`**（716c2fb7，Paper）与 **`folia-test`**（8A932DD4，Folia）。
> 目标：把核心 + 全部插件升到目标渠道最新版，并把**配置文件按新版定义迁移**（缺键补齐、旧自定义值保留），最后清理所有备份残留。
> 全部操作用 MCSM API 完成（面板栈在 **Windows E:/orzmc**，Mac 端 `/Users/Shared/orzmc/...` 只是历史副本，**勿再直读**）。

## 0. 前置事实（2026-09-12 实测）

| 项 | 现状 |
|:--|:--|
| 面板 | `https://mcs.{SERVER_NAME}.cn/`，凭据 `~/.hermes/.env` 的 `MCSM_LOCAL_*`；daemon `fbb3492c...` |
| paper 实例 | docker 型，`eclipse-temurin:25-jre`，`java -Xms4G -Xmx4G -jar paper.jar nogui`，端口 `25565:25565/tcp` + `19132:19132/udp`，autoStart/autoRestart 均 false |
| folia 实例 | 同上，`-Xms2G -Xmx2G -jar folia.jar nogui`，端口 `25566:25565/tcp` + `19133:19132/udp` |
| 两实例 | **各自独立地图**，可同时启动；冷启动 Done ≈ 90~155s |
| paper 特有点 | `im.yml` = `backend: builtin`（含 QQ/飞书凭据）；`i18n.default_lang: en-US` |
| folia 特有点 | `im.yml` = `backend: easybot`（默认值）；`i18n.default_lang: zh-CN` |

> ⚠️ **双实例差异是刻意设计（老板 2026-09-12 明确确认，勿"统一修复"）**：
> - **paper = 英文语言包 + builtin 直连**（专用于验证 i18n 英文包与内置直连通道）；其群消息会以**英文**推送，`default_lang: en-US` 属预期，**不要改回 zh-CN**。
> - **folia = easybot 网关 + zh-CN**（验证网关通道）。
> - 两条 IM 通道**并行保留**（A/B 覆盖），不要合并成单通道。
> - 副作用须知：两实例的飞书通知目标**指向同一个群**（paper `player_group` == folia `admin_group` = `oc_00eb…`），因此该群会同时收到两台服消息（paper 侧英文）；如需降噪应改目标群而非改语言/通道。
> - `default_lang` 作用面（源码实证 `I18nService`）：`langFor(Player)` **跟随客户端 locale**（玩家游戏内文案不受影响）；`default_lang` 只管**群事件通知 / 控制台广播 / 维护文案 / Bot 交互兜底**。

## 1. 升级流程（六步）

```
① 抓产物本地校验 → ② 实例内备份(临时) → ③ 投递 → ④ 首启动触发迁移 → ⑤ 配置补键/改值 → ⑥ 二次启动验收 → ⑦ 清理备份
```

### ① 抓产物 + 本地 sha 校验
```bash
python3 - <<'EOF'   # 见本次实录：Modrinth/Hangar/Geyser API/metadata.luckperms.net 全部取直链 + 哈希
EOF
```
- Modrinth 版本接口给 **sha512**（`files[].hashes.sha512`）；Hangar 给 `fileInfo.sha256Hash`；Geyser 给 `downloads.spigot.sha256`；LuckPerms 走 `metadata.luckperms.net/data/all` 的 `downloads.bukkit`（无哈希，官方渠道直链）。
- **Paper 核心用 fill-data 内容寻址直链**：`https://fill-data.papermc.io/v1/objects/<sha256>/paper-26.2-123.jar` —— URL 自带哈希，投递后自带完整性保证。
- 渠道查询：`scripts/parse_papermc.py [paper|folia]`（页面内嵌 JSON → 最新 STABLE + sha256）。

### ② 实例内备份（临时，验收后删）
```python
req(inst,"POST","/api/files/mkdir",{"target":"/upgrade-bak-YYYYMMDD"})
req(inst,"POST","/api/files/copy",{"targets":[["/plugins/X.jar","/upgrade-bak-YYYYMMDD/X.jar"], ...]})
```
- `copy` 的 `targets` 是**二维数组** `[[源,目标],...]`，一次调用可批量；核心 jar 也一并复制。
- 校验：备份目录 `list` 实读文件数 == 计划数。

### ③ 投递
- **核心 jar**：`POST /api/files/download_from_url {"url":<fill-data直链>,"file_name":"/paper.jar"}` ——
  ⚠️ **实测可覆盖已存在文件**（先写 0 字节文件再投递同名 URL → 覆盖成功），所以旧 jar 必须先 copy 到备份目录。
- **插件 jar — ⚠️⚠️ 2026-10-05 起：上传通道不可用，统一走 daemon 直传**
  - ❌ `POST /api/files/upload?upload_dir=/plugins/update` 取证 → `POST {addr}/upload/{password}` multipart **实测全线失败**：凭据 `addr` 现为 **`wss://mcs-node.{SERVER_NAME}.cn:443`**（不是 localhost:24444），https 化后仍 **403 Forbidden**，部分文件报 `Broken pipe`。**别再在这条路上浪费重试**
  - ✅ **标准做法 = `POST /api/files/download_from_url`** body `{"url":官方直链,"file_name":"/plugins/update/<文件名>.jar"}` —— 2026-10-05 实测 **7 个文件（含 47MB Geyser）全部 200 一次成功**；小件同样适用，比 upload 更稳
  - ✅ 投递后 **sha256 回读验收**（`POST /api/files/download` 签发 → `GET {addr}/download/{pwd}/{文件名}`，`wss://` 换 `https://`，`localhost` 换面板主机名）——本次 7/7 与本地一致。同账号签发限流 3s/次，**串行 + sleep 3.2~3.6s**
  - 📌 老版本 upload 通道的「addr 拼 https://host/upload/<pwd>」写法保留在此仅作历史参考，勿再使用
- 投递后**立即回读校验**（`mcsm_download` 拉回 + sha256 比对本地）：本次 paper 4 个 + folia 8 个插件全部 OK。
- ⚠️ **回读要赶在服务器启动前**——启动后 `plugins/update/` 会被消费（文件移走），回读报「回读失败」是假故障。

### ④ 首启动（触发插件自带配置迁移）
- `GET /api/protected_instance/open` 启动；轮询 `latest.log` 等 `Done (`。
- OrzMC 会打**配置升级**日志（示例）：
  `配置升级: config.yml schema legacy(config-version=2) → 14，新增默认键 13 个：i18n+1 bot+3 geoip+1 prison+1 gamemode-correction+3 update+4，旧默认翻转 5 项：...，保留自定义 1 项：entity_teleport_whitelist`
  `配置升级: templates.yml ... 正文迁移（删键走语言包/翻直通壳） 33 项`
  `配置升级: easybot.yml ... 新增默认键 1 个：config-version+1（原文件已备份为 easybot.yml.bak）`
- ⚠️ **新规范**：1.0.24+ 起模板正文迁到语言包（`jar 内 messages/messages_zh-CN.yml`），templates.yml 只剩「直通壳 `{message}` + 格式表 + 配色 + 数据键」→ 旧默认正文被删键是**正常零回归**（语言包同文案），自定义正文保留。
- ⚠️ **easybot.yml 的 `cmd_prompt_char`/`discord_server_link`/`qq_group_id` 是 v12 前遗留键**：插件会自动迁到 `config.yml bot:` 并**删除**旧键（`ConfigService.migrateBotParamsToConfig`）→ **不要手工补回**，补了下次启动也会被清掉。

### ⑤ 配置补键 / 改值（`scripts/config_merge_defaults.py`）
```bash
# 1) 从新 jar 提取默认定义
python3 ~/.hermes/skills/gaming/orzmc/scripts/config_merge_defaults.py --extract OrzMC-1.0.25-dev.416.jar --extract-dir defaults/
# 2) 预览缺键（只读）
python3 .../config_merge_defaults.py --default defaults/ --target <实例配置目录> --dry-run
# 3) 生成合并文件（新定义补键 + 旧值保留 + 注释保留，ruamel 往返）
python3 .../config_merge_defaults.py --default defaults/ --out to_upload/
```
- 语义：**新默认的键集为准**，缺失键按新默认补；**既有键一律保留实例值**（自定义优先）；实例独有的键**不删**（运行时数据如 `permission.yml reviews.requests.*` 会保留并报告）。
- 写回实例：`PUT /api/files/?daemonId=&uuid=` body `{"target":"/plugins/OrzMC/config.yml","text":"<全文>"}`（**只能写已存在文件**；body 字段名是 `text`）。
- 写后回读 + 关键值断言（本次：folia `update.channel=beta`、`bot.qq_group_id=1082305302`；paper im.yml 四平台段齐全且凭据保留）。
- 三端/双实例常见待改：**OrzMC `update.channel`**（dev 验证机应为 `beta`；`release` 只收正式版）。

### ⑥ 二次启动 + 验收清单
- [ ] 核心行：`This server is running Paper version 26.2-123-main@...` / `Folia version 26.2-7-...`
- [ ] 各插件 `Enabling X vY` 与目标版本一致
- [ ] `Could not load plugin` / `SEVERE` / `not marked as supporting` = 0 条
- [ ] `plugins/update/` 已清空；`plugins/` 内 jar 名 = 新版本名
- [ ] **jar sha256 回读比对**（最终权威证据，比日志版本号可靠——Geyser 日志只打 `2.11.2-SNAPSHOT`）
- [ ] OrzMC `配置健康检查` 无**新增**告警（历史建议项：`easybot.api_server` 明文、`qq.admin_dm` 未配置 → 非本次引入）
- [ ] OrzMC `自更新已启用（通道 beta，当前 vX）`

### ⑦ 清理备份（老板要求：不留堆积）
```python
req(inst,"DELETE","/api/files/",{"targets":["/upgrade-bak-YYYYMMDD", "/plugins/OrzMC/config.yml.bak", ...]})
```
删后必须 `list` 复核真的没了；本地工作目录（产物 + before/after 配置快照）一并删。

## 2. 本次（2026-09-12）实录结果

| 实例 | 核心 | 插件升级 |
|:--|:--|:--|
| papermc-test | Paper 26.2-121 → **26.2-123** | Geyser-Spigot 1233→**1235**、LuckPerms 5.5.81→**5.5.82**、voicechat 2.6.21→**2.6.23**、OrzMC 1.0.25-dev.415→**1.0.25-dev.416** |
| folia-test | Folia 26.2-7（部署 jar sha256 = 官方，**已最新**） | Geyser 1233→**1235**、LuckPerms 5.5.81→**5.5.82**、AxGraves 1.29.0→**1.31.0**、EssentialsC 4.2.8→**4.3.0**、GriefPrevention3D 18.3.4→**18.3.10**、ExecutableEvents 3.26.8.10→**3.26.9.9**、SCore 5.26.8.10→**5.26.9.9**、OrzMC 1.0.23→**1.0.25-dev.416** |

- 保持不升（已最新/既有决策）：EssentialsX 2.22.0、WorldEdit 7.4.5、WorldGuard 7.0.18、packetevents 2.13.0、**Via 系列 5.11.0（稳定版不升 SNAPSHOT）**、GriefPrevention 16.18.7、SkinsRestorer 15.12.5、F3F4Perms 1.3.0、GrimAC 2.3.74（比 GitHub release 新）、VaultUnlocked 2.20.2、SimpleLogin 1.16.7、本地打包的 EzShops 2.5.9/LoginSecurity 3.3.2/DeathChest 3.0.1/GetMeHome 3.0.2。
- 配置：paper 已 schema 14（无迁移，仅补 `im.yml` 平台段）；folia 由 legacy(2)→14（13 键补齐 + 5 项旧默认翻转 + templates 正文迁语言包），自定义 `entity_teleport_whitelist`(16 项) 与其 QQ 群号 `1082305302` 完整保留；两实例 `update.channel` 均 = **beta**。
- 待老板决策的观察项：paper `i18n.default_lang: en-US`（folia 是 zh-CN）→ paper 群消息/游戏文案走英文语言包。

## 2b. 2026-10-05 实录（第二轮升级 + 核心版本化落地）

| 实例 | 升级项 | 启动 |
|:--|:--|:--|
| papermc-test（Paper 26.2-129） | Geyser 1247→**1248**、LuckPerms 5.5.85→**5.5.87**、SkinsRestorer 15.12.5→**15.12.6**、OrzMC 1.0.28-dev.425→**1.0.29-dev.427** | Done 179s |
| folia-test（Folia 26.2-7） | Geyser 1247→**1248**、LuckPerms→**5.5.87**、SkinsRestorer→**15.12.6**、ExecutableEvents 3.26.10.2→**3.26.10.4**、SCore 5.26.10.2→**5.26.10.4** | Done 116s |

- AxGraves 1.32.1 已最新（巡检脚本报「查询失败」属误报）
- 交付：**全部走 `download_from_url`**，7 文件 sha256 回读 7/7 一致；`plugins/update` 启动后被消费（total=0）
- OrzMC 升级触发配置迁移 `config.yml schema 14 → 15`（新增 `tnt` / `exploit_hardening`，`entity_teleport_whitelist` 16→17 项），自动留 `config.yml.bak`
- 核心改名后验证：`latest.log` = `Paper 26.2-129` / `Folia 26.2-7`，根目录只剩 `paper-26.2-129.jar` / `folia-26.2-7.jar`
  （当日曾短暂使用带 `logs/start-script.log` 审计行的加强版脚本，当日即按老板要求精简为 4 行版 → 见 §2c；如需审计行可自行加回）
- **启动日志异常（新发现，勿重复排查）**：
  - 🔴 paper `[Essentials] You are running an unsupported server version!` —— EssentialsX 最新正式版 2.22.0（2026-05-31）**未适配 26.x**，main 分支已有 26.2/26.3 修复（26-08-05 起）但**未发版**。老板决策：**不上 dev 构建，等正式版**
  - 🟠 folia `[SimpleLogin] ProtocolLib not found → /login /register 明文写控制台`。**ProtocolLib 不可装**：Folia 相关 issue 全被关成 **not_planned**、最新 release 5.4.0 早于 26.x、26.2 仍有 open bug（#3660）、26.3 修复仅在 dev 提交。SimpleLogin 配置里**无隐藏开关**（已核对 config.yml）。替代只有迁 AuthMe（Modrinth `authmereloaded` loaders 含 folia）。老板决策：**保持现状**
  - 🟡 folia `duplicate keys found: chiseled_sandstone / chiseled_red_sandstone` —— **40+ 插件 yml 全扫未命中**，疑似 jar 内置资源；影响可忽略
  - 🟡 folia Geyser 报 `ViaVersion 过旧`（5.12.0 已是最新正式版，只 SNAPSHOT 更新 → 按纪律不动）
  - ⚪ 既有噪音：offline mode / root 用户 / spark 统计超时 / EzShops 菜单 `slot -1` 越界 / GrimAC+ViaBackwards 组合提示
- **依赖插件核查结论**：packetevents 2.14.0 ✅、Vault/VaultUnlocked ✅、Via 三件套 ✅、SCore↔ExecutableEvents ✅、WorldEdit↔WorldGuard ✅；**唯一真缺口 = ProtocolLib**（见上）、唯一上游未适配 = EssentialsX
- 备份清理：删除陈旧 `/upgrade-bak-20260919`（paper 90.5MB + folia 36.9MB），保留 `/upgrade-bak-20261001`（paper 57.4MB + folia 60.4MB）

## 2c. 核心 jar 版本化命名 + `/start.sh`（2026-10-05 落地，两实例已生效）

**动机**：核心曾固定叫 `paper.jar` / `folia.jar`，文件名不含版本/构建号 → 无法判断跑的是哪个构建，版本巡检只能靠启动日志反推。

**现状（已落地）**：
- 启动命令（老板在面板改的，普通 apikey 改不了 → 见下方坑）：**`sh /server/start.sh`**
- 实例根目录核心：`paper-26.2-129.jar` / `folia-26.2-7.jar`（**真实版本名**）
- `/start.sh` 自动识别：优先 `{paper,folia}-*.jar`（`sort -V` 取版本最高），否则回退固定名

**每次核心升级的新流程**：投递 `paper-<新版本>.jar`（`download_from_url`）→ 删旧 jar → 重启；删旧前先 `copy` 到 `/upgrade-bak-YYYYMMDD/`

**脚本全文（2026-10-05 老板要求精简后的最终版，实例根目录 `/start.sh`，两实例仅 prefix 与内存不同）**：
```sh
#!/bin/sh
# MCSM 启动命令 = sh /server/start.sh ｜ 自动选版本化核心（版本最高），回退 paper.jar
J=$(ls -1 paper-*.jar 2>/dev/null | sort -V | tail -1)
exec java -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -Dlog4j2.configurationFile=/server/config/log4j2.xml -Xms4G -Xmx4G -jar "${J:-paper.jar}" nogui
```
（folia 实例：`paper` → `folia`、`-Xms4G -Xmx4G` → `-Xms2G -Xmx2G`）

**精简取舍（4 行版 vs 初版 32 行，逐条已验证）**：
- ❌ 删 `cd /server`：MCSM docker 实例 cwd 本来就是 `/server`（原固定名命令直接跑通、日志里 `file:/server/libraries/...` 可证），无需 cd
- ❌ 删多 jar 计数/告警、找不到 jar 的显式报错、`[start.sh]` console echo：`sort -V | tail -1` 已保证取最高版本；echo 会被 MCSM 滚动缓冲吃掉，无实际价值
- ❌ 删 `logs/start-script.log` 审计落盘：核心版本以 `logs/latest.log` 的 `This server is running ...` + 根目录 jar 名双重核对即可
- ✅ **必须保留**：`sort -V | tail -1` 选版本化核心、`${J:-paper.jar}` 固定名回退、**`exec`**（不加 exec → MCSM 的 stop（stdin 注入 `stop`）失效，只能强杀）
- ✅ 精简版实测（4 场景 + 真实重启）：版本化 jar→选中；双版本→取最高；仅固定名→回退；都无→回退 `paper.jar`；两实例重启后 `latest.log` = `Paper 26.2-129` / `Folia 26.2-7`，零 start.sh 相关错误

**坑与验证要点**：
1. ⚠️ **`PUT /api/instance` 改实例配置对普通 apikey 是 403「密钥不正确」** → 启动命令变更**必须老板在面板做**（或换管理员 apikey）。文件类 API（touch/PUT/DELETE/move/list/download_from_url）普通 apikey 全可用。
2. 新建脚本文件：`POST /api/files/touch` `{"target":"/start.sh"}` → `PUT /api/files/` `{"target":"/start.sh","text":"<全文>"}`（PUT 只能写已存在文件；body 字段 `text`）→ 回读校验。
3. **切换顺序**：先让老板把启动命令改为 `sh /server/start.sh`（脚本含固定名回退，此时照跑 `paper.jar`）→ 再停服改名 → 启动验证。顺序颠倒会让现启动命令找不到 jar。
4. **`exec` 不能省**：不加 exec → MCSM 的 stop（stdin 注入 `stop`）失效，只能强杀。
5. ⚠️ **MCSM 的 `outputlog` 是滚动缓冲**（重启后可能只剩几十行）→ **`[start.sh]` 的 echo 会滚掉**，因此脚本额外落盘 `logs/start-script.log`（审计用）；核心版本以 `logs/latest.log` 的 `This server is running ...` 为准（`outputlog` 里可能已看不到该行）。
6. 验证清单：`logs/start-script.log` 出现 `使用核心: paper-26.2-129.jar`；`latest.log` 的版本行与 jar 名一致；根目录只剩一个核心 jar；`sh -n` + 4 场景（单版本化 / 双版本化取最新 / 仅固定名 / 都没有报错退出 1）。
7. 附带收益：`mc_version_check.py` 可**直接读文件名**判定已部署核心版本（此前 folia 只能靠日志反推）。

## 2d. 2026-10-12 实录（第三轮：核心 26.2-133 + Geyser 1251 + Via 5.12.1 + folia 三件套 + GP3D）

> 触发：周巡检（`d81c8325fe8b`）报告「有更新可用」清单 + 老板逐条批准。全程 MCSM API，产物本地 sha 校验 → 备份 → `download_from_url` 直传 → 回读 sha256 → 启动 → 日志验收。

| 实例 | 升级项 | 结果 |
|:--|:--|:--|
| papermc-test | Paper **26.2-129 → 26.2-133**、Geyser **1248 → 1251**、ViaVersion **5.12.0 → 5.12.1**、ViaBackwards **5.12.0 → 5.12.1** | ✅ `Paper version 26.2-133-ver/26.2@58e6e45` |
| folia-test | Geyser **1248 → 1251**、Via 双件 **→ 5.12.1**、EssentialsC **4.3.2-all → 4.3.3**、ExecutableEvents **3.26.10.4 → 3.26.10.10**、SCore **5.26.10.4 → 5.26.10.10**、GriefPrevention3D **18.4.8 → 18.4.12** | ✅ `Folia version 26.2-7-ver/26.2.x@14b7fee`，`Done (258.480s)` |

- **交付 11 文件 / 回读 sha256 11-11 一致**（paper 64.5MB 核心 + Geyser 49.9MB ×2 + 其余）；`plugins/update/` 启动后被消费（两实例均空）；根目录只剩 `paper-26.2-133.jar` / `folia-26.2-7.jar`
- **备份**：建 `/upgrade-bak-20261012`（paper 4 件 / folia 7 件），删旧 `/upgrade-bak-20261001`；**实例最终停回原状**（升级前亦为停止态）
- **OrzMC 无需升级**：两实例已是 1.0.29-dev.427（=Hangar beta 最新），启动自更新回显「已是最新」，无配置迁移
- **验收唯一 ERROR**：paper `[Essentials] You are running an unsupported server version!`（既有已知，老板决策等正式版）；OrzMC 配置健康检查仅既有建议项（easybot 明文 http/ws、folia qq admin_dm 未配置），**无新增告警**
- ⚠️ **观察项（本轮新发现，非升级引入）**：**两实例同时冷启动**时 folia 出现 4 次 `Folia Watchdog Thread: Tick region ... has not responded in 5.4s`（栈顶 villager `AcquirePoi` → Moonrise POI 加载）→ 疑为宿主资源争抢所致。**下次升级建议串行启动（paper 起完 Done 再起 folia）**

**本轮新增实现坑（脚本已沉淀）**：
1. **Modrinth version API 只给 `hashes.sha512` + `sha1`（无 sha256）** —— 断言别写死 sha256，会 `KeyError`。
2. **Geyser build 响应无 `url` 字段**（只有 name+sha256）→ 直链须自行拼 `https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/<build>/downloads/spigot`。
3. **Paper fill v3 API 的下载对象哈希在 `downloads["server:default"]["checksums"]["sha256"]`**（不是顶层 `sha256`）→ 内容寻址直链 = `https://fill-data.papermc.io/v1/objects/<sha256>/<name>`。
4. **Modrinth API 偶发 `IncompleteRead`** → 抓取函数须自带退避重试（本轮流式重试 4 次通过）。
5. **Modrinth 侧 jar 文件名可能不含版本号**（如 `GriefPrevention3D.jar`）→ 投递时改名为 `<名>-<版本>.jar`，维持「文件名含版本」惯例（否则 `mc_version_check.py` 又要靠 fallback 表）。
6. **`mc_version_check.py` 未识别 jar 会导致漏报升级项**：本轮 `GriefPrevention3D-18.4.8.jar` 因 PREFIX_NAME 缺该前缀被报「未识别」→ 其 **18.4.8→18.4.12** 的升级项在周报里根本没出现（已修映射表，见 SKILL.md）。

## 2e. 2026-10-12 Paper **26.3 升级兼容性实测**（真机两轮，结论：可升但插件需同步）

> 触发：老板问「测试服确认核心能否升 26.3、插件是否支持/是否要一起升」。做法：真机把 papermc-test 核心换成 `paper-26.3-177.jar`（STABLE）实测，两轮日志取证。

**第一轮（原插件集）→ ❌ 服务器崩溃**
- 核心启动 OK：`Paper version 26.3-177-main@fbec96a`（Java 25 满足）
- **WorldEdit 7.4.5 启用失败** → `Error occurred while enabling WorldEdit` 栈：`java.lang.ExceptionInInitializerError` ← `java.lang.IllegalArgumentException: Couldn't find asBukkitCopy or asCraftMirror method on CraftItemStack`（`WorldEditPlugin.initializeRegistries`）
- 连带 **WorldGuard 7.0.19 disable 报错** → 随后 **整服 crash**：crash-report `Description: Exception in server tick loop` / `com.sk89q.worldedit.extension.platform.NoCapablePlatformException: No platform was found supporting CONFIGURATION`（`SimpleHelpMap.initializeCommands` → `MinecraftServer.initPostWorld`）
- 取证：`/server/crash-reports/crash-2026-10-12_19.29.43-server.txt`；本地副本 `/tmp/orzmc_263_check/crash.txt`

**第二轮（WorldEdit → 7.4.6-beta-02）→ ✅ 启动全绿**
- `Done (74.273s)!`，**21 插件全部 Enabling 成功**，WorldGuard 正常加载三世界 region，**无 crash**
- 唯一新问题：**Geyser-Spigot 1251 启用失败**（同一个反射根因：其 shaded `org.incendo.cloud` 的 `CraftBukkitReflection.firstNonNullOrThrow` → `Couldn't find asBukkitCopy or asCraftMirror method on CraftItemStack`）→ Geyser 自我 disable = **基岩通道不可用**
- Essentials 仍报 `unsupported server version`（既有）

**结论表（Paper 26.3 升级所需）**

| 组件 | 现状 | 26.3 是否可用 | 处置 |
|:--|:--|:--|:--|
| Paper 核心 | 26.3-177 **STABLE** | ✅ 可跑 | 可升（测试服已验证） |
| **WorldEdit** | 7.4.5（release） | ❌ 启用失败并**拖垮整服** | **必须升 `7.4.6-beta-02`**（Modrinth beta，09-24 起支持 26.3） |
| **Geyser-Spigot** | 1251（最新） | ❌ 启用失败（基岩不可用） | **暂无兼容版**（上游无相关修复提交）→ 等 Geyser 发版 |
| WorldGuard | 7.0.19 | ✅（依赖 WE 7.4.6+） | 无需动 |
| GrimAC | 2.3.74-abb95b6（alpha） | ✅ 实测其 shaded packetevents = `2.14.1-SNAPSHOT`，日志有 `Loading block mappings for V_26_3` → **26.3 支持已在手** | 无需动（原「无解」结论已被推翻） |
| ViaVersion/ViaBackwards 5.12.1、ViaRewind 4.2.0、packetevents 2.14.0、OrzMC 1.0.29、LuckPerms 5.5.87、Vault、SkinsRestorer 15.12.6、GriefPrevention 16.18.7、voicechat 2.6.24、LoginSecurity、EzShops、DeathChest、BackOnDeath、GetMeHome、F3F4Perms 1.3.0 | — | ✅ 均正常启用（**F3F4Perms 元数据虽只标到 26.2，实测可用**） | 无需动 |
| **Folia 端** | Folia 26.2-7 | — | **Folia 无 26.3 版本线**（fill API 只有 26.2）→ folia-test **无法升 26.3** |

**共同根因**：Paper 26.3 改了 `CraftItemStack` 的 `asBukkitCopy`/`asCraftMirror` 反射面 → 所有走 **incendo-cloud `CraftBukkitReflection`** 的插件会在启用时炸（WE、Geyser 中招；WE 已在 7.4.6-beta 修好，Geyser 未修）。

**回滚/切换（一键）**：
- 回 26.2：删根目录 `paper-26.3-*.jar`（133 仍在，`start.sh` 自动选最高版本回落）；WE 回 7.4.5 从 `/upgrade-bak-20261012-263/worldedit-bukkit-7.4.5.jar` 复制回 `/plugins/`
- 再切 26.3：产物已缓存 `/tmp/orzmc_263_check/paper-26.3-177.jar` + `worldedit-bukkit-7.4.6-beta-02.jar`
- ⚠️ Via 在测试服 `block-versions: []` **未阻断 26.3 客户端** → 可以直接用 26.3 客户端实测

### 🔒 老板决策（2026-10-12）· 26.3 升级挂起

> 原话：「**测试服先保持现状，等插件都正式支持 26.3 后，再进行升级**」

- **测试服现状 = 保持 26.3 实验态**：`papermc-test` = **Paper 26.3-177 + WorldEdit 7.4.6-beta-02**（Geyser 因无兼容版**未启用**）；`folia-test` = Folia 26.2-7（Folia 无 26.3）
- **正式升级（含生产端）门槛 = 「所有插件都正式支持 26.3」** → 就绪判据（全部满足才算就绪）：
  1. **WorldEdit**：出**正式版**（release ≥ 7.4.6，非 beta）且 `game_versions` 含 26.3
  2. **Geyser-Spigot**：新 build（>1251）**在 26.3 上能成功 Enabling**（修掉 `asBukkitCopy/asCraftMirror` 反射问题）
  3. **EssentialsX**：正式版声明支持 26.x（当前 2.22.0 报 `unsupported server version`）
  4. **GrimAC**：正式 release 含 26.3（当前 alpha `abb95b6` 实测已可用）
  5. **F3F4Perms**：元数据标 26.3（实测已可用，属"口径"项）
  6. **SimpleLogin**：元数据标 26.3（folia 用）
- 就绪前**不动生产端（Exaroton）**；就绪后再按「MCSM 测试服 → Exaroton 生产」顺序推进

## 2f. 2026-10-19 实录（第四轮：Paper 26.3-205 + WE 7.4.6 正式版 + Geyser 2.12.0 → **26.3 两大门槛解除**）

> 触发：老板「先在测试服上更新插件和核心到最新版本，测试一下」。两实例均停服 0 玩家时执行。

| 实例 | 升级项 | 结果 |
|:--|:--|:--|
| papermc-test | Paper **26.3-177 → 26.3-205（STABLE）**、WorldEdit **7.4.6-beta-02 → 7.4.6 正式版**、WorldGuard **7.0.19 → 7.0.20**、Geyser **1251 → 2.12.0-b1265** | ✅ `Paper 26.3-205-main@a90108f`、`Done (146.714s)`；重启后 `Done (94.448s)` |
| folia-test | Geyser **1251 → 1265**、EssentialsC **4.3.3 → 4.3.4**、ExecutableEvents **3.26.10.10 → 3.26.10.17**、SCore **5.26.10.10 → 5.26.10.17**、GriefPrevention3D **18.4.12 → 18.4.14** | ✅ Folia 26.2-7（核心未动）+ `Done (117.509s)`；重启后 `Done (100.451s)` |

**🎉 26.3 就绪门槛（2026-10-12 定的 6 项）本轮解除 2 项**：
1. ✅ **WorldEdit 出正式版 7.4.6（release，game_versions 含 26.3）** → 26.3 上 `Enabling v7.4.6+7648-00664b0`、adapter=`PaperweightAdapter v26_3`，**不再崩服**
2. ✅ **Geyser 2.12.0-b1265 在 26.3 上能正常启用**（`Started Geyser on UDP 19132`）——10-12 那个 `asBukkitCopy/asCraftMirror` 反射坑已修
3. ⏳ 仍缺：EssentialsX 正式版（2.22.0 仍报 unsupported）、GrimAC 正式 release、F3F4Perms/SimpleLogin 元数据口径

**folia 核心未动的判据（可复用）**：`folia-26.3-3` 通道 = **ALPHA**（26.2-7 是 BETA），违反「核心只升 STABLE/BETA」纪律 → 暂不升；等 Folia 26.3 有 BETA 构建。

**插件元数据须逐条核对 game_versions 再决定是否升 folia**：`WorldGuard 7.0.20` 的 `game_versions` **只标 26.3**（无 26.2）→ folia（26.2-7）**故意不升**，仍是 7.0.19 / WE 7.4.5。**教训：同一插件在两实例可能不能同版本，取决于各实例核心版本线**。

### 本轮新增坑（重要）

1. 🔴 **`/tmp` 会在 macOS 重启时被清空**（`/tmp -> private/tmp`）——本轮 Mac 中途重启，`/tmp/orz_up*` 全部消失（脚本/产物/日志/`mc.py` 全丢，得重建）。→ **多步升级的工作目录一律放 `~/.hermes/tmp/<任务名>/`**，别用 `/tmp`。
2. 🔴 **sha256 回读必须在「启动前」做**（对 `plugins/update/` 里的新文件）：服务器启动后插件 jar 被 JVM 加载 → **Windows 侧文件被锁**，回读会挂住/只读到半包（本轮 7.9MB 的 WE 只读到 524288B 就 EOF）。核心 jar 在根目录未被锁，运行态仍可回读（本轮 55MB `paper-26.3-205.jar` 运行中回读 sha256 ✅）。
3. 🔴 **面板 daemon 下载通道会「迟钝/截断」**（本轮实测：签署耗时 16.4s、流被截断、多次读取挂到超时）→ 触发后**停手等待**，别重试风暴；期间起服验收改用 **`GET /api/protected_instance/outputlog?size=1200`**（绕开 daemon 拉流，一行 `Done (Xs)!` 就够判定），完全不依赖 latest.log 下载。
4. 🟡 **`mc_version_check.py` 的 Modrinth slug 不能猜**：`GriefPrevention3D` = `griefprevention-3d-subdivisions`、`SimpleLogin` = `simple-login`（按 `loaders` 过滤 folia）；用错 slug 会返回同名但完全无关的老项目（本轮误查到 `1.2`/2025-10-15 版）。
5. 🟡 **验证链分层**（下载通道不可靠时的替代证据）：① 上游→本地哈希直验 ② `files/list` 落地 size 与本地逐字节相等 ③ 启动日志 `Enabling X vY` 版本号。三层齐全即可判「部署成功」，sha256 回读作为补强而非唯一依据。
6. 🟡 **`paper-26.3-177.jar` 出现过「删了又回来」**：删除后确认只剩 133/205，重启后目录里又见 177（疑为手动恢复或面板状态回滚）→ 删核心前先确认再删；`start.sh` 取 `sort -V | tail -1` 保证选最高版（205），多留旧 jar 不影响启动，只吃磁盘。
7. ⚠️ **Geyser 2.12 新警告（时间敏感）**：`NetherNet support is NOT enabled ... Players will not be able to connect to your server, starting October 27th` → **2026-10-27 起基岩玩家将无法连接**，须在此之前启用 NetherNet（官方 blog `/blog/preparing-for-nethernet`，扩展仓库 `GeyserMC/GeyserNetherNet`）。实测 **paper 侧有该警告、folia 侧未见** → 处理时两实例都要查 config。
8. ⚠️ **宿主磁盘压力**：本轮 Mac `df` 显示 **94% 占用、仅剩 6.6GB** → 升级前后都看一眼；`/upgrade-bak-*` 会累积（paper 已有 1012、1012-263、1019 三个），清理时注意 **26.2 回滚依赖 `upgrade-bak-20261012-263/worldedit-bukkit-7.4.5.jar`**，别提前删。

## 2g. 升级包交付规范（老板要「打包发生产」时，2026-10-19 落地）

交付物放 `~/Downloads/orzmc-upgrade-YYYYMMDD/`（= 老板 S: 盘「下载」共享），并在同目录生成同名 zip。

**目录结构（按适用性分组，避免误发）**：
```
orzmc-upgrade-YYYYMMDD/
├── 01-core/                  # 自建/自托管核心 jar（Exaroton 不能用，其核心由面板选）
├── 02-plugins-<版本线>/       # 元数据只支持新版本的插件（如 WG 7.0.20 只标 26.3）
├── 03-plugins-common/        # 新旧核心都兼容的（如 Geyser）
├── 04-plugins-folia/         # Folia 独有
├── 05-production-catchup/    # 生产端落后项的补差 jar
├── SHA256SUMS.txt            # `find . -name "*.jar" -print0 | xargs -0 shasum -a 256 | sort -k2`
├── ANNOUNCEMENT.md           # 可直接粘贴的公告（emoji 标题 + 33 连字符分割线 + 分节）
└── SYNC-GUIDE.md             # 生产端 vs 测试服版本对照表 + 同步顺序 + 就绪门槛
```

**包内 jar 的来源（2026-10-26 定型，优于重新下载）**：先 `scp` 从运行实例回取（`scp "win:E:/.../<uuid>/plugins/X.jar" .`），再与升级时记录的 sha256 比对 → 保证「包内文件 = 实际部署件」；不要重新去上游下载（可能已发新 build，与线上不一致）。本次 7 个 jar 回取后 7/7 一致，包自检 `shasum -c` 全 OK + `unzip -t` 无错误。

**两条硬规矩**：
1. 🔴 **包内路径必须 ASCII**（`01-core` 而不是 `01-核心`）——macOS `zip` 打中文目录名，**Windows 解压会乱码**（本轮实测 `unzip -l` 已见乱码）。中文只放**文档正文**里。
2. 🔴 **生产端补差必须用「正式版优先」**：如 OrzMC 同时存在 `1.0.29`（Release）与 `1.0.29-dev.427`（Beta），差 1 小时但代码等同 → **给生产端用 Release**，测试服可继续 dev。
3. 🟡 打 zip 前先 `rm -f <zip>` 避免旧包残留；打完后 `unzip -l` 核对内层路径是 ASCII。

## 2h. 2026-10-26 实录（第五轮：Paper 26.3-224 + 两端 Geyser/LuckPerms + voicechat + folia 三件套；**SSH 直投成为标准交付通道**）

> 触发：老板「测试服插件和核心都升级最新版本」。Folia 核心 26.3-5 = **ALPHA** → 老板明确选「保持 26.2-7 不动」。

| 实例 | 升级项 | 结果 |
|:--|:--|:--|
| papermc-test | Paper **26.3-223 → 26.3-224（STABLE）**、Geyser **1265 → 1271**、LuckPerms **5.5.87 → 5.5.88**、voicechat **2.6.24 → 2.6.26** | ✅ `Paper version 26.3-224-main@eb9098a`、`Done (119.375s)`、Geyser `Started on UDP 19132` |
| folia-test | Geyser **1265 → 1271**、LuckPerms **5.5.87 → 5.5.88**、EssentialsC **4.3.4 → 4.3.5**、SCore **5.26.10.17 → 5.26.10.20**、**GriefPrevention3D 18.4.14 → 19.0.1（跨大版本）** | ✅ `Folia 26.2-7-ver`、`Done (140.574s)`、GP3D 19.0.1 正常 `Enabling` |

- 未升（已最新/纪律）：Via 三件套（5.12.2 仅 SNAPSHOT）、packetevents 2.14.0、GrimAC（本地 alpha 比 release 新）、WorldEdit/WorldGuard/EssentialsX/SkinsRestorer/GriefPrevention/F3F4Perms
- **folia 的 WE/WG 保持 7.4.5 / 7.0.19**：WG 7.0.20 元数据只标 26.3，folia 是 26.2 线 → 不同步升（同「同一插件在两实例可能不能同版本」教训）
- 唯一 ERROR：paper `[Essentials] unsupported server version`（既有，等正式版）
- 备份：`/upgrade-bak-20261026`（paper 102.8MB / folia 59.4MB）留存；已删旧的 `20261012-263`、`20261019`×2（共释放 ~236MB）

### 🔴 交付通道变更：**scp 直投取代 `download_from_url`（本轮起标准做法）**

面板 files API 本轮依然不可靠（配置巡检拉取 2/5 失败、单文件 111~135s）→ 直接走 **SSH + scp**，9/9 sha256 回读一致，55MB 核心秒级。

| 步骤 | 命令（Mac 侧） |
|:--|:--|
| 投递 | `scp paper-26.3-224.jar "win:E:/orzmc/mcsmanager/daemon/data/InstanceData/<uuid>/"` <br> `scp *.jar "win:E:/.../<uuid>/plugins/"` |
| 备份 | `ssh win "powershell -File E:/orzmc/tmp/backup.ps1"`（`Copy-Item` 到 `upgrade-bak-<日期>`） |
| 校验 | `powershell -File E:/orzmc/tmp/verify.ps1` → `Get-FileHash -Algorithm SHA256 -LiteralPath` vs 本地 `shasum -a 256` |
| 停/启 | 仍走面板：`command=stop` → 轮询 status=0；`open` 启动（面板抖动时 `kill` 兜底） |

**踩坑（都吃过）**：
1. **Windows OpenSSH 默认 shell = PowerShell** → `cmd /c a & b` 会被当后台作业、路径通配符行为不同 → 一律 `powershell -NoProfile -Command "..."` 或写 .ps1。
2. **三层嵌套引号（bash → ssh → PowerShell）必翻车**（`\.Line` / `ExpectedExpression`）→ **脚本落盘 + `scp` + `powershell -File`**，脚本内只用 ASCII。
3. **Windows 输出是 GBK** → 本地管道加 `LC_ALL=C tr -d '\r'`，脚本里不要输出中文。
4. **面板 `command=stop` 请求可能 TLS 超时/断连但仍已送达**（本轮 folia 报 2 次 ERR，实际服务照常停止）→ 见 status=0 即可，别重复发。
5. 冷启动：paper 131s、folia 105~140s 才 `status=3`；**串行启动**（paper `Done` 后再起 folia）避免 Folia Watchdog。

## 2i. 2026-11-02 实录（第六轮：Paper 26.3-237 + Geyser 1280 + LuckPerms 5.5.90 + voicechat 2.6.27 + GP 16.18.8 / GP3D 19.0.5 + 交付包）

> 触发：老板「核心和插件都升级，升级后打包放到 S: 盘」。距上一轮（10-26）一周，版本已前进。

| 实例 | 升级项 | 验证 |
|:--|:--|:--|
| papermc-test | Paper **224 → 237（STABLE）**、Geyser **1271 → 1280**、LuckPerms **5.5.88 → 5.5.90**、voicechat **2.6.26 → 2.6.27**、GriefPrevention **16.18.7 → 16.18.8**（同时把无版本文件名 `GriefPrevention.jar` 改为 `GriefPrevention-16.18.8.jar`） | ✅ `Paper 26.3-237-main@7e88a0d`、`Done (93.6s)`、Geyser `Started UDP 19132` |
| folia-test | Geyser **1271 → 1280**、LuckPerms **5.5.90**、GP3D **19.0.1 → 19.0.5** | ✅ `Folia 26.2-7`、`Done (96.7s)` |

- **Folia 核心仍不升**：26.3 线到 11-02 只有 **build 6（ALPHA）** → 保持 26.2-7（BETA）
- 跳过（同既有纪律）：Via 三件套（仅 5.12.3-SNAPSHOT）、packetevents（`2.14.0+spigot` 同版本）、GrimAC（本地 alpha 更新）、folia 的 WE/WG
- 全程：SSH 实读清单 → 上游比对 → curl 下载+哈希 → console `stop`（这次两端各 20s 干净停机）→ `upgrade-bak-20261102` 备份 → scp 投递 → **8/8 sha256 远端=本地** → 串行启动验收 → 打包交付
- 交付：`~/Downloads/orzmc-upgrade-20261102/`（01-core / 02-plugins-paper / 03-plugins-common / 04-plugins-folia + SHA256SUMS + README + ANNOUNCEMENT + SYNC-GUIDE）+ 同名 zip（103MB，`unzip -t` 无错、路径全 ASCII）

### 本轮新增坑

0. 🔴 **比对「最新版」必须先按 `version_type=release` 过滤，再比日期**（2026-11-02 真实疏漏）：ViaVersion 在 Modrinth 上最新一条是 `5.12.3-SNAPSHOT`（beta），若只看「最新一条」就会把整项当 SNAPSHOT 跳过，而底下躺着 10-27 发布的 **5.12.2 正式版**。→ 判定顺序：先取 release 集合里版本号最高的，再判断「是否等于部署版」；SNAPSHOT/BETA 只作参考列，不参与「是否需要升级」的结论。

1. 🟡 **`E:/orzmc/tmp` 会消失**（一周后重跑时 scp 报 `No such file or directory`）→ 每次先 `New-Item -ItemType Directory -Force` 再造 .ps1。
2. 🟡 **`paper-26.3-<build>.jar` 名字随构建变**：升级要「投新名 + 删旧名」，`start.sh` 的 `sort -V | tail -1` 会自动选最高版本，删旧前必须已备份。
3. 🟡 **无版本号文件名的插件（`GriefPrevention.jar`）顺手改成 `<名>-<版本>.jar`**，让 `mc_version_check.py` 的前缀映射能识别，避免下轮报「未识别 jar」漏报升级。
4. 🟢 面板本轮响应好（stop 20s 到位、status 查询 5~15s）；**同一面板时快时慢，脚本仍需重试 + 超时容忍**。

## 2j. 2026-11-09 实录（第七轮：Paper 246 + Geyser 1298 + LP 5.5.91 + WG 7.0.21 + OrzMC 1.0.30；folia 二批三件）

> 触发：老板按巡检报告批复 #2/#3/#4「纳下轮」，另追加 folia 独有三件。

| 端 | 升级项 | 验证 |
|:--|:--|:--|
| papermc-test | Paper **237 → 246（STABLE，11-09 发布）**、Geyser **1280 → 1298**、LuckPerms **5.5.90 → 5.5.91**、WorldGuard **7.0.20 → 7.0.21** | ✅ `Paper 26.3-246-main@b31b4b5`、`Done (94.1s)`、Geyser `Done (5.49s)` |
| folia-test | Geyser **1298**、LuckPerms **5.5.91**（WG 保持 7.0.19） | ✅ `Done (106.9s)` |
| folia-test（二批） | AxGraves **1.32.1 → 1.32.2**、ExecutableEvents **3.26.10.17 → 3.26.11.2**、SCore **5.26.10.20 → 5.26.11.2**（三件均 Modrinth release，**SCore↔EE 必须成对升**） | ✅ 三件 `Enabling` 均出现在日志、`Done (99.0s)`、无 SEVERE |
| Exaroton | Paper 246（平台自带）+ Geyser **1298**、LuckPerms **5.5.91**、OrzMC **1.0.29 → 1.0.30（Release）** | ✅ `Done (37.4s)`，回读 sha256 3/3 |

- 交付包：`~/Downloads/orzmc-upgrade-20261109/`（8 jar / 目录 117MB / zip **111MB** / `SHA256SUMS.txt` 8 条，`unzip -t` 无错）
- 校验链：本地 `unzip -t` 5/5 + `plugin.yml` 版本 → 测试服远端 sha256 **6/6** 一致 → Exa PUT 后回读 **3/3** 一致

### 本轮新增坑（都是真踩过的）

0. 🔴 **备份必须「移出目录」（Move-Item），不能只 Copy**：旧 jar 留在 `plugins/` 会与新 jar **同时被加载**（Geyser、LuckPerms 这种同 plugin 名双份尤其危险）。本轮起流程改为：`Move-Item` 到 `upgrade-bak-<日期>/` → 目录里只剩新版。
1. 🔴 **Modrinth 只提供 `sha512` / `sha1`，不提供 `sha256`**：脚本按 `hashes["sha256"]` 取会得到 `None`，随后比对必然「不一致」→ 误判下载损坏。正确做法：把 API 返回的**所有** hash 逐项比对（`hashlib.new(alg, data)`）。
2. 🟡 **报告里的旧版本号不可信**：本轮 SCore 实为 `5.26.10.20`（巡检报告写 `5.26.10.17`），按报告名去 Move 直接 `[skip missing]` → **升前一律 `ls` 实读文件名**。
3. 🟡 **OrzMC 有启动自更新**：paper 侧 `1.0.29-dev.427` 启动后自动升到 `1.0.30`，不必手工投递；Exaroton 端不会自更新（平台无更新源），**必须手工上传**。
4. 🔴 **PowerShell 脚本一律纯 ASCII**（一天内踩两次）：`…` `→` 全角括号等字符经 SSH 下发后按 GBK 解析 → 字符串引号失衡，报一串 `表达式或语句中包含意外的标记`，报错位置与真正原因毫无关系。脚本里不要输出中文。
5. 🟢 冷启动基线更新：paper **94–109s**、folia **102–107s**、Exa **37s**（判定 `Done (` 要用本次新落的日志，别看滚动缓冲）。
6. 🟢 **Exaroton 升级后不必改 Geyser 配置**：平台用环境变量覆盖 `transport` / 端口 / `advertise-addresses`（详见 `nethernet.md §5.6`），文件里的值只是静态声明；验收以「`<域名>:19132` 返回 308 → 跟随 HTTPS 得 `/v1/join` 200」为准。

## 2k. 跨大版本线 + 代理侧 Geyser 的一轮（**实例保持停止**时的验收口径）

> 形态区别于 §2d–§2j：老板明确要「后端保持停止，自用验证再起」→ 本轮**只做文件层升级**，不起服验收。
> 适用场景：入口已迁统一代理（ADR-036）后，三块要一起动 —— 实例内 Geyser-Spigot、代理侧 Geyser-Velocity、Exaroton 侧 Geyser。

| 端 | 升级项 | 验收证据（无启动日志时） |
|:--|:--|:--|
| papermc-test（停止态） | Paper STABLE 新版 + Geyser-Spigot 新版 | 远端 `Get-FileHash` = 本地 sha256；根目录只剩单一版本化核心 jar |
| folia-test（停止态） | Folia 跨线（26.2→26.3 STABLE）+ Geyser + EE + SCore 成对 | 同上（逐件比对） |
| orzmc-velocity（运行中） | Geyser-Velocity 新版 | 重启后日志 `Loaded plugin geyser <版本>` + `Built-in signaling started on ...` + `Done (Xs)` |
| Exaroton（OFFLINE） | Geyser-Spigot + WorldGuard | `PUT` 后 `GET` 回读 sha256 一致 → `DELETE` 旧 jar → `files/info/plugins/.` 确认只剩单版本 |

**不起服时验收链 = 三层证据**：① 上游→本地哈希直验 ② 远端 `Get-FileHash` 与本地逐字节一致 ③ 目录里只剩目标版本（旧件已 Move 出 `plugins/`）。**启动验收留给老板自用时做**，交付包 `SYNC-GUIDE.md` 里必须写清「串行启动 + 首启会做世界数据升级 + 重点看哪几个插件 Enabling」。

**代理侧 jar 换版顺序（唯一可行写法）**：备份旧 jar 到 `E:/orzmc/tmp/` → `docker stop orzmc-velocity` → `scp` 覆盖 `E:/orzmc/eagler/proxy/plugins/Geyser-Velocity.jar` → `Get-FileHash` 校验 → `docker start` → 看日志。原因见 SKILL.md Pitfalls「运行中容器的 bind mount jar 无法覆盖」。

**跨大版本线（Folia 26.2 → 26.3）必须同时给出回滚路径**：`start.sh` 取 `sort -V | tail -1`，所以回滚 = 删新版核心 jar + 把 `upgrade-bak-<日期>/<旧核心>.jar` 移回根目录，无需改启动命令。跨线前用 Modrinth `game_versions` 逐件核对 folia 侧插件是否声明新版本线；查不到声明的（如 GP3D / EssentialsC / SimpleLogin）单独列成「启动时重点观察项」，不要默认它们能用。

**Exaroton 写文件的定型流程**（离线校验写在脚本里，别靠记忆）：脚本开头断言 `GET /v1/servers/{id}` 的 `status == 0`，否则直接退出不写；`PUT /files/data/plugins/<name>.jar/`（body=裸字节）→ `GET` 回读 sha256 比对 → `DELETE /files/data/plugins/<旧名>.jar/` → `GET /files/info/plugins/.` 复核列表。

## 3. 机制与坑

1. **MCSM 面板/API stop 会置 `eventTask.ignore=true` 并落盘** → `autoRestart` 名存实亡（下次 daemon 重启内存复位，但磁盘仍 true）。测试实例本就手动启停，影响可控；如需恢复须改 Windows 侧 `InstanceConfig/<uuid>.json`。
2. **`download_from_url` 是 daemon 侧异步任务**：投递大文件（64MB 核心）后要等 20~30s 再启动，避免半包。
3. **读文件两步法**：`POST /api/files/download` 签发凭据（同账号 3s 限流，脚本内串行 + sleep 3.2~3.6s）→ `GET {addr}/download/{pwd}/{文件名}`。
4. **别用 `nohup` 起长任务**（Hermes 禁 shell 后台包装）→ 用 `terminal(background=true, notify_on_complete=true)`。
5. **回读失败≠投递失败**：启动后 `update/` 被消费 → 以「插件版本日志 + `plugins/` jar sha」为准。
6. **第三方插件无需人工迁配置**：Geyser/LuckPerms/AxGraves/EssentialsC/SCore/ExecutableEvents 本次升级前后配置**逐字节无变化**（或仅注释里的版本号变化）→ 它们的 schema 未变；有捆绑默认的可用配置合并工具做缺键兜底检测。
7. **GriefPrevention3D 无 `config.yml`**（默认生成在 `GriefPreventionData/`），别在 `plugins/GriefPrevention3D/` 找配置。
