# 群消息样式规范（2026-08-19 统一，PR #197）

> **统一原则**：所有群通知 = 表情标题 + 33 连字符分割线 + 内容（版块式）。全仓「真分割线」（独立成行的连字符）必须恰好 33；`------xxx------` 夹文字装饰是标题样式，**保留不动**。

## 消息格式一览（模板键 → 样式）

| 场景 | 模板键 | 样式 |
|:--|:--|:--|
| 白名单拦截 | `whitelist_block` | `🙅🏻‍♂️ {玩家} 尝试加入服务器，被白名单拦截`（表情在模板层，文案可配） |
| 上线/下线/被踢 单发 | `player_join` / `player_quit` / `player_kick` | `🎮 当前玩家({online_count}/{max_count})⏎分割线⏎🥰 上线：⏎{name}`（下线 😋 / 被踢 😂） |
| 上下线聚合摘要 | `player_digest` | `🎮 当前玩家({online_count}/{max_count})` + 各版块（Java 动态注入分割线） |
| 申请发起 | `review_submitted` | `🙋🏻‍♂️ [申请发起] {玩家}⏎分割线⏎{summary}` |
| 申请撤回 | `review_cancelled` | `↩️ [申请撤回] {玩家}⏎分割线⏎{summary}` |
| 申请拒绝 | `review_rejected` | `❌ [申请拒绝] {玩家}⏎分割线⏎{summary}⏎分割线⏎审核人：{审核人}` |
| 申请通过 | `review_approved` | `✅ [申请通过] {玩家}⏎分割线⏎{summary}⏎分割线⏎审核人：{审核人}` |
| 异常 | `exception_alert` | `⚠️ 服务器异常⏎分割线⏎{message}`（`{message}` 多行=多项异常同列） |
| 白名单关闭 | `whitelist_toggle_alert` | 同上（`⚠️ 服务器异常⏎分割线⏎白名单关闭`） |
| 服务器启动/停止 | `server_load` / `server_stop` | `Minecraft {版本} {离线服}⏎分割线⏎启动完成⏎…`（分割线在 Java 侧：`ServerFeedbackService` / `ServerLifecycleService`） |
| 群帮助 `$h` | Java 常量 | `BotCommandFeedbackService.DIVIDER`（33 连字符） |

## 聚合摘要规则（PlayerEventAggregator.buildSection）

- 窗口内单事件 → 单发原模板（延迟一窗口）；多事件 → `player_digest` 版块式
- **空版块连同其上分割线整体省略**（无被踢事件就不出现 `😂 被踢` 段）
- 版块内 **1 人不显示人数**，多人显示 `(N)`（如 `😋 下线(3)：`）
- 超 `max_list_items` 用「+等N人」截断（计数不受影响）
- 渲染变量：`online_count` / `max_count` / `join_summary` / `quit_summary` / `kick_summary`
- 版块分割线常量 `PlayerEventAggregator.SECTION_DIVIDER`（33）

## 改模板的联动清单（4+1 处，漏一处测试挂/样式漂移）

1. `src/main/resources/templates.yml` — 默认模板（含 `i18n.command` 段）
2. `infra/config/configs/Templates.java` — Java 兜底默认值
3. `infra/notify/ReviewNotifierAdapter.java` — 审核消息 fallback（模板加载失败时用）
4. `infra/templates/TemplatePlaceholderValidator.allowedVarsByTemplateKey()` — 占位符白名单（漏注册 → ConfigHealthCheck 挂，报「模板变量未知」）
5. 测试：`TemplateResourceSmokeTest`（分割线整行恰好 33 断言 + 模板存在性）、`PlayerEventAggregatorTest`、`PlayerNotifyIntegrationTest`（对账正则 `🥰 上线(?:\((\d+)\))?：`）

⚠️ **分割线断言技巧**：`contains("33连字符\n")` 有子串漏洞（41 连字符行含 33 前缀 + 后续连字符），必须**整行匹配**（split("\n") 后 `line.matches("-+")` 且 `line.length()==33`）或 `startsWith("33连字符\n")`（锚定串首才精确）。

## 升级注意（存量服）

**修改既有模板键的值**（如本次）→ 存量服 `templates.yml` 不随 jar 升级自动更新，须手动同步新 `templates.yml` + `/config reload`，否则旧样式。**新增模板键** → 同理同步（见 plugin-mgmt.md 三件套）。

## 真实环境验证方法（2026-08-19 实测）

```bash
# 1. 打包 + 部署（带版本号 jar 不走 update/：停服 → cp 覆盖 plugins/ 同名 jar → 启动）
cd ~/OrzMC/plugin && ./gradlew shadowJar && cp build/libs/OrzMC-*.jar /Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/8A932DD47F4D42AAAD6A6A9A5FAD2A91/plugins/
# 重启 = 面板重启 folia-test 实例（2026-09-03 起无 start.sh；实例目录宿主可见可直接 cp）
# 2. 触发事件（bot 脚本，见 mineflayer-bot.md）
cd ~/minecraft-bot
node exec-cmds.js StyleUp "list"          # 上下线（先 RCON whitelist add StyleUp）
node exec-cmds.js StyleNotWhite "list"    # 白名单拦截（未加白名单直接连）
RCON_PASSWORD=xxx python3 ~/.hermes/skills/gaming/orzmc/scripts/rcon.py "whitelist off" 25575  # 白名单关闭异常（测完 whitelist on 恢复）
node exec-cmds.js TestNewbie "/apply builder 测试"   # 申请发起（需先 lp user X parent set member）
node exec-cmds.js StyleAdm "/review approve TestNewbie"  # 申请通过（StyleAdm 需 op）
# 3. 查投递：摘要版 easybot_deliveries.py；完整版 API /api/v1/messages?limit=N 的 messages[].text
#    （admin 密码 ~/Services/easybot-deploy-kit-*/easybot-deploy-kit/.env；role=Assistant 是出站）
#    ⚠️ 群里看到的消息 = 飞书+QQ 双平台投递记录，比插件日志可靠
```

## Folia 测试服操作坑（2026-08-19 实测）

- ⚠️ **screen stuff 喂 stop 不可靠**（`> stop` 显示但服务器不退）→ 用 RCON `stop`（rcon.py）
- ⚠️ **重复 `screen -dmS folia ./start.sh` 会叠加多实例**：同端口第二个实例 bind 失败但仍占 screen/资源——启动前先 `ps aux | grep folia-26` 确认无残留 + `screen -wipe`
- ⚠️ **cp 覆盖运行中 jar 不生效**（旧类已加载），且重新打包后必须核对 sha256（Gradle 增量可能跳过 shadowJar → 用 `--rerun-tasks` 强制）
- 测试服 = MCSM 实例 `folia-test`（uuid 8A932DD4，Folia 26.2，端口 25565/25575），配置在实例目录 `plugins/OrzMC/`（宿主 `/Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/8A932DD47F4D42AAAD6A6A9A5FAD2A91/`）
- 干净启动流程（2026-09-03 迁 MCSM 后；2026-09-11 起两实例地图已独立、可同时跑）：面板停止实例 →（若上次异常崩溃）清**该实例自己** `world/session.lock` 残留 → 面板启动 folia-test → 等端口监听 + 日志 `Done (.*)! For help`
