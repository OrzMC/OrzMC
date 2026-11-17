# 配置差异审计（2026-09-09 v4 起：两端模型；历史三端档案见下方时间线）

> **v4（2026-09-09，平台迁移 Windows 后）**：巡检端 = **MCSM（mcs.{SERVER_NAME}.cn Windows 运行栈，原本地测试服迁移后）+ Exaroton** 两端。
> 本地端退役（目录直读废止）、{SERVER_HOST} 旧远程 MCSM 废弃。**关键变化**：
> - 配置清单 = MCSM 面板 API **递归扫描**（`mcsm_env.mcsm_scan_plugin_configs`，真源，不再依赖本地目录；自动过滤 macOS `._` 垃圾）
> - MCSM 配置拉取 = 面板 REST **list + https 下载**（download 两步法 addr 现返回 `wss://host:443`，实测 **HTTPS GET https://host/download/{pwd}/{fn} 可用**；mcsm_env v4 兼容；请求须带 Mozilla UA，面板中间件拦 Python UA）
> - **性能模型（方案 B，joker 普通用户）**：面板 files API 全系**账号级限流 ~3s/次**（download 签发路由 `speedLimit(3)` 硬编码；files/list 实测同限流）→ MCSM 端 66 文件拉取下限 ≈ 签发 66×~3s ≈ 3.5-5min + 并行拉流 30s；scan 带清单缓存（`/tmp/mcsm_cfg_manifest.json`，顶层目录校验命中即跳过递归）→ 缓存命中总耗时实测 **6m34s**（零失败）；量级提速需管理员 API key（跳过限流，方案 A，未启用）
> - 脚本：`orzmc_config_audit.sh` v4 + `fetch3_configs.py` v4（两阶段：串行签发 + 并行拉流）+ `cmp3_configs.py` v4（两目录对比）+ `cmp3_report.py` v3（两端报告 /tmp/cmp3_report_latest.md）
> - cron：并入「orzmc MC 每周巡检」`d81c8325fe8b` 每周一 9:00（原三 job 已删）；MCSM API key = .env `MCSM_LOCAL_API_KEY`（面板需开 API 密钥功能）
> - 2026-09-09 首跑：✅ SUCCESS，Exa=52/MCSM=66 文件（零失败），34 一致/25 差异/8 数据（差异多为 Exa 端缺失 + 定位类差异，属预期漂移项）

---

## 🧾 已确认「有意差异」白名单（2026-10-12 老板逐条拍板 · **周报勿再重复报为待决策**）

> 用途：每周巡检报告里这些项应**直接标「✅ 有意差异（勿报）」**，不再进「待用户决策」。新增确认项追加到本表。

| # | 项 | 两端值 | 老板决策 |
|:--|:--|:--|:--|
| 1 | **GrimAC 配置** | MCSM 有 / Exa 全缺（10 文件） | **Exaroton 上不需要加反作弊插件** → 有意缺失，勿再报 |
| 2 | **GetMeHome `limit.yml`** | MCSM=30 / Exa=10 | **有意为之**（家上限不同） |
| 3 | EzShops `game-mode`/`language` | smp+en / prison+zh | 分属不同玩法/语言，预期 |
| 4 | OrzMC `channel` | beta / release | 测试端 beta、生产端 release |
| 5 | OrzMC IM 凭据（`im.yml`/`easybot.yml`） | 内网 easybot+builtin / 公网域名+easybot | 环境差异，预期（两张 IM 通道并行保留） |
| 6 | CustomWorldHeight `config.yml` | MCSM 有 / Exa 缺 | 插件已计划移除，预期 |
| 7 | bStats `serverUuid` | 两端不同 | 每服独立 UUID，正常 |
| 8 | 运行时数据文件（homes/transactions/ip_blacklist/permission/player-shops/daily-sells…） | 两端独立 | 玩家数据，**非配置漂移** |

### 2026-10-12 待执行（老板已批准，按端分工）

| 项 | 目标 | 谁做 | 状态 |
|:--|:--|:--|:--|
| WorldEdit `disallowed-blocks` + `limits` **统一** | Exa 补齐 MCSM 基准：`limits.max-blocks-changed 1000000/2000000` + disallowed 追加 `sand/red_sand/gravel/water/lava`（Exa 当前 `-1/-1` 无限 + 只禁 tnt/fire/bedrock = **防崩服方案 A 未落地**） | Exaroton 端（生产） | ⏳ 待执行 |
| Geyser `config-version` Exa 7→8 | 随 Geyser 插件升级（Exa 现 build 1230 → 1251）由插件自动迁移，或补键 | Exaroton 端 | ⏳ 待执行 |
| bStats `enabled` 对齐 | **Exa true → false**（基准端 MCSM=false） | Exaroton 端 | ⏳ 待执行 |
| OrzMC 主插件升级 + 配置迁移 | Exa 现 **1.0.24**（config-version 12）→ Hangar Release **1.0.29**（config-version 15） | Exaroton 端 | ⏳ 待执行 |
| Paper 26.3 采用 | **维持 26.2**（GrimAC 无正式版支持 26.3） | 全体 | ✅ 已定（老板 2026-10-12） |
| `mc_version_check.py` 映射表 | GriefPrevention3D / SkinsRestorer 未识别 → 已补 PREFIX_NAME | Hermes | ✅ 已完成 |
| Cloudflare 隧道自愈 | Windows 侧已加 | 老板 | ✅ 已完成（2026-10-12） |

# 三端配置差异审计（2026-08-11 三次审计；2026-08-12 重启审查 → v2 只审查不重启；2026-08-17/24/31 审查超时失败（MCSM 侧密钥三周未修）；**2026-09-03 v3：本地端迁 MCSM 本机栈**；**2026-09-07 v3 首跑审查超时失败：远程 MCSM 密钥四周未修 + 本机 MCSM 面板 API「API 响应异常」**）

> **v3（2026-09-03，本地测试服迁 MCSM 后）**：三端 = **本地端**（本机 MCSM 栈 Paper 实例 716c2fb7，**目录直读复制** → `/tmp/mcsm_local_configs2`）/ **Exa**（Exaroton 海外服 API）/ **MCSM**（远程 Win11 面板 API）。脚本 `orzmc_config_audit.sh` v3 三路并发（fetch3_configs.fetch_all），STATUS 三端文件数检查。
> ⚠️ **v10 面板下载协议不兼容**：本机 MCSM 面板为 v10.18（文件下载走 wss 私有协议，非 v9 http 两步法）——本地端配置本就在宿主（InstanceData/<uuid>），fetch3 用**目录直读复制**（产物与 API 拉取目录同构，cmp3/report 复用不变）；远程 MCSM 若同为 v10 则 `mcsm_download`（v9 协议）同样失效，需 v10 wss 适配（未做，见下方根因）。
> ⚠️ **远程 MCSM 连续三周挂死根因（2026-09-03 实证）**：远程面板报「未开启API密钥创建功能」= 远程 `enableApiKey=false`（MCSM API key 需面板开启 + 用户配置 apiKey；.env `MCSM_API_KEY` 同步）。**修复需在远程 Win11 面板操作**（本机栈已同法修复验证：SystemConfig enableApiKey=true + User apiKey + 重启 web → API 通）。
> 工具：`scripts/cmp3/fetch3_configs.py`（拉取）+ `cmp3_configs.py`（对比）+ `cmp3_diff_detail.py`（明细）+ `cmp3_report.py`（完整报告生成）+ `cmp3_trend.py`（新旧报告变化跟踪）。
> 基线：77 个配置文件（核心 7 + 插件 70），**重启后全量审查（2026-08-11 四次）：8 个差异文件、8 个运行时数据文件、61 个完全一致**。
> **完整报告（保留最近两份，最新为准；其余已轮换·cron 仅 file 工具未物理删除，留档备查）**：
> - `references/config-drift-report-20260907.md`（2026-09-07 审查·❌ 脚本超时 3600s·v3 首跑：本地端 93/93 + Exa 79 成功、MCSM 远程 0 文件挂死·连续四周同因·最新）
> - `references/config-drift-report-20260831.md`（2026-08-31 审查·❌ 脚本超时 3600s·Exa 77/77 成功 MCSM 0 文件挂死·连续三周同因·已轮换）
> - `references/config-drift-report-20260824.md`（2026-08-24 审查·❌ 脚本超时 3600s·Exa 77/77 成功 MCSM 0 文件挂死·已轮换）
> - `references/config-drift-report-20260817.md`（2026-08-17 审查·❌ 脚本超时 3600s 无数据·基线快照·已轮换）
> - `references/config-drift-report-20260812.md`（基线 61/8/8·已轮换）
> - `references/config-drift-report-20260811.md`（已轮换）
> - `references/config-drift-report-20260810.md`（已轮换）

> **变化跟踪（20260907 三端配置审查·❌ 失败：脚本超时 3600s，连续四周同因；v3 首跑：本地端(目录直读) 93/93 + Exa 79 成功落盘，远程 MCSM 0 文件挂死；本机 MCSM 面板 API 首次报「API 响应异常」）**：
> - **执行**：09:15:41 启动 → 三端状态读取完成（MCSM 远程 ❌「未开启API密钥创建功能」，**与 0817/0824/0831 同因，连续四周**；**MCSM 本机栈 ❌「API 响应异常」——首次出现的新信号**；Exa ✅ status=0(OFFLINE) 未重启；三端均未重启）→ 并发拉取阶段 **本地端 93/93 完整落盘**（目录直读，不受面板 API 影响）、**Exa 79 文件完整落盘**（/tmp/exa_configs2 实测 79；本地清单 93 中约 14 路径为本地独有/Exa 端不存在），**远程 MCSM 0 文件**（/tmp/mcsm_configs2 实测 0）→ python fetch_all 未返回（卡远程 MCSM 线程）→ 被 cron 3600s 超时杀死 → `/tmp/cmp3_report_latest.md` 未生成、无 STATUS 行 → 判定 **❌ FAIL**
> - **三端状态（09:15，均未重启）**：MCSM 远程 ❌ API 密钥异常（**连续四周，0824/0831 建议修复均未落地，需人工在 Win11 面板操作**）；**MCSM 本机栈 ❌ API 响应异常（🆕 需人工查 mcs.{SERVER_NAME}.cn 面板服务健康度；实例目录完好，不影响目录直读）**；Exa ✅ status=0(OFFLINE)；本地端未重启（设计）
> - **审查无新对比数据**：差异基线沿用 20260812（61 一致 / 8 差异 / 8 数据）；⚠️ **口径变更**：v3 首跑，本地端 = 本机 MCSM Paper 实例（清单扩容 93 文件），本地列与旧基线不可直接同比
> - **对齐项部分验证（Exa 今日新鲜数据 vs 本地端今日实测，新口径）**：sync-chunk-writes Exa=false 平台保留（0811 结论维持）、command-spam-threshold-seconds=100000 两端确认生效、force-gamemode/allow-flight/online-mode/enforce-whitelist ✅ 一致、difficulty/jmx/query 两端同为 easy/true/true（旧基线差异项随口径切换消失，非对齐动作）、max-tick-time 60000/600000 平台差异不变、resource-pack-prompt 无实质差异、view/simulation-distance 本地 6/3 vs Exa 10/5 维持（0831 观察项新口径复核仍在）；MCSM 远程侧全部对齐项无法验证（连续四周）
> - **诊断进展（vs 0831）**：卡点第三次实证锁定**远程 MCSM 线程**——本周 Exa 与本地端均已完整落盘仍被拖死整脚本（两端数据齐全却零产出，「部分报告」论据最强）；**🆕 本机 MCSM 面板 API「API 响应异常」为新信号**；修复建议（总时长护栏/fast-fail/部分报告）三周未落地，本周照挂
> - **修复建议（0824/0831 已提，本周第三次重申）**：① 修复远程 MCSM 面板 API 密钥（连续四周，不修则每周审查必挂）；② **排查本机 MCSM 面板 API「API 响应异常」**（mcs.{SERVER_NAME}.cn 服务健康）；③ 脚本加总时长护栏 + MCSM 错误响应 fast-fail；④ MCSM 失败时保留 Exa×本地端数据出部分报告；⑤ cron 兜底维持（无 STATUS 行/无报告判 FAIL）

> **变化跟踪（20260831 三端配置审查·❌ 失败：脚本超时 3600s，连续三周同因；Exa 77/77 成功，MCSM 0 文件挂死）**：
> - **执行**：09:15:54 启动 → 三端状态读取完成（MCSM ❌「未开启API密钥创建功能」，**与 0817/0824 同因，连续三周**；Exa ✅ status=0(OFFLINE) 未重启；本地未重启）→ 并发拉取阶段 **Exa 77/77 完整落盘**（/tmp/exa_configs2 实测 77 文件），**MCSM 0 文件**（/tmp/mcsm_configs2 实测 0 文件），python fetch_all 未返回 → 被 cron 3600s 超时杀死 → `/tmp/cmp3_report_latest.md` 未生成、无 STATUS 行 → 判定 **❌ FAIL**
> - **三端状态（09:15，均未重启）**：MCSM ❌ API 密钥异常（**连续三周，0824 已建议修复未落地，需人工查面板**）；Exa ✅ status=0(OFFLINE)；本地未重启（设计）
> - **审查无新对比数据**：差异基线沿用 20260812（61 一致 / 8 差异 / 8 数据）；**对齐项部分验证（Exa 今日新鲜数据 vs 本地实测）**：sync-chunk-writes Exa=false 平台保留（0811 结论维持）、command-spam-threshold-seconds=100000 Exa/本地均确认生效（2026-08-12 对齐值）、max-tick-time 60000/600000 平台差异不变、resource-pack-prompt 无实质差异；MCSM 侧全部对齐项无法验证（连续三周）
> - **诊断进展（vs 0824）**：与 0824 完全同构——Exa 侧再次 77/77 完整落盘，卡点再次锁定 **MCSM 线程**；无新信息量，根因（MCSM 面板密钥）三周未修，本周照挂
> - **观察项复核**：0824 观察「本地 view-distance 8→6、simulation-distance 6→3」今日实测**仍为 6/3**（~/minecraft-server/server.properties），确认持续存在，待人工确认是否有意为之
> - **修复建议（0824 已提，本周重申）**：① **修复 MCSM 面板 API 密钥**（连续三周，不修则每周审查必挂）；② 脚本加总时长护栏 + MCSM 错误响应 fast-fail；③ MCSM 失败时保留 Exa 数据出双端部分报告；④ cron 兜底维持（无 STATUS 行/无报告判 FAIL）

> **变化跟踪（20260824 三端配置审查·❌ 失败：脚本超时 3600s；Exa 77/77 成功，MCSM 0 文件挂死）**：
> - **执行**：09:15:31 启动 → 三端状态读取完成（MCSM ❌「未开启API密钥创建功能」，**与 0817 同因，连续两周**；Exa ✅ status=0(OFFLINE) 未重启；本地未重启）→ 并发拉取阶段 **Exa 77/77 完整落盘**（/tmp/exa_configs2 实测 77 文件），**MCSM 0 文件**（/tmp/mcsm_configs2 实测 0 文件），python fetch_all 未返回 → 被 cron 3600s 超时杀死 → `/tmp/cmp3_report_latest.md` 未生成、无 STATUS 行 → 判定 **❌ FAIL**
> - **三端状态（09:15，均未重启）**：MCSM ❌ API 密钥异常（连续两周，需人工查面板）；Exa ✅ status=0(OFFLINE)；本地未重启（设计）
> - **审查无新对比数据**：差异基线沿用 20260812（61 一致 / 8 差异 / 8 数据）；**对齐项部分验证（Exa 今日新鲜数据 vs 本地实测）**：sync-chunk-writes Exa=false 平台保留（0811 结论维持）、command-spam-threshold-seconds=100000 Exa/本地均确认生效（2026-08-12 对齐值）、max-tick-time 600000 平台差异不变；MCSM 侧全部对齐项无法验证
> - **诊断进展（vs 0817）**：0817 两侧均 0 文件无法定位卡点；本次 Exa 77/77 落盘反证 **卡点锁定 MCSM 线程**（面板 API 密钥异常 → 77 文件 × 多轮重试耗尽时间窗，整脚本无总时长护栏）
> - **新增观察**：本地测试服 view-distance 8→6、simulation-distance 6→3（vs 0811 基线；疑似 2026-08-18 Folia 接管后性能档调整，**需人工确认是否有意为之**）
> - **修复建议**：① 修复 MCSM API 密钥（连续两周，不修则每周审查必挂）；② 脚本加总时长护栏 + MCSM 错误响应 fast-fail；③ MCSM 失败时保留 Exa 数据出双端部分报告；④ cron 兜底维持（无 STATUS 行/无报告判 FAIL）

> **变化跟踪（20260817 三端配置审查·❌ 失败：脚本超时 3600s 无数据）**：
> - **执行**：09:15:11 启动 → 拉取阶段（fetch3 并发拉取）挂死，**被 cron 3600s 超时杀死**；`/tmp/cmp3_report_latest.md` 未生成（文件不存在）、/tmp/exa_configs2 与 /tmp/mcsm_configs2 均 0 文件、无 STATUS 行 → 判定 **❌ FAIL**
> - **三端状态（09:15，均未重启）**：MCSM ❌ 状态查询报「未开启API密钥创建功能」（面板侧 API 密钥权限异常，上轮 0812 未出现，需人工查面板）；Exa ✅ status=0(OFFLINE)；本地未重启（设计）
> - **审查无新数据**：差异数不可比，基线沿用 20260812（61 一致 / 8 差异 / 8 数据）；对齐项（sync-chunk-writes 等）本次未验证，上轮结论维持（Exa sync-chunk-writes 平台保留 false）
> - **卡点分析**：python 输出块缓冲 + 进程被杀 → 日志停在「--- 2. 三端配置审查 ---」，无法定位卡在 Exa 还是 MCSM；各单请求有超时（Exa GET 60s / MCSM POST 20s×3、下载 GET 60s×4）但 **MCSM 侧 77 文件×多轮重试最坏数小时、整脚本无总时长护栏**
> - **修复建议**：① 查 MCSM 面板 API 密钥权限/重新生成（同步 .env）；② 脚本加总时长护栏（超时即输出 STATUS ❌ exit 非 0）；③ fetch3 错误响应 fast-fail 勿耗满重试；④ cron 侧「无 STATUS 行/无报告文件」直接判 FAIL

> **变化跟踪（20260812 三端重启+审查）**：
> - **三端重启**：MCSM ✅ 已重启（运行 15min<60min，玩家 1/150）；本地 ✅ 启动完成（`Done` 日志确认，pid 40655）；Exa 从 STOPPED(0) 启动 → LOADING(2)×3 → **STARTED(1) 稳定×10 → 实际已启动成功**，但脚本报「⚠️ 未确认」——**脚本 bug：等待常量写成 4（=RESTARTING），1（=STARTED）才是运行态**，正常 start 路径等不到 4（建议修复）
> - **审查 ❌ 失败（无新差异数据）**：脚本 125/136/137 行用 `timeout`，**macOS 无此命令**（已知坑「macOS 无 timeout」未应用于脚本）→ fetch3 未执行、拉取 **Exa=0 / MCSM=0 文件**，cmp3 对比/报告未运行，`/tmp/cmp3_report_latest.md` 仅 87B 报错行。差异数不可比，**基线沿用 20260811（61 一致 / 8 差异 / 8 数据）**
> - **对齐项验证未完成**：Exa/MCSM server.properties 未拉取，仅本地 `sync-chunk-writes=true`；上轮对齐结论（Exa sync-chunk-writes 平台保留 false、SkinsRestorer/DeathChest/paper-global 已生效）维持不变
> - **2026-08-11 已知问题「Exa 启动反复失败（LOADING→STARTING→STOPPED 循环+日志空）」本次未复现**（status 2→1 后稳定，无循环）
> - **修复建议**：① `orzmc_reboot_audit.sh` 的 `timeout` 改 `gtimeout`（coreutils）/`perl -e 'alarm shift; exec @ARGV'`，或去掉（fetch3 内部已有请求超时）；② Exa STARTED 判定 4→1；③ 审查失败应输出失败标记，勿静默产出空报告
> - **2026-08-12 复测确认（Geyser 升级期间）**：`sync-chunk-writes` Exa=false **平台强制再次实证**——PUT true → 重启 → 平台重写回 false（server.properties 文件头时间戳=启动时刻 10:54:55），与 8/11 结论一致：**Exa 非白名单键无法持久化，永久标记为平台保留差异，三端不期望一致**。另发现：**Exaroton 平台启动器自动升级核心**（`version_history.json`：26.2-111→26.2-112，2026-08-12 10:12 启动时自动完成）→ 三端核心版本天然可漂移（Exa 自动最新，本地/MCSM 手动），属预期，版本巡检已覆盖

> **变化跟踪（20260811 上午对齐审查 → 下午重启后审查）**：
> - **✅ 对齐项生效（重启后三端一致）**：SkinsRestorer connectionOptions（三端 `sslMode=trust&serverTimezone=UTC`）、ifNoServerBlockCommand（三端 false）、perSkinPermissionsConsent（三端无引号）；paper-global.yml `-minecraft`/`no-permission`/`secret`（MCSM 重启后与本地/Exa 一致）；DeathChest debug（三端 false）+ sound（三端 `BLOCK_CHEST_LOCKED;1.0;1.0`）；paper-global velocity.online-mode（三端 false）；paper-world-defaults enderpearl-exploit（三端 true）/max-leash-distance（三端 default）。**汇总：61 一致 / 8 差异 / 8 数据（vs 上次 60/9/8，净 -1 差异）**
> - **❌ Exa 两项回退（2026-08-11 重大发现）**：Exa 重启后 `server.properties` **sync-chunk-writes 回退 false、resource-pack-prompt 回退 `""`**。**根因：Exaroton 平台每次启动用「平台模板 + files/config 白名单 35 项」重新生成 server.properties（文件头时间戳=启动时刻）**——非白名单键（sync-chunk-writes/max-tick-time 等）PUT files/data 修改**重启即被覆盖、无法持久化**（POST files/config 也假成功，文档已记载）；白名单键（resource-pack-prompt 等）须用 `POST /files/config/{path}/` 修改（即时生效，无需重启）。**结论：Exa sync-chunk-writes 无法通过 API 对齐为 true，属平台限制**（`""` 无实质影响：require-resource-pack=false 不显示提示）
> - **保留差异不变**：GetMeHome limit 10/10/30、OrzMC allow_country_code []/[]/[CN,JP,TW,DE]（2026-08-11 为德国玩家加）、easybot 各端群/api_key、bStats UUID、paper-global max-packet-rate MCSM=10000（防攻击调高）、server.properties 18 项定位/平台差异
>
> **对齐决策（2026-08-11，用户拍板）**：
> - **第一类 7 项零风险已对齐**：velocity.online-mode 统一 false（三端都未跑 Velocity 代理）、paper-world-defaults enderpearl-exploit 统一 true（安全加固）、max-leash-distance 统一 default、DeathChest sound 统一枚举格式、SkinsRestorer perSkinPermissionsConsent 统一无引号、server.properties resource-pack-prompt 统一空。despawn hard/soft 保留 Exa 128/32（性能优化）。
> - **第二类 11 项定位/平台差异保留**（motd/端口/距离/management-server=Exaroton 平台自动等）。
> - **第三类**：sync-chunk-writes **已标记平台保留（2026-08-11 实测：Exaroton 每次启动重写 server.properties，非白名单项 PUT 修改重启后重置，放弃对齐——Exa 的 false 是性能优化，无害）**；DeathChest debug 统一 false；SkinsRestorer ifNoServerBlockCommand 统一 false；GetMeHome limit 保持 10/10/30 现状；SkinsRestorer connectionOptions **已对齐（2026-08-11 补充执行）**——三端 storage.type 均 FILE（未用 MySQL），原本是 MySQL 专用参数的默认值形态差异，按用户决策以本地最新版默认为基准统一为 `sslMode=trust&serverTimezone=UTC`。
> - 生效方式：本地/Exa 文件已改（Exa 重启后生效）；MCSM 文件已改、**等待无玩家窗口重启生效**（9 玩家在线时只写文件不重启）。
> - **重启验证（2026-08-11 上午 9 点 MCSM 自动重启 + 手动重启 Exa/本地后实测）**：MCSM ✅ 全部生效（9 点自动重启，已运行 <60min 确认新进程）；本地 ✅ 全部生效；Exa ⚠️ **server.properties 非白名单键修改被平台重启覆盖**（sync-chunk-writes/resource-pack-prompt 回退），**其余配置（paper-global/paper-world-defaults/插件 yml）修改全部持久化生效**。

## 对比工具链（新增/修复）

| 脚本 | 作用 |
|:--|:--|
| `fetch3_configs.py` | 以本地插件清单为基准，从 Exaroton + MCSM 拉全量配置到 /tmp（**2026-08-10 修复：MCSM 改串行拉取+失败自动重试（指数退避 3s×3），一次 77/77 全成功，不再有并发 500**；空文件判定用 `data is None`，0B 文件正常落盘） |
| `cmp3_configs.py` | 语义对比（已修复：server.properties 用 `=` 解析，之前假一致） |
| `cmp3_diff_detail.py` | 逐 key 输出三方值明细 |
| `mcsm_refetch.py` | MCSM 失败文件串行补拉（并发→500） |

**API 坑（拉取时实测）**：
- MCSM `/api/files/list` **必须传 `file_name`（可空串）否则返回 total=0**；page_size ≤50（200 触发 500）
- Exaroton `files/info` 用 `isDirectory` 字段（不是 `type`）
- ⚠️ **Exaroton 的 server.properties 曾被 JSON 包装写入残留**：文件尾多一行 `{"text"="server-ip\=..."}`（2009B 转义块），Java 解析为垃圾 key 无害；对比时前 73 行真实配置仍有效。**根因已定位并修复（2026-08-10）**：`exa_apply_config.py` 的 put_file 曾用 `{"text": content}` JSON 包装 PUT → 改共享模块 `scripts/exa_file.py`（GET 自动解包、PUT 裸文本）；`fix_exaroton_cfg.py` 坏依赖 /tmp/exa_file.py 已改为引用共享模块

## 一、核心配置差异（真实差异）

### server.properties（17 项真实差异，vs Exa 19 处 / vs MCSM 12 处）

| key | 本地 | Exa | MCSM | 判定 |
|:--|:--|:--|:--|:--|
| difficulty | normal | easy | easy | ⚠️ 本地测试难度与云端不同（云端 easy） |
| enable-jmx-monitoring | false | true | true | ⚠️ 云端开 JMX，本地关 |
| enable-query / query.port | false | true / 9898 | true / 9898 | ⚠️ 云端开 query，本地关 |
| enable-rcon / rcon.password | true / orztest2026 | false / 空 | false / 空 | ✅ 本地测试开 RCON（预期） |
| management-server-enabled | false | true | false | ⚠️ 仅 Exa 开管理服务器（0.0.0.0:9900） |
| management-server-secret | 本地值 | Exa 值 | MCSM 值 | ✅ 每端独立密钥（预期） |
| max-players | 20 | 20 | 150 | ⚠️ **MCSM 150 vs 本地/Exa 20**（定位差异，用户决策保留） |
| max-tick-time | 60000 | 600000 | 60000 | ⚠️ Exa 放大 10 倍（允许单 tick 长时间卡顿） |
| motd | 本地测试 | 海外服 | 国内服 | ✅ 定位差异（预期） |
| pause-when-empty-seconds | -1 | 60 | -1 | ⚠️ Exa 无人 60s 停（省钱），本地/MCSM 不停 |
| server-port | 25565 | 39742 | 25565 | ✅ 定位差异（预期） |
| simulation-distance | 6 | 5 | 3 | ⚠️ 三端都不同（本地 6 / Exa 5 / MCSM 3） |
| sync-chunk-writes | true | false | true | ⚠️ Exa 关（性能优化，崩溃丢档风险） |
| view-distance | 8 | 10 | 6 | ⚠️ 三端都不同（本地 8 / Exa 10 / MCSM 6） |
| enable-command-block | false | 无键 | 无键 | ✅ 缺省同 false |
| previews-chat | 无键 | false | 无键 | ✅ 缺省同 false |
| resource-pack-prompt | 无键 | "" | "" | ✅ 无实质差异 |

**一致性亮点**：online-mode=false（三端离线）、force-gamemode=false（三端已统一）、white-list/enforce-whitelist=true、allow-flight=true、spawn-protection=0、op-permission-level=4、enable-rcon 以外全部对齐。

### bukkit.yml
- `connection-throttle`：本地 **0** / Exa 4000 / MCSM 4000 —— ✅ 本地测试关登录冷却（预期，testing.md 记载）

### spigot.yml / paper-global.yml（行为一致，文件形态差异）
- spigot.yml：**Exa 369 行（全量展开版，显式写出 entity-activation-range animals:32/monsters:32/raiders:64 等默认值）** vs 本地/MCSM 184 行（精简版，缺省用 Paper 默认）——cmp3 交集对比确认本地显式配置的 key 三端值相同，**行为一致**，非真实差异
- paper-global.yml：三端一致 ✅

### config/paper-world-defaults.yml
- `engine-mode`：本地 **2** / Exa **1** / MCSM **2** —— ⚠️ **Exa 用原版红石引擎（1），本地/MCSM 用 Alternate Current（2）**（性能差异）

## 二、插件配置差异（真实差异）

| 插件文件 | key | 本地 | Exa | MCSM | 判定 |
|:--|:--|:--|:--|:--|:--|
| DeathChest/config.yml | debug | true | false | false | ✅ 本地调试开（预期） |
| DeathChest/config.yml | sound | `minecraft:block.chest.locked;1.0;1.0` | `BLOCK_CHEST_LOCKED;1.0;1.0` | 同 Exa | ⚠️ sound 格式不同（本地新格式 vs 云端旧枚举） |
| DeathChest/config.yml | exclude-died-player | false | 无键 | 无键 | ✅ 缺省同 false |
| GetMeHome/limit.yml | limit | 10 | 10 | **30** | ⚠️ **MCSM 家上限 30 vs 本地/Exa 10** |
| OrzMC/config.yml | allow_country_code | [] | [] | [CN, JP, TW] | ⚠️ **仅 MCSM 配 GeoIP 白名单**（1.0.15 内网短路后无害但未对齐） |
| OrzMC/config.yml | qq_group_id / title / ups | 空/占位 | 空 | '902452859' + 3 个 B站 UP | ⚠️ **仅 MCSM 配 UP 关注推广** |
| OrzMC/easybot.yml | api_server / ws_server | test-bot.{SERVER_NAME}.cn | bot.{SERVER_NAME}.cn | bot.{SERVER_NAME}.cn | ✅ 本地测试网关 vs 云端正式（预期） |
| OrzMC/easybot.yml | api_key | 各自 | 各自 | 各自 | ✅ 每端独立 key（预期） |
| OrzMC/easybot.yml | qq_group_id | 1082305302 | 1012877775 | 753649704 | ✅ 各端群不同（预期） |
| OrzMC/easybot.yml | discord_server_link | 空 | discord.gg/9JAb9vpvUE | 空 | ⚠️ 仅 Exa 有 Discord 链接 |
| SkinsRestorer/config.yml | connectionOptions | sslMode=trust | verifyServerCertificate=false&useSSL=false | 同 Exa | ⚠️ 本地 MySQL 连接参数不同（无 SSL 验证 vs 显式关 SSL） |
| SkinsRestorer/config.yml | perSkinPermissionsConsent | 'I will follow the rules'（带引号） | 无引号 | 无引号 | ✅ YAML 引号差异，值相同 |
| SkinsRestorer/config.yml | ifNoServerBlockCommand | true | false | false | ⚠️ 本地 true vs 云端 false（无皮肤时禁命令） |
| bStats/config.yml | serverUuid | 各自 | 各自 | 各自 | ✅ 实例标识（预期） |

## 三、非配置差异（玩家数据/运行时，正常，勿"对齐"）

- BackOnDeath/config.yml：玩家 UUID → 死亡坐标（三端玩家不同）
- GetMeHome/homes.yml：玩家家数据（三端玩家不同）
- EzShops/shop-rotations.yml：商店轮换 next-change 时间戳
- OrzMC/permission.yml：builder-promotion 审批请求记录（仅 MCSM 有历史）
- OrzMC/ip_blacklist.yml：空列表格式差异
- Essentials/userdata、EzShops/shop/*（价格/菜单为配置，玩家商店为数据）

## 四、结论与建议（按用户三端配置决策原则：默认对齐、定位保留）

**建议对齐（功能类，非定位）**：
1. GetMeHome limit：MCSM 30 → 10（或决策统一值）——需玩家通知（已有 30 上限用户）
2. DeathChest sound 格式：本地 `minecraft:` 前缀（新版格式）→ 云端同步
3. SkinsRestorer ifNoServerBlockCommand：云端 false → 按意愿对齐（本地 true 是测试态？）
4. OrzMC allow_country_code：三端统一 []（1.0.15 已有内网短路，白名单无必要）或统一 [CN,JP,TW]
5. OrzMC UP 推广（qq_group_id/title/ups）：确认是否三端都要，若只 MCSM 保留则记录为定位差异

**建议保留（定位/环境差异）**：
- motd、server-port、max-players、view-distance/simulation-distance（性能档）、pause-when-empty-seconds（Exa 省钱）、enable-rcon（本地测试）、enable-jmx/query（云端监控）、management-server（Exa）、easybot 网关/群/api_key、bStats UUID

**风险提示**：
- Exa `sync-chunk-writes=false` + `max-tick-time=600000`：性能优先配置，崩溃可能丢 chunk 数据
- Exa `engine-mode=1`（原版红石）：与本地/MCSM 的 AC 红石行为不同，**跨服传送后红石机器行为可能不一致**

## 附：复现命令

```bash
# 1. 拉取（改配置前跑，落 /tmp/exa_configs2 /tmp/mcsm_configs2）
python3 ~/.hermes/skills/gaming/orzmc/scripts/cmp3/fetch3_configs.py
# MCSM 并发失败后补拉：
python3 ~/.hermes/skills/gaming/orzmc/scripts/cmp3/mcsm_refetch.py
# 2. 对比
python3 ~/.hermes/skills/gaming/orzmc/scripts/cmp3/cmp3_configs.py /tmp/exa_configs2 /tmp/mcsm_configs2 ~/minecraft-server
# 3. 明细
python3 ~/.hermes/skills/gaming/orzmc/scripts/cmp3/cmp3_diff_detail.py > /tmp/diff_detail.txt
```

## 附2：Exaroton JSON 包装污染修复记录（2026-08-10）

**问题**：早期脚本用 `{"text": 全文}` JSON 包装 PUT 写 Exaroton 配置 → 被原样存为文件内容：
- YAML 文件尾残留 `text: "..."` 折叠块（整个配置的转义副本，Paper 解析为垃圾 key）
- server.properties 尾残留 `{"text"="..."}` 单行

**污染源**：`exa_apply_config.py` 的 put_file 用 JSON 包装 PUT（2026-08-09 文档已修正但脚本漏改）

**修复**：
1. 新建共享模块 `scripts/exa_file.py`：GET 自动解包（yaml.safe_load 取 text / json 解包），**PUT 必须裸文本**
2. `exa_apply_config.py` / `fix_exaroton_cfg.py`（原依赖 /tmp/exa_file.py 已坏）改用共享模块
3. 新增 `scripts/exa_recover_residue.py`：从残留块解出原始完整配置并覆盖恢复
4. 线上已恢复 3 个文件：paper-global.yml（160 行完整版）、paper-world-defaults.yml（328 行完整版）、server.properties（删残留行）

**原则（用户拍板 2026-08-10）**：残留块 text 值 = 配置文件原始完整内容，**以原始内容为准恢复**。
⚠️ 例外：server.properties 的残留块是旧快照（force-gamemode=true 等废弃值）→ 只删残留行保留当前真实段。

**残留块解包方法**：`yaml.safe_load(整个文件)` 取 `text` 键 → 再解 `\n`→换行、`\=`→`=`、`\"`→`"`（双重转义）

**修复后对比更真实**（残留块曾干扰 cmp3 判定）：
- paper-global.yml：恢复出 timings 段等 11 键（此前被残留块掩盖）
- paper-world-defaults.yml：despawn-ranges 显式值、anti-xray hidden-blocks 差异（Exa 无 raw_copper_block/raw_iron_block 等）
