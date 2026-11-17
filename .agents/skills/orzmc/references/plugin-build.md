# 插件源码构建与开发（plugin-build）

> 合并自：minecraft-plugin-source-build + paper-plugin-development（2026-08-10 阶段一整合）
> 触发：需要从源码构建/修改插件 jar 并部署（自维护仓库、上游 bug 修复、PR 产物测试）。

## 构建工具选择（关键）

1. **确认构建工具**：`gradlew`（Gradle）/ `pom.xml`（Maven）
2. ⚠️ **两者并存时先看 git 近期提交**：项目可能从 Maven 迁移到 Gradle（如 LoginSecurity `migrate to papermc 26.2 and java 25` 只改 build.gradle.kts，pom.xml 是陈旧残留）。**陈旧 pom 编译必然失败**（`程序包 io.papermc.paper.event.player 不存在` 等 API 缺失 = 构建工具选错的信号，不是源码坏了）→ 改用 `./gradlew shadowJar`
3. **Maven 缺失**：清华镜像 `https://mirrors.tuna.tsinghua.edu.cn/apache/maven/maven-3/`（先查目录版本列表选存在的 3.9.x，如 3.9.16）

## 构建命令

- Gradle：`./gradlew shadowJar`（产物 `build/libs/`）
- Maven：`mvn clean package -Dmaven.test.skip=true`（**测试编译与 API 版本冲突时用 `-Dmaven.test.skip=true` 而非 `-DskipTests`**——后者仍编译测试代码）
- ⚠️ **产物名带版本号**（OrzMC-1.0.15-dev.jar → bump 后变 1.0.16-dev.jar）——部署前 `ls -la build/libs/*.jar` 确认**实际产物名+时间戳**再拷贝（一直拷贝旧文件名 = 部署旧 jar，无报错但改动无效，实测踩坑）
- Gradle toolchain 不匹配：build.gradle.kts 钉死版本（如 21）本机只有 JDK 25 → 改 toolchain 为 25（`options.release.set(17)` 保证字节码兼容）
- 部署确认 shaded 版（含依赖），否则运行时报 NoClassDefFoundError

## 部署（源码构建产物）

- **新装**：停服 → 删旧插件目录+旧 jar（不删目录则插件输出 "Skipping bundled default category files"，旧配置/语言不刷新）→ 放新 jar → 启动生成新配置 → 改配置 → 重启
- **升级（PaperMC update/ 机制）**：新 jar 放 `plugins/update/` → 重启自动替换（按插件名匹配）；**带版本号 jar 例外**：文件名不同 update/ 不生效 → 备份→删旧→新 jar 直放 plugins/

## 源码级修复工作流（paper-plugin-development 核心）

1. 查仓库：plugin.yml main 包名 → GitHub 搜；确认 MIT 协议 + 活跃
2. clone → 读源码定位（控制流图 `*.mmd`/`docs/` 往往直接暴露根因）
3. **先复现再修**：改代码前记录修复前基线，修复后同一条件验证消失
4. 编译 → 部署 → 回归验证（≥8 轮自动化，轮间 sleep 30 防登录冷却）
5. **提 PR 上游**：fork → fix 分支 → PR（描述含回归数据）→ 稳定后切 fork main 重提 → 关旧 PR 注明被取代
6. **发布流程（自家插件）**：feature/bugfix 走分支→PR→合入 main→**询问用户确认**→打 SemVer tag（不加 v）触发 Publish；误发版撤销 = `gh run cancel` + `git tag -d` + `git push origin :refs/tags/<ver>`。发布验证（1.0.17 实测）：① GitHub Release `gh release view <ver>`；② Hangar API `api/v1/projects/OrzMC/versions` 看 channel=Release；③ **Modrinth 用 `api/modrinth.com/v2/project/{id}/version` 查询可能 404/空（slug 解析不可靠）——以 publish.yml CI 日志 `Successfully uploaded version X to <id> as version ID <vid>` 为权威证据**；④ CI 会自动 bump paper-plugin.yml version（如 1.0.17→1.0.18）并直推 main，勿手动重复 bump

## 高频坑速查（详见各 references）

- **Paper 26.2 与 EssentialsX 2.22 不兼容**：unsupported server version + /spawn 未注册 + op 权限全拒；排查铁律：LP 权限即时生效 / Unknown=命令未注册≠权限问题 / 本地复现须同核心构建 / 优先回退核心到插件支持版
- **dispatchCommand 必须主线程**：异步线程调抛 `IllegalStateException: Asynchronous Command Dispatched Async`——runSync 回主线程
- **LP API 集成三连坑**（implementation→Provider 副本 NotLoadedException / compileOnly+旧 softdepend→ClassNotFoundException / `track.promote()` 必须 `saveUser().get()` 落库）→ references/permission-impl.md
- **LoginSecurity 拦截未登录玩家命令**（op 也不能免）：mineflayer 测试 spawn 后必须先 `/login <密码>`
- **mockStatic 泄漏**：每个测试 try-with-resources 包住
- **markAlwaysSave 配置停服后改**：运行中改会被关服保存的内存态覆盖
- **read_file 误判中文注释 .java 为 binary**：用 sed/grep 看
- **新增模板键 = 4 处注册清单 / 删除 = 8 处联动（见 references/review-framework.md）**
- **新增模板变量（非键）也要注册白名单**：`TemplatePlaceholderValidator.allowedVarsByTemplateKey()` 必须加新变量，否则 `ConfigHealthCheck`/`ConfigBackwardCompatTest` 挂（报「模板变量未知: templates.<key> {<var>}」）。实例：PR #171 加 `duration_human` 漏注册 → 2 个测试失败

## 支持文件（references/）

- `ezshops-maven-build.md`：EzShops 构建（jaker macOS 大小写坑）
- `loginsecurity-build.md`：LoginSecurity 构建（Gradle 非 Maven、26.2 迁移）+ AuthModeChangedEvent name-null 报错与 null 防御修复
- `deathchest-fix.md`：DeathChest 修复案例
- `permission-impl.md`：LP API 直调（类加载三连坑/saveUser/AMBIGUOUS_CALL）
- `permission-impl.md`：LP 晋升幂等（promoted 标记）
- `permission-impl.md`：权限状态动态化
- `review-framework.md`：通用审核框架 + 模板键注册
- `review-framework.md`：审核框架验收
- `testing.md`：RCON+orzdebug+Mineflayer 自动化测试
- `testing.md`：Bot 命令测试
- `orzmc-entity-teleport-tnt.md`：实体传送/TNT
- `permission-impl.md`：在线时长数据源（stats 文件）

## 脚本（scripts/）

- `rcon.py` / `rcon.js`：RCON 客户端（`$` 安全，node 原生实现）
- `check-death-chest.js`：死亡点箱子回归验证
- `regression-loop.sh`：多轮回归循环
- `stress-concurrent.js`：并发压测
- `fix_exaroton_cfg.py`：Exaroton 配置文件修复（JSON 包装）
- `templates/migrate_keys.py`：配置键迁移模板

---

# Paper 26.x 命令注册与 Tab 补全（Brigadier）（2026-09-12 由独立技能 paper-26-plugin-dev 合并入）

## When to Use
- Paper 26.x 服务器上插件命令**执行正常但 Tab 补全失效/显示错误内容**（多插件同名命令被抢占）
- 开发 Paper 26.x 插件需要注册命令（新命令或迁移旧式 Bukkit 命令）
- 排查插件命令的 Brigadier 注册/权限/补全问题

## 核心机制（2026-08-31 实测确认）

**Paper 26.2 插件模式忽略 YAML 命令声明**（OrzMC 主插件 paper-plugin.yml 注释原话）——命令必须通过 `LifecycleEvents.COMMANDS` + Brigadier 注册。

**执行与补全分离**：Bukkit 旧式命令（plugin.yml `commands:` + `TabExecutor`）：
- **执行**：仍走 Bukkit CommandMap（后注册覆盖，功能正常）
- **补全**：走 Brigadier 命令树 → **被原生 Brigadier 注册的同名命令抢占**（如 Essentials 2.22 用 1.21.4+ SyncCommands 注册 /home）

**典型症状**：`/home` 执行正常（走 GetMeHome），但 `/home ` Tab 补全显示别的插件内容（玩家名+冒号 `joker:` 前缀 = Essentials 风格）而非自己的家名列表。

## 正确注册方式（Paper 26.x）

```java
// onEnable 或 PluginBootstrap 里：
getLifecycleManager().registerEventHandler(LifecycleEvents.COMMANDS, event -> {
    Commands commands = event.registrar();
    commands.register(
        Commands.literal("home")
            .requires(src -> src.getSender().hasPermission("getmehome.command.home"))
            .executes(ctx -> { /* 无参逻辑 */ })
            .then(Commands.argument("home", StringArgumentType.greedyString())
                .suggests((ctx, b) -> { /* 参数补全 */ return b.buildFuture(); })
                .executes(ctx -> { /* 带参逻辑 */ }))
            .build(),
        "命令描述", List.of("别名")
    );
});
```

参考模板：`~/OrzMC/plugin/src/main/java/com/{SERVER_NAME}/paper/plugin/orzmc/assembly/FeatureCommandRegistrar.java`（OrzMC 主插件的全部 Brigadier 命令注册）。

## 构建配置（对齐 OrzMC 主插件）
- `gradle.properties`: `paper_api_version=26.2.build.119-stable`（26.2 稳定坐标；最新见 maven-metadata：repo.papermc.io，本地服务器 26.2-121 对应 `26.2.build.121-stable`）
- `plugin.yml` / `paper-plugin.yml`: `api-version: '26.2'`
- 构建：`JAVA_HOME=/Library/Java/JavaVirtualMachines/microsoft-25.jdk/Contents/Home ./gradlew shadowJar`

## 诊断步骤
1. **真客户端实测**（mineflayer 协议层不可靠时以真客户端为准）：补全内容判断来源 —— 玩家名`:`前缀=Essentials；自己家名=正常
2. 查看是否有原生 Brigadier 竞争者：Essentials 2.22 日志 `Selected 1.21.4+ Sync Commands Provider` = Brigadier 注册
3. 临时验证 workaround：竞争者插件的 `disabled-commands`（Essentials config.yml）禁掉同名命令 → 补全恢复即证实抢占（**不治本**，正解是 Brigadier 注册）
4. 服务器侧配置检查：spigot.yml `tab-complete: 0`（0=全量，勿设其他值）

## 临时 workaround（配置层，已验证有效）
Essentials `config.yml`：
```yaml
disabled-commands:
  - home
  - homes
  - sethome
  - delhome
```
`/ess reload` 热生效。适用于不想改源码的快速止血，但插件重启/重装后仍依赖该配置，正解是插件侧 Brigadier 注册。

## 迁移陷阱（Bukkit 命令 → Brigadier 自查清单，2026-08-31 GetMeHome PR #7 实测）

1. **幽灵命令（最隐蔽）**：保留 plugin.yml `commands:` 声明 + 改用 Brigadier 注册 + 删掉 setExecutor → Bukkit CommandMap 仍注册该命令但无 executor → 执行返回 false → **打印 plugin.yml 的 `usage:` 字符串**（如 `/home [home name]`、`/listhomes`）。症状像「命令被别的插件抢了」，实测中先怀疑 Essentials，最后定位是自家 plugin.yml 的 usage 字段。**正解：删掉 plugin.yml 整个 commands 段**（permissions 段保留）—— Paper 26.x 模式本就忽略 YAML 命令声明，残留声明只会制造幽灵命令。诊断锚点：命令响应文本与 plugin.yml usage 字段逐字一致 = 幽灵命令。
2. **每个参数节点都要 suggests**：旧 TabExecutor 的 onTabComplete 对每个 args 长度分支都有补全 → Brigadier 每个 argument 节点都要配 `.suggests()`，漏一个就是静默补全回归（实例：setdefaulthome 漏 suggests，`/setdefaulthome <Tab>` 空白）。
3. **参数类型 word() vs string() vs greedyString()**：`word()`/`string()` 的 unquoted 字符集**不含中文和 `:`**（只允许 `[0-9A-Za-z._+-/<>^=]`）——`/sethome 验收点`、`/home 测试:家` 报「Expected whitespace to end one argument, but found trailing data」（原版 Bukkit 按空格 split 中文家名完全可用 = 行为回归）→ **家名/自由文本参数一律用 `greedyString()`**（读所有非空格字符，空格天然分隔参数，1 参/2 参形式均正常）；greedy 模式下**补全建议绝不能加引号**（引号会被吞进参数值）。纯玩家名参数才可用 word()。
4. **控制台 sender 崩溃**：args>=2 + `.other` 权限时控制台执行 `/home <player> <home>` → `home((Player) sender)` 转型 ClassCastException（存量 bug 被 Brigadier 暴露）。home/sethome 分支前显式 `!(sender instanceof Player) → consoleCommand(...); return true;`（delhome/setdefaulthome 无转型不需）。
5. **`.requires()` 的语义**：无权限玩家看到 "Unknown or incomplete command" 而非明确拒绝 —— 是有意的安全实践（隐藏命令存在性），Paper 26.x 原生行为。接受即可，在类 Javadoc 注明，别试图加兜底 executor。
6. **别名注册**：`Commands.register(builder, desc, List.of("h"))` 复制完整子树（含 suggests/requires），测试须覆盖别名路径（/h、/homes）。
7. **短旗标一致性**：补全判断只认 `-global` 不认 `-g`（旧版也如此）→ 迁移时顺手统一。
8. **Paper-only 声明**：Brigadier 注册硬依赖 `io.papermc.paper.*`，非 Paper 服务器 NoClassDefFoundError 整个插件禁用 —— CLAUDE.md / plugin.yml 注释明示 Paper 26.2+ only。

## deprecation 警告清理（Paper 26.x 构建 0 警告，2026-08-31 GetMeHome PR #7 实测）

paper-api 26.x 构建/CI 常见 deprecation 警告及**零行为变化**清理法：

- **`org.bukkit.ChatColor` 整个类 deprecated** → 清全部引用：`ChatColor.RED` → `"§c"`、`ChatColor.BOLD` → `"§l"`、`ChatColor.ITALIC` / `ChatColor.ITALIC.toString()` → `"§o"`、`ChatColor.RESET` → `"§r"`；config 颜色字符 → `"§" + ch`（替代 `ChatColor.getByChar`）；`ChatColor.translateAlternateColorCodes('&', s)` → `s.replace('&', '§')`；持有颜色的 getter/字段 `ChatColor` → `String`
- **关键判断：`sendMessage(String)` 在 paper-api 26.2 未 deprecated**（构建警告只有 ChatColor 类、零 sendMessage 警告可证）→ 清 ChatColor 警告**不需要**全量 Adventure 迁移，§ 码字符串方案即可；若见 sendMessage 警告再上 `TempUtils.legacyString2Component` / `sendMessage(Component)`
- **Guava `Charsets.UTF_8` deprecated** → `java.nio.charset.StandardCharsets.UTF_8`（import 与用法同步换，`new OutputStreamWriter(fos, ...)` 两处）
- **CI 警告核对**：`gh run view <run-id> --log | grep -iE "warning:|deprecat"`（`##[warning]` 前缀行）；Gradle 输出里 "Important project hierarchy lookup deprecations" 只是 **release notes 文本**不是警告，勿误判
- 老板视角：MR 的 CI 警告会逐个被点名要求清理 —— 本地构建先 `grep -cE "warning:.*deprecat"` 清零再推，别等 CI 跑完才发现

## Pitfalls
- **Bukkit 命令声明（plugin.yml commands）在 Paper 26.2 上补全不保证生效** —— 迁移到 Brigadier 是唯一稳定路径；且残留声明=幽灵命令（见上清单 #1）
- 权限：Brigadier 用 `.requires(src -> src.getSender().hasPermission(...))`；控制台 sender 判断用 `src.getSender() instanceof Player`（Brigadier 的 sender 是 `CommandSourceStack#getSender()`）
- 别名用 `List.of("h")` 传入 register 的第 3 参
- 复用旧 TabExecutor 业务逻辑时：Brigadier 执行体里构造 args 数组调旧 onCommand，或做最小适配层 —— 不要重写业务
- 改完部署验证要跑**行为回归**（/home /homes /sethome /delhome 全链路）+ **补全协议测试**双覆盖，只测补全会漏执行层回归（如幽灵命令）

## 支持文件（新增）

- `references/papermc-tabcomplete-testing.md` — mineflayer 协议层验证 Tab 补全（包格式 `{transactionId,text}`、协议须 1.21.10=776、脚本 `~/minecraft-bot/tab-single.js`）
