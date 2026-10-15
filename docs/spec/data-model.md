# 数据模型（Core Data Model）

> **状态**：草案 `specVersion 0.1` ｜ **最后更新**：2026-10-15
> 语言无关的数据形状定义；末节给出 Python ↔ Swift 字段对照。
> 未定项以 **【待定】** 标注。

---

## 0. 通用约定（Conventions）

| 约定 | 规范取值 |
|:--|:--|
| **路径分隔** | 逻辑路径用 `/`；各实现按平台转换 |
| **哈希** | 完整性默认 SHA-1（Mojang 等上游口径）；字段显式携带 `hashType` |
| **OS 枚举** | `windows` / `linux` / `osx` |
| **Arch 枚举** | `x86` / `x86_64` / `arm64` |
| **版本通道** | `release` / `snapshot`（非 release 一律归 `snapshot`） |
| **内存单位** | 字符串如 `512M` / `2G`（与 JVM 参数一致） |
| **时间** | ISO-8601 字符串 |

---

## 1. `RootLayout`（根目录布局）

**这是两边差异最大的实体。** 规范选定**唯一布局**（沿用 Python 现行布局），Swift 侧需对齐。

```
<root>/                                   # 默认 ~/minecraft
  versions/<mc_version>/
    client/    assets/ libraries/ natives/ profiles/ <version>.jar  launcher_profiles.json
    server/<server_type>/   <core>.jar  eula.txt  server.properties  plugins/  world/
  java/<java_major>/                       # 托管 JRE/JDK
  cache/  backup/worlds/  backup/music/<version>/
```

| 字段（方法） | 规范值 |
|:--|:--|
| `root` | 默认 `~/minecraft`，可配置 |
| `versionsDir` | `<root>/versions` |
| `versionDir(v)` | `<root>/versions/<v>` |
| `clientDir(v)` | `<versionDir>/client` |
| `clientAssetsDir(v)` | `<clientDir>/assets` |
| `clientIndexesDir(v)` | `<clientAssetsDir>/indexes` |
| `clientObjectsDir(v)` | `<clientAssetsDir>/objects` |
| `clientObjectPath(v, sha1)` | `<objectsDir>/<sha1[0:2]>/<sha1>` |
| `clientLibrariesDir(v)` | `<clientDir>/libraries` |
| `clientNativesDir(v)` | `<clientDir>/natives` |
| `clientJarPath(v)` | `<clientDir>/<v>.jar` |
| `clientProfilesDir(v)` | `<clientDir>/profiles` |
| `serverDir(v, type)` | `<versionDir>/server/<type>` |
| `serverJarPath(v, type)` | 见 `GameType.serverJarName` |
| `serverEulaPath` | `<serverDir>/eula.txt` |
| `serverPropertiesPath` | `<serverDir>/server.properties` |
| `serverPluginsDir` | `<serverDir>/plugins` |
| `serverWorldDir` | `<serverDir>/world` |
| `javaDir` | `<root>/java` |
| `javaMajorDir(major)` | `<javaDir>/<major>` |
| `javaExecutable(major)` | `<javaMajorDir>/bin/java[.exe]` |
| `cacheDir` | `<root>/cache` |
| `versionManifestPath` | `<cacheDir>/version_manifest.json` |
| `versionJsonsDir` | `<cacheDir>/versions` |
| `downloadTmpDir` | `<cacheDir>/download_tmp` |
| `backupDir` | `<root>/backup` |

**对照**

| 规范 | Python（`domain/paths.py`） | Swift（`Game/GameDir.swift`） |
|:--|:--|:--|
| `versions/<v>/client` | ✅ 现行为准 | ⚠️ 现为 `manifest/<v>/client/<type>`，需对齐 |
| `java/<major>` | ✅ | ⚠️ 无托管 Java 路径 |

> **布局对齐策略（已决）**：**不做迁移**。先把 Swift 一次性对齐到规范布局，此后一律按规范执行；
> 检测到旧布局（`manifest/<v>/`）时**提示用户删除旧目录重建**，不自动搬迁。

---

## 2. `VersionManifest` / `VersionEntry`

| 实体 | 字段 | 说明 |
|:--|:--|:--|
| `VersionManifest` | `latest: {release, snapshot}`、`versions: VersionEntry[]` | Mojang `version_manifest_v2.json` |
| `VersionEntry` | `id`、`type`、`url`、`time`、`releaseTime`、`sha1`（可选）、`complianceLevel`（可选） | `channel = release if type==release else snapshot` |

**对照**：Python `core/mojang.py` / `services/versions.py` ↔ Swift `MojangAPI`（`Version`）。

---

## 3. `GameType`（核心/装载器类型）

| 值 | 客户端 | 服务端 |
|:--|:--|:--|
| `vanilla` | ✅ | ✅ |
| `fabric` | ✅ | ✅ |
| `forge` | ✅ | ✅ |
| `paper` | ❌ | ✅（vanilla 客户端可连） |

| 字段/方法 | 规范值 |
|:--|:--|
| `isClientCapable` | `vanilla/fabric/forge` |
| `isServerCapable` | 全部 |
| `serverJarName(version)` | `paper-<v>.jar` / `forge-<v>.jar` / `fabric-server-launch.jar` / `server.jar` |

**对照**：Python `domain/types.py::GameType`（四值齐全）↔ Swift `Game/GameDir.swift::GameType`（仅 `vanilla/paper`，Fabric 在独立 `Fabric` 库）。
**规范要求**：实现须声明**能力矩阵**，不支持的类型显式返回"不支持"（而非静默失败）。

---

## 4. `JavaRequirement`

| 字段 | 说明 |
|:--|:--|
| `majorVersion` | 读自 version JSON `javaVersion.majorVersion`，缺失默认 `8`；**不得按 MC 版本硬编码** |
| `distribution` | 【待定】默认 `temurin` |
| `runtimeKind` | JRE（满足所有类型） |

**对照**：Python `domain/java.py` + `services/java.py`（下载托管）↔ Swift `OrzMCLauncher.JavaRuntimePolicy`（只判断，不托管）。

---

## 5. `ArtifactRef` / `DownloadItem`（下载项）

| 字段 | 说明 |
|:--|:--|
| `url` | 源地址 |
| `dest` | 目标路径（相对 `RootLayout` 的逻辑路径） |
| `size` | 字节数（若上游提供） |
| `hash`、`hashType` | 默认 SHA-1 |
| `executable` | 是否置可执行位 |
| `kind` | `version_json` / `client_jar` / `library` / `asset_index` / `asset_object` / `log_config` / `server_core` / `java_runtime` / `profile` |

**行为**（详见后续 `behavior.md`）：SHA-1 校验；失败拒绝写入；大文件可 `Range` 分块。

**对照**：Python 下载项在 `core/*` provider 内生成（`services/downloader.py` 执行）↔ Swift `Game/Client+Download.generateDownloadItemInfos()` 返回 `DownloadItemInfo`。

> **【待定】** 规范是否要求实现暴露"纯计划"API（不执行下载即可产出 `DownloadItem[]`）——建议要求，便于一致性校验。

---

## 6. `LibraryRule`（Mojang 库解析规则）

| 字段 | 说明 |
|:--|:--|
| `name` | Maven 坐标 |
| `downloads` | `artifact` / `classifiers`（含 `natives`） |
| `rules` | `{action: allow\|disallow, os{name,version,arch?}, features?}` |
| `natives` | 平台→classifier 映射（如 `osx → natives-osx`） |
| `extract` | 是否解压 natives |

**对照**：Python `domain/libraries.py`（`os_key/os_arch/rules_allow`）↔ Swift `Client+Boot` 内内联处理 + `MojangAPI` 模型。

---

## 7. `ProgressEvent`（进度）

| 字段 | 说明 |
|:--|:--|
| `kind` | `count`（文件计数）或 `bytes`（字节） |
| `description` | 任务描述 |
| `total` | 总数；`count` 可为 `null`（不定长） |
| `current` | 当前值 |
| `phase` | 阶段名（六阶段之一） |

**规范要求**：`count` 与 `bytes` 必须区分（速度列对两者语义不同）。

**对照**：Python `ProgressSink.start / start_bytes` ↔ Swift `progressHandler: (Double) -> Void`（需扩展为结构化事件）。

---

## 8. `ClientLaunchPlan`（客户端启动计划）

| 字段 | 说明 |
|:--|:--|
| `executable` | `RootLayout.javaExecutable(major)` |
| `cwd` | `clientDir(v)` |
| `jvmArgs` | 来自 version JSON `arguments.jvm`（含规则过滤） |
| `gameArgs` | 来自 `arguments.game` |
| `mainClass` | 默认 `net.minecraft.client.main.Main` |
| `memory` | `{min, max}` |
| `classpath` | 库 + 客户端 jar + loader 附加库 |
| `tokens` | `natives_directory` / `assets_root` / `assets_index_name` / `auth_player_name` / `version_name` / `game_directory` / `launcher_name` / `launcher_version` / `version_type` / `auth_uuid` / `auth_access_token` / `user_type` / `clientid` / `auth_xuid` / `path`(log config) |
| `features` | `is_demo_user` / `has_custom_resolution` / `quick_play_*`（规则开关） |

**认证 token 语义**（正版授权见 [`auth.md`](auth.md)；离线/已认证两态）：

| token | 离线（默认） | 已认证（`--auth`） |
|:--|:--|:--|
| `auth_uuid` | 随机/占位 UUID（实现保证非空合法） | 档案 `uuid`，**带连字符**的规范形式 |
| `auth_access_token` | `"0"` | MC `accessToken` |
| `auth_player_name` | `guest` / `-u` | 档案 `name` |
| `user_type` | `legacy` | `msa` |
| `auth_xuid` | `""` | 当前留空（保留） |
| `clientid` | `""` | `""`（保留） |

**对照**：Python `domain/launch.py`（`jvm_args` / `game_args` / `memory_args`）↔ Swift `Client+Boot.parseBootArgs()`（内联 tokens）。

---

## 9. `ServerDeployPlan`（服务端部署计划）

| 字段 | 说明 |
|:--|:--|
| `version`、`type` | 目标版本与核心类型 |
| `coreArtifact` | `DownloadItem`（vanilla `server.jar` / paper build / fabric launcher / forge installer） |
| `eula` | 是否写入并接受 EULA（`eula=true`） |
| `properties` | 【待定】`server.properties` 默认键值集 |
| `workdir` | `serverDir(v, type)` |
| `loaderInstall` | Forge：运行官方安装器 `--installServer`；Fabric：生成 launcher jar |

**对照**：Python `core/server/*` + `services/server.py` ↔ Swift `Game/Server/Deploy/{Vanilla,Paper}.swift`。

---

## 10. `ServerLaunchPlan`（服务端启动计划）

| 字段 | 说明 |
|:--|:--|
| `executable` | Java |
| `cwd` | `serverDir` |
| `jvmArgs` | `-Xms/-Xmx` + 用户 `jvmArgs` |
| `jarPath` | 核心 jar |
| `serverArgs` | `--nogui` / `--forceUpgrade` / `--demo` / `--pidFile` / 用户 `jarOptions` |

**对照**：Python `services/server.py::_build_server_command` ↔ Swift `Server+Launch.launchServer()`。

---

## 11. `CachePolicy`（缓存与刷新）

| 字段 | 规范值 |
|:--|:--|
| `ttlSeconds` | 默认 `86400`（24h） |
| `refresh` | 绕过所有缓存读 |
| `fallbackToStale` | 拉取失败时回退磁盘旧副本并 warn |
| `futureSkewSeconds` | `300`（容忍小幅未来时间戳） |
| 缓存对象 | version manifest / version JSON / fabric-meta / paper / forge promotions |

**对照**：Python `infra/cache.py::MetadataCache`（完整）↔ Swift 无统一缓存层（需补齐）。

---

## 12. 产品面与安装（Surface / InstallRecord）

> 支撑"CLI 与 GUI 互相安装/打开"（架构 §1.2）。

| 实体 | 字段 | 说明 |
|:--|:--|:--|
| `Surface` | `cli` / `gui` | 产品面 |
| `InstallRecord` | `tool`、`schemaVersion`、`platform`、`installDir`、`binary`、`surface`、`source`、`pathFile`、`pathLine`、`rootDir` | 安装记录；与 Python 现有 `install.conf`（key=value）对齐 |
| `CrossSurfaceAction` | `install` / `open` / `uninstall` | CLI↔GUI 互操作动作 |

**契约要点（【待定】细化）**：
- CLI → GUI：`orzmc app install`（下载并安装图形应用）、`orzmc app open`。
- GUI → CLI：GUI 提供"安装命令行工具"入口，把 `orzmc` 写入 PATH 并写 `InstallRecord`。
- 卸载只删除自己登记过的内容（沿用 Python `self-uninstall` 的安全护栏）。

**对照**：Python `services/selfinstall.py`（`InstallManifest`）+ `selfupdate.py`；Swift `OrzAppUpdater` + App 安装器。

---

## 13. 字段对照总表（Phase 1 验收项）

> 目标：两边公共字段都能**无损映射**到本模型。✅=已有对应；⚠️=命名/结构不同需适配；❌=缺失需补。

| 规范实体 | Python | Swift | 状态 |
|:--|:--|:--|:--:|
| `RootLayout` | `domain/paths.py::PathLayout` | `Game/GameDir.swift` | ⚠️ 布局不同 |
| `VersionManifest/Entry` | `core/mojang.py`、`services/versions.py` | `MojangAPI` | ✅ |
| `GameType` | `domain/types.py` | `Game/GameDir.swift`（+ `Fabric`） | ⚠️ 能力集不同 |
| `JavaRequirement` | `domain/java.py` | `OrzMCLauncher.JavaRuntimePolicy` | ⚠️ 托管策略不同 |
| `ArtifactRef/DownloadItem` | provider + `services/downloader.py` | `Game/Client+Download` 的 `DownloadItemInfo` | ⚠️ 结构不同 |
| `LibraryRule` | `domain/libraries.py` | `MojangAPI` + `Client+Boot` | ⚠️ |
| `ProgressEvent` | `infra/progress.py` | `progressHandler` | ⚠️ 需结构化 |
| `ClientLaunchPlan` | `domain/launch.py` | `Client+Boot.parseBootArgs()` | ⚠️ |
| `ServerDeployPlan` | `core/server/*` | `Game/Server/Deploy/*` | ⚠️ |
| `ServerLaunchPlan` | `services/server.py` | `Server+Launch.launchServer()` | ⚠️ |
| `CachePolicy` | `infra/cache.py` | （无） | ❌ |
| `InstallRecord` | `services/selfinstall.py` | `OrzAppUpdater`（部分） | ⚠️ |

> 下一版（`behavior.md` / `conformance.md`）将把上述 ⚠️/❌ 逐条转为**行为契约 + 黄金样例**。
