# 审核框架与 PR 审查清单

> 2026-11-10 由 3 篇合并（内容未改写）。审核框架（权限系统二期落地）、本地验收记录、插件 PR 代码审查清单。
>
> 用法：新功能「开工前」对齐框架 → 合 PR 前逐条过清单 → 验收按第 2 节记录方式留证。

## 1. OrzMC 通用审核框架（权限系统二期，2026-08-07 落地）
> 来源：原 `references/review-framework.md`（2026-11-10 并入本文件，内容未改写）

> 背景：Rank 一期（时长读 stats + default→member 自动晋升 + member→builder 申请）的审核逻辑
> 写死在 rank 模块（`pending_application` 字段），无法复用于白名单/领地等其它审核项。
> 二期抽象出**通用审核框架** `features/review/`，rank 模块退化为消费者。
> **用户明确要求：框架按「未来可单独沉淀为通用审核插件」设计**——拆插件 = 搬 `features/review/` 包
> + `permission.yml` 的 reviews 节 + 补 4 个端口适配器，核心代码零改动。
> 完整方案文档：`~/OrzMC/plugin/docs/permission-system-v2.md`

## 设计要点（用户拍板的架构约束）

| 约束 | 落地 |
|:--|:--|
| 审核请求**携带结构化内容** | `ReviewRequest.data`（Map<String,String>），「审核什么」明确表达，框架不感知业务 |
| 审核类型**注册表驱动** | `ReviewType`（record：id/displayName/commandKey/argsParser/eligibility/summary/handler），消费者模块构建后 `reviewService.register(type)` |
| **handler 由消费者注入**，框架零 LP 依赖 | BUILDER_PROMOTION 的 handler = `rankPromoter::promoteToBuilder`，在 FeatureModule 装配时注入，不在 review 包写死 |
| **端口解耦**（可拆插件） | review 包只依赖 4 个端口接口：`ReviewStore`（持久化）/ `ReviewNotifier`（通知）/ `PlayerLookup`（玩家名↔UUID），实现留在宿主侧 |
| **单一配置文件** | `permission.yml` 三段式（config 阈值 / ranks 晋升状态 / reviews 审核记录），`PermissionStore` 一个类实现 RankStore + ReviewStore 两个接口，替代原 ranks.yml |
| 群指令 + 游戏内命令全通用化 | `$v`（l/y/n）+ `/apply <type> [理由]` + `/apply status|cancel` + `/review approve|reject` + `/rank` 增强 |

## 核心类（features/review/，零宿主依赖）

- `ReviewRequest` — record(id, typeId, applicantId, data, status, createdAt, reviewedAt, reviewerName)；Status 枚举 PENDING/APPROVED/REJECTED/CANCELLED；`reviewed()` 生成审核后新记录
- `ReviewType` — record(id, displayName, commandKey, argsParser, eligibility, summary, handler)；`parseArgs(rawArgs)` / `isEligible(uuid)` / `summarize(data)`
- `ReviewService` — 核心编排：`submit`（资格预检→防重复→PENDING→双端通知）/ `cancel`（仅本人 PENDING）/ `review`（通过时执行 handler）/ `reviewByApplicantName`（按玩家名定位，多条待审提示用类型区分）/ `cancelForApplicant`；通知逻辑收在 service 层，任何入口触发都自动通知
- `ReviewHandler` — `@FunctionalInterface CompletableFuture<Boolean> approve(UUID applicantId)`；**异步授权**（2026-08-19 PR #196 改造，见下节）
- 端口接口：`ReviewStore`（save/findById/listPending/listByApplicant/pendingFor/hasPending）、`ReviewNotifier`（gameMessage/groupEvent）、`PlayerLookup`（resolve/name）

宿主侧端口实现：
- `infra/notify/ReviewNotifierAdapter` — 适配 TypedConfigProvider + Notifier
- `infra/player/BukkitPlayerLookup` — 适配 `Bukkit.getOfflinePlayer()`（离线服审核时申请者可能已下线）

## ⚠️ 通知模板必须用 renderTemplate，不能用 renderEvent

`TypedConfigProvider.renderEvent(key, vars)` 走 `TemplateService.templateForEvent()`——**硬编码白名单**（player_join/whitelist_block/...），
**未列入白名单的键渲染成空字符串**（不报错！）。新增事件通知模板必须用
`renderTemplate(key, vars, fallback)`（`TemplateRenderer.resolveTemplate` 直接按配置键读取，带 fallback 兜底）。

```java
// ✅ 正确（ReviewNotifierAdapter.groupEvent）
MessageEnvelope env = configs.renderTemplate(templateKey, vars, fallback); // fallback 含 {player}/{summary}/{reviewer} 占位
notifier.event(templateKey, env);
// ❌ 错误：renderEvent("review_submitted", vars) → 渲染为空，群消息静默丢失
```

## ⚠️⚠️ renderTemplate 第二层坑：模板占位符必须 ⊂ vars 键集（PR review 抓到的 C1 Critical）

用对 `renderTemplate` 也不够——**默认模板占位符与调用方 vars 键集不匹配时，字面 `{message}` 直接透传**：

- `ReviewService.groupEvent` 传 vars `{player, type, summary, reviewer}`（**无 message 键**）
- 仓库默认模板 `review_submitted: "{message}"`（模板文件里只有 `{message}` 占位）
- `TemplateRenderer.render()` 只替换 vars 里**存在的键**，不存在的占位符原样保留 → 群通知推送字面 `{message}`
- **fallback 不救场**：`resolveTemplate` 优先命中模板文件（有 `{message}` 就用它），fallback 只在模板缺失/为空时生效
- **为什么 E2E 没抓到**：测试服 templates.yml 被手工改过（中文文案）→ 全绿；新部署用仓库默认模板 → 必现。**测试环境配置漂移掩盖生产 bug**

**修复模式**：默认模板必须用与 vars 一致的占位符（`📋 [新申请] {player}：{summary}（$v l 查看）`），或调用方补 `message` 键。
**review 检查点**：凡 `renderTemplate(key, vars, fallback)`，核对 vars 键集 ⊇ 模板占位符键集（可用 python 模拟 render 快速验证）。
**✅ 防回归测试已落地（2026-08-07）**：`TemplateResourceSmokeTest.testReviewGroupEventsRenderRealText_notLiteralMessage` ——
用真实 vars 渲染 `review_submitted/approved/rejected` 断言「含玩家名」且「不含字面 `{message}`」。
新增模板键时在此测试补断言（同时记得 4 处注册，见下节）。

## ⚠️⚠️⚠️ 授权处理已异步化（2026-08-19 PR #196，Folia 死锁修复核心）

> 背景：`/review approve` 在 Folia 上曾死锁 132s+（region 线程同步等 LP 异步 future → 自锁）。三阶段演进后定为**异步授权**模式，改 review 相关代码必读 `docs/dev/folia-luckperms-gotchas.md` 与 `folia-experiment.md` 线程红线节。

- **ReviewHandler 签名**：`CompletableFuture<Boolean> approve(UUID applicantId)`——LP 操作（loadUser/saveUser 的 `.get()`）必须在**自己管理的异步线程**执行（`Bukkit.getAsyncScheduler().runNow`），**任何服务器调度线程（global/region）不得同步等待 LP future**（回调排自己后面必自锁）。
- **状态一致性**：`ReviewService` 异步等待 handler 结果后**才落 APPROVED**（授权成功才通过，失败保持 PENDING）；落状态前重读校验仍 PENDING（防并发覆盖）。授权结果与申请状态**原子一致，无漂移**。
- **in-flight 去重（防并发越级）**：异步授权后双管理员同时 approve 会并发操作同一 LP User → 跳过中间档越级（member→admin）。`ReviewService` 用 `ConcurrentHashMap.newKeySet()` 按 requestId 占位，处理中重复 approve/reject/cancel 一律返回「正在处理中」，`whenComplete` 释放。
- **写盘加锁**：approve 在 global 线程落状态、submit/cancel/reject 在 region 线程写——`PermissionStore.save` 用锁包住 write+saveConfig 临界区（防丢更新/YAML 损坏）。
- 游戏内反馈：「已通过 X 的申请」= 授权成功；「申请保持待审」= 授权失败（链顶/LP 异常）。

## PR 代码 review 检查点（Paper 插件通用，2026-08-07 权限二期 review 实战）

1. **模板/消息渲染**：renderTemplate vars 键 ⊇ 占位符键（上条）；模板键 4 处注册齐全；`command_review_list` 类传 `message` 键所以没事，`review_*` 四键没传所以坏——逐个核对
2. **handler 副作用顺序**（2026-08-19 起已异步化，见上节）：`store.save(APPROVED)` 必须在 handler **授权成功之后**（异步等结果），失败保持 PENDING——「已通过但无权限」或「已晋升但状态 PENDING（漂移，重复 approve 会越级）」都是不允许的；旧实现「先落状态再执行 handler」的坑已被异步化根除
3. **ID 生成**：`System.currentTimeMillis() + UUID.randomUUID().hashCode()` —— hashCode 可能为负、同毫秒碰撞概率存在；用完整 UUID 更稳（S1）
4. **语义字段**：`cancel()` 把申请人 UUID 当 reviewer 存（CANCELLED 记录的 reviewer 应是名字或 null，W5）
5. **迁移性能**：循环内每次 `save()` 全量落盘 → 批量迁移攒批一次保存（W3）
6. **旧文件清理**：迁移后 ranks.yml 残留，成功迁移后改名 `.bak`（W4）
7. **异步 dispatch 主线程**（已有）：`$v`/orzdebug 链路 handler 内 dispatchCommand 必须回主线程

## 新增模板键 = 4 处注册（漏一处必踩坑）

1. `TemplateKeys.java`：常量 + 加入 `ALL` 数组（ConfigHealthCheck 校验用）
2. `src/main/resources/templates.yml`：`format:` 段（PLAIN/CODE_BLOCK）+ 消息正文段
3. `src/test/resources/templates-test.yml`：测试资源同样要加
4. `ConfigHealthCheckTest.java`：`requiredCmds` 数组——**文件里有两处相同的数组**（fullValid 与 minimal），
   用 patch 时 `replace_all=true`，只改一处另一处会漏（2026-08-07 实测 test 失败即因此）

## 装配与接线（FeatureModule）

- `PermissionStore(platform.configService())` 注册在 `ConfigService.setup()`：`registerConfig("permission","permission.yml")` + `markAlwaysSave("permission")`
- `migrateLegacyRanks()`：启动时把旧 `ranks.yml` 的 `promoted` 标记和 `pending_application=true` 幂等迁入 permission.yml（已迁移跳过）
- **构造顺序坑**：rankService 必须先于 register() 创建（BUILDER_PROMOTION 的 eligibility lambda 引用 `rankService` 字段，
  final 字段在赋值前被 lambda 捕获 → 编译错误「可能尚未初始化变量rankService」）
- **BotCommandService 注入时机**：BotCommandService 在 BotModule（Phase A）创建，早于 FeatureModule 的 review/rank 服务——
  新群指令 handler 依赖的服务用 **setter 注入**（`setReviewService`/`setRankService`），在 `FeatureModule.setupEventListeners()`
  开头补调用（与 maintenance/blacklist 同一模式）

## 群指令 $v（扩展自 OrzUserCmd 枚举）

- `OrzUserCmd.REVIEW("v", "查看/处理审核申请", true)` → `BotCommandService` handlers map + `handleReview`
- `$v l`（待审列表，带申请人当前组，Paginator 分页）/ `$v y <玩家>`（通过）/ `$v n <玩家>`（拒绝）
- 支持 `$v y <typeId> <玩家>` 精确按类型定位
- 审核人身份记为「群管理员」（群内 isAdmin ≠ 游戏 LP 组，见 orzmc-bot-command-testing.md）

## 游戏内命令（FeatureModule registerRank，Brigadier）

- `/apply`（列可申请类型）/ `/apply <type> [理由]` / `/apply status` / `/apply cancel <type>`
- `/review approve|reject <name>`（替代一期 `/rank approve|reject`）
- `/rank`（当前组+时长/进度+下一步可申请——「下一步」由 ReviewType 注册表反向生成，资格预检通过的项）
- 玩家侧三件套：`/rank`（我是谁）· `/apply status`（我申请了什么）· `/apply cancel`（我能撤回）

## 通知矩阵（4 环节全覆盖，模板键 + 默认文案）

| 环节 | 触发方 | 模板键 |
|:--|:--|:--|
| 提交 | 玩家 /apply | `review_submitted` = 📋 [新申请] {player}：{summary}（$v l 查看） |
| 撤回 | 玩家 /apply cancel | `review_cancelled` = ↩️ {player} 撤回了申请：{summary} |
| 通过 | 管理员 | `review_approved` = ✅ {player} 的申请已通过（审核人：{reviewer}）：{summary} |
| 拒绝 | 管理员 | `review_rejected` = ❌ {player} 的申请被拒（审核人：{reviewer}）：{summary} |

玩家结果三层兜底：游戏内消息（在线即发）→ 群通知（离线可见）→ `/apply status` 随时自查。

## 测试

- `ReviewServiceTest`（纯 JUnit + Mockito）：提交/预检/防重复/撤回归属/审核 handler 副作用（int[] calls 计数）/多待审按类型提示
- `PermissionStoreTest`：stats 解析 + 三段读写 round-trip
- 注意：`reviewByApplicantName` 测试里 `store.findById` 也要 mock（`listPending` 之外 service 内部还会查 findById）

## 2. OrzMC 审核框架本地验收（2026-08-07，已全部闭环）
> 来源：原 `references/review-framework.md`（2026-11-10 并入本文件，内容未改写）

> 背景：权限系统二期（通用审核框架 + `$v` 群指令 + permission.yml 三段式）本地 E2E 验收。
> 验收环境：本地主服 25565（Paper 26.2，OrzMC jar 已部署最新 HEAD），mineflayer bot 进服测玩家侧，
> orzdebug 模拟群指令测管理员侧。

## 已验证通过（游戏内路径，可靠）

1. **持久化**：重启后 permission.yml 的 reviews/ranks 记录保留（markAlwaysSave）
2. **`/apply builder <理由>` 提交**：资格预检 → 防重复 → PENDING 落盘（permission.yml reviews 节可查）
3. **重复申请被拒**：`你已提交过「晋升建造者」申请，请等待管理员审核。`
4. **资格预检**：非 member（本地无 promoted 标记）→ `你不满足「晋升建造者」的申请条件。`
5. **游戏内 `/review approve <玩家>`**（主线程）：记录变 APPROVED + reviewed-at 落盘 ✅，LP 组确认 builder
   （LP info 输出 `> builder` 需连后续行抓——Adventure 组件把标题与内容分行，见 SKILL.md「LP 状态验证三手段」）

## ⚠️ 资格判定看「本地状态」不是 LP 组（验收踩坑，重要）

`RankService.currentGroup()` 判定：**有 APPROVED 的 builder-promotion 记录 = builder；有 promoted 标记 = member；否则 default**。
- **LP 组 ≠ 本地资格**：TestMember 在 LP 是 builder+member，但本地无 promoted 标记 → currentGroup=default → 被预检拒绝
- TestNewbie 已有 APPROVED 记录 → currentGroup=builder → 不能再申请 builder（合理）
- **要测「申请通过路径」需要「干净 member」**：promoted 标记 + 无 APPROVED 记录。验收时手工给 TestMember
  补了 promoted 标记（permission.yml 停服改文件）才通过预检

## ✅ 已闭环问题：群指令 `$v y <玩家>` 受理后状态不落盘（根因：Paper 26 Brigadier 不触发 ServerCommandEvent）

**现象**（干净状态复现）：`$v y TestMember` 经 orzdebug 受理后，LP 授权执行了但 permission.yml 记录保持 PENDING、文件 mtime 不变；同记录游戏内 `/review approve`（主线程）正常落盘。

**最终根因**（分层日志定位，见 SKILL.md #9 断链调试法）：**Paper 26 中 Brigadier 注册的命令（`literal(...)`）不触发 ServerCommandEvent**。
- `/orzdebug` 的 `.executes()` 正常执行（玩家收到"已受理"），但 OrzDebugEvent 监听器**永远收不到任何 ServerCommandEvent/RemoteServerCommandEvent**（旧方案"双事件注册+剥斜杠"已失效）
- 日志 `TestAdmin issued server command: /orzdebug ...` 是 Bukkit 通用命令日志，**不代表** ServerCommandEvent 触发
- **"LP 授权执行了"是上一轮游戏内 `/review approve` 测试的残留**——测试状态污染伪造"部分生效"假象（见 SKILL.md #11）

**修复**：在 Brigadier `.executes()` 里**直接调用** `botModule.botInboundHandler().handleMessage(cmd, true, callback)`（`runTaskAsynchronously` 包裹，输出打日志），不再依赖事件监听器。

**验证**（修复后实测通过）：`$v y TestMember` → 日志出现 `parse 匹配: cmd=v → handleReview 进入 → emit: command_review_result → cmd debug: 已通过` 完整链路 → permission.yml 变 `status: APPROVED + reviewer: 群管理员 + reviewed-at` → PENDING 归零。`$v l` 列表正常（`[晋升建造者] TestMember（当前组：member）：申请晋升 builder：理由（刚刚 提交）`）、`$v n` 拒绝正常（REJECTED + reviewer）、拒绝后可重新申请均验证通过。

## 第二轮补充验收（2026-08-07 晚，全部通过）

修复闭环后做了**完整验收**，覆盖群指令全链路 + 配置化：

1. `$v l` 待审列表：类型/玩家名/当前组/请求内容摘要/提交时间 全显示 ✅
2. `$v n <玩家>` 拒绝：REJECTED + reviewed-at + reviewer=群管理员 ✅；**拒绝后可重新申请**（REJECTED 不阻塞 hasPending）✅
3. `$v y <玩家>` 通过：LP `parent add builder` 执行 + APPROVED 落盘 + reviewer=群管理员 ✅
4. **阈值配置化验收**（模式详见 e2e-testing skill「配置类功能验收模式」）：permission.yml `member-threshold-hours` 10→1 → 重启 → HermesBot（106min > 60min，无 promoted 标记，LP=default）上线 → 日志 `[LP] LOG > promote rank` → LP 组 default→**member**（只升一级）→ permission.yml 写入 `promoted: true` ✅
5. **幂等**：HermesBot 再次上线**无** promote rank 日志（promoted 标记防重复晋升）✅
6. 验收后阈值恢复 10h（测试环境还原）

**测试账号状态（验收后）**：HermesBot 已 promoted（member）；TestMember 已 APPROVED（builder）+ promoted 标记保留（模拟真实晋升状态，无需还原）。

## 验收测试账号状态（改过，测完恢复注意）

- TestMember：permission.yml 手工加了 promoted 标记（验收用）→ 验收后应删除还原
- TestNewbie：LP=member+builder（多次测试叠加），有 APPROVED 记录
- HermesBot：stats 106 分钟（时长读取正常）
- 测试数据清理：markAlwaysSave 的 permission.yml **必须停服改文件**，运行中改会被关服保存覆盖（见 SKILL.md）

## 3. OrzMC 插件 PR 代码审查清单（2026-08-07 PR #160 review 沉淀）
> 来源：原 `references/review-framework.md`（2026-11-10 并入本文件，内容未改写）

审查本地 PR 分支时的检查流程 + 实际发现的高发问题。适用于任何 OrzMC 插件 PR 合并前。

## 一、文档脱节检查（PR #160 一次性发现 8 处——最高发问题）

**PR body/文档声称的功能与代码实际不符**是本项目常见病。逐项对照：

| 检查点 | 手法 | PR #160 实例 |
|:--|:--|:--|
| PR body 声称的功能 | grep 代码确认存在 | body 声称「旧 ranks.yml 自动迁移」但 `migrateLegacyRanks` 已随配置最小化重构删除 |
| 功能生命周期 | `git log --oneline -- <file>` + `git show <commit>:<file>` 对比历史实现 vs HEAD | 迁移逻辑 16dfa4c 有、b278fb3 删——确认「曾实现后删除」而非「从没实现」 |
| javadoc vs 实现 | 读接口/类 javadoc 对照代码 | RankPromoter javadoc 写「反射访问 LP API」，实际早已改无反射条件实例化 |
| 资源文件 vs 消费方 | `grep -rn "ranks.yml" src/main/java/` | ranks.yml 无任何 loadFile 引用 → 无消费方残留，删除 |
| 配置注释 vs 配置结构 | 读 permission.yml 注释对照代码读写节 | 注释写「三段式 ranks 晋升状态节」，实际 ranks 节已删（两段式） |
| build 注释 vs 实际配置 | 读 build.gradle.kts 注释 | 注释写「softdepend 保证加载顺序」，实际用 paper-plugin.yml `dependencies:` 新格式 |
| 常量表 vs 字符串字面量 | 搜新事件键是否进 TemplateKeys | rank_promoted/rank_demoted 只有字面量，TemplateKeys 缺 → ConfigHealthCheck 模板校验覆盖不到（与 {message} 事故同源） |
| docs/ 设计文档 vs 最终实现 | grep docs 中的「迁移/三段式/ranks」等关键词 | 3.6 数据迁移章节、检查表、开发清单全说过时描述 |
| **接口签名 vs 文档代码块** | 读接口源码对照 docs 里的签名片段 | ReviewHandler 文档写 `void onApproved`，实际 `boolean onApproved`（S1 修复后文档没跟）——单行签名最容易漏 |
| **常量/模板键计数** | 数 TemplateKeys 常量 + templates.yml 内容段/format 段 vs docs 写的键数 | docs 写「5 键」，实际 11 键（rank_promoted/demoted + command_review_* 漏数） |
| **监听器集合 vs 文档描述** | grep @EventHandler 对照文档「双监听/单监听」描述 | 8.4 写「双事件监听」，M3 已改单通道 RCON |
| **验收文档（acceptance）滞后** | 检查 commit hash、测试键数、行为描述（审核人显示等） | acceptance 写 commit 3358e5a（实际 e1c18c1）、「补 5 键」、「审核人=群管理员」（S2 后=发送者昵称透传） |

**教训**：设计文档（docs/）+ javadoc + 配置注释 + PR body 四处极易滞后于代码。大重构（如「配置最小化删 ranks 段」）后必须全链路同步。

## 二、PaperMC/Java 插件审查 check 项（PR #160 实际发现）

1. **void 回调吞掉失败 → 状态假成功**：副作用回调返回 void + 被调方法失败时返回 **null 而非抛异常** → 调用方无法感知。实例：`ReviewHandler.onApproved`（void）→ handler 是 `rankService::promote`（失败返回 null）→ 审核仍落 APPROVED 但玩家组没变。修法：回调返回 boolean，调用方检查。**测试也要覆盖「返回 null」而非只覆盖「抛异常」**（现有测试只有 handlerThrows 异常路径）。
2. **N+1 LP 查询**：`currentTrackGroup` 循环 `trk.getGroups()` 内每次调 `isInGroup` → 每次 `loadUser`（离线玩家最多 3s×4）。修法：loadUser 一次，遍历 `user.getInheritedGroups()` 匹配 track 组。$l 列表对每个玩家调 currentGroup → N 玩家 × 4 次查询。
3. **审核人身份硬编码**：群指令审核 `reviewerName = "群管理员"` 丢真实操作人 → 审计/追溯失效（`/apply status` 无法显示谁审核的）。isAdmin 参数传进来了但没用。
4. **主线程阻塞风险**：`PlayerJoinEvent`（主线程）→ `checkPromotion` → `loadUser().get(3s)` + `saveUser().get(3s)`。在线玩家缓存通常命中（LP 也在 join 加载），但需评估异步化兜底。
5. **双通道事件并存**：Brigadier `executes()` 直调 + `ServerCommandEvent`/`RemoteServerCommandEvent` 事件监听并存——当前 Paper 26 事件不触发无问题，但 Paper 行为变化时同命令处理两次 → 群消息重复。留一个通道，另一个注释说明。

## 三、Review 流程技巧

```bash
git diff main...<branch> --stat                    # 全貌（文件数/增删量）
git diff main...<branch> -- <file>                # 逐个文件
git log --oneline -- <file>                       # 文件生命周期（找「曾实现后删除」）
grep -c "@Test" src/test/java/.../*Test.java      # 快速评估测试量
gh pr checks <n>                                  # CI 状态
```

- **测试覆盖评估**：搜测试名覆盖的「失败路径形态」——异常 vs null 返回是两种不同路径，只测异常会漏 null 静默失败
- **权限校验**：每个命令入口查拦截器（guardAdminCommand / adminInterceptors / requires）
- **异步链路**：runSync + CompletableFuture.join 模式检查异常传播（Bukkit 调度器吞异常只打日志）
- **状态一致性**：副作用（LP 授权）与持久化（状态落盘）的顺序——「先 handler 后落状态」正确，但 handler 失败信号必须能传播

## 四、Folia 异步/并发审查检查点（2026-08-19 PR #196 实战新增）

1. **服务器调度线程等 LP future = 自锁**：全局搜 `loadUser|saveUser|\.get\(|\.join\(`，确认没有任何 global/region 线程同步等待 LP 异步 future（回调排自己后面必自锁/超时）。授权类操作必须 `CompletableFuture` 异步化（LP 在自己管理的异步线程执行）。
2. **状态漂移**：授权结果与业务状态必须原子一致——「LP 已晋升 + 状态 PENDING」= 漂移，重复操作会越级。检查异步回调落状态前是否重读校验。
3. **并发竞态（异步化新引入）**：异步授权后同一实体可被并发操作——in-flight 去重（CHM keySet 占位）或 PROCESSING 占位 CAS；授权在途时撤回/拒绝互斥。
4. **region 线程判定**：`Bukkit.isGlobalTickThread()` 不覆盖 region 线程（Folia 需 `isRegionOwnedByCurrentThread()`，paper-api 编译期无此方法须反射）；任何服务器调度线程上都不应做可能阻塞的离线读。
5. **写盘并发**：异步化把写挪到不同线程后，共享配置对象（FileConfiguration）读写必须加锁，防丢更新/YAML 损坏。
6. **join 超时**：所有 `done.join()` 必须有超时（调度器停摆时防永久挂起）。

## 五、backup-core/备份功能审查检查点（2026-08-20 PR #215 实战新增）

1. **依赖 API 语义先确认源码，勿凭命名猜测**：review 曾把 `IOOptions` 第三参 `syncOnFinalize` 误判为 zipOutput（结论需返工）——升级依赖的 PR，review 前先 `git show <tag>:core/.../OptimizerConfig.kt` 确认参数语义与默认值。
2. **overlap 校验**：0.3.x input/output 不得重叠（相同/祖先/后代全拒）——备份 output 必须放 input 外。**正解：input 用世界目录**（`getWorldFolder()`），output=`backup/tempDir`（backup/ 是世界目录兄弟路径）。勿用「output 放系统临时目录 + zip 移回」的绕路方案（多一步移动就多一个静默丢备份点）。
3. **世界目录选择**：`getWorlds().get(0)` 顺序不保证主世界在前——优先选择含 `dimensions/` 或 `region/` 的真实世界目录（26.2 结构各维度均在 world/ 内）。
4. **备份成功判定**：zip **计数**有误判（同名覆盖 count 不变→假失败；空 zip 计成功→prune 删旧留空）——用「最新 zip mtime 变化」判定（`before` 记录最新 mtime，`after` 无更新 mtime 的 zip 才报失败）。
5. **空世界语义**：zipOutput 模式 0 chunk 也产出 22B 最小 zip（**成功**，非失败）——失败判定只能靠「无新 zip」。
6. **启动清理**：崩溃/断电残留的 `backup/tempDir` 启动清理——**必须异步**（大残留同步删除阻塞启动），onEnable 调度安全。
7. **备份完成验证**：zip 边写边落盘（进行中 64M → 完成 1.1G），验证完成看日志「地图备份 完成」+ tempDir 消失，勿用「zip 出现」。
