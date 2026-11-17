# 权限体系实现细节（LuckPerms 集成 / Rank 模块 / 权限组配置）

> 2026-11-10 由 9 篇专题合并（内容未改写，仅按主题分区）。**上层概念与四组规划**见 `permission.md`；插件默认权限盘点、LP API 集成、track 设计、Rank 晋升与时长数据源、状态展示、权限组收敛方案都在本文。
>
> 目录：1) Bootstrap 校正与权限名核实 2) LP API 软依赖集成 3) track API 与权限链设计 4) Rank 模块细节 5) 权限组配置指针 6) 插件默认开启权限盘点 7) Rank↔LP 幂等验证 8) 在线时长数据源 9) 权限状态展示与数据卫生

## 1. LuckPermsBootstrap 校正模式 + 权限名核实（2026-08-08 实战）
> 来源：原 `references/permission-impl.md`（2026-11-10 并入本文件，内容未改写）

## 背景

OrzMC 权限系统：LuckPermsBootstrap 启动自动建 track「rank」（default→member→builder→admin）
与组（member→default、builder→member、admin→builder）。原实现「已有组跳过」导致 1.0.15
遗留组继承错误永不校正（MCSM builder parent=default 缺 member 功能）。改造为「校正继承与
track 链序，权限节点不碰」。

## LP 5.5.71 API 细节（编译/测试踩坑实录）

| API | 事实 | 坑 |
|:--|:--|:--|
| `Group.getParentGroups()` | **不存在** | 想当然写它编译报「找不到符号」 |
| `NodeMap.toMap()` | 返回 `Map<ImmutableContextSet, Collection<Node>>` | key 是上下文集**不是 String**，mock `thenReturn(Map<String,...>)` 编译错 |
| `NodeMap.toCollection()` | 返回扁平 `Collection<Node>` | 读继承/权限节点的正道——遍历 `instanceof InheritanceNode` |
| `NodeMap.clear(Predicate<? super Node>)` | 按谓词清节点 | 清继承：`clear(node -> node instanceof InheritanceNode)`——只动继承不动权限 |
| `Track.getGroups()` | 返回 **`List<String>`**（组名） | 想 stream map `Group::getName` 报「方法引用无效」（元素已是 String） |
| `TrackManager.deleteTrack(Track)` | 存在，返回 CompletableFuture | 链序不一致时 delete 后重建 |
| 继承节点写入 | `api.getNodeBuilderRegistry().forInheritance().group(name).build()` | 静态 `InheritanceNode.builder()` 在测试环境抛 NotLoadedException——必须走注入的 api |

## 校正实现骨架（ensureParent 模式）

```java
// 读当前继承：toCollection 过滤 InheritanceNode
Set<String> current = new HashSet<>();
for (Node node : group.data().toCollection()) {
    if (node instanceof InheritanceNode in) current.add(in.getGroupName());
}
if (current.size() == 1 && current.contains(expectedParent)) return; // 已正确，跳过
// 校正：清继承节点 → 重挂设计 parent → saveGroup
group.data().clear(node -> node instanceof InheritanceNode);
group.data().add(api.getNodeBuilderRegistry().forInheritance().group(expectedParent).build());
api.getGroupManager().saveGroup(group);
```

track 链序校正：`existing.getGroups()`（List<String>）与设计链比对，不一致 →
`deleteTrack(existing)` 后 `createAndLoadTrack` + 逐个 `appendGroup(getGroup(name))`。

## 单测模式（mock 继承节点）

```java
private Group mockGroup(String name, String parent) {
    Group g = mock(Group.class);
    NodeMap nm = mock(NodeMap.class);
    Collection<Node> nodes = new ArrayList<>();
    if (parent != null) {
        InheritanceNode node = mock(InheritanceNode.class);
        when(node.getGroupName()).thenReturn(parent);
        nodes.add(node);
    }
    when(nm.toCollection()).thenReturn(nodes);  // 关键：mock toCollection 而非 toMap
    when(g.data()).thenReturn(nm);
    return g;
}
```

覆盖场景：继承正确→跳过（never saveGroup）；继承错误→只校正目标组（saveGroup times(1)）；
track 链序一致→跳过；不一致→deleteTrack+createAndLoadTrack。

## 权限名核实方法（配置表重梳，避免配无效节点）

**双通道确认权限名真实存在**：
1. **plugin.yml 权威**（权限树 + children 结构）：`unzip -p <jar> plugin.yml | sed -n '/^permissions:/,/^[^ ]/p'`
   - 父权限检查 children：如 `getmehome.user` 的 children 含 5 个家命令——**1 个父权限替代
     5 个分列节点**（LP 展开 children，check command.sethome 也 true）
   - EzShops 的 `ezshops.shop` **无 children**（buy/sell 独立）——不能合并
2. **jar 字节码 grep**（代码注册的权限，plugin.yml 不列）：
   ```bash
   unzip -oq <jar> "*.class" -d /tmp/x && grep -rao "插件前缀\.[a-z.][a-z.]*" /tmp/x | sort -u
   ```
   - 实测确认：LoginSecurity 的 `ls.bypass`、DeathChest 的 `deathchest.command.report` 都在代码里
   - 剔除无效名：`essentials.reply`/`essentials.craft`/`essentials.teleport` 在 EssentialsX 2.22.0
     plugin.yml 与字节码都不存在（/reply 随 /msg；/craft 是 /workbench 别名）；`essentials.baltop`
     真实名是 `essentials.balancetop`

**合并候选规则**：能通配/父权限合并的绝不分列；但**通配避开管理分支**（`worldedit.*` 含 reload、
`worldguard.region.*` 含 bypass/override、`essentials.gamemode.*` 含 others——都用裁剪子集通配
如 `worldedit.selection.*`、`worldguard.region.claim.*`）。

## 验证三连（每项权限配置后）

1. `lp group <组> permission check <节点>`（bot 群 $e 通道，日志 grep「結果: true/undefined」）
2. 实际命令（对应组账号实测——如 `/gamemode creative`、`//wand`、`/sethome`）
3. 越权反查（`lp group admin permission check minecraft.command.op` → false）

## 2. LuckPerms API 软依赖集成（2026-08-07 权限链重构实战）
> 来源：原 `references/permission-impl.md`（2026-11-10 并入本文件，内容未改写）

场景：插件内直接调 LP API（`net.luckperms:api`）实现权限链升降级，替代旧的
`dispatchCommand("lp user X ...")` 控制台命令方案。本文记录类加载、持久化、track
语义三块硬坑，全部经本地实测验证。

## 1. 类加载三连坑（按出现顺序，每坑一次部署实测）

### 坑 1：`implementation` 打进 jar → `NotLoadedException: The LuckPerms API isn't loaded yet!`

把 `net.luckperms:api` 作为 `implementation` 打进 shadowJar 后，插件**能启动**，
但运行时报：
```
net.luckperms.api.LuckPermsProvider$NotLoadedException: The LuckPerms API isn't loaded yet!
```
根因：Bukkit 插件类加载器是 **child-first**——插件加载的是**自己 jar 里的**
`LuckPermsProvider` 副本，而 LP 插件注册 provider 用的是**它自己类加载器里**的
`LuckPermsProvider`，两个类不是同一个 → 静态 provider 字段为空。

### 坑 2：`compileOnly` + 旧格式 `softdepend` → `ClassNotFoundException`

改 `compileOnly` 后插件启动即崩：
```
java.lang.ClassNotFoundException: net.luckperms.api.context.ContextSet
```
根因：**Paper 26 的 paper-plugin.yml 不认旧格式 `softdepend:`**——类加载顺序无保证，
OrzMC 先于 LuckPerms 加载，LP API 类尚不存在。

### 坑 3（正确解法）：`compileOnly` + Paper 26 新格式 `dependencies:`

```yaml
# build.gradle.kts
compileOnly("net.luckperms:api:5.4")     # 不打进 jar
testImplementation("net.luckperms:api:5.4")

# shadowJar 显式排除（双保险，防 minimize 误收）
exclude("net/luckperms/**")

# paper-plugin.yml — Paper 26 新格式，保证 OrzMC 在 LP 之后加载且 API 类可见
dependencies:
  server:
    LuckPerms:
      required: false
```
LP 插件运行时向全局 classpath 提供 API 类，依赖插件复用即可。

## 2. `track.promote()/demote()` 只改内存，必须显式 `saveUser()`（最容易漏）

LP API 的 `track.promote(user, ctx)` 返回 `SUCCESS` 但**不落库**——修改的是
`loadUser()` 返回的内存 User 对象。不调用 `saveUser` 的话：日志显示 SUCCESS、
本地显示"已升级"，但 `lp user X parent info` 查组**没变**（假成功）。
```java
PromotionResult r = track.promote(user, contextsFor(user));
if (r != null && r.wasSuccessful()) {
    api.getUserManager().saveUser(user).get(3, TimeUnit.SECONDS); // 必须！
}
```

## 3. track API 关键调用形态

```java
// 顶层入口：Bukkit 主线程外也安全（Provider 已由 LP 插件注册）
LuckPerms api = LuckPermsProvider.get();

// 用户：在线走缓存同步，离线异步加载（阻塞等 3s）
User user = api.getUserManager().getUser(uuid);          // 在线/已缓存
if (user == null) user = api.getUserManager().loadUser(uuid).get(3, SECONDS); // 离线

// track：名 "rank"，组序 default→member→builder→admin
Track track = api.getTrackManager().getTrack("rank");

// 上下文：promote/demote 需要 ContextSet（不是 QueryOptions！）
ImmutableContextSet ctx = api.getContextManager().getContext(user)
        .orElseGet(ImmutableContextSet::empty);

// 组查询：getInheritedGroups 收 QueryOptions，返回 Collection<Group>，
// 组名用 getName()（不是 getGroupName()——那个是 Node 的）
boolean in = user.getInheritedGroups(user.getQueryOptions()).stream()
        .anyMatch(g -> g.getName().equalsIgnoreCase("builder"));
```

## 4. 边界状态枚举（javap 反编译确认，不绕圈）

- `PromotionResult.Status`：SUCCESS / ADDED_TO_FIRST_GROUP（不在 track 自动加首组）/
  END_OF_TRACK（**链顶再 promote = 失败，不绕回**）/ MALFORMED_TRACK / AMBIGUOUS_CALL / UNDEFINED_FAILURE
- `DemotionResult.Status`：SUCCESS / REMOVED_FROM_FIRST_GROUP（链底移除首组回 default）/
  NOT_ON_TRACK / AMBIGUOUS_CALL / ...

**API 语义离线验证法**（网络受限时比 web 搜索可靠）：
```bash
curl -sL -o /tmp/lp-api.jar "https://repo1.maven.org/maven2/net/luckperms/api/5.4/api-5.4.jar"
unzip -o -q /tmp/lp-api.jar -d /tmp/lp-api-extract
javap -p /tmp/lp-api-extract/net/luckperms/api/track/PromotionResult\$Status.class
```

## 5. AMBIGUOUS_CALL：玩家同时挂在 track 多个组上时 promote/demote 失败

存量玩家常见（早期 `parent add` 叠加出 builder+member 双组）。此时 `track.promote`
返回 `AMBIGUOUS_CALL`，插件会误报"已在最高等级"。
**迁移动作**：`lp user X parent remove member`（保留最高组），track 语义要求单组。
涉及多端数据时，迁移脚本要幂等可重跑。

## 6. 为什么本地权限状态可以全删（架构结论）

LP track 成为唯一事实源后：
- `promoted` 标记（防重复自动晋升）→ LP 组本身就是幂等（已在 member 则
  `currentTrackGroup != default` 不触发）
- `demoted` 标记（抑制 APPROVED 记录判定）→ LP 里没有 builder 组 = 自然降级
- `admin` 标记（识别链顶）→ 不需要，LP 真实组直接给出

permission.yml 只剩 config（阈值）+ reviews（审核记录）两段。**唯一保留本地推断的
场景**：LP 未安装时回退（有 APPROVED builder 记录 → builder，否则 default）。

## 7. 软依赖降级：条件实例化 + Noop（用户拍板，禁止反射）

先做了一版反射（Class.forName+Method.invoke）规避类加载，用户否决（「反射容易
出问题，可以不用反射实现吗」）。**最终方案利用 JVM 惰性类加载——不执行 `new`
就不加载类，方法签名里的 LP 类型永不解析**：

```java
// ① 接口零 LP 引用（纯业务类型）——Noop 实现才能零依赖
public interface RankPromoter {
    boolean isAvailable();
    String currentTrackGroup(UUID id);   // 返回目标组名而非 LP 结果对象
    String promote(UUID id);             // null = 链顶/失败/LP 缺失
    String demote(UUID id);
    boolean isInGroup(UUID id, String group);
    UUID resolvePlayerId(String name);
    Optional<String> playerName(UUID id);
}

// ② LP 实现直接 import net.luckperms.api.*（类型安全），结果翻译成 String
// ③ NoopRankPromoter：全 null/false，零 LP 引用
// ④ 装配层：
if (Bukkit.getPluginManager().isPluginEnabled("LuckPerms")) {
    rankPromoter = new LuckPermsPromoter(resolver, serverFacade::runSync);
} else {
    rankPromoter = new NoopRankPromoter();
    log.warning("未检测到 LuckPerms，权限管理功能不可用（时长查询/申请记录仍可用）");
}
```

⚠️ **嵌套接口陷阱**：PlayerNameResolver/ServerScheduler 等辅助端口**必须提为独立
顶层文件**。若作为 `LuckPermsPromoter` 的嵌套接口，装配层引用
`LuckPermsPromoter.PlayerNameResolver` 会**连带加载外层类** → LP 缺失时
NoClassDefFoundError 照样炸（实测踩坑：嵌套接口版无 LP 启动崩溃，独立文件版正常）。

⚠️ **Mockito 测 LP API 的坑**：
- 嵌套 stubbing：`thenReturn(helper(...))` 里 helper 内部再 `when()` →
  UnfinishedStubbing。先构造局部变量再 thenReturn。
- `ImmutableContextSet.empty()` 是真实静态方法（内部调
  `ContextManager.getContextSetFactory()`）——mock 环境直接调用 NPE，连
  `verify(x).promote(user, ImmutableContextSet.empty())` 断言都炸。须 mock
  `ContextManager.getContextSetFactory()`（stub `immutableEmpty()`），verify 用
  `any(ImmutableContextSet.class)`。

**验收证据**（本地 25565）：有 LP——降级 admin→default 3 连 SUCCESS、升级
default→admin 3 连 SUCCESS、链顶 END_OF_TRACK 提示「已在最高等级」、链底
「已在最低等级」，全链真实落库（`lp user X parent info` 双证据）；无 LP（删
LP jar 重启）——插件正常启动、$p 提示「未检测到 LuckPerms，权限管理功能不可用」。

## 3. LuckPerms track API 与权限链设计（2026-08-07 决策记录）
> 来源：原 `references/permission-impl.md`（2026-11-10 并入本文件，内容未改写）

OrzMC 权限系统二期「升降级 + 权限链生命周期」的设计决策与 API 证据。未来做权限链/等级系统时先读本文。

## 一、LP track API 原生钳位语义（反编译证据，LP api 5.4）

从 `repo1.maven.org/maven2/net/luckperms/api/5.4/api-5.4.jar` 反编译（`javap -p`）：

**PromotionResult$Status**：`SUCCESS`、`ADDED_TO_FIRST_GROUP`（不在 track 上 → 加入首组）、`MALFORMED_TRACK`、`END_OF_TRACK`（链顶再 promote = 失败，**不绕回**）、`AMBIGUOUS_CALL`、`UNDEFINED_FAILURE`

**DemotionResult$Status**：`SUCCESS`、`REMOVED_FROM_FIRST_GROUP`（链底 demote = 移除首组回 default）、`MALFORMED_TRACK`、`NOT_ON_TRACK`（不在 track = 已是 default）、`AMBIGUOUS_CALL`、`UNDEFINED_FAILURE`

**Track 接口**：`getGroups()`（链定义）、`promote(User, ContextSet)` / `demote(User, ContextSet)`、`getNext/getPrevious(Group)`、`containsGroup`、`appendGroup/insertGroup/removeGroup/clearGroups`

**UserManager**：`getUser(UUID)` 同步查缓存（在线）、`loadUser(UUID)` 异步 CompletableFuture（离线）、`getPrimaryGroup()`

## 二、设计决策链（用户评审驱动）

1. **用户问「升级/降级到链底/链顶时后续如何处理」** → 最初假设 LP track 绕圈 → 用显式 parent add/remove 钳位。**反编译证伪该假设** → LP track API 原生钳位，一行调用即可。
2. **用户问「为什么要标记 admin」** → 本地 admin 标记会造成**双写漂移**：管理员手动 `lp user X parent add admin` 时本地无标记（$l 显示错误）；`$p u` 升 admin 后 LP 手动移除，本地标记残留（幽灵权限）。结论：**当前组快照必须以 LP 为准，本地不存**。
3. **用户要求「配置文件中尽量以最少的记录信息完成功能」** → promoted/demoted/admin 本地标记全删，permission.yml 只留 config + reviews 两段。
4. **用户拍板「$v 纯审核、$p 权限管理」** → 审核命令（l/y/n 裁决申请）与管理命令（u/d 管理员主动操作）语义分离；`$d` 已被黑名单占用故用 `$p`。
5. **用户要求「玩家权限变化需群广播」** → 通知双通道：游戏内消息（在线玩家）+ 群广播（所有人可见）。复用 `ReviewNotifier`（已有 gameMessage + groupEvent 两方法）。
6. **用户要求「兼容无 LuckPerms」** → `RankPromoter.isAvailable()` 守卫；无 LP 时 `promote/demote/checkPromotion` 跳过且**不写本地状态**（防「本地已升 LP 未变」脱节）；`$p` 明确提示「未检测到 LuckPerms，权限管理功能不可用」；/rank 时长、/apply 记录仍可用。

## 三、事件标记 vs 状态快照（核心概念）

- **promoted/demoted 是「一次性事件标记」**：记录「发生过自动晋升/降级」，可以本地存（幂等用）。
- **admin 是「当前组状态快照」**：反映「现在是什么组」，必须查 LP 真实组，本地存必然漂移。
- 判断标准：标记记录「发生了什么」（事件）可本地化；记录「现在是什么」（状态）必须权威源查询。

## 四、LP API 查询的线程安全注意

- 在线玩家 `getUser(uuid)` 有缓存，同步安全。
- 离线玩家 `loadUser(uuid)` 异步：`$p` 低频操作可在异步线程 `.get(3, SECONDS)` 阻塞；主线程严禁阻塞等待（Paper 主线程卡顿）。
- LP 命令派发仍须主线程（`Asynchronous Command Dispatched Async`），见 SKILL.md 陷阱 #2。

## 五、LP API 直调实现骨架（LuckPermsPromoter 重写版，2026-08-07 实测，含类加载三连坑修正）

**build.gradle.kts**：
```kotlin
compileOnly("net.luckperms:api:5.4")          // 软依赖：不打进 jar（见下方类加载规则）
testImplementation("net.luckperms:api:5.4")   // 单测 mock Track/User/结果枚举需要
```
依赖在 `repo1.maven.org` 可解析（repo.luckperms.net 常被墙，不要用）。

**paper-plugin.yml（Paper 26 新格式，旧 `softdepend:` 不提供类加载器可见性）**：
```yaml
dependencies:
  server:
    LuckPerms:
      required: false
```

**shadowJar 必须排除 LP 包**（否则 child-first 加载自带 Provider 副本 → `LuckPermsProvider$NotLoadedException`）：
```kotlin
shadowJar { exclude("net/luckperms/**") }
```

**类加载安全（无反射，用户明确拒绝反射）**：`RankPromoter` 接口只用纯业务类型（String/UUID/boolean，promote/demote 返回目标组名）；装配处条件实例化——
```java
RankPromoter promoter = Bukkit.getPluginManager().isPluginEnabled("LuckPerms")
    ? new LuckPermsPromoter(resolver, sched)
    : new NoopRankPromoter();  // 返回 null/false，$p 提示不可用
```
JVM 类加载惰性：`if` 为假时永不加载 LuckPermsPromoter 类（其方法签名含 LP 类型），LP 缺失时插件正常启动。**不要用 Class.forName/Method.invoke 反射**——脆弱难维护。

**⚠️ 注入接口必须独立文件**：`PlayerNameResolver`/`ServerScheduler` 若定义为 `LuckPermsPromoter` 的嵌套接口，装配层引用 `LuckPermsPromoter.PlayerNameResolver` 符号会加载 LuckPermsPromoter 类（嵌套成员在外部类加载时定义）→ 破坏惰性加载。两个注入接口都提为独立顶层文件（`PlayerNameResolver.java`、`ServerScheduler.java`）。

**核心调用模式**（全部走 API，废弃控制台命令 dispatch）：
```java
// 1. 拿 track（未加载返回 null）
Track track = LuckPermsProvider.get().getTrackManager().getTrack("rank"); // "rank": default→member→builder→admin

// 2. 加载用户（在线缓存同步 / 离线异步阻塞 3s）
User user = LuckPermsProvider.get().getUserManager().getUser(uuid);       // 在线
if (user == null) user = LuckPermsProvider.get().getUserManager().loadUser(uuid).get(3, TimeUnit.SECONDS);

// 3. 升降级（钳位由 LP 原生保证，返回结果枚举）
// ⚠️ 第二参数是 ContextSet 不是 QueryOptions！用用户上下文或空集：
ImmutableContextSet ctx = LuckPermsProvider.get().getContextManager().getContext(user)
        .orElse(ImmutableContextSet.empty());
PromotionResult r = track.promote(user, ctx);  // 或 track.demote(user, ctx)
// r.wasSuccessful() 判断；r.getGroupTo() / r.getGroupFrom() 是 Optional<String>（翻译提示用）
// END_OF_TRACK → 链顶提示；REMOVED_FROM_FIRST_GROUP / NOT_ON_TRACK → 链底提示

// 4. ⚠️⚠️ 成功后必须显式持久化——LP API 变更只改内存 User 对象，不自动落库！
//    （游戏内 lp 命令路径会自动保存，API 直调不会。漏掉 = SUCCESS 假成功，组查询不变）
if (r.wasSuccessful()) {
    LuckPermsProvider.get().getUserManager().saveUser(user).get(3, TimeUnit.SECONDS);
}

// 5. isInGroup 真实现：getInheritedGroups(QueryOptions) 返回 Collection<Group>，取组名用 group.getName()
Collection<Group> groups = user.getInheritedGroups(user.getQueryOptions());
boolean in = groups.stream().anyMatch(g -> g.getName().equalsIgnoreCase(groupName));

// 6. 必须在主线程调用！复用现有 scheduler.runSync + CompletableFuture.join 模式（SKILL.md #2）
```

**RankService 侧**（翻译结果 + 双通道通知）：
- `promote/demote` 返回 `String`（目标组名）：`result.getGroupTo().orElse(currentGroup(playerId))`；`!wasSuccessful()` 或结果 null → 返回 null（调用方提示「已在最高/最低等级」）
- `checkPromotion` 幂等由 LP 保证：`promoter.currentTrackGroup(id)` 为 null 或 "default" 且时长达标才 promote（无需本地 promoted 标记）
- 通知双通道：`notifier.gameMessage(uuid, "你的权限已升级：X。")` + `notifier.groupEvent("rank_promoted"/"rank_demoted", Map.of("player", name, "group", displayName))`（复用 ReviewNotifier 两个方法即可，无需新端口）。⚠️ 新增 groupEvent 调用点必须同步登记到 `ReviewNotifierAdapter.groupEvent` 的 fallback switch + templates.yml 默认键 + 单测断言 fallback（漏了群消息原样输出 `{message}`，详见 SKILL.md「群广播模板 fallback 陷阱」整节）
- `groupDisplayName` 补全四档：admin→管理员、builder→建造者、member→会员、default→访客
- `RankPromoter` 接口加 `playerName(UUID) → Optional<String>`（群广播要玩家名，resolvePlayerId 的反向）

**RankStore 瘦身**：只剩 `getPlaytimeMinutes(UUID)`（读 stats），promoted/demoted 全部方法删除；PermissionStore 只实现 ReviewStore + playtime。

## 4. OrzMC 权限系统（rank-promotion 二期）细节
> 来源：原 `references/permission-impl.md`（2026-11-10 并入本文件，内容未改写）

仓库：`~/OrzMC/plugin`（分支 feat/rank-promotion，PR #160 → 1.0.16）
方案/验收文档：`docs/permission-system-v2.md` + `-acceptance.md`（与代码同步维护）

## 四级 track 与中文名

`default→member→builder→admin`（LP track 名 `rank`）。中文名唯一事实源 `RankService.groupDisplayName()`：访客/成员/建造者/管理员，组外回退访客。$l 在线列表、广播、rank 通知、/rank、$p 反馈全走此方法。

## 状态展示矩阵（/rank 与 /apply 按当前组动态）

| 当前组 | /rank | /apply 可申请 |
|:--|:--|:--|
| default | 时长 + 晋升成员阈值进度（还需 X / ✅已达标）+ 「下一步：在线时长达标后自动晋升为成员」 | 无 |
| member | 时长 + 阈值（✅已达标）+ 「下一步可申请：晋升建造者（/apply builder）」 | 晋升建造者 |
| builder | 时长（不展示已完成的 member 阈值）+ 「下一步可申请：晋升管理员（/apply admin）」 | 晋升管理员 |
| admin | 时长 + 「已达最高等级（管理员）」 | 无 |

「下一步可申请」由 ReviewType 注册表反向生成（资格预检通过的项），不硬编码。

## 审核框架（features/review/）

- ReviewType 注册表驱动：`builder-promotion`（member→builder）+ `admin-promotion`（builder→admin）；handler 由 rank 模块注入（LP 授权），review 包零 LP/宿主依赖
- 群指令 `$v l/y/n <玩家>`（待审列表含当前组）；游戏内 `/apply`（列表按资格过滤）+ `/review approve|reject`
- 审核通过 = `rankService.promote(playerId) != null`（null=链顶/LP 异常 → 保持 PENDING，避免「已通过但未生效」）
- 群通知 4 环节模板键：review_submitted/cancelled/approved/rejected + rank_promoted/rank_demoted
- 玩家结果三层兜底：游戏内消息 → 群通知 → /apply status
- $h 帮助与 $cmd ? 用法：BotCommandFeedbackService.helpInfo 硬编码拼接 + usageTip switch——加新指令须同步两处（曾漏 $v/$p）

## 管理员私信（PRIVATE）场景（admin_dm 目标）

Notifier.routeEvent 按模板键路由，PRIVATE 仅 3 键：exception_alert（插件/GeoIP 异常，带 ThrottledNotifier 节流）、maintenance_backup_error、maintenance_optimize_error。其余全 PUBLIC 群消息。server_maintenance_hint（最后一人退出提示维护）已移除（8ad86be，触发过频）。

## 排障案例：joker AMBIGUOUS_CALL（根因闭环）

- 现象：$p d joker 提示「无法再降级」；/rank 显示建造者（已 demote 至 default）
- 排查：`$e lp user joker parent info` 实锤 world=world/gamemode=creative 上下文的 builder+member 组——一期 $p 用玩家实时上下文操作产生（LP 把节点存为完整上下文快照）
- 修复链：① 数据清理无上下文叠加组（治标）→ ② 代码统一 global 上下文（治本，63dc5ef）→ AMBIGUOUS_CALL 消失；$p u 不在 track 的玩家连续 promote 直达 member
- 教训：看到 AMBIGUOUS_CALL 先查 parent info 看是否有带上下文/重叠节点；别再只当「边界提示」处理

## 测试环境

- 本地服 = MCSM 实例 papermc-test（uuid 716c2fb7，enable-rcon=true, 25575 容器内）；部署链（2026-09-03 起）：cp build/libs/OrzMC-*.jar → 实例目录 `plugins/` → 面板重启实例（~60s Done）
- RCON 驱动 orzdebug 模拟群消息：~/minecraft-bot/p-test.js（`$p` 参数须单引号防 shell 展开）
- bot 玩家登录跑游戏内命令：rank-single.js / cmd-one.js（自动 /login，LoginSecurity 有 30s 重登冷却）
- 测试账号：TestMember=81b4d507…、HermesBot=74ce0d95…、joker=bbb8b47e…（密码在脚本内，勿外泄）
- 门禁：./gradlew spotlessApply + check + shadowJar（CI Java 25）

## 5. 权限组配置（指针版 — 2026-08-12 方案①收敛）
> 来源：原 `references/permission-impl.md`（2026-11-10 并入本文件，内容未改写）

> **唯一权威来源：`OrzMC/plugin/docs/permission-groups.md`**（git 版本化，含每项验证指令 / 验收记录 / 插件默认权限盘点）。
> 本文件只留指针与关键决策，**不再维护节点明细**——改权限 = 改仓库文档 → 重新生成，防止多源漂移（旧摘要版已出现 L2 31 vs 实际 33 的漂移，故收敛）。

## 生成与同步

```bash
# 1. 从权威文档生成 LP 命令清单（输出含父链命令 + 高危注释）
python3 ~/.hermes/skills/gaming/orzmc/scripts/gen_perm_commands.py -o /tmp/perm.txt
# 2. 三端同步：每端先 lp export 备份 → 每组 permission clear + 逐条 set
#    （执行前 grep -v '^#' 过滤注释）→ 完成后 export 对比验证（组节点数+继承链）→ LP 实时生效
```

## 关键决策（防回归）

- 四组增量：default(23) / member(19) / builder(35) / admin(37)；继承链 member→default、builder→member、admin→builder（LuckPermsBootstrap 启动自动校正）
- **2026-08-30 重规划**（老板审核通过，决策记录见仓库文档）：L0 +10 生存工具（rules/motd/list/depth/compass/getpos/recipe/hat/near/seen）、L1 +5（tpdeny/tpacancel/ptime/pweather/abandonclaim）、L2 +2（speed/f3f4perms.use）、L3 +4 运营工具（mute/tempban/banip/unbanip）；/nick 不开放；/kit 维持 member；siege/GetMeHome 家功能保持默认
- **高危节点任何组不授**：`*`、`luckperms.*`、`minecraft.command.op`、`bukkit.command.op`、`essentials.stop/reload`
- builder 必须显式 `essentials.gamemode.others false`（父权限含 .others，防改他人模式）
- Litematica 投影三件套：`minecraft.command.setblock/fill/data`；**不授 `summon`**
- 插件 default:true 权限（未声明也生效）盘点 → `references/permission-impl.md`

## 6. 插件默认开启权限盘点（2026-08-08）
> 来源：原 `references/permission-impl.md`（2026-11-10 并入本文件，内容未改写）

场景：OrzMC 权限最小化重梳后「joker 是 default 却能用 sethome」——最终根因是
**插件权限默认值**（GetMeHome `default: true`），与残留 member 组并存（残留组贡献
tpa，插件默认贡献 sethome）。

## 盘点方法

- 脚本：`scripts/scan_default_perms.py`（python zipfile+yaml 遍历插件 plugin.yml，
  过滤 `default: True` 的权限）
- **WE/WG 权限在代码注册**（plugin.yml 无 permissions 段）——不在此列，
  默认按 false/op 处理（builder/admin 显式配置才可用）

## 盘点结果（本地 16 插件，default: true）

| 插件 | 权限 | 配置表声明 | 实际影响 |
|:--|:--|:--|:--|
| GetMeHome | `getmehome.user`（父——含 sethome/home/delhome/listhomes/setdefaulthome） | L0 未声明 | **所有玩家可用全部家功能**——禁需 default 组 6 条显式 false（父+5 命令，插件默认不吃父 false） |
| GetMeHome | `bstats` | - | 统计（无关） |
| EssentialsX | `essentials.back.onteleport` | 未声明 | 传送后死亡点回档 |
| EssentialsX | `essentials.teleport.cooldown.bypass.tpa` / `.back` | 未声明 | tpa/back 冷却豁免 |
| EzShops | `ezshops.playershop.create` / `.buy` | L1（冗余） | default 也能创建/购买玩家商店 |
| EzShops | `ezshops.stock.view` / `teamshop` / `teamshop.market` / `teamshop.treasury.withdraw` | 未声明 | 库存/团队商店默认开 |
| GriefPrevention | `createclaims` | L1（冗余） | default 也能圈地 |
| GriefPrevention | `claims` / `trapped` / `ignore` / `givepet` / `unlockdrops` / `buysellclaimblocks` / `abandonallclaims` | 部分未声明 | 领地基本功能默认开 |
| GriefPrevention | `siege` | 未声明 | **攻城默认开**（风险项） |
| BackOnDeath | `bod.back` | L0 已声明 | 一致 |

## 关键结论

1. **LP check undefined ≠ 不可用**：组无节点时 LP check 显示 undefined，但插件默认
   true 实际可用——命令可用性唯一权威是 bot 实测命令（default 玩家实测：
   /sethome ✅ 可用、/rg claim ✅ 权限放行、/tpa ❌ 无权限——对齐）
2. **插件默认不吃父权限 false**：`getmehome.user false` 不覆盖子权限默认 true——
   必须逐项显式 `set <node> false`
3. **风险项建议**（需用户决策）：GP `siege`（攻城）、`abandonallclaims`（一键弃全部
   领地）——如不允许需 default 组显式禁
4. **命令未注册 ≠ 权限问题**（反例标注）：`essentials.spawn`、`worldedit.navigation`
   （//unstuck）在 Paper 26.2 命令未注册——权限节点有效（LP check true）但命令
   Unknown，标注「当前不可用」保留节点（命令恢复后即生效）

## 文档对齐原则

权限组配置文档须反映**实际可用状态** = LP 组声明 ∪ 插件默认清单；
不可用项（命令未注册）在配置表标注「当前不可用」而非删除节点。

## 7. OrzMC Rank 模块 LP 集成：幂等与状态验证（2026-08-07 实测）
> 来源：原 `references/permission-impl.md`（2026-11-10 并入本文件，内容未改写）

背景：Rank 自动晋升通过 `server.dispatchCommand(consoleSender, "lp user <name> promote rank")` 执行（零 API 依赖）。本文件记录**幂等设计**与**状态验证手段**的实测结论。

## ⚠️ 核心教训：`lp promote <track>` 没有天然幂等

- `lp promote rank` 每次调用都沿 track **升一级**（default→member→builder→admin），不是"确保达到某组"。
- 多调一次 = 多升一级。**没有任何幂等保护**。

## 实测 bug：isInGroup 预判失效 → 连升两级

### 症状
TestNewbie（default，达标 600min）两次 join 后 LP 显示 **builder**（预期 member）。

### 根因
```java
// ❌ 错误实现（占位判断，不是真 LP 查询）
public boolean isInGroup(UUID id, String group) {
    return DEFAULT_GROUP.equals(group) && server.getPlayer(id) != null; // 在线即认为在 default
}
```
控制台执行 LP 命令的结果**无法回读**（RCON 不回显 Adventure 组件输出），isInGroup 只能退化成"玩家在线"占位 → 每次 join 都满足"在 default"→ 每次达标都 promote → 两次 join 升了两级。

### ✅ 正确方案：自有持久化标记保证幂等
```java
// RankStore 接口新增
boolean hasPromoted(UUID playerId);
void markPromoted(UUID playerId);

// RankService.checkPromotion
if (store.hasPromoted(playerId)) return;          // 已晋升过不重复处理
if (store.getPlaytimeMinutes(playerId) >= threshold) {
    promoter.promoteToNext(playerId);
    store.markPromoted(playerId);                  // 标记落盘 ranks.yml
}
```
- isInGroup 改为**恒 false**（不做预判，语义改成"不依赖 LP 查询"），预判职责完全交给 hasPromoted。
- ranks.yml：`players.<uuid>.promoted: true`（markAlwaysSave 持久化）。
- 注意：手动把玩家调回 default 重测时，**旧 promoted 标记会阻止再晋升**——重测前清标记（或对测试账号直接预置标记）。

## LP 状态验证三手段（实测排序）

| 手段 | 适用 | 坑 |
|:--|:--|:--|
| **bot 玩家身份 `lp user X info`** | 常规验证 | **Adventure 组件截断输出**：`[LP] - Parent Groups:` 与内容 `[LP]     > builder` 是**两条独立消息**，grep 关键词只见标题不见内容——必须连后续行一起抓（如 grep -A2 或监听多条消息拼接） |
| **H2 mtime** | 判断命令是否执行 | `stat -f %m .../luckperms-h2-v2.mv.db` 前后对比；**运行中 H2 被 LuckPerms 独占锁定**，外部连库报 `Database may be already in use ... [90020-214]`，只能停服后查 |
| LP 命令回显 | 中文 locale | `> default`/`> member` 等行，注意 locale 差异 |

## 测试账号重置流程（重测自动晋升前）✅ 已实测（2026-08-07）

```bash
# 用 TestAdmin（admin 组）执行：
#   lp user TestNewbie parent remove builder
#   lp user TestNewbie parent add default
# 然后验证：lp user TestNewbie info → Parent Groups: > default
# 最后清/预置 ranks.yml 的 promoted 标记
```
实测：重置回 default + 清 promoted 标记 → 上线 join → **只升一级到 member**（LP info 确认 `> member`）→ 再 join 不再升（标记生效）。

## LP 软依赖检测（2026-08-07 用户拍板实现，防无 LP 服静默失败）

插件未在 plugin.yml 声明 LP 依赖（软依赖），`lp ...` 命令在无 LP 服务器上执行**静默失败**（无报错无晋升）。已实现运行时检测：

```java
// LuckPermsPromoter
public boolean isLuckPermsEnabled() {
    PluginManager pm = Bukkit.getPluginManager();
    return pm != null && pm.isPluginEnabled("LuckPerms");
}
public void promoteToNext(UUID playerId) {
    String name = nameResolver.resolve(playerId);
    if (name == null || !isLuckPermsEnabled()) return;  // LP 未装 → 跳过晋升
    dispatch("lp user " + name + " promote " + TRACK);
}
```
- FeatureModule 装配时检测：未装打警告日志「未检测到 LuckPerms，Rank 晋升功能禁用（时长查询/申请记录仍可用）」
- 降级行为：无 LP 服 `/rank` 时长、`/apply` 申请记录仍可用，仅晋升动作跳过
- 测试：`LuckPermsPromoterTest`（mockStatic Bukkit + try-with-resources 包住；LP 装载/缺失 × isLuckPermsEnabled/promoteToNext/promoteToBuilder）
- ⚠️ mockStatic 泄漏教训：`mockStatic(Bukkit.class)` 必须在每个测试的 `try(...)` 内开启，@BeforeEach 里开不关会让 stub 泄漏到后续测试

## 关联
- `references/permission-impl.md`（时长数据源：stats 文件读取）
- SKILL.md「OrzMC 新 feature 开发坑」章节
- minecraft-bot-mineflayer `scripts/perm-check.js`（LP 权限验证 bot）

## 8. OrzMC Rank 玩家在线时长数据源调研（2026-08-07 实测，最终方案已验证）
> 来源：原 `references/permission-impl.md`（2026-11-10 并入本文件，内容未改写）

背景：Rank 晋升模块需要「累计在线时长」。用户要求**优先 PaperMC 插件 API**、与服务器同一数据源、玩家离线也能读。以下为三种方案的实测结论。

## 方案对比（实测终版）

| 方案 | 必须在线？ | 实测结果 | 结论 |
|:--|:--|:--|:--|
| 自计算（join/quit 事件差） | ✅ 必须 | 可行但崩溃丢最后一段时长；quit 事件异常断线不触发 | ❌ 放弃 |
| **读 stats 文件**（`<世界根>/players/stats/<uuid>.json`） | ❌ 不需要 | **✅ 最终采用**：与服务器同源、离线可读、零自计算误差 | ✅ 采用 |
| `OfflinePlayer.getStatistic(Statistic.PLAY_ONE_MINUTE)` | ❌ 设计上可离线 | **在线/离线都恒返回 0**（Paper 已知 bug） | ❌ 不可用 |

## ✅ 最终实现方案（已实测通过，HermesBot 显示 106 分钟）

```java
static Path statsDirectory() {
    var worlds = Bukkit.getWorlds();
    if (!worlds.isEmpty()) {
        Path p = worlds.get(0).getWorldFolder().getAbsoluteFile().toPath();
        while (p != null) {
            if (Files.exists(p.resolve("players").resolve("stats"))) {
                return p.resolve("players").resolve("stats");
            }
            p = p.getParent();
        }
    }
    // 兜底：世界容器根
    return Bukkit.getWorldContainer().getAbsoluteFile().toPath()
            .resolve("world").resolve("players").resolve("stats");
}
// 读值：Gson 解析 stats.minecraft.custom["minecraft:play_time"]，tick ÷ 1200 = 分钟
```

**⚠️ Paper 26+ 核心坑（调试日志逐层暴露）**：
- `Bukkit.getWorlds().get(0).getWorldFolder()` 返回**维度子目录**：`world/dimensions/minecraft/overworld`——不是世界根！
- stats 实际在世界根：`world/players/stats/`（players 子目录，不是 `world/stats/`）
- **固定 getParentFile() 一次/两次都错**（`.../dimensions/minecraft/overworld` 的父链是 `minecraft` → `dimensions` → `world`，层级会随版本变化）——**向上遍历找含 `players/stats` 的祖先目录**最稳
- 插件代码里 `Paths.get("world",...)` 相对路径解析到 `<server>/plugins/<PluginName>/world/...`（data folder，不存在）→ 必须绝对路径

## ✅ 已验证事实（可复用）

1. **stats 文件位置**：`<世界根>/players/stats/<uuid>.json`——注意是 **players 子目录**（`world/players/stats/`），不是 `world/stats/`
2. **时长键**：`stats.minecraft.custom["minecraft:play_time"]`（tick 单位），另有 `minecraft:total_world_time`。实测 joker=269726 ticks≈224 分钟
3. **tick→分钟**：÷1200（20 tick/s × 60 s/min）
4. **离线服 UUID 算法**：`UUID.nameUUIDFromBytes(("OfflinePlayer:"+name).getBytes())` 的 **RFC4122 v3**（bytes[6] |= 0x30、bytes[8] |= 0x80）。Java 手拼 UUID 会错版本位（如 1187 vs 3187）——用 `UUID.nameUUIDFromBytes` 或 Python `uuid.uuid3` 等价实现
5. **Paper API 无自定义 key 读统计方法**：反编译 paper-api 26.1.2 确认 `OfflinePlayer.getStatistic`/`Player.getStatistic` 只收 `Statistic` 枚举（无 NamespacedKey 版本）
6. **getStatistic(PLAY_ONE_MINUTE) 恒 0 的根因**：PaperMC/Paper#9507——Bukkit 按枚举名生成键 `play_one_minute`，但 MC 1.20.2+ 服务器内部键改名 `minecraft:play_time`，映射断裂；`TOTAL_WORLD_TIME` 同理（键名虽一致但离线玩家 getStatistic 也不读磁盘）

## 调试方法（本会话有效）

- **读 0 且原因不明时，在 getPlaytimeMinutes 加临时日志打印解析路径 + Files.exists()**——日志直接暴露真实路径（`world/dimensions/minecraft/overworld/...`）→ 才知道是维度目录问题
- 日志条件注意：只在 `ticks <= 0` 时打，避免刷屏；修完删日志
- **⚠️ 部署前确认 jar 产物名**：gradle shadowJar 产物名带版本号（`OrzMC-1.0.15-dev.jar` → bump 后变 `OrzMC-1.0.16-dev.jar`）——**一直拷贝旧文件名 = 部署旧 jar**，改代码毫无效果且无报错。构建后 `ls -la build/libs/*.jar` 看实际产物名+时间戳再部署

## 关联
- orzmc `references/permission-system.md`（user-owned：权限组设计与 LP 命令坑）
- minecraft-bot-mineflayer `scripts/perm-check.js`（LP 权限验证 bot）

## 9. 权限状态展示动态化 + LP track 数据卫生（2026-08-07 权限二期收尾实测）
> 来源：原 `references/permission-impl.md`（2026-11-10 并入本文件，内容未改写）

## 1. 四级流转状态矩阵（/rank 与 /apply 按当前组动态）

权限链 default→member→builder→admin 完整闭环：
- default→member：**自动晋升**（stats 时长达标，上线时 checkPromotion）
- member→builder：申请审核（BUILDER_PROMOTION，`/apply builder`）
- builder→admin：申请审核（ADMIN_PROMOTION，`/apply admin`——**2026-08-07 补全**，否则 builder 是死胡同）

| 当前组 | /rank 展示 | /apply 可申请 |
|:--|:--|:--|
| default | 时长 + 晋升成员阈值进度（还需 X / ✅已达标「下次上线将自动晋升为成员」） + 「下一步：在线时长达标后自动晋升为成员」 | 无 |
| member | 时长 + 阈值（✅已达标） + 「下一步可申请：晋升建造者（/apply builder）」 | 晋升建造者 |
| builder | 时长（**不再展示已完成的 member 阈值**） + 「下一步可申请：晋升管理员（/apply admin）」 | 晋升管理员 |
| admin | 时长 + 「已达最高等级（管理员）」 | 无 |

**设计原则**（用户两次纠正定案）：
- 已完成的事不再展示（builder/admin 不显示 member 阈值行）
- 展示与当前状态严格匹配：builder 玩家不得看到「申请 builder」、不得看到 member 时长条件
- 「下一步可申请」由 ReviewType 注册表**反向生成**（`isEligible` 过滤）——与审核类型天然同步，新增类型零展示层改动
- `/apply` 列表同样按 `isEligible` 过滤；空列表给通用文案「当前没有可申请的审核类型。」

实现位置：`RankCommandService.statusOf()` 的 switch 分支 + `ReviewCommandService.listTypes()` 的 filter。
分层注意：ReviewCommandService 在 review 框架包内，**不能依赖 RankService**（框架零宿主依赖）——引导文案放 /rank（有 RankService），/apply 只做资格过滤 + 通用空提示。

## 2. LP API 无 TrackNode——叠加组干扰判定（joker 实证）

**事实**（unzip LP api jar 实锤）：`net.luckperms.api.node.types` 只有 InheritanceNode/WeightNode/MetaNode 等，**没有 TrackNode**。track 组在用户身上就是**普通继承节点**（InheritanceNode），track 关系只存在于全局 `Track` 对象（组列表）。

**推论**：`currentTrackGroup` 按「`user.getInheritedGroups()` ∩ `track.getGroups()`」取最高位是官方标准做法，但**代码无法区分**「track 给的组」与「手动 `parent add` 叠加的同名组」。

**故障链（实测）**：joker 有叠加的 builder 组（`lp user joker parent info` 显示 `> builder` 无 track 标注）→ `$p d joker` 三次降级到 default（日志 demote SUCCESS）→ /rank 和 `$l` 仍显示「建造者」（继承组匹配把叠加组当 track 组）。

**唯一正解 = 数据清理 + 规范**（代码层面无解，别浪费时间找 API 区分）：
```bash
lp user X parent info        # 定位：看 parents 里无 track 标注的同名组
lp user X parent remove <组> # 清理叠加组
```
**规范**：权限组只经 `$p u/d`（track）升降级管理，禁止 `lp user X parent add` 叠加——叠加组是体系外数据，会造成权限实际状态与 /rank 显示脱节 + 双写漂移风险。

## 3. AMBIGUOUS_CALL 两个场景

LP promote/demote 返回 `AMBIGUOUS_CALL`（当前实现返回 null → 提示「已在最高/最低等级」，**误导**）：
1. **叠加组**：手动 parent add 的组与 track 组并存（旧场景）
2. **track 节点重叠**：同一玩家同时持有两个 track 组节点（如 builder+member 并存，测试数据脏）——2026-08-07 实测 TestMember

诊断：`lp user X parent info` 看 parents 列表；修复 = `parent remove` 多余节点（保留最高位组）。
日志特征：`[OrzMC.LP] demote(uuid) -> AMBIGUOUS_CALL`。

## 4. 帮助注册单一事实源（$h / $cmd ?）

- `helpInfo` 若手工 `+ OrzUserCmd.X.display()` 拼接 → 新增枚举项后 $h 不自动包含（本会话 $v/$p 漏注册）
- **正确**：帮助列表由枚举 `values()` 遍历生成，或至少补全拼接
- `usageTip` switch 漏 case → `$cmd ?` 静默降级为**直接执行**（`?` 当参数执行，无提示）——新增指令必须补 usageTip case
- 验收：`/orzdebug $h`、`/orzdebug $v ?`、`/orzdebug $p ?` 输出（群侧反馈在服务器日志 cmd debug 段）

## 5. 全面转向外部权威源后的一期残留清理模式

LP track 接管权限状态后，以下「本地兜底」应清理（用户要求「统一清理干净」）：
- **无 LP 时的本地推断**：`hasApprovedBuilder`（按审核记录推断组）→ 删除，无 LP 一律回退 default（访客）——虚假展示比不可用更糟；顺带解除 RankService 对 ReviewStore 的依赖
- **命令面分裂**：`/rank demote` 与群侧 `$p` 并存 → 统一 `$p`（群升降级）+ `/review`（游戏内审核）+ `/rank`（纯查询）
- **死占位符/死条目**：模板 fallback 里的 `{role_alias}`、占位符白名单里的 role_alias（配置已删但 fallback 没删，新装服务器原样输出）
- **过时注释**：描述一期结构（「三段式」「/rank [approve|reject]」）的注释同步更新

清理原则：权限状态判定 100% LP 单一事实源；「配置最少记录、可推导不落盘」。
