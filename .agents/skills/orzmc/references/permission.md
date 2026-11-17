# LuckPerms 权限体系（permission）

> 合并自：minecraft-permission-audit + luckperms-api-integration + luckperms-plugin-integration（2026-08-10 阶段二整合）
> 触发：梳理/审计/验收权限组配置；插件集成 LP API（升降级/组查询/AMBIGUOUS_CALL）；「default 却能用 X」类排查。

## LP API 核心事实（血泪教训）

1. **LP API 无 TrackNode 类型**——track 组就是普通继承节点（InheritanceNode），代码无法区分「track 给的组」和「手动 parent add 的组」——同名叠加组必然干扰判定，只能数据清理 + 运维规范（权限组只经 $p u/d 管理，禁止 parent add 叠加）
2. **上下文陷阱（最重要）**：`track.promote/demote(user, ctx)` 必须传 **global 上下文**（`ImmutableContextSet.empty()`）——实时上下文会把节点带完整上下文快照落库 → 节点重叠 → `AMBIGUOUS_CALL` + 组判定错乱
3. **组查询也要 global**：`QueryOptions.builder(QueryMode.CONTEXTUAL).context(empty).build()`
4. **promote/demote 只改内存**：必须 `saveUser` 显式落库（落库失败视为操作失败）
5. **主线程派发**：异步线程调 LP API 抛 `IllegalStateException: Asynchronous Command Dispatched Async`——runSync 回主线程
6. **离线玩家**：loadUser 有超时（建议 3s）；一次加载继承组集合避免 N+1

## AMBIGUOUS_CALL 调试清单

1. `lp user <name> parent info` 看 parents（群 $e 通道输出进 latest.log；**RCON 通道执行生效但无回显**）
2. 带完整上下文快照的组 = 历史代码用实时上下文操作的产物——**根治清理**：`lp user X parent clear`（清全部节点）→ `parent set <组>`（重设 global 单节点）——比 `--context` 精确移除可靠（bot 群 $e 通道引号被拆）
3. **复发与「LP 操作都是加法」**：反复 $p d/u 会累积组节点（降级只加低组不清高组）；代码级根治 = promote/demote 操作前先清全部继承节点（`data().clear(InheritanceNode)`）→ add 当前 track 组 → saveUser（normalizeSingleGroup 模式）
4. `permission set` 同样是加法：最小化配置后重跑 set 清单**不会移除**被删出清单的旧节点——对齐必须 `lp group <G> permission clear` + 重设
5. **「为什么玩家能用 X」用 check 溯源**：`lp user X permission check Y` 输出「在環境 global 中，<组> 的權限 Y 被設為 true」

## 插件默认权限（default: true——未声明也生效）

- 插件 plugin.yml 声明 `default: true` 的权限，LP 未设节点也**实际可用**（GetMeHome 家命令全开、GP createclaims/siege 等 9 项、EzShops playershop 默认开）
- **LP check undefined ≠ 不可用**（组无节点但插件默认 true）；check true ≠ 可用（命令未注册/子权限缺失）——**命令可用性唯一权威 = bot 实测命令**
- 盘点：python zipfile+yaml 遍历插件 plugin.yml 过滤 default:True（脚本 `scripts/scan_default_perms.py`）
- 禁用：插件默认**不吃父权限 false**——必须逐项显式 `set <node> false`
- 「一切以实际可用为准」：配置文档标注实际不可用项（spawn///unstuck 标「当前不可用（命令未注册）」）

## 权限名真实性核对（防「假权限」）

- plugin.yml 的 permissions 段（`unzip -p plugins/<Jar>.jar plugin.yml | grep -E "^  <前缀>\."`）
- 代码注册的 → jar 字节码字符串（unzip 后 `grep -rao "essentials\.<名>[a-z.]*"`）
- 已踩坑：`essentials.balancetop` ✅ / `essentials.baltop` ❌；`essentials.reply/craft/teleport` ❌；`ls.bypass` 代码注册 ✅

## 权限审计流程

1. **权限名核对**（上节）→ 2. **子权限模式**（/time set 需 time.set、/mail send 需 mail.send、/warp 列表需 warp.list、/gamemode 他人需 .others）→ 3. **通配符/父权限最小化**（父权限 1 替代多；通配避开管理分支：不给 `worldedit.*`（含 reload）、`worldguard.region.*`（含 bypass）、`essentials.*`、`minecraft.command.*`（含 op）；增量原则子组只配增量）→ 4. **LP 命令通道**（bot $e 通道 orzdebug 执行 + 查 latest.log；RCON 只适合批量 set 不适合查询）→ 5. **bot 实测验收**（每权限组一账号；区分 Unknown=未注册/「没有 X 权限」=缺配置/静默=放行；管理命令用不存在玩家目标测放行安全无副作用）→ 6. **越权检查**（admin check `minecraft.command.op` → false）+ 继承检查

## 三端 LP 权限同步（生成器蓝本）

- 同步清单：`scripts/gen_perm_commands.py` 从**仓库 `docs/permission-groups.md`（唯一权威）**解析 L0-L3 表格生成（`lp group <g> permission set <节点> true|false` + parent 链 + 高危注释）；改权限 = 改文档 → 重新生成，勿手改产物
- ⚠️ 执行前**必须过滤注释行**（`grep -v '^#'`——文档语法示例行会被误匹配执行 → LP 报用法错误）
- 命令 API 发送成功 ≠ LP 执行成功——查日志三个确认模式：`Set <节点> to true for <组>` / `already has <节点> set` / `parent groups cleared, and now only inherits <父组>`；缺任一 = 未执行需补发
- MCSM 命令端点必须 **GET** + `?command=` URL 编码 + 冷却重试（500 sleep 3-4s）；Exaroton 无玩家自动停——先 `POST /extend-time/`（`{"time":600}`）延长窗口
- 脚本：`scripts/exa_lp_sync.sh`（extend-time + parent 链 + 全量 set）；`scripts/rcon_batch.js`（RCON 批量，**有漏执行风险事后必须 LP check 验证**）

## 装即用：LuckPermsBootstrap 自动初始化（幂等 + 校正）

- 启动时自动补齐 track + 组（无 LP 由 NoopRankPromoter 降级）：`createAndLoadTrack/Group` 返回 CompletableFuture；先建组再建 track（`ensureGroups().thenRun(this::ensureTrack)` 链式）
- **幂等但校正**：组缺失→创建挂继承链；**组已存在→校验继承节点与设计不符则清继承重挂 parent**（只动继承不碰权限节点）；track 已存在链序不一致→deleteTrack+重建
- 校正 API 细节：读继承用 `group.data().toCollection()` 过滤 InheritanceNode（**`Group.getParentGroups()` 不存在**）；`Track.getGroups()` 返回 `List<String>`（组名）
- 新建组挂继承链：member→default、builder→member、admin→builder（不内置权限节点）

## 权限组配置（去 op 化）

- 四组增量配置（admin→builder→member→default，只配增量）；**高危节点任何组都不授**：`*`、`luckperms.*`、`minecraft.command.op`、`bukkit.command.op`、`essentials.stop/reload`
- 双实现注意：用 GetMeHome 当家插件时 Essentials home 权限不给——家功能用 **`getmehome.user` 父权限**（2026-08-08 起合并，替代 5 个 `command.*` 分列）
- 完整节点清单（唯一权威）：仓库 `docs/permission-groups.md`（执行清单由 `scripts/gen_perm_commands.py` 生成）；插件默认权限 → `references/permission-impl.md`

## LP 命令语法速记

- 正确结构：`lp track <track> <action>`（`lp track rank info`；`lp track info rank` 报「未知的指令」）
- LP 5.5 无 track delete 命令（子指令仅 info/editor/append/insert/remove/clear/rename/clone）
- `lp user X parent remove <组>` 只删无上下文节点；带上下文快照的节点删不掉——`parent clear+set` 一步到位

## 实战坑（2026-08-12 三端对齐）

- **LP export 文件名按分钟粒度**（`luckperms-YYYY-MM-DD-HH-mm.json.gz`）：同分钟多次 export **覆盖同名文件**——本地验证导出时先 `date` 确认分钟，或等下一分钟再导出，避免误读旧文件
- **MCSM/Exaroton 插件目录可能有历史导出**（`verify-*`、`post-*`、`pre-*` 等手工导出）：列目录找最新**必须过滤 `luckperms-` 前缀**再按文件名倒序（字母序 v/p 会排在 luckperms 前面）
- **EssentialsX `/gamemode` 命令认父权限 `essentials.gamemode`**（08-12 实测：只给子权限 .creative/.survival 命令仍报「没有权限」）——父权限含 .others，**必须同组显式 `essentials.gamemode.others false`**（具体权限优先于父权限，可精确防改他人）；08-08 验收「子权限够用」是父权限残留假象
- **MCSM 目录 `page_size` 上限 100**：LuckPerms 目录导出文件多时用 `page_size=100` + 过滤词缩小范围
- **三端对齐流程模板**（2026-08-12 全流程验证）：`gen_perm_commands.py` 生成蓝本 → 每组 `permission clear` + 逐条 set → 每端先 `lp export` 备份 → 完成后 export 对比验证（组节点数 + 继承链）→ LP 实时生效无需重启（MCSM 有玩家也可执行）

## 单测陷阱（Mockito）

- `ImmutableContextSet.empty()` 是静态工厂依赖 ContextManager——**用惰性方法不要静态初始化字段**；`InheritanceNode.builder()` 同样依赖 LuckPermsProvider.get()——产品代码用 `api.getNodeBuilderRegistry().forInheritance().group(name).build()`
- mock Group 的 `data()` 返回 null → `.add()` NPE（难查的「Wanted but not invoked」）——必须 stub `when(g.data()).thenReturn(mock(NodeMap.class))`
- createAndLoadGroup 动态 mock：thenAnswer 存 Map，getGroup 从 map 取值
- 嵌套 stubbing → UnfinishedStubbingException——先构造结果对象到局部变量再 thenReturn
- 断言用 `argThat(qo -> qo.context().isEmpty())`（访问器是 `context()` 不是 `getContext()`）

## 配套存储：审核记录增长控制（YAML）

- PENDING 天然有界（防重复提交）；**结案记录（APPROVED/REJECTED/CANCELLED）需裁剪**：save() 写盘前按玩家保留最近 N 条（如 10），超限删最旧；PENDING 永不删

## 支持文件

- `references/permission-impl.md`：权限组配置指针版（权威源=仓库 docs/permission-groups.md，含生成/同步流程）
- `scripts/gen_perm_commands.py`：从权限权威文档生成 LP 命令清单（方案①：文档唯一权威）
- `references/permission-impl.md`：插件默认开启权限盘点清单
- `references/permission-impl.md`：Bootstrap 校正模式（LP 5.5 API 细节）
- `references/context-trap-case-study.md`：上下文陷阱完整根因链
- `references/permission-impl.md`：LP API 直调（类加载三连坑/saveUser/AMBIGUOUS_CALL——从 paper-plugin-development 迁入）
- `scripts/scan_default_perms.py`：扫描 default:true 权限
- `scripts/rcon_batch.js`：RCON 批量执行（2 字节 padding 协议，85 条 ≈ 30 秒）
- `scripts/rcon_cmd.js`：RCON 单条命令
- `scripts/exa_lp_sync.sh`：Exaroton LP 同步
