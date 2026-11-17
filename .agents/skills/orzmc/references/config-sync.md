# 部署配置同步（Deploy-Time Config Sync，2026-08-11 从 deployment-config-sync 技能合并）

> 场景：升级后配置缺失告警（config drift）：diff 三端配置、fallback 判定、补键同步。配置同步方法论归本节，工具链/API 坑见 `three-end-config-drift.md`。

**核心教训（2026-08-08 OrzMC 插件上线实证）**：升级二进制 ≠ 升级配置。
新代码新增的配置键（如模板键 `review_submitted`、`rank_promoted`）在开发机配置里已更新，
但线上/测试服的旧配置没有——启动时健康检查报「缺失: templates.xxx」，
看起来像 bug，实际是 **config drift**（功能靠代码 fallback 兜底正常，但告警吵 + 新文案不可自定义）。

## 触发场景

- 升级插件/jar 后，服务器/服务启动日志出现「配置健康检查发现问题」「缺失: xxx.yyy」
- 新功能上线后线上行为正常但告警不断
- 多环境（本地/测试/生产）配置版本不一致

## 排查路径（先判定是代码 bug 还是配置 drift）

1. **看健康检查实现**：它通常遍历一个**规范键列表**（如 `TemplateKeys.ALL`）校验
   `cfg.contains("templates.<key>")`——缺失条目 = 旧配置，不是坏代码。
2. **看读取方有无 fallback**：形如 `resolveTemplate(key, cfg, fallback)`——
   `fallback == null ? "" : fallback`。**有 fallback → 功能正常，纯告警**。
3. **对比三端配置**：下载远端配置（Exaroton: `GET files/data/...`；MCSM:
   `POST /api/files/download` 换 hostname 后 GET），与本地/repo 版本 `diff`。
   - 只差新增键 + 远端无自定义 → 全量覆盖安全
   - 远端有自定义 → 只补缺失键，绝不盲覆盖
4. **修复后验证**：重启/重读配置，确认健康检查告警消失。

## 部署清单（每次二进制升级必做）

1. 升级 jar 后 **diff 远端配置 vs repo 版**（下载 → diff），别只看版本号。
2. 配置改动与读它的代码**同一 changeset 提交**（repo 配置 = 权威源）。
3. 三端（本地/测试/生产）配置同步是部署的一部分，写入发布 checklist。
4. 验证：重启后健康检查无新增键缺失告警。

## Pitfalls

- ⚠️ **Exaroton 写配置文件 `PUT files/data/{path}/` 必须发裸文本 body——严禁 `{"text": ...}` JSON 包装**（2026-08-10 实测翻车）：JSON 包装会被**原样存为文件内容**——YAML 配置尾残留 `text: "..."` 折叠块（整份配置的转义副本，插件解析静默回退默认值），server.properties 尾残留 `{"text"="..."}` 垃圾行。GET 可能返回裸文本**或** JSON 包装（两种都实测过）→ 统一先 `json.loads`/`yaml.safe_load` 尝试解包 text 键。读写封装用 orzmc `scripts/exa_file.py`（GET 自动解包、PUT 裸文本）。
- ⚠️ **JSON 残留块解包恢复原则（用户拍板 2026-08-10）**：残留块 `text` 值 = 配置文件原始完整内容，**以原始内容为准恢复**（`yaml.safe_load(整个文件)['text']` → 再解 `\n`→换行、`\=`→`=`、`\"`→`"` 双重转义 → PUT 回）。⚠️ 例外：若残留块是**旧快照**（含已废弃值，如 server.properties 残留 force-gamemode=true 而真实段是 false）→ 只删残留行、保留当前真实段。判断标准：残留块解包 vs 真实段 vs 本地权威版三方 diff，残留块是超集且无废弃值才覆盖。
- ⚠️ **禁止 import 带顶层执行代码的脚本**（2026-08-10 事故）：`import exa_apply_config` 验证导入时**真实改写了 Exaroton 线上配置**（脚本顶层直接跑 apply()）。写操作脚本必须 `if __name__ == '__main__':` 保护；验证导入用 `ast.parse` 而非 `import`。
- ⚠️ 全量覆盖前必须 diff——远端可能有运营自定义文案/参数，盲覆盖 = 丢配置。
- ⚠️ 线上有玩家/流量时写配置要遵守运维规则（先查在线人数，等窗口或授权）。
- ⚠️ 上传文件用绝对路径（`curl --data-binary @~/path` 波浪号不展开 → 报错）。
- ⚠️ 数据库型配置（如 LuckPerms H2）运行中下载会 500/锁——用应用自带 export
  命令生成 JSON 再下载解析（查 LP 现状最可靠的方式）。
- ⚠️ 控制台/RCON 通道执行插件命令可能输出不完整（分页器对非玩家 sender 异常）——
  验证用 bot 玩家身份或 export 数据对比，别依赖命令回显。
- ⚠️ **命令/端点名以源码或实测为准，别信文档二手记载**（2026-08-11 教训）：OrzMC 配置热重载文档旧写 `/orzconfig reload`，实测返回 `Unknown or incomplete command`——反编译 jar（`javap -c` 看 `literal()` 字符串）或查插件源码 `FeatureModule.java` 的 `commands.register(node, "配置管理", List.of("cfg"))`，确认根命令是 **`/config reload`**（别名 `cfg`）。**排查路径**：本地测试服 RCON 逐个试候选命令名 → 确认正确命令 → 再到线上执行。**验证生效**：不能只看命令发送成功（HTTP 200 只代表已投递），要查服务器日志（成功有 `[OrzMC] 配置已重新加载` / `所有配置文件已重新加载`，失败有 `Unknown or incomplete command`）。
- ⚠️ 拉取三端配置的 API 坑（2026-08-10/11 实测）：MCSM `/api/files/list` **必须传 `file_name`（可空串）否则返回 total=0**，page_size ≤50（200 触发 500）；**并发下载触发面板全局限流（500）已根治（2026-08-11）：`mcsm_env.py` 的 `mcsm_api_post`/`mcsm_download` 两步都感知 status!=200 并指数退避重试，`fetch3_configs.py` 的 MCSM 拉取改**串行 + 失败自动重试（3s×3）**——一次 77/77 全成功，不再需要 mcsm_refetch 手动补拉**；Exaroton `files/info` 判断目录用 `isDirectory` 字段（不是 `type`）。
- ⚠️ **MCSM URL 拼接坑（2026-08-11 实测）**：`cfg["url"]` 已含尾斜杠（`http://面板:23333/`），拼 API 路径时**不能加前导 `/`**——`cfg["url"] + "/api/files/"` → 双斜杠 → 404；正确是 `cfg["url"] + "api/files/..."`（mcsm_env.py / mcsm_apply_config.py 均用无前导斜杠写法，照抄）。
- ⚠️ **空文件（0B）也是有效文件，必须拉取成功**（2026-08-10 修复）：下载结果判失败用 `data is None`（网络失败）或 `data[:2] == b"PK"`（返回 jar 魔数=路径配错），**禁用 `if not data` / `if data and ...`**——`b""` 是 falsy，会把 0B 文件误判为失败（MCSM EzShops/stock-prices.yml 曾因此被标"下载失败"，实际是 0B 空文件）。

## 三端配置全量对比工具链

orzmc `scripts/cmp3/` 提供完整工具链（2026-08-10 新增/修复）：
- `fetch3_configs.py`：以本地插件清单为基准，从 Exaroton + MCSM 拉全量配置到 /tmp
- `cmp3_configs.py`：语义对比（**已修复：server.properties 用 `=` 解析，此前按 YAML `:` 解析全部跳过导致假一致**）
- `cmp3_diff_detail.py`：逐 key 三方值明细（输出巨大，落盘再看）
- `cmp3_report.py`：**完整审计报告生成器**——逐文件分组输出（插件目录分组），判定口径=交集语义（三端共同 key 值全同=一致；单端独有 key 另计），并把玩家数据类文件（homes/transactions/死亡点/审批记录等）单列为"运行时数据"不计入配置漂移
- `mcsm_refetch.py`：MCSM 失败文件串行补拉（并发已根治后基本用不到，保留兜底）
- `exa_recover_residue.py`：JSON 残留恢复（`[--dry-run]` 预览差异）
- 差异基线/决策记录 → orzmc `references/three-end-config-drift.md`；二次审计完整报告 → orzmc `references/config-drift-report-20260810.md`（77 文件：59 完全一致 / 10 配置差异 / 8 运行时数据）
