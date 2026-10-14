# OrzMC 客户端/服务端工具统一化推进计划

> **状态**：草案（待评审） ｜ **创建**：2026-10 ｜ **维护方式**：每推进一步更新本文档的状态表与「变更记录」
>
> 本文档是这项工作的**单一事实来源**。任何新会话/AI 智能体只读本文件 + 第 9 章列出的源文件，
> 即可无损接着推进。**不要**依赖聊天记录或记忆。

---

## 0. 如何使用本文档

1. 先读第 2 章「现状事实（已核验）」——它是决策依据，路径均已核对。
2. 再读第 3 章「核心决策」——已经拍板的方向，除非有新证据否则不再翻案。
3. 按第 5 章「阶段计划」推进，每完成一项就把第 6 章状态表的复选框勾上，并在第 10 章追加一条记录。
4. 悬而未决的事项集中在第 7 章，推进前先清掉阻塞项。

---

## 1. 背景与目标

### 1.1 触发问题

`OrzPythonMC`（python 子模块）与 `OrzMCApp`（app 子模块）在**产品层面**都对外提供
「Minecraft Java 版 客户端启动 / 服务端部署」能力，用户提出：是否应合并为一个统一子方向、
同一仓库承载、统一架构/平台支持/模块划分，对外形成统一产品、对内形成可组合组件，
并沉淀一套语言无关标准。

### 1.2 核验后的结论（详见第 2 章）

- 两者**不在同一层**：app 是 GUI 前端，引擎在**外部 Swift 依赖链**（`OrzMCKit` →
  `MojangAPI` / `PaperMC` / `OrzSwiftKit`）；python 是「引擎 + CLI + 安装器 + 自升级」全栈。
- 真正的重复在**引擎层**（Python `orzmc.core` ↔ Swift `OrzMCKit` 链），不在「python vs app」。
- 因此**不合并仓库**；改为「一份规范 + 多套实现 + 多个前端 + 一个产品伞」。

### 1.3 目标（可验收）

- G1：沉淀语言无关规范 **`docs/spec/`**（= `orzmc-spec` 雏形）：统一数据模型、中间表示（计划表）、行为契约、版本化；成熟后再下沉独立仓库。
- G6：产品形态统一为**一个 `orzmc`**：CLI 与 GUI 两面、**共用核心逻辑**、可**互相安装/打开**；允许差异化功能，但主体核心逻辑一致。
- G2：建立**跨语言一致性套件**（黄金样例），Python 与 Swift 实现跑同一套用例，差异即红灯。
- G3：引擎收敛为**可分阶段调用的可组合组件**（resolve → plan → download → verify → assemble → launch）。
- G4：前端各自独立发布，父仓库提供**统一产品伞**（品牌 / 文档索引 / 版本列车）。
- G5：**不**强制统一版本号、**不**牺牲平台灵活性（iOS 不跑 Python、Windows/Linux 不跑 Xcode）。

### 1.4 非目标（明确排除）

- ❌ 把 Swift GUI 与 Python CLI 塞进同一个仓库（工具链/CI/签名/平台矩阵不兼容，理由见第 3 章）。
- ❌ 统一 UI 代码或架构（前端各异是合理的）。
- ❌ 用一套版本号给所有子件发版。

---

## 2. 现状事实（已核验）

> 证据口径：仓库内实际文件与 `Package.swift` / `project.pbxproj` / `AGENTS.md` 中的声明。

| 维度 | `python/` (OrzPythonMC) | `app/` (OrzMCApp) |
|---|---|---|
| 角色 | 引擎 + CLI + 安装器 + 自升级，全栈自持 | GUI 外壳；引擎**不在本仓库** |
| 引擎位置 | 仓内 `orzmc/orzmc/core/`（`mojang.py` / `fabric.py` / `forge.py` / `client/*` / `server/*`） | 外部 **Swift 依赖链**：`OrzMC/OrzMCKit`（`Game` / `Fabric`，**并自带 `orzmc` 可执行 CLI**）→ `wangzhizhou/MojangAPI`、`wangzhizhou/PaperMC`（`DownloadAPI`/`HangarAPI`）、`OrzGeeker/OrzSwiftKit`（`JokerKits`/`Utils`）；app 仓内仅 `GUIClient: Game.Client`、`GUIServer: Game.Server` 适配器 |
| 关键引擎符号归属 | `orzmc/services/{client,server,versions,downloader,java}.py` | `Game.ClientInfo` / `Game.ServerInfo` / `GameDir` / `generateDownloadItemInfos()` / `parseBootArgs()` 来自 `Game` 包（仓内 grep 无定义） |
| 本仓组件 | 库 `orzmc`（PyPI）+ 应用 `orzmc-app`（typer CLI） | 本地 SwiftPM 模块：`OrzMCFoundation` / `OrzMCLauncher` / `OrzMCProtocol` / `OrzMCRemoteHosting` / `OrzMCDesignSystem`（`Package.swift`），另有 iOS SLP/RCON/Query、Exaroton 云集成、`OrzAppUpdater` |
| 代码量 | ~5.6k LOC Python（`orzmc` + `orzmc_app`） | ~5.7k LOC Swift，且大半是 SwiftUI |
| 平台 | Windows / Linux / macOS × x86_64 / arm64（6 目标） | macOS + iOS（Apple only） |
| 发布 | PyPI 双包（OIDC + PEP740 provenance）+ 6 平台 PyInstaller 二进制 + `install.sh/ps1`；release-please | Developer ID 签名 + notarize + appcast；CI 固定 `macos-26` + Xcode 26.3 |
| 架构成熟度 | 分层严格（domain/infra/core/services），AGENTS.md 为单一事实来源，测试/验收/CI 完整 | 引擎已抽出，前端已做本地 SwiftPM 模块化，但引擎仍在编外仓库 |
| 父仓库关系 | git 子模块，branch=main | git 子模块，无 branch 声明 |

**引擎链与治理发现（2026-10-13 浅克隆 `OrzMCKit` 核验）**：
- `OrzMCKit` 产出 `Game` / `Fabric` 两个库 **外加一个 `orzmc` CLI 可执行**（swift-argument-parser，命令 `client`/`server`/`fabric`/`plugin`）——与 Python `orzmc` CLI **功能重叠**，是第三个前端面。
- 引擎并非单仓：`Game` 依赖 `MojangAPI`（元数据）、`PaperMC`（`DownloadAPI`/`HangarAPI`）、`OrzSwiftKit`（`JokerKits`/`Utils`），**后三者位于个人仓库**（`wangzhizhou/*`、`OrzGeeker/*`），不在 `OrzMC` 组织下。
- **根目录布局两边不一致**：Swift `~/minecraft/manifest/<v>/client/<type>/...` vs Python `~/minecraft/versions/<v>/client/...`；类型支持也不同（Swift 服务器仅 vanilla/paper）。详见 [`product-architecture.md`](product-architecture.md) 第 8 章。

**引擎重复点（G1/G2 的靶心）**：Mojang 版本清单、version JSON、libraries/assets 下载计划、
natives OS-arch 规则、Java 版本推导、Fabric/Forge/Paper provider、启动参数拼装——两边各写了一套。

**已有可复用先例**：父仓库中 `plugin` 已有独立 `orzmc-api`（零 Bukkit、可发布）；`tools/thanos`
与 `tools/rust-thanos` 是「上游 + 自研重写」的对照模式，证明本组织接受「多实现 + 对齐」。

---

## 3. 核心决策

| # | 决策 | 理由（摘要） |
|---|---|---|
| D1 | **不合并 python 与 app 仓库** | 工具链（uv vs Xcode/SwiftPM）、CI runner（6 廉价 vs `macos-26`+证书）、发布通道（PyPI vs notarize/appcast）、平台矩阵（6 平台 vs Apple only）不兼容；iOS 不能跑 Python，「同一仓库=同一产品」不成立 |
| D2 | 目标架构 = **一份规范 + 多套实现 + 多个前端 + 一个产品伞** | 消灭引擎重复且不牺牲平台灵活性 |
| D3 | **语言无关标准**落到父仓库 `docs/spec/`（Q2 已决；成熟稳定后再下沉独立仓库 `orzmc-spec`） | 先降低落地成本不新增仓库；成熟后独立可避免寄居某语言仓库 |
| D4 | 一致性靠**黄金样例 + 跨语言 conformance 套件**，不靠人肉对表 | 唯一能长期防漂移的手段 |
| D5 | `OrzMCKit`（Swift 引擎）应纳入 org 治理视野（子模块登记或迁移） | 目前是「编外引擎」，是上下文丢失的最大来源之一 |
| D6 | 父仓库（OrzMC）承担**产品伞**：品牌 / 文档索引 / 版本列车 | 父仓库本就是统一入口，无需代码合并 |
| D7 | 产品形态：**一个 `orzmc`**，CLI + GUI 两面，**共用核心逻辑**、可**互相安装/打开**；允许差异化功能、核心统一 | 用户期望的是一个可自洽的产品，而非两个同名工具 |
| D8 | `OrzMCKit` 定位为 **Swift 语言下可复用的基础组件**（非 App 私有引擎）：既服务 Swift CLI，也服务 GUI | 使其可被其它 Swift 项目复用，改善治理 |
| D9 | CLI 需**可被 AI 调用**：全局 `--json` + 能力发现（`capabilities`）+ 非交互确定性；**评估 MCP**，不追 “open-cli” 空名 | AI 协作者需要可解析、可发现的接口 |
| D10 | Swift/SwiftPM 依赖一律用 `OrzMC/*` **规范路径**（禁重定向）；`OrzMCKit` 本地覆盖**仅供开发态、不提交** | 消除重定向误读，同时不破坏 app 独立构建 |
| D11 | **外部 Swift 依赖版本策略：HEAD 制**——`OrzMCKit` 的 `MojangAPI`/`PaperMC`/`OrzSwiftKit` 改用 `branch: main` | 与 Q7 一致，支撑快速迭代 |
| D12 | **`MojangAPI` 平台下限抬到 macOS 13 / iOS 16**（消费 `CacheKit`） | 统一缓存层跨包复用；预稳定期可接受 |

> 决策若被推翻，必须在本章追加「~~D#~~ 已推翻，原因…」并说明替代方案，不得直接删除。

---

## 4. 目标架构

```
Layer 3  产品伞（父仓库 OrzMC + profile + site）          ← 品牌 / 版本列车 / 文档索引
            ▲                        ▲
Layer 2  前端 orzmc-app (typer CLI)   OrzMCApp (SwiftUI GUI + iOS 助手)
            │                        │
Layer 1  引擎 orzmc (PyPI lib)        OrzMCKit (Game / MojangAPI)   ← 各自实现，同过 conformance
            │                        │
Layer 0  ─────────────  orzmc-spec  ─────────────
         数据模型 / 归一化中间表示 / 行为契约 / 版本号 / 黄金样例
```

**可组合阶段（G3 的统一抽象）**：

```
resolve   解析元数据（版本清单 / version JSON / loader / Java 需求）
  → plan      生成纯数据计划表（download items / launch args / server plan）
  → download  按计划下载（并发 / Range 分块 / 缓存）
  → verify    SHA-1 等完整性校验
  → assemble  组装运行时（类路径 / natives / 配置）
  → launch    启动客户端 / 服务端并托管生命周期
```

每个阶段都应能被**单独调用**（二次开发接缝），实现内部可跨语言不同，但**输入/输出符合 spec**。

---

## 5. 阶段计划

> 每阶段给出：目标 / 交付物 / 验收标准 / 影响仓库 / 依赖。
> 影响仓库标注：`parent`=OrzMC 父仓库，`spec`=待建，`python`=OrzPythonMC，`app`=OrzMCApp，`kit`=OrzMCKit。

### Phase 0 — 冻结边界与决策（文档）

- **目标**：把第 2/3/4 章固化，定义各层所有权与"不该做什么"。
- **交付物**
  - `parent:docs/product-unification-plan.md`（本文件）
  - `parent:docs/product-architecture.md`（分层、所有权、前端/引擎/平台件边界；供协作者与用户阅读）
  - 在父仓库 README 增补一行指向上述文档（可选，待确认）
- **验收**：评审通过第 3 章决策；`product-architecture.md` 中列出每层的"允许依赖方向"与"禁止事项"。
- **依赖**：无。
- **产出物状态**：☑ 计划文档 ☑ 架构文档（`docs/product-architecture.md`）☑ README 链接

### Phase 1 — `docs/spec/`（orzmc-spec 雏形）：数据模型与中间表示

- **目标**：抽出跨语言共用的纯数据契约，并定义统一的 CLI/产品面契约。
- **落点（Q2 已决）**：父仓库 `docs/spec/`，成熟稳定后再考虑下沉独立仓库 `OrzMC/orzmc-spec`。
- **交付物**（均落在 `docs/spec/`）
  - [`spec/data-model.md`](spec/data-model.md)：核心数据模型（`RootLayout` / `VersionManifest` / `VersionEntry` /
    `GameType` / `JavaRequirement` / `DownloadItem` / `LibraryRule` / `ProgressEvent` / `ClientLaunchPlan` /
    `ServerDeployPlan` / `ServerLaunchPlan` / `CachePolicy` / `InstallRecord`）+ **Python↔Swift 字段对照**。
  - [`spec/behavior.md`](spec/behavior.md)：行为契约 B1–B11。
  - [`spec/cli-surface.md`](spec/cli-surface.md)：CLI 命令面统一契约 + 冲突解决表 + 迁移清单。
  - [`spec/install-update.md`](spec/install-update.md)：安装/自升级/跨面安装（无 sudo / Shell 自动识别 / 补全 / 双渠道兜底）。
  - [`spec/conformance.md`](spec/conformance.md)：黄金样例格式与一致性套件契约。
- **验收**：python `orzmc/domain/*` 与 Swift `Game`/`MojangAPI` 的公共字段都能**无损映射**到该模型（`data-model.md` 字段对照总表）。
- **依赖**：Phase 0；`OrzMCKit` 类型已核验（Q1 已决）。
- **产出物状态**：☑ `docs/spec/` 建立 ☑ 数据模型 ☑ 字段对照表 ☐ 字段映射验证（待 Phase 2 样例跑通）

### Phase 2 — 黄金样例 + 跨语言 conformance 套件

- **目标**：把「计划表」变成可断言的对象，防实现漂移。
- **交付物**
  - `docs/spec/fixtures/`：钉住快照（`version_manifest.json` / `versions/*.json`）——已落地。
  - `docs/spec/fixtures/<area>/`：`given→expect` 黄金样例（**27 例**：layout / version-resolve / java / verify / cache / download / client-plan / server-plan / non-tty / progress / error）。
  - `scripts/conformance/`：语言无关**运行器** `run.py` + **规范参考适配器** `reference.py`（子集 / Contains / Order / Count / Set 断言、点号路径、错误码）。
  - `python`：适配器断言 plan == 期望（复用 `orzmc` 内部 API）。
  - `kit`：适配器断言 `Game` 纯计划 == 期望。
  - 剩余：`server-plan/` / `server-lifecycle/` 样例；把两个真实适配器接入。
- **验收**：参考适配器自检全绿（27/27）；两个真实适配器在 CI 跑 fixtures 全绿；**故意改坏一处能被红灯抓到**（负向用例）。
- **依赖**：Phase 1。
- **产出物状态**：☑ fixtures ☑ 期望输出 ☑ 运行器/参考适配器 ☑ Python 适配器 ☐ Swift 适配器 ☐ CI 接线

### Phase 3 — 引擎对齐与收敛

- **目标**：消除 Phase 2 暴露的差异，补齐行为契约。
- **交付物**
  - 行为契约文档（并入 spec）：SHA-1 校验、缓存 TTL/refresh 语义、小文件并发批量、
    大文件 `Range` 分块与 200 回退、重试退避、natives OS-arch 规则、Java 版本推导。
  - python：把内部「计划」阶段显式暴露为可测试/可复用接缝（现已有 `PathLayout` 纯函数基础）。
  - kit：确保 plan 生成可独立调用、可序列化。
  - 差异清单 + 逐条决策（谁改、为什么）。
- **验收**：Phase 2 全部矩阵绿；行为契约中每条都至少有一个跨语言用例。
- **依赖**：Phase 2。
- **产出物状态**：☐ 行为契约 ☐ Python 接缝 ☐ Swift 接缝 ☐ 差异清单清零

### Phase 4 — 前端组件化（方便二次开发）

- **目标**：把「基础功能组件」做成可独立复用/组合的稳定 API。
- **交付物**
  - python：维持库/应用双层（已达成），补齐公共 API 契约与文档；确保 6 阶段可单独调用。
  - app/kit：延续本地 SwiftPM 模块化（`OrzMCFoundation/Launcher/Protocol/RemoteHosting/DesignSystem`），
    冻结稳定协议（如 `RemoteServerHosting`），引擎 `Game` 的公共 API 语义化。
  - 一份「二次开发指南」：如何只用引擎、如何只用计划阶段、如何接入新前端。
- **验收**：存在一个**最小示例**（Python 与 Swift 各一），仅依赖组件完成「解析→生成计划」而不启动游戏。
- **依赖**：Phase 3。
- **产出物状态**：☐ Python 公共 API 冻结 ☐ Swift 协议冻结 ☐ 二次开发指南 ☐ 双语言最小示例

### Phase 5 — 统一产品发布列车

- **目标**：对外形成统一产品认知，但不合并仓库/版本号。
- **交付物**
  - `parent:RELEASES.md`：各子件版本对应关系（product release train）
  - 父仓库统一文档索引（引擎/前端/规范/工具）
  - `site` 上统一产品介绍页（可选）
- **验收**：任意一次发版，`RELEASES.md` 能说明"本轮产品 = 哪些子件版本"。
- **依赖**：Phase 1 起即可并行（内容型）。
- **产出物状态**：☐ RELEASES.md ☐ 文档索引 ☐ 官网产品页

---

## 6. 进度与里程碑状态表

| 阶段 | 关键里程碑 | 状态 |
|---|---|---|
| Phase 0 | 计划文档落库 | ☑ 已完成（本文件） |
| Phase 0 | `product-architecture.md` | ☑ 已完成 |
| Phase 0 | 第 3 章决策评审通过 | ☐ 待评审 |
| Phase 1 | `docs/spec/` 规范建立 | ☑ 已完成 |
| Phase 1 | 数据模型 + 字段对照表 | ☑ 已完成（`data-model.md`） |
| Phase 1 | CLI/安装/行为/一致性契约 | ☑ 已完成（`cli-surface.md`/`install-update.md`/`behavior.md`/`conformance.md`） |
| Phase 1 | 字段映射验证（样例跑通） | ☐ 待 Phase 2 |
| Phase 2 | fixtures + 运行器/参考适配器 | ☑ 已完成（27/27 自检绿） |
| Phase 2 | Python 适配器接入 | ☑ 已完成（27/27，PR #32/#33） |
| Phase 2 | Swift 适配器接入 | ☑ 已完成（26/26，OrzMCKit CI） |
| Phase 2 | CI 接线 | ☐ 未开始 |
| Phase 3 | 差异清零 + 行为契约 | ☐ 未开始 |
| Phase 4 | 双语言最小示例 | ☐ 未开始 |
| Phase 5 | RELEASES.md | ☐ 未开始 |

---

## 7. 开放问题（推进前须清）

| # | 问题 | 影响 | 建议默认 | 状态 |
|---|---|---|---|---|
| Q1 | `OrzMCKit` 仓库是否可读/可改？（决定 Phase 1 能否核对 Swift 类型） | 解阻塞 Phase 1 | ✅ 已确认：可访问（`main`），已浅克隆核验；注意其引擎依赖 `MojangAPI`/`PaperMC`/`OrzSwiftKit` 在个人仓库 | ✅ |
| Q2 | `orzmc-spec` 落点？ | 决定 Phase 1 落点 | ✅ 已决：**父仓库 `docs/spec/`**，成熟后再下沉独立仓库 | ✅ |
| Q3 | `OrzMCKit` 如何定位？ | 治理与复用 | ✅ 已决：**Swift 可复用基础组件**（非 App 私有引擎），服务 Swift CLI 与 GUI | ✅ |
| Q4 | app 仓库 `.gitmodules` 已空、且曾移除 OrzMCKit 子模块——是否要恢复登记以避免"引擎游离"？ | D5 具体做法 | ✅ 已决：**登记为父仓库子模块**（`OrzMCKit`，路径 `OrzMCKit/`，`main`，钉 `e302d4e`） | ✅ |
| Q5 | spec 数据模型用 JSON Schema 还是「Markdown + JSON 样例」起步？ | Phase 1 工作量 | ✅ 已决：先 **Markdown + JSON 样例**（已落 `docs/spec/data-model.md`），稳定后再补 Schema | ✅ |
| Q6 | conformance 是否要求 Swift 侧也进父仓库 CI（跨仓库触发）？ | Phase 2 复杂度 | ✅ 已决：**各实现仓库 CI 内跑**——OrzMCKit CI 检出父仓库 fixtures 后跑 `run.py --strict`；父仓库只做状态汇总 | ✅ |
| Q7 | “伞内引擎版本”定为 tag（`0.0.6`）还是分支 HEAD？子模块钉 HEAD，app 的 `Package.resolved` 钉 tag，当前不一致 | Phase 2/3 对齐 | ✅ 已决：**HEAD 制（B）**——子模块与 app 都跟随 `OrzMCKit` 的 `main` HEAD（app 改用 `branch = main`），因需快速迭代 | ✅ |

---

## 8. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 过度抽象：spec 比实现还重 | 拖慢两条产品线 | 先只覆盖「计划表」纯数据，行为契约按需增补 |
| spec 漂移（实现偷偷偏离） | 一致性套件失效 | fixtures 进 CI，差异即红灯；spec 自身带版本号 |
| 单点维护者带宽（单人项目） | 计划搁置 | 分阶段可独立交付；Phase 5 内容型可与 Phase 1 并行 |
| 跨仓库改动难协调 | PR 割裂 | 用父仓库「版本列车」记录一次产品变更涉及哪些子件 PR |
| 方案被误读为"必须合并仓库" | 走错方向 | 第 3 章 D1 + 第 1.4 节非目标显式排除 |

---

## 9. 上下文包（关键源文件清单，供后续会话按需读取）

> 新会话续接时，读本文件 + 下列文件即可，**不要**整仓扫描。

**python 引擎与分层**
- `python/AGENTS.md`（单一事实来源：分层/缓存/进度/下载并发/发布链路）
- `python/orzmc/orzmc/domain/{types,paths,java,launch,libraries,options}.py`
- `python/orzmc/orzmc/core/{mojang,fabric,forge}.py`、`core/client/*`、`core/server/*`
- `python/orzmc/orzmc/services/{client,server,versions,downloader,java}.py`
- `python/orzmc/orzmc/__init__.py`（公共 API 契约）

**app 前端与引擎边界**
- `app/README.md`、`app/OrzMC/Common/documentation.docc/Architecture.md`
- `app/Package.swift`（本地 SwiftPM 模块划分）
- `app/OrzMC/Launcher(MacOS)/Controller/{GUIClient,GUIServer}.swift`（引擎适配器，看 `Game`/`MojangAPI` 用法）
- `app/OrzMC/Launcher(MacOS)/Model/{GameModel,GameCatalogService,GameLaunchService,JavaRuntimeService,SettingsModel}.swift`
- `app/OrzMC.xcodeproj/project.pbxproj`（外部包：`OrzMC/OrzMCKit`、`OrzGeeker/OrzSwiftKit`、`OrzGeeker/OrzAppUpdater`、`wangzhizhou/ExarotonAPI`）
- `app/Sources/OrzMCRemoteHosting/RemoteServerHosting.swift`（稳定协议示例）
- `app/Package.resolved`

**父仓库与先例**
- `README.md`、`.gitmodules`
- `plugin/docs/architecture.md`（orzmc-api 分层先例）
- `tools/thanos` ↔ `tools/rust-thanos`（多实现对齐先例）

---

## 10. 变更记录

| 日期 | 变更 | 作者 |
|---|---|---|
| 2026-10 | 初始草案：核验现状、确立 D1–D6、列出 Phase 0–5 与开放问题 | — |
| 2026-10-13 | Phase 0：产出 [`product-architecture.md`](product-architecture.md)（分层/依赖/治理） | pi |
| 2026-10-13 | 决策 Q1（OrzMCKit 可访问）+ 新增 D7（一个 `orzmc`、CLI+GUI 两面、共核、互相安装/打开）/ D8（OrzMCKit 定位） | pi |
| 2026-10-13 | 决策 Q2（规范落 `docs/spec/`）/ Q3（OrzMCKit=Swift 可复用基础组件）/ Q5（Markdown+JSON 起步）；Phase 1 启动，产出 `docs/spec/` | pi |
| 2026-10-13 | Phase 1 规范草案完成（`data-model`/`behavior`/`cli-surface`/`install-update`/`conformance`） | pi |
| 2026-10-13 | 清 待定：`--root-dir/--verbose` 全局、`--json`、`--auth` 纳入、`server` 默认 vanilla、CLI 支持 AI 调用（D9）；Windows 落点 `%LOCALAPPDATA%\Programs\orzmc`、引入 `beta` 渠道、GUI 计划中；布局一次性对齐不迁移、arch 支持 x86 | pi |
| 2026-10-13 | 定稿 `--json` 信封（`cli-surface.md` §6.1：`{ok,command,data,error}`）；`capabilities` / `orzmc mcp` 列为**计划、低优先级** | pi |
| 2026-10-13 | Phase 2 启动：产出 `docs/spec/fixtures/`（26 样例 + 快照 + schema）与 `scripts/conformance/{run.py,reference.py}`（语言无关运行器 + 参考适配器，自检 26/26 绿） | pi |
| 2026-10-13 | Python 适配器接入：`OrzPythonMC#32` 新增 `orzmc/tests/conformance/adapter.py`（26/26 绿，6 平台 CI 过） | pi |
| 2026-10-13 | **Q4 已决**：登记 `OrzMCKit`（`OrzMC/OrzMCKit`，`main`，钉 `e302d4e`）为父仓库子模块；核实 `MojangAPI`/`PaperMC` 已入组织 | pi |
| 2026-10-13 | 依赖 URL 统一迁到组织规范路径（`OrzMC/MojangAPI`、`OrzMC/PaperMC`、`OrzMC/ExarotonAPI`、`OrzMC/OrzMCKit`、`OrzMC/OrzMCApp`，含 `SUFeedURL`）；明确本地覆盖仅供开发态（D10） | pi |
| 2026-10-13 | **Q7 已决（B/HEAD 制）**：伞内引擎版本 = `OrzMCKit` `main` HEAD；`app` 的 SwiftPM 依赖改用 `branch = main` | pi |
| 2026-10-13 | **D11**：外部 Swift 依赖也改 HEAD 制（`OrzMCKit` → `MojangAPI`/`PaperMC`/`OrzSwiftKit` 用 `branch: main`） | pi |
| 2026-10-13 | Swift 基础①：`OrzSwiftKit` 新增 `CacheKit`（统一元数据缓存，D-c；PR #2 已合，CI 绿）；放宽 OrzGeeker 保护（关 `enforce_admins`） | pi |
| 2026-10-13 | Swift 基础①(续)：`OrzSwiftKit` 新增 `RuntimeKit`（Java 获取原语，D-b）与 `TransferPolicy`（B2 纯策略）（PR #3 已合，CI 绿） | pi |
| 2026-10-13 | Swift 基础②（`MojangAPI`）：渠道归一 + 真实清单离线解码 + `JavaRequirement`；消费 `CacheKit` 落盘缓存（D-c/D12，CI 绿） | pi |
| 2026-10-13 | Swift 引擎③起步（`OrzMCKit`）：`GameType` 四值 + 能力矩阵 + `serverJarName`；新增规范对齐的 `GamePlan.layout` 纯计划契约（D-a，strangler-fig） | pi |
| 2026-10-13 | Swift 引擎③续：`GamePlan.planClientLaunch`（B6 纯计划，含 `VersionPlan`/rules/令牌/classpath） | pi |
| 2026-10-13 | Swift 适配器④：`OrzMCKit` `ConformanceAdapter` 26/26 绿；OrzMCKit CI 新增 `conformance` job（Q6） | pi |
| 2026-10-13 | Phase 3：`GameDir` 改为**委托 `GamePlan` 的兼容层**（路径切规范布局，CLI/app 无需改动）；Swift 引擎布局对齐 | pi |
| 2026-10-13 | `OrzMCApp` 新增**构建校验 CI**（xcodebuild build），验证布局切换后 app 仍可编译（绿） | pi |
| 2026-10-13 | 运行时：`JavaRuntime` 托管 JRE（B5）接入引擎（服务端/客户端/CLI/GUI），移除 `which java`；修 `OrzAppUpdater` 平台声明并发 0.0.3 | pi |
| 2026-10-13 | 网络层统一：`OrzSwiftKit` 新增 `TransferKit`（B2，URLSession），**移除 Alamofire**（Swift 侧不再有三方 HTTP 客户端） | pi |
| 2026-10-13 | `TransferKit` 新增**断点续传**：`.part` 持久化 + `Range` 续传（单流与 4 路分块均支持） | pi |
| 2026-10-13 | `TransferKit` 新增**结构化进度 `TransferProgress`**（B8）：单流报 `bytes`、批量报 `count` | pi |
| 2026-10-13 | 一致性扩到服务端：新增 `server-plan/`（`planServerDeploy`，27 例）；Swift/参考/Python 三适配器均实现（OrzMCKit `507d467`、`OrzPythonMC#33`） | pi |
| 2026-10-14 | B7 进程原语：`OrzSwiftKit` 新增 `ProcessRunner`/`ManagedProcess`（优雅停止 → SIGTERM → SIGKILL、退出码归一、`onLine` 透传；含测试） | pi |
| 2026-10-14 | B7 接线：引擎 `Server` 生命周期切到 `ManagedProcess`（CLI 前台等待 + 打印退出码；app `GUIServer` 返回 `ManagedProcess`） | pi |
