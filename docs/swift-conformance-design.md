# Swift 引擎一致性设计与能力边界

> **状态**：草案 ｜ **最后更新**：2026-10-13
> 目标：让 Swift 引擎（`OrzMCKit` + 依赖）满足 [`docs/spec/`](spec/README.md)，并接入父仓库
> 一致性套件（[`scripts/conformance/`](../scripts/conformance/README.md)）。为"全局最优"，
> 允许直接改各依赖仓库（均属维护者自有，见 [`AGENTS.md` §7.1](../AGENTS.md)）。

---

## 1. 现状能力地图（Swift 侧）

| 模块 | 现有能力 | 定位判断 |
|:--|:--|:--|
| `OrzMC/MojangAPI` | 版本清单（TTL 内存缓存）、版本列表、`Version.gameVersion`、asset index、OpenAPI DTO、`BuildType` | **元数据 + 缓存**职责 |
| `OrzMC/PaperMC` | `DownloadAPI`（Paper 构建/下载）、`HangarAPI`（插件）、`SimpleDownloader` | **服务端核心/插件获取** |
| `OrzGeeker/OrzSwiftKit` | `JokerKits`（FileManager/Shell/JSON/`Downloader`/`OracleJava`）、`Utils.Platform`（os/arch）、`SwiftUIX` | **基础设施** |
| `OrzMC/OrzMCKit` `Game` | `GameDir` 布局、`GameType`(vanilla/paper)、`Client`(Download/Boot/Fabric/Profile/Auth)、`Server`(Launch/Config)、`Deploy`(Vanilla/Paper)、`ClientInfo`/`ServerInfo` | **引擎：布局/下载计划/启动** |
| `OrzMC/OrzMCKit` `Fabric` | Fabric meta 模型 | 引擎子域 |
| `OrzMC/OrzMCKit` `OrzMC` | ConsoleKit CLI（client/server/plugin/fabric） | **产品面（CLI）** |
| `OrzMC/OrzMCApp` | SwiftUI GUI + 本地包（Foundation/Launcher/Protocol/RemoteHosting/DesignSystem） | **产品面（GUI）** |

---

## 2. 目标能力边界（L1）

- **元数据/缓存**：`MojangAPI` 唯一负责 Mojang 元数据与**统一缓存策略**（落盘 + TTL + refresh + 离线回退）。
- **服务端核心/插件**：`PaperMC` 负责 Paper/Hangar；`Game` 只编排。
- **基础设施**：`OrzSwiftKit` 提供文件/网络/Java/平台能力；**不承载业务语义**。
- **引擎契约**：`Game` 暴露**纯计划** API（不 IO），实现 [`spec/behavior.md`](spec/behavior.md)。
- **产品面**：`OrzMCKit` 的 `orzmc` CLI 与 `app` GUI 只消费 `Game` 公共 API。

---

## 3. 与规范的差距（按契约）

| 契约 | 规范 | Swift 现状 | 差距 |
|:--|:--|:--|:--|
| B4 布局 | `versions/<v>/{client,server/<type>}`、`java/<major>`、`cache/`、`backup/` | `manifest/<v>/client/<type>/…`（type 混入 client 路径） | **布局需重写**；`GameDir` 为枚举拼接，改造面广 |
| 类型 | `vanilla/fabric/forge/paper` + 能力矩阵 | `GameType` 仅 `vanilla/paper`；fabric 走独立 `FabricModel` | **类型收拢** |
| B5 Java | 托管 `java/<major>`（Adoptium），不依赖系统 java | `OracleJava`（仅 macOS，检测系统 JDK） | **需引入托管 JRE** |
| B1 缓存 | 磁盘 + TTL 24h + `refresh` 绕过 + 离线回退旧副本 | `APICache`（**仅内存**、TTL 由调用方传、`forceUpdate` 默认 `true`） | **需落盘 + 回退 + 统一 TTL** |
| B2 并发 | 默认 16、`Range` 4 路分块、连接池 ≥ 并发 | `Downloader`（Alamofire 重试）逐项下载 | **需分块 + 并发 + 池** |
| B3 校验 | 写入前/后 SHA-1，失败拒绝 | `DownloadItemInfo(hash, hashType)` 存在；校验待确认 | 需覆盖全链路 |
| B6 启动 | 纯函数、`-cp <joined>`、令牌规范（`user_type` 等） | `parseBootArgs` **扫描文件系统**拼 classpath、无显式 `-cp`、`user_type=mojang`、额外 `preferIPv4Stack` | **需纯计划化 + 令牌统一** |
| B7 生命周期 | stop/Ctrl-C 优雅退出、60s 超时、无孤儿 | `Server+Launch` + `Shell.stopAll` + pid 文件 | 需对齐退出码/超时 |
| B8 进度 | `count` 与 `bytes` 区分 | `progressBar`/回调（无类型区分） | 需结构化 |
| B9 非 TTY | 不阻塞、版本默认最新 release、用户名 `guest` | ConsoleKit 交互为主 | 需补非 TTY 分支 |
| B10 版本 | `release`/`snapshot`、latest.release | `Mojang.latest(type:)`、`BuildType` 四值 | 映射 `oldAlpha/oldBeta → snapshot` |
| B11 错误 | service 层归一化中文消息 | `MojangAPIError` 等 | 需归一 |

---

## 4. 一致性适配器设计

新增 **`Sources/ConformancePlan`（库，纯计划）+ 一个薄可执行/测试入口**，读 stdin JSON、回 stdout JSON
（协议见 [`conformance.md` §6](spec/conformance.md)）。操作映射：

| operation | 复用 | 需新增的纯计划接缝 |
|:--|:--|:--|
| `planLayout` | `GameDir`（**先对齐规范布局**） | `GamePlan.layout(root:version:type:platform:)` |
| `resolveVersion` | `MojangAPI` 清单 | 从**给定快照**解析（离线），不联网 |
| `requiredJava` | MojangAPI `GameVersion.javaVersion` | `GamePlan.requiredJava(versionJSON:)` |
| `verifyArtifact` | `Downloader`/`URL+FileHash` | 对给定字节计算 SHA-1 |
| `cacheDecision` | `MojangAPI.APICache` | 抽出**纯判定**（mtime/ttl/refresh/offline） |
| `planDownloadConcurrency` | — | 并发/分块常量（对齐 B2） |
| `resolveConcurrency` | — | clamp(1..64) |
| `planClientLaunch` | `Client+Boot` | **纯化** `parseBootArgs`（去掉 FS 扫描，classpath 由下载计划推导） |
| `nonTtyDefaults` | `Mojang.latest` | 显式非 TTY 分支 |
| `normalizeProgress` | — | 事件结构（B8） |

**离线要求**：适配器必需一个"喂入给定 JSON"的接缝（`MojangAPI` 目前从网络取）。最小改动：
给 `Mojang`/`APICache` 增加可从**给定数据**构造的入口（或适配器内自行解析 DTO）。

---

## 5. 改造清单（跨仓库）

| 仓库 | 改动 | 破坏性 |
|:--|:--|:--:|
| `OrzMCKit/Game` | `GameDir` 对齐规范布局；`GameType` 扩到 4 值 + 能力矩阵；`parseBootArgs` 纯化 + 令牌统一；`ConformancePlan` 接缝 | **是**（layout/类型） |
| `OrzMCKit/Fabric` | Fabric 归入 `GameType.fabric` 路径 | 是 |
| `MojangAPI` | 缓存落盘 + TTL 常量 + 离线回退；从给定 JSON 构造 | 部分 |
| `OrzSwiftKit` | `Platform.os` 映射 windows/osx/linux；下载并发/分块；Java 托管（或迁到 `Game`） | 部分 |
| `PaperMC` | 暴露 Paper 纯计划（build → `DownloadItem`） | 否 |
| `app` | 跟随 `GameDir`/类型变更（HEAD 制，需同步） | 是（级联） |

---

## 6. 执行顺序

1. **P2.1（附加，不破坏）**：在 `OrzMCKit` 加 `ConformancePlan` + 适配器骨架；先跑不依赖布局的操作
   （verify / concurrency / java / resolve / cache 判定），非布局类 fixtures 转绿；布局类如实 FAIL 作为基线。
2. **P3.1（破坏，需同步 app）**：`GameDir` 对齐规范布局 + `GameType` 四值 → 布局/启动类 fixtures 转绿；同批改 `app`。
3. **P3.2**：Java 托管、缓存落盘/回退、下载分块、进度结构。
4. **P2.3 / Q6**：父仓库运行器驱动 Swift 适配器；CI 接线。

---

## 7. 决策（以长期正确性为准）

- **D-a｜布局对齐方式：strangler-fig，不搭返工骨架**。引入**规范对齐的纯计划契约 `GamePlan`**（新契约，
  只用规范布局），旧 `GameDir` 暂存待退役；迁移 `OrzMC` CLI 与 `app` 后删除 `GameDir`。
  理由：在旧布局上先搭骨架会把错误路径写进适配器与测试，产生必然返工；把契约前置可让适配器/CLI/app 共建在同一正确契约上。
- **D-b｜Java 托管分层**：**获取原语**（按 os/arch/major 解析 Adoptium → 下载 → 校验 → 解压）放
  `OrzSwiftKit` 新 `RuntimeKit`（通用、可被非 MC 项目复用）；**托管策略与落点**（选哪个 major、放 `java/<major>`）放 `Game`。
  理由：原语通用、策略属引擎语义；避免把通用能力埋进引擎或把业务策略塞进工具库。
- **D-c｜统一缓存归属**：**基础设施**放 `OrzSwiftKit`（磁盘 + TTL 24h + `refresh` + 离线回退），
  `MojangAPI` / `PaperMC` 消费。理由：B1 的缓存对象跨多个 provider（Mojang/fabric-meta/Paper/Forge），
  与 Python `orzmc/infra/cache.py` 同层；放单一 provider 会耦合、难复用。
- **D11｜外部 Swift 依赖版本策略：HEAD 制**。`OrzMCKit` 的依赖（`OrzMC/MojangAPI`、`OrzMC/PaperMC`、
  `OrzGeeker/OrzSwiftKit`）由 tag（`from:`）改为 `branch: main`，与 Q7 一致、支持快速迭代。
- **D12｜`MojangAPI` 平台下限抬到 macOS 13 / iOS 16**（对齐 `OrzSwiftKit`），以消费 `CacheKit`；
  不再声明 tvOS/watchOS/visionOS（产品不使用；预稳定期可接受）。

### 7.1 执行顺序（按长期正确性排布）

1. **基础设施**（`OrzSwiftKit`）：☑ `CacheKit`（D-c）；☑ `RuntimeKit` JRE 获取原语（D-b）；
   ☑ `TransferKit`（B2/B8：**URLSession** + 4 路 `Range` 并行 + 200 回退 + 连接池 + 哈希跳过 + **断点续传** + **结构化进度 `count`/`bytes`**；**移除 Alamofire**）。
2. **元数据**（`MojangAPI`）：☑ 消费 `CacheKit`（manifest 落盘缓存）；☑ 真实清单离线解码 + `resolve(channel:)`；
   ☑ `BuildKind.channel`（非 release → snapshot）；☑ `JavaRequirement` 解析。
3. **引擎契约**（`OrzMCKit`）：☑ `GameType` 四值 + 能力矩阵 + `serverJarName`；☑ `GamePlan.layout`（规范布局）；
   ☑ `GamePlan.planClientLaunch`（B6 纯计划）；☑ `GamePlan.planServerDeploy`（data-model §9）；☑ `JavaRuntime`（托管 JRE 接入服务端/客户端，B5）；
   ☑ 服务端生命周期切到 `ManagedProcess`（B7）；☐ `GamePlan` 下载计划 / 进度；☐ 全量退役 `GameDir`。
4. **适配器**：☑ `ConformanceAdapter`（`OrzMCKit`）接入父仓库运行器；☑ OrzMCKit CI `conformance` job（Q6）。
5. **产品面**：☑ `GameDir` 已**退役**；CLI 与 app 调用点迁到 `GamePlan`（`GamePlan+Paths` 提供路径便捷 API）。
6. **CI（Q6）**：父仓库/子仓库接线。

> 验证前提：本地需能编译 `swift-tools-version:6.0` 的包（见下）——否则只能靠 CI/真机。
