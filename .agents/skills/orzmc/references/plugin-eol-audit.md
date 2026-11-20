# 插件维护状态调研（一堆 jar → 能否检索 / 是否持续维护 / 功能与迁移建议）

> 触发：老板丢来一个 `plugins/` 打包（几十个 jar）要「看看这些插件还能不能维护、是不是该换」。
> 与 `plugin-inventory.md`（本服插件的指令/权限清单）、`version-check-pitfalls.md`（本服插件查最新版的坑）分工：本文管**外部插件的生态存活判定**，不碰本地部署细节。

## 0. 交付形状（老板的固定要求）

- **主交付 = 一张表格文件**（xlsx 优先），列固定为：插件名 / 包内版本 / 启用状态 / 平台可检索性 / 上游最新版与日期 / 维护状态 / 版本落后 / 核心功能 / 建议。冻结首行、按状态上色（活跃=绿、停滞=琥珀、弃用/查不到=红）。
- **聊天里再给三层结论**，不要只丢文件：① 分档计数表（活跃 / 发版停滞 / 半停更 / 弃用 / 平台查不到）；② 「最该注意的 3 件事」（落后最多的几个、被禁用的功能件、需要成组升级的依赖链）；③ 逐条可执行建议。
- 用 `MEDIA:<绝对路径>` 把文件发出去，不能只在文字里描述表格内容（老板明确要过：生成的产物必须发文件）。
- 表里给的是「上游最新版 vs 包内版本」，不要用「该升级了」这种无信息量的话——写清楚版本号跨度。

## 1. 先读包内真值，别靠文件名

解压用户上传的压缩包用 `execute_code` + `zipfile`（`extractall` 到 scratch 目录），**不要**在终端拼 `rm -rf <dir> && mkdir && cd && unzip` 这种破坏性组合——它会命中审批门，而解压本身根本不需要删目录。

每个 jar 的元数据按优先级读：`plugin.yml` → `paper-plugin.yml` → `velocity-plugin.json` / `bungee.yml`。取 name / version / main / authors / description / website，写成 `plugins_meta.json` 再做后续查询。

- **jar 里的 `name` 才是检索主键**，文件名常带中文前缀或渠道前缀（`[跨服传送]Stp.jar`、`[bukkit_spigot_paper]AllMusic_Server-3.3.3-all.jar.disabled`），按文件名搜必然搜不到。
- **`.jar.disabled` / `.disable` 同样是插件**，要统计「启用状态」列——被禁用的往往是重要功能件（查熊、自定义物品、登录），值得单独提醒老板确认是不是刻意关的。
- **平台无页时读 `META-INF/MANIFEST.MF` 的 `Built-By` 与顶层 package 前缀**判断来源：前缀像个人命名空间、顶层只有几个 class = 自研/小圈子构建；有 `org.bukkit` 之外的大包名可反查作者。这一步能把「查不到」从「我搜错了」降级成「确实没有公开页」。

## 2. 三源交叉检索（缺一即误判）

| 源 | 调用 | 取什么 |
|:--|:--|:--|
| Modrinth | `GET https://api.modrinth.com/v2/search?query=<name>&limit=6&facets=[["project_type:plugin"]]`；命中后 `GET /v2/project/<slug>` + `/v2/project/<slug>/version?limit=5` | `date_published` 最新一条、`downloads`、`game_versions` |
| Hangar | `GET https://hangar.papermc.io/api/v1/projects/<owner>/<slug>`（**必须 owner/slug 两段**） | `lastUpdated`、`createdAt`、`stats.downloads` |
| GitHub | `gh api repos/<owner>/<repo>`、`gh api repos/<owner>/<repo>/releases?per_page=5`、`gh api search/repositories?q=<name>` | `pushed_at`、`archived`、`stargazers_count`、最新 release `published_at` |
| SpigotMC | 网页检索 `<name> spigotmc resource` | 资源页编号、最后更新时间、CurseForge 的 UNMAINTAINED 标记 |

判定规则（写成一句就能复用的口径）：

- **多源不一致时以「最近一次真实发版」为准，不以某一页为准**。Spigot 原版停更 ≠ 插件已死——常见形态是原作者归档、第三方在本仓库/fork 继续维护；反之只在 Spigot 发版的插件 GitHub 上是空的。两个方向都要看，只看一页就会把活跃插件判成弃用或反之。
- **`archived=true` 是硬信号**，直接判弃用；`pushed_at` 新但有两年没发 release → 判「发版停滞」而非「可升级」，不要把 commit 当成可用的构建。
- **slug ≠ plugin.yml 的 name**：系列插件按系列名检索（Vane 系列拆成多个仓）、有的在 Hangar 只有 `owner/slug` 形式、有的名字带 `++`。一次检索无果要换作者名/关键词再搜一轮，再判「平台查不到」。
- **平台查不到（Modrinth + Hangar + Spigot + GitHub 全无）= 自研/小圈子插件**，结论写「按自研对待，升级/排障只能看 jar 本身，无上游可依赖」，不要硬给一个升级建议。
- **仅有个位数 ★ 的个人仓库**也算「半停更」档：存在但随时可能断，建议锁定版本、不追新。

## 3. 依赖链必须成组看

单插件视角会给出错误建议。调研时显式记下这几类关系，写进结论：

- **同版本四件套**（Vane 系列）：必须同版本升，单独升一件会因内部 API 变更崩。
- **硬依赖库**（ItemsAdder → LoneLibs）：库本身停更/标 OUTDATED 不代表要换掉，它是跟着宿主插件走的，只有在宿主插件也停更时才成问题。
- **底层被依赖项**（ProtocolLib、PlaceholderAPI）：几乎所有服都装，升级影响面最大——说清楚「它只是分发依赖，不用频繁追新」。
- **SNAPSHOT/dev 构建**：与「只跟 release 正式版」的版本纪律冲突时按纪律判，写「包内是 dev 构建，应回退正式版」而不是「已是最新」。

## 4. 判档口径（写进结论的三~五档）

| 档位 | 判定 | 建议口径 |
|:--|:--|:--|
| 活跃维护 | 近 6 个月内有 release | 可跟最新正式版 |
| 发版停滞 | 有提交/有历史但 >6 个月无 release | 保持现值，别追 |
| 半停更（个人小插件） | 只有个人仓库、零星更新 | 锁版本，做好自备 fork 的准备 |
| 弃用 | archived / 原作者明确停更 / >2 年无动静 | 给迁移目标（如菜单类 → DeluxeMenus），不要「找 fork 凑合」 |
| 平台查不到 | 四源皆无 | 按自研插件对待 |

「版本落后」列单独算：**上游最新正式版 vs 包内版本**，落后就写跨度（`1.4.28 → 1.5.66`），不要只写 ✅/❌。

## 5. 生成 xlsx（当前解释器无 xlsx 库时的零依赖做法）

先 `import openpyxl` 试一次；不可用时用 `zipfile` 手写最小 OOXML，够用且可控：

- 必需成员：`[Content_Types].xml`、`_rels/.rels`、`xl/workbook.xml`、`xl/_rels/workbook.xml.rels`、`xl/worksheets/sheet1.xml`、`xl/styles.xml`。
- 单元格用 **inline string**（`<c r="A1" t="inlineStr" s="1"><is><t>…</t></is></c>`），免掉 `sharedStrings.xml` 这一整套。
- 冻结首行 = `<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews>`。
- 列宽 = `<cols><col min="1" max="1" width="22" customWidth="1"/>…</cols>`；自动换行/状态色靠 `styles.xml` 的 `cellXfs`（0=普通 1=表头 2=换行 3=绿 4=琥珀 5=红），把 `s=<id>` 挂到 `<c>` 上。
- 生成后必须**回读校验**（`read_file` 能读出内容 / `zipfile` 能列出全部成员），再交给老板。
- **回读既有 xlsx 也一样零依赖**：`zipfile` 读 `xl/sharedStrings.xml`（`<si>` 抽成字符串数组）+ 各 `xl/worksheets/sheetN.xml`（`<row>`→`<c t="s">` 的 `<v>` 是 sharedStrings 下标，`t="inlineStr"` 取 `<is><t>`）即可还原成二维表；不要因为 `import openpyxl` 失败就改用 `read_file` 硬看（宽表会截断、看不出列归属）。

## 6. 数据落盘约定

中间产物留在 scratch 目录，别写进技能目录：`plugins_meta.json`（jar 元数据）、`plugins_lookup.json`（各平台原始命中）、`plugin_table.json`（`hdr` + `rows`，表格的唯一数据源）。**先攒 JSON 再一次性生成表格**，这样中途超时也不会丢已查完的结果。

## 7. 第二问：这些插件能不能加进现有服（功能 + 冲突评估）

同一批 jar 往往紧接着被问「都有什么功能、和现有插件冲突吗、哪些能加」。这是**相对现有环境**的判定，与 §1–§4 的「插件自身是否健康」完全不同的轴——上游再活跃，与现装体系撞车也是不可加。

**先取现有环境真值（不看这一步的评估全是空谈）**：

- 每个后端实例的 `InstanceData/<uuid>/plugins/` 命名空间（本机 MCSM 栈 = `E:/orzmc/mcsmanager/daemon/data/InstanceData/<uuid>/`，Paper 与 Folia 各一套），再读 `server.properties` / `start.sh` 确认核心与端口。
- **代理层 `eagler/proxy/plugins/`**（容器 `orzmc-velocity`，挂载 `-> /srv`）——登录/转发/基岩相关插件的冲突常常只在代理侧暴露。
- 自研插件（`OrzMC-*.jar`）用 `zipfile` 枚举 `plugin.yml`/`paper-plugin.yml` + class 包前缀，反推它已覆盖的命令面（`unzip -p x.jar plugin.yml` 对该 jar 可能空输出，别据此判「没有元数据」）。

**冲突判定三轴**（三轴任一命中就不叫「可加」，最多「需测试」）：

| 轴 | 具体查什么 | 命中后的处置 |
|:--|:--|:--|
| 命令命名空间 | 与 EssentialsX/GP/WE/WG/自研已注册命令 + 别名的交集 | 关掉对应子模块（`essentials.invsee`）或改别名，否则玩家看到的是随机赢家 |
| 存储与数据格式 | 同一功能是否各有自己的 yml/db（家/传送点/经济/白名单） | 两套数据并存迟早分裂；判「重复且包内版本更旧」直接否 |
| 玩法规则改写 | 是否改掉落/物品行为/出生点/登录流程等核心语义 | 会悄悄改行为的框架类插件默认否（收益分散、排查成本高） |

**兼容性三条硬门槛**（任一不过就是「不可加」，不用再谈功能）：

1. **MC 版本**：Modrinth 的 `game_versions` 必须含实际核心版本（本服 26.3），只有 1.21.x 的老构建不算「能跑」。
2. **Folia**：`loaders` 含 `folia` 才算支持；Hangar 的 `supportedPlatforms` 只标 PAPER 不可信（只能上 Paper 实例的就明确写「仅 Paper」）。
3. **三端入口（本服特有、最容易漏）**：测试服是 Java + 基岩(Geyser) + 网页(Eaglercraft) 三端入口，**需要客户端资源包或客户端 mod 的插件（ItemsAdder / AllMusic / voicechat 类）等于把基岩与网页玩家排除在外** → 判「不可加」，理由写成「三端入口不兼容」而不是「功能不好」。

**底层库只留一个**：`packetevents` 与 `ProtocolLib` 这类 netty/协议注入库同装会互相踩（GrimAC 依赖 packetevents）→ 已有则否掉另一个，不要「先装上试试」。

**结论只用三档**：`可加` / `需测试` / `不可加`，每档都要带前置动作（「先关 essentials.invsee」「拉上游 2.8.0 重测再上」「仅 Paper 实例」）。没有前置动作的「可加」在老板眼里等于没说。

**交付形状**：在主表之外加**第二张 sheet = 三端现有插件清单**（供对照），聊天里给三档计数 + 三张短表（可加/需测试/不可加的原因归类：重复且更旧、命令撞车、三端不兼容、版本/Folia 不支持），再单列「顺手发现的现有配置问题」（例：同一实例同时装了 AuthMe 与 SimpleLogin，两者抢 PlayerLoginEvent）。xlsx 生成沿用 §5 的零依赖写法。

**边界纪律**：老板说「先只做评估」= 不写任何 `plugins/`、不改配置、不重启实例、不装依赖；结尾必须显式确认「未改动任何文件与服务」，并给出「要动手先上哪个」的下一问。

## 8. 第三问：包里哪些**实际在用**、哪些没用（采用情况核对）

事后老板会回头问「之前 zip 包里的插件实际使用是哪些」。这是一次**事实核对**，不是再调研一次——不要重新搜上游、不要再造一份评估表，直接拿三层现成证据对账：

1. **包内清单**：`scratch/plugins_meta.json`（§1 解的 jar 元数据，`name`/`version`/`file` 三列就够）。它还在 scratch 就用它，比重解压快。
2. **实装清单**：每台实例的 `InstanceData/<uuid>/plugins/`，取文件名 + 版本 + **mtime**。同一批时间戳（如全部 11-19 11:14）的那几个就是这批新装的，其余是历史存量——这是判「本批采用了哪些」最快的锚点。
3. **加载确认**（必做）：`logs/latest.log` 里 grep `Loading server plugin <Name>` / `Enabling <Name>`。装了但没 Enabling = 加载失败或没重启，不能算「在用」。

**关键区分（答错会直接被识破）**：

- 「**用了这个插件**」≠「**用了包里这个 jar**」。Chunky / DecentHolograms / ToolStats / PlaceholderAPI 是采用了，但装的是**最新版**而非包内旧版（`1.4.28 → 1.5.66` 这类），必须写成两列。
- 包内版本更旧且**已装更新版**的（LuckPerms / SkinsRestorer / ViaVersion 三件套 / voicechat）单独归为「已在用，但不换包内版本」，不要混进「未采用」——否则数字对不上、结论失真。
- 一律核对总数：`采用 + 已用不换 + 未采用 = 包内插件数`，三个数加起来对不上就是漏了（含 `.disabled` 也算一个）。

**未采用的归因分桶**（每桶一条原因，比 23 条流水账好读）：

| 桶 | 典型成员 | 原因写法 |
|:--|:--|:--|
| 功能重叠/命令撞车 | HuskHomes、InvSee++、MiniMOTD、OriginXWhitelist、ProtocolLib、Stp、ChestCommands | 点明撞哪个命令/哪个配置项已在管（`MOTD 在 velocity.toml`、`packetevents 已在`） |
| 三端入口不兼容 | ItemsAdder、LoneLibs、AllMusic3 | 资源包/客户端 mod 依赖 → 基岩与网页端注定看不到 |
| 版本或维护已死 | dynmap、AdvancedPortals、HideMyArmors | 写明卡在哪个 MC 版本 / 无 Folia / 作者停更 |
| 改写玩法语义 | PeacefulMode、LetMeDespawn | 动刷怪/掉落/实体消失，出问题极难归因 |
| 替换或唯一性冲突 | FAWE、LibreLogin | 装上等于接管 WE；登录插件只能有一个 |
| 成套框架 | Vane core/admin/enchantments/trifles | 一条共同原因：不支持 Folia + 与 Essentials/SCore 重叠，别拆成四条重复理由 |

**收尾必须点出唯一的「待定项」**：评估里被判「需测试」的那一两个（通常是查熊类 CoreProtect）不属于「不要」，而是「还没测」。明确说清它的价值与卡点，并把「要不要现在实测」作为下一问抛给老板——不要让它悄悄沉进 23 条里。

**汇报形状**：一张总览（`N 个 → 采用 X / 已用不换 Y / 未采用 Z`）＋ 分桶表格（插件、包内版本→实装版本、原因）＋ 一段待定项建议。日志证据用行内引用（`[Chunky] Enabling Chunky v1.5.66`），不要贴整段日志。
