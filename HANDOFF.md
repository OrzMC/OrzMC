# HANDOFF.md — OrzMC 跨会话 / 跨设备交接文档

> **用途**：任何 AI 智能体或维护者在**新会话 / 新设备**接手父仓库工作时，先读
> [`AGENTS.md`](AGENTS.md)（规则）+ 本文件（状态）+ 进行中方案，即可无损恢复上下文。
>
> **为什么必须有**：聊天记录不跨会话、不跨设备；本地未提交状态不跨设备。
> **凡是"下次还要知道"的信息，都必须落到 Git 里的文件**——本文件就是那个落点。
>
> **维护规则**：
> 1. 每次会话**结束前**更新第 1 章「当前焦点」、第 2 章「状态快照」、第 5 章「会话日志」。
> 2. 会话日志**只追加不删改历史**，最新在最上。
> 3. 本文件是**状态**，不是**规则**（规则在 `AGENTS.md`）也不是**方案**（方案在 `docs/`）。
>    只放"现在到哪了、下一步做什么"，不复制规则与方案正文。
>
> **最后更新**：2026-10-30 by pi（UI 优化 + 验收交接给 Codex）

---

## 0. 接手速查（Session Start Checklist）

```bash
git status --short --branch             # 先检查分支、未提交改动与 ahead/behind
git -C swift/app status --short --branch # app 子模块也要单独检查
git submodule status                    # 子模块指针与初始化状态
# 只有工作区干净且确认目标分支后，才 fetch/pull；不要对有改动的接力工作树直接 pull
python3 scripts/verify/check.py        # 父仓库组合校验（登记表一致 + 一致性参考自检）
```


## 0.1 接力提示词（**维护者不用复制** —— `AGENTS.md` §0 会让新会话自己读到这里）

> 你在 `OrzMC` 父仓库（产品伞，22 个子模块）。**先读 `AGENTS.md`（规则）+ `HANDOFF.md`（状态）**，
> 再按需读 `docs/`。铁律：**代码改子模块、父仓库只 bump 指针**、**禁用 `git add -A`**、
> 一次提交只 bump 一个子模块（同一产品级变更可合并 bump，见 AGENTS §2）。
>
> **本轮焦点：P2-7 多供应商（Exaroton + MCSManager）—— 第 1 步 ✅，从第 2 步开工。**
> 待办、维护者拍板四条、建议的 5 步顺序都在
> [`swift/app/docs/backlog-2026-10-25.md`](swift/app/docs/backlog-2026-10-25.md) 的 P2-7（开头就是"已拍板 + 开工顺序"）；
> 抽象层的分层与不变量见 [`swift/app/docs/remote-hosting-providers.md`](swift/app/docs/remote-hosting-providers.md)。
>
> **当前状态（2026-10-25；0.1.5 已发布，P2-7 第 1–2 步已合入）**
> - **先跑 `./scripts/dev/boot-check.sh`**（只读自检；换设备或隔了几天用 `--fetch`）——
>   它检查父仓库是否落后、子模块是否初始化、指针在不在本地、组合校验是否通过，并直接给出要跑的命令。
> - 工作目录 `/Users/joker/Documents/OrzMC`（Air 本机正式仓库）；**不要用 `ssh air` / 旧 `scripts/air/run.sh`**（已删）。
> - 父仓库 `main` 与 `swift/app` `main` 均已推送干净（app = `218ff8e6`，含 0.1.5 发版、P2-7 计划与第 1–2 步）。
>   **不要 `git reset --hard`**（父仓库常有未提交文档），用 `git merge --ff-only`。
>   父仓库里 `tools/OrzMCBackup` 显示为 `m`（子模块内部有本地改动）**是历史遗留，别动它、别 bump**。
> - **0.1.5 (57) 已发布**（notarized + Sparkle appcast）；本机 `/Applications/OrzMC.app` 与
>   iPhone SE3 都已是 0.1.5 (57)。0.1.4 修掉的两个回归：删除确认框崩溃（译文占位符顺序）、
>   远程控制台不显示日志（行尾 `\r` 被吞）。
> - 门禁：`swift/app/scripts/dev/check.sh`（`--fast` / 默认含单测+macOS 构建 / `--ios` / `--ui`）；
>   UI 自动化 `swift/app/scripts/dev/run-ios-ui-tests.sh [--device <UDID>]`。
>   ⚠️ `protocol-live` 偶发失败（假 RCON 多包拼接用例），`gh run rerun --failed` 即绿，别急着改产品代码。
> - **远程状态只有一条路**：供应商无关的 `RemoteStatusCenter`（`Sources/OrzMCRemoteHosting/RemoteStatusCenter.swift`）
>   = 唯一写入口 `publish(_:for:source:)` + 订阅 `events()`；app 侧接缝是
>   `OrzMC/Common/ExarotonUI/Model/ExarotonServerModel+StatusCenter.swift`（`publishStatus` / `statusEvents()` /
>   `effectiveStatus`）。轮询判据是"WebSocket 是否安静 30 秒"（`RemoteStatusRefreshPolicy`，同文件），
>   **不要再用 `isLive` 当判据**。读 [`swift/app/docs/remote-status-source.md`](swift/app/docs/remote-status-source.md)
>   与 [`swift/app/docs/remote-hosting-providers.md`](swift/app/docs/remote-hosting-providers.md)（分层 + 不变量）。
> - 供应商抽象层（P2-7 第 1 步）：`Sources/OrzMCRemoteHosting/RemoteHostingProvider.swift`；
>   exaroton 适配器 `OrzMC/Common/ExarotonUI/Model/ExarotonHostingProvider.swift`（界面还没消费它，行为不变）。
>   状态中心的键是 `RemoteInstanceID`（供应商 + 原始 ID），**不要**退回裸字符串 id。
> - MCSM 客户端（P2-7 第 3 步）：**新子模块** `swift/lib/MCSManagerAPI`（`OrzMC/MCSManagerAPI`）；
>   `Sources/MCSMAPI/openapi.yml` 是**按官方 apidoc 手写的最小 spec**（官方没有机器可读 OpenAPI），
>   改端点要同步 spec + README；本机可 `swift test --package-path swift/lib/MCSManagerAPI` 验证。
>   ⚠️ 面板需在设置里打开 API Key 功能，否则带 key 的请求一律 403。
> - MCSM 只读接入（第 4 步，app 侧）：`OrzMC/Common/MCSManager/`（凭据/接口/实现/模型）+
>   `OrzMC/Common/MCSManagerUI/`（`MCSManagerSection` 面板卡/实例行；`MCSManagerPanelEditor` 增/改面板）。
>   两个 DEBUG 钩子：`ORZMC_DEMO_MCSM_FAKE=1`（假面板）、`ORZMC_DEMO_MCSM_DIAGNOSE=1`
>   （**无界面**拉一遍所有面板 → 写 `Caches/orzmc-mcsm-<id>.json`（含分支轨迹）→ 退出；
>   macOS 无屏幕录制权限、iPhone SE 上 MCSM 分组在折叠线下，靠它验收）。
>   ⚠️ **别在 SwiftUI 容器上设 `accessibilityIdentifier`**（会下发给子元素并覆盖子元素自己的 identifier）。
> - ⚠️ MCSM 面板 **10.18.0 的响应坑**（已适配，改 spec 时别踩回去）：
>   ① `GET /api/auth` 被包了一层 `{status,data:{…}}`；② `loginTime`/`registerTime` 是**字符串**；
>   ③ 错误响应 `Content-Type: text/plain`（body 是 JSON 文本）。
>   实例的键是 `RemoteInstanceID`（供应商 + 原始 ID），**不要**退回裸字符串 id。
> - 状态徽章只有 `OrzMCStatusBadge`（`Sources/OrzMCDesignSystem/StatusBadge.swift`），旋转图标是
>   `TimelineView` 时间驱动（**不要**改回 `@State` + `repeatForever`）。
> - 控制台渲染已统一（P2-6）：解析 `Sources/OrzMCFoundation/ConsoleText.swift`、渲染
>   `Sources/OrzMCDesignSystem/ConsoleText.swift`，规则见
>   [`swift/app/docs/console-rendering.md`](swift/app/docs/console-rendering.md)。
>   ⚠️ 解析按 **Unicode 标量**遍历（Swift 把 `"\r\n"` 当一个 Character）；行尾 `\r` **不能**丢掉整行。
> - 文案：改 `Localizable.xcstrings` 后必须过 `check-localization.py`（已含"占位符数量/顺序一致"守卫，
>   写反会让 `String(localized:)` 崩）。
> - 真机验收链路：凭据在 `swift/app/scripts/dev/uitest-secrets.env`（**gitignore，永不入库**）；
>   真机装包 `scripts/dev/install-ios-device.sh`（`--release` / `--ipa` / `--app`）、
>   归档/TestFlight `scripts/release-ios.sh`（详见 [`swift/app/docs/ios-release.md`](swift/app/docs/ios-release.md)）。
>   **必须在 Terminal.app 里跑**（后台会话拿不到钥匙串，`codesign` 会 `errSecInternalComponent`）；
>   AI 会话的做法：写一个 `.command`，`open -a Terminal` 投递到图形会话，再轮询日志。
> - iPhone SE3 UDID `00008110-0001712226A0401E`；模拟器 `OrzMC-UI` = `571ACD8A-64EB-4427-B803-D41836EB2B9F`。
> - iOS 分发（TestFlight）**暂不做**；要开时：加 3 个 secret（`IOS_DIST_CERT_P12` /
>   `IOS_DIST_CERT_PASSWORD` / `IOS_PROFILE`，脚本已支持 manual signing）或把 ASC API key 提到 Admin。
> - 下次发版：改 `Config.xcconfig` 版本/build + 写 `docs/release-notes/<版本>.md`，PR 合入后
>   `gh workflow run release-app.yml --ref main`（无 dry-run 输入）。
> - ⚠️ 磁盘曾差点写满（`lipo: No space left on device`）：已清掉 4 个废弃
>   `~/Library/Developer/Xcode/DerivedData/OrzMC-*`（约 8GB）；若再遇到，先清这些再重试。

## 1. 当前焦点（Current Focus）

| 项 | 内容 |
|---|---|
| **主题** | **远程托管多账号与实例 UI**（维护者最新要求：先 Mac，用 Mac 凭据在模拟器开发；真机之后统一验收）：原交接文档 [`swift/app/docs/ui-handoff-2026-10-30.md`](swift/app/docs/ui-handoff-2026-10-30.md)。0.1.7 发版排在这轮之后 |
| **状态** | 🟢 多账号 PR [#123](https://github.com/OrzMC/OrzMCApp/pull/123) 已 squash 合入（app `84325973`），完整 Mac 门禁、整套模拟器 UI 与必需 CI 全绿。Mac 开发包已安装；0.1.6 (58) 仍是当前已发布版本，未发版 |
| **待办看板** | 本轮看 [`swift/app/docs/ui-handoff-2026-10-30.md`](swift/app/docs/ui-handoff-2026-10-30.md) §4（UI-1..UI-6）；历史 [`swift/app/docs/backlog-2026-10-25.md`](swift/app/docs/backlog-2026-10-25.md) 已全 ✅ |
| **swift/app 基线** | `swift/app` `main` = `84325973`（多供应商多账号与实例展示 + Terminal 启动修复）；`swift/lib/MCSManagerAPI` = `061866f`（tag **0.5.0**）；`swift/lib/OrzMCKit` = `f004baa`；父仓库 `main` 见 `git log -1` |
| **已知坑** | ① **真机 XCUITest 可用**：必须**插数据线**（Wi-Fi 下会 `DTX 握手被拒/exit 74`；首次还需设备允许「自动化模式」，保持解锁亮屏）；`run-ios-ui-tests.sh --device <UDID> --detach` 一条命令跑完并回传结果。② 真机签名必须经 Terminal.app（脚本已用 `--detach` 自动处理）。③ 升 `Package.resolved` 版本后报 `Couldn't check out revision`：`scripts/dev/refresh-package.sh <包名>`。④ 降级依赖 pin 后 `scripts/dev/purge-package-cache.sh <包名>`。⑤ `check.sh --changed` 按改动范围选档。⑥ **真机已知失败**：`testStatusBadgeKeepsSpinningAfterReentering` 在 iPhone SE3 / iOS 27.0.1 上必失败（像素哈希判动画，模拟器绿，**app `main` 上同样失败**，与本轮改动无关，待单独跟）。⑦ 单个 UI 用例复跑：`UI_ONLY_TESTING=OrzMCUITests/<类>/<用例>`；⑧ **验收装开发包**：`swift/app/scripts/dev/install-dev-app.sh [--release|--no-build|--accept|--restore]`（10~20 s，覆盖装 `/Applications`，不要为验收去跑公证）。 |
| **下一步（下次开工就从这里开始）** | 维护者先验收已安装的 Mac 远程托管账号页；实现与验收细节见 [`swift/app/docs/remote-accounts-2026-10-30.md`](swift/app/docs/remote-accounts-2026-10-30.md)。原 UI-1 真机判据、UI-3 停止秒数及大字号全面巡检尚未完成，真机由维护者后续统一验收。本轮不发版 |
| **开放决策** | 已拍板：多供应商 UI **按供应商分组**；MCSM 走独立 OpenAPI 依赖；抽象层在 API 之上；能下沉就下沉到 `Sources/*` |

## 2. 状态快照（Repo State）

> 最新接力分支：`feat/ui-refresh-handoff`；本轮仅 bump `swift/app` 到 `b13b422`（远端 app 分支 `feat/ui-refresh`）。以下历史表格不作为当前 Git 指针依据，实际以 `git ls-tree HEAD` 为准。

### 2.1 父仓库（OrzMC）

| 项 | 值 |
|---|---|
| 分支 | `feat/ui-refresh-handoff`（相对 `origin/feat/ui-refresh-handoff` ahead 6；勿强制同步或覆盖） |
| 工作区 | **有未提交改动**：`AGENTS.md`、`CONTRIBUTING.md`、`HANDOFF.md`、`docs/README.md`、`docs/cli-comparison.md`、`docs/iteration-efficiency.md`、`scripts/dev/prepush.sh`；删除 `scripts/air/run.sh`；新增 `docs/github-iteration-workflow.md`、`scripts/swift-check.sh`；`swift/app` 与 `tools/OrzMCBackup` 子模块亦有改动。以实时 `git status` 为准，勿清理。 |
| app 子模块（未提交） | `feat/ui-refresh` @ `b13b422` 之上：新增 11 个源码文件（`ExarotonSocketDelegate`/`ExarotonMemorySection`/`ConsoleHeader`/`ConsoleInputRow`/`ConsoleWindowView`/`ConsoleTarget`/`DetailInstance`/`DirectoryRow`/`FormSectionHeader`/`InstanceSection`/`PluginSheetTarget`）与 4 个纯逻辑件（`ConnectionEpoch`/`RemoteStreamPlan`/`RemoteActionGate`/`ServerMemoryState`/`ConsoleFollowState`）+ 5 个测试文件；`BasicInfo.swift` 由 626 行拆到 6 个文件。**未提交、未推送、未 bump 父仓库指针**。 |
| 父仓库 CI | ✅ `.github/workflows/ci.yml` → `python3 scripts/verify/check.py` |
| 已删除（历史） | `GEMINI.md`、`.cursor/rules/` |

> ⚠️ 父仓库禁用 `git add -A`/`git add .`——会误暂存**所有**子模块指针（曾误将 `plugin` 的 develop 记入），**始终显式 `git add <路径>`**。

### 2.2 子模块记录指针（`git ls-tree HEAD`，钉 `main` 发布线）

| 子模块 | 记录指针 | 说明 |
|---|---|---|
| `plugin` | `5eadd6e` | 本地常检出 `develop`（`bd908b8`）→ `M plugin` **预期，不要 bump** |
| `python` | `5e70745` | `OrzPythonMC`；**2.13.0 已发布**（6 资产）；**`fix(app)`**：非 macOS 一律 `E_UNSUPPORTED`（原 `E_RUNTIME`）；**2.18.0 已发布（含 `auth.lock` 跨进程锁 + runtime 回滚）**；`feat(runtime)` 转发通道 + `orzmc runtime status|install`；`feat(conformance)`：`default_state_dir(environ=, is_windows=)` 接缝 + `statePaths` 适配器操作；`ledger` 台账校验 + 命令面 `--strict`；**`fix(download)`（`#98`）**：`HttpStatusError` —— 4xx/5xx 不重试且保留 requests 原文，续传 416 且已取全按成功；`JavaEnv` 404 补「上游缺该平台构建」提示；验收 harness 的 `log_contains` 改去全部空白（rich 软换行不再切断标记）；根 `conftest.py` autouse 钉 `ORZMC_RUNTIME=python`；**`docs`（`#100`）**：CLI 验收脚本路径同步到父仓库 `scripts/accept/cli.py`；**`docs`（`#101`）**：合规标记注释点明单一事实源在父仓库；**2.18.1 已发布**（PyPI 双包 + 6 资产 + Release notes） |
| `swift/app` | `aa22c90a` | `OrzMCApp`；**0.1.5 (57) 已发布**，`main` 已积累 15 个提交待发 **0.1.6**；**P2-7 五步完成**：供应商抽象层 + `RemoteStatusCenter` + MCSManager 只读接入 + 动作/控制台 + 面板增删改（普通用户/管理员两种 key 均验） |
| `swift/lib/OrzMCKit` | `6944afb` | **Swift 引擎 + `orzmc` CLI**；**`v0.19.0` 已发布**（六资产；**Linux 自包含**：静态链 Swift 运行时、glibc 2.35、62–65 MB）；Windows arm64 链路（`build-windows` 双臂矩阵 + `.github/actions/msvc-arm64` + `windows-arm64` 探针）；`feat(conformance)` 把 `install.conf`/`auth.json`/补全落点收敛进 `Game.StatePaths`；`--strict` + `ledger` 三处 CI 校验 |
| `swift/lib/{MojangAPI,PaperMC,ExarotonAPI,OrzAppUpdater}` | 见 [`RELEASES.md`](RELEASES.md) | Swift 依赖（引擎依赖 + 基础设施 + 自升级），随 `swift/` 收拢；HEAD 制，本地改后各自仓库提交 → 上层 bump |
| `swift/lib/MCSManagerAPI` | `7428340` | MCSManager 面板 API 客户端（OpenAPI 生成）；tag **0.3.1**（`/api/auth` 外壳 + 去字符串时间戳 + `text/plain` 错误体 + 动作/控制台端点 + `MCSMResponseEnvelope`）；20 条测试 |
| `site`/`deploy`/`proxy`/`webmc`/`profile`/`tools/*` | 见 [`RELEASES.md`](RELEASES.md) | 均钉 `main`（`LoginSecurity`/`tools/thanos` 为 `master`） |

| `swift/lib/OrzSwiftKit` | `f35e4dc` | `OrzGeeker/OrzSwiftKit`；**0.0.20**：`ManagedProcess` 的 `send`/`terminate`/`forceKill`/`waitForExit(timeout:)`、`run(inheritStandardInput:)`；**`#1`**：`Package.resolved` 里 swift-nio 2.73→**2.104**、swift-system 1.3.2→1.8.1（都是 console-kit 的传递依赖）→ ⚠️ **构建工具链下限抬到 Swift 6.1**（见 §2.5） |

> `git submodule status` 行首 `+` = 检出与记录不一致（plugin 正常）；`-` = 未初始化。
> 2026-10-22 全量指针：`swift/app fa571e7`、`OrzMCKit 6944afb`、`OrzSwiftKit f35e4dc`、`OrzAppUpdater b23e0c4`、
> `MojangAPI c5a0ead`、`PaperMC 14df328`、`ExarotonAPI 4f5c1a2`、`python 5e70745`、`plugin 5eadd6e`、
> `tools/rust-thanos b79defb`（父仓库按 `main` 钉；
> 本地 `plugin` 常检出 `develop`，2026-10-22 起多一条 `211c203`「依赖安全告警处置」文档 —— **预期，不 bump**）。

### 2.3 验证 / 治理命令

```bash
git submodule status
git status --porcelain
python3 scripts/verify/check.py            # 父仓库组合校验（CI 同款：登记表 + 参考自检 + manifest 结构）
python3 scripts/verify/check.py --remote   # 追加：子模块指针是否在远端（需网络）
python3 scripts/sync_compliance.py --check      # 合规文案漂移校验（单一来源 docs/compliance/）
python3 scripts/verify/surface.py --self-check   # 命令面 manifest 结构自检
# 只读对比某实现的命令面漂移（--strict 时才退出 1）：
python3 scripts/verify/surface.py --implementation python \
  --command "uv run --directory python orzmc --json capabilities"
python3 scripts/conformance/run.py --list  # 列出一致性样例（当前 76）
python3 scripts/release/composition.py     # 生成发版组合表（更新 RELEASES.md 用）
# Swift 依赖仓库各自的门禁（本机工具链能编）：
swift test --package-path swift/lib/MCSManagerAPI   # MCSManager API 客户端（秒级，不联网）
```

### 2.4 远程真机验证环境（Windows）

| 项 | 值 |
|---|---|
| SSH 主机 | `win`（`WangA@192.168.0.33`，免密 key；主机名 `LAPTOP-APCBNCLR`） |
| 默认 shell | **PowerShell**（`&` 是后台运算符，注意引号） |
| 收敛工作根 | **`E:\orzmc-verify\`**（`bin/ minecraft/ tmp/ logs/`，已创建） |
| 执行助手 | `scripts/win/run.sh -c '<ps>'` / `-f <file.ps1>` / stdin；服务端 E2E 用 [`scripts/win/e2e-server.ps1`](scripts/win/e2e-server.ps1) |
| 清理 | `scripts/win/run.sh -c 'Remove-Item -Recurse -Force E:\orzmc-verify'` |

> ⚠️ `E:\orzmc` 是**生产部署**（caddy/cloudflared/database/mcsmanager），**勿动**。详见 [`AGENTS.md` §8.1](AGENTS.md)。
>
> ⚠️ **Windows 上 `uv` 坑**：默认托管目录可能残留不可信装入点（`os error 448`）→ `uv sync` 失败。
> 解决：`$env:UV_PYTHON_INSTALL_DIR="E:\orzmc-verify\uvpython"` 后 `uv sync --directory E:\orzmc-verify\src --all-packages`（`git`/`uv` 已装，无系统 Python）。

### 2.5 Swift 构建与验证

| 项 | 值 |
|---|---|
| 本地工具链 | `~/Library/Developer/Toolchains/swift-6.0.3-RELEASE.xctoolchain`（Swift 6.0.3，已装） |
| 本地 SDK | 仅 macOS 12/13（CLT）→ **`OrzMCKit` 整包无法本地编译**（OpenAPIKit 需 macOS 14 API） |
| 验证途径 | `OrzMCKit` CI（`macos-15`：`swift build`+`swift test`+`conformance`）。⚠️ **2026-10-22 起 `OrzSwiftKit` 也不能在本机编译了**：其依赖图（swift-nio **2.104** / swift-system 1.8.1）自带 `swift-tools-version:6.1`，本机 6.0.3 工具链 `swift package resolve` 直接报 `is using Swift tools version 6.1.0 but the installed version is 6.0.3`；`swift-latest`/6.5-dev 工具链又因 built for macOS 15 在 macOS 13 上 dyld 起不来。⇒ Swift 侧本地只保留 `OrzMCKit/scripts/dev/local-build.sh lint\|check`（纯静态/语法，不解析依赖）；构建与测试一律走 CI 或 Air（Swift 6.1.2 / 6.4） |
| **远程 Mac（`ssh air`）** | macOS 27 / Swift 6.4 / Xcode 27（arm64）——**可本地编译 OrzMCKit**（本机 SDK 太旧时的替代）。Swift 验证两条路：`ssh air` 本地编译 / `OrzMCKit` **CI**（`conformance` job 检出父仓库 fixtures 跑 `--strict`，权威）。构建目录 air `~/orzmc-build/{OrzMCKit,parent,OrzSwiftKit}`（`parent` 下放了 fixtures+conformance 供适配器跑） |
| Air 上的 SwiftLint 坑 | 单独构建 `OrzSwiftKit` 时，新解析的 SwiftLint 在 Swift 6.4 下编译失败（`MemberImportVisibility`）；但 `OrzMCKit` 的 `.build` 用钉住版本可正常构建 |
| 本地联调 | `scripts/swift-dev.sh {sync,edit,status,unedit,xcode}` —— 把 `swift/lib/OrzMCKit` 的依赖本地覆盖到 `swift/lib/*`（开发态、不提交；app 的 Xcode 覆盖见 `xcode` 子命令） |
| 不可用 | `swift-latest`/6.5-dev 工具链需 macOS 15；`swiftly` 在本机崩溃 |

**本地能力矩阵（2026-10-22 实测，别把它读成「CLI 本地验证没了」）**

CLI 迭代的主线是 **Python 实现**（`docs/two-cli-strategy.md` §6：唯一对外分发），它在**本机是全能的**；
Swift 侧少掉的只是「整包编译/单测」，静态与语法检查照旧，且一致性/命令面校验用 Python 适配器就能本地跑。

| 想验证什么 | 本机能不能 | 命令（实测耗时） |
|---|---|---|
| Python CLI 行为（信封/退出码/取消/补全/MCP，25 例，真实进程） | ✅ | `bin="$(cd python && uv run --all-packages python -c 'import shutil; print(shutil.which("orzmc"))')"` 然后 `python3 scripts/accept/cli.py --cli "$bin"`（实测 64s）。⚠️ **不能**写 `--cli 'uv run orzmc'`：每个用例从自己的沙箱 cwd 启动，相对路径/无绝对入口必挂（`OrzPythonMC#102`） |
| Python 单测 / lint / 类型 | ✅ | `uv run --directory python --all-packages pytest`（20s）、`ruff`、`mypy` |
| 一致性 conformance（79 例） | ✅ | `scripts/conformance/run.py --adapter "uv run --directory python python orzmc/tests/conformance/adapter.py" --strict`（几十秒，**不需要 Swift**） |
| 命令面 manifest / 能力台账 | ✅ | `scripts/verify/surface.py --self-check`、`scripts/verify/parity.py` |
| Swift 代码的可移植性 / 语法 | ✅（秒级，不解析依赖） | `swift/lib/OrzMCKit/scripts/dev/local-build.sh lint`（0.6s）/ `check`（11s） |
| Swift 整包 `swift build`/`swift test` | ❌ 本机不做 | CI `macos-15`（Swift 6.1.2）/ air（6.4） |
| Swift 侧一致性适配器、Swift CLI 验收 | ❌ 需要先构建 | `OrzMCKit` CI 的 `conformance`/`cli-acceptance` job（权威） |

### 2.6 Swift 依赖（现为 `swift/lib/*` 子模块）

> 2026-10-15 起这些仓库已作为父仓库子模块收拢到 `swift/lib/*`（路径/指针见 §2.2 与 `RELEASES.md`）。
> 消费侧（`app`/`OrzMCKit`）仍以 SwiftPM `branch=main` 远端解析；开发态用 `scripts/swift-dev.sh` 本地覆盖。

| 子模块 | 当前 | 说明 |
|---|---|---|
| `swift/lib/OrzSwiftKit` | `main`（`d71cc57`） | 基础设施：`CacheKit`/`RuntimeKit`/`TransferKit`/`JokerKits`(含 `ProcessRunner`)；CI 含 `network-smoke`；**#8 修复 `ArchiveExtractor`（`.tmp` 临时名按魔数回退）**；**#10 lint 插件改用 SwiftLint 预编译二进制（插件回归：本地/CI 每次构建自动 lint，但不再编译 swift-syntax）** |
| `swift/lib/MojangAPI` | `main`（`0f11294`） | 元数据；平台 macOS 13 / iOS 16（D12）；**版本 JSON 可选磁盘缓存（原始字节，`configurePackageCache`）**；**CI 加缓存 + 修重复触发；联网用例门控 `ORZMC_NETWORK_SMOKE`（离线确定性）** |
| `swift/lib/PaperMC` | `main`（`19ae5af`） | Paper/Hangar |
| `swift/lib/ExarotonAPI` | `main`（`1eea571`，tag `0.0.9`） | Exaroton API 客户端 |
| `swift/lib/MCSManagerAPI` | `main`（`b63c4b5`） | **新建（2026-10-25，P2-7 第 3 步）**：MCSManager 面板 API 客户端；官方无 OpenAPI，`Sources/MCSMAPI/openapi.yml` 按官方 apidoc 手写最小子集（节点列表 / 实例列表 / 实例详情）；`APIKeyMiddleware` 注 `X-Request-API-Key`；`swift test` 9 条（请求拼装 + 官方示例 JSON 解码）；`scripts/check-apidoc-drift.sh` 防官方端点改名 |
| `swift/lib/OrzAppUpdater` | tag `0.0.3`（`b23e0c4`） | 平台 macOS 13；被 app 以 tag 依赖 |

## 3. 待决策 / 开放问题

**决策（已落定）**：
- D1 不合并 `python` 与 `app` 仓库；D2 一份规范 + 多实现 + 多前端 + 一个产品伞；D3 规范落父仓库 `docs/spec/`（成熟后下沉）；
- D4 黄金样例 + 跨语言 conformance；D5/D8 `OrzMCKit` = Swift 可复用基础组件；D6 父仓库 = 产品伞；
- D7 一个 `orzmc`（CLI+GUI 两面、共核、互相安装/打开）；D9 CLI 可被 AI 调用（`--json` + `capabilities`；评估 MCP）；
- D10 依赖用 `OrzMC/*` 规范路径 + 本地覆盖仅开发态；D11 外部 Swift 依赖 **HEAD 制**；D12 `MojangAPI` 平台 macOS13/iOS16。

**开放问题**：Q1–Q7 均已决（见 [`docs/product-unification-plan.md`](docs/product-unification-plan.md) 第 7 章）。**当前无阻塞项。**

**待定（计划项，非阻塞）**：`capabilities` schema ✅（§8.1）；`orzmc mcp` schema ✅（§8.2，server 待实现）；`--json` 错误码表 ✅（§6.1）。

**待决策（需维护者拍板，均非阻塞）**
- **命令面单一化（已选路线 A）**：把 `cli-surface.md` 升级为**机器可读 manifest**（`cli-surface.json`）+ 两侧生成/校验，消除“手写两遍”的漂移成本。第一步（manifest + 只读校验器，已接父仓库 CI 自检）已落地；剩余：按 `cli-surface.md` §8.3 已知漂移清单收敛两侧，再谈 codegen。
- **`--auth` 的认证方案（已定）**：Microsoft 设备码流程；令牌存**状态目录 `auth.json`（0600）**；非 TTY 允许设备码输出到 stderr + 有界轮询；scope `XboxLive.signin offline_access`；错误码 `E_AUTH*`。契约见 [`docs/spec/auth.md`](docs/spec/auth.md)。**唯一待办：注册 Azure 应用取得 `client_id`**（公开非密钥；无卡阶段可暂用 `ORZMC_AZURE_CLIENT_ID` 覆盖）。

**已决（本阶段）**
- 版本身份：**不统一** Python 与 Swift 的版本号——Swift 走 `OrzMCKit` 自己的 release 线（当前 `v0.1.0`），Python 走 `OrzPythonMC`（`2.4.x`）。

## 4. 下一步（Next Actions，增量、非阻塞）

### ★ 下一会话起点（2026-10-20 方向调整后）

> 本轮按新决定收口：**Python 是实现主体与唯一对外分发**，**Swift 同步迭代但不对外分发**（pre-release）。
> `2.15–2.17` 的「默认走 Swift」实验已回退（`2.17.2`）；M3 归档。细节见 §5。

**A. Python 主力线（正常迭代，无阻塞）**
- 按 `docs/spec/` 正常推进功能；两套 CLI 的行为对齐仍走台账 + 三处 CI 校验（`parity.json` 不变）。
- 新功能按 `lead` 分工：引擎语义/CLI 契约 Swift 侧先行、Python 跟随；`plugin` 与分发以 Python 为准。

**B. 正版登录改道（需要先定范围，唯一需要拍板的）**
- Mojang 两次拒绝（2026-10-17 / 2026-10-20）→ 按规则不再投第 3 次。
- 待定：只支持"用户自填 authlib-injector / Yggdrasil 服务器地址"（轻），还是内置常见第三方认证（重）？
  以及它与现有 `--auth`（微软设备码）并存还是替代。
- 定了范围就写 `docs/spec/auth.md` 新一节（服务器地址 + 复用 `auth.json` + `E_AUTH*`），Swift lead、Python 跟随。

**A2. `swift/app`（GUI）迭代（用户 2026-10-20 指定下一阶段）**
- [x] 代码审查 + 四步重构（P0 / 拆模型 / 视图瘦身 / 多实例），`OrzMCApp#29`。
- 车道已就位：`scripts/air/run.sh app`（增量 ~17s）。
- 现状：GUI 已收敛到引擎（`launchClient`/`downloadClient` 共用、服务端四类型、结构化进度、托管 JRE，
  `#25`）、设置页可反向安装/查看 `orzmc` CLI（`#26`，`ORZMC_SURFACE=gui`）。
- [x] `install.conf.surface` 接通（`#27`）；[x] iOS 进 CI + 平台分层（`#28`）。
- 用户已定：**登录界面先不动**（等 authlib-injector 方向）。

**C. 小加固**
- [x] **`auth.json` 跨进程写锁**（`frontends.md` **F4.1**，2026-10-20）：`<stateDir>/auth.lock` 目录锁，
      **两侧算法逐字一致**（mkdir 原子 / 陈旧 30s / 超时 10s → `E_AUTH_LOCKED`）；刷新改为「持锁 → 锁内重读 → 需要才刷」。
      Python `OrzPythonMC#96`（2.18.0）、Swift `OrzMCKit#89`（0.20.0）。
- [x] **`runtime` 真身损坏回滚**（`install-update.md` §10.1）：安装留 `.bak`、运行前魔数预检、执行失败回滚重试一次；
      顺带修「自己的 payload 被误判可复用 → 永远无法升级」。
- [ ] Swift Linux 体积（65 MB）继续探索压缩（`--gc-sections` / 评估去掉 ICU）；纯实验收益，不急。
- [ ] （建议）跨语言并发冒烟：Python 与 Swift 各持锁一次，确认互斥真实生效（两侧算法一致但没做过联测）。

**接手时最容易踩的坑（更新）**
1. **git 钩子不入版本库**：新机器必须 `scripts/dev/install-hooks.sh`。
2. **`ssh air` 会休眠**：`ssh air true` 超时 → 先唤醒；构建优先 `scripts/air/run.sh`（14–24 秒）。
3. **`parity.json` 是硬约束**（Swift 虽不对外分发，但**仍要同步迭代**，差异照样会让 CI 红）。
4. **别用「跳过工作流」省 CI**：必需检查不上报 = PR 永久 BLOCKED。
5. **dry-run 不要带旧 tag**（`release.yml` 用 `inputs.tag || github.ref` checkout）。
6. **release-please 不为 `build:`/`docs:`/`ci:`/`chore:` 升版本**：要发就加 `Release-As: X.Y.Z` footer。
7. **凡是"直接跑 `orzmc`"的 CI/脚本都要钉 `ORZMC_RUNTIME=python`**（默认已是 Python，但钉住能防止实验开关误开）。
8. **Python 侧 ruff 禁全角标点**（RUF002/RUF003）。
9. **`GITHUB_TOKEN` 建的 PR 不触发 `pull_request` 工作流** → release PR 没 checks 是常态，close/reopen 补触发。
10. **Swift 的 Release 全是 pre-release**：`releases/latest` 返回 **404**（历史 22 个也已转换）→
    OrzMCKit 自带的 `install.sh`/`install.ps1` **必须显式给版本**；实验通道（`runtime`）已改为列 Release 取最新
    （实测可拉到 pre-release 的 `0.19.0` 并安装）。

> **★ 下一会话起点（2026-10-15 交接）**：本地 `--auth` 离线部分（阶段 A/B/C，三适配器 73/73）与
> **`orzmc mcp` server（两端）均已完成**。真实登录 E2E 等办卡/注册后再做（待办 A）；
> 无阻塞时可选推进「命令面单一化」（§4 可选/治理）。
>
> **待办 A — 正版授权 `client_id`（2026-10-15 进展）**
> - [x] A1. 注册 Azure 公共客户端应用（`组织目录 + 个人账号`，`Allow public client flows = Yes`）→ `client_id = 1a3e628b-c9a5-4a7f-b7b7-562e22b9787e`。
> - [x] A2. 内置两端：Python `orzmc/core/auth.py` `DEFAULT_CLIENT_ID` / Swift `Game/Auth/AuthConfig.swift` `defaultClientId`（保留 `ORZMC_AZURE_CLIENT_ID` 覆盖）；已合并（python #54 / OrzMCKit #27）。
> - [x] A3a. **真实 MSA→XBL→XSTS 验证通过**（设备码 → MSA 令牌 → Xbox Live RPS → XSTS 均 200；Xbox 档案可读）。
> - [x] A3b. **已提交 Mojang Game Service API 申请**（2026-10-16，类型 New AppID for Approval）；提交回执（Microsoft Forms 提交 ID）`v4j5cvGGr0GRqy180BHbR-ajEQ1td1ROpz00KtS8Gd5UNVpPTkVLNFVROVQxNkdRMEtXVjNQQjdXVC4u`；官方免责声明已加（父仓库/各子模块 README、官网 `site-footer.html`、App `SettingsView` Disclaimer）。待人工审核（结果通常发到联系邮箱）；通过后做 A4。
> - [x] A3c. **Mojang 审核结果：被拒（2026-10-17）**——Mojang Enforcement（`MCENotify@microsoft.com`）称本批 appID **未获批准**（未进 API 白名单），同批另有违规应用被处置，并明确**不提供申诉/咨询/排障**。⇒ `login_with_xbox` 仍 `403`，内置 `client_id` **实际不可用**。
>   - **门的位置（已核实）**：只有 ⑤ `api.minecraftservices.com/authentication/login_with_xbox` 需要 Mojang 白名单；①–④（微软 OAuth / Xbox Live / XSTS）任何自注册 app 都能用。Prism/HMCL 能用是因为它们的 client ID **已在名单内**（旁证：`mlcmLauncher` PR #7 先前用的是 **Prism 的 client ID**）。
>   - **不做**冒用官方 client id 等规避（违反 EULA）。
> - [~] A3d. **第 2 次提交（launcher-only，仅改材料）**：把申请表述收敛为 **launcher-only**（第 1 次把 server-management 与启动器并列，对方回信却在讲 “3rd party server” → 疑被归类分流）。**不改产品、不改 appID、不改实现**。
>   - **2026-10-17 已提交**；结果等邮件（发到表单里的联系邮箱）。提交后的返回页就是**表单页面本身**（`forms.cloud.microsoft/...ResponsePage.aspx?id=v4j5cvGG…`）——**没有可引用的提交编号**。
>   - 参照第 1 次（2026-10-16 提 → 2026-10-17 出结果）：约 1 天一批；若两周无邮件，按未通过处理。
>   - **无论结果如何不再投第 3 次**；未通过即转 authlib-injector / Yggdrasil。
> - [ ] A4. **真实账号 E2E：被 A3c/A3d 阻塞**（需账号有 Minecraft Java 版）。仅在路线 A（authlib-injector / Yggdrasil）落地后才好验证。
> - [x] A5. 推送已完成（python/OrzMCKit 先，父仓库 auth fixtures 随后；见 §5）。
>
> **待办 B — `orzmc mcp` server（不依赖 `client_id`）✅ 已完成（2026-10-15）**
> - 规范：`cli-surface.md` §2/§4/§8.2/§10 已定稿（stdio 换行分隔 JSON-RPC 2.0；`initialize` / `tools/list` / `tools/call`；tool 排除集 `capabilities`/`completion`/`mcp`/`self-uninstall`；RPC 错误码）。
> - [x] B1. 规范：`mcp` 纳入 §2 命令总览 + §4 契约，§8.2 由「计划」改为「Python ✅ / Swift ✅」。
> - [x] B2. Python：`orzmc_app/cli/mcp.py`（JSON-RPC + `tools/*`）+ `cli/introspect.py`（`capabilities`/`mcp` 共用内省）+ `orzmc mcp` 子命令；`tools/list` 由 `capabilities` 生成，`tools/call` 用 `typer.testing.CliRunner` **进程内**转调 `--json` 路径；零新增依赖。
> - [x] B3. 离线测试：`orzmc_app/tests/test_mcp.py`（14 例：`initialize`/`tools/list`/`tools/call` 成功与 `isError`/参数校验/帧与通知）；`ruff`/`mypy`/`pytest`（382 passed）/`uv build` 全绿。
> - [x] B4. Swift：`MCPServer.swift`（可注入 runner；默认 `orzmc --json <cmd>` 子进程）+ `Commands/MCPCommand.swift` + `CommandGroup` 注册；`capabilities` 补 `schemaType`/`required` 并修正位置参数名（不再误加 `--`）。`ssh air`：`swift build` 绿、`swift test` **46 例**绿、真实 `orzmc mcp` 冒烟（initialize/tools list/call/parse error）通过、conformance **73/73**。
>
**T1 端到端实跑（进行中，降最大风险）**
- [x] **macOS 实跑**（Python `orzmc`）：真实下载 Java17 + 服务端 → 世界生成 → `stop` 优雅停止 → 退出码 0；顺带发现并修复「流式中途断连不重试」。
- [x] **Windows 真机**：经 `scripts/win/e2e-server.ps1` 跑通同流程（1.20.4 vanilla：下载→启动→`Done (`→`stop`→退出码 0、无残留 java；root 236MB）。
- [x] **Swift 冒烟**：`OrzSwiftKit` 新增真实网络下载测试（`TransferNetworkSmokeTests`，`ORZMC_NETWORK_SMOKE=1` 触发）+ CI `network-smoke` job；单流与 2 路 Range 均通过。

**新发现（已修复）**
- [x] **Swift `Transfer` 无运行内重试**：已在 `OrzSwiftKit` 补**运行内有界重试**（`TransferPolicy.maxAttempts`，默认 4；失败保留 `.part`/`.partN`，`Range` 续传；size/hash 校验不重试）。`OrzSwiftKit#5`（`5c05337`）+ `OrzMCKit#13` 跟进 `Package.resolved`。

**T2 统一 CLI 命令面（进行中）**
- [x] **Swift 选项收敛**：`--debug→--verbose`、`--ms/--mx→--min-mem/--max-mem`、`--gui→--nogui`、`--force_upgrade→--force-upgrade`、`--jar-opts→--server-args`；去掉 `defaultCommand`（无子命令打印帮助）。
- [x] **Swift 补命令**：`version`/`list`/`remove`/`backup`/`completion`(bash/zsh)/`capabilities`/`update`/`self-uninstall`/`app` ✅；`fabric` 隐藏别名 ✅；全局 `--version`/`--verbose`/`--root-dir`/`--json` ✅。**Swift CLI 命令面已全部对齐规范。**
- [x] **Swift CLI 发行化（D13）**：release-please + `release.yml`（tag→`orzmc-macos-{arm64,x86_64}` + SHA256SUMS）+ `scripts/install.sh`；README（#6）。
- [x] **Python 全局项**：`--version`/`--root-dir` 全局；内存选项规范名 `--min-mem/--max-mem`（旧名别名）。
- [x] **Python `--json` 信封**（D9 AI 调用核心）：全局 `--json`，`{ok,command,data,error}`，日志/进度转 stderr。
- [x] **Python `completion`**：`orzmc completion <shell>` / `install`（typer `add_completion=True`）。
- [x] **Python `capabilities`**（D9 能力发现）：内省输出命令/选项/退出码/信封 schema。
- [x] **Python `plugin`/`app`**：`plugin` 吸收自 Swift（Hangar 搜索/列表/下载）；`app` 跨面 GUI（macOS）。全局 `--auth`（正版授权，需库支持）仍待办。
- [x] **Swift `list`/`remove`**：引擎 `installedVersions`/`removeInstalled` + CLI 命令（#3）。
- [x] **Swift `backup`**：引擎 `GamePlan.backupWorld` + CLI 命令（#4）。
- [x] **Swift `version` + 全局选项**：工具版本单一事实源 `Game/OrzMCVersion` + `version` 命令；全局 `--version`/`--verbose`/`--root-dir`/`--json`（ConsoleKit 之上预解析 argv）；`--json` 信封；`ClientInfo`/`ServerInfo` 贯通 `rootDir`；无子命令退出 0；服务端 `--type` 缺省 vanilla（#5）。

**其他**
- [x] **规范收尾**：`cli-surface.md` §6.1 补**错误码表**（E_USAGE/E_UNSUPPORTED/E_UNSUPPORTED_TYPE/E_VERSION_NOT_FOUND/E_NOT_FOUND/E_VERIFY/E_NETWORK/E_CANCELLED(130)/E_INTERNAL/E_RUNTIME）；§8.1 `capabilities` schema（已实现）/§8.2 `orzmc mcp` schema（已实现，两端）；Python/Swift 用户取消退出码统一为 **130**。
- [x] **Phase 4｜`downloadClient` 收敛**：`Downloader.download` 加 `onProgress`（`OrzSwiftKit#6`）；引擎新增 `Client.downloadClient(onProgress:)`（`OrzMCKit#14`）；CLI `Launcher.download()` 与 GUI `GUIClient.download()` 共用（`app#16`）。
- [x] **一致性｜新增操作**：`planClientDownload`（客户端下载清单）与 `normalizeExit`（B7 退出码归一，暴露并修了 Python 服务端退出码未归一的分叉）；参考 + Python + Swift 三适配器 **53/53**。
**剩余项（下一会话，非阻塞）**

- [x] **App Phase B** —— `install.conf.surface`（规范 §3.1 + 两通道 + GUI 读/写）、GUI 反向安装 CLI
  （设置页 Command Line 区块）；详见 §5。
- [ ] **App Phase C（暂停）** —— GUI 认证 UI：**维护者已定（2026-10-17）先等 Mojang 第 2 次申请的邮件回复**，
  不提前实现（路线未定时做会返工）。
- [ ] **下次 OrzMCKit 发版**：Release notes 补「升级须知」——此前 Swift 通道安装记录 `version` 字段可能被合规声明污染，
  重跑安装器即可（见 §5）。
- [ ] **`--auth`（正版授权）** —— **离线优先**（安全敏感；`client_id` 依赖项待维护者注册）。
  - 现状：`--auth` 两端**离线链路已实现**（阶段 A/B/C ✅：契约 + 纯映射 + 令牌存储/设备码编排 + CLI 接线）；仅剩阶段 D（注册 `client_id` 后的真实 E2E）。
  - **[x] 阶段 A（父仓库，已完成）**：`docs/spec/auth.md` 定稿（Microsoft 设备码流程 → XBL → XSTS → MC → profile；令牌模型/持久化/刷新；非 TTY/`--json`；错误码 `E_AUTH*`；安全红线）；`reference.py` 新增 **13 个 `auth*` 纯映射操作**；`docs/spec/fixtures/auth/` **20 例**（参考适配器 **73/73**）；同步 `cli-surface` / `data-model` / `install-update` / `conformance` / `fixtures README`。
  - **[x] 阶段 B（Python，离线，已完成）**：`orzmc/domain/auth.py` + `orzmc/core/auth.py`（纯映射）+ `orzmc/infra/auth_store.py`（原子写 0600）+ `orzmc/services/auth.py`（设备码编排）+ `RuntimeOptions.auth_*` + 启动参数注入 + CLI `client --auth` + 适配器；`ruff`/`mypy`/`pytest` 绿，一致性 **73/73**（strict）。
  - **[x] 阶段 C（Swift，离线，已完成）**：`Game/Auth/{AuthModel,AuthMapping,AuthStore,Authenticator}.swift` + `ConformanceAdapter` 的 `auth*`（**73/73**）+ `ClientCommand --auth` 接线 + 修 `Client+Boot` 离线默认值（`auth_access_token=0`/`user_type=legacy`/`auth_xuid=""`/`clientid=""`）；`ssh air`：`swift build` + 35 单测 + CLI 冒烟（`--json client --auth` → `E_AUTH_NOT_CONFIGURED`）全绿。
  - **[ ] 阶段 D（`client_id` 依赖，待办卡+注册）**：维护者注册 Azure 公共客户端应用（组织目录 + 个人账号、Allow public client flows），提供 `client_id`；写入两套实现内置默认值；真实账号 E2E（需 Minecraft Java 拥有权）→ 记入本文件。当前 `client_id` 仅支持 `ORZMC_AZURE_CLIENT_ID` 覆盖。
  - **⚠️ 合入顺序（避免子模块 CI 红灯）**：`auth/*` fixtures 已在父仓库工作区；**Swift CI 检出父仓库 main 并 `--strict`**。Python/Swift 的 `auth/*` 适配器改动**仅在本地**，所以**在子模块变更推送/合并前，勿把 `auth/*` 合入父仓库 main**。建议：先推子模块（其 CI 检旧 fixtures，绿）→ 再合父仓库 auth fixtures。
- [x] **`orzmc mcp` server**（已完成，见上「待办 B」）—— schema `cli-surface.md` §8.2：`initialize`/`tools/list`/`tools/call`，stdio JSON-RPC 2.0；每端一个 `orzmc mcp` 子命令，`tools/list` 由 `capabilities` 生成，`tools/call` 转调 `--json` 路径。

**可选 / 治理（非阻塞）**
- [x] **命令面单一化（路线 A）** —— 已落地：`docs/spec/cli-surface.json`（机器可读 manifest + `deviations` 收敛 backlog）+ `scripts/verify/surface.py`（结构自检接 `check.py`/父仓库 CI）。**两侧 `--strict` 均 0 未声明、0 已声明漂移**（Python/Swift 完全一致）；**Swift 侧 `--strict` 已接 `OrzMCKit` CI**（`conformance` job 构建 `orzmc` 导出真实 `capabilities` 后对比）。**已收敛**：Python 全量；Swift `client --type`（vanilla/fabric/forge）、`server`/`remove`/`self-uninstall` 各选项（详见 `cli-surface.md` §8.3）。**codegen 评估结论：暂不做代码生成**（保留 manifest + `--strict`；理由与重估触发条件见 `cli-surface.md` §8.3）。
- [x] **一致性再扩（“彻底”）**：① `planLayout` 无 `type` 时省略 server 字段（新增 `layout/no-type-1.20.4`）；② `planClientLaunch`/`planClientDownload` 版本源统一为显式 `given.version`（新增 `*/mismatched-version-id`）。运行器新增 `absent` 断言；参考/Python/Swift 三适配器 **76/76**（Swift 适配器接缝覆盖 `id`、无 type 不产 server 字段）。
- [x] **Python 侧反向对齐**：三适配器 **76/76** 全绿，无新增分叉。
- [x] **Windows 真机实测**：T1 已完成服务端 E2E；CLI 新增的 `plugin`/`app`/`mcp` 无 Windows 侧差异（`app` 仅 macOS），未额外跑。
- [x] **治理｜外部依赖**：已核（2026-10-15）：`OrzSwiftKit`@`fd88d7d`、`MojangAPI`@`bb8dbe8`、`PaperMC`@`19ae5af`（均 `main` HEAD）；`OrzAppUpdater` 最新 tag `0.0.3`（app 要求 `>=0.0.2`，CI 删 lock 重解析）。

> 历史（本会话已完成）：Phase 0/1/2/3 全部、Phase 5 治理（`RELEASES.md`+`check.py`+父仓库 CI）、Phase 4 起步（`launchClient`）、
> 一致性套件 26→31 例、`GameDir` 退役、Java 托管、`TransferKit`（含续传/进度/离线测试）、B7 生命周期、B9 非 TTY、B11 错误语义。

## 5. 会话日志（Session Log，只追加，最新在最上）

### 2026-10-30 — Codex（远程托管多账号、界面复用与 Terminal 启动修复）

- 维护者明确扩大范围为“每个供应商多个账号、每个账号多个实例”；之后指定先做 Mac，使用 Mac 凭据在模拟器开发，真机验收留待之后统一进行。
- app 分支 `feat/ui-polish-remote-accounts` 已推送，PR [#123](https://github.com/OrzMC/OrzMCApp/pull/123)；实现 exaroton 账号 UUID + 独立 Keychain + 独立模型，旧 Token 成功迁移后才删除，迁移失败保留旧凭据。MCSM 同一地址支持不同凭据。供应商标题、账号标题、表单框架及实例名称/徽章布局共用；独有能力特化，不操作真实服务器生命周期。
- `check.sh` 完整门禁通过；新增迁移失败保护与账号隔离单测通过。模拟器多账号、详情自动进入、Mac 真实凭据页面和截图巡检共 4 项定向全绿；最终整套 `check.sh --ui` 全绿（含旋转徽章重入），PR 必需 CI 全绿。改前/改后和账号截图已随 PR 保存到 `swift/app/docs/ui-remote-accounts/`。
- Mac 开发版已安装到 `/Applications/OrzMC.app`（保留原安装备份），`install-dev-app.sh --accept` 退出 0；管理员／普通用户两账号各两台实例，四路只读控制台流均 LIVE。真实 Mac 面板凭据经进程环境注入模拟器，已只读验证相同两账号与实例，不复制或提交凭据。
- Terminal 故障已定位为沙箱中的 LaunchServices 限制：名称查询失败，完整路径也可能误报可执行文件缺失；沙箱外成功。与 Ghostty 默认终端无关。脚本使用系统完整路径并明确沙箱外执行要求，`.command` 写回探针和开发版安装均验证通过。
- 原 UI-1 真机判据、UI-3 exaroton 停止进度及大字号全面巡检未标完成。未发版；PR #123 已 squash 合入 app `84325973`，本次父仓库显式 bump `swift/app` 指针到该远端 main 提交。
- 父 CI 首次失败暴露检出配置遗漏：原来只检出 Python/OrzMCKit，却对 app 与其余 Swift 库执行声明审计，导致缺文件误报平台下限。已补齐 9 个浅检出的必要输入，不弱化审计、不检出全部 22 个子模块。

### 2026-10-30（十二）— pi（子模块全量同步）

- 逐个 `fetch` 对比 22 个子模块：**只有 2 个落后远端**，其余全部已与 `origin/<branch>` 一致
  （`tools/thanos` / `tools/LoginSecurity` 按 `master` 比对，也已一致）。
- `deploy` → `acae452`（`v0.1.2-1`，落后 24 个提交）：**v0.1.0 破坏性变更** ——
  `DATA_ROOT` 取消默认值必须显式 `-d`、边缘层删除、面板中转成唯一拓扑、`MC_PUBLIC_TCP/UDP` 显式声明（ADR-034）。
  ⚠️ **实际部署升级要按 `deploy/CHANGELOG.md` 迁移**，父仓库 bump 只是记录组合。
- `swift/lib/ExarotonAPI` → `bd96526`（tag `0.0.10`）：补 `TRANSFERRING(9)`、未知状态码退化解码（避免整条消息解码失败）。
- `RELEASES.md` 顶部基准组合刷新为 **2026-10-30**，并写明 deploy 的破坏性升级提示。
- `scripts/verify/check.py` 全绿（PASS=79 FAIL=0）。**未跑** deploy 的 docker 门禁（其 CI 已在上游跑过）。
- 之后写 **UI 优化 + 验收交接文档** `swift/app/docs/ui-handoff-2026-10-30.md`（`swift/app` @ `a5dd650a`），
  含环境事实、UI-1..UI-6 候选任务、红线、验收协议（`check.sh` 各档 / 真机 `--detach` / 截图巡检导出 /
  `install-dev-app --accept`）与可直接复制的 Codex 提示词。

### 2026-10-28（十一）— pi（B2 强杀 + 停止进度；验收改开发包）

**B2 落地**
- `MCSManagerAPI` **0.5.0**（PR #2）：`GET /api/protected_instance/kill`；官方 apidoc 已收录 →
  drift 检查 `[ok]`；`/kill` 的 200 **不声明响应体**（实测 `data` 结构不固定：官方写
  `{instanceUuid}`，10.18.0 实际是 `{instanceUuid, instances:[…]}`），声明 schema 会解码失败；
- app PR #122：`RemoteServerAction.kill`（`pendingState = .stopping`，`canPerform` 只要不是
  `offline` 就给 —— 唯一允许在自己过渡态执行的动作）、`RemoteStopProgress`（<30s/30–60s/≥60s）、
  `stopRequestedAt` 记账、`⋯` 菜单「强制终止」（destructive + 二次确认）、停止中秒数 +
  久等行内强杀按钮（`TimelineView` 秒级重绘）；exaroton 抛 `actionNotSupported`。

**⚠️ 现场记录（重要）**
1. 我用 curl 直接探 `/kill` 时对**运行中的 FoliaMC** 发了请求 → 服务器**真的被杀掉**
   （请求挂到 30 秒超时 = 面板的 `INSTANCE_KILL_TIMEOUT`）。随后用 `/api/protected_instance/open`
   重新启动，`{"status":200}`，实例已回到 **online**。教训：**不要在运行中的实例上探破坏性端点**，
   要探就用已停止的实例（我第一步就是用 PaperMC 探的，那步是安全的）。
2. 笔记里那把 key（`064118…`）现在已经 **403「密钥不正确」**；**钥匙串里那把（len 32）仍然有效**。
   以后取值一律 `security find-generic-password -s com.joker.OrzMC.credentials -a mcsm.panel.<uuid> -w`
   （Terminal.app 里跑）。

**验收方式（已固化）**：`swift/app/scripts/dev/install-dev-app.sh --accept` —— 装开发包到
`/Applications` + 无界面自检，退出码 0；本轮实测面板两个都 `err None`，实例状态 `FoliaMC online`。

### 2026-10-27（十）— pi（验收改为装开发包）

**动因**：每次验收都在等 Apple 公证（Release → 签名 → notarize 9 min → dmg → 装 dmg → 断言，
一轮 10~15 min）。验收要验的是"装好之后能不能用"，跟公证无关。

**落地** `swift/app` PR #121 → `47dd131c`：`scripts/dev/install-dev-app.sh`
- Debug（默认）/`--release` 开发签名构建，复用 `OrzMC-local`；打印版本 / 架构 / minos / 签名主体；
- 备份现有 `/Applications/OrzMC.app` 到 `~/Library/Caches/orzmc-app-backup` → `ditto` 覆盖 →
  `codesign --verify --deep --strict` → `open -a` 启动并确认进程；
- `--accept` 装完跑无界面自检（面板列表 + 控制台实时流）；`--restore` 还原正式版；
- 边界写死：不公证/不打包/`spctl` 必报 rejected 属正常，发版门禁仍是 `release.sh` 的 dry-run。

**实测**（Terminal.app）：构建 → `0.1.6 (58)` / `arm64` / `minos 14.0` / `Apple Development: zhizhou wang`
→ 备份 → 装 `/Applications/OrzMC.app` → 签名校验 → 自检退出码 **0**。

**⚠️ 环境**：自检时两个面板都报 `HTTP 530 / error code 1033` —— **面板的 cloudflared 隧道此刻没起**
（`curl https://mcs.jokerhub.cn` 同样 530）。代码侧 B1 已在前一轮用真面板验过；面板恢复后
`install-dev-app.sh --accept` 可直接复跑。

**两个新坑**
1. `vtool … | awk '/minos/{print $2; exit}'` —— awk 提前 `exit` 让 vtool 吃 SIGPIPE，
   `set -o pipefail` 下整个脚本返回 141、半路死掉（表里看着像"构建完成就退出"）；
2. bash 3.2 按字节解析变量名：`say "（$CONFIG，…）"` 会把全角逗号吞进变量名 →
   `CONFIG，: unbound variable`。**紧跟非 ASCII 一律 `${VAR}`**（本轮又踩一次，已全脚本扫过）。

### 2026-10-27（九）— pi（B1：MCSM 控制台实时流）

**协议调研**（`MCSManager/MCSManager` 源码 `panel/src/app/routers/instance_operate_router.ts` +
`frontend/src/hooks/useTerminal.ts`）：`POST /api/protected_instance/stream_channel` → `{addr, password, prefix}`，
then socket.io（Engine.IO v4）：`stream/auth {data:{password}}` → `{data:true}`，之后 `instance/stdout {data:{text}}`。
面板有 `dataPlane=direct|proxy` 两种模式；**我们的面板是 direct**（返回节点地址 `wss://mcs-node.jokerhub.cn:443`，公网可达）。

**落地**
- `swift/lib/MCSManagerAPI` **0.4.0**（PR #1）：新 product `MCSMStream`（帧编解码 + 地址解析 + 客户端，
  零依赖）＋ spec 加 `stream_channel`；20 条测试，含**测试内起真 WebSocket 服务端**的端到端用例；
  另加 `LiveStreamTests`（默认跳过，`ORZMC_MCSM_LIVE_*` 启用）对真面板跑一遍。
- `swift/app` PR #120：控制台流优先、轮询兜底；`ConsoleTextBuffer`（增量 + 按行裁剪）；
  `MCSManagerModel.probeStream()` + `ORZMC_DEMO_MCSM_STREAM_PROBE=1` 无界面自检。

**踩到的坑（都进了注释/测试）**
1. `/socket.io/` 的**尾部斜杠不能少**：少了被反代 404，表现成 `-1011 Websocket handshake failure`；
2. **必须回 pong**（Engine.IO v4 由服务端 ping），否则 20~25 秒被踢；
3. 口令**一次性** → 客户端收 `makeEndpoint` 闭包，重连重新申请；
4. `@frozen` 生成枚举里 `case .undocumented(let code, _)` 在**测试构建**下报
   `'_' can only appear in a pattern…`（`build` 不报）→ 改用 `@unknown default:`。

**验证**
- 真面板（macOS，`ORZMC_DEMO_MCSM_STREAM_PROBE=1`）：`ready=true`，`/list` 回显 + 结果实时到达；
- app 单测 73 → 79；`swift test`（MCSManagerAPI）全绿；模拟器 UI 全套绿；
- **真机 UI：`testStatusBadgeKeepsSpinningAfterReentering` 必失败** —— 已用 app `main`（改动前）
  复现同样失败，判定为**设备侧/既有问题**，与 B1 无关。

**顺带修的 DX**：`--detach` 之前丢参数（解析后才拼命令行）→ 解析前存 `ORIGINAL_ARGS`；
`UI_ONLY_TESTING`；`check-secrets.py` 短口令按词边界匹配（`jokerhub` 在域名里被误报）。

### 2026-10-26（八）— pi（真机 UI 真因纠正 + O3/O4/O5 完成）

**真机 XCUITest 真因纠正**：维护者提示"是不是没插数据线"——正是。
`Transport Type: localNetwork`（Wi-Fi）下 runner 会 `DTX 握手被拒 → exit 74`；插线（`wired`）后：

```
Test Case '…testMCSManagerSectionShowsInstancesAndStatus' passed (20.162 seconds)
Test Suite 'RemotePanelsUITests' passed …  ** TEST EXECUTE SUCCEEDED **
```

全套 8 用例（4 个按设计 skip）真机全绿。我此前"Xcode 27.0 < iOS 27.0.1 版本不匹配"的定因**是错的**，
已把 `run-ios-ui-tests.sh` 的预检降级为**只警告不阻断**，并新增「连接方式不是 `wired` → 提示插数据线」。
（插线后首次仍报 `Timed out while enabling automation mode`，保持解锁亮屏重跑即过。）

**O3/O4/O5 落地**
- `run-ios-ui-tests.sh --detach`：自己在 Terminal 里重跑并等结果，一条命令拿到退出码 + 末尾日志（实测跑通真机全量）；
- `scripts/dev/release.sh --version X.Y.Z [--plan]`：版本递增（`sort -V`）+ notes 存在且 ≥400 字节 +
  main/clean/同步检查 → 升 `Config.xcconfig`（build 自动 +1）→ `--fast`/`--full`/`--ui`/真机 UI → 建 PR → 打印后续三步；
  `--plan` 已验证正常路径与两个负例（版本倒退、缺 notes 均拒绝）；
- `check.sh --changed`：纯文档/`*.xcstrings` → 只跑静态；纯测试 → 包单测 + 应用测试；其它 → 默认档（保守）。

至此迭代复盘清单 **O1–O6 全部完成**：本地 `check.sh` 2–4 min → ~50 s、PR `build` 6.8 → 3.4 min、
DerivedData 8→2 个、真机 UI 恢复且一条命令可跑、发版前半段全自动。

### 2026-10-26（七）— pi（迭代优化第二轮：O1/O2/O6 落地，实测提速）

维护者决定「暂时不升 Xcode，先做优化」，于是把复盘清单里最省时间的三项做完（PR #117）：

| 措施 | 实测 |
|---|---|
| **O1 收敛 DerivedData**：`run-macos-signed.sh` → `OrzMC-local`、`install-ios-device.sh` → `OrzMC-local-ios`（都与 `check.sh` 共用） | 先签名构建再 `check.sh` → **49.9 s**（原 2–4 min）；目录 **8 个/6.8 GB → 2 个/4.2 GB**；签名 `Apple Development` 与真机安装均照常 |
| **O2 CI：PR 用锁定依赖**（`Resolve package dependencies` 只在非 PR 跑；main 仍 HEAD 解析） | PR `build (macOS)` **6.8 → 3.4 min**、`build (iOS)` 6.8 → 5.7 min；main 上 `build` 4 min / `intel` 5.2 min |
| **O6 `reclaim-space.sh`**（新，默认 dry-run） | 清掉 6 个残留目录，回收约 2.5 GB |

**累计**：一次功能迭代的纯等待从 **40–60 min → 约 25–35 min**。
剩下待做：**O3**（UI 测试 `--detach`，把 Terminal 依赖自动化）、**O4**（发版一键脚本）、**O5**（`check.sh --changed`）。

**真机 XCUITest**：仍不可用（Xcode 27.0 < iOS 27.0.1）；已在 `run-ios-ui-tests.sh --device` 加 3 秒预检，
等维护者升级 Xcode 后即可恢复，届时把预检当作"版本不匹配"的守门人。

### 2026-10-26（六）— pi（真机 XCUITest 排查 + 迭代耗时复盘）

**① 真机 XCUITest（`exit 74`）排查进展 —— 真因已定位，卡在设备重启后解锁**

| 步骤 | 结果 |
|---|---|
| 复现 | `OrzMCUITests-Runner … exited with code 74 before establishing connection` |
| 排除锁屏 | `lockState` → `passcodeRequired: false`；`devicectl` 截图确认屏幕亮着、已解锁 |
| 排除签名 | runner = `Apple Development: zhizhou wang (X3C2MG74H2)`，profile 有效到 2027-10-18 |
| 排除我们自己的 xctestrun 补丁 | 用**干净 `xcodebuild test`**（全新 DerivedData、不打补丁）同样失败 |
| **真因** | runner 起来 19 秒后：`Connection peer refused channel request for "dtxproxy:XCTestDriverInterface:XCTestManager_IDEInterface"` → `Exiting due to IDE disconnection`。即宿主机 ↔ 设备 `testmanagerd` 的 **DTX 握手被设备拒绝**，与工程/签名无关 |
| 已试无效 | 重装 runner/App、彻底 uninstall、`devicectl process launch`（能起） |
| 本轮动作 | 已 `devicectl device reboot`（经典修复）；**重启后设备 `unavailable`，iOS 要求在设备上解锁一次才恢复信任 → 等维护者解锁后复测** |
| 若仍失败 | 设备 iOS **27.0.1** 比本机 Xcode **27.0.0** 新 → 升级 Xcode 到 27.0.1+ |

⚠️ 期间我直接 `xcodebuild` 会在 CodeSign 处报 `errSecInternalComponent`（非交互 shell 拿不到钥匙串私钥）
—— 真机构建/测试**必须**经 Terminal.app，这也是自动化只剩"轮询日志"的原因（见 ②的 O3）。

**② 迭代耗时复盘（`swift/app/docs/iteration-cost-2026-10-26.md` 新增）**

实测：一次「功能 + 真机验收 + 发版」墙钟 **1.5–2 小时**，其中**纯等待构建/CI ≈ 40–60 分钟**。
六个根因：① 同一份代码要构建 6–8 次（本地 6 个 DerivedData + CI 每次删 `Package.resolved` HEAD 解析）；
② 升依赖就 `Couldn't check out revision`（本轮 4 次）；③ 真机 UI 不可用→截图+诊断钩子；
④ 真机签名只能走 Terminal；⑤ DerivedData 13 GB 撞过一次磁盘满（整次构建报废）；⑥ 发版无演练档。

**本轮落地（已随 PR #115 合并）**：
`scripts/dev/refresh-package.sh`（秒级刷新依赖缓存，替代手工 fetch+删 checkout）、
`check.sh` 磁盘预检、CI `intel` 只在需要时跑、`release-app.yml` 加 `dry_run`。

**待做 O1–O6（写进文档，供下次挑）**：收敛 DerivedData（-10 min/功能）、PR 用锁定依赖（6.8→4–5 min）、
`run-ios-ui-tests.sh --detach`、发版一键脚本、`check.sh --changed`、DerivedData 定期清理。

### 2026-10-26（五）— pi（**0.1.6 (58) 发布**：MCSManager 面板支持）

**为什么发**：backlog 全部清空，`main` 比 0.1.5 多 15 个提交（MCSM 多供应商 + 动作/控制台 + 面板增删改 + 两个真实面板坑），
两端真机都验过 —— 不发版等于这些工作没人能用。

**过程**
1. `Config.xcconfig` 0.1.5(57) → **0.1.6(58)**（build 号严格递增，Sparkle 靠它判新旧）；
2. 写用户视角 `docs/release-notes/0.1.6.md`（怎么加面板 / 面板侧两个前提 / 两种 key 各看到什么 /
   面板可改可删 / 动作 / 控制台 / **需要手动做的事：没有** / 已知问题）；
3. `check.sh --full` 全绿（静态 + 包单测 + 应用 73 条 + macOS/iOS 构建 + 真 socket 联调）；
4. `check.sh --ui` 模拟器 UI 全绿（8 用例）；
5. PR #114 → CI 5 job 全绿（含 `intel` x86_64 门禁）→ squash 合并；
6. `gh workflow run release-app.yml` → **success**（约 15 分钟）。

**产物核验（不只看绿）**

| 项 | 结果 |
|---|---|
| Release | `0.1.6`：`OrzMC_0.1.6_58_20261026_125009.dmg`（9 MB）/ `.zip`（8 MB）+ `appcast.xml` |
| 架构 | `x86_64 arm64`；Sparkle 也 Universal |
| minos | `14.0`（与平台分层一致） |
| 签名/公证 | `Developer ID Application: Zhizhou Wang (2N62934Y28)`；`spctl` → **accepted / Notarized Developer ID** |
| appcast | 流水线已回写 `main`（0.1.6 在 0.1.5 之上） |

**真机 XCUITest 踩到一个环境问题（未解决，已记「已知坑」）**：`OrzMCUITests-Runner` 启动即退
（`exit code 74 before establishing connection`）。已排除：设备已解锁（`devicectl device info lockState`
→ `passcodeRequired: false`）、Developer Mode 已开、重装 runner 与 App 均无效。
发版前用模拟器 UI 套件 + 手动真机验收替代；下轮单独排查（疑似 Xcode 27 runner 的签名/profile）。

### 2026-10-26（四）— pi（Intel + macOS 13 真机验证）

**维护者给了真机**：`ssh pro` = **MacBookPro12,1**（i5-5257U / 16 GB）/ **macOS 13.7.8** —— 正是
"卡在 Ventura 的 Intel Mac"这个目标机型，于是直接把 §6 清单跑了。

**结果**

| 层 | 内容 | 结果 |
|---|---|---|
| 分发层（Python CLI） | 官方一键安装器 | ✅ 自动选 `orzmc-macos-x86_64`（`Mach-O x86_64`）；`--version` 2.18.1 / `capabilities` / `list` 正常，启动 ~1.2s |
| 逻辑层（Swift CLI 旧版） | 机器上已有的真身 0.18.0 | ✅ `x86_64` / `minos 13.0` / `list` / `app status` 正常 |
| 逻辑层（Swift CLI **main**） | CI artifact `orzmc-x86_64-macos13`（`OrzMCKit` 的 `platform` job）→ scp → 跑 | ✅ 0.21.0 / `x86_64` / `minos 13.0`，`--version` 21ms |
| GUI | 官方 0.1.5 包（`x86_64 arm64`） | ⛔ 按预期起不来：`dyld: built for macOS 14.0 which is newer than running OS` |

**两个新事实（已写进文档）**
1. **Ventura 上不能构建逻辑层**：最高 Xcode 15（Swift 5.10）< `swift-tools-version:6.0` →
   真机只跑 CI 产物；为此给 `OrzMCKit` 的 `platform` job 加了 **artifact 上传**（PR #103）。
2. GUI 的 Intel 切片是真存在的（`lipo` 双架构），只是 minos 14.0 —— 所以"Intel 支持"与"Ventura 支持"是两件事。

**补跑（同一会话内，维护者要求）**：`orzmc client -v 1.20.1 -u guest --root-dir ~/orzmc-smoke/minecraft`
- 日志 `下载 Temurin JRE 17 (mac/x64)` → `file java` = **x86_64**，Temurin 17.0.20.1；
- `versions/1.20.1/client/natives/` 的 `liblwjgl/libglfw/libopenal.dylib` 全是 **x86_64**；
- 窗口 **`Minecraft 1.20.1`**（854×508）出现，`OpenAL initialized`、纹理图集全建、CPU ~30% → **进主菜单**；
- 体积 866 MB（JRE 109 + 游戏 757），启动约 1.5 分钟；离线 `guest` 无需正版登录；
- 无用日志两项：`Failed to verify authentication 401`（离线启动预期）、`screencapture` 抓 GL 窗口是黑图（不影响判定）。
- 游戏进程已 `kill`，`~/orzmc-smoke` 保留（含下载物，可 `rm -rf`）。

**环境**：验证目录 `~/orzmc-smoke`（36 MB，`bin/orzmc` Python CLI + `orzmc-swift-main`）；
真机信息也登记进 `AGENTS.md` §8.1.2（含"只能跑不能编"与"别跑长任务"的提醒）。

### 2026-10-26（三）— pi（平台支持：Intel 已支持 + 逻辑层钉 macOS 13）

**维护者问**：能不能支持 macOS 13 和 Intel 芯片。**拍板**：按折中方案落地 ——
GUI 保持 macOS 14（`@Observable` 要求），**逻辑层（CLI/库）钉在 macOS 13**。

**分析结论（写进 `docs/platform-support.md`）**
- **Intel：本来就支持**。0.1.5 官方包 `lipo -archs` = `x86_64 arm64`；JRE 按架构取
  （Adoptium `x64`/`aarch64`）、MC natives 按 `os.arch` 过滤、自升级资产按 `#if arch` 选。
- **macOS 13：GUI 不支持**，硬阻塞是 Observation 宏（16 个 `@Observable` 类、23 处
  `@Environment(X.self)`、19 处 `.environment(model)`、全仓 0 处 `ObservableObject`）；
  其余是 9 处 14-only UI + 3 处预览。改造估 1–2 周，收益只覆盖 2017 款及更老的 Intel Mac
  （它们的 CLI 已可用）→ 不做，清单留在文档 §7。

**落地的东西**
- `docs/platform-support.md`：三层矩阵、证据（含 CI 首次跑绿记录）、Intel 冒烟清单（7 步）、
  "降到 13"的代价清单、维护约定。
- `scripts/dev/check-platforms.sh`：不需要 Rosetta/Intel 真机的门禁 ——
  声明审计（逻辑层必须 ≤13、GUI 必须 14、不许写死 `ARCHS`/`EXCLUDED_ARCHS`）+
  产物审计（`otool -l` 读 `minos`）+ 分发审计（发布包必须 Universal）；
  `--arch` 做 x86_64 交叉编译（无 Rosetta 时明确跳过）。
- 父仓库 CI：`scripts/verify/check.py` 接 `--declarations-only`（ubuntu 也能跑）。
- `swift/app` CI 新增 **`intel` job**：`-destination 'platform=macOS,arch=x86_64'` → `BUILD SUCCEEDED`（3m18s）。
- `swift/lib/OrzMCKit` CI 新增 **`platform` job**：`声明下限: macOS 13` / `orzmc minos = 13.0` /
  `x86_64 产物架构 = x86_64`（4m02s）。两个 job 里都先确保 Rosetta（runner 实测**已预装**）。

**仍然缺的一块**：**Intel 真机运行**（编译已过，跑起来没验）→ 有 Intel Mac 时按 `docs/platform-support.md` §6 走一遍。

### 2026-10-26（续）— pi（P2-7 第 5 步：MCSM 动作 + 控制台，收尾）

**做了什么**
- `MCSManagerAPI` 0.3.0 → **0.3.1**：`GET /api/protected_instance/{open,stop,restart,command,outputlog}`；
  403/500 同时声明 `text/plain`；新增 `MCSMResponseEnvelope`（拆面板 `{status,data,time}` 外壳）。
- app：实例行 `⋯` 菜单（启动/停止/重启）+ **点行开控制台**；`RemoteActionGate` 防重入；
  提交后立刻显示过渡态（`starting/stopping/restarting`）；失败撤回并把**面板原话**写在实例下；
  控制台 3 秒轮询 `outputlog`，渲染共用 `ConsoleTextParser` + `ConsoleLineText`（红线未动）。
- 无界面探针扩展：`ORZMC_DEMO_MCSM_ACTION_PROBE=/list`（对每台在线实例发命令 + 取日志尾部，
  结果进诊断文件）。实测：`sent=true`、日志读回 4 KB（**只用只读命令**，别用 `stop`）。

**真机/模拟器抓出的 5 个真问题（都已修）**
1. 面板 `protocol.ts` 把**所有** `/api/*` 响应都包成 `{status,data,time}` → `outputlog` 的纯文本里也是外壳；
2. `Data(collecting:upTo:)` 上限设成"想要的字节数"→ 日志比它长直接抛 "too many bytes"（改固定 4 MB）；
3. `section` 上两个 `.sheet` 只认一个 → **控制台永远弹不出来**（合并成 `Sheet` 枚举）；
4. `minWidth: 420` 是给 macOS 写的 → iPhone SE（375pt）上控制台内容被裁掉两边（最小尺寸只在 macOS 生效）；
5. 菜单项在 XCUITest 里点不动 → 改成**点实例行开控制台**（更好的交互，也更好测）。

**门禁**：`OrzMCTests` 73 条、`MCSManagerAPI` 20 条、`check.sh` / `--ios` / **`--ui`** 全绿
（新增 3 条 MCSM UI 用例：分组与徽章、菜单项齐全、点行→控制台→发命令清空输入框）。

**遗留/注意**
- ⚠️ 面板 `mcs.jokerhub.cn` 2026-10-26 上午多次 20–25 秒甚至超时（Cloudflare Tunnel + 本机 VPN），
  诊断会因 20 秒超时失败 —— 是网络，不是代码；网络好时同一份包全部正常。
- XCUITest 两个坑：空 `TextField` 的 `value` 是**占位符**（不是空串）；容器上的
  `accessibilityIdentifier` 必须先 `.accessibilityElement(children: .contain)`。

### 2026-10-26 — pi（P2-7 第 4 步收尾：MCSM 双端真机验收通过 + 面板可编辑）

**维护者给的关键信息**：手机上配的是**普通用户** key、macOS 上是**管理员** key；面板网页里能看到 2 台实例。

**根因（两个响应格式坑叠加，跟权限判断无关）**
1. `GET /api/auth` 在面板 **10.18.0** 上被包了一层 `{status, data:{…用户对象…}}`；
   spec 只声明"裸用户对象"（字段全可选）→ 外壳解成空对象 → `permission = nil / instances = 0`
   → 普通用户永远「没有实例」（管理员只是靠节点端点兜住了）；
2. `data.loginTime` / `registerTime` 是**字符串**（`"2026-10-24 16:26:49"`），spec 按 int64
   → **整条响应解码失败**，连 `permission` 都拿不到，界面只显示「面板返回了错误（HTTP 200）」；
3. 另外错误响应是 `Content-Type: text/plain`（body 是 JSON 文本）→ 只声明 `application/json`
   会把面板那句「密钥不正确」丢掉。

**改动（MCSManagerAPI 0.2.1 → 0.2.3 / app PR #105–#109）**
- 按 `permission` 选入口：管理员走节点端点，普通用户走 `GET /api/auth?advanced=true`；
  `permission` 缺失时先试管理员端点、403 且有实例就回退；
- 403/500 同时声明 `text/plain`；`/api/auth` 兼容外壳；删掉不用的字符串时间戳字段；
- 403 转述**面板原话**（「面板拒绝了这个 API Key：密钥不正确」）；MCSM 请求 20 秒超时；
- 面板可**编辑**（Key 留空=不修改）+ 表单优化（就地校验、**测试连接**、macOS 尺寸、iOS `.large`）；
- 无界面验收钩子 `ORZMC_DEMO_MCSM_DIAGNOSE=1`（拉一遍 → 写 Caches json（含分支轨迹）→ 退出）。

**双端验收结果（同一台面板 mcs.jokerhub.cn / 10.18.0）**

| 端 | 面板 | 轨迹 | 实例 |
|---|---|---|---|
| macOS | 测试服管理员 | `permission=10` → 节点路径 | FoliaMC / PaperMC（在线） |
| macOS | 测试服普通用户 | `permission=1` → `/api/auth` 路径 | FoliaMC / PaperMC（在线） |
| iPhone SE3 | 测试服普通用户 | `permission=1` → `/api/auth` 路径 | FoliaMC / PaperMC（在线） |
| iPhone SE3 | 测试服管理员 | `permission=10` → 节点路径 | FoliaMC / PaperMC（在线） |

手机截图确认：MCSManager 分组显示 4 台实例（2 面板 × 2 实例）、徽章「在线」、玩家数 0/0。

**环境状态**
- `/Applications/OrzMC.app` = 开发签名版（Apple Development），官方 0.1.5 备份在
  `~/Applications-backup/OrzMC-official-0.1.5.app`；
- iPhone SE3 上是同一份 Debug 开发包（0.2.3 依赖 + 诊断钩子）；
- 本机 `~/Library/Caches/orzmc-mcsm-*.json` 是 macOS 端的诊断快照（勿提交）。

**留给下一个会话**
- **下一件事：P2-7 第 5 步**（MCSM 动作 + 控制台命令）。⚠️ 注意普通用户的动作端点
  (`/api/protected_instance/open|stop|restart`) 要 `uuid` + `daemonId`，我们已经有 `daemon/uuid` 键。
- 维护者可继续手动验收：macOS 上「远程托管 → MCSManager」应看到两组面板共 4 台实例；
  改面板信息走 `⋯ → 编辑面板`（Key 留空=不修改）。

### 2026-10-25 — pi（P2-7 第 3–4 步：MCSManagerAPI 新库 + MCSM 只读接入，已合入）

**维护者拍板**：① 新仓库 public `OrzMC/MCSManagerAPI`；② OpenAPI 来源用官方 apidoc；③ 凭据沿用
`SelfHostedCredentials`/`KeychainStore` 的做法。

**第 3 步（新仓库，PR 直接在 main 上首次提交）**
1. 查证：官方**没有**机器可读 OpenAPI（`MCSManager/Documentation` 只有 markdown），所以 `openapi.yml`
   是按官方 apidoc 手写的最小可用子集（节点列表 / 实例列表 / 实例详情），头部写明依据的 commit。
2. 仓库内容：`APIKeyMiddleware`（`X-Request-API-Key` + 官方要求的 `X-Requested-With`/`Accept`）、
   `MCSMClient.make(serverURL:apiKey:transport:)`、9 条测试、`scripts/check-apidoc-drift.sh`（CI 跑，不阻塞）、
   CI/LICENSE/README；打了 tag `0.1.0`。
3. 父仓库：作为**第 22 个子模块**收进 `swift/lib/MCSManagerAPI`（`.gitmodules` + `AGENTS.md` 登记表，
   `verify/check.py` 绿）。

**第 4 步（app 侧，PR #103 数据层 + #104 界面）**
4. 数据层：`MCSManagerPanel`（地址规范化 + UserDefaults/Keychain 凭据）、`MCSManagerPanelAPI`（app 内部只读接口，
   避免模型/单测依赖 OpenAPI 生成类型）、`MCSManagerAPIClient`、`MCSManagerModel`（分页取全、状态进
   `RemoteStatusCenter`、`shouldRefresh` 轮询、换面板清快照）、`MCSManagerErrorText`（403 在 MCSM 常是
   "面板没开 API Key 功能"）；新增 `RemoteHostingError.actionNotSupported`。12 条离线测试。
5. 界面：`MCSManagerPanelsModel`（多面板、每面板一份模型/状态中心）+ `MCSManagerSection`
   （远程托管页里按供应商分组，面板卡 + 实例行 + 添加/删除面板）+ `RemoteServerState+Presentation`；
   DEBUG 钩子 `ORZMC_DEMO_MCSM_FAKE=1`；UI 测试 `testMCSManagerSectionShowsInstancesAndStatus`。

**踩到的坑（都写进文档了）**
- SwiftUI **容器**上的 `accessibilityIdentifier` 会下发给所有子元素并覆盖子元素自己的 identifier →
  状态徽章的 id 被面板卡冲掉，UI 测试查不到；改为容器只留最外层 `.accessibilityElement(children: .contain)`
  + identifier，内部靠 label 断言。
- app 测试目标直接 `import OpenAPIRuntime` 会链接失败（`Undefined symbols`，就算把 MCSMAPI 加进测试目标也一样）
  → 结论：**测试只依赖 app 内部的纯接口**（`MCSManagerPanelAPI`），生成的 OpenAPI 类型只在 app 目标里用。
- `swift-openapi-generator` 把 JSON 字段 `protocol` 映射成 `_protocol`；`HTTPRequest.path` 是 `String?` 且含查询串。

**验证**
- `swift test`（MCSManagerAPI 9 条）、app `check.sh`（默认档）、`--ios`、新增 UI 用例单独跑 ✅
- ⚠️ 本地 `check.sh --ui` 全量里 `testRealSelfHostedServerShowsOnline` 当前失败：**与本轮无关**
  （stash 掉 4b 改动在 main 上跑同一条同样失败；那台真实自建服务器从模拟器探测不到在线）。
- CI：app PR #103 / #104 四项全绿；MCSManagerAPI 仓库 CI 绿。

**留给下一个会话**
- **下一件事：P2-7 第 5 步**（MCSM 动作 + 控制台命令）——详细口径见 §1「下一步」。
- 真面板验收仍待维护者：填 URL + API Key 后应能看到实例与状态变化（界面已具备）。

### 2026-10-25 — pi（P2-7 第 3 步：新建 OrzMC/MCSManagerAPI）

**维护者拍板（本轮开工前确认）**：① 仓库 public，名字 `OrzMC/MCSManagerAPI`；
② OpenAPI 来源用**官方仓库 apidoc**；③ 凭据沿用 `SelfHostedCredentials`/`KeychainStore` 的做法。

**做了什么**
1. 先查证：官方**没有**机器可读的 OpenAPI/Swagger（`MCSManager/Documentation` 只有 markdown，
   MCSManager/UI/Daemon 里也搜不到 swagger），所以 spec 是按官方 apidoc **手写的最小可用子集**，
   并在 `openapi.yml` 头部与 README 里写清依据的文档 commit（`287c3936`）与鉴权实现参考（`ad4f903a`）。
2. 新建仓库 `OrzMC/MCSManagerAPI`（public，MIT，CI 与 `ExarotonAPI` 同构：macos-26 + Xcode 26 + `swift test`）：
   - `Sources/MCSMAPI/openapi.yml`：`GET /api/service/remote_services`、
     `GET /api/service/remote_service_instances`、`GET /api/instance`；
     `required` 保守（只有依赖的字段必填，其余可选），列表项不含 `processInfo`/`space`（官方文档如此）；
   - `APIKeyMiddleware`：`X-Request-API-Key` + 官方要求的 `X-Requested-With` / `Accept`；
   - `MCSMClient.make(serverURL:apiKey:transport:)`：去尾部斜杠、默认 URLSession、可注入假 transport；
   - 9 条测试：请求拼装（路径/查询参数/鉴权头，**零网络**）、官方文档示例 JSON 解码、中间件；
   - `scripts/check-apidoc-drift.sh`：拉官方 markdown 检查我们声明的端点还在不在（CI 里跑，**不阻塞**）。
3. 父仓库：作为**第 22 个子模块**收进 `swift/lib/MCSManagerAPI`（`.gitmodules` + `AGENTS.md` 登记表 +
   `verify/check.py` 全绿）；AGENTS/HANDOFF 里的「21 个子模块」改成 22。

**踩到的坑（记下来省下次）**
- swift-openapi-generator 把 `protocol` 属性名映射成 **`_protocol`**（Swift 关键字），测试里别写 `.protocol`；
- `HTTPRequest.path` 是 **`String?` 且含查询串**（没有 `request.query`）→ 断言要用
  `URLComponents(string: path)?.queryItems`；
- 测试目标第一次跑会报 "target has overlapping sources"，因为 `Tests/<target>` 目录还不存在
  （SwiftPM 退回去扫 `Sources/`）——先建目录/文件再 build。

**验证**
- 本机 `swift test`（9 条全绿）、`/api` 端点漂移检查 3/3 通过
- 父仓库 `python3 scripts/verify/check.py`：登记表 22 个子模块一致

**留给下一个会话**
- **下一件事：P2-7 第 4 步**（app 侧 MCSM 只读适配）—— 详细口径见 §1「下一步」。
- 需要真机/真面板验收时：`deploy/` 里有 MCSManager 的 docker compose；面板必须打开 API Key 功能。

### 2026-10-25 — pi（P2-7 第 2 步：状态中心泛化，已合入）

**本轮做了什么**
1. 把 exaroton 专用的 `ExarotonStatusCenter` 下沉成**供应商无关**的
   `RemoteStatusCenter`（`swift/app/Sources/OrzMCRemoteHosting/RemoteStatusCenter.swift`）：
   - 键：`RemoteInstanceID`（供应商 + 原始 ID）—— 两家供应商 ID 撞车不会串；
   - 值：`RemoteInstanceStatus`（`state` 归一化 + `rawStatus` 供应商状态码，LOADING/PREPARING 不丢）；
   - 事件：`RemoteStatusChange`（`Sendable`，`instance` / `previous` / `status` / `source` / `at`）；
   - 唯一写入口 `publish(_:for:source:)`（只在真变化时发事件 + 递增 `version`）、`events()`、
     `status(for:)`、`lastSource(for:)`、`forget()`、`reset()`；
   - 刷新节律：`noteWebSocketActivity` / `beginRefresh` / `finishRefresh` /
     `shouldRefresh(hasCredentials:isAppActive:isLoading:now:)`；**30 秒判据一字未改**；
   - `RemoteStatusRefreshPolicy` 一并下沉（纯函数，签名不变）。
2. app 侧只留接缝：`ExarotonStatusCenter.swift` → **`ExarotonServerModel+StatusCenter.swift`**
   （SDK 状态码 ↔ 归一化、字符串 id ↔ `RemoteInstanceID`、`liveStatuses` 改成状态中心的投影、
   `statusVersion` 只在真变化时递增）。`reloadList` 用 `beginRefresh/finishRefresh` 记账。
3. 顺手补一个真问题：**换账号时清空状态**（`resetRemoteStatus()`）—— 以前旧账号的 `liveStatuses`
   会留在快照里，理论上会漂到新账号的列表上。
4. MCSM 不用另写节律：它没有 WS（从不记 activity），`shouldRefresh` 自然退化成按最小间隔轮询。

**验证**
- `swift/app/scripts/dev/check.sh`（静态 + 包单测 + `OrzMCTests` + macOS 构建）✅
- `--ios` ✅、`--ui`（模拟器 UI 验收）✅
- 库测新增 12 条（含从 app 挪过来的刷新节律 7 例）；PR #102 四项 CI 全绿 → squash 合并
- 排错记录：`ExarotonServerDetail` 里的 `.task { for await event in model.statusEvents() where event.serverID == id }`
  在字段改名后触发「compiler is unable to type-check this expression in reasonable time」，
  改成 `event.instance == model.instanceID(id)` 即恢复（这类报错先找**不再存在的成员**，别急着重构表达式）。

**留给下一个会话**
- `swift/app` `main` = `218ff8e6`；父仓库已 bump 指针；工作区干净（只剩 `tools/OrzMCBackup` 的历史 `m`）。
- **下一件事：P2-7 第 3 步** —— 新建 `OrzMC/MCSManagerAPI`（独立 OpenAPI 依赖：`openapi.yml` +
  generator build plugin + `X-Request-API-Key` 中间件，先只做「列实例 + 实例状态」+ 单测），
  再第 4 步接 app 只读适配（凭据进 Keychain、UI 按供应商分组）。
  ⚠️ 新建仓库 + 选定 MCSM 的 OpenAPI 来源属于跨仓库决定，**开工前先跟维护者确认**。

### 2026-10-25 — pi（P2-7 第 1 步：供应商抽象层，已合入）

**本轮做了什么**
1. 按 §1 的"下一步"开工：在 `swift/app/Sources/OrzMCRemoteHosting` 定稿供应商抽象层
   （`ProviderKind` / `RemoteInstanceID` / `RemoteInstanceSummary` / `RemoteHostingProvider` /
   `RemoteHostingGrouping` / `ClosureRemoteHostingProvider` / `RemoteHostingError`），
   把旧的 `RemoteServerHosting` / `RemoteServerIdentifier` / `RemoteServerSummary` 合并掉（避免两套并行抽象）。
2. app 侧加 `ExarotonHostingProvider`（`servers` → 摘要，状态取唯一来源 `effectiveStatus(for:)`；
   动作转发现有 start/stop/restart，`false` 转成 `actionFailed`）。**只做映射，行为不变、无新 UI。**
3. 新增 `swift/app/docs/remote-hosting-providers.md`（分层 / 不变量 / 三条红线 / 5 步进度），
   backlog P2-7 第 1 步标 ✅。
4. 测试：10 条包测（命名空间 / 分组 / 去重 / 闭包适配器 / 错误透传）+ 7 条 app 测试
   （映射、静态地址优先、无 id 跳过，拒绝别家实例、gate 占用时报 actionFailed）。
5. 顺带修 `swift/app/scripts/dev/{install-hooks.sh,check.sh}`：`$name（…）`「变量紧跟中文标点」
   在部分 shell 下被当成变量名的一部分 → `--check` 直接 unbound variable；统一改成 `${name}`。
   之后按 §8.1.1 给这个子模块 clone **装了 pre-push 钩子**（之前没装）。

**验证**
- `swift/app/scripts/dev/check.sh`（静态检查 + 包单测 + `OrzMCTests` + macOS 构建）✅
- `swift/app/scripts/dev/check.sh --ios` ✅
- PR #101 四项 CI 全绿（split / protocol-live / build macOS / build iOS）→ squash 合并
- ⚠️ 本地磁盘只剩 ~7GB：已删掉可再生的 `DerivedData/OrzMC-local-release`（2.4G）与 `OrzMC-device`（2.6G）。

**留给下一个会话**
- `swift/app` `main` = `30a5eeec`，父仓库已 bump 指针；工作区干净（只剩 `tools/OrzMCBackup` 的历史 `m`）。
- **下一件事：P2-7 第 2 步** —— `ExarotonStatusCenter` → 供应商无关的 `RemoteStatusCenter`
  （`publishStatus` / `statusEvents()` 上移；`RemoteStatusRefreshPolicy` 当时还在 app 里，第 2 步才真正下沉，
  只需把它与状态中心接上；**"WS 是否安静 30 秒"这个判据不要动**）。
- 第 3 步要新建 `OrzMC/MCSManagerAPI` 仓库（独立 OpenAPI 依赖），属于跨仓库动作，开工前先确认。

### 2026-10-25 — pi（收工交接：P2-7 新会话开工准备）

**这次会话做完了什么（按时间）**
1. 按 backlog 顺序清掉 P0-1 / P1-2/3/4 / P1-5 / P2-6（四个 PR，全部 CI 四项绿、父仓库逐个 bump）。
2. 发 **0.1.4 (56)**（notarized + Sparkle appcast，产物逐项核验）。
3. 补 iOS 链路：`scripts/release-ios.sh`（归档/导出/TestFlight 上传/装真机）、
   `install-ios-device.sh` 扩展、`Release iOS` workflow、`docs/ios-release.md`；
   CI 实测「开发签名可用、分发签名差权限」，并实现了 manual signing 分支（等 3 个 secret）。
4. 真机验收揪出 0.1.4 两个回归并修掉：删除确认框崩溃（译文占位符顺序 + 新增 i18n 守卫）、
   远程控制台不显示日志（行尾 `\r` 被吞 + 4 条回归测试）。
5. 发 **0.1.5 (57)** 热修；本机 `/Applications/OrzMC.app` 与 iPhone SE3 都已升到 0.1.5。
6. 把 P2-7 的拍板结论与 5 步开工顺序写进 `swift/app/docs/backlog-2026-10-25.md`。

**留给下一个会话的状态**
- 代码/文档全在远端：父仓库 `main`、`swift/app` `main` = `79ac5963`，工作区干净
  （只有 `tools/OrzMCBackup` 的历史遗留 `m`）。
- P2-7 从 backlog 的"第 1 步"开始：协议定稿 → 状态中心泛化 → `Sources/MCSMAPI` →
  app 侧 MCSM 只读适配 → 动作/命令/多账号。
- **P2-7 的三个红线**（已在 backlog 与 §0.1 写明）：WS 安静 30 秒的轮询判据不能改；
  状态徽章只能有一个实现；控制台解析按 Unicode 标量、行尾 `\r` 不能丢行。
- 未做/待维护者：iOS TestFlight 分发（需 3 个 secret 或提 ASC API key 角色）；
  `uitest-secrets.env` 里的 RCON 密码等于公开服务器名（建议轮换）。

### 2026-10-25 — pi（0.1.5 热修发版）

- 维护者真机验收两个修复通过后发版：版本 `0.1.5 (57)`、新增 `docs/release-notes/0.1.5.md`
  （面向用户：两个修复 + **无需手动处理**）、PR #100 合入后跑 `Release App`。
- 产物核验：GitHub Release `0.1.5`（zip/dmg/appcast）；dmg `stapler validate` 通过、
  `spctl` = Notarized Developer ID；`products/appcast.xml` 已含 0.1.5 (57) 的 `edSignature`。
- 本机 `/Applications/OrzMC.app` 已换成**官方 0.1.5 dmg**（Release + 公证），iPhone SE3 也升到 0.1.5 (57)。
- 父仓库 bump `swift/app` → `c58ed602`；`RELEASES.md` 追加 0.1.5 基准组合表。

### 2026-10-25 — pi（验收揪出 0.1.4 的两个回归，已修）

**1) macOS：点删除按钮必崩（#98）**
- 崩溃报告 `~/Library/Logs/DiagnosticReports/OrzMC-2026-10-25-153739.ips`：
  `String.init(localized:)` → `__CFSTRING_IS_CALLING_OUT_TO_AN_OBJECT_FORMAT_ARGUMENT`
  → `objc_opt_respondsToSelector(0x2)`，栈顶是 `View.alert(_:isPresented:presenting:…)`。
- 根因：`RiskyAction.deleteAllInstances` 正文英文键是 `All %lld instance folders (%@)…`，
  zh-Hans 译文写成 `会永久删除 %@ 的全部 %lld 个实例目录…`（**顺序反了**）→
  `String(localized:)` 按译文顺序取参数，第一个 `%@` 拿到 Int → 崩。
- 修：译文改成保持顺序（`全部 %lld 个实例目录（%@）`）。**并加守卫**：
  `check-localization.py` 现在校验"键与译文占位符的数量/类型/顺序一致"（以前带插值的键直接跳过），
  实测能抓住这次的原始错误。

**2) iOS：远程控制台一直停在占位（#99，P2-6 回归）**
- 根因：`ConsoleTextParser.lines(in:)` 把单独 `\r` 当"行内覆盖"，直接丢掉前半行；
  **exaroton 的 console 流每行都以 `\r` 结尾** → `"line…\r"` 被整行丢弃 → 缓冲区永远为空。
- 修：`\r` 语义改成"取最后一个非空分段"（`"Done\r"`→`"Done"`，`"10%\r50%"`→`"50%"` 不变），
  `lines(in:)` 与 `parse(_:)` 两层都改；补 4 条回归测试（含缓冲区级、带颜色的行）。

**已装好的验收件**
- 本机 `/Applications/OrzMC.app`：Release + Developer ID 签名（本地构建、未公证），含两个修复。
- iPhone SE3（`00008110-0001712226A0401E`）：Release 开发签名包，main `9a907ef4`，含两个修复。
- ⚠️ 磁盘一度只剩 1GB（`lipo: No space left on device`），已清掉 4 个废弃的
  `~/Library/Developer/Xcode/DerivedData/OrzMC-*`（约 8GB）。

**其它**
- ⚠️ `protocol-live` 偶发失败：`testLiveRCONJoinsMultiplePackets`（假 RCON 多包拼接）
  报 `There are 2 of a max of 20 players online:`，`gh run rerun --failed` 后即绿 —— 是**测试自身**的
  时序抖动，不是产品代码问题（本轮 2 次里出现 1 次）。

**建议**：0.1.4 是**带崩溃的已发布版本**，修完应尽快出 **0.1.5**（等维护者点头）。

### 2026-10-25 — pi（真机装 0.1.4 开发包）

- 按维护者要求**只装开发签名包，不做分发**。后台会话拿不到钥匙串，用
  `open -a Terminal <x.command>` 把命令投递到图形会话执行、轮询日志（HANDOFF 里记的老办法）。
- 结果：iPhone SE3（`00008110-0001712226A0401E`）装上 **OrzMC 0.1.4 (56)**（Release 配置、开发签名），
  `devicectl device process launch` 后进程在跑。Debug 配置用 `install-ios-device.sh`（不加 `--release`）。
- 顺手修掉一个真 bug（#97 → app `4956ee21`）：`install-ios-device.sh` 的 EXIT trap
  在没走 `--ipa/--app` 时返回 1 → **装包成功却报 exit 1**（`release-ios.sh --install` 会被 `set -e` 打断）。
  修完在真机上复测 `EXIT=0`。
- 分发（TestFlight）按维护者要求**暂不做**；要开时按 `swift/app/docs/ios-release.md` 的
  「方式 A」加 3 个 secret，或把 ASC API key 提到 Admin。

### 2026-10-25 — pi（iOS 分发签名：把本机那一步搬进 CI）

**问题**：上一轮说「CI 直传 TestFlight 被权限挡住」，维护者问"本机有 Apple Distribution 就行，
这步能不能放 CI"。

**查清的事实**
- 分发包要两样：**Apple Distribution 证书私钥** + **App Store 描述文件**。
- 本机：私钥在登录钥匙串；描述文件**本地也没有现成的**（实测
  `~/Library/Developer/Xcode/UserData/Provisioning Profiles` 只有 Team / Ad Hoc），
  第一次导出是 **Xcode 登录的 Apple ID** 现场创建的。
- CI：两样都没有，ASC API key 的角色也不足以让云签名代办 → `Cloud signing permission error`。
  属于**权限**问题，不是脚本参数。

**做完了**（#96 → app `075bb246`）
- `release-ios.sh` 支持 **manual signing**：`IOS_DIST_CERT_P12`（base64 .p12 含私钥）+
  `IOS_DIST_CERT_PASSWORD` + `IOS_PROFILE`（base64 .mobileprovision）→ 证书进临时钥匙串
  （`set-key-partition-list` 免交互）、描述文件装进 `~/Library/MobileDevice/Provisioning Profiles/`、
  ExportOptions 写 `provisioningProfiles`（bundle id 取自归档），退出**恢复钥匙串搜索列表**并删临时钥匙串。
- workflow 透传这三个 secret；不配时仍走云签名（`debugging` 回归验证通过 #40171594562）。
- 文档补「为什么本机能、CI 不能」对照表、自查命令、三种搬法对比与代价、生成 secret 的命令。

**待维护者做（二选一，之后 CI 一条命令直传 TestFlight）**
1. 加 3 个 secret（命令在 `swift/app/docs/ios-release.md`「方式 A」）；或
2. 把 App Store Connect API key 角色提到 **Admin**（云签名自动建证书，不加 secret）。

### 2026-10-25 — pi（补 iOS 归档 / TestFlight / 真机装包）

**做完了**
- `swift/app/scripts/release-ios.sh`（新）：`archive` → `-exportArchive` 出 ipa →
  可选 `--upload`（altool 传 TestFlight）/ `--install`（交 `install-ios-device.sh --release` 装真机）。
  导出方式取 Xcode 新名（`debugging`/`release-testing`/`app-store-connect`，老名自动映射）；
  ExportOptions 由脚本生成并 lint（`manageAppVersionAndBuildNumber=false`）；
  签名两条路：本机钥匙串（automatic）或 ASC API key 云签名（`-authenticationKey*`）；
  导出后当场校验 ipa（bundle/版本/签名/图标）。
- `install-ios-device.sh` 扩展 `--release` / `--app <app>` / `--ipa <ipa>`（解包安装，不重复构建）。
- `.github/workflows/release-ios.yml`（`Release iOS`）：`export` 默认 `debugging`、
  `upload` 默认 **false**（true 会真的产生 TestFlight 构建并通知测试员）。
- `swift/app/docs/ios-release.md`（新）+ `docs/iteration-flow.md` §4.2 / README 补入口。

**实测结论（重要）**
- CI `export=debugging` ✅（#40163544468）：云签名拿到 `Apple Development: Created via API` +
  Team 描述文件，产物 ipa 核验通过（0.1.4 (56)、`com.joker.OrzMC.iOS`、图标在包里、
  描述文件有效到 2027-10-25）。
- CI `export=app-store-connect` ❌（#40163232403）：archive 成功，export 报
  `Cloud signing permission error` / `No signing certificate "iOS Distribution" found` /
  `No profiles for 'com.joker.OrzMC.iOS' were found`。**API key 角色不足**，云签名建不了分发证书。
  三条出路：① 本机 Terminal.app 里导出+上传（钥匙串里已有 Apple Distribution，今天就能用）；
  ② 把 ASC API key 提到 Admin；③ CI 里塞分发证书+描述文件（manual signing，脚本尚未实现）。
- 坑：bash 里 `$VAR` 紧跟中文全角括号会被当成变量名的一部分（`unbound variable`），
  脚本里统一改成 `${VAR}`。

**流程提醒**：这条文档补正是直接 push 到 app `main` 的（只改默认值 + 文档），
没走 PR —— 下次类似改动仍按"分支 → PR → squash"来。

### 2026-10-25 — pi（backlog 全清 + 0.1.4 发版）

**做完了**（四条支线各一个 PR，全部 CI 四项绿、squash 合并；父仓库逐个 bump 指针）
- **P0-1 远程托管错误弹窗**（#90）：新增 `RemoteHostingErrorText`（取消 → `nil` 不弹窗；
  离线/401·403/5xx/兜底各一句中文），额度池、内存、生命周期动作、WS 流操作全部改走它；
  单测 9 例 + UI 用例「真实账号连进出额度池 20 轮零弹窗」。
- **P1-2/3/4 界面收口**（#91）：空态移出 `ScrollView`（`defaultScrollAnchor(.bottom)` 是占位贴底的根因）；
  内存行去掉 `LabeledContent` 改 `HStack`；服务器菜单去掉编辑/删除、选中态「勾+加粗+着色」、
  热区移进 label。三个新 UI 用例（空态用**像素**判定位置——Form 会合并行内无障碍元素，量 frame 判不出来）。
- **P1-5 iOS 图标**（#92）：根因是 `AppIcon-iOS.appiconset` 一个 png 都没有。改成 macOS/iOS
  共用 `AppIcon`（universal 1024 单尺寸条目），删空集；1024 图重新导出为**无 alpha**。
- **P2-6 控制台 ANSI 渲染**（#93）：`OrzMCFoundation.ConsoleTextParser`（纯逻辑，20 例单测）
  + `OrzMCDesignSystem.ConsoleLineText`（按亮暗模式调色，AttributedString，不用 WebView），
  三处控制台共用；`RemoteConsoleBuffer` 支持一条消息多行。文档 `swift/app/docs/console-rendering.md`。
  坑：Swift 把 `"\r\n"` 当成**一个** Character，必须按 Unicode 标量遍历。
- **0.1.4 发版**（#94 → `8bc96ed1`）：`Config.xcconfig` 0.1.4 (56) + `docs/release-notes/0.1.4.md`
  （面向用户，**无**需手动处理事项）；`Release App` workflow 成功。
  产物已核验：dmg/zip 内 app 均 0.1.4 (56)、Developer ID + hardened runtime、
  `stapler validate` / `spctl` = Notarized Developer ID；`products/appcast.xml` 含 0.1.4 的
  `edSignature`，`SUFeedURL` 指向 main 的 appcast。

**还没做 / 下一步**
- **P2-7 多供应商**：维护者已拍板——① MCSM 走**独立 OpenAPI 依赖**（与 `ExarotonAPI` 同构）；
  ② API 之上加抽象层统一服务端交互与事件；③ 能下沉的尽量下沉到 `Sources/*` 复用；
  ④ UI **按供应商分组**。第 1 步：`Sources/MCSMAPI`（openapi.yml + generator plugin +
  `X-Request-API-Key` middleware）+ `docs/remote-hosting-providers.md`。
- ⚠️ 交付提醒：`swift/app/scripts/dev/uitest-secrets.env` 里的 RCON 密码**等于公开的服务器名**，
  `check-secrets.py` 因此拦过一次新增字面量（已绕开），建议轮换。
- ✅ iOS 链路补齐（见下一条会话日志）：归档/导出/装真机可用；**CI 直传 TestFlight 仍缺分发证书权限**。



**做完了**
- 真机/模拟器验收出的四类问题全部修完并合入：内存「还原」按钮失效（Form 行按钮合并）、
  封禁名单被解析成一段文本（Paper 的 `banlist` 回复**没有换行**，改为按 `was banned by` 结构切）、
  状态来源不一致（新增 `RemoteStatusCenter`：`publishStatus` 唯一入口 + `statusEvents()` 订阅）、
  徽章旋转图标退出重进后停止（改 `TimelineView` 时间驱动，删掉重复的 `ExarotonServerStatusView`）。
- **SDK 侧找到真 bug**：`OrzMC/ExarotonAPI` 的 `ServerStatus` 漏了 `9 = TRANSFERRING`，
  导致 WS 的 `status` 消息整条解码失败、状态更新被丢弃 → 已修并发 **0.0.10**（app 依赖已升）。
  证据：只读探针在真实账号上跑通启停，HTTP 与 WS 状态序列完全一致；status=9 解码会抛错。
- 轮询判据修正：旧实现用 `isLive`（含 `readyServerID`），WS 掉线后 `readyServerID` 不清空 →
  轮询被永久跳过 → 状态卡在「加载中」。现在以"WS 是否安静（30s）"为准。
- 新增 UI 自动化：`testStatusBadgeKeepsSpinningAfterReentering`（截徽章像素比差异，已验证能抓住旧 bug）、
  `testMemoryRevertRestoresValue`、`testConsoleInputNotCoveredByTabBar`、`testSnapshotRemoteConsole`。
- 工具：`scripts/dev/purge-package-cache.sh`（升级 pin 后清 SwiftPM 缓存）。

**尚未做（下一会话从这里开始）**
- 维护者新反馈的 8 项，已按优先级写进 [`swift/app/docs/backlog-2026-10-25.md`](swift/app/docs/backlog-2026-10-25.md)：
  P0 远程托管错误弹窗（原始 NSError + 取消当错误）、P1 控制台空态位置 / 内存行布局 / 服务器菜单三项 /
  iOS 应用图标缺失、P2 统一终端渲染（ANSI）、P2 多供应商（Exaroton + MCSM）与多实例预研。
- 发版保持暂停，等这批体验项做完统一出 0.1.4。

### 2026-10-23 — pi（状态通知 + 真机验收脚本）

- **状态变化通知**（app #58 → `cf51fbb1`）：
  `ServerStatusNotifier`（开关 `orzmc.selfHosted.notifyStatus`，**打开时才申请权限**，被拒自动回弹；
  每台服务器 60 秒节流；删除服务器时清历史）+ `ServerStatusChangeDetector` 纯逻辑
  （只在**真的翻转**时报事件，首次观测不报——否则每次启动都误报）。5 个单测。
  只在在线↔离线时报；**不报"某玩家上线"**（轮询拿不到可靠事件流）。
- **真机验收脚本**（无需改 App 代码）：
  - `scripts/dev/verify-real-server.py`：只用 SLP + RCON 连真实服务端，打印**原始回复**与解析结果；
  - `scripts/dev/accept-real-server.sh`：定位 `versions/<v>/server/server.properties`，
    `--patch` 写入 `enable-rcon`/`rcon.port`/`rcon.password`（**先备份**、密码沿用或随机生成），
    `--wait N` 等服务端起来后自动检查；**不启动/不停止**服务端。
  - 两个脚本已用假 SLP/RCON 服务端跑通全链路（patch → 备份 → 等待 → 检查）。
- ⚠️ 待人工执行：给真实 26.3 服务端打开 RCON 并重启后，跑
  `./scripts/dev/accept-real-server.sh --version 26.3 --wait 240`，
  把 `whitelist list` / `banlist list` 的**原文**贴回来，确认解析器兼容。

### 2026-10-23 — pi（本地验收：macOS + iOS + 假服务端）

验收环境：`scripts/test-servers/` 的假 SLP(25566) + 假 RCON(25575)，DEBUG 钩子提供 RCON 密码。

**通过项**
- 「服务器」窗口 · 我的服务器：状态卡（在线/26.3/2-20 名玩家/MOTD/更新时间）、
  玩家卡三个页签（在线 alice·bob / 白名单 Remove·OP / 封禁 carol（griefing）·Unban）、
  控制台卡（常用命令 / 清空 / 输入 / 发送）。
- 设置页「测试连接」：`✓ 26.3 · 2/20 · RCON OK`（SLP + RCON 双验证，不落盘）。
- 失败路径：连不上 → `连不上 127.0.0.1:25999，请检查地址、端口和网络。`（端口无千位分隔）。
- Esc 关闭「服务器」窗口：投递前 2 个可见窗口 → 投递后 1 个。
- macOS 主窗口 26.3 详情（客户端 Vanilla / 服务器 Fabric 两张卡）、设置 6 页渲染正常。
- iOS：我的服务器（在线 + 在线(2) alice·bob）、离线错误文案；底部两个 Tab 正常。

**验收发现并修掉的问题**（app PR #57 → main `55c106a8`）
1. 状态卡显示 2/20 名玩家，玩家卡却「在线（0）」——名单只从 RCON 来。改为优先 RCON、
   拿不到则回退 SLP 的 `players.sample`；RCON 不可用时在线名单只读。
2. 合成鼠标事件到不了次级窗口的 SwiftUI 控件 → 新增 DEBUG 验收钩子：
   `--players-tab` / `--selfhosted-settings` / `ORZMC_DEMO_RUN_TEST` / `ORZMC_DEMO_RCON_PASSWORD`
   （写法见 `swift/app/docs/iteration-flow.md`）。

**未覆盖**：真实 Minecraft 服务端上的 RCON（本机服务器未开 rcon）、远程托管（需要真实 exaroton Token）、
玩家动作按钮的实际点击（靠 `SelfHostedServersModelTests` 的假流用例覆盖）。

### 2026-10-23 — pi（分支收敛到 main + app 迭代流程标准化）

- **分支核对与清理**：OrzMCApp 的 9 个本地分支 + 2 个远端分支全部确认已通过 squash 合入
  `main`（逐个比对内容），本地与远端已删干净，只剩 `main`（`9e29c2cb`）+ 自动的 `gh-pages`。
  父仓库 `feat/ui-refresh-handoff` 已与 main 同步（解决 `HANDOFF.md` 冲突）→ PR #40 合入 main，
  随后删除该分支；现在两个仓库都只有 `main`。
- **app 迭代流程标准化**（app PR #56，见 `swift/app/docs/iteration-flow.md`）：
  `scripts/dev/check.sh`（`--fast` / 默认 / `--full`）、`check-pbxproj.py`（新增文件必须登记工程）、
  `check-localization.py`（文案必须有 zh-Hans，顺手补了 15 条漏译）、pre-push 钩子、
  PR 模板；CI `split` job 同步加这两项检查。
- ⚠️ **事故与恢复**：清理分支时我在父仓库执行了 `git reset --hard origin/main`，
  **误删了工作区里未提交的本地改动**（`AGENTS.md`、`CONTRIBUTING.md`、`docs/README.md`、
  `docs/cli-comparison.md`、`scripts/dev/prepush.sh`，以及 `scripts/air/run.sh` 的删除）。
  - `AGENTS.md` 已按会话开始时读到的**完整内容**逐字恢复（§8.2 本机构建、§8.1.1 本地门禁等）。
  - 其余按当前"本机构建"方案重建：`prepush.sh` 改用 `scripts/swift-check.sh test`；
    `cli-comparison.md` 去掉"必须走 ssh air"的过时结论；`docs/README.md` 补 `github-iteration-workflow.md` 索引；
    删除 `scripts/air/run.sh`；把一直未跟踪的 `scripts/swift-check.sh`、`docs/github-iteration-workflow.md` 纳入版本库。
  - **仍不确定**：`CONTRIBUTING.md` 的本地改动无法还原（当前 = main 上一版），请维护者过一眼。
  - 教训：**在父仓库不要用 `git reset --hard`**（这里常年有未提交的文档改动）；要同步用 `git merge --ff-only`。
- 另外修好 `scripts/dev/install-hooks.sh`：全角括号紧跟变量名导致 `set -u` 直接退出（`$rel（` → `${rel}（`），
  已在本机装好 python 与 OrzMCKit 的 pre-push 钩子。

### 2026-10-23 — pi（分支清理 + 迭代流程标准化）

- **分支核对**：OrzMCApp 的 9 个本地分支与 2 个远端分支全部已通过 squash 合入 `main`
  （逐一确认内容无误），本地与远端已清理；只剩 `main`（`9e29c2cb`）与自动生成的 `gh-pages`。
  父仓库 `feat/ui-refresh-handoff` **尚未合入 main**（37 ahead / 9 behind），见下方待办。
- **迭代流程标准化**（app PR #56）：
  - `scripts/dev/check.sh` 一条命令跑门禁（`--fast` 静态 / 默认 单测+应用测试+macOS 构建 / `--full` +iOS+真 socket 联调）；
  - 新增两个秒级静态检查并接进 CI `split`：`check-pbxproj.py`（新增文件是否登记工程）、
    `check-localization.py`（文案是否都有 zh-Hans，顺手补了 15 条漏译）；
  - `scripts/dev/install-hooks.sh` + `pre-push` 钩子（纯文档放行 / 源码跑 `--fast` / `PREPUSH_FULL=1` 全量 / `SKIP_PREPUSH=1` 逃生）；
  - `docs/iteration-flow.md`（流程 + CI job 说明 + 快照验证 + 发版五步 + 已知坑表）、
    `.github/pull_request_template.md`、README 加「开发」小节。

### 2026-10-23 — pi（玩家管理 + CI 真联调 + **发布 0.1.3**）

- **玩家管理**：`PlayerListParser`（解析 RCON 的 list / whitelist list / banlist list，8 个单测）+
  模型 `refreshPlayerLists` / `performPlayerAction` + 界面「玩家」卡（在线/白名单/封禁三段，
  每行给动作，底部可按名字加白/封禁）。
- **真 socket 联调进 CI**：`scripts/test-servers/{slp_server,rcon_server}.py` + `run-live-tests.sh`，
  CI 新增 `protocol-live` job。VarInt 那个 bug 的防线。
- **应用层测试 target 终于被跑**：`OrzMCTests` 以前从未执行（引用了已删除的服务，早就编不过）。
  已重写到当前 API，并新增 `SelfHostedServersModelTests`（假 RCON 流 + 注入密码 provider）。
  `swift-check.sh app-test` 现在两套都跑；CI 在 macOS 格加了测试步骤。
  踩坑：CI 步骤里不能调 `scripts/swift-check.sh`（那是**父仓库**的脚本）。
- **发布 0.1.3 (55)**：`MARKETING_VERSION=0.1.3` / build `55`；新增
  `docs/release-notes/0.1.3.md`（用户视角说明），`release-macos.sh` 自动按版本号找这份文件。
  Release workflow 跑绿 → <https://github.com/OrzMC/OrzMCApp/releases/tag/0.1.3>，
  appcast 已更新到 main（`81d0525d`）。
  **核验**：zip 7.7M / dmg 8.9M，`spctl` = accepted "Notarized Developer ID"，
  `lipo -archs` = x86_64 arm64，版本 0.1.3 (55)。
- app PR #54、#55 → main；main HEAD `81d0525d`（appcast 提交）。

### 2026-10-23 — pi（测试连接 + VarInt 修复 + 清理死代码）

- **修了一个藏很久的协议 bug**：`MCSLPPacket.readVarInt` 用 `UInt8` 左移 7 位，高位溢出丢失 →
  字符串长度 ≥128 的响应全部解析失败（278 字节的 JSON 被读成 22），界面永远"检查中…"。
  短包碰巧正常，所以之前单测全绿。修法：先转 `Int32` 再移位；新增 400 字符 MOTD 的回归用例。
- **设置页「测试连接」**：保存前先 SLP 查状态；（RCON 打开且填了密码）再跑 `list` 验证密码，
  失败给具体原因，不写任何存储。
- **删掉老的同步实现**（−14 文件）：`MCSLP` / `MCRCON` / `MCQuery` + `MCServerInfo` /
  `MCServerStatusInfo` / `MCSLPStatus` / 4 个无用 `Utils` 扩展；分包编解码保留。
- 「服务器」窗口记住上次看的面（`orzmc.serversWindow.mode`）。
- 验证：真 socket（本地 Python 假 SLP 服务端）+ 界面截图；app / app-ios / 33 组单测全绿。
- app PR #53 → main `a8b9e9e0`。
- ⚠️ 本轮曾因 `github.com:443` 被阻断卡住约 40 分钟（`api.github.com` 正常），
  换 IP / HTTP1.1 / CONNECT 代理均无效，最后是网络自行恢复。**再遇到时直接等，别折腾 git 配置。**

### 2026-10-23 — pi（服务器页清理 + 多档案 + 常用命令）

- 远程托管页右上两个裸图标（刷新 / 账号）**功能正常但看不懂** → 挪进摘要卡，带文字「刷新」「账号」，
  ⌘R 保留；工具栏清空。
- **多台自建服务器**：`Sources/OrzMCLauncher/SelfHostedProfiles.swift`（模型 + 存取 + 旧格式迁移，9 个单测）；
  页面顶部胶囊菜单切换/新增/编辑/删除（删除二次确认）；每台各自保留状态与控制台记录。
  旧键 `orzmc.selfHosted.profile` 与旧 Keychain 账户自动迁移。
- **常用命令**菜单（列出玩家/保存/广播/踢出/封禁/解封/OP/白名单），要参数的只填前缀；
  玩家行加「踢出」「OP」快捷动作。
- 修：错误文案里 `Int` 端口插值被加千位分隔符（`25,565`）→ 改用拼好的地址字符串。
- 新增真 socket 联调：本地 Python RCON 假服务端拆两包，`ORZMC_LIVE_RCON=…` 跑
  `testLiveRCONJoinsMultiplePackets` → 通过。
- app PR #52 → main `a9060d5f`。⚠️ 期间 GitHub 连接不稳，`git push` 需加 `-c http.version=HTTP/1.1`。

### 2026-10-23 — pi（Esc 统一 + 「服务器」窗口 + RCON 多包）

- **Esc 关闭规则定稿**：主窗口不关（留给取消搜索/退出编辑）；辅助窗口（设置/控制台/**服务器**）
  和弹层都能 Esc 关。统一实现 `EscapeClosesWindow`（`.escapeClosesWindow()`），替掉两处重复监听，
  并给服务器窗口补上（以前完全没接）。控制台保留 `allowWhenNotKey`（#45 的原因）。
  文档：`swift/app/docs/app-ui-design.md` §3.2.1。
- **远程窗口 → 「服务器」窗口**：顶部分段控件切换「我的服务器 / 远程托管」，默认按是否配过自建地址决定。
- **RCON 多包响应**：`runRCON` 第一包必读，之后 120ms 内还有数据继续读并拼接；
  `MCByteStream.hasPendingInput(timeoutMilliseconds:)`；新增多包单测。
- ⚠️ **补回上一轮丢失的改动**：PR #49/#50 只提交了「新建文件」，`ExarotonServerList` 卡片化、
  详情「概览」卡、统计标签本地化、`--remote-detail` / `remote: true` 调试钩子都没进提交。
  本轮全部重做并逐个验证（教训：提交前看 `git status`/`git show HEAD:path`，别只信构建通过）。
- app PR #51 → main `aa76d128`。

### 2026-10-23 — pi（P1–P3 剩余项一次做完）

一轮把 backlog 里剩下的五项清空（app 一个 PR #50 → main `9c856c00`）：

1. **目录扫描移出主线程**：新增 `DetailInstanceScan`（纯逻辑 + 注入 IO，`scanInBackground` 用专用队列），
   `BasicInfo.refreshInstances()` 改成「主线程组装描述 → 后台扫描 → 回主线程赋值」，body 里不再有文件 IO。
   7 个新单测（含「后台结果 == 同步结果」）。
2. **侧边栏 `+N`** → `\(n) more` → 中文「另 N 项」。
3. **未安装实例的无意义动作**：逐处核查后确认已无残留（卡片按目录存在过滤；目录行/批量删除/全部停止/
   CLI 的 Reveal 都已按存在性禁用）。本轮不再改。
4. **远程服务器窗口统一**：列表改成「品牌摘要卡 + `orzMCPanel()` 服务器卡/额度池卡」，抽 `ExarotonServerCard`
   供列表与详情「概览」共用；新增 `OrzMCDesignSystem/PointerHover.swift` 悬停反馈；全中文化
   （section/统计标签/按钮/空态/窗口标题）。调试工具加 `--snapshot-watch` 的 `remote:true` / `clickRemote`
   与 `--remote-detail`，终于能快照这个只能用菜单打开的次级窗口。
5. **iOS 自建服务器最小闭环**：`OrzMC/Common/SelfHosted/`（profile + model + 视图 + 设置页）、
   `KeychainStore`、协议层 `MCByteStream` / `MCReadBuffer` / `RaceWithTimeout` / `MCStatusSummary` /
   `MCServerProbe`，iOS 首页变成「我的服务器 / 远程托管」两个 Tab。
   顺手修了三个真 bug：读缓冲丢多余字节（表现为永远"检查中…"）、阻塞 IO 占并发线程（超时被拖成 8 秒）、
   task group 竞速要等卡住的子任务。实测本机 Fabric：`26.3 / 0/20 / 2ms`。
   文档：`swift/app/docs/ios-self-hosted.md`。

⚠️ 过程中发现 **PR #49 漏把 `ExarotonServerCard.swift` 登记进 `project.pbxproj`**（本地增量构建 +
CI 缓存把问题藏住了，干净构建会失败）。#49 已关闭并折叠进 #50，登记补齐；同时删除废弃的
`MobileHelper(iOS)/App/Model.swift`、解除 `OrzMCProtocol` 的 ios-only 平台过滤、把 `MCSLPError` /
`MCRCONError` 改 public。

### 2026-10-23 — pi（错误弹窗中文化）

- `LauncherError` 增加 `codeHint`（按 `E_*` 给一句中文结论）与 `messageIsChinese`；
  「操作失败」弹窗改为：中文原始信息直接显示；英文原始信息则**第一行中文结论 + 第二行灰色原文(E_XXX)**。
- 覆盖 E_USAGE / E_NETWORK / E_VERIFY / E_AUTH* / E_UNSUPPORTED* / E_IO / E_CANCELLED / E_RUNTIME / E_INTERNAL。
- 既有 `LauncherErrorTests` 里追加 3 个用例（错误码覆盖、未知码、中英判定）；Launcher 单测 76 个全绿。
- app PR #47 → main `b278c718`。

### 2026-10-23 — pi（二次确认弹窗中英混排清理）

- 盘了全部 6 处确认/错误弹窗（删除服务端/客户端/全部、停止/重启/终止、全部停止、
  CLI 安装卸载、Exaroton 停止重启）。
- 发现正文**硬编码英文**（标题是 `String(localized:)`，正文不是）→ 现在全部走 xcstrings；
  删除类不再打印目录绝对路径。
- 文案压成「标题=对象 + 一行后果」；用短句拼接（每句独立翻译键），不再用大段多行字符串。
- 脚本扫描 5 个弹窗文件：**0 个文案键缺中文**；截图复核「删除 Vanilla 客户端文件？」全中文、三行内。
- app PR #46 → main `2f0ad710`。

### 2026-10-23 — pi（⌘← 与 Esc 的语义收口）

- 维护者澄清：**⌘← 只用于「详情页内的控制台页」返回详情**；独立控制台窗口用 **Esc** 关闭。
- 实现：
  - `BasicInfo` 在 `consoleTarget != nil`（页面推入）期间装监听，⌘← → `consoleTarget = nil`（pop）；
  - `ConsoleWindowView` 去掉 ⌘←，改为 Esc 关闭；判定用「窗口可见」而非「是 key window」
    （`openWindow(value:)` 实测不会把 key 交过去，`isKey=false`）；关闭走 `performClose` + `orderOut` 兜底；
  - 文案 `Console page: back to detail`，设置页固定键表补 `Esc 关闭窗口`。
- app PR #45 → main `ca5723b0`；实测：卡片 → 控制台页 → ⌘← 回详情；独立控制台 Esc 关闭（2→1）。

### 2026-10-23 — pi（快捷键与输入法/全局冲突排查 + Esc 关闭设置）

- **快捷键失灵的真因**：监听器用 `modifierFlags.intersection(.deviceIndependentFlagsMask)` 判空，
  把方向键/Esc 自带 `.function`／`.numericPad` 也算作修饰键 → 判定永不成立。
  统一改走 `ShortcutEvents.modifiers(of:)`（只映射 ⌘⌥⌃⇧）。
- 输入法拼写（marked text）时不再抢键；「正在输入文本」只让开无修饰方向键与 ⌘←（文本语义），
  ⌘T/⌘F 这类 ⌘ 组合在输入时仍然生效。
- 设置窗口 Esc 关闭：`.onExitCommand` 无效（第一响应者为空）→ 本地监听 + `WindowReader` +
  `performClose`（SwiftUI Settings 窗口会忽略 close 时兜底 `orderOut`）。
- 设置页「快捷键」新增「优先级与冲突」说明（应用内优先 / 输入法让位 / 系统与其它 App 的全局热键先拦截）。
- 新增 `ShortcutEvents`（IME/文本编辑/sheet/修饰键/键码匹配）与 `WindowReader` 两个共用件；
  四个监听器（列表方向键、⌘T、⌘F、⌘←）全部改用它们。
- app PR #44 → main；实测 Esc 关设置（2→1）、⌘← 关控制台、⌘T/⌘F 正常。

### 2026-10-23 — pi（客户端卡片按类型 + ⌘← 修复 + ⌘T/⌘F）

- **客户端卡片按类型出现**：新增 `ClientKindMarkers`（`<client>/.orzmc/client-kinds/<Kind>`），
  启动时打标记，详情页只显示标记过的类型；旧安装按 fabric-loader / 客户端 jar 兼容推断。
  修「启动 Vanilla 后 Fabric 卡也出现」（两者共用同一个 client 目录）。
- **⌘← 控制台返回不生效**：零尺寸隐藏按钮在独立 Window 里不参与键盘分发 → 改为本地监听 + `performClose`；
  匹配改用键码（合成/输入法事件里 `charactersIgnoringModifiers` 可能为空）。
  ⚠️ 顺带修掉一个**必崩**问题：控制台/远程两个 scene 没注入 `ShortcutStore`，打开控制台即
  `Fatal error: No Observable object of type ShortcutStore found`（已补 `.environment(shortcuts)`）。
- 新增 **⌘T** 切换启动目标、**⌘F** 聚焦版本筛选（回车/Esc 交还焦点；启动时不再抢焦点），
  两条都进 `AppShortcut` 与设置页「快捷键」。
- app PR #43 → main；实测 ⌘T/⌘F/⌘← 全部生效。
- 备注：测试期间 26.2 / 26.3 的 `client/` 目录已被删除（误触删除按钮），下次启动会重新下载。

### 2026-10-23 — pi（客户端状态彻底按卡片独立 + 批量删除 + 隐藏空卡片 + 去滚轮）

- 用户报「启动 Fabric 后 Vanilla 的控制台图标也亮」→ 控制台键从按版本改为按类型
  （`ConsoleInstanceKey.client(versionId:kind:)` / `ConsoleTarget.clientKind`）；
  顺带修 `isCurrentInstanceRunning`（客户端）与 `removeClientConsole`。服务端本按核心键，无同类问题。
- 详情页工具栏新增**删除全部实例**（`RiskyAction.deleteAllInstances`，确认框逐个列出目录；
  客户端两种类型共用目录 → 路径去重）。
- **不存在的实例不再占位**：只渲染根目录存在的卡片；全空显示 `ContentUnavailableView`。
- 去掉鼠标滚轮切换启动目标（受焦点影响不稳定），⌘↩ / ⌘← / 快捷键页保留。
- app PR #42 → main `c86bee7f`；实测：启动 Fabric 后只有 Fabric「运行中」+ 控制台高亮。
- 注意：维护者测试期间 26.3 的 `client/` 目录已被删除，详情页因此显示空状态（不是 bug）。

### 2026-10-23 — pi（按卡片隔离状态 + Fabric 库下载 + 快捷键体系）

- **Fabric 启动失败根因在引擎**：`downloadFabric()` 只写在 `Launcher`（CLI）上，
  `GUIClient` 只 `download()+launch()` → loader 库从未下载。OrzMCKit **#99/#101**
  把 `downloadFabric(onEvent:)` 提升到 `extension Client` 并 `public`；GUI 在下载阶段调用。
  实测：`Loading Minecraft 26.3 with Fabric Loader 0.19.5`、主类 `KnotClient`、库落盘。
- **状态/进度按卡片隔离**（app #41）：客户端按类型记活动/运行进程/进度
  （`ConsoleInstanceKey.client(versionId:kind:)`）；服务端进度按实例写 `instanceProgress`，
  卡片标题显示百分比，详情页顶部不再有全局进度。实测启动 Fabric 时 Vanilla 仍「已停止」。
- **快捷键**：`Sources/OrzMCLauncher/AppShortcut.swift` 登记表 + `ShortcutStore`（UserDefaults 覆盖）；
  ⌘↩ 启动、⌘← 控制台返回、目标胶囊滚轮切换；设置新增「快捷键」页（5 条可改 + 5 条系统固定）。
- 提交流：OrzMCKit #99/#101 → 父仓库执行 `scripts/dev/bump-deps.sh` 刷锁 → app #41（`5b00d55b`）。
- 待验：滚轮手感（合成事件不好验）、⌘← 在独立控制台窗口里的行为、快捷键录制后的冲突提示（尚未做）。

### 2026-10-23 — pi（详情页三个验收 bug 修复）

- **Fabric 启动 = 原版**：GUI `GameLaunchService.startClient` 只传 `type:`、从未解析 `addon`；
  引擎仅在 `addon != nil` 时下载 Fabric 库/换主类。已改为 Fabric 时 `FabricMeta.resolve` →
  `ClientInfo(addon:)`。探针实测 `addonLibraries=7`（修复前 0）+ `cache/meta/fabric-profile` 落盘。
- **启动客户端点亮全部服务端卡片**：`BasicInfo.isBusy()` 混了全局 `launch.isLaunching`；
  改为按实例（`activities[key]`），客户端也按实例记活动，启动中显示「启动中…」。
- **「当前」胶囊挤动状态徽标**：去掉胶囊 → 整卡 accent 描边高亮 + tooltip；徽标严格对齐。
- 侧边栏安装徽标本地化（`Client` → 客户端，`%@ server` → `%@ 服务端`）。
- app PR **#40** 已合入 main（`856000cb`）；快照/构建/单测/分层校验全绿。
- 测试经验：反复 SIGTERM 后 macOS 状态恢复会让窗口不出现，快照/自动启动需加
  `-ApplePersistenceIgnoreState YES`；另外 `print` 在 GUI 进程里是缓冲的，调试输出要用 stderr。
- 待办顺序（P1→P3）见本轮对话：未安装实例禁用无意义动作、玩家名空提示、远程窗口样式统一、
  `+N` 文案、无窗口自动重开；P2 目录扫描移出主线程、离屏 500×500 窗排查；P3 iOS 远控最小闭环。

### 2026-10-22 — pi（UI 大改造合入 main + 全功能包本机验收）

- **PR #37（feat/ui-refresh）转 Ready 评审并 squash 合入 app main**（`51b339d7`，92 文件 +11003/−2236）；
  PR 描述整体重写（原文还写着"保留为草稿"，与合入状态不符）。
- **本机打全功能包**：`SKIP_NOTARIZE=1 ./scripts/release-macos.sh` → `dist/macos/0.1.2-54/`
  - `OrzMC.app` 18M（universal arm64+x86_64，Developer ID 签名 + hardened runtime，
    内嵌 Sparkle.framework，min macOS 14.0，Release 里**没有** DEBUG 快照工具）
  - `...zip` 7.0M / `...dmg` 7.7M；Gatekeeper 显示 `rejected / Unnotarized`（SKIP_NOTARIZE 预期）；
    `generate_appcast` 因本机无 EdDSA 私钥（CI secret）失败，属预期
- **顺手修打包脚本**（app PR **#39**，已合）：macOS 自带 `/bin/bash` 是 3.2，
  `set -u` 下展开空数组会 `unbound variable` → 本机不设 `DEVELOPER_ID_KEYCHAIN` 时脚本直接死。
  改成 `${arr[@]+"${arr[@]}"}`；`SKIP_NOTARIZE=1 /bin/bash ./scripts/release-macos.sh` 全新跑通
  到 DMG 完成（只有 appcast 需要私钥）。
- **本机验收**（合入后的主干）：主窗口（亮/暗）、版本列表与元数据、详情页启动卡 + 6 实例分组、
  设置 5 页、外观=浅色（系统为深色时全局变浅，`NSApp.appearance` 生效）、菜单全中文
  （关于/检查更新/帮助=使用文档+联系作者/游戏=跳转+启动+停止全部）、Release 包启动正常。
- 父仓库指针更新：`swift/app` → app main `1b03401c`。

### 2026-10-22 — pi（Swift CLI 装不上：根因 + 发版 + 依赖漂移）

- **根因**：安装器/自升级都用 `releases/latest`，而 GitHub 该端点只指向正式版；OrzMCKit 按
  `two-cli-strategy.md` §6 一律 pre-release → `releases/latest/download/<asset>` 恒 404。
  GUI「重装 → Swift CLI」必失败；`orzmc update` 报「网络问题/限流」也是同一个坑。
- **修复**（OrzMCKit **#98**，已合入）：`install.sh` / `install.ps1` 改为先问
  REST `releases?per_page=1`（含预发布）再回退 latest；`SelfUpdate.latestTag()` 增加
  `firstReleaseTag()` 回退。父仓库规范同步：`docs/spec/install-update.md` §6。
- **发版**：release-please **#92** 合入 → **v0.21.0**（pre-release，7 个资产齐全）。
  实测：安装器默认解析到 `最新发布: v0.21.0` 并装好；新二进制的 `orzmc update --yes`
  回「已是最新版本 v0.21.0」（此前是 E_NETWORK）。
- **依赖漂移**（`Package.resolved` 落后 main，R4/R7 同款）：新增 `scripts/dev/bump-deps.sh`
  （`--check` 报漂移；带参数则改写分支钉 → 重解析 macOS/iOS 两套 DerivedData → 打印 diff）。
  已刷新 OrzMCKit 6944afb5→771421cc、OrzSwiftKit 616212d0→f35e4dc3。
- **需求形态对齐**：app 里 OrzSwiftKit 原写 `upToNextMajor 0.0.18`，但 OrzMCKit 自己声明
  `branch: "main"`，SwiftPM 需求合一后分支优先 → 锁文件长期是分支钉。已把 app 侧也改成
  `branch = main`，消除"声明版本号、锁文件却是分支"的错觉。
- **依赖策略结论**：继续 HEAD 制（branch main）+ 锁文件纪律；**等 app 对外发版/接 Sparkle
  时**再把 OrzMCKit 切成 `upToNextMinor`（标签是干净的 `vX.Y.Z`，SwiftPM 可解析）。
- 设置页优化（app `b3e62089`）：**维护者验收通过**——五页拆分（通用/客户端/服务器/命令行/关于）、
  外观设置（NSApp.appearance）、Java 区块、渐进披露、消除重复标签与 CLI 教程式文案。

### 2026-10-22 — pi（详情页启动卡，维护者验收通过）

- 启动区从窗口标题栏移回详情页内部，做成自定义「启动卡」：14pt 圆角 + 品牌色薄渐变 + 强调描边，
  与其他实例列表卡区分；一行展示 启动目标菜单 / 玩家名（仅客户端）/ Java 状态 / ▶ 启动客户端。
- 启动目标合并成一个菜单（客户端 Vanilla·Fabric + 服务端 4 个核心）；玩家名占位「输入玩家名称」，
  为空时描边转警告色；Java 状态可点击重扫。
- 修 Java 需求异步到达不刷新的 bug（`VersionCatalogModel.onGameInfoLoaded` → `syncJavaRequirement`）。
- 收起/展开全部移到客户端组标题行右侧；语义色新增 `controlFill` / `selectionFill`。
- **维护者验收通过**，app 提交 `f8f88396` 已推送；CI 见 OrzMCApp#37。
- 下一步候选（未开始）：详情页其他细化 / 提交 PR 评审。

### 2026-10-22 — pi（版本详情页：标题栏启动区 + 全实例分组 + 折叠）

- 标题栏（`LaunchToolbar`）：模式 / 类型（服务端核心用下拉避免溢出）/ 启动设置 popover（玩家名、Java）/
  启动主按钮 + 进度指示；正文不再有启动面板。
- 正文列出**全部 6 个实例**并按类型分组（客户端 Vanilla/Fabric 共用目录；服务端 4 个核心各自独立），
  当前启动类型带「当前」标记。
- 展示模式：右上角两个图标动作按钮（全部折叠/全部展开，默认折叠）+ 单栏点标题折叠；
  折叠态卡片上下内边距对称（逐像素测过）。
- 表头动作自适应：`HeaderActionPlan`（+6 单测）按可用宽度决定内联 / 进 ⋯，不再默认藏高危动作。
- 页面内仍待处理（下一步）：**标题区**（维护者指定）。
- app 提交 `aae26ffb` 已推送。

### 2026-10-22 — pi（菜单项修正：关于 / 检查更新 / 帮助）

- 「关于 OrzMC」→「关于」（`replacing: .appInfo` + `orderFrontStandardAboutPanel`）；「Check for Updates...」
  改为应用传入本地化标题（显示「检查更新…」，⌘U 不变）；帮助菜单用 `replacing: .help` 换掉系统
  自动插入的死项「OrzMC 帮助」，改为「使用文档」+「联系作者」。
- 顺手修「启动 客户端」的空格（`"Start %@"` 的 zh-Hans 改「启动%@」）。
- 新增 DEBUG 自测开关 `--dump-menus` / `--test-about`；菜单已逐项核对无灰项、无英文残留。
- app 提交 `d76f94e4` 已推送。**下一阶段焦点：版本详情页优化**（维护者专注此项）。


### 2026-10-22 — pi（外部链接移到侧边栏顶部）

- 维护者意见：详情页右上角的「外部链接」不该在版本详情里，要放到**窗口最顶部**，与远程服务器入口、
  侧边栏开关同一排。`LinkMenu` 从 `UI/Detail/` 移到 `UI/SideBar/`，挂进 `GameView` 的 `.toolbar`
  （图标态、`.menuIndicator(.hidden)`，与相邻按钮同为圆/胶囊）；删除 `DetailViewTool.swift` 与 `.detailTool()`，
  **版本详情页不再有工具栏**，只保留启动配置 / 实例目录 / 控制台。
- 第一版误放进侧边栏搜索行（第 4 个图标），已按维护者意见改到窗口工具栏；实测收起侧边栏后工具栏入口仍可见。
- 版本详情页本轮改造（全实例分组 + 折叠 + 启动卡）**维护者验收通过**（app `f8f88396`）；两个 PR 仍为 Draft，未合并/未发版。
- 门禁：`app` / `app-ios` 构建通过，`app-test` 全绿，平台分层与 `git diff --check` 通过；
  96/1200pt、亮/暗自截图复核通过。已提交并推送（app `0ffaa31e`）。

### 2026-10-22 — pi（提交推送 app 改动并关闭父仓库 PR #39）

- app 子模块提交 `c28c70a3`（70 文件）并推送 `feat/ui-refresh`；父仓库 `0c1ff04`（HANDOFF）+ `0eff4bc`（只 bump swift/app 指针）推送 `feat/ui-refresh-handoff`。app PR #37 CI（split + macOS + iOS）全绿。
- **关闭父仓库 PR #39**，原因（已写在该 PR 的说明里）：① 它把 `swift/app` 钉在 `c28c70a3`（`feat/ui-refresh`，基于 `fa571e70`），而父仓库 `main` 已钉 app `main` 的 `d90d7af7`（含 #38），**合并会让 app 指针回退**；② 其余 6 个子模块指针与 main 完全一致，全为空操作；③ 该 PR 没有可评审差异（app 真实改动在 PR #37），且 token 创建的 PR 不上报 checks。
- **后续正确路径**：app PR #37 合并进 app `main` 后，父仓库开一个**只 bump `swift/app`** 的新 PR，指针指向 app `main` 的合并提交，并把本分支 HANDOFF 的文档内容一起带上（分支保留未删）。

### 2026-10-22 — pi（⌘↑/⌘↓ 真正滚到列表首/末）

- 反馈"⌘↓ 只切选中项、列表没到底"。实测确认 `ScrollViewReader.scrollTo` 对懒加载 List 只按估算位置滚（加锚点/动画/补滚都不收敛）。
- 新增 `VersionListScrollProbe`：按窗口坐标在视图树中找到 List 的 `NSScrollView` + `NSTableView`，用 `scrollRowToVisible` + 文档高度贴边、循环 5 轮收敛；中间行仍用 `scrollTo` 最小滚动。
- 自测（`--test-keys` / `--test-keys-top`）：⌘↓ 后 `1.0` 完整可见且底部留白露出；⌘↑ 后 `26.3` 完整可见。
- `app`/`app-ios` BUILD SUCCEEDED；`app-test` XCTest 107 + Swift Testing 13 全绿；平台分层与 `git diff --check` 通过。

### 2026-10-22 — pi（快捷键返工：本地监听 + 单行输入框也让路）

- 反馈"快捷键不生效"后自测发现两点：`.onKeyPress` 依赖列表焦点；而侧边栏焦点默认在搜索框，第一版监听把"编辑文本"整体放行 → 全部被跳过。
- 改为 `NSEvent` 本地监听（`VersionListKeyboardNavigation`）：主窗口无 sheet 时，↑/↓ 走一格、⌘↑/⌘↓ 跳首末；**只有多行编辑器**才让开方向键，单行输入框里方向键归列表（事件 consume，不影响输入）。
- 自测：投递 ↓/↓/⌘↓ 后选中项从 26.3 跳到 `1.0`，列表滚到底、详情标题同步；`--test-keys` 调试入口留在 DEBUG 构建里。
- `app`/`app-ios` BUILD SUCCEEDED；`app-test` XCTest 107 + Swift Testing 13 全绿；平台分层与 `git diff --check` 通过。

### 2026-10-22 — pi（时间戳到秒 + 版本列表键盘导航）

- 侧边栏时间戳精确到秒，文案改为「版本信息更新于 今天 18:55:18」。
- 键盘导航抽出 `VersionSelectionStepper`（纯函数，6 例测试）：↑/↓ 走一格且边界停住，⌘↑/⌘↓ 跳最新/最旧；⌘ 快捷键同时挂进 Game 菜单（不聚焦列表也能用）。
- `app`/`app-ios` BUILD SUCCEEDED；`app-test` XCTest 101 + Swift Testing 13 全绿；平台分层与 `git diff --check` 通过。
- 仍待维护者按一次方向键确认手感（截图无法验证按键）；未提交、未推送。

### 2026-10-22 — pi（侧边栏一体化）

- 去掉侧边栏的分隔线（搜索行下方、底部栏上方各一处）；更新时间从底部移到**搜索框与列表之间**，头部 = 搜索行 + 更新时间，无背景/描边，与列表共用侧边栏材质，读起来是一整块（`sidebarHeader`）。
- `app`/`app-ios` BUILD SUCCEEDED；`app-test` XCTest 95 + Swift Testing 13 全绿；平台分层与 `git diff --check` 通过；960×593 深色自截图核对。

### 2026-10-22 — pi（版本列表元数据 + 液态玻璃面板）

- **版本行方案 B**：版本号 + 「最新/最新快照」徽标；副标题 `发布日期 · 已装内容（+N）`；日期用「今天/昨天/N 天前」，<8 天之外显示绝对日期（`VersionDateText`，6 例测试）。`manifest.latest` 接进 `VersionCatalogModel`。
- **清单刷新时间**：`lastRefreshedAt` 持久化，侧边栏底部显示「清单更新于 今天 18:36」。
- **筛选行放大** + 侧边栏可拖拽（260–520pt）。
- **液态玻璃**：新增 `.orzMCPanel()`（macOS/iOS 26+ `glassEffect`，更老系统等效回退）；详情页从 `Form(.grouped)` 改为 `ScrollView` + 两块玻璃面板，对齐由 `Grid` 保证；实例面板末尾分隔线修正。
- 验证：`app`/`app-ios` BUILD SUCCEEDED；`app-test` XCTest 95 + Swift Testing 13 全绿；平台分层与 `git diff --check` 通过；960×593 深色 + 1200×742 亮色自截图核对。
- 仍未提交、未推送、未 bump 指针。

### 2026-10-22 — pi（详情页启动面板重做：路径变浅 + 用 Grid 解决对不齐）

维护者反馈「操作路径深、启动区总对不齐」。重做启动面板（页面结构仍是启动卡片 + 信息卡片）：

- **主按钮上移到卡片标题栏右侧**（`启动客户端/启动服务端`），不用滚到底、不必先选完类型才看到启动；
- **改用 `Grid` 固定 96pt 标签列**取代 `LabeledContent`（分段控件/菜单/输入框内边距不同是"对不齐"的根因）；服务端核心由菜单改为分段控件，一行全是同类选项片；
- **行序 = 操作序**（模式+二级类型 → 玩家名 → Java），服务端保留「账户」行显示说明，面板不塌缩；
- 截图核对 960×593 亮/暗 + 1200×742 深；`app`/`app-ios` BUILD SUCCEEDED、`app-test` XCTest 89 + Swift Testing 13 全绿、平台分层与 `git diff --check` 通过。
- 仍未提交、未推送、未 bump 指针。

### 2026-10-22 — pi（视觉第二轮：侧边栏搜索行 / 列表极简 / 启动区按模式重构）

维护者按截图给出四条意见，全部落地；仍未提交、未推送、未 bump 指针。

- **侧边栏**：新增 `SidebarSearchBar`（搜索框 + 只看正式版 + 刷新，两个单图标按钮同行），删除底部过滤栏与 `.searchable`；列表项只显示版本号（安装状态在行首图标 + 悬停提示）。
- **启动区**：删除「版本」行（标题已有）；**新增客户端类型选择（Vanilla/Fabric）**——此前客户端换 Fabric 在启动区没有任何反馈；模式与类型/核心合并到一行，客户端 3 行 / 服务端 2 行，进度挪到 Start 左侧。
- **详情页**：删除 5 路实例分段控件，改为按 `gameMode` 派生当前实例（客户端 → `版本#Client`，服务端 → 当前核心），切换模式/类型/核心时下方信息区即时跟随。
- **验证**：自截图核对客户端与服务端两种模式的 1200×742 深色布局；`app`/`app-ios` BUILD SUCCEEDED；`app-test` XCTest 89 + Swift Testing 13 全绿；平台分层、`git diff --check` 通过。

### 2026-10-22 — pi（自截图复核：视觉第一轮修正）

维护者反馈"样式还是不满意"并授权我自己截图。`screencapture` 被 TCC 拒绝（无屏幕录制授权），改为调试构建内渲染自己的窗口：新增 `OrzMC/Launcher(MacOS)/Debug/WindowSnapshot.swift`（`#if DEBUG`；`--snapshot` 一次性 / `--snapshot-watch` 常驻请求式；支持 `size`/`appearance`/`settings`/`settingsTab`），Release 不编译。

- **截图确认的真实问题**：macOS 分组 Form 的标签列撑到半行宽 → 标签与控件被拉到两端；`Form` 里空标题 `TextField` 仍占标签列 + 默认右对齐"值" → 输入框文字右对齐、位置偏移（就是维护者说的"文字对齐异常"）。
- **处理**：新增 `OrzMCFieldRowStyle`（固定 96pt 标签列，主窗口/设置四页/远程详情统一）；字段一律 `.labelsHidden()` + 显式 `multilineTextAlignment`；启动区标题做成"卡片标题 + 分隔线"、Start 贴右下角紧凑宽度；侧边栏副标题改「类型 · 前两项 · +N」、未安装行单行；实例栏图标只保留"控制台运行中"用状态色；设置页路径行改单行布局、`@AppStorage` 记住分页。
- **验证**：`app`/`app-ios` BUILD SUCCEEDED；`app-test` XCTest 89 + Swift Testing 13 全绿；平台分层与 `git diff --check` 通过；960/1200pt 深/浅截图对照通过（自测，非维护者验收）。
- **约定更新**：`swift/app/docs/app-ui-design.md` 新增「字段与行布局约定」10 条 + §8.1 快照工具用法；`docs/ui-review-2026-10-22.md` 第五轮记录"看到的现象 → 根因 → 处理"。
- 仍未提交、未推送、未 bump 指针；PR 仍 Draft。

### 2026-10-22 — pi（视觉复审 B 轮：维护者报的 4 条 + V1–V3 落地）

维护者反馈「版本列表不好看 / 顶部按钮区要改 / 启动区排布混乱 / 输入框文字对齐异常」，按 `apple-native-product-design` + `swiftui-pro` 定位并修正；仍未提交、未推送、未 bump 指针。

- **版本列表**：图标改为居中（原来 `.firstTextBaseline` 装 SF Symbol 会低半格）、第二行固定最小高度（行高不再跳）、侧边栏不再用胶囊（类型/已装内容改次要文本）。
- **顶部按钮区**：过滤+刷新从窗口工具栏搬到列表底部栏（`VersionFilterBar`，`.switch` 开关、加载不换图标），删除 `SideBarTool.swift` 与 `sideBarTool` 修饰器。
- **启动区**：三行统一成 `LabeledContent`（Version / Mode / Username|Core / Java），Mode 恢复可见标签，Start 单独一行跨满宽度，加 `.focusSection()`。
- **输入框**：内存字段改基线对齐 + 数值右对齐；控制台 `.plain` 字段补内边距与中心对齐；远程令牌恢复单行；路径/参数等宽改 `.body.monospaced()` 并去掉多余 `.labelsHidden()`。约定写进 `swift/app/docs/app-ui-design.md`（10 条）。
- **V3**：控制台工具栏收敛为「生命周期 4 个 + 溢出菜单」；启动区/详情/设置四页加 `.focusSection()`；标签描边 0.35→0.5、错误/警告 banner 正文改主色；实例分段控件去掉与状态徽标重复的 `●`；设置窗口 560×480 → 600×560。
- **验证**：`app`/`app-ios` BUILD SUCCEEDED（无新增警告）；`app-test` XCTest 89 + Swift Testing 13 全绿；平台分层与 `git diff --check` 通过；新构建已重启（无崩溃报告）。
- **仍待维护者**：视觉与焦点环验收（本轮 4 项均属观感类，未经截图验证）。

### 2026-10-22 — pi（UI/UX 审查清单 A1–A25 / B1–B4 全量落地）

维护者要求把审查报告里的每条发现都处理掉。未提交、未推送、未 bump 指针，PR 仍为 Draft。

- **并发/状态**：`startConnect` 显式 `callbackQueue: .main`；模型不再遵守 WebSocket 协议，改由新的 `ExarotonSocketDelegate`（`@MainActor`）转发；新增 `ConnectionEpoch` 丢弃上一条连接的迟到回调（修「离开详情后仍显示旧断线原因」）；`httpClient` getter → `makeClient() throws` + `clientOrReportError()`；`statusVersion` 取代 `Optional.publisher`；删除两个 3 秒定时器，改用 `RemoteStreamingPolicy`/`RemoteStreamPlan` 的 `reconcileStreams`（只发缺的流指令）。
- **可访问性/本地化**：help 改 `LocalizedStringKey`（实例名进 `accessibilityValue`）、图标按钮补文字标签、Stepper 带标签、`%lld GB` 等 17 条 zh-Hans 文案、tag 字号与状态徽标换行、Copy 状态机 + `Task.sleep` 取代 GCD。
- **布局**：模式选择器改 `minWidth`、设置页路径行 `ViewThatFits` 退化、路径错误随编辑清除、macOS 去掉无效 `.refreshable`、token 显示切换保焦点、控制台正文 `.caption` → `.subheadline`。
- **性能/结构**：安装状态改用 `catalog.installStates`（新增 `hasServer(id:)`），目录清单与存在性移出 body；`BasicInfo.swift` 626 行拆成 6 个文件（新增 `InstanceSection` 等）；打开/删除目录失败不再被 `try?` 吞掉；内存编辑收进 `ExarotonMemorySection`；`@State` 全部 private。
- **验证**：`app`/`app-ios` BUILD SUCCEEDED（无新增警告）；`app-test` XCTest 89 例 + Swift Testing 13 例全绿（本轮新增 8 例）；平台分层与 `git diff --check` 通过；启动一次新构建产物无崩溃报告。
- **仍待维护者**：视觉验收（960/1200pt、亮暗/对比度、焦点环）、真实日志手感、真实 exaroton 失败/限速路径。详见 `swift/app/docs/ui-review-2026-10-22.md` 第三轮一节。


### 2026-10-22 — pi（app 三项未结项收尾：Follow / 远程互斥与失败反馈 / RAM 失败语义）

接手时保持维护者未提交改动不变，未 pull/reset/clean/commit/push，也未 bump 任何子模块指针。本轮把三个“只能靠人眼”的交互拍成**可单测的纯逻辑**，再在视图里接线：

- **控制台 Follow**：新增 `Sources/OrzMCLauncher/ConsoleFollowState.swift`（跟随/暂停/未读/搜索四态）+ 8 例测试。上滚暂停并计数；**用户滚回底部自动恢复**（依据 `NSScrollView.didLiveScrollNotification`，程序滚动不触发）；搜索期间不跟随；结束搜索不自动恢复；「回到最新」= 退搜索+恢复跟随+滚动（滚动等状态生效后执行，Reduce Motion 不带动画）。
- **远程动作互斥/失败反馈**：新增 `Sources/OrzMCRemoteHosting/RemoteActionGate.swift`（实例级在途互斥，生命周期动作与内存变更互斥，首次 `await` 前占用，结束即释放）+ 5 例测试；模型的 `pendingActions`/`pendingMemoryChanges` 改为由 `gate` 提供，换账号 `gate.reset()`。三个生命周期端点收敛到同一实现；成功只承诺“已提交请求”；失败不再弹全局确认框，改为动作区 `OrzMCBanner(.error)` + `Retry`（请求结束即可重发）。
- **RAM 保存失败**：新增 `Sources/OrzMCRemoteHosting/ServerMemoryState.swift`（草稿/已确认/保存中）+ 7 例测试；失败时**确认值不变、草稿保留**，界面继续显示「Unsaved changes」并可重试/Revert；保存中拒绝重复提交；读取失败不再静默隐藏 Memory 行（`Unavailable` + `Retry`）；Stepper 重新编辑会清掉旧错误。新增 7 条 zh-Hans 文案。
- **验证（本机 Air）**：`scripts/swift-check.sh app` 与 `app-ios` 均 `BUILD SUCCEEDED`；`app-test` XCTest 81 例 + Swift Testing 13 例全绿（Launcher 60 / RemoteHosting 16 / Protocol 4 / DesignSystem 1）；`check-platform-split.sh`、`git diff --check` 通过。启动一次本机构建产物冒烟后退出，无新增崩溃报告（本会话 AX 权限不可用，未断言窗口数量）。
- **仍未做**：960/1200pt、亮暗与提高对比度、键盘焦点/焦点环、真实日志下的 Follow 手感、真实 exaroton 失败/限速路径（需 token 与额度）；截图一律由维护者在桌面会话操作。验收清单已写入 `swift/app/docs/ui-review-2026-10-22.md`（「收尾轮」一节）与 `swift/app/docs/console-acceptance.md`。PR #37/#39 仍为 Draft。

### 2026-10-22 — Codex（交接给 pi：GitHub 迭代流程与 UI 后续）

- 本轮新增 `docs/github-iteration-workflow.md`，并在 `CONTRIBUTING.md`、`docs/README.md` 建立入口。选择短分支 + Draft PR + 子模块独立合并 + 父仓库锁定组合；`git diff --check` 和本地 Markdown 链接核对通过。
- `python3 scripts/verify/check.py` 的子模块登记表、一致性 79/79、manifest、能力台账通过；整体因三个既有合规文案漂移失败：`python/README.md`、`swift/lib/OrzMCKit/README.md`、`site/layouts/partials/site-footer.html`。未改动这些文件。
- 交接时父仓库 `feat/ui-refresh-handoff` 相对 origin ahead 6；app `feat/ui-refresh` 在 `b13b422` 与 origin 同步。父仓库 `swift/app`、`tools/OrzMCBackup` 及多个父仓库文件均有未提交改动。不要 pull/reset/clean/覆盖，也不要把 app 子模块内部文件误加到父仓库。
- app 后续仍按 `swift/app/docs/ui-review-2026-10-22.md` 完成受控验证和维护者桌面视觉验收；PR #37/#39 保持 Draft，不自动合并或发版。Swift 后续只走本机 `scripts/swift-check.sh`，不再使用 SSH Air。

### 2026-10-22 — Codex（GitHub 项目迭代流程）

新增 [`docs/github-iteration-workflow.md`](docs/github-iteration-workflow.md)，选定“短生命周期分支 + Draft PR 尽早验证 + 子模块独立合并 + 父仓库显式锁定组合”的 PR 优先流程。依据当前仓库结构、父仓库必需检查约束及 `swift/app` 的 macOS/iOS 双目标 CI，明确了跨仓互链、先合子模块再 bump、GUI 人工验收保持 Draft 的节奏；没有修改 GitHub 仓库设置、分支保护、PR 合并状态或发布状态。文档已加入 `CONTRIBUTING.md` 和 `docs/README.md` 入口。

### 2026-10-22 — Codex（Air 正式仓库与设备分工）

维护者要求把父仓库接力分支放到 Air `~/Documents/OrzMC`，初始化 Swift 相关子模块，并让 app 检出 feat/ui-refresh。Apple UI 后续在该正式仓库继续；bot 后续用于 CLI 与本机可独立完成的工作。接力首先核对两个仓库 Git 状态，读取 app 的 air-ui-handoff-2026-10-22.md；已有未实施审查建议与视觉验收边界保持不变。

### 2026-10-22 — Codex（UI 分支推送与 Air Git 接力）

**完成记录**：app PR https://github.com/OrzMC/OrzMCApp/pull/37；父仓库接力 PR https://github.com/OrzMC/OrzMC/pull/39（均为草稿，未合并）。远端 app SHA 已核对为 b13b422a27cac5be8cc937fdf7dc16e00e3fc41c。Air 已删除 app 构建镜像、app-dd-ios、macOS 编译/索引/依赖缓存和旧 patch 交接包；macOS app-dd 从 3.2G 降为 193M，仅保留仍运行应用所需的 Build/Products，连同其他删除项约释放 5.4GB。新设备须拉取 feat/ui-refresh-handoff，不是仅拉 main。

维护者授权提交推送，并清理 Air 旧临时文件。app 使用 feat/ui-refresh，父仓库使用 feat/ui-refresh-handoff 显式记录单一 app 指针；保留已有 UI 改动和三技能审查建议，未自动合并或发版。app 提交为 `23baf01`（UI 实现）、`b13b422`（设计/接力文档）；本轮 Air macOS/iOS 均 BUILD SUCCEEDED，单测 13/13、平台分层及父组合校验通过。Air 接力以 docs/air-ui-handoff-2026-10-22.md 的 Git 拉取步骤为准；旧构建镜像、iOS DerivedData、macOS 可再生成缓存及 patch 交接包在推送核验后清理；macOS app-dd/Build/Products 因仍有 OrzMC 进程使用而保留。

### 2026-10-21 — pi（macOS UI 梳理 + Settings 崩溃修复，**swift/app 待提交**）

**结果**：完成 macOS 启动器 UI/交互全面梳理，并落地 P0/P1/P2 优化。

1. **Settings 崩溃根因**（air 崩溃报告 `OrzMC-2026-10-21-195204.ips`）：
   `Settings` 只注入了 `app.settings`，但 `SettingsView` 读 `@Environment(AppModel.self)`
   → `EnvironmentValues.subscript` 断言（SIGTRAP）。修复为 `.environment(app)`，
   并把 `AppModel` 提到 `OrzMCApp` 的 `@State`，保证主窗口 / Settings / 控制台窗口 / 远程窗口共享同一实例。
2. **多窗口边界**：
   - 主启动器 `WindowGroup` → `Window`，移除 File > New Window（复制 `AppModel` 会破坏进程登记/探活/控制台）；
   - 新增 `WindowGroup(for: ConsoleTarget.self)`：控制台可 `Open in New Window`，共享同一份控制台缓冲；
   - 新增 `Window(id:"remote")`：Exaroton 远程托管独立窗口，不再混进本机实例导航；
   - 新增 Window > Show Main Window（⌘0）。已用 AppleScript 核对中文菜单：
     无 File 菜单，`设置…` / `显示边栏` / `全部停止服务器…` / `显示主窗口` 均在。
3. **信息架构**：侧边栏只负责版本列表 + 搜索/过滤/刷新；启动配置移到详情页顶部
   `LaunchControls`（压成 3 行：版本+模式 / Java 状态 / 用户名或核心 + Start）；
   详情页 Terminate/Delete 收进 `⋯` 菜单；文本框统一为“行标签 + 示例 prompt”，不再重复同一文案。
4. **设计系统**：新增 `OrzMCTheme` / `OrzMCStatusBadge` / `OrzMCTag` / `OrzMCBanner` /
   `.consoleSurface()`；设置页四页 `TabView` + 系统 Form/Section/LabeledContent；控制台深色模式修复。
5. **交互修复**：控制台搜索 + 导出日志 + Follow；Exaroton 条件加载遮罩、`NavigationLink`、
   sheet 副作用、日志上限 2000 行、加载 RAM 不再重复 changeRAM；插件管理改用 `NavigationStack` + `.searchable`；
   外部链接走默认浏览器；删除未使用的 SwiftUIX / FeedbackToAuthor；
   远程服务器列表/详情改为状态徽标 + 软件/玩家标签 + 地址行 + 指标标签，Actions 用 Start 主按钮 + Stop/Restart
   `ControlGroup`，额度池使用大额度卡。
6. **本地化**：`Localizable.xcstrings` 补齐 200+ zh-Hans 条目（静态 UI、设置、确认文案、状态）；
   引擎错误长文案仍为英文（错误码已保留）。
7. **顺带修复**：详情页 1.5s 只重算当前版本；侧边栏重复启动；停止全部忙碌标记；⌘C/⌘S 快捷键冲突。
8. **验证**：`scripts/air/run.sh app`（macOS）与 `app-ios` 构建绿；`app-test` 绿；
   `check-platform-split.sh` 绿。完整梳理与后续 P2 路线见
   [`swift/app/docs/app-ui-design.md`](swift/app/docs/app-ui-design.md)；
   Codex 交接文档与提示词见 [`swift/app/docs/ui-handoff.md`](swift/app/docs/ui-handoff.md)。
9. **状态**：`swift/app` 有未提交改动（未开分支/未推送），父仓库暂不 bump 指针。

### 2026-10-22 — pi（远端 issue/PR 巡检后的三件事：合规标记口径 / 发布 2.18.1 / plugin 告警噪音）

先做了一次全组织巡检（父仓库 + 21 子模块 + 被引用的 OrzGeeker 仓库）：open issue 11 条、open PR 10 条。
按维护者指定的顺序处理了三件，其余（Swift/App 类、上游 thanos、内容类）留在 §1「下一步」或归 Air。

**① 合规标记口径（`OrzMCApp#32` 关闭）**
- 结论：**生成器没缺** —— `scripts/sync_compliance.py` + `docs/compliance/` 在父仓库，写穿 5 处标记块
  + 3 个整文件，`--check` 一直绿。误报的成因是标记注释写成了**子仓库里不存在的相对路径**
  （`scripts/sync_compliance.py; edit docs/compliance/`）。
- 改 `GENERATED_NOTE` 指名父仓库 → 重新生成，父仓库 + 4 个子仓库各一笔：
  `OrzPythonMC#101`、`OrzMCKit#97`、`OrzMCApp#38`、`OrzMCSite#8`，父仓库 `c36bc44`（脚本 + README + 四指针）。
- 同步在 `.github#3`（组织级合规自查）留言纠正同一条误判，并给出「扩面覆盖 16 个仓库」的分期建议
  （对外发布渠道优先；`LoginSecurity` 是上游 fork，建议不动 README）。

**② 发布 `python` 2.18.1（把早上的下载修复真正交付）**
- release PR `#99` 因 GITHUB_TOKEN 不触发工作流而没有检查（老坑）→ close/reopen 补触发 → 11 项检查绿 → squash 合并。
- 流水线：tag `v2.18.1` → 6 平台 PyInstaller 资产 → PyPI 双包（`orzmc` / `orzmc-app` 均 2.18.1）→
  Release 非 draft → 官网 pages 重新部署。**无需「升级须知」**（旧版只是错误文案误导，不涉及迁移）。
- 父仓库指针 `43d0729` bump 到 `5e70745`。

**③ `OrzMCPlugin` 的 Dependabot 每日红（`#535`）**
- 根因不是依赖没修：**依赖图里残留了已删除的 `pom.xml` manifest**（2026-01-09 `6a246ce` 移除 Maven 构建，
  之后只有 Gradle）→ security update 作业每次都 `pom.xml not found` → 必红且**无法用 PR 修**
  （`dependabot.yml` 的 `ignore` 也只能阻止开 PR，作业照样失败）。
- 处置（现 0 open）：maven 6 条 dismiss `not_used`（manifest 已不存在；实际依赖 log4j 2.26.1 / snakeyaml 2.7
  均在已修版之上）；npm `uuid` 1 条 dismiss `tolerable_risk`（经 mineflayer→prismarine-auth→@azure/msal-node
  传入，Dependabot 自报 `fix_available=false`，唯一修复会把 mineflayer 降级到 1.4.0；漏洞只在调用方
  自带 buffer 的 v3/v5/v6，msal-node 只用 v4，且 e2e 依赖不随 jar 分发）。
- 新增 `plugin/docs/dev/dependency-security-alerts.md`（处置表 + 复核条件 + 核对命令）+ 索引入口 +
  AGENTS 指针，合入 `develop`（`211c203`）。**父仓库不 bump**：plugin 按 `main` 钉，等下一次里程碑 develop→main。

**④ 顺手合掉两个可直合的依赖 PR（`rust-thanos` `#3`/`#4`）**
- `#3` lz4_flex 0.11.5→0.11.6、`#4` time 0.3.44→0.3.55（都只动 `Cargo.lock`，CI 3 平台绿）→ squash 合并；
- 合并后在本地补跑该仓库的完整门禁：`cargo check --locked` / `cargo test`（14 例）/ `cargo fmt --check` /
  `cargo clippy --all-targets --all-features -D warnings` 全绿，main CI 绿；
- 父仓库指针 bump 到 `b79defb`。

**⑤ `OrzGeeker/OrzSwiftKit#1`（swift-nio 2.73 → 2.104）**
- PR 原是 `CONFLICTING`（lock 与 main 的 `Package.resolved` 打架）→ 留言 `@dependabot rebase`，
  dependabot 顺带把目标从 2.102 提到 **2.104.0**，并连带 swift-system 1.3.2→1.8.1（都是 console-kit 的传递依赖）。
- 该仓库只有 `Package.resolved` 变更；**库的 lock 不影响下游解析**（SwiftPM 忽略依赖包的 `Package.resolved`），
  所以消费侧（`OrzMCKit`/app）不受影响，价值在于我们自己的 CI 会提前跑新 nio。
- CI `build-test`（macos-15）1m52s 绿 → `gh pr merge --admin`（OrzGeeker 组织要求 1 review，`--admin` 是既有惯例）。
- ⚠️ **副作用（已实测）**：nio ≥ 2.100 的 manifest 是 `swift-tools-version:6.1` ⇒ **OrzSwiftKit 的构建下限抬到
  Swift 6.1**。本机 6.0.3 工具链跑 `swift package resolve` 直接失败，6.5-dev 工具链在 macOS 13 上起不来，
  故 **「本机可单独编译 OrzSwiftKit」这条已作废**（§2.5 已改）。要恢复本机编译只有两条路：
  钉回 nio < 2.100（会与 dependabot 长期对抗）或本机升到 macOS 15+。CI/air（6.1.2 / 6.4）不受影响。

**⑥ 顺带纠正一处文档坑 + 明确「本机能做什么」**
- 发现上一笔 `OrzPythonMC#100` 写的示例 `--cli 'uv run orzmc'` **跑不起来**：harness 的每个用例都从
  **自己的沙箱 cwd** 启动（HOME/XDG 也换掉），命令串里的相对路径按沙箱解析 → `No such file or directory`。
  改为 CI 同款（`bin="$(uv run … shutil.which("orzmc"))"` + `--cli "$bin"`，25 例 64s 全过），`#102` 已合；
  父仓库 `scripts/accept/cli.py` 的 `build_cli` docstring 补了这条 cwd 说明（行为不变）。
- 在 §2.5 增「**本地能力矩阵**」：CLI 主线（Python）本机是全能的（行为验收 / 单测 / 一致性 79 例用
  python adapter 也能本地跑 / 命令面与台账校验）；Swift 侧只少了整包编译，静态与语法检查照旧（0.6s / 11s）。
  —— 避免把「OrzSwiftKit 不能本地编译」误读成「CLI 本地验证没了」。

### 2026-10-22 — pi（本机 CLI 线：HTTP 状态错误不再误报「中途断开」+ 夜间验收复绿）

**上下文**：按新设备分工开工（Apple GUI 归 Air；bot 本机只做 CLI 与可独立完成的迭代，不连 Air/Windows）。
入手点不是新功能，而是 `OrzPythonMC` 上**挂了一周的夜间验收红**（issue #35，自 2026-10-15 起每晚追加一条）。

**定位**：6 个平台里只有 `windows-11-arm` 失败，7 个 case 全挂在同一句
「下载 Temurin JRE 25 (windows/aarch64) → 下载中途多次断开，已重试 4 次仍失败」。
实测该 URL **就是 404**：Temurin 有 `windows/aarch64` 的 Java 21，**没有 25**（jre/jdk 都无）。

**两个真 bug（各一半责任）**：
1. **实现侧**：`HttpClient.stream_range` 把 `raise_for_status()` 抛的 `requests.HTTPError`（4xx/5xx）
   当成「流式中途断连」续传重试 → 4 次无谓请求 + 统一报「中途断开」，真因被掩盖。
   修：新增 `HttpStatusError(RuntimeError)`（带 `status`/`url`，消息保留 requests 原文），
   4xx/5xx **立即失败**；唯一例外是续传回 **416 且本地已取全** → 按成功返回（那正是「下完了」）。
   放弃续传时消息补上最后一次底层错误。`JavaEnv` 再对 404 补一句可执行提示（上游未发布该平台构建）。
2. **判定侧**：harness `log_contains` 只把空白压成**一个空格** → rich 软换行把长 URL 切开、断点落在
   标记内部时仍匹配不到 `UP(gap)` 标记。修：两侧都**去掉全部空白**再比（标记不依赖空格）。
3. 顺带：新增根 `conftest.py` autouse 钉 `ORZMC_RUNTIME=python`。本机状态目录里存着
   早前实验的 Swift 通道 → `main()` 把 argv 交给 Swift 真身、POSIX 下 `os.execv`，**把 pytest 进程整个换掉**：
   退出码 1、无 traceback、无 summary，用例凭空消失（`test_usage_error_exit_code_is_one` 起整批没了）。
   基线（stash 后）同样复现 ⇒ 与本次修复无关，是测试非封闭；CI 一直钉着这个变量，现在本地一致。

**验证**：`python` `ruff`/`mypy`/`pytest`（485 passed, 3 skipped）/ 父仓库 `scripts/accept/cli.py`（25 passed）；
PR `OrzPythonMC#98` 全检查绿后合并（`c78eff6`）。真机层面：本地用真实网络打那个 404 URL，
确认一次请求即报 `404 Client Error: Not Found for url: …`（旧行为：4 次重试 + 错误文案）。
随后手动 dispatch `acceptance.yml` on main（run `39674450183`）：**6 平台全绿**，
`windows-11-arm` 7/7 判 `UP(gap)`（警告），issue #35 已在本条结论后关闭。

**另一笔（文案漂移）**：`scripts/accept_cli.py` 早按 M2 收口到父仓库 `scripts/accept/cli.py`，但
`python/{AGENTS,CONTRIBUTING,README}.md` 里 11 处仍写本仓库旧路径（照着敲直接 No such file，且漏 `--frozen`）→
PR `OrzPythonMC#100`（纯文档）。

**留给下一会话（需拍板 / 需远端）**：
- **Windows ARM64 跑最新版要 Java 25，Temurin 不给**。加**厂商回退**（Microsoft OpenJDK 有
  `windows-aarch64` 的 25）就能真跑；不加则该平台只能自装 Java。产品决定，未动。
- **Swift 侧同构隐患（需 air 构建）**：`OrzSwiftKit/Transfer` 对非 206 响应一律当「完整正文」（含 404），
  最终表现为 size/hash 不符而不是清楚的状态码错误；对齐 Python 需要远端构建验证，本机不做。

### 2026-10-21 — pi（服务端运维收口：控制台 / 生命周期 / 插件 / 目录，**验收通过**）

**结果**：维护者验收通过。四轮改动合起来把"服务端在 GUI 里能不能好好管"这件事做完整了。

1. **Paper 控制台命令无效**（`OrzMCKit#94`）：根因 `PaperServer.start()` 带了 `--noconsole`
   （Paper 的 *Disables the console*）→ 完全不读 stdin。air 真实 Paper 26.3 A/B 实测：
   去掉后 `list`/`say`/`stop` 全通；带 `--nojline` 保留（不加时 JLine 会打一条非 MC 格式告警进 GUI）。
2. **Swift CLI 服务端收不到命令**（`OrzSwiftKit#19` 0.0.19 + `OrzMCKit#95`）：`ProcessRunner` 建了 stdin 管道
   而 CLI 从不写 → 命令石沉。加 `inheritStandardInput`，CLI 让子进程继承终端 stdin（与 Python `Popen` 语义一致）。
   真机验证：`| orzmc server --type paper` 发 `list`/`say` 有回应。
3. **生命周期四操作 + 插件管理 + 目录**（`OrzMCApp#34`、`OrzMCKit#96`、`OrzSwiftKit#20` 0.0.20）：
   - 启动/重启/停止（送 `stop` 优雅退出）/终止（SIGTERM→SIGKILL）；`InstanceActivity` + `…Availability` 防连点；
     无句柄（上个会话启动的实例）只能终止，UI 灰掉停止；`InstanceLifecycleTests` 6 例；
   - 插件下载/更新并入 **Plugins 目录条目**（`Manage Plugins` 面板），**新装 → `plugins/`、
     更新 → `plugins/update/`**（Paper `update-folder`）；`PluginInstaller` 10 例；
   - 详情页每 1.5s 复核目录存在性（服务端自建 `world/`、插件 `update/` 立即出现）。
4. **UI 与体验修正**（`OrzMCApp#36`、`OrzMCKit` 常用目录 + `ServerProperties`、`OrzMCApp#35`）：
   - 目录条目只留「图标 + 标题 + 一句说明 + 打开按钮」（路径进悬停提示）；
   - 各核心常用目录（Paper: plugins+更新队列；Fabric/Forge: mods+config；全部: 根/世界/日志，
     **世界目录读 `server.properties` 的 `level-name`**）；客户端 Game/Logs/Saves/Mods/ResourcePacks；
   - **选中行里禁用 `Color.accentColor`**（与选中背景同色 → 标签隐身），改语义色；
   - 详情页顶部实例切换器（装 2 个以上才出现），四核心+客户端不再铺一屏；
   - 控制台页补四操作；客户端控制台只读；
   - **停止全部改为优雅**：只对有句柄的实例送 `stop`，无句柄的**不动**并列出名字；「Terminate All」需显式选择；
     无句柄「终止」= SIGTERM→10s→SIGKILL；无句柄「重启」直接报错（避免起第二份撞端口）。

**遗留**：跨语言 `auth.lock` 真机对抢未测；正版登录改道仍待定范围。

### 2026-10-21 — pi（服务端控制台：日志 + 命令输入，跨三仓）

用户要求"先做服务端控制台输出，同时接受用户输入命令"。分三层落地，一次 bump 三个指针。

| 层 | 仓库 | 改动 |
|---|---|---|
| 送命令 | `OrzSwiftKit` **0.0.18**（`#18`） | `ManagedProcess.send(_:)`：往子进程 stdin 写一行（自动补 `\n`；进程不在返回 false）。之前 stdin 私有，外部只能 `stop()` |
| 给日志 | `OrzMCKit`（`#91`） | `ServerInfo.onServerLog`：无 ConsoleKit 控制台的前端（GUI）拿运行期 stdout+stderr 合流；转给 `ProcessRunner.run(onLine:)`。CLI 不传 → 行为不变 |
| 显示/输入 | `swift/app`（`#30`） | `ServerConsoleModel` + `ServerConsoleView`：去 ANSI、按行切、`\r` 覆盖、限 2000 行、可复制、自动滚动；输入框 + ↑↓ 历史 + 命令回显；进程退出自动 detach 并清登记。入口：详情页 ⌘⇧L |

**关键设计**：服务端输出是**字节块**（半行/多行/带颜色码/进度条用 `\r` 自刷新），
这些全在 `ServerConsoleBuffer`（`Sources/OrzMCLauncher`，**9 个单测**）里处理干净，视图只渲染成品。

**踩到的工具坑（记住）**：
1. **`Package.resolved` 必须在本地改**：pre-push 钩子会 `rsync --delete` 把本地树盖到 air，
   在 air 上 `swift package update` 的结果会被下次同步冲掉。本地又跑不了解析（CLT 13.3 +
   macOS 14 SDK 缺失）→ 正确做法：单独目录 resolve（`~/orzmc-build/OrzMCKit-resolve`）后 scp 回本地。
2. `OrzGeeker/OrzSwiftKit` 的分支保护**要求 1 个 review**（与 OrzMC 组织的"admin 可绕过"不同）→ 用 `gh pr merge --admin`。
3. 可移植性检查会拦测试里写死的 `/bin/sh` → 加进 `scripts/verify/portability.py` 的 `ABS_PATH_ALLOW`（附理由）。

**验收（2026-10-21 追加）**：本机是 **macOS 13.7.8 / x86_64**，而 app 是 `MACOSX_DEPLOYMENT_TARGET = 14.0`
→ **装回本机也起不来**（不是架构问题）。所以：
- 自动验收：`ServerConsoleModel` 下沉到 `Sources/OrzMCLauncher`（依赖倒置成 `ServerConsoleProcess` 协议，
  共用目标不引 JokerKits）+ `ServerConsoleEndToEndTests` 3 例（真子进程读命令、回 ANSI 日志、`stop` 退出、
  退出后拒绝发送、半行 flush）→ 任何 `swift test` 环境都能跑（`OrzMCApp#33`）；
- 人工验收：`scripts/air/run.sh app-run` 在 air 上打开（实测 pid 25003），清单见
  `swift/app/docs/console-acceptance.md`（8 步：起服务端 → ⌘⇧L → `say hello` → ↑↓ 历史 → `op` → `stop` → Clear）。
- SSH 会话**拿不到截图**（没有屏幕录制/辅助功能权限）→ 观感只能人眼看。

**按验收意见改（2026-10-21 追加）**：控制台原入口在导航条上（= 全局一个），与"支持四种核心、
可同时多实例"矛盾。改为**一实例一控制台**（`OrzMCApp#34`）：
- `ServerConsoleRegistry` 按 `ConsoleInstanceKey`（`版本#核心`，与进程登记表同构）各持一个模型；
  `detach` 只解绑、**日志保留**；`remove` 仅在该实例文件被删时清空；
- 入口搬到**每个服务端实例的 section 标题行**（运行中绿色实心终端图标），四种核心各自独立；
  导航条的全局入口已移除；
- 控制台标题 `Console — 1.21.5 Paper`；停服显示 `Stopped … (log is kept)`；
- 测试 `ServerConsoleRegistryTests` 6 例（实例隔离 / 同 key 复用 / detach 保日志 / remove 只清自己）。

**客户端控制台（2026-10-21 补齐）**：`ClientInfo.onClientLog`（`OrzMCKit#93`）+ GUI 侧
`GUIClient.startWithProcess()` 返回进程句柄 → 客户端实例的控制台（键 `版本#Client`）与 4 种服务端同构：
日志来自引擎、命令经 `ManagedProcess.send`、退出自动解绑并保留日志。
`ConsoleInstanceKey.softwareId` 更名 `instanceId`（服务端=核心名，客户端=`Client`）。
测试：`ClientConsoleEndToEndTests`（假客户端收日志/`chat hello`/`quit` 退出）+ 注册表隔离用例。

**详情页实例栏（2026-10-21 二次验收后改）**：
- 布局：左「实例名 + 运行状态徽标」、右「控制台 / 停止 / 删除」图标按钮；
- **客户端也有运行状态**（以 `版本#Client` 控制台挂载进程为准，游戏退出即 Stopped）；
- **高危操作统一二次确认**（新增 `RiskyAction`）：删服务端/客户端文件（弹窗带路径 + 不可恢复）、
  停止单个服务端（玩家会掉线）、菜单「Stop All Servers」（原来**无确认**直接执行）；
- **防连点**：`busyInstanceId` 期间该实例按钮全禁用 + 转圈；`perform` 里再 `guard` 一次；
- 修 `AppModel.stopServer` 按 `versionId` 定位（原来用当前选中项，确认期间切版本会杀错实例）。

**Paper 控制台命令无效（2026-10-21 用户实测后修）**：`PaperServer.start()` 的 jar 参数带了
**`--noconsole`**（Paper 文档：*Disables the console*）→ Paper 完全不读 stdin，GUI/CLI 送的
`list`/`say`/`help` 全被丢弃（Vanilla 没这个 flag，所以正常）；`stop` 也没人读 → 停服要等 60s 超时。
修复：抽出 `PaperServer.launchArguments(onlineMode:)`，去掉 `--noconsole`，保留 `--nojline`（只关 JLine 行编辑）。
**air 上真实 Paper 26.3 A/B 实测**：无 `--noconsole` → `There are 0 of a max of 20 players online` +
`[Server] hello-from-console`；带 `--noconsole` → 两条均无输出。防回归 `PaperLaunchArgumentTests` 3 例。

**`--nojline` 该不该留（2026-10-21 实测）**：**留**。同一 Paper 26.3 两组对比（都通过 stdin 管道喂命令）：
`list`/`say`/`stop` **功能完全一致**；差别只有——不加时 Paper 走 JLine，会打一条
`2026-10-21T…Z ServerMain WARN Advanced terminal features are not available in this environment`
（非 MC 格式、不走 `[HH:mm:ss INFO]` 前缀），直接进 GUI 控制台像故障。`--nojline` 只关行编辑、
不影响读 stdin；GUI 有自研命令历史，不需要 JLine。

**CLI 服务端控制台（2026-10-21 补）**：`--noconsole` 修掉后暴露另一半——**Swift CLI 从来收不到服务端命令**
（`ProcessRunner` 建了 stdin 管道，CLI 只 `waitForExit`、从不写；Python 侧因子进程继承终端所以一直能用）。
修法：`OrzSwiftKit 0.0.19` 的 `run(inheritStandardInput:)` + `ManagedProcess.canSendCommands`；
`ServerInfo.inheritStandardInput`（CLI `server` 传 `true`、GUI 保持 `false`）。
air 真机验证：`( echo list; echo say hi ) | orzmc server --type paper` → `There are 0 of a max of 20 players online`
+ `[Server] hello-from-cli`（修复前两条都没有）。现在 **Python CLI / Swift CLI / GUI 三面都能用控制台**。

**服务端四操作生命周期（2026-10-21，`OrzMCApp#34`）**：以前「停止」= `kill <pid>`（SIGTERM 硬杀）。
现在：**启动**（无确认）/ **重启**（优雅停 → 等退出 → 起，确认）/ **停止**（送控制台 `stop`，
让服务端自己存档退出，超时才升级 SIGTERM→SIGKILL，确认）/ **终止**（立刻 SIGTERM→SIGKILL，
可能丢存档，确认）。要点：
- `AppModel` 持有本次运行启的**进程句柄**（`[ConsoleInstanceKey: ManagedProcess]`）——登记表只有 PID，
  送不进 `stop`；进程退出监听里清句柄；
- **App 重启后接管**以前启的服务端 → 句柄已丢 → `canStop = false`，只能「终止」（UI 灰掉停止按钮）；
- `InstanceActivity`（starting/stopping/terminating/restarting）→ 状态徽标 + 全按钮禁用防连点；
- 纯决策逻辑在 `Sources/OrzMCLauncher/InstanceLifecycle.swift`（6 例单测）；
- OrzSwiftKit `0.0.20` 提供 `terminate()`（SIGTERM→SIGKILL）/`forceKill()`/`waitForExit(timeout:)`。
  ⚠️ 方法别叫 `kill()`：同类型里的同名方法会抢全局 `kill(2)` 解析（实测编译报错）。

**插件管理（2026-10-21，`OrzMCKit#96` + `OrzMCApp#34`）**：插件下载**并入 Plugins 目录条目**
（`Manage Plugins` 面板），不再单列一条 `PluginsUpdate` 目录项、也不再"长按批量下 15 个到 update/"。
目标目录按 **Paper 官方 update-folder 机制**：
- 没装过 → `plugins/`（下次启动加载）；
- 已装（更新） → `plugins/update/`（**下次重启时**服务端自动替换旧 jar）。
引擎侧 `PluginInstaller`（`OrzMCKit`）：扫描生效中的 jar（忽略 `.jar.disabled`、不进 `update/`）、
jar↔项目归一化前缀匹配（`ViaVersion` 不误配 `ViaBackwards`）、从文件名认版本、`state` 三态、
`target(for:)` 决策；`PaperPlugin.installPlan(...)` 一次给出"装到哪 + 下载项"。10 例单测。
面板只在点 `Check Updates` 时联网（15 次请求），`Update All` 顺序更新。

**详情页目录实时感知（2026-10-21）**：以前只在切换版本时算一次目录状态 → 服务端自建的 `world/`、
插件装出来的 `update/` 要切版本才看得见。现在详情页可见期间 `.task` 每 **1.5s** `refreshInstallStates()`
（纯 `stat`，无网络/无子进程），视图消失自动取消。

**详情页目录条目与常用目录（2026-10-21，`OrzMCApp#35`）**：目录条目不显示路径（前缀人人一样又占地方），
改成 **图标 + 标题 + 一句说明 + 右侧「打开」**，路径在悬停提示里、双击整行也能开；不存在的目录显示
`not created yet` 灰标、打开按钮禁用。`Manage Plugins` 从 Plugins 行上移到 **section 表头**（拼图图标）。
各核心的常用目录由 `GameDirectoryCatalog`（`Sources/OrzMCLauncher`，7 例单测）决定：
全部服务端 = 根/世界/日志；Paper = + plugins/plugins-update；Fabric/Forge = + mods/config；Vanilla 只有三项；
客户端 = Game/Logs/Saves/（Fabric）Mods/Resource Packs。**世界目录读 `server.properties` 的 `level-name`**
（`ServerProperties`，8 例单测），不写死 `world`。排版：版本列表等宽数字 + 紧凑徽标；详情页标题层级、
按钮三组（看/管｜生命周期｜删除）加细分隔线。

**UI 修正轮（2026-10-21，`OrzMCApp#36`）**：
- **侧边栏选中行里千万别用 `Color.accentColor`**：选中背景就是 accentColor，同色互相覆盖 →
  版本号下面的 `Client`/`Paper` 标签直接隐身。行内元素一律用语义色（`.primary`/`.secondary`/`.tertiary`）；
- **详情页一次只看一个实例**：顶部 segmented 切换器（装 2 个以上才出现，带 `●` 运行标记），
  只渲染当前实例的目录 + 表头；默认聚焦"正在运行的"实例。四核心+客户端全装时不再一屏 5 段；
- **控制台页也有四操作**（服务端）：启动/重启/停止/终止 + `Stopping…` 进行态；**客户端控制台只读**
  （底部写明"the Minecraft client does not accept console commands"）；
- **停止全部 = 优雅**：只对有句柄的实例送 `stop`；上个会话启动、无句柄的实例**不动**、只列名字；
  「Terminate All」需用户显式选择；无句柄「终止」= `SIGTERM` → 10s → `SIGKILL`；
  无句柄「重启」直接报错（否则会起第二份撞端口）。

**工具坑（务必记住）**：`.pbxproj` 的 `/* Begin PBXFileReference section */` 标记一旦丢失，
后加文件会只有 `PBXBuildFile` 条目而无 `PBXFileReference` → **Xcode 静默跳过该文件**，
表现为「cannot find type X，而 X 明明就在磁盘上」。2016-10-21 踩过一次，已补回并加校验意识：
新增 Swift 文件后要确认三处都在（fileRef / buildFile / Sources phase）。

**待办**：CLI 侧本来就有终端，不需要控制台；GUI 若要"自动滚到底开关/日志导出"再说。

### 2026-10-20 — pi（macOS 启动器按评估重构：P0 全修 + 拆上帝对象 + 多实例）

对 macOS 侧做了代码审查（见对话），按结论四步走完，全部合在 `OrzMCApp#29`。

**P0（用户可感）**
1. **每秒一个 `ps` 子进程 → `kill(pid, 0)`**：旧链路 `BasicInfo` 1Hz `Timer` → `Shell.allRunningServerPids()`
   （`ps` 全机搜 `nogui`）。既耗 CPU，又把**别人启动的**服务端算成自己的（`Stop All` 误杀）。
2. **进程登记落盘**：`~/Library/Application Support/OrzMC/servers.json`（原子写），重启不失忆。
3. **错误保留规范错误码**：`CodedError` + `LauncherError.wrap(_:fallbackCode:)` → UI 显示「人话 (E_VERIFY)」。
4. **内存/客户端类型可配**：内存校验复用引擎 `MemorySpec`；**Fabric 客户端**以前根本装不出来
   （`ClientInfo.type` 吃默认值）。

**结构（Step 2–3）**：390 行 `GameModel` → 六个聚焦模型 + `AppModel` 组合根
（`docs/app-launcher-architecture.md`）。顺带：进度收成单一 `LaunchProgressState`；`filtered` 改计算属性；
`GameList` 不再在 body 里逐行 3 次 stat；`GameType`(client/server) 更名 `GameMode` 消除与引擎 `Game.GameType` 的歧义；
删掉三个死文件（`LauncherServices.swift` / `New/RemoteServer.swift` / `VersionFilterService.swift`）。

**多实例（Step 4）**：`settings.rootDir` 透传到 `ClientInfo`/`ServerInfo`/`GamePlan.*(root:)`/JRE 扫描；
设置页可手填/选目录/回默认；改根自动重算"装了什么"并重置 JRE 与进程视图。

**测试**：新增 5 个测试文件共 22 例（进度语义、安装扫描、进程登记落盘/探活、错误码映射、过滤规则），
`swift test` 四包全绿；macOS + iOS 模拟器构建绿；平台分层校验绿。

**工具坑（已修进 `scripts/air/run.sh app`）**：air 的 app 车道曾**静默用旧版 OrzMCKit** ——
SwiftPM 缓存 bare repo 的 `main` 落后 + `-resolvePackageDependencies` 没带 `-derivedDataPath`
（于是删锁也没用，解析走默认 DerivedData 里的旧状态），表现为「引擎里明明有的 API 报 cannot find in scope」。
现在：刷新缓存分支 ref + 清 DerivedData 内 checkout/workspace-state + 解析带 `-derivedDataPath`。

### 2026-10-20 — pi（swift/app：surface 接通 + iOS 进 CI + 平台分层）

用户定了三件事：① 登录界面**先不动**（等 authlib-injector 方向）；② **GUI 要接 `install.conf.surface`**；
③ iOS 与 macOS 功能不完全相同，**相同的收敛后迭代、不同的单独迭代**。

**1. `install.conf.surface` 接通（`OrzMCApp#27`）**
- 之前只"用一次"：安装时传 `ORZMC_SURFACE=gui`、界面上翻成一句文案。现在是一等公民：
  状态区显示 surface / source（反推通道 Python CLI vs Swift CLI）/ `completion_file` / 记录落点 / 真身是否在；
- **升级不再重跑安装器**：有真身时默认动作是 `orzmc update --yes` —— 它保留 `surface`/`source`，
  所以"由终端安装"的记录不会被 GUI 静默改写成 `gui`；重装降为菜单里的次要入口（确认框明说会改写归属）；
- **卸载** = `orzmc uninstall --yes`；真身缺失 → 告警 + 只给重装；旧记录缺 surface → 如实显示"未知"，不猜成 `cli`；
- 判定逻辑落在**平台无关**的 `Sources/OrzMCLauncher/InstallRecordView.swift`（+4 单测），GUI 只留展示与进程调用。

**2. iOS 进 CI + 平台分层（`OrzMCApp#28`）**
- **真问题**：`ci.yml` 只构建 `platform=macOS` → **iOS 代码路径从没被构建过**（手工实测是绿的，但那是运气）。
  改 matrix：macOS + iOS 模拟器（缓存 key 按平台分），`fail-fast: false`。
- 新增 `docs/app-platform-split.md`（判定树）+ `scripts/check-platform-split.sh`（`Sources/*` 禁
  `import AppKit`/`UIKit`），作为秒级 job 先跑。
- 布局纠偏：`OrzMC/MobileHelper(iOS)/Protocol` → `Sources/OrzMCProtocol`（本来就是 iOS 专用 SwiftPM 目标）。
- **收敛现状**：Exaroton 面板是真共用（一个多平台 target 编两遍）；版本目录/JRE 判定/版本过滤/
  `install.conf` 语义是平台无关逻辑（`Sources/OrzMCLauncher`）；SLP/RCON/Query 是 iOS 专用独立目标。
  **"共用"的边界在逻辑，不在 UI**。

**3. air 车道扩展**：`app`（macOS）/`app-ios`（iOS 模拟器）/`app-test`（swift test）/`app-clean`。

### 2026-10-20 — pi（收口清理 + swift/app 迭代车道就位）

**1. 工作区与分支清理（全 21 子模块扫过）**
- 未提交改动：**0 处**（父仓库与所有子模块）；
- 44 个本地残留分支 / 24 个远端残留分支：全部核实为**已合并 PR**（其中 3 个 `git cherry` 报"未落地"是
  squash 合并导致的 patch-id 误报，PR 状态均 `MERGED`）→ 已全部删除；
- `plugin` 之前处于 detached HEAD（指向 `origin/main` 同一点）→ 已 `switch main` 归位；
- 合并 **8 个已绿的 dependabot PR**：`OrzMCPlugin#533/#534`（目标是 `develop`，不影响父指针）、
  `OrzMCBackup#54/#57/#58/#59/#60`、`rust-thanos#2` → bump `tools/OrzMCBackup`(`2d10606`)、`tools/rust-thanos`(`c4ffc4c`)。
- **剩 3 个 PR 未动**（派生仓库、无 CI，需你定）：`LoginSecurity#1`（log4j 2.17.2→2.25.4，安全修复）、
  `LoginSecurity#2`（sqlite-jdbc 3.7.2→3.41.2.2，跨大版本）、`EzShops#3`（mysql-connector-j 8.2.0）。

**2. `swift/app` 迭代车道（关键：不然每轮迭代要等 4 分钟 CI）**
- `scripts/air/run.sh` 新增 **`app` / `app-clean`**：rsync `swift/app` → air，`xcodebuild build`
  （免签名），DerivedData 固定 `~/orzmc-build/app-dd` 保增量。实测**首轮 1m、增量 17s**；产物
  `~/orzmc-build/app-dd/Build/Products/Debug/OrzMC.app`。
- **踩到一个坑并已内建规避**：app 仓库里的 `OrzMC.xcodeproj/.../Package.resolved` 把 `orzmcKit` 钉在旧
  revision（`1244125a`），直接 build 会报一片「`GameType` 没有 `fabric`」「找不到 `LaunchProgress`/`ManagedProcess`」
  的**假失败**。CI 的做法是每次删锁重解析（HEAD 制），车道照做（只删远端副本，不动本地仓库文件）。
- 顺带确认：app `main` 对 **OrzMCKit 0.20.0** 可正常编译（CI `workflow_dispatch` 也绿）。

**3. 文档纠偏**
- `frontends.md` §7.2 还写着「D14：Swift 收敛为唯一 CLI 方向」「Python 维护模式」——**已作废**的口径，
  改为现行分发口径（Python 对外分发 / Swift pre-release 同步迭代 / GUI 正式分发）。
- `AGENTS.md` §8.2 补 `air` 的 app 车道与那个 `Package.resolved` 坑。

### 2026-10-20 — pi（两项加固落地：auth.json 跨进程锁 + runtime 真身回滚）

**1. `auth.json` 跨进程写锁（`frontends.md` 新增 F4.1，normative）**
刷新令牌是「读 → 联网换新 → 写」，而微软的 refresh token **轮换** —— 两个前端同时刷，后者覆盖前者，
被覆盖的那份立刻失效 → **用户被登出**。规范把锁算法写死（两侧必须逐字一致，否则互不加锁）：

| 项 | 规定 |
|---|---|
| 锁 | `<stateDir>/auth.lock` **目录**（`mkdir` 在 POSIX/Windows 都原子） |
| 陈旧 | 目录 mtime > 30s → 视为持锁进程已崩，删除重试 |
| 超时 | 最多等 10s → `E_AUTH_LOCKED`（**绝不**在没锁时刷新） |
| 临界区 | 持锁 → **重读** → 需要才刷新 → 写 |

- 为什么不用 `flock`：`flock` 与 `fcntl` 锁在 Linux/macOS 是**不同命名空间**，跨语言会出现"看起来加了锁、
  其实互不可见"；Windows 没有 `flock`。`mkdir` 三平台语义一致。
- 实现：Python `OrzPythonMC#96`（`infra/filelock.py`，`Authenticator.ensure()` 持锁+重读，7 单测）、
  Swift `OrzMCKit#89`（`Game/Utils/FileLock.swift`，5 单测）。
- 已发版：**`orzmc-app 2.18.0`**、**`OrzMCKit 0.20.0`**（后者 `prerelease=true` —— 新分发口径首次实跑验证）。

**2. `runtime` 真身损坏回滚（`install-update.md` §10.1）**
安装时旧真身改名 `.bak` → 原子替换（失败还原）；运行前对自己副本做**魔数预检**，坏且 `.bak` 完好 → 回滚并 warn；
`exec` 报 `EACCES/ENOEXEC` 之类 → 回滚后**重试一次**，仍失败报 `E_RUNTIME` 并提示重装。
**顺手修一个真 bug**：`runtime install` 把 `channel=wrapper`（自己的副本）也当"可复用"→ 永远无法升级；
现在只对**别人装的**原生 Swift 安装 no-op。

**已知待补**：跨语言并发联测（两侧算法一致，但还没有"Python 持锁 + Swift 抢锁"的实测）；已记入 §4 C。

### 2026-10-20 — pi（方向调整落地：Python 唯一对外分发，Swift 同步迭代但不分发）

用户决定：**Python CLI 因体积 / 迭代速度 / 单二进制优势做对外分发主力**；**Swift CLI 保留、与 Python 同步迭代**
（命令面/行为继续对齐），但**不对外分发**（选方案 B：继续发 **pre-release**、不宣传）；**M3 归档**。

**⚠️ 先回退了一件已经在用户手里的行为**：`2.15–2.17` 让「`pip` 全新安装 → 默认下载 Swift 真身」
（Linux 65 MB）—— 等于正在对外分发 Swift。`2.17.2` 已回退：

| | 2.15–2.17.1 | 2.17.2 起 |
|---|---|---|
| 全新安装（无 `install.conf`） | 下载 Swift 真身（13–65 MB）后转发 | **Python 实现，零下载**（实测：不创建状态目录） |
| `channel=wrapper` / `source=OrzMCKit` | swift | 仍 swift（用户自己装过，尊重选择） |
| `ORZMC_RUNTIME=swift` | swift | 仍 swift（**实验开关**） |

**Swift 侧**：`release.yml` 的 `gh release create/edit` 加 `--prerelease`（`releases/latest`、官网、安装器默认路径都不会指向它）；
并把**历史 Release（22 个）一并转成 pre-release** → `repos/OrzMC/OrzMCKit/releases/latest` 现在返回 **404**（不再对外指向 Swift）；
README 顶部加「实验性 / 不对外分发」提示、Install 小节提示需显式版本。
**联动**：Python 的 `runtime` 实验通道改为**列 Release 取最新**（`releases/latest` 不再指向 pre-release），新增单测。

**文档**：`two-cli-strategy.md` 新增 **§6 分发口径**（含实测依据与"为什么这么分工"）；`install-update.md` §10.1 整节
降级为实验通道；`cli-comparison.md` 结论改为「Python 对外 / Swift 实验」；`AGENTS.md` 登记表与 §9 导航同步。

**没有动的**：`parity.json` 与并行规则（**Swift 仍同步迭代**，差异照旧会让 CI 红）、PyInstaller 6 平台资产（保留）。

### 2026-10-20 — pi（修掉 Linux 自包含硬伤：静态链 + jammy 构建 + 干净容器验收）

用户「修掉」→ 把 `docs/cli-comparison.md` §6.1 的两条硬伤修完并实发验证（**`OrzMCKit v0.19.0`**）。

**探针先行**（`linux-static-probe.yml`，matrix = x64/arm64 × 动态/静态，跑完即删）：
| 组合 | 结果 |
|---|---|
| 动态链 + jammy | ❌ 仍依赖 `libswiftCore.so` 等（只是 glibc 降到 2.35） |
| **静态链 + jammy** | ✅ **无 `libswift*` 依赖**，`GLIBC_2.35`，能直接运行 |

**路上三个坑**
1. jammy 上构建被 **SwiftLint 预编译二进制**挡住：它要求 `GLIBC_2.38`/`GLIBCXX_3.4.32`，插件失败会
   中止构建 → 给自有依赖 **OrzSwiftLint 0.0.10** 加 `ORZSWIFTLINT_SKIP=1` 逃生阀（仅发布构建用），
   OrzSwiftKit 升依赖（#17）。
2. 我把「自包含断言」插错 job（`Assert architecture` 在 macOS 与 linux 两处都有）→ macOS 上 `ldd` 失败；
   容器 job 默认 shell 是 `sh`（无 `pipefail`）→ 都补 `shell: bash`。
3. `verify-linux` 原用 `swift:6.0`（自带运行时）→ 等于没验依赖；改 **干净 `ubuntu:24.04` + binutils**。

**结果**：`v0.19.0` 六资产发布；`orzmc-linux-*` 62–65 MB（比动态的 35 MB 大，静态 Foundation/ICU 的代价），
无 `libswift*` 依赖、`GLIBC_2.35`、仍依赖系统 `libcurl4`；**`verify-linux` 在干净容器里全绿**
（自包含断言 + 共享验收 + `install → verify → uninstall`）。Release notes + CHANGELOG 写了「升级须知」。

**顺带修的一个真回归**：加 `runtime` 到 manifest 后 Swift CI 红（`surface.py` 不认台账的 `na`）→
检查器改为读 `parity.json`，标 `na` 的命令从「缺失」里剔除（反向约束仍在：标 na 却实现会被 `parity.py` 抓）。

### 2026-10-20 — pi（两套 CLI 实测对比 + 一个必须先修的硬伤）

用户要求「按 6 平台对齐平替」评估两侧，产出 **`docs/cli-comparison.md`** + 可复跑脚本
**`scripts/bench/cli.py`**（标准库、跨平台、离线）。核心数据：

| 维度 | Python（官方资产） | Swift（官方资产） |
|---|---|---|
| `--version` 中位 | **934 ms**（CPU 874） | **13 ms**（CPU 10） |
| `--json capabilities` | 938 ms | 28 ms |
| 峰值 RSS | 37 MB | 4 MB |
| 体积 | 15.5 MB 单文件 | 13.9 MB 单文件 |
| `--version`（pip 源码形态） | 628 ms | — |

- **Swift ≈ 25–70× 启动、≈9× 内存**；Python 慢的原因是 PyInstaller **onefile** 每次运行都解包到
  `$TMPDIR/_MEI*`（CPU≈墙钟，不是等待）。
- 迭代：Python 本地门禁 **10 s**（任意机器）/ 473 测试 vs Swift **25.7 s 且必须走 `ssh air`** / 98 测试；
  Python CI `quality` 43 s、`test` 24 s；Swift `test` 100 s、`linux` 131 s、`conformance` 109 s、`windows` 618 s。
- 发布：Python 整条 **2.7 min**、单腿 28–77 s；Swift **15.4 min**、Windows 腿 805–1037 s（工具链坑多）。

**⚠️ 抓到一个必须先修的硬伤：Swift 的 Linux 资产不自包含**
`orzmc-linux-x86_64` 动态依赖 `libswiftCore.so` / `libFoundation*.so` / `libdispatch.so` 等，
且 **glibc 下限 2.38**（构建机 ubuntu-24.04）；干净 Ubuntu 上直接
`libswiftCore.so: cannot open shared object file`。对比 Python 资产：只需 `libc/libdl/libpthread/libz`，
**glibc ≥ 2.14**、macOS 10.13+。Windows 侧 Swift 是 **33 文件 zip**（exe+32 DLL，35 MB），Python 是单 exe。
`verify-linux` 至今在 **`swift:6.0` 容器**里验（自带运行时）→ 等于没验到运行时依赖。

**结论（写进文档）**：运行效率 Swift 完胜；独立可运行性 / 发布与迭代成本 Python 完胜。
**并行期分工**：Swift 主体验（修好 Linux 自包含后），Python 作发行通道 + 兜底（`ORZMC_RUNTIME=python`）。
**下一步（已列进 §4）**：① Swift Linux 试 `--static-swift-stdlib` 并把构建机降到 ubuntu-22.04（glibc 2.35）；
② `verify-linux` 改干净 `ubuntu:24.04` 容器；③ 两条都绿后再评估 M3 阶段 2。

### 2026-10-20 — pi（M3 收口：默认切换 + 维护窗口 + PyInstaller 下线排期）

用户「按建议来」→ D-M3-1 / D-M3-2 / D-M3-4 拍板并落地，**`orzmc-app 2.17.0` 已发布**。

**D-M3-1 默认判定**（`install-update.md` §10.1，四步）
无 `install.conf` → **swift**（pip 新装）；`channel=wrapper` → swift；`source=OrzMCKit` → swift；
其余（含一键安装器）→ **python**（存量零打扰）。显式 `ORZMC_RUNTIME` 永远优先，`python` 是永久逃生阀。
> 第 4 条刻意把「安装器新装」也算存量：安装器装的是 PyInstaller 二进制，再默认下真身等于白下两遍。
> 解法排进 D-M3-4：安装器改为直接装 Swift 二进制 → 自动落规则 3 → 再下线 PyInstaller 通道。

**D-M3-2 维护窗口**：`2.17.0` 起 6 个月（至 2027-04-20）只修安全 / 数据损坏 / 无法启动（写在 README）。

**D-M3-4 排期**：观察期内把一键安装器改成装 Swift 二进制，之后下线 6 平台 PyInstaller 资产
（保留 macOS x86_64 + Linux x86_64 作离线包）；`review_by 2027-04-20`。

**三次连环踩坑（都是"默认判定"的连带影响，值得记住）**
| 现象 | 根因 | 修法 |
|---|---|---|
| CI `quality`/`ledger` 127（`libswiftCore.so` 缺失） | 干净 runner = 无 `install.conf` → 被当新装 → 下载真身并 exec | `ci.yml` 加**工作流级** `env: ORZMC_RUNTIME=python` |
| 发版 `binary` 六腿全红（"自报版本 0.18.0 ≠ v2.17.0"） | `release.yml` 的断言直接跑二进制 → 同上 | `release.yml` 也加工作流级 env（#90），重发 2.17.0 |
| Windows 单测四条红 | 用例注入 unix 形状 env，却按主机平台解析状态目录 | 用例显式 `is_windows=False`（#89） |

**教训（已进 AGENTS.md 开发注意节）**：**凡是"直接跑 `orzmc`"的 CI/脚本/开发命令都要显式钉住
`ORZMC_RUNTIME=python`**；要验运行时通道的用例自己 `env=` 覆盖（共享 harness 的沙箱与
`accept_selfupdate.py` 都已钉住）。

2.17.0 的 CHANGELOG + Release notes 补了「升级须知」（新装首跑要下载 / 老用户不变 / 逃生阀 / 维护窗口）。

### 2026-10-20（深夜）— pi（D-M3-3 / D-M3-5 落地，其余 3 条待拍板）

用户选了「先把不改用户行为的两条做掉」。

**D-M3-3 真身落点 = 混合方案**（`OrzPythonMC#86` + 规范 `install-update.md` §10.1 R1–R5）
- 事实基础：同一台机器可能同时有 `install.sh` 装的**原生** Swift 版与 shim 自管副本；
  旧行为会多存一份 13–35MB，并改写 `install.conf` 让原生版的 `update` 护栏拒写记录（记录漂移）。
- 现在：**R1 复用优先**（`source` 指向 OrzMCKit 且可执行 → 直接 exec，不下载不写记录）、
  **R2 绝不复用 Python 实现**（否则自己转自己）、R3 记录不覆盖、R4 失效回退、R5 `install` 复用时 no-op。
- `runtime status --json` 新增 `reused`；端到端实测：伪造原生安装 → shim 直接 exec 它（退出码原样），全程无下载。

**D-M3-5 库定位**：README 顶部 + 库的 `pyproject` description 写清「`orzmc-app` 是产品主路径，
`orzmc`（库）供 Python 程序调用、新功能优先落 Swift、不承诺 API 稳定扩张」。

**仍待拍板**：D-M3-1（默认是否切 swift；建议先 C 观察再 D 只对新装用户切）、
D-M3-2（旧引擎维护期限，建议 6 个月）、D-M3-4（PyInstaller 6 平台资产是否下线，等 D-M3-1）。
证据（代码量 / 资产体积 / 下载量 / 发布成本 / PyInstaller 验收现已全绿）已在回答与 §5.1 里。

### 2026-10-20（夜间）— pi（讲清 5 个待拍板点 + 修好 PyInstaller 验收链路）

用户要求「详细说明待拍板的点」，核对事实时顺带发现 **PyInstaller 资产的验收从 M2 起就没真跑过**：

| 层 | 问题 | 修法 |
|---|---|---|
| CI（python `binary` job） | 跑 `parent/scripts/accept/cli.py` 却**没检出父仓库** → 六腿常年报 404 | 补 `Checkout parent`（#83） |
| 同上 | 命令用 `\` 续行，Windows runner 默认 shell 是 **pwsh**（续行是反引号）→ `ParserError` | 改单行（#85） |
| 共享 harness | 补全落点断言直接比字符串 → Windows 的 `\` vs 规范模板的 `/` 假红 | 比较前归一成 `/`（`_logical()`） |

修完后 `gh workflow run ci.yml -f full=true`：**binary 六腿 + installer 六腿全绿** —— 这是
D-M3-4（是否下线 PyInstaller 通道）需要的基线证据：那条通道本身是好的，此前是**漏检**不是**坏**。

另外把 5 个待拍板项的事实（代码量 / 资产体积 / 下载量 / 发布成本 / 共存风险）整理成对照表，
写进回答里并在 `two-cli-strategy.md` §5.1 保留权威版本。

### 2026-10-20（傍晚）— pi（M3 阶段 1 落地：PyPI 作发行通道，opt-in）

**背景**：Mojang 第 2 次申请（launcher-only）**同样被拒** → 按既定规则**不再投第 3 次**，正版登录转
authlib-injector / Yggdrasil（记在 `docs/auth-application.md` 头部与 §4 待办 B）。空出的精力推进 M3。

**做了什么（规范先行 → 实现 → 验收）**

1. **规范**：`install-update.md` **§10.1 运行时分发（wrapper 通道）**——launcher/payload 两个角色
   （对 F1「PATH 上只有一个 orzmc」的裁定）、`ORZMC_RUNTIME` 开关、`SHA256SUMS` 强校验、转发语义、
   **版本号语义**（`--version` 报真身版本；launcher 版本只在 `runtime status` 的 `wrapper` 字段）、
   `install.conf` 的 `channel=wrapper`。
2. **实现**（`OrzPythonMC#80`，`orzmc/services/runtime.py`）：资产解析 → 下载 → SHA256 校验 →
   原子落盘 `<stateDir>/bin/`（Windows 的 DLL 先落目标目录）→ `execv` 转发；
   `orzmc runtime status|install` 管理命令；首次下载的进度/日志走 **stderr**（stdout 只留真身输出）。
3. **台账/命令面**：`cli-surface.json` + `parity.json` 新增 `runtime`（python `lead` / swift `na`）；
   共享 harness 加 `contract/runtime-status-shape`（只有实现该命令的一侧才跑）。
4. **端到端实测（真实资产）**：`ORZMC_RUNTIME=swift orzmc --version` → 首次下载 `orzmc-macos-x86_64`
   （13MB，SHA256 校验）→ 输出 **`orzmc 0.18.0`**（真身版本，不是 launcher 的 2.14.x）；
   `install.conf` 写入 `binary=<真身>` / `channel=wrapper` / `source=github:OrzMC/OrzMCKit`。

**当场抓出的三个 bug（都修了）**
| 现象 | 根因 | 修法 |
|---|---|---|
| Windows zip 装完只有 exe，DLL 不见了 | 解包到临时 staging，随后整目录被删 | DLL 先 `os.replace` 到目标目录，exe 最后原子替换 |
| 测试把文件写进宿主机真实 `~/AppData` | `default_state_dir(environ=...)` 仍 `expanduser("~")` 兜底 | **显式 environ 即权威**，不做宿主兜底 |
| `ORZMC_RUNTIME=swift orzmc --version` 报 launcher 版本 | 转发判断只认「第一个位置参数是子命令」 | `--version`/`--help`/裸 `orzmc` 也转发（规范要求报真身版本） |

**没做的事（刻意）**：不动默认运行行为、不下线 PyPI 的 6 平台 PyInstaller 资产、
不做 D-M3-2..5 的任何取舍 —— 那些是产品决策，已列在 §4 待拍板。

### 2026-10-20（午后）— pi（A/B/C/D 四件挂着的事全部收口）

**A. Windows arm64 资产 → 已发布**（台账唯一挂账，清空）
- arm64 那笔是 `build(windows): ...`，而 **release-please 不为 `build` 升版本** → 资产永远等不到发版。
  用官方支持的 **`Release-As: 0.18.0`** footer（空提交 + 说明）让机器人开 release PR，**不手改版本号、不手打 tag**。
- `v0.18.0` 已发布 **六类资产**：`orzmc-{macos,linux}-{arm64,x86_64}` + `orzmc-windows-{x86_64,arm64}.zip`；
  `verify-linux` 在真实资产上跑共享 harness（含本日新增用例）全绿。
- Release notes + `CHANGELOG.md` 补「升级须知」（arm64 首次提供：怎么装 / 已装 x64 怎么切 / x64 无影响），
  按 AGENTS §7 —— release-please 只渲染 commit 列表，不会替你说「该怎么办」。

**B. `orzmc app` 非 macOS 对齐**（方向确认：**改 Python**，不是 Swift）
- 规范先行：`install-update.md` §8 加 normative（一律 `E_UNSUPPORTED` + 固定文案、不假装成功、不降级 `E_RUNTIME`、不联网）。
- **Python 是偏离侧**：`AppInstaller` 抛 `RuntimeError` → CLI 映射成 `E_RUNTIME`。改为在碰网络/文件**之前**
  用 `AppInstaller.available` 前置判定（#77）+ 单测（monkeypatch `sys.platform`，macOS 本机也能跑）。
- Swift 只改文案（#81）。
- 共享 harness 新增 `contract/app-unsupported-outside-macos`：四个子命令在 Linux/Windows CI 上断言
  码 + **文案逐字相等**。已实测：python `quality`（源码模式）**PASS**、`v0.18.0` 的 Linux 资产上 **PASS**。

**C. `state.paths` 动态一致性（`frontends.md` §7 待补第 1 条）→ 一致性 76 → 79**
- 参考适配器新增 `statePaths`，**直接读 `docs/spec/state-paths.json`** 做 `${VAR:-默认}` / `$HOME` / `%VAR%`
  替换 —— 比对对象是规范文件本身，不是另抄一份常量。
- 三个 fixture：`state-paths/{unix-xdg,unix-defaults,windows}`；分隔符归一 `/`，Windows 形态在 macOS/Linux
  上也能断言；Windows 块没有 `completion` → 用 `absent` 断言。
- **实现侧的关键不是加适配器，而是把路径收敛成单一来源**：
  Swift `Game.StatePaths` 补 `installRecord`/`authSession`/`completionPath(shell:home:)`，
  并把 `InstallManifest.defaultPath`、`AuthStore.path`、`CompletionCommand` 三处手写落点改成从它派生（#83）；
  Python 给 `default_state_dir()` 加 `environ=`/`is_windows=` 接缝，适配器复用 `orzmc_app.cli.completions.target_path`（#78）。
- 验证：参考/Python/Swift 适配器 **79/79**；Swift 单测 98 例绿（`ssh air`）。

**D. M3 评估成文**（`docs/two-cli-strategy.md` §5.1）
前置条件核对（六类资产 ✅、干净环境 ✅、离线降级未做）、建议方案（~300 行 shim：找真身 → 校验 → `exec`，
命令语义零落在 Python 侧）、**三处规范硬冲突**（F1 同一路径唯一可执行体 / F3 `update` 只替换自己 /
版本号语义）与建议裁定、风险缓解表、**5 个待拍板项 D-M3-1..5**。

**顺手记的坑**
- `release.yml` 用 `ref: inputs.tag || github.ref` checkout → **dry-run 带旧 tag 会 checkout 旧代码**（已写进 §4 坑 5）。
- python 的 ruff 禁全角标点（RUF002/RUF003），中文注释要写半角。
- 本机到 `github.com` 的 DNS 一度不可达（`api.github.com` 正常）；后恢复，直连即可。

### 2026-10-20 — pi（合并两个 release PR + Windows arm64 打通 + 一个 CI 回归）

**A. 两个 release PR 合并**（`OrzMCKit#77` → 0.17.0、`OrzPythonMC#75` → 2.13.0），但先撞上一个**回归**：

`OrzPythonMC#73`（2026-10-19 的 CI 成本优化）加了 `pull_request.branches-ignore: release-please--**`，
而 `main` 的分支保护要求 `pr-title` / `quality` / `test (ubuntu-latest, x86_64)` →
**工作流不跑 = 必需检查永不上报 = release PR 永久 BLOCKED**（`statusCheckRollup` 为空，只能 admin 绕过）。
`OrzMCKit` 的 `main` 没开保护所以只是红了个空 run。

- 修法（python `#76`）：删掉 `branches-ignore`，release PR 与普通 PR 走同一套。
  省成本的边界本来就在「`binary`/`installer` 是 push-only」+「`test` 矩阵并行」，不是跳过整个工作流。
  合入后 `#75` 我这边补触发一次（close/reopen）→ 三条必需检查全绿 → 正常合并（**不需要 admin**）。
- 不变式写进 `python/AGENTS.md`「迭代流程」，避免下次又用「跳过工作流」省成本。

**B. Windows arm64 打通**（台账唯一挂账 / M3 前置）。三次探针（`gh workflow run ci.yml --ref <branch>`），
每轮只暴露一个新事实：

| 轮 | 失败点 | 修法 |
|---|---|---|
| 1 | `lld-link: msvcrt.lib(...): machine type x64 conflicts with arm64` | runner 默认 `vcvarsall x64`；且 `compnerd/gha-setup-swift` 默认装 **amd64** 包 → `build_arch: arm64` |
| 2 | `ilammy/msvc-dev-cmd` 失败：`The input line is too long.` | 该 runner PATH 极长，`vcvarsall` 内部展开 PATH 撞 cmd **8191** 上限 → 不调 vcvarsall |
| 3 | `STL1000: Unexpected compiler version, expected Clang 20 or newer` | arm 镜像同时装 VS17+VS18；VS18 的 STL 要 Clang 20+（Swift 6.2 = Clang 19）→ 选**最老且带 `lib\arm64`** 的工具集 |

最终形态：本地 composite action `.github/actions/msvc-arm64`（枚举 VS → 收集带 `lib\arm64` 的工具集 →
最老优先 → 导出 `INCLUDE`/`LIB`/`VCToolsInstallDir`/`WindowsSdkDir`/…），`ci.yml` 的 `windows-arm64`
（手 dispatch、零常态成本）**build+冒烟+单测全绿**；`release.yml` 的 `build-windows` 变 x64+arm64 双臂矩阵，
dry-run 里 `build-windows (windows-11-arm, arm64)` **全绿**（zip 打包 + 干净 PATH 断言 + 版本断言）。
下游零改动：`install.ps1` 早已把 `PROCESSOR_ARCHITECTURE=ARM64` 映射成 `arm64`，自升级按 `arch(arm64)` 判定。

⚠️ 记一笔坑：`release.yml` 用 `ref: ${{ inputs.tag || github.ref }}` checkout，**dry-run 时若指定已存在的
旧 tag，会 checkout 到旧代码**——第一次 dry-run 用 `-f tag=v0.17.0` 就因此报
`Can't find 'action.yml' … .github/actions/msvc-arm64`。新东西没发版前，dry-run **不要带 tag**。

**C. 收尾小项**
- ✅ `install.ps1` 进 README（`OrzMCKit#79`）：README 从「macOS 原生实现」改成跨平台 + Windows 一键装 +
  手动资产表（含 arm64 zip 与「为什么是 zip」）；顺带修 `Development` 里早已失效的 `scripts/accept_cli.py`
  引用（M2 后只有父仓库一份）与 `install.ps1` 文件头把资产名写成 `.exe` 的错。
- ✅ `install.ps1` 进站点文档（`OrzMCSite#7`）：`content/client.md` 的「备选安装方式」补 Swift 原生实现。
  没动主推通道——两个通道是否并列展示/何时收敛是 M3 的产品决策。
- ✅ dependabot `OrzPythonMC#30`/`#31` 已合。
- ⏭ `orzmc app` 非 macOS 对齐尚未做，且**方向变了**：规范（`frontends.md` §7.2）要 `E_UNSUPPORTED`，
  Swift 已符合，**Python 实际返回 `E_RUNTIME`**（`AppInstaller` 抛 `RuntimeError`）——是 Python 侧要改，
  下次会话一并做（规格先行 + 两侧 + 验收）。

**E. 顺手修掉一个指针缺陷**：`git ls-tree HEAD -- plugin` 竟是 `bd908b8`（**develop**）——
`abed948`（2026-10-19「父仓库 CI 检出两个 harness 子模块」）把 plugin 指针一起改掉了，
正是 `AGENTS.md` §5 反复警告的坑（本地 `plugin` 常检出 `develop`）。`f143fb1` 修过一次，这次是复发。
已归位 `5eadd6e`（main），并刷新 `RELEASES.md` 基准组合（`python 95d50c0` / `OrzMCKit bad15bd` / `site 31d215f`）。
👉 下次动 `ci.yml` 之类「看似只改父仓库自有文件」的提交时，**务必 `git add <明确路径>`**。

**D. 父仓库层面**：`docs/windows-port.md` 新增 §3.5（arm64 三个坑与做法）、§4 前提表拆 x64/arm64；
`docs/spec/frontends.md` 更新平台矩阵与证据链（并修掉 M2 已删除的 `scripts/accept_cli.py` 引用）；
`docs/spec/parity.json` 的 `knownDrift` 改成「资产未发布」的准确说法（构建链路已验）。

### 2026-10-19 — pi（会话收尾：v0.16.0 发布 + M2 落地 + 交接）

本轮后半段完成三件事（细节见上面两条日志）：

1. **v0.16.0 发布**：dry-run（**未打 tag 也能跑**）→ 抓出 `build-windows` 断言拿到 `main` 的缺陷 → 修 →
   正式发布 6 个资产；Windows 真机（无 Swift）复验 `install.ps1` → `orzmc 0.16.0` ✓。
2. **M2 落地**：`scripts/accept/cli.py`（父仓库）成为唯一验收脚本（1566 → 875 行），
   两侧 CI 稀疏检出调用；**共享判据当场抓出 Swift 3 个真 bug**（内存/并发数前置校验、补全 rc 标记）并修复。
3. **交接整理**：§0.1 接力提示词、§1 焦点、§2 指针、§4「下一会话起点」全部刷新到当前事实
   （父仓库 `main` @ `971619e`，python `e7b8d27`，OrzMCKit `acd99d4`，工作区干净）。

**待合 PR**：`OrzMCKit#77`（0.17.0）、`OrzPythonMC#75`（2.13.0）。
**下一步第一件事**：合并这两个 release PR（或先 dry-run），然后 Windows arm64 资产。

### 2026-10-19 — pi（M2 落地：验收判据收敛成一份，并抓出 Swift 3 个真 bug）

**M2（`docs/two-cli-strategy.md`）完成**：两个 `accept_cli.py`（842 + 724 行）→ 父仓库
`scripts/accept/cli.py` 一份；两侧 CI 稀疏检出父仓库调用（python 的 `quality`/`binary`、OrzMCKit 的
`cli-acceptance`/`linux`/`verify-linux`），本地副本删除。`--frozen` 表达冻结二进制专属用例。

**上来就抓到 Swift 侧 3 个真 bug（已修，`OrzMCKit#76`）**：

| 现象 | 根因 | 修法 |
|---|---|---|
| `--json client -m nope -v 1.20.4` **90 秒超时** | 非法内存值一路带到下载阶段（先联网） | `Game.MemorySpec` 前置校验 → `E_USAGE`（文案与 Python 一致） |
| `--json client -v 1.20.4 -j 0` **挂住** | 并发数未校验 | `Game.LaunchOptionRules`（1–64）→ `E_USAGE` |
| 补全 rc 行缺 `# added by orzmc` | 与 Python 不一致（幂等识别靠标记） | 补齐标记 |

**验证**：`ssh air` + 共享脚本对 Swift **22/22**；python `quality` 源码模式 **22/22**；
`parity.py` 变为「共享脚本就位 + 两侧 CI 必须引用 + 不许引用旧副本」。

### 2026-10-19 — pi（发布 dry-run 实测通过）

对 `v0.15.0` 实跑 `gh workflow run release.yml -f tag=v0.15.0 -f dry-run=true`：

| 项 | 结果 |
|---|---|
| `verify` + 构建（macOS×2 / Linux×2 / **Windows zip**） | 全 success（Windows 侧 `zip: 33.38 MB` + 干净 PATH 断言） |
| `publish` / `verify-linux` | **skipped**（按设计） |
| 总耗时 | **10 分钟**（对比：真实重发 16–18 分钟，且会动线上资产） |
| 副作用 | Release 资产快照前后 `diff` **完全一致** |

→ 定成标准动作（写进 `AGENTS.md` §8.1.1 与 `iteration-efficiency.md` §3.6）：
**发版前必跑 dry-run，绿了再正式 dispatch。**

### 2026-10-19 — pi（迭代成本取证 + 三项 CI 优化）

**取证（GitHub API，不是估算）**：OrzMCKit 一天 **CI 58 次 / 257 分钟**、**Windows Probe 20 次 / 117 分钟**、
**Release 7 次 / 76 分钟**（同一 tag 重发 3 次），父仓库 15 次（各 10 秒）。
单次 job：`windows` **13:15**、`linux` 2:11、`test` 2:02、`conformance` 1:23、`cli-acceptance` 1:16、`portability` 4 秒。

**浪费的六个模式**：W1 每推一个小修跑满 6 个 job（`feat/windows-probe` 推了 14 次）· W2 探针一次只测一个组合 ·
W3 发布后才暴露打包问题导致重发 · W4 release-please 分支跑满 CI（11 次）· W5 纯文档/指针 bump 也跑 13 分钟的 Windows ·
W6 同一改动验证 3 遍。

**已落地**（两个子模块各一个 PR）：
- 跳过 release-please 分支与纯文档 push；
- **Windows job 只在源码/依赖/工作流变更时跑**（`git diff HEAD~1 HEAD -- Sources …`）→ 每次省 13 分钟；
- **`release.yml` 支持 `dry-run`**（发布前排雷，替代"重发 3 次"）。

**纪律**（写进 `AGENTS.md` §8.1.1 与 `docs/iteration-efficiency.md` §3.7）：推前先 `air` 验证（25 秒 vs 3.3 分钟）、
攒改动一次推、探针用 matrix、发布先 dry-run、**指针可批量 bump**（同一次产品级变更）。

### 2026-10-18 — pi（两套 CLI 并行策略 + 能力台账）

**用户决策**：Python CLI 与 Swift CLI **先并行**，找更合理的关系、降低重复开发。

**结论（写进 [`docs/two-cli-strategy.md`](docs/two-cli-strategy.md)）**：
- 采用 **B：并行 + 单一主导 + 台账**（现在），**M3：Python 作发行通道、功能委托 Swift**（中期目标）；
- 规则 R1–R5：规范先行 / **一个功能只在一侧写** / 平台差异归平台侧 / 共用件只有一份 / 落后要交差；
- `lead` 分工：引擎语义与 CLI 契约以 **Swift** 为准；`plugin` 与 PyPI 分发以 **Python** 为准；`app` 是 Python 的 `na`。

**已落地机制**：
- `docs/spec/parity.json`（13 命令台账）+ `scripts/verify/parity.py`（已接 `check.py` → 父仓库 CI）：
  覆盖率、状态自洽、`behind` 到期、**两个验收 harness 用例集合对齐**、可选 capabilities 反向校验。
- **本轮就抓到真漂移**：Python harness 有 4 个 Swift 没有的用例（typer 自动选项 / 冻结二进制 / 动态补全 /
  补全落点 vs `state-paths.json`）→ 前三条登记为实现独有，最后一条给 M2（共享 harness）定了 `review_by: 2026-12-31`。

**三处门禁已就位**（都真跑，不是摆设）：
- 父仓库 `check.py` → `parity.py` 静态校验 + 两个 harness 用例对齐（CI 里浅检出两个子模块）；
- `OrzMCKit` CI `ledger` job → `parity.py --swift-caps`；
- `python` CI `ledger` job → `parity.py --python-caps`。

**当场抓到两处真漂移**：① Python 独有 4 个验收用例（已登记，其中 1 条定了 M2 的 review_by）；
② 台账把 `app` 写成 `python: na`，而 Python 其实也有 `app` → Python 侧 ledger job 报错，已修正为 `parity`。

**M2 待做**：把两个 `accept_cli.py`（842 + 724 行）合并成父仓库 `scripts/accept/cli.py`，两侧 CI 通过 checkout 父仓库调用。

### 2026-10-18 — pi（Windows W3–W6 完成并发布：v0.15.0 真机验证通过）

- **W6**：`ci.yml` 新增 `windows` job（`windows-2022` + Swift 6.2 + `update-sdk-modules` + 开发者模式），
  硬门禁 = build + 冒烟 + **98 单测**；`release.yml` 新增 `build-windows`。
- **W4**：`PlatformTools` 升级为「命令+参数」：`zip/unzip` ↔ `tar.exe -a -c -f` / `-x -f` / `-x -O`。
- **W3**：自升级按平台——资产名/平台标签（顺带修了 Linux 会下 macOS 二进制的 bug）、魔数 Mach-O/ELF/PE、
  Windows「改名旧 exe → 放新 exe」+ 失败回滚。
- **W5**：`scripts/install.ps1`（zip 资产 / SHA256 / PE 魔数 / 用户 PATH / `install.conf` / F6 提示 / `-uninstall`）。
- **关键发现**：`--static-swift-stdlib` 在 Windows 上**不生效**（`dumpbin` 仍列 `swiftCore.dll` 等），
  真机直接 `0xC0000135`。→ 资产改为 **zip（exe + 32 个运行时 DLL，33 MB）**，安装器解压，自升级从 zip 取 exe。
- **真机验收（`ssh win`，PS 5.1，未装 Swift）**：install → `orzmc --version` = 0.15.0 →
  `--json capabilities` ok/13 命令 → `completion bash` = `function _orzmc()` → `install.conf` 正确。
- 发布：**v0.15.0** 资产 `orzmc-{macos,linux}-*` + **`orzmc-windows-x86_64.zip`**；`verify-linux` 每版自动验收。

### 2026-10-18 — pi（Windows W1/W2 完成并合并）

- **W1 补全函数名**：`orzmc completion bash` 在 Windows 曾输出 `function _D:\a\...\orzmc.exe()`（用 `argv[0]` 全路径）。
  现在 `programName(from:)` 归一为 `orzmc`（切 `/`、`\`，去 `.exe`）→ Windows 实测 `function _orzmc()` ✓。
- **W2 状态目录**：规范 `state-paths.json` 早已写 Windows 形状，Swift 实现没跟上。新增 `Game.StatePaths`
  （平台判定**可注入** → macOS 上也能单测 Windows 形态），`InstallManifest` / `AuthStore` / `GamePlan.defaultRoot` 全部改走它。
- 验证：`air` 上 `swift test` **94 passed**（新增 4 例）；Windows 探针（windows-2022 + Swift 6.2）构建 + 冒烟全绿；
  PR `OrzMCKit#63` 已合并（含 `Terminal` 走 `ucrt`、crypto 条件加 `.windows`、探针改手动触发）。
- 剩余：**W3** 自升级替换、**W4** 备份走 `tar.exe`、**W5** `install.ps1`、**W6** CI job + `.exe` 资产。

### 2026-10-18 — pi（Windows 探针：编译 + 基础运行已通过）

**8 轮探针**（`windows-probe.yml`，每轮 3–10 分钟）把"Windows 到底行不行"问清楚了：

| 轮 | 失败点 | 处理 |
|---|---|---|
| 1 | `Invalid manifest … module 'ucrt'` | `update-sdk-modules: true` |
| 2 | `Tool 'swiftlint' is not supported` | OrzSwiftLint **0.0.9**：Windows 跳过 lint 插件 |
| 3 | `missing inputs: …GeneratedSources/*` | 开发者模式（符号链接）；SwiftPM 6.0 缺陷 → **换 Swift 6.2** |
| 4 | `STL1000: expected Clang 20+` | 用 `windows-2022`（VS 2022），不用 windows-2025 |
| 5 | `no such module 'Crypto'` | swift-crypto 条件加 `.windows`（OrzSwiftKit#14 / MojangAPI#10） |
| 6 | `cannot find 'SIGKILL'/'kill'` | OrzSwiftKit#15：`terminate()` + Shell 的 Windows 实现（tasklist/taskkill/powershell） |
| 7 | `run` 重载歧义 | OrzSwiftKit#16：显式类型标注 |
| 8 | — | **`orzmc.exe` 构建成功**，`--version` / `--json capabilities` / `--json list` / `completion bash` 均能跑 |

**结论：A 路线（全量 Windows）可行**，剩余是 6 项平台细节（W1 补全脚本函数名、W2 状态目录
`%LOCALAPPDATA%`、W3 自升级替换、W4 `tar.exe` 备份、W5 `install.ps1`、W6 CI/发布资产）。
详见 [`docs/windows-port.md`](docs/windows-port.md)。

**前提（已写进文档）**：`windows-2022` + **Swift 6.2** + `update-sdk-modules: true` + 开发者模式。

### 2026-10-18 — pi（构建搬到 `ssh air`：增量 24 秒）

**本机不再构建**（SDK 13.3 / 磁盘 9.8GB / no-op 构建 16.7s，见上一条）。改为远端构建：

- 新增 **[`scripts/air/run.sh`](scripts/air/run.sh)**：`env|sync|build|test|accept|all|sh|clean`；
  `rsync --delete`（排除 `.build`）→ `~/orzmc-build/OrzMCKit` → 远端 `swift build`。
- `air`：`joker@192.168.0.26`，**Apple Silicon M1 / 8 核 / Swift 6.4 / SDK 27 / 24GB 可用**。
- 关键优化：依赖 `branch: main` 每次解析都联网 → 默认 `--only-use-versions-from-resolved-file`
  （**1m07s → 24s**）；要更新依赖用 `ORZMC_UPDATE_DEPS=1`。
- 依赖迭代：`ORZMC_LOCAL_DEPS=1` 会把 `swift/lib/{MojangAPI,PaperMC,OrzSwiftKit}` 同步过去并把
  **远端副本**的 `Package.swift` 改成 path 依赖（37s 完成构建，不必先 push）。
- **实测**：build 24s（编译本体 1.5–15s）/ test 25s（90+1 例全过）/ accept 1m33s（20/20 通过）。

已写进 [`AGENTS.md`](AGENTS.md) §8.2（含"air 休眠 → ssh 报 `This system is locked`"的排查提示）
与 [`docs/iteration-efficiency.md`](docs/iteration-efficiency.md) §3.2（四条路径耗时对比）。

### 2026-10-18 — pi（本机 Swift 6 工具链 + 秒级反馈车道）

**装好了**：`swiftly` 安装 `swift-6.0.3-RELEASE.xctoolchain`（免 sudo，`~/Library/Developer/Toolchains`），
`swift --version` 正常。**但本机仍无法全量构建**，三个客观限制（已写进 `docs/iteration-efficiency.md` §3.1）：

1. macOS SDK **13.3** < 14 → 依赖 `OpenAPIKit 3.9.0` 用 macOS 14 才有的 `URL(string:encodingInvalidCharacters:)`；
2. 只有 CommandLineTools（无 Xcode）→ SwiftLint 构建插件找不到 `sourcekitdInProc`；
3. 磁盘仅剩 ~9.8 GB → 装 Xcode 16（~20 GB）不可行。
   本机性能：空项目 no-op 构建 **16.7s**（user 1.7s）、本包冷构建 **35 分钟**。

**于是把「反馈回路」分层缩短**（本地 + CI 两条快车道）：

| 层级 | 手段 | 实测 |
|---|---|---|
| 平台写法错误 | `OrzMCKit/scripts/dev/local-build.sh lint` / CI 新 job `portability` | **1s** / **5s** |
| 语法错误 | `local-build.sh check`（`swiftc -parse` 80 文件） | **50s** |
| 完整门禁 | CI `linux`（缓存） / macOS 三件套 | 2m02s / 1m07s–1m56s |

`scripts/dev/local-build.sh` 会打印工具链/SDK/开发者目录诊断与具体修复建议（不静默失败），
子命令 `check|lint|parse|build|test|linux`。CI 里 `portability` 已拆成独立快 job（宿主机跑，不建容器）。

### 2026-10-18 — pi（D14：Linux 侧完工 + 迭代效率专项）

**发版**：`OrzMCKit v0.14.0` 已发布，资产 `orzmc-{macos,linux}-{arm64,x86_64}` + `SHA256SUMS`（首次含 Linux）。
`release.yml` 新增的 `verify-linux` **在真实发布资产上全绿**：`sha256sum -c` → `accept_cli.py` **20/20** →
`install.sh` 安装 → 版本/补全/`install.conf` 断言 → `uninstall --yes` 清理。

**途中修的两个发布链路问题**（都是容器特有，CI 里发现不了）：
1. `swift:6.0` 精简镜像没有 `file` → `Assert architecture` 直接 127；改用 `uname -m` + 执行产物双重断言。
2. 容器默认 shell 是 `sh`（不支持 `set -o pipefail`）、且不带 `python3` → 显式 `shell: bash` + 先装工具。

**Linux 收尾（OrzMCKit#59 / #61）**：`scripts/install.sh` 支持 Linux（平台判定 / `orzmc-<os>-<arch>` /
`sha256sum` 回退 / ELF 魔数 / `platform=linux-*` / `zip` 缺失提示）；`verify-release` 挂进 release 流水线。

**迭代效率**（用户要求专项分析，落进 [`docs/iteration-efficiency.md`](docs/iteration-efficiency.md)）：
本轮 9 轮 CI / 约 2.5 小时，其中 5 轮只换来一句编译错误。已落地：
- `scripts/verify/portability.py`（秒级静态扫描 `CryptoKit` / `FoundationNetworking` / `/usr/bin/*`）→ 接进 CI 首步；
- Linux job 加 SwiftPM 缓存 → **8m52s → 2m07s**；
- `scripts/dev/linux-build.sh`（docker/podman 本地跑 build/test/accept）；
- 发布后自动验收（资产坏了流水线就红）。
建议下一步：本机装 Swift 6（`swiftly install 6.0`）把编译循环从 7 分钟降到 1–2 分钟。

### 2026-10-18 — pi（D14：Swift CLI 跨平台收敛，Linux 编译已打通）

**用户决策**：一套规范两份实现的迭代成本太高；Swift 长期会跨平台，因此 **Swift CLI 按跨平台迭代**，
验证通过后**停掉 Python CLI 迭代**（已落进 `docs/product-unification-plan.md` **D14 + D14.1 退场判据**）。

**做法（验证驱动，不猜）**：本地 Swift 5.8.1 无法编译（包要 6.0），故用 CI 探针 `swift:6.0` 容器真跑
`swift build`，一轮一轮消缺口：

| 轮 | 报错 | 根因 | 修法（仓库） |
|---|---|---|---|
| 1 | `URLSession has no member 'shared'` | `PaperMC/Common/SimpleDownloader` 缺 `FoundationNetworking` | 补条件导入；corelibs 无 async bytes → `data(from:)` 后本地分块（PaperMC#5） |
| 2 | 同样报错（依赖被 `Package.resolved` 钉住） | 需刷新 pin | 刷新 `Package.resolved` |
| 3 | `CryptoKit` 缺失 / 多处 `URLSession` | MojangAPI 无条件 `import CryptoKit`；多库缺 `FoundationNetworking` | `swift-crypto` 兜底（MojangAPI#8）、8 文件补导入（OrzSwiftKit#12）、OracleJDK（OrzSwiftKit#13）、MojangAPI#9、PaperMC#6 |
| 4 | `Shell` 缺失 / 适配器 `CryptoKit` | `JokerKits.Shell` 被 `#if os(macOS)` 关掉 | Shell 放开到非 Windows（OrzSwiftKit#12）；`ConformanceAdapter` 用 `Crypto` 兜底 |
| 5 | — | — | **`Build complete!` Linux 编译通过** ✅ |

**OrzMCKit 侧**（分支 `feat/linux-build` / PR #57）：新增 `Game.PlatformTools`（`unzip` 路径解析，缺失则降级或报错）、
两处 `/usr/bin/unzip` 收拢、`AppInstaller` 整块 `#if os(macOS)`、`AppCommand` 在非 macOS 返回 **`E_UNSUPPORTED`**、
多处 `FoundationNetworking`。

**规范**：`product-unification-plan.md` 新增 **D14 / D14.1 / Phase 6（6.1–6.6）**；`frontends.md` 新增 **§7.2 平台支持矩阵**。

### 2026-10-18 — pi（CLI 契约 0.2：冻结二进制补全崩溃 + CLI 自动化验收；已发 Python 2.12.0 / Swift 0.13.0）

**触发**：用户实测发布版 `orzmc --install-completion` / `--show-completion` 崩在
`RuntimeError: Shell detection not implemented for 'posix'`。

**根因**：typer 的补全安装走 `shellingham`，而它用 `importlib.import_module(f".{os.name}")`
**动态**导入平台实现；PyInstaller 静态分析看不到、contrib 也没有 hook → 冻结二进制缺
`shellingham.posix` / `nt`。受影响的**不只是两个多余选项**：规范 §9 的
`orzmc completion install` 在发布版里一直是坏的（单测用 CliRunner 进程内调用，全绿）。

**先改规范（父仓库 `docs/spec/`，`specVersion 0.2`）**
- `cli-surface.md`：新增 **§4.5 `completion` 全契约**（shell 只读环境变量、禁进程探测、
  落点/幂等/rc 边界、`powershell`/`pwsh` 的 `install` → `E_UNSUPPORTED`、`data = {mode,shell,path,hint}`、
  禁框架自带补全开关）；§6 明确**用法错误也退 1**（框架的 2 必须归一）、**错误/日志一律 stderr**；
  §7 把“非 TTY 用默认”拆成**破坏性操作 → `E_CANCELLED`/130** 与“有默认意图（`update`/EULA）”两类；
  §9 重写为总览 + 现状；§10.1 列出 **Swift 待对齐清单**。
- `behavior.md`：**B9 定稿**「非 TTY 破坏性操作缺 `--yes` → 取消且数据不动」；**B11** 补退出码/流/信封规则。
- `frontends.md`：**F6 重写**（落点、判定、幂等、rc 边界、禁改执行策略/禁进程探测、`completion_file` 登记）；
  F2 补现状（`completion_file` 两侧均已落地）。
- `install-update.md`：§5 重写（含“安装器自动装补全 + `--no-completion` **尚未实现**”的坦白状态）；
  §9 明确非交互卸载必须 `--yes`。
- `conformance.md`：新增 **§12 CLI 行为验收（acceptance）**——分组 `surface/envelope/contract/completion/mcp/frozen/network`，
  要求**每套实现提供等价 harness**（Swift 待建）。

**Python 实现（分支 `fix/cli-completion-acceptance`，**尚未合入 main / 未 bump**）**
- `scripts/build.py` 加 `--collect-submodules shellingham`（冻结二进制补全崩溃的直接修复）。
- `completion install` 换成自带安装器 `orzmc_app/cli/completions.py`：环境变量判定、固定落点幂等、
  不改 PowerShell 执行策略、bash/zsh 只补一行带标记的 rc、powershell/pwsh → `E_UNSUPPORTED`；
  落盘后经 `record_completion_file()` 登记到 `install.conf`（库新增 `completion_file` 字段 +
  `uninstall` 清理 → 与 Swift 对齐）。
- 摘掉 typer 的 `--install-completion`/`--show-completion`（保留 `add_completion=True` 供
  `_ORZMC_COMPLETE` 动态补全）；`uninstall --json` 日志切 stderr；`remove`/`uninstall` 非交互缺 `--yes`
  → `E_CANCELLED`；错误写 stderr；用法错误 2 → 1；`-h` 与 `--help` 等价；`E_UNSUPPORTED_TYPE`；
  `RichReporter` 给注入的 Console `push_theme`（否则 `--json` 下第一次日志就 `MissingStyle` → `E_RUNTIME`）。
- **新增 `scripts/accept_cli.py`**（CLI 自动化验收，真实进程 + 沙箱 + 超时；`--cli` 跑冻结二进制、
  `--state-paths` 比对父仓库快照）。CI：`quality` 源码模式（带 `--state-paths`），`binary` 6 平台 `--cli`。
- 本地结果：pytest / ruff / mypy 全绿；`surface --strict` 0 漂移；acceptance 源码 20/20、
  **冻结二进制 23/23**；`check.py` 全绿；`accept_selfupdate`（跳过网络）24/24。

**第二轮（同一天，按用户要求把文档 / Pages / Swift 一起对齐）**
- **Python 文档与 Pages**:`README.md`（补全用法/落点/幂等/登记、`-h`、验收命令、「2.12 起的行为变化」）、
  `docs/index.html`（卸载需 `--yes`、卸载连补全一起清、quickstart 补 `completion install`、features 加「Shell 补全」）。
- **新发现的两处实现差异，已对齐**:`--json` + 无子命令 → 两端统一 `E_USAGE`/1（Python 之前把帮助打到 stdout）；
  `remove` 目标不存在 → 两端统一 `E_NOT_FOUND`（Python 新增 `VersionNotFoundError`，之前是 `E_RUNTIME`）。
- **Swift 对齐（`OrzMCKit` 分支 `feat/cli-contract-0-2`）**:非交互 `remove`/`uninstall`/`app uninstall` 缺 `--yes`
  → `E_CANCELLED`（经 ConsoleKit `confirmOverride`）；`completion install` 补 `data.hint`、未知 shell → `E_USAGE`、
  powershell/pwsh 明确 `E_UNSUPPORTED`、落盘后登记 `completion_file`、`pwsh` 回显请求值；
  安装器加 `ORZMC_NO_COMPLETION=1`；**新增 `scripts/accept_cli.py`**（与 Python 侧同分组同语义，
  落地时用 Python 二进制做过对照 20/20）+ CI `cli-acceptance` job。
  `-h` 与用法错误退出码 1 经核对 **本来就符合**（ConsoleKit `GlobalSignature` 含 `-h`；`main()` 统一 exit 1）。
- **规范回写**:`cli-surface.md` §1（`--json` 无子命令例外）+ §10.1 全部打勾；`conformance.md` §12.3
  两个 harness 均接入；`install-update.md` §5 状态（Swift 安装器自动装补全 + 关闭开关 ✅，Python 仍 backlog）；
  `frontends.md` F6 / `behavior.md` B9 现状改为两端 ✅。
- **第三轮（收尾）**:Python 安装器也补齐「装完自动装补全 + `--no-completion`/`ORZMC_NO_COMPLETION`
  + 记录 `completion_file` + 卸载清理」（Unix），Windows 按 F6 不落盘；`accept_selfupdate.py`
  新增 3b) 步骤覆盖这条链路（HOME 也关进沙箱）。Windows 真机 PS 5.1 上验证过 install.ps1 的解析/安装记录。

**PR 与 CI（2026-10-18）**
- Python **#71** <https://github.com/OrzMC/OrzPythonMC/pull/71>；Swift **#56** <https://github.com/OrzMC/OrzMCKit/pull/56>。
- 两端都已全绿：Python `quality` + 6×`test`，另用 `gh workflow run ci.yml -f full=true`
  跑了 **6×`binary`（冻结二进制 CLI 验收）+ 6×`installer`**；Swift `test` / `conformance` / **`cli-acceptance`**。
- **CI 抓到的 4 个真问题**（都已修，说明验收确实在起作用）：
  1. `completion install` 用 `PSModulePath` 猜平台 → ubuntu runner 有 pwsh 环境变量，被误判成
     Windows 报 `E_UNSUPPORTED`；改为按 `os.name` 判定（规范已补「不得用 PSModulePath 猜平台」）。
  2. 验收 harness 自己在 Windows 控制台（cp1252）第一行中文就 `UnicodeEncodeError` → 强制 UTF-8。
  3. Swift `remove` 把「缺 `--yes`」判在「目标是否存在」之前 → 不存在时报 `E_CANCELLED` 而非
     `E_NOT_FOUND`；改为先判存在性（与 Python 一致）。
  4. Windows 上 `frozen/completion-install-does-not-crash` 断言退出 0，但按 F6 应 `E_UNSUPPORTED` —— 用例改按平台断言。
- **已合并并 bump**：`OrzPythonMC#71`（squash → `65f24a5`）、`OrzMCKit#56`（squash → `e96de48`）；
  父仓库两次独立 `chore(submodule)` 提交（`f272e46` / `29d21b1`），父仓库 CI ✓，Pages 已重新部署 ✓。
- **Release PR 已就绪（等人工按「合并」）**：Python **#70 → 2.12.0**、Swift **#55 → 0.13.0**；
  两边的 `### ⚠️ 升级须知` 已手工写进 release PR 的 `CHANGELOG.md`（补全命令改道、非交互需 `--yes`、
  错误改 stderr、用法错误退 1），CI 全绿（含 `quality` / `cli-acceptance`）。
- **已发版（2026-10-18）**：Python **v2.12.0**（Release 6 平台资产齐、`orzmc` / `orzmc-app` 双双上 PyPI 2.12.0、
  Pages 已重部署）与 Swift **v0.13.0**（`orzmc-macos-{arm64,x86_64}` + `SHA256SUMS`）。
  两边的「升级须知」已补进 **GitHub Release notes**（release-please 生成 notes 时用的是 PR 创建时的快照，
  手工改 CHANGELOG 不会自动带进 notes —— 合并后必须 `gh release edit --notes-file` 再同步一次）。
- **发版后验证**：直接下载 **已发布** 的 `orzmc-macos-x86_64`（v2.12.0）跑 `scripts/accept_cli.py --cli …`
  → **24/24 通过**（含曾经必崩的 `completion install` / `--show-completion`），确认用户拿到的产物是修好的。
- **流程教训（已记进 CONTRIBUTING）**：release-please 会 force-push 自己的分支，手工写进 release PR 的
  CHANGELOG 段落可能在它下一次更新时被覆盖 → 「升级须知」在**合并前最后一刻**加，或合并后用
  `gh release edit` 补到 Release notes（本次就是后者）。

- **注意**:Swift 侧本地无法编译（本机只有 CommandLineTools，包要 Swift 6），改动以 `OrzMCKit` CI
  （macos-15，含 `cli-acceptance`）为准 —— 现已全绿。

**下一步**
1. 用户确认后推分支 → PR（标题建议 `fix(cli): 修复冻结二进制补全崩溃并补齐 CLI 自动化验收`）→ 合并后父仓库 bump `python` 指针。
2. **发版时补「升级须知」**：`--install-completion`/`--show-completion` 已移除（改用 `completion install`）；
   非交互卸载/移除必须带 `--yes`（缺则 130）；用法错误退出码 2 → 1；错误改走 stderr。
3. **Swift 待对齐**（见 `cli-surface.md` §10.1）：`-h`、非交互 `remove`/`uninstall` 取消语义、
   `completion install` 的 `data.hint` 与未知 shell 的 `E_USAGE`、CLI acceptance harness。

### 2026-10-17 — pi（App Phase B：`install.conf.surface` + GUI 反向安装 CLI；发 0.12.0）

**发版**：合并 OrzMCKit release PR #53 → **`v0.12.0`**（六平台资产 + SHA256SUMS 已发布）。

**规范先行（父仓库）**：`install-update.md` 新增 **§3.1**：`surface = cli|gui` = **哪个前端装了
PATH 上的 `orzmc`**（不是 GUI 自身登记）；安装器写、`update` 保留原值、缺失 = 旧记录；
选择手段是环境变量 `ORZMC_SURFACE`（缺省 `cli`）。`frontends.md` F1 身份判断加入 `surface`。

**实现（两个通道 + GUI 都写/读）**
- Python（#69）：`InstallManifest.surface`；`docs/install.sh` / `install.ps1` 写 `surface=`；
  `update` 走 `dataclasses.replace` 天然保留。
- Swift（#54）：**`InstallManifest` 下沉到 `Game` 公共面**（`Sources/Game/Install/`，新增 `surface`
  与只读 `current()`）——它是跨前端共享契约，CLI `update`/`uninstall` 与 GUI 都要读；
  `scripts/install.sh` 写 `surface=`。
- GUI（#26）：设置页 **「Command Line」** 区块——显示 `orzmc` 版本/路径/**由谁安装**，
  一键调用官方安装器（Python / Swift 通道，**不复制安装逻辑**）并以 `ORZMC_SURFACE=gui` 运行；
  确认对话框显示将执行的一行命令，安装中逐行回显输出与退出码。**D7「互相安装/打开」补齐**。

**顺手抓到一个真 bug（Swift 通道安装器）**：`scripts/install.sh` 用
`orzmc version | awk '{print $2}'` 取版本，而 `orzmc version` 之后会打印**多行合规声明**
→ 声明被写进 `install.conf` 的 `version` 字段（实测 0.12.0 装出
`version=0.12.0\n\nAN\n是独立的社区开源项目，与\nMojang`）。已改为 `head -n 1 | awk` +
空值兜底 `unknown`；影响范围仅 Swift 通道安装记录（`update`/`uninstall` 不依赖该字段解析，功能未坏）。
→ **下次 OrzMCKit 发版时，Release notes 需补「升级须知」**：该版本前安装的记录 `version` 字段可能被污染，
重跑一次安装器即可修复（符合 §7 发版须知规则）。

**观察（非缺陷）**：发版后立刻用 `releases/latest/download/<asset>` 可能拿到**上一版**二进制
（0.12.0 刚发布时 latest 的 arm64 仍是 0.11.1 字节，而 SHA256SUMS 已是 0.12.0）→ 安装器 SHA256
校验会拦下并报错（**失败安全**）。等几分钟或 `ORZMC_VERSION=vX.Y.Z` 即可。

**验证**：Python `ruff`/`mypy`/`pytest` 全绿 + CI 六平台绿；引擎 air `swift test` 88 tests/22 suites、
conformance 76/76；GUI air `xcodebuild build` 绿、CI 绿；两个安装器真实实跑（临时 `XDG_STATE_HOME`）：
`ORZMC_SURFACE=gui` → `surface=gui`、缺省 → `surface=cli`，`version` 单行正确。

**父仓库**：三次独立 bump（`e854d54` python `3974436`、`453aeec` OrzMCKit `329230f`、`5c6ac12` app `50b08a6`）
+ `2d336a8` 规范定稿。

### 2026-10-17 — pi（App Phase A：GUI 收回成纯适配器）

**起因**：CLI 侧基本收敛完了，问「macOS App 是否需要先改造适配」。核对结论：共核已完成大半
（`GUIClient`/`GUIServer`/`GamePlan`/托管 JRE），但 GUI 仍有三处「自成一套」——服务端只支持
vanilla/paper、进度只有一个 `Double`、Java 状态读系统 JDK 并引导手动装。Phase A 只做这三件事。

**引擎（OrzMCKit #52，分支 `feat/gui-progress-observer`）**
- 新增 `Game.LaunchProgress`（kind/completed/total/label/fraction/isComplete），由 `TransferProgress` 映射；
  前端不必依赖 `TransferKit`，也不必假装有控制台。
- `ProgressReporter(observer:)`、`Client.downloadClient(onProgress:onEvent:)`、`ServerInfo.onProgress`
  把同一条进度并行发给前端；CLI 不传 → 行为不变。
- Vanilla/Paper/Fabric/Forge 部署进度全部接观察者；`ForgeMeta.downloadInstaller(onEvent:)`。
- **Paper 服务端改流式落盘**（临时件 → 原子替换），此前整包 `Data` 堆内存。

**GUI（OrzMCApp #25，分支 `feat/phase-a-engine-adapters`）**
- `GUIServer` 206 → 22 行，只做类型分发；删掉自写 Paper/Vanilla 下载（无续传/校验/重试）与
  「fabric/forge 暂未接入」缺口。`SettingsModel.ServerSoftware` 增 Fabric/Forge，详情页按四种核心统一渲染。
- `LaunchProgressHandler: Double → Game.LaunchProgress`；`GameModel` 保存阶段标题/已完成/总量/单位，
  **不定长时不画假 0%**（旋转指示器 + 阶段文案）。
- `JavaRuntimeService` 只扫 `<root>/java/<major>`（`JavaRuntime.managedExecutable`），状态语义
  `valid` / `missing`（启动自动安装）；**删除侧栏手动 Download/Install JDK**（与 B5 托管冲突）。

**验证（air）**：引擎 `swift build` 绿、`swift test` **86 tests/22 suites**、conformance **76/76**、
`surface.py --strict` 0 差异；GUI `xcodebuild build` 绿（对引擎 feat 分支，air 上临时把 pbxproj 的
`branch = main` 指向 feat 分支，未提交）、`swift test` 4 suites 绿；真实 smoke：
`orzmc server --type paper` → 下载 100% → Paper 启动成功（已清理）。

**合并（已按序完成）**：先引擎 #52（CI 绿）→ 再 GUI #25（首次 CI 因 HEAD 制解析旧 `main` 而红，符合预期；
引擎合并后 rerun 即绿）→ 父仓库两次独立 bump（`ce14853` OrzMCKit `0d36e26`、`e43e7d7` app `23b4130`）。
教训：**GUI 的 HEAD 制依赖决定了「引擎 PR 必须先进 main，GUI CI 才会绿」**，不要并行等 CI。

**剩余（Phase B/C，未做）**：① `install.conf` 的 `surface = cli|gui`（需先改 `install-update.md` §3）；
② GUI 反向「安装/打开 CLI」入口（D7 的另一半）；③ GUI 认证 UI —— **等 authlib-injector / BYO 决策**，
现在做会返工。

### 2026-10-17 — pi（新增规范 `spec/frontends.md`：多前端、单数据）

- **起因**：确认“同一台机器同时装 Python CLI 与 Swift CLI + App 会不会冲突”。实测结论：
  两侧**刻意共用同一套落点**（`${XDG_STATE_HOME:-~/.local/state}/orzmc/{install.conf,auth.json}`、
  `${XDG_BIN_HOME:-~/.local/bin}/orzmc`、`~/minecraft`、补全文件）；冲突主要集中在
  **同名二进制占位**、**共享记录导致 uninstall 连带拆除**、**同一 profile 运行时争抢**，而非格式不兼容。
- **维护者定位（已写入规范）**：这不是缺陷，而是设计预想——**不同实现就是同一套数据的不同“前端”，
  规范与数据唯一、前端可以有多个，规范驱动**。
- **产出**：
  - 新增 [`docs/spec/frontends.md`](docs/spec/frontends.md)：模型图、数据归属表（位置/写入者/并发语义）、
    共存规则 **F0–F9**、隔离矩阵、**新前端接入清单**、反模式、现状与待补。
  - 新增 [`docs/spec/fixtures/state/paths.json`](docs/spec/fixtures/state/paths.json)：共享落点机器可读快照
    （供将来的 `state.paths` conformance 用例）。
  - 交叉引用：`spec/README.md`（§1/§2/§3）、`docs/README.md` 索引、`product-architecture.md` §1.2
    标题改为“一个 `orzmc`，多个前端，一套数据”、`install-update.md` §2/§3、`auth.md` §5、`fixtures/README.md`。
- **顺手抓到一个真实漂移**：`install-update.md` §3 早已声明 `install.conf` 的 `surface = cli|gui` 字段，
  但**两侧安装器都没写**（Python `install.sh`、Swift `InstallManifest` 均缺）——已标“尚未写入”，列为待补项 2。
- **待补**（frontends.md §7）：① `state.paths` conformance 用例（需两侧适配器各加一个 op）；
  ② `surface` 字段落地；③ `auth.json` 跨进程刷新锁。

### 2026-10-17 — pi（第 2 次 AppID 申请已提交：launcher-only）

- 维护者已在 `aka.ms/mce-reviewappid` 按新材料提交（launcher-only）。
- **提交后返回页**：`https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=v4j5cvGG…`——这就是**表单页本身**，
  与之前记录的表单 ID 一致；即**没有可引用的提交编号**，结果只能等邮件（发到表单填的联系邮箱）。
- 已回填：`docs/auth-application.md` §7 两次提交表 + §9 状态；本文件 §1 下一步、§4 A3d。
- **判定口径**：参照第 1 次（10-16 提 → 10-17 出结果，约 1 天一批）；**若两周无邮件即按未通过**，
  **不再投第 3 次**，转 authlib-injector / Yggdrasil。

### 2026-10-17 — pi（核实白名单到底卡在哪一步 + 改写为 launcher-only 申请材料）

- **问题**：到底哪个 API 需要白名单？是不是大部分第三方启动器根本不需要？
- **核实结论（有外部证据）**：
  - ① 设备码 / ② 令牌 / ③ Xbox Live / ④ XSTS = 微软公开接口，**自注册 Azure app 即可**；
  - **只⑤ 是门**：`POST https://api.minecraftservices.com/authentication/login_with_xbox`（Mojang allow-list）；
  - 我们自己的实测：①–④ 均 200，⑤ 403 `Invalid app registration` —— 可定位到单点。
  - **Prism/HMCL 能用 ≠ 不需要**：证据是 `neil289506-commits/mlcmLauncher` PR #7——
    其自家 Azure app “Mojang 已通知審核通過” 后才生效；**在那之前它用的是 Prism 的 client ID**（说明 Prism 在名单内）。
  - 旁证：`yannickfan67-ai/UN_Nexo` issue #22 收到与我们**措辞几乎一致**的拒信（2026-09-21），
    并明确说“未给技术原因，不能据此推断被认定为 bad app”；其补救尝试是**删掉离线启动面**——
    但 Prism 本身支持 Offline 账号却仍在名单内，所以该假设**不成立**，真实标准是黑盒。
- **顺带纠正一处记录错误**：`v4j5cvGG…` 是 **Microsoft Forms 的表单 ID**（所有人相同），不是提交回执；
  已写入 `docs/auth-application.md` §7。
- **本次产出（纯材料，不动产品）**：`docs/auth-application.md` 整篇改写为**第 2 次提交（launcher-only）**：
  - Purpose / 描述 / Justification 只讲**启动器 + 用户本人登录启动**；服务端部署降为“不调用该 API 的独立工具”；
  - 不再主动强调“默认离线启动”，改为正面陈述“不绕过 entitlement”（仍为事实，无虚假陈述）；
  - 新增 §0「为什么这么改」与 §9「提交步骤」；§7 加两次提交记录表。
- **待维护者操作**：在 `aka.ms/mce-reviewappid` 提交后回填日期/结果；再被拒则**停止重投**，转 authlib-injector。

### 2026-10-17 — pi（Mojang 审核被拒：记录结论 + 申请材料脱敏）

- **事实**：收到 Mojang Enforcement（`MCENotify@microsoft.com`）邮件——本批 appID **未获批准**、未进 API 白名单；同批另有违规应用被处置；明确**不提供**申诉/咨询/排障。
  ⇒ `login_with_xbox` 仍 `403`，**内置 `client_id` 实际不可用**；`--auth` 离线部分（契约/映射/存储/错误码）不受影响。
- **决定**：不再重复提交（该批次已有 bad-app 处置语境，继续提交边际收益为负）；**不做**冒用官方客户端的 client id 等规避行为（违反 Minecraft EULA/Usage Guidelines）。
- **邮件里的 "Official Minecraft Server List"**（`aka.ms/OfficialMinecraftServerList` → `findmcserver.com`）只是**公开服务器目录/发现入口**（面向服主，供玩家检索），不提供任何 API 授权或认证能力——与 appID 白名单无关，对本项目无用。
- **本轮改动（纯簿记，无代码行为变更）**：
  - `docs/spec/auth.md` §10：状态从“待审核”改为“**已提交、2026-10-17 被拒**”，加后果与“不重复提交/不冒险规避”的边界；A4（真实 E2E）标为被阻塞。
  - `docs/auth-application.md`：顶部标结果；两个真实邮箱 **9 处脱敏**为 `<redacted>`；联系渠道改为 GitHub 组织（与合规声明的 `contact_url` 一致，不再写邮箱）。
  - `docs/spec/README.md` §4、`docs/spec/cli-surface.md` §10：去掉过时的“`client_id` 待注册”，改为“已注册但审核被拒”。
  - 本文件 §1 主题/状态/下一步、§4 A3c/A4 同步。
- **待拍板**：A. authlib-injector / Yggdrasil（推荐）/ B. 摘掉内置 `client_id` 改 BYO / C. `--auth` 降级。

### 2026-10-17 — pi（发版：OrzPythonMC 2.11.0 / OrzMCKit 0.11.1）

- **发版**：release-please PR python #68（2.11.0）、kit #48（0.11.0）与 kit #51（0.11.1）均用 `--admin` 合并（bot PR 触发不了检查）。
- **产物**：python 6 平台二进制 + PyPI（`orzmc` / `orzmc-app` = 2.11.0，已核对 PyPI JSON）；kit `orzmc-macos-{arm64,x86_64}` + `SHA256SUMS`。
- **真机验收**：
  - 本机重新用 `python/docs/install.sh` 装 2.11.0 → `--version`、`install.conf`（`v2.11.0` / `macos-x86_64`）、`capabilities` 的 enum 均对；
  - 下载 kit 0.11.0/0.11.1 的 x86_64 二进制实测：`--version`、`completion fish`、enum 正常。
- **发版后修复（0.11.1）**：`server --type` 帮助仍写 `vanilla/paper`，与 0.11.0 新增的 fabric/forge 矛盾 → #50，随后 0.11.1 patch（`851f322`）已含修复（实测 0.11.1 二进制文本为 `vanilla/paper/fabric/forge`）。
  > 注：0.11.0 与 0.11.1 资产**字节数恰好相同**，但 SHA256 不同——不要用 size 当身份。
- **教训**：发版后必须抽一个**发布二进制**跑一遍关键 help/enum，不要只看 CI 绿；本次就是这样抓到帮助文本过期的。

### 2026-10-17 — pi（收尾 B8/B10：进度结构化 + 版本选择器）

上一轮剩下两条 ⚠️ 是 Swift 侧行为契约差异，本轮全部清掉：

- **B8 进度**：`TransferKit` 本就产出 `TransferProgress`（kind/total/current），但 `Downloader` 只透 `fraction`。
  OrzSwiftKit #11（`01dc675`）新增 `onEvent` 通道 → OrzMCKit 新增 `Game/Progress/ProgressReporter`：
  count/bytes 分开；`total == nil` **不画 0% 假进度**，改输出一行状态；`tracking()` 统一起条/收尾/失败标红。
  接入 client 下载 / music / Fabric 库 / vanilla+fabric 服务端与 installer；`ConformanceAdapter.normalizeProgress`
  改用**真实模型**（此前是直拷输入，等于没测）。
- **B10 版本选择**：`VersionPickerState`（纯逻辑）+ `runVersionPicker`（行式）：`t` 切 release/snapshot、
  子串搜索、`n`/`p` 翻页、序号选择、`x` 清除、空行回退最新 release；显式 `-v` 现在 release+snapshot 都查
  （非 release 一律算 snapshot）；非 TTY 行为不变。OrzMCKit #49（`71cbf44`）。
- **验证**：air `swift test` **80 tests / 20 suites**；conformance **76/76**；surface 对 Swift **0 漂移**。
- **文档**：`behavior.md` B8/B10 转 ✅（交互形态差异不属契约）；`spec/README.md` §5 「仍待统一」= 无；
  `product-unification-plan.md` Phase 3 差异清零 ☑。

### 2026-10-17 — pi（一份规格约束两套实现：补齐缺口 + 校验可发现）

用户问「CLI 改造完成了吗 / 满足一份规格约束两种实现吗」。实跑核对后发现：**命令面 0 漂移、conformance 76×3 全绿、两侧 CI 已接**，但有 4 个功能层缺口，且 `surface.py` **不比 enum**，所以“声明了没实现”会静默漏掉。本轮全做：

1. **校验器纳入 enum 比对**（父仓库 `8511b12`）：`surface.py` 对 manifest 的 `option.enum` 与实现 `capabilities` 上报值做集合比对，缺值/多值均为漂移；未上报视为 unknown（只提示）。`cli-surface.json` 新增 `deviations.{python,swift}`，已声明 `app --channel appstore`（App Store 未上架）。
2. **Python 上报枚举**（#67 `74578c1`）：`introspect.ENUM_VALUES` → capabilities `enum`；MCP `inputSchema` 透传。
3. **Swift 补齐服务端 fabric/forge**（#46 `04df994`）：`FabricServer`（先落 vanilla `server.jar`，再跑 fabric-installer 生成 launcher）、`ForgeServer`（promotions → 官方安装器 → shim+`libraries/` 或旧版 universal）；`GamePlan.Layout.serverBuildDir`、`ServerInfo.refresh`、`ServerCommand` 四类型接线。
4. **Swift 补齐补全 + 上报枚举 + 升级护栏**（#47 `9f91bee`）：`completion fish/powershell/pwsh`（与 `capabilityList()` 同源渲染）、`capabilityEnums`、MCP schema enum；`update` 对齐 Python 三个坑（安装记录护栏 / `.orzmc-update.log` / staging 失败清理）。

**验证**：air `swift test` 70 tests/18 suites；conformance 76/76；`surface.py --strict` Python/Swift 均 **0 处未声明差异**（各 1 处已声明）；`check.py` 全绿。
**文档**：`behavior.md` 按代码刷新 B1–B11（Swift 仅余 B8 运行时进度、B10 snapshot 渠道/搜索）；`product-unification-plan.md` 进度表更新；`spec/README.md` §5 改为「已对齐/仍待统一」。

### 2026-10-17 — pi（清理个人仓库旧链接 / 文档不一致）

- **背景**：子模块中不在 `OrzMC` 的只有 3 个（`OrzGeeker/OrzSwiftKit`、`OrzGeeker/OrzAppUpdater`、`aternosorg/thanos`）+ 非子模块依赖 `OrzGeeker/OrzSwiftLint`。用户决定：`OrzAppUpdater` 也是通用 App 自升级组件，与 `OrzSwiftKit`/`OrzSwiftLint` 一样**不迁移**（通用基础设施留在 OrzGeeker）；`thanos` 是第三方上游，不迁移。
- **修复的旧链接**（违反 `product-architecture.md §7.1`「禁用会重定向的旧路径」）：
  - `MojangAPI`（#7，`b4f0dd6`）：README Package 示例/SPI 徽章 + `openapi.yaml` 的 Repo 链接；
  - `PaperMC`（#4，`44ef06d`）、`ExarotonAPI`（#2，`4f5c1a2`）：README 里的 Package/clone/SPI/blob 链接；
  - 旧 SPI 路径实测 **404**，`OrzMC/*` 为 **200**（所以这不是纯措辞问题）。
- **文档措辞**：`product-unification-plan.md` / `product-architecture.md` 把「部分依赖在个人仓库（`wangzhizhou/*`）」改为现状：引擎依赖（MojangAPI/PaperMC/ExarotonAPI）均已在 `OrzMC`，仅通用组件在 `OrzGeeker`。
- **profile**（`OrzMC/.github` #2，`bb6b4ac`）：`thanos` 由“上游 fork”改为“直接引用上游，未 fork”（组织内确无 `OrzMC/thanos`）。
- 保留不动：作者署名注释、`PaperMC/LICENSE` 的 Copyright、`plugin` 里对 `wangzhizhou/pi`（上游工具 fork）的引用，以及 `product-architecture.md §7.1` 的「旧路径」映射表（它就是规则本身）。

### 2026-10-17 — pi（CLI 卸载命令 self-uninstall → uninstall，规范先行）

- **诉求**：`self-uninstall` 不符合 CLI 卸载命名习惯，改为 `uninstall`；**先改规范再改实现**。
- **规范（父仓库 `f3c639b`）**：`docs/spec/cli-surface.json`（命令名 + `--yes/--remove-root/--force`）、`cli-surface.md`、`install-update.md`、`data-model.md`、`product-unification-plan.md`（D13）、`docs/compliance/privacy.md` 先行改名。
- **实现**：python #66（`3c061cb3`）、OrzMCKit #45（`f277e4f5`）、site #6（`88e14b1b`）。Python `@app.command("uninstall")` + MCP 排除清单 + README/落地页/installer-design/AGENTS/验收 harness；Swift `UninstallCommand` + `Feature.uninstall`（rawValue 即命令名）+ MCP 排除。
- **规范驱动 CI 的坑**：`docs/spec/cli-surface.json` 是**父仓库**的单一事实源，子模块 CI 会 `checkout OrzMC/OrzMC` 后 `--strict` 比对——所以**必须先把父仓库 spec 推上 main**，否则子模块 CI 会报“缺少 self-uninstall / 多出 uninstall”（本次先推父仓库再 rerun 即绿）。
- **破坏性变更**：按仓库约定（2.x 不用 `!`）走 minor + CHANGELOG 人工注明。
- **已发版**：OrzPythonMC **2.10.0**（`fdfe17b`）+ OrzMCKit **0.10.0**（`41c4950`），六平台二进制 + PyPI 全部成功；两处 CHANGELOG 与 Release notes 均已补「⚠️ 升级须知（卸载命令改名）」。
- **发版后文档/Pages 一致性修复（python `fd8e65a`）**：`docs/install.sh` / `docs/install.ps1`（Pages 上的一键安装器）帮助与提示仍写 `self-uninstall` → 改 `uninstall`（**保留 install.ps1 的 BOM**）；删掉误入库、无人引用且会被上传到 Pages 的 `docs/index.html.bak`；ci.yml 注释同步。Pages 已重新部署（`fd8e65a`）。教训：搜“待同步命令名”时别漏 `*.sh`/`*.ps1` 这类非代码后缀。

### 2026-10-17 — pi（合规声明单一事实源 + 版本输出美化/去邮箱）

- **诉求**：`orzmc version` 的声明中英混在一行、与版本号无视觉分隔、且泄露联系邮箱；其他显示声明处也有类似问题；希望“声明改一处全局生效”。
- **事实**：声明早已是单一事实源——父仓库 `docs/compliance/compliance.json` + `scripts/sync_compliance.py` 会生成 Swift `Compliance.swift`、Python `_compliance.py`、四处 README 合规块、官网页脚/隐私页。本次改的是**渲染格式与联系渠道**。
- **变更**：去掉 `contact_email` → `contact_url`（GitHub 组织）；声明渲染为**英文/中文/商标各占一行**（`Compliance.text` / `disclaimer_text()`，保留 `disclaimer_line` 旧名）；CLI 版本行与声明空行分隔 + dim + soft_wrap；app 的联系按钮由 mailto 改为打开 GitHub 组织。
- **落地**：python #64（`b332bfb`）、OrzMCKit #43（`a1af7c5`）、app #24（`eba6fd5`）；父仓库合规源同步。
- **顺手修的 CI 坑**：app 的 OrzMCKit 是 `branch: main`（HEAD 制），但 `org.swift.swiftpm` 共享仓库缓存里的**分支 ref 与 SourcePackages 解析状态会钉住旧 revision**，删 `Package.resolved` 也没用（CI 实测把源码回退到旧 revision、构建报 `no member 'contactURL'`）。已改为解析前显式 `git fetch` 分支 + 清掉缓存的 OrzMCKit checkout/`workspace-state.json`。

### 2026-10-17 — pi（修复 `orzmc update` 无法升级：裸名 argv[0] 解析）

- **症状（用户报）**：本机 `orzmc update` 执行后没升级，`orzmc version` 仍是旧版。
- **根因**：CLI 用 `Path(sys.argv[0]).resolve()` 定位自身二进制。经 PATH 以裸名 `orzmc` 调用时 `sys.argv[0]` 就是 `orzmc`（不是路径），会按**当前目录**解析 → 升级/创建了 `./orzmc`，安装的二进制没动；同时 `install.conf` 仍被改写，下次运行还以为“已是最新”。实测：在含同名文件的目录里裸名运行，CWD 的占位文件被换成 16MB 新二进制，安装目录里的仍是旧版。
- **修复（OrzPythonMC #60 / #62，`e2bf959`）**：新增库公共 API `running_binary()`（含分隔符则直接用；frozen 用 `sys.executable`；否则 PATH 查找并**丢弃落在 CWD 的命中**；再退回解释器）；CLI `update`/`self-uninstall` 改用它；`_record` 仅在安装记录指向的二进制与本次目标一致时才改写（升级拷贝不再污染全局记录）；验收 harness 加步骤 5b（六平台）。Windows 上 `shutil.which` 会**先搜 CWD**，故 frozen 分支必须用 `sys.executable`（main CI 的 windows installer 两例复现过）。
- **验证**：`ruff`/`mypy`/`pytest`（395）全绿；重建 PyInstaller 二进制实测修复；`scripts/accept_selfupdate.py` **24/24**；main CI 六平台 `installer` 全绿。
- **待办（需确认）**：release-please 已开 **#61 → 2.9.1**。用户机器当前是 2.9.0（含此 bug，裸名调用），需发 2.9.1 后用户用**绝对路径**再跑一次 `~/.local/bin/orzmc update`（或用一键安装器）才会拿到修复。
- **已发布 `2.9.1`（`0a8a797`）**：合并 #61 → Release 六平台二进制 + PyPI 全部成功；用户机器已用绝对路径升级到 **2.9.1**（`orzmc version` = 2.9.1，`install.conf` 一致），裸名 `orzmc update` 已验证正常；顺手清理了 bug 期间产生的拷贝（`~/OrzMC/orzmc`、`~/Downloads/orzmc`）与 `.orzmc-update.log`。
- **`air` 也命中同一 bug（已修）**：其安装的 `~/.local/bin/orzmc` 是 **2.4.1**（Sep 21）；在 `~` 下裸名 `orzmc update` 把 2.9.1 写进了 `~/orzmc`、安装的没动（`install.conf` 被改成 v2.9.1）。已用**绝对路径** `~/.local/bin/orzmc update` 升到 **2.9.1** 并清理 `~/orzmc` + `~/.orzmc-update.log`；裸名复测正常。→ **2.9.1 之前所有已发布二进制都带此 bug**，旧机器需用绝对路径（或一键安装器）过河。
- **Windows 验证机（`win`）正常**：安装的 `…\Programs\orzmc\orzmc.exe` = **2.9.1**，无残留 `orzmc.exe`。
- **升级须知已入库并固化为约定（OrzPythonMC #63，`a57fb6f`）**：
  - `CHANGELOG.md` 的 2.9.1 条目加「⚠️ 升级须知」（现象 + 三种「过河」方式）；
  - GitHub Release `v2.9.1` 的 notes 已用 `gh release edit` 同步（保留机器人生成正文）；
  - `CONTRIBUTING.md` 新增「升级须知」节（触发条件 + 写法模板 + 同步命令）；`AGENTS.md` 发布链路补硬性规则；父仓库 `AGENTS.md §7` 同步一条伞级规则。
  - 原则：**release-please 只渲染 commit 列表，不会替你说“用户该怎么办”**；凡需用户手动处理（自升级/安装器 bug、破坏性变更、迁移、已知问题）必须写进该版本 CHANGELOG **和** Release notes。

### 2026-10-16 — pi（CI/迭代提速：SwiftPM 缓存 + 修重复触发）

- **诊断**：一次跨三仓改动 CI 墙钟 ~130min。根因：Swift 侧无缓存（每轮冷编整棵依赖图）+ `OrzSwiftLint` 构建插件把 `swift-syntax` 拖进每次编译（MojangAPI 引入 CacheKit 后 2.8→9.4min 即为实证）+ MojangAPI `push`+`pull_request` 双跑 + Intel release 冷编 58min。
- **已落地**：
  - OrzMCKit（`398cec8`）：CI `test`/`conformance` + Release `build` 加 `actions/cache`（`.build`+SwiftPM 克隆，~3GiB/job）。
  - MojangAPI（`32af446`）：加缓存 + `on.push.branches:[main]`（PR 不再双跑）。
  - app（`96f93e2`/`1a163c3`）：加 DerivedData/SwiftPM 缓存。
  - **缓存配额修正（`ci/cache-scope`）**：GitHub 缓存按分支计费（10GiB/仓），PR 分支各存一份 3GiB 会互相驱逐（实测 OrzMCKit 4 份 12.13GiB）。改为 `actions/cache/restore` + **仅 main 未命中时 `actions/cache/save`**，且 test/conformance 共用同一 debug key → 每仓 **1 份 ~3GiB**。
  - 实测 warm（缓存命中）：MojangAPI 9.2→**4.1min**、OrzMCKit 8.3→**3.5min**、app 10.1→**4.9min**（首次 run 因写缓存偏慢）。
- **受阻**：Release 的 x86_64 交叉编译（`swift build --arch x86_64`）被 `swift-openapi-generator` 构建插件挡下（按 `ARCHS` 校验、`VALID_ARCHS` 仅 arm64），故仍用 Intel runner，靠缓存提速。**真正的下一步是 E：把 SwiftLint 从 release 编译路径移走**（去 swift-syntax）。
- **lint「两全」（最终方案）**：先（OrzSwiftKit #9）摘掉 build-tool 插件以去编译开销，但发现本地不再自动 lint（问题后置到 CI）→ 不理想。
  最终：`OrzSwiftLint 0.0.8`（`OrzGeeker/OrzSwiftLint`）改用 SwiftLint 官方**预编译** `SwiftLintBinary.artifactbundle.zip`（binaryTarget），`OrzSwiftKit #10` **把插件重新挂回** → **本地/CI 每次构建都自动 lint**，且**零 swift-syntax 编译**。
  air 实测：本包冷建 ~50s、`MojangAPI` 冷建 43s、`.build` ~0.7–1.7GiB（原源码方案 ~2.5–3GiB）、日志 0 次 swift-syntax 编译；OrzSwiftKit CI 183s。
- **顺带**：MojangAPI 把打线上 API 的用例（`manifest/versions/getUserInfo`）门控到 `ORZMC_NETWORK_SMOKE=1`（曾 3 次因 HTTP 421 把 CI 跑红），并加手动 `network-smoke` job → CI 只跑离线确定性套件。
- **Release 提速（验证）**：发 `v0.9.1`（`c42f677`）时 Release job 也带了缓存，且无 swift-syntax：arm64 ~**4m17s**、Intel ~**13m02s**（原 58m27s，~4.5×）。
- **成本**：全流程**零花费**（仓库均 public；只用标准 `macos-15`/`macos-15-intel`/`macos-26`/`ubuntu` runner，未用计费的 `-large`/`-xlarge`；缓存 ≤10GB 免费额度）。已在各 `ci.yml`/`release.yml` 加护栏注释防误用。
- 父仓库分别 bump `swift/lib/MojangAPI` / `swift/lib/OrzMCKit` / `swift/app` 指针；同步 `RELEASES.md` / 本文件。

### 2026-10-16 — pi（三端共享 Mojang 元数据缓存 + 布局文档对齐）

- **问题**：`docs/spec/data-model.md §1` 对照表过时（指向已退役 `GameDir.swift`）；Swift 的清单/版本 JSON 落在 `~/Library/Caches/MojangAPI`，版本 JSON 更是只走内存 —— 与 Python `<root>/cache` 不共享。
- **MojangAPI #1（`fe72c69`）**：`configurePackageCache(directory:)` + `packageCacheDirectory`；版本 JSON 以**原始 Mojang 字节**落 `<dir>/versions/<id>.json`（逐字节保留是刻意的：Python 按清单 sha1 校验缓存，重编码会哈希不符而被丢弃）；读缓存校验 sha1；未配置时行为不变（仅内存）。
- **OrzMCKit #36（`v0.9.0`，`8662410`）**：`Game/MojangCache.configure(root:)`，在客户端下载/启动、Vanilla/Paper 服务端、`JavaRuntime`、`GameUtils`、CLI `chooseGameVersion` 等入口配置为 `<root>/cache`；`Package.resolved` 跟进 MojangAPI。
- **app #20（`42a06eb`）**：`GameCatalogService` 同样按 `GamePlan.defaultRoot` 配置。
- **验证（air，Swift 6.4）**：`swift build` 绿；`swift test` 55 例；`ORZMC_NETWORK_SMOKE=1` 新增冒烟确认 `<root>/cache/version_manifest.json` + `<root>/cache/versions/1.20.4.json` 落盘且版本 JSON 的 sha1 与清单 URL 一致；conformance **76/76**；三仓 CI 绿；`v0.9.0` 发版。
- **文档**：`docs/spec/data-model.md §1` 对照改为「两侧已一致」，并补「元数据缓存位置（与 Python 共享）」说明。
- **父仓库**：分别 bump `swift/lib/MojangAPI` / `swift/lib/OrzMCKit` / `swift/app` 指针；同步 `RELEASES.md` / 本文件。

### 2026-10-16 — pi（文档一致性普查：python 文档 + 两处 GitHub Pages）

- **python 文档**：`README.md` 命令行清单补齐 `capabilities`/`completion`/`mcp`/`plugin`/`app` 与 `client --auth`、`server --demo`/`--print-jar-help`/`--online-mode`/`--kill-all`、`update --channel`、全局 `--json`/`--root-dir`；新增「正版登录」要点。`AGENTS.md` 修正 `client_id` 说明（现为 `resolve_client_id()` 三级解析，内置 `DEFAULT_CLIENT_ID` 开箱即用）。PR #59（`b4f1408`）。
- **python Pages（`docs/index.html`）**：快速开始补 forge 客户端与 `--auth` 示例；特性区新增「正版登录」卡片（同 PR #59）。
- **组织官网 GitHub Pages（`site`）**：`content/client.md` 参数表补 `--auth`/`-j`/`--refresh`、数据管理补 `orzmc update`。PR #5（`a9307fb`）。
- **报告未改**：`orzmc client --auth` 的 help 文本仍写「需 `ORZMC_AZURE_CLIENT_ID`」（`orzmc_app/cli/app.py:195`），与内置 client_id 不符 —— 属实现文案、需发版生效，建议单独 `fix(cli)`。
- 父仓库分别 bump `python`/`site` 指针；`check.py` 绿（未触碰合规块）。

### 2026-10-16 — pi（官网页脚 UI + 组织级隐私政策）

- **页脚合规块重设计**：加顶部分隔线，免责声明与「隐私政策 · GitHub 组织」链接分行，链接 hover/focus 下划线，小字对比度提升（原 `white-40` → 0.5 / 链接 0.72）；**不再暴露个人邮箱**，改链 GitHub 组织主页。
- **隐私政策改为组织视角**：适用范围（官网 / 开源软件 / GitHub 协作）、软件本地数据与 `--auth` 令牌、官网第三方（不蒜子统计、`api.mcstatus.io`、`mc-heads.net`）、第三方清单、数据安全与保留、你的权利、儿童、变更、联系（GitHub）；修复同页双 `<h1>`、补 TOC。
- **单一事实源同步**：父仓库 `docs/compliance/`（新增 `contact_url`、重写 `privacy.md`）+ `scripts/sync_compliance.py`（重写 `html_block`、`site_privacy` 去正文 H1/加 `toc`）→ 生成 `site/content/privacy.md` + 页脚块；`site` PR #4（`79ba16a`），父仓库 bump `site` 指针。
- 验证：`hugo -e production --minify --gc` 构建通过；`scripts/check_content.py` 通过；隐私页 `<h1>` 计数 = 1；页脚/隐私页不再含邮箱。

### 2026-10-16 — pi（Swift `client --type forge` + 修复托管 JRE 解压 + `--strict` 进 CI + codegen 评估 + 发版 v0.8.0）

- **OrzSwiftKit（PR #8，`9b69dba`）**：修复 `ArchiveExtractor` 仅按扩展名分派——`URLSession.download` 的临时文件名为 `.tmp`，导致托管 JRE 下载后解压抛 `unsupportedExtension`（`JavaRuntime.ensure` 首次下载必然失败，是 forge/launch 的**既有阻塞 bug**）。改为扩展名优先、缺失时读魔数（gzip/zip）；离线单测模拟 `.tmp`。
- **OrzMCKit（PR #33 → `v0.8.0`）**：`client --type forge`——新增 `ForgeMeta`（`promotions_slim` → 下载官方安装器 → 读内嵌 `version.json` → 托管 JRE17 无头 `--installClient` → 收集库/patched `-client.jar`），`ProfileAddon.usesOwnClientJar` 排除 vanilla jar；仅支持现代 ForgeBootstrap（1.20.4+），旧版显式 `E_UNSUPPORTED_TYPE`；`Package.resolved` 跟进 OrzSwiftKit。
- **`--strict` 进 CI（PR #35）**：`OrzMCKit` `conformance` job 构建 `orzmc`、导出真实 `capabilities` 与父仓库 manifest 对比，未声明漂移即红灯（不再只靠人工跑）。
- **codegen 评估**：结论「**暂不做代码生成**」（保留 manifest + 两侧 `--strict`；理由与重估触发条件写入 [`docs/spec/cli-surface.md`](docs/spec/cli-surface.md) §8.3）。
- **验证**：air `swift build` 绿；`swift test` **53 例**（含 `ORZMC_NETWORK_SMOKE=1` 真实 **Fabric + Forge** 解析/安装冒烟）；conformance **76/76**；`surface.py --strict` **0 处差异**；CI 绿。发布 `v0.8.0`（期间 Intel release 构建贴 45min 超时被取消 → `release.yml` 抬到 60min 后重跑成功）。
- **父仓库**：bump `swift/lib/OrzSwiftKit` → `9b69dba`、`swift/lib/OrzMCKit` → `ea38889`；类型矩阵/codegen 评估进 `docs/spec`；同步 `RELEASES.md` / 本文件。
- **剩余**：`--auth` 真实 E2E（等 Mojang Game Service API 审核）。

### 2026-10-16 — pi（Swift `client --type fabric` + 命令面两侧 0 偏差 + 发版 v0.7.0）

- **OrzMCKit（PR #31 → 发布 `v0.7.0`）**：客户端 `--type/-t`（`vanilla|fabric`；`forge` 命令面接受、引擎待落地，运行时报 `E_UNSUPPORTED_TYPE`）。新增 `FabricMeta.resolve`（fabric-meta 最新稳定 loader → loader profile JSON，经统一 `MetadataCache`（`<root>/cache`，TTL 24h、`--refresh` 绕过）缓存）+ `ProfileAddon`/`FabricModel.profileAddon` 映射（`FabricModel.Library` 补 `sha1`/`size`/Maven `path`）；Fabric 库落地客户端 `libraries/`（classpath 递归扫描自动包含），启动主类换 `KnotClient` 并追加 loader `arguments.jvm`/`arguments.game`；新增纯计划 `GamePlan.planProfileAddonDownload`；`--json` 信封含 `type`。
- **命令面收敛**：air 上 `orzmc --json capabilities` + `surface.py --strict` → **Swift 0 处差异**；`cli-surface.json` 移除 Swift `client --type` deviation，**两侧均 0 漂移**（Python 早已 0）。
- **验证**：air `swift build` 绿、`swift test` **49 例**（+2；含 `ORZMC_NETWORK_SMOKE=1` **真实 fabric-meta 解析**）、conformance **76/76**（strict）；OrzMCKit CI（test + conformance）绿；发布 `v0.7.0`（macOS arm64/x86_64 + SHA256SUMS）。
- **父仓库**：bump `swift/lib/OrzMCKit` → `0ebf8b9`（发布提交）；同步 `RELEASES.md` / `docs/spec/cli-surface.{json,md}` / 本文件。
- **剩余**：Swift `client --type forge`（Forge installer + patched jar，新引擎能力）；`--auth` 真实 E2E（等 Mojang 审核）。

### 2026-10-16 — pi（合规单一来源 + 免责声明/隐私政策/CLI 声明 + 提交 Mojang 申请）

- **单一来源**：新增 `docs/compliance/{compliance.json,privacy.md}` + `scripts/sync_compliance.py`（`--write`/`--check`），把免责声明/责任主体/联系方式渲染到 8 处引用（README×4、官网页脚、Swift `Game/Compliance.swift`、Python `orzmc/_compliance.py`、官网 `content/privacy.md`）；`check.py` 增加漂移校验（子模块未检出时自动跳过）。
- **落地**：官网页脚免责声明 + **隐私政策页**；App 设置页 Disclaimer（改用 `Game/Compliance`，含隐私链接）；Python/Swift `version`/`--version` 页脚声明。
- **提交 Mojang Game Service API 申请**（2026-10-16，New AppID for Approval）：材料 `docs/auth-application.md`（表单逐字段 + Justification + 合规核对）；提交 ID `v4j5cvGGr0GRqy180BHbR-...`。真实 E2E 阻塞于审核。
- **新增** `python/scripts/accept_auth.py`（审核后真实账号验收；只打状态不打印令牌）。
- 涉及 PR：python #57 / OrzMCKit #30 / app #19 / site #3 / 父仓库 #36、#37（均已合）。

### 2026-10-15 — pi（发版：Python 2.9.0 / Swift v0.6.0，含内置 client_id）

- 合并 release PR：Python **`2.9.0`**（PyPI + 6 平台）、OrzMCKit **`v0.6.0`**（macOS 二进制）。
- 父仓库锚点对齐发布提交（`python edf4292` / `OrzMCKit 0013a89`）。
- 正版授权真实 E2E 仍等 **Mojang Game Service API 审核**（见上一条）。

### 2026-10-15 — pi（正版授权：内置 client_id + 真实 MSA/XBL/XSTS 验证；Mojang API 审核为唯一阻塞）

- 内置 `client_id`（`1a3e628b-c9a5-4a7f-b7b7-562e22b9787e`）：Python `DEFAULT_CLIENT_ID` / Swift `AuthConfig.defaultClientId`（PR #54 / #27 已合）。
- 真实 E2E（本机、走我们的服务代码）：设备码 → MSA 令牌 → Xbox Live RPS → XSTS **全部 200**；`profile.xboxlive.com` 可读 Gamertag。
- **阻塞**：Mojang `login_with_xbox` → `403 Invalid app registration`；`aka.ms/AppRegInfo` → Minecraft 帮助《New: Java Edition Game Service API Review or Application Process》→ 需 **Mojang 审核/申请通过**后方可使用 Game Service API（外部流程）。
- 排障佐证：正确 RP → 403「Invalid app registration」，错误 RP → 401；MSA/XBL/XSTS 均成功 → 不是 client_id/端点/映射问题，而是应用授权门。
- 附带修复：内置 client_id 后，原「缺 client_id」CLI 用例会走**真实设备码轮询**致 CI 挂起 → 改为 monkeypatch `resolve_client_id` 返回空（不联网）；`quality` 由 20min 超时恢复 21s 通过。

### 2026-10-15 — pi（引擎项：extract-music / download-threads / kill-all）

- **OrzSwiftKit (#7)**：`Downloader.concurrency`（默认 `TransferPolicy.defaultThreads`），`transfer` 按当前并发构造。合并 `163053f`。
- **OrzMCKit (#24)**：`client --extract-music`（`Client.extractMusic()`：确保 jar → `unzip "*.ogg"` → `backup/music/<version>`）；`client/server --download-threads`（设 `Downloader.concurrency`，clamp 1–64）；`GameError.clientJarNotFound`；`Package.resolved` 跟进 OrzSwiftKit。
- **OrzPythonMC (#51)**：`server --kill-all`（`infra/process_registry.py` + `ProcessRunner.on_start` + `ServerService` 注册/清除 + 公共 API `kill_all_servers` + CLI）；测试 4 例。
- 父仓库本批 bump + 更新 `cli-surface.json` deviations（**Python 现完全一致；Swift 仅剩 client `--type`**）+ 文档。
- 验证：Python 门禁绿（390 passed）；OrzMCKit（air）build/test 46 绿、conformance 绿；OrzSwiftKit build-test 绿。

### 2026-10-15 — pi（swift-dev 本地联调脚本 + app 清理）

- 新增 `scripts/swift-dev.sh`：`sync`（子模块）/ `edit`（把 OrzMCKit 依赖本地覆盖到 `swift/lib/*`）/ `status` / `unedit` / `xcode`（打印 app 手动步骤）。开发态、不提交。
- app 清理（OrzMCApp PR #17）：删除空 `.gitmodules`；本地 SwiftPM 包 `OrzMCKit` → `OrzMCAppKit`（消除与远端引擎同名冲突）。app 构建 CI 绿；父仓库 bump `swift/app`（PR #22）。
- 文档：`AGENTS.md` §6、`docs/product-architecture.md` §7.1、本文件 §2.5/§2.6 同步。

### 2026-10-15 — pi（结构：Swift 相关子模块收拢到 swift/）

- 新目录约定：`swift/app`（GUI）+ `swift/lib/*`（引擎与 Swift 依赖）——按技术栈分组，与 `tools/` 同构。
- 移动：`app` → `swift/app`；`OrzMCKit` → `swift/lib/OrzMCKit`。
- 新增子模块：`swift/lib/{MojangAPI,PaperMC,ExarotonAPI,OrzSwiftKit,OrzAppUpdater}`（共 21 个子模块）。
- 同步 `AGENTS.md` §1/§4/§7.1、`RELEASES.md`、`docs/**`、`HANDOFF.md` 路径引用；`check.py` 通过（21 一致）。
- **注意**：`app`/`OrzMCKit` 仍以 SwiftPM 远端消费引擎；伞内子模块用于**锁定与本地检出**。开发态本地覆盖路径改为 `swift/lib/OrzMCKit`、`swift/lib/*`。这与 D11 HEAD 制有张力（伞内现在也钉组织自有/OrzGeeker 的 Swift 依赖版本），已在 §3 待决策记一笔。

### 2026-10-15 — pi（发版：Python 2.7.0 / Swift v0.4.0 + 锚点对齐）

- python PR #49（`update --channel`）→ release #50 → **`2.7.0`**。
- OrzMCKit PR #22（`--refresh` / `--symlink` / `--force-download`）→ release #23 → **`v0.4.0`**。
- 父仓库 PR #18（规范 + bump）→ 合并；随后 bump 到发布提交（`python 5fa45d5` / `OrzMCKit 9cf5cf4`）。

**剩余引擎项（最大/最后的几个）**：Swift `client --type`(fabric/forge，需 fabric-meta 解析 + forge 客户端)、`--extract-music`、`--download-threads`(需 OrzSwiftKit `Downloader` 并发参数)；Python `server --kill-all`(跨平台进程跟踪)。

### 2026-10-15 — pi（引擎下沉批：Swift refresh/symlink/force-download + Python update --channel）

- **Swift（OrzMCKit #22）**：`client/server --refresh`（`Mojang.versions(forceUpdate:)`）；`server --symlink`（world → `backup/worlds/<version>`）；`server --force-download`（删/忽略核心 jar 强制重下）。
- **Python（OrzPythonMC #49）**：`update --channel release|beta`（beta 走 GitHub releases 列表，失败回退稳定版）；公共 API 加 `channel`。
- 父仓库本批同步 manifest/spec + bump + RELEASES/HANDOFF。
- 两侧 `surface.py --strict`：Python 声明 1（`server --kill-all`）、Swift 声明 4（client `--type`/`--extract-music`/`--download-threads`、server `--download-threads`）。

### 2026-10-15 — pi（发版：Python 2.6.0 / Swift v0.3.0）

- 合并 python PR #47（`server --print-jar-help`）→ release PR #48 → **`2.6.0`**（PyPI `orzmc`/`orzmc-app` + 6 平台二进制）。
- 合并 OrzMCKit PR #20（`server --print-jar-help` 改名 + client `--jvm-opts`）→ release PR #21 → **`v0.3.0`**（macOS arm64/x86_64 + SHA256SUMS）。
- 父仓库 PR #16（规范改名 + `update --channel` 进规范 + bump + RELEASES/HANDOFF）→ 合并；随后 bump 子模块指针到**发布提交**（`python f20f7ca` / `OrzMCKit 455b019`）。

### 2026-10-15 — pi（B4 进规范 + 参数改名 + 引擎下沉 jvm-opts）

**做了什么**
- **B4 进规范**（父仓库）：`server --print-jar-help`（由 Swift `--jar-help` 改名，名称反映功能）、`update --channel release|beta` 写入 `cli-surface.json` / `cli-surface.md`；`deviations` 相应收敛（Swift 额外项清除）。
- **两侧实现**：
  - Python（PR #47）：`server --print-jar-help`（服务端加 `--help`）+ 补 `demo`/`online_mode`/`print_jar_help` 单测（386 passed）。
  - Swift（PR #20）：`server --print-jar-help` 改名；客户端新增 `--jvm-opts`（`ClientInfo.jvmArgs` → `parseBootArgs` 追加 JVM 旗标）。
- 子模块 bump + `RELEASES.md` 刷新（`python cfcda47` / `OrzMCKit 0df2feb`）。

**状态**
- `surface.py --strict`：Python 0 未声明（声明 2：`server --kill-all`、`update --channel` beta）；Swift 0 未声明（声明 8：client 4 + server 4）。

**剩余**
- 引擎下沉待办：Swift `client --type`(fabric/forge)、`--extract-music`、`--refresh`、`--download-threads`；server `--symlink`、`--force-download`、`--refresh`、`--download-threads`；Python `server --kill-all`、`update --channel`。

### 2026-10-15 — pi（A1 落地 + A2 发版：三仓合并 + Python 2.5.0 / Swift v0.2.0）

**做了什么（全部已推送/发布）**
- `OrzPythonMC`：PR #46（`--auth` 离线链路 + `orzmc mcp` + 服务端选项）→ squash 合并 `969cd05`；release PR #37 → 发布 **`2.5.0`**（PyPI `orzmc`/`orzmc-app` + 6 平台二进制）。
- `OrzMCKit`：PR #19（`--auth` + `mcp` + 命令面收敛/一致性适配）→ 合并 `e237d32`；release PR #16 → 发布 **`v0.2.0`**（macOS arm64/x86_64 + `SHA256SUMS`）。
- 父仓库：PR #14（`auth`/`cli-surface` 规范 + `cli-surface.json` + `surface.py` + `auth/*`/一致性 fixtures + bump `python`/`OrzMCKit` + `RELEASES.md`）→ 合并 `a855dde`。

**顺序**：先子模块（CI 检父仓库**旧** fixtures 仍绿）→ 后父仓库（避免 Swift CI 在 `--strict` 下红灯窗口）。

**已知（既有问题，非本次引入）**：`python3 scripts/verify/check.py --remote` 报 `tools/rust-thanos`、`tools/thanos`、`webmc` 的记录指针不在远端。

**剩余**：待办 A（`client_id`/真实 E2E）；命令面 `deviations` 收敛（Swift 引擎能力 + Python `--kill-all`）；codegen（路线 A 第 3 步）。

### 2026-10-15 — pi（命令面收敛 Step 2：修一批 + deviations 机制）

**做了什么**
- **修实现（实际收敛）**：
  - Python `server`：新增 `--demo`（服务端加 `--demo`）与 `--online-mode`/`-o`（写入 `server.properties`）；`RuntimeOptions` 加 `demo`/`online_mode`。
  - Swift `server`：`--online-mode` 由带值 Option 改为 **Flag**；新增 `--jvm-opts`（映射 `ServerInfo.jvmArgs`，引擎早已支持）、`--yes`（命令面兼容，Swift 默认自动接受 EULA）。
  - Swift `remove`：新增 `--yes`（TTY 确认可跳过；非交互维持原行为）；`self-uninstall`：新增 `--root-dir`（覆盖安装记录/默认根）。
- **deviations 机制**：manifest 加 `deviations.<impl>`，validator 先剔除**已声明**差异——`--strict` 只对**未声明**漂移失败；自检新增「deviations.missing 必须引用真实选项」。
- validator：选项 `required` 不比较（ConsoleKit 无法表达，由运行时报错强制），仅位置参数比较。

**结果**
- Python 漂移 3 → **1**（剩 `--kill-all`）；Swift 漂移 17 → **12**（其中 `remove --version required` 为校验语义问题，已由规则调整消除）。
- 两侧 `surface.py --strict` 均 **0 未声明漂移**（已声明：Python 1、Swift 11）。
- 门禁：Python `ruff`/`mypy`/`pytest`（382 passed）绿；`uv build` 绿；Swift（`ssh air`）`swift build` 绿、`swift test` **46 例**绿；一致性 76/76（参考/Python/Swift）。

**下一步**：按 `deviations` 收敛引擎侧能力（Swift 客户端 fabric/forge、JVM 旗标、缓存/并发、音乐提取、世界软链接/强制重下；Python `--kill-all`），再评估 codegen。

### 2026-10-15 — pi（命令面单一化 路线 A 第一步：manifest + 只读校验器）

**背景**：维护者确认按推荐执行——先落机器可读 manifest + 只读校验器，不阻断，跑顺后再谈 codegen。

**产出**
- 新增 `docs/spec/cli-surface.json`：13 个命令 + 全局选项的机器可读 manifest（选项长名/短名/别名/类型/flag/required/enum/default/位置参数）。
- 新增 `scripts/verify/surface.py`：
  - `--self-check`：manifest 结构自检（纯 stdlib，已接入 `scripts/verify/check.py` → 父仓库 CI，**阻断**）；
  - `--implementation <name> --command/--capabilities`：与实现 `capabilities --json` **只读对比**，列出缺命令/多命令/缺选项/多选项/类型·flag·required 不一致；默认退出 0，`--strict` 才退出 1。
  - 语义：`aliases` 同一选项；位置参数按顺序匹配（名字不比较）；实现多出的全局选项不算漂移。
- `cli-surface.md` 新增 **§8.3**（manifest + 校验器 + 当前已知漂移清单）。

**发现的漂移（将成为收敛清单）**
- Python（3）：`server` 缺 `--online-mode`/`--demo`/`--kill-all`。
- Swift（17）：`client` 缺 `--type`/`--jvm-opts`/`--extract-music`/`--refresh`/`--download-threads`；
  `server` 缺 `--jvm-opts`/`--yes`/`--symlink`/`--force-download`/`--refresh`/`--download-threads`，
  `--online-mode` 实现为带值 option 而非 flag；`remove` 缺 `--yes`（且 `--version` 未标 required）；
  `self-uninstall` 缺 `--root-dir`；规范外多出 `server --jar-help`、`update --channel`。

**状态 / 下一步**
- 自检已进父仓库 CI（`check.py` 第三项）；实现对比**未接 CI**（只读、手动跑）。
- 下一步：按 §8.3 清单收敛一/两侧命令面，再评估 `--strict` 接入与 codegen。

### 2026-10-15 — pi（清理非卡依赖待办：一致性再扩 ①/② + 依赖核验）

**背景**：维护者要求处理 §4 中**不依赖 `client_id`/办卡**的待办项。

**一致性再扩（父仓库 + Swift 适配器）**
- 运行器 `run.py` 新增**反向断言** `"absent": [dotted-path, ...]`（字段必须不存在）；`conformance.md` §4 与 `fixtures/README.md` 同步。
- ① `planLayout` 无 `type`：新增 `layout/no-type-1.20.4`（断言 server 字段不存在）；参考/Python 本就省略，**Swift 适配器 `opPlanLayout` 改为仅在 `given.type` 存在时输出 server 字段**。
- ② 版本源统一为**显式 `given.version`**：新增 `client-plan/mismatched-version-id` 与 `client-download/mismatched-version-id`（`given.version=1.20.5`，snapshot `id=1.20.4`）；参考/Python 本就以 `given.version` 为准，**Swift 适配器新增 `decodeVersionPlan(_:)`，在解码后覆盖 `id`**（引擎仍以 `VersionPlan.id` 为准，接缝处对齐）。`conformance.md` §5 记录该决策。
- 结果：参考 / Python / Swift 三适配器 **76/76**（strict；Swift 在 `ssh air` 上重编并跑）。

**其余非卡待办（核验完成）**
- **Python 侧反向对齐**：三适配器 76/76 全绿，无新增分叉。
- **Windows 真机实测**：T1 已完成；`plugin`/`app`/`mcp` 无 Windows 侧差异（`app` 仅 macOS）。
- **治理｜外部依赖**：`OrzSwiftKit`@`fd88d7d`、`MojangAPI`@`bb8dbe8`、`PaperMC`@`19ae5af`（`main` HEAD）；`OrzAppUpdater` 最新 tag `0.0.3`。

**未处理（需维护者拍板）**
- **命令面单一化（路线 A）**：`cli-surface.md` → 机器可读 manifest + 两侧生成/校验。属架构决策（且需先处置现有命令面差异，如 Swift `client` 无 `--type`），本轮未动手，待路线确认。

### 2026-10-15 — pi（`orzmc mcp` server：规范 + Python/Swift 两端 + 离线测试）

**背景**：维护者确认推进 §4 待办 B，并要求 Swift 同会话完成。

**B1 规范（父仓库）**
- `cli-surface.md`：§2 命令总览新增 `capabilities`/`mcp`；§4 新增 `mcp` 契约；§8.2 由「计划」改写为**定稿**（stdio **换行分隔** JSON-RPC 2.0；`initialize`/`ping`/`tools/list`/`tools/call`；tool 排除集、位置参数、`protocolVersion`、标准错误码 `-32700/-32600/-32601/-32602`；工具失败走 `isError` + 信封）；§10 勾选。

**B2/B3 Python（`OrzPythonMC`，全部离线、零新增依赖）**
- 新增 `orzmc_app/cli/introspect.py`：把 `capabilities` 内省抽为 `command_specs(app)`，供 `capabilities` 与 `mcp` 共用（去重、防漂移）。
- 新增 `orzmc_app/cli/mcp.py`：手写 JSON-RPC（`handle_message`/`serve` 可注入 stdin/stdout）；`tools/list` 由 `capabilities` 生成，`tools/call` 用 `typer.testing.CliRunner` **进程内**转调 `--json`，信封作为 `content[].text` + `isError`；参数→argv、类型校验、未知 tool/参数报 `-32602`。
- `cli/app.py`：`capabilities` 改用 `introspect`；新增 `orzmc mcp` 子命令（延迟 import 断开循环）。
- 新增 `orzmc_app/tests/test_mcp.py`（14 例）；`ruff`/`format`/`mypy` 绿；`pytest` **382 passed**；`uv build --all-packages` 绿；真实冒烟：stdout 仅 JSON-RPC、stderr 空。

**B4 Swift（`OrzMCKit`，`ssh air`）**
- 新增 `Sources/OrzMC/MCPServer.swift`（`MCPRunning` 可注入；默认 `SubprocessMCPRunner` 拉起 `orzmc --json <cmd>`；stdio 循环、`initialize`/`ping`/`tools/list`/`tools/call`、解析容错、`isError`）。
- 新增 `Commands/MCPCommand.swift` + `CommandGroup` 注册（`Feature.mcp`）。
- `Capabilities.swift`：`SignatureValueSpec` 补 `schemaType`/`required`；**修正位置参数名**（`Argument` 不再误加 `--`，`app action` 归位为位置参数）。
- 新增 `Tests/OrzMCTests/MCPTests.swift`（11 例，注入假 runner，全离线）。
- 验证：`swift build` 绿；`swift test` **46 例**绿；真实 `orzmc mcp` 子进程冒烟（`list`/`app status` 信封、parse error）通过；conformance **73/73**（air，strict）。

**状态 / 下一步**
- 所有改动**仅本地工作区**（父仓库 + `python` + `OrzMCKit`），未提交/未推送。
- 剩：待办 A（`client_id`/真实 E2E，需办卡+注册 Azure）；可选：命令面单一化（机器可读 manifest）。

### 2026-10-15 — pi（`--auth` 离线优先：阶段 B/C 实现 + 三适配器 73/73）

**背景**：维护者决定**全部保留本地、不推送**，先把不依赖 `client_id` 的离线部分做完。

**阶段 B（Python 库 + CLI，全部离线）**
- 新增 `orzmc/domain/auth.py`（数据形状）、`orzmc/core/auth.py`（13 个纯映射：请求构造/响应解析/错误分类）、`orzmc/infra/auth_store.py`（`<状态目录>/auth.json`，原子写 + `0600`）、`orzmc/services/auth.py`（`Authenticator`：缓存→刷新→设备码轮询/错误分类，HTTP 可注入）。
- `RuntimeOptions.auth_uuid/auth_access_token/auth_user_type` + `domain/launch.py` 启动参数注入（已认证：uuid/token/`user_type=msa`；离线仍 `0`/随机/`legacy`）。
- CLI `orzmc client --auth`：读 `ORZMC_AZURE_CLIENT_ID`（缺失→`E_AUTH_NOT_CONFIGURED`）；非 TTY/`--json` 设备码写 **stderr**；`--json` 信封含 `authenticated/uuid/expiresAt/source`，**不含 token**。
- `infra/http.py` 新增 `request()`（不在 4xx/5xx 抛错，供 auth 自判状态）；`infra/fs.py` 新增 `write_text_atomic`；`default_state_dir` 下沉到 `infra/fs.py`（selfinstall 重导出）。
- 适配器 `auth*` + `orzmc/tests/test_auth.py` + CLI 测试。**`ruff`/`mypy`/`pytest` 全绿**；Python 适配器一致性 **73/73**（strict）。

**阶段 C（Swift `OrzMCKit`，全部离线）**
- 新增 `Game/Auth/{AuthModel,AuthMapping,AuthStore,Authenticator}.swift`（纯映射 + 原子写 0600 + 设备码编排 + `authenticate(...)` 入口）。
- `ConformanceAdapter` 新增 `auth*` 分发；`ClientCommand --auth` 接线（缺 `client_id`→`E_AUTH_NOT_CONFIGURED`，设备码写 stderr，`--json` 含 `authenticated/uuid/expiresAt/source`）；`AuthError` 接入 `ErrorPresentation`。
- **修 `Client+Boot` 离线默认值**：`auth_access_token=0`（原随机 UUID）、`user_type=legacy`（原 `mojang`）、`auth_xuid=""`、`clientid=""`；`Client+Auth.auth()` 标明 legacy 已废弃。
- `ssh air`（macOS 27 / Swift 6.4）：`swift build` 绿、`swift test` **35 单测**绿、适配器一致性 **73/73**（strict）、CLI 冒烟 `--json client --auth` → `E_AUTH_NOT_CONFIGURED`（exit 1）、`capabilities` 含 `-a/--auth`。

**状态 / 下一步**
- 所有改动**仅本地工作区**（父仓库 + `python` + `OrzMCKit`），未提交/未推送。
- **待办（`client_id` 依赖）**：维护者注册 Azure 公共客户端应用（组织目录 + 个人账号、Allow public client flows）→ 内置 `client_id` → 真实账号 E2E（需 Minecraft Java 拥有权）。
- **合入顺序**：先推子模块（其 CI 检旧 fixtures，绿）→ 再合父仓库 `auth/*` fixtures（否则父仓库 main 的 Swift CI 在子模块改动合入前会红灯）。

### 2026-10-15 — pi（`--auth` 离线优先：契约 + 纯映射一致性 + Phase A）

**背景与决策（维护者确认）**
- 维护者目前**无卡** → 全球版 Azure 免费账户走不通（强制卡验证，且不收预付卡）；**Azure for Students 可无卡**（需学生邮箱）。
- 决策：**离线优先**——先把不依赖 `client_id` 的部分做完全；待维护者办卡注册 Azure 免费账号 + 应用后，再做 `client_id` 依赖项与真实 E2E。

**做了什么（阶段 A，父仓库，可在参考适配器下自检）**
- 新增规范 [`docs/spec/auth.md`](docs/spec/auth.md)：Microsoft **设备码流程**（`consumers` 端点 → Xbox Live RPS → XSTS → `login_with_xbox` → `/minecraft/profile`）；请求/响应映射；令牌模型 + 状态目录 `auth.json`（0600）；刷新与失效；TTY/非 TTY/`--json` 行为；错误码 `E_AUTH*`；安全红线。
- `scripts/conformance/reference.py` 新增 **13 个 `auth*` 纯映射操作**（`authDeviceCodeRequest` … `authClassifyXstsError`）。
- 新增 **20 个黄金样例** `docs/spec/fixtures/auth/*`（设备码/ XBL / XSTS / MC 登录 / profile / 令牌状态 / 令牌与 XSTS 错误分类）。
- 同步：`cli-surface.md`（新增 `E_AUTH*` 错误码、`--auth` 语义、`--json` data 不含令牌）、`data-model.md` §8（离线/已认证 token 语义）、`install-update.md`（`--auth` 由【待定】改已决）、`conformance.md` / `fixtures/README.md`（加入 `auth` 域）、`docs/spec/README.md`。

**验证**
- `python3 scripts/conformance/run.py --adapter "python3 scripts/conformance/reference.py"` → **PASS=73 FAIL=0 SKIP=0**（原 53 + `auth/*` 20）。
- `python3 scripts/verify/check.py` → 登记表一致（16）+ 参考自检 73/73。

**⚠️ 合入顺序（重要）**
- `auth/*` fixtures 将使**未实现该操作的适配器**在 `--strict` 下失败；而 **`OrzMCKit` CI 会检出父仓库 main 并 `--strict`**。
- 因此：**在 Python/Swift 适配器实现并合并前，不要把 `auth/*` 合入父仓库 main**；建议先子模块分支实现适配器（其 CI 检旧 fixtures 仍绿），再合父仓库 auth fixtures。

**下一步**
- 阶段 B：Python `orzmc/core/auth.py` + `auth_store.py` + CLI `--auth` + 适配器；假 HTTP 单测。
- 阶段 C：Swift `Game/Auth/*` + 适配器 + CLI 接线 + 修 `Client+Boot` 离线默认值。
- 阶段 D（待办）：注册 Azure 应用 → 内置 `client_id` → 真实 E2E。

### 2026-10-14/15 — pi（阶段收尾 + 交接）

**本阶段总产出**
- **T2 命令面统一完成**（Python 与 Swift 两套实现全对齐 `cli-surface.md`）；
- **Phase 4 前端收敛完成**（CLI/GUI 共用 `launchClient`/`downloadClient`）；
- **Swift CLI 发行化**（release-please + `release.yml` + `install.sh`，已发 `v0.0.6`/`v0.1.0`）；
- **一致性 31→53 例**（新增 `planClientDownload`、`normalizeExit`，并修了 3 处真实分叉：Python 服务端退出码归一、参考 `verifyArtifact` 过宽、legacy natives/Maven 回退缺失）；
- Transfer 运行内重试、错误码表/schema、退出码 130 均落地。

**当前基线（交接时的可复现状态）**
- 父仓库 `main` = `4d6f73d`；`OrzMCKit` = `599616b`（`v0.1.0` + 4，含 53/53 conformance）、`app` = `3e4d92f`、`python` = `dee5be7`；`plugin` 本地检出 `develop`（`M` **预期，勿 bump**）。
- 三端 CI 均绿：父仓库 `check.py`、`OrzMCKit`（test + conformance）、`OrzPythonMC`（quality + 6 平台）。
- 一键安装/自升级实测通过（`orzmc-macos-arm64/x86_64` 已发布）。

**下一会话起点（剩余项，详见第 4 章）**
- **`--auth`**：先定 Microsoft 设备码方案 + 补 spec，再库层实现；两套 `--auth` 目前均为 stub。
- **`orzmc mcp` server**：低优先级，schema 已定稿（§8.2）。
- **环境**：`ssh air` 在本会话尾部一度锁屏不可达（`Too many authentication failures`），**已恢复**；Swift 验证可用 air 或 CI。

### 2026-10-14 — pi（一致性做彻底：34→53 例 + 修正参考/引擎）

**做了什么（覆盖矩阵 + 负向）**
- 新增 19 个样例（`34→53`）：layout osx-arm64；server-launch paper/fabric(去重)/forge；server-plan paper 不支持；server-lifecycle SIGKILL；download 阈值边界/并发夹紧；client-download legacy-windows / windows / paper-不支持 / legacy-natives；client-plan features 默认关闭 + windows；non-tty 显式值；progress 计数无总数；verify sha256 不支持。
- 新快照 `conditional-1.20.4`（features/os 门控 + 未知 token）与 `legacy-natives`。

**修正（—“彻底”暴露的真问题）**
- **参考 `verifyArtifact` 过宽**：此前用 `hashlib.new(hashType)` 接受任意算法，比两套实现（均 sha1-only）更宽 → 改为非 sha1 显式 `E_UNSUPPORTED_OP`。
- **`planClientDownload` 缺 legacy 路径**：参考与 Swift 未处理 legacy `natives` classifier、也未做无 `downloads` 的 Maven 回退（Python 已有）→ 参考与 Swift 均补齐（`OrzMCKit#18`）。

**结果**
- 参考 / Python / Swift 三适配器 **53/53**；父仓库 fixtures/reference 先合（`37c7054`）。

### 2026-10-14 — pi（一致性：`server-lifecycle`/`normalizeExit`，32→34）

**做了什么**
- 规范新增操作 `normalizeExit`（B7）：POSIX wait 状态 → `{exitCode, signaled, signal}`，被信号 N 杀死 → `128+N`。
- 父仓库：`reference.py` 实现 + fixtures `server-lifecycle/killed-by-sigterm`（-15→143）/`normal-exit`（0）；conformance.md / fixtures README / spec README 状态 32→34。
- **暴露并修复一处真实分叉**：Python `ProcessRunner.run_stream` 直接返回 `wait()` 的负值（-15），与 Swift（143）及 B7 不一致 → 新增 `normalize_exit_code` 并在 `run_stream` 归一（`OrzPythonMC#45`）。
- Swift 适配器实现 `normalizeExit`（`OrzMCKit#17`）。

**结果**
- 参考 / Python / Swift 三适配器 **53/53**；父仓库 fixtures/reference 先合（`21a81e6`），子模块 PR 绿后 bump。

### 2026-10-14 — pi（一致性：新增 `planClientDownload` 样例，31→32）

**做了什么**
- 规范新增操作 `planClientDownload`（`conformance.md` §5）：版本 JSON + 布局（+ 可选资源索引）→ 客户端下载清单 `{url,path,sha1,size}`（客户端 jar / 资源索引 / 资源对象 / 库，rules 过滤 + legacy natives）。
- 父仓库：`reference.py` 实现 + fixture `client-download/vanilla-1.20.4-macos-arm64` + 紧凑资源索引快照 `snapshots/assets/5.json`；`conformance.md`/`fixtures README`/`spec README` 状态 31→32。
- Python（`OrzPythonMC#44`）：适配器实现（`resolve_libraries` + `Mojang.assets_object_url`）。
- Swift（`OrzMCKit#15`）：`VersionPlan.AssetIndex` 补 `url/sha1/size`；新增 `AssetIndexPlan`/`DownloadPlanItem` 与 `GamePlan.planClientDownload`；适配器分发。

**结果**
- 参考 / Python / Swift 三适配器均 **32/32**；父仓库 fixtures/reference 先合（`2e6d183`），随后子模块 PR CI 绿；父仓库 bump `OrzMCKit`/`python` + `RELEASES.md`。

### 2026-10-14 — pi（发布 0.1.0 + Phase 4 前端收敛）

**发布**
- 合并 `OrzMCKit` release PR #8 → `v0.1.0`（含 `update`/`self-uninstall`/`app`/`completion`/`capabilities` 全部新命令）；`release.yml` 构建 `orzmc-macos-{arm64,x86_64}` + `SHA256SUMS`。

**Phase 4（CLI/GUI 共用下载编排）**
- `OrzSwiftKit#6`：`Downloader.download` 加可选 `onProgress`。
- `OrzMCKit#14`：引擎 `Client.downloadClient(onProgress:)`；`Launcher.download()` 改用它；`Package.resolved` 跟进 `fd88d7d`。
- `OrzMCApp#16`：`GUIClient.download()` 改用它（修了 `mutating self` 并发捕获编译错）。
- 三仓均绿并合；父仓库 bump `OrzMCKit`/`app` + `RELEASES.md`。

### 2026-10-14 — pi（遗留项：Transfer 重试 / 错误码与 schema / 退出码 130）

**做了什么**
- **Swift `Transfer` 运行内有界重试**（`OrzSwiftKit#5`，`5c05337`）：`TransferPolicy.maxAttempts`（默认 4）；单流与 Range 分块各自重试，失败保留 `.part`/`.partN` 并 `Range` 续传；校验错不重试；新增离线测试（FlakyTransport）。`OrzMCKit#13` 跟进 `Package.resolved`。
- **规范收尾**（父仓库 `cli-surface.md`）：§6.1 错误码表；§8.1 `capabilities` schema；§8.2 `orzmc mcp` schema。
- **退出码 130**：Python（`OrzPythonMC#43`）与 Swift（`OrzMCKit#12`）用户取消统一退出 130。

**结果**
- `OrzSwiftKit#5`（build-test 绿）、`OrzMCKit#12`（test+conformance 绿）、`OrzPythonMC#43`（quality+6 平台绿）均已合；`OrzMCKit#13` 待合。

**评估后暂缓（非阻塞，已记入第 4 章）**
- Phase 4 `downloadClient` 收敛（需进度抽象 + 改 app）；一致性 `planClientDownload`（需先把客户端下载清单抽成纯计划）；Python `--auth`（两套均为 stub，需 Microsoft 认证方案）；`orzmc mcp` server（低优先级计划）。

### 2026-10-14 — pi（T2 收尾：Python `plugin` / `app`）

**做了什么**
- `OrzPythonMC` 新增 `orzmc plugin`（#42）：`core/hangar.py` Hangar v1 适配器 + `services/plugins.py` `PluginService`；CLI `--search/--list/--output/--version/--count`。
- 新增 `orzmc app`（#42）：`services/app.py` `AppInstaller`（macOS 跨面 GUI：resolve/install/open/uninstall/status；非 macOS 显式拒绝；App Store 渠道上架前 E_UNSUPPORTED）。
- 公共 API 导出 + `--json` 信封；离线测试（FakeHttp / fake process / 沙箱 HOME）。

**结果 / 产出**
- `OrzPythonMC` PR #42 已合（`11a423a7cceb`，`quality` + 6 平台 `test` + `pr-title` 全绿）；父仓库 bump + `RELEASES.md` 刷新；`cli-surface.md` §2/§10 同步。
- 本地门禁：ruff / mypy / pytest（349 passed）全绿。
- **T2「统一 CLI 命令面」完成：两套实现的命令面已全部对齐规范。**

**尾部**
- 合并 `OrzMCKit` #10/#11 后 release-please 持续维护 0.1.0 的 release PR（#8）。
- 剩余非阻塞：Python `--auth`（需库支持）、`capabilities`/`mcp` schema、Phase 4 前端收敛、一致性样例扩展。

### 2026-10-14 — pi（T2 Step 2：Swift `app` 命令 - 跨面 GUI）

**做了什么**
- `OrzMCKit` 新增 `orzmc app install|open|uninstall|status`（#11）：从 `OrzMCApp` 的 GitHub Release 取最新/指定 `.zip`（多产物按名取最新），解压 `.app` 到 `~/Applications`；status 读 `Info.plist` 版本；App Store 渠道上架前显式 `E_UNSUPPORTED`。
- **Swift CLI 命令面至此全部对齐 `cli-surface.md`。**

**结果 / 产出**
- `OrzMCKit` PR #11 已合（`33504ac6bc52`，CI 绿）；父仓库 bump + `RELEASES.md` 刷新；`cli-surface.md` §10 同步。
- 验证（`ssh air` 沙箱 HOME）：`app status`/`open`（未安装→`E_NOT_FOUND`）/`--channel appstore`（`E_UNSUPPORTED`）；`app install --yes`（真实 `OrzMCApp 0.1.2`）→ `~/Applications/OrzMC.app`；status 报 0.1.2；`app uninstall` 成功。

**下一步**
- Python：`plugin`（Hangar）与 `app`（跨面 GUI）；这是 T2 最后一项。

### 2026-10-14 — pi（T2 Step 2：Swift `update` / `self-uninstall`）

**做了什么**
- `OrzMCKit` 新增发行产品生命周期（#10）：`InstallManifest`（`install.conf` 读写）、`orzmc update`（GitHub releases 解析 + 版本比较 + 下载/本地文件 + Mach-O magic 校验 + 分离助手延迟替换）、`orzmc self-uninstall`（还原 PATH / 删补全与记录 / 删二进制 / 可选删 game root）。
- `scripts/install.sh` 补齐 `version`/`path_file`/`path_line`/`completion_file` 记录。新增单测（install.conf、版本比较）。

**结果 / 产出**
- `OrzMCKit` PR #10 已合（`586cc605ba8c`，CI 绿）；父仓库 bump + `RELEASES.md` 刷新；`cli-surface.md` §10 同步。
- 验证（`ssh air` 沙箱）：`update --check`（真实 GitHub）；完整 `update --force -v 0.0.6`（下载→校验→分离助手替换成功）；本地文件 magic 不符→`E_VERIFY`；`self-uninstall --yes --force --remove-root` 全清理且 rc 其余行保留。

**下一步**
- Swift `app`（跨面安装/打开/卸载）——已写好待接线；Python `plugin`（Hangar）/`app`。

### 2026-10-14 — pi（T2 Step 2：Swift `capabilities` + `fabric` 隐藏别名）

**做了什么**
- `OrzMCKit` 新增 `orzmc capabilities`（#9）：反射各命令 `Signature()` 生成命令/选项清单（`AsyncCommand` 扩展 + `Mirror`，与签名自动同步）；`--json` 信封含 `tool/version/exitCodes/envelope/commands`。
- `fabric` 改为隐藏别名（自定义 `CommandGroup.run` 拦截）：仍可用，但不列入 `commands` → 不出现在帮助/补全/capabilities。
- 单测：命令面、fabric 隐藏、capabilities 反射。

**结果 / 产出**
- `OrzMCKit` PR #9 已合（`c4ec57f94fb4`，CI 绿）；父仓库 bump + `RELEASES.md` 刷新；`cli-surface.md` §10 同步。
- 验证：`ssh air` build/test(22) 绿；`--help` 不列 fabric、列出 capabilities；capabilities human/json 正确；`orzmc fabric` 仍可用。

**下一步**
- Swift：`update`/`self-uninstall`/`app`（按 `install-update.md`，复用 `install.conf`）。Python：`plugin`/`app`。

### 2026-10-14 — pi（T2 Step 2：Swift `completion` 命令）

**做了什么**
- `OrzMCKit` 新增 `orzmc completion`（#7）：`completion bash|zsh` 用 ConsoleKit 原生生成器打印脚本；`completion install` 按 `$SHELL` 落盘（bash：`~/.local/share/bash-completion/completions/orzmc` + `.bashrc`；zsh：`~/.zsh/completions/_orzmc` + `.zshrc` `fpath`），均幂等；`fish`/`powershell` 显式 `E_UNSUPPORTED`。
- `--json` 信封（script/install）；路径改用 `$HOME`（可被沙箱覆盖；`NSHomeDirectory()` 在 macOS 会忽略 `$HOME`）。新增单测（命令面 + 原生 shell 支持）。
- 父仓库同步 `cli-surface.md` §2/§9/§10。

**结果 / 产出**
- `OrzMCKit` PR #7 已合（`c2759964294c`，CI 绿；conformance 31/31）；父仓库 bump + `RELEASES.md` 刷新。
- 验证：`ssh air` `swift build`/`swift test`(20)/conformance 31/31 绿；冒烟：bash/zsh 脚本、`--json` 信封、fish 报 `E_UNSUPPORTED`、沙箱 HOME 下 install 落盘正确。
- release-please 开出了 release PR #8（`chore(main): release 0.1.0`，等待维护者合并，合并后自动发 `v0.1.0`）。

**下一步**
- Swift：`capabilities` + `fabric` 隐藏别名；`update`/`self-uninstall`/`app`。Python：`plugin`（Hangar）/`app`。

### 2026-10-14 — pi（D13 续：首次 Swift release `v0.0.6` 实测通过）

**结果**
- 合并 `OrzMCKit#6` 后 `release-please.yml` 在 main push 触发 → 依 manifest/代码版本 `0.0.6` 建 `v0.0.6` tag → 接力 `release.yml` → macos-15(arm64, 14m45s) / macos-15-intel(x86_64, 34m55s) 构建 + 校验 → 发布 GitHub Release `v0.0.6`，资产：`orzmc-macos-arm64`、`orzmc-macos-x86_64`、`SHA256SUMS`。**发版链路端到端验证通过。**
- 说明：这是 merge 触发的**引导性发布**（OrzMCKit 旧 tag 无 `v` 前缀，`v0.0.6` 成为新发布线起点）；后续 release-please 从 0.0.6 起开下一个 release PR。
- 另记：OrzMCKit main 的 CI `test` 曾因 SwiftPM 缓存里 SwiftLint artifact「already exists」瞬时失败（conformance 绿），属 runner 缓存 flake，非代码问题；必要时可在 CI 加 `rm -rf ~/Library/Caches/org.swift.swiftpm/artifacts` 缓解。

### 2026-10-14 — pi（D13：Swift `orzmc` CLI 发行化 - 发版链路 + 一键安装）

**背景**
- 维护者拍板：**Swift `orzmc` CLI 是要发行的产品**（→ D13）。上一步的「不发行则不实现 `update/self-uninstall/app`」待决策解除。

**做了什么**
- `OrzMCKit` 新增发版基建（#6）：`release-please` 配置/工作流 + `release.yml`（tag `v*` → 护栏校验 tag==`OrzMCVersion.current` 且落在 `main` → `macos-15`/`macos-15-intel` 构建 `orzmc-macos-arm64`/`x86_64` → 断言架构+自报版本 → 全部到位后才发布 Release + `SHA256SUMS`）。
- `OrzMCVersion` 加 `x-release-please-version` 标记；新增 `CHANGELOG.md`。
- `scripts/install.sh`：macOS 用户级一键安装（SHA256 + Mach-O magic 校验 → `~/.local/bin` → PATH → 补全 → `install.conf`），免 sudo，契约对齐 `install-update.md`。README 补齐。
- 父仓库：新增决策 **D13**；更新 `install-update.md` 现状；HANDOFF。

**结果 / 产出**
- `OrzMCKit` PR #6 已合（`d5084868526e`，CI `test` + `conformance`(31/31) 绿）；父仓库 bump + `RELEASES.md` 刷新。
- 验证：`ssh air` `swift build`/`swift test` 绿；`swift build -c release --product orzmc` → `orzmc 0.0.6`（Mach-O arm64）；YAML/JSON 校验通过；`sh -n install.sh` 通过。

**待确认**
- **版本身份**：Swift CLI 暂用 OrzMCKit 版本线（`0.0.6`）；是否与 Python `orzmc`（`2.4.x`）统一为同一产品版本，需维护者定。

**下一步**
- Swift：`completion`/`capabilities` + `fabric` 隐藏别名；然后 `update`/`self-uninstall`/`app`（按 `install-update.md` 契约，与 `install.sh`/`install.conf` 一致）。

### 2026-10-14 — pi（调研：ConsoleKit 维护现状 + 双 CLI 冗余评估）

**做了什么（只读调研，未改代码）**
- 核实 **ConsoleKit 未停止维护**：`vapor/console-kit` 最近提交 `5acfda6`（2026-08-14）、发布 `5.0.0-beta.2` 与 `4.16.1`（2026-08-11）；未归档、4 个 open issue、583★。**Vapor main 仍依赖 `console-kit from 5.0.0-beta`**（product `ConsoleLogger`）。
- 澄清误解：`OrzMCKit` 锁定 `4.15.2`（2025-01-13）是因为它是 **`OrzSwiftKit`/`JokerKits` 的传递依赖**（`from: 4.15.2`），且未 `swift package update`；`Game`/`OrzMC` 直接 `import ConsoleKit` 但未在 `Package.swift` 声明。
- 替代方案：参数解析主流是 `apple/swift-argument-parser`（3790★、活跃、bash/zsh/fish 补全）；终端 UI/颜色/进度无单一标准（`Rainbow`/`Chalk`、`swift-tools-support-core`）。Vapor 社区并未替换 ConsoleKit。
- 双 CLI 评估：Swift CLI 无发行、app 只用引擎；Python CLI 是唯一发行的跨平台 CLI（PyInstaller 6 平台 + 自升级）。命令面/编排逻辑重复，由一致性套件（31 例）约束；已见分叉成本（Transfer 重试、缓存 TTL、`.exe`）。

**结论 / 建议**
- 无需替换 ConsoleKit；可选把 `OrzSwiftKit` 的 console-kit 升到 `4.16.1`，并让 `OrzMCKit` **显式声明** console-kit 依赖（消除传递依赖脆弱性）。
- 双 CLI 屬「跨语言跨平台 + GUI 共用引擎」的固有成本，**部分冗余可接受**；但命令面应单一化 + 用 conformance 守住行为；**优先决策 Swift CLI 是否作为发行物**（决定 T2 Step 2 是否值得做）。

**下一步**
- 等维护者对上述两个待决策项拍板；不做未授权的发版/架构变更。

### 2026-10-14 — pi（T2 续：Swift version + 全局选项 + --json 信封）

**做了什么**
- `OrzMCKit`：新增 `Game/OrzMCVersion.swift`（工具版本单一事实源，取最近发布 tag `0.0.6`）与 `orzmc version` 命令；`OrzMC.main` 在 ConsoleKit 之上**预解析 argv**，支持全局 `--version`（工具，与子命令 `-v` 游戏版本靠位置区分）/`--verbose`/`--root-dir`/`--json`。
- **`--json` 信封**（规范 §6.1）：`{ok,command,data,error}`；新增 `StderrConsole`（`--json` 下日志/进度转 stderr，stdout 只留信封）与 `CLIError`（错误经 main 出信封、退出码 1）；覆盖 client/server/plugin/fabric/list/remove/backup/version。
- `--root-dir` 贯通引擎：`ClientInfo.rootDir` / `ServerInfo.rootDir`（带默认值，向后兼容）；client/server/list/remove/backup 一致。
- 无子命令打印帮助并**退出 0**（修正此前 1）；服务端 `--type` 缺省改为 `vanilla`（规范 §4.2）；服务端不支持的类型由“静默回退 paper”改为显式 `E_UNSUPPORTED`。
- 单测 +14（GlobalOptions.parse / 版本格式）。

**结果 / 产出**
- `OrzMCKit` PR #5 已合（`31c706daf321`，CI `test` + `conformance`（31/31）绿）；父仓库 bump + `RELEASES.md` 刷新；`docs/spec/cli-surface.md` 状态同步。
- 验证：`ssh air`（macOS 27 / Swift 6.4）`swift build`/`swift test` 绿；CLI 冒烟（`--version`、`--json` 各命令、错误信封/退出码、无子命令退出 0）。

**踩坑 / 决定**
- `AsyncCommand` 是 `Sendable`，`GlobalOptions` 用值类型；`Console` 代理需实现 `userInfo`/`supportsANSICommands`。
- `Launcher.start()` 是 `Client` 协议要求（void，app 依赖）→ 新增 `run() -> Int` 供 CLI 取退出码，不动协议。
- 版本源决定：沿用 Python 的「源码常量即版本源」；`OrzMCKit` 尚无 release-please，后续可加（本会话不替维护者做发版决定）。

**下一步**
- Swift 补 `update`/`self-uninstall`/`app`/`completion` 与 `fabric` 隐藏别名；Python `plugin`（Hangar）/`app`。

### 2026-10-14 — pi（T2 续：Swift backup 命令）

**做了什么**
- `OrzMCKit` 引擎新增 `GamePlan.backupWorld`（zip 世界到 `backup/worlds/`，对齐 Python `Backup.backup_world`）与 `GameError.worldNotFound`；CLI 新增 `orzmc backup [-v] [-t] [--root-dir]`（版本缺省自动推断）；离线单测 2 例。
- 踩坑：新增 `GameError` case 后，`ErrorPresentation` 的 `switch` 必须补分支（switch 穷尽）。

**结果 / 产出**
- `OrzMCKit` PR #4 已合（`70f3751c0b1e`，CI test + conformance 绿）；父仓库 bump `0454887`；`RELEASES.md` 刷新。

**下一步**
- Swift 补 `version`/`update`/`self-uninstall`/`app`/`completion` 与全局 `--root-dir`/`--json`；Python `plugin`/`app`。

### 2026-10-14 — pi（T2 续：Swift list/remove 命令）

**做了什么**
- `OrzMCKit` 引擎新增 `GamePlan.installedVersions` / `removeInstalled`（扫描 / 清理 `<root>/versions/<v>/{client,server/<type>}`）；CLI 新增 `orzmc list`（含 `--root-dir`）与 `orzmc remove -v <ver> [--server -t <type>]`；引擎离线单测 4 例。
- 踩坑：ConsoleKit `@Option` 属性必须可空（`Value?`），非可选会编译失败。

**结果 / 产出**
- `OrzMCKit` PR #3 已合（`b9398b1ea5ec`，CI test + conformance 绿）；父仓库 bump `ed107d1`；`RELEASES.md` 刷新。

**下一步**
- Swift 补 `version`/`backup`/`update`/`self-uninstall`/`app`/`completion` 与全局 `--root-dir`/`--json`（可在 `ssh air` 上编译）。

### 2026-10-14 — pi（T2 续：Python capabilities 命令）

**做了什么**
- Python CLI 新增 `capabilities`（规范 §8/D9）：内省 Typer 应用输出命令 / 选项 / 退出码 / 信封 schema；`--json` 下走信封。
- 顺带把 `list` 命令函数改名 `list_command`（原名遮蔽内建 `list`，影响注解解析）。

**结果 / 产出**
- `OrzPythonMC` PR #41 已合（`b6886fbb8c95`，6 平台 CI + quality 绿）；父仓库 bump `a83996e`；`RELEASES.md` 刷新。

**下一步**
- Swift 补命令（在 `ssh air` 上编译验证）；Python `plugin`/`app`。

### 2026-10-14 — pi（T2 续：Python completion 命令）

**做了什么**
- Python CLI 对齐规范 §9：开启 typer 补全（`add_completion=True`，补全回调生效）；新增 `orzmc completion <bash|zsh|fish|powershell|pwsh>` 打印脚本、`orzmc completion install` 安装；`--json` 下输出信封。新增 3 个测试。
- 更新 `docs/spec/cli-surface.md` 状态（`completion` Python ✅、§9/§10）。

**结果 / 产出**
- `OrzPythonMC` PR #40 已合（`051857ad9b75`，6 平台 CI + quality 绿）；父仓库 bump `aabe4e0`；`RELEASES.md` 刷新。

**下一步**
- Python `plugin`（Hangar）/`capabilities`/`app`；Swift 补命令（可在 `ssh air` 上编译）。

### 2026-10-14 — pi（T2 续：Python 全局 --json 信封）

**做了什么**
- Python CLI 新增全局 `--json`（D9 AI 调用核心）：成功/失败各输出恰好一个 JSON 对象 `{ok,command,data,error}`（失败时 `error={code,message}` 且退出码 1）；`--json` 下进度/日志改走 stderr，stdout 只留信封；覆盖 `version`/`list`/`client`/`server`/`remove`/`update`/`backup`/`self-uninstall`；错误码 `E_USAGE`/`E_UNSUPPORTED`/`E_RUNTIME`。
- 人类可读模式输出保持不变。新增 3 个信封单测。

**结果 / 产出**
- `OrzPythonMC` PR #39 已合（`c49b1d2c28be`，6 平台 CI + quality 绿）；父仓库 bump `205a3bb`；`RELEASES.md` 刷新。

**下一步**
- Python 其余命令（`completion`/`plugin`/`capabilities`/`app`）；Swift 补命令（可在 `ssh air` 上编译）。

### 2026-10-14 — pi（T2 续：Python 全局选项收敛）

**做了什么**
- Python CLI 对齐规范：全局 `--version`（工具版本；子命令 `-v/--version` 仍是游戏版本）；全局 `--root-dir`（子命令缺省回退）；内存选项规范名 `--min-mem/--max-mem`（旧名 `--minmem/--maxmem` 保留别名）。
- 探得 **`ssh air`**：macOS 27 / Swift 6.4 / Xcode 27（arm64）——后续 Swift 侧可在 air 上本地编译验证。

**结果 / 产出**
- `OrzPythonMC` PR #38 已合（`b4c8dabcbee5`，6 平台 CI + quality 绿）；父仓库 bump `fd6da4c`；`RELEASES.md` 刷新。

**下一步**
- Python `--json` 信封（D9）；Swift 补命令（可在 air 上编译）。

### 2026-10-14 — pi（T2 起步：Swift CLI 选项收敛）

**做了什么**
- 对齐 `docs/spec/cli-surface.md` 收敛 Swift CLI：`--debug→--verbose`、`--ms→--min-mem(-m)`、`--mx→--max-mem(-x)`、`--gui→--nogui`（反向，默认 false=GUI 与 Python/spec 一致）、`--force_upgrade→--force-upgrade`、`--jar-opts→--server-args`。
- 去掉 `CommandGroup.defaultCommand`：无子命令时打印帮助（不再隐式跑 `client`）。

**结果 / 产出**
- `OrzMCKit` PR #2 已合（`e075e1a`，CI test + conformance 绿）；父仓库 bump `760608e`；`RELEASES.md` 刷新。

**下一步**
- Swift 补 `version/list/remove/backup` 等命令与全局 `--root-dir/--json`；Python 补全局 `--version/--json` 与 `plugin/completion` 等。

### 2026-10-14 — pi（T1 完成：Swift 真实网络冒烟）

**做了什么**
- `OrzSwiftKit/TransferKit` 新增 `TransferNetworkSmokeTests`：用**内容寻址**的 Mojang 对象（URL 里的 sha1 即内容哈希）验证真实下载 + 哈希，覆盖单流与 2 路 `Range`；默认跳过（`ORZMC_NETWORK_SMOKE=1` 启用），常规 `swift test` 保持离线。
- CI 新增 `network-smoke` job（`workflow_dispatch` 手动触发）。

**结果 / 产出**
- `OrzGeeker/OrzSwiftKit` PR #4 已合（`eca6beb`）；手动触发 CI → `build-test` + `network-smoke` 均绿（`singleStream…` / `ranged…` 真实通过）。
- **T1 全部完成**：macOS ✅ + Windows ✅ + Swift 冒烟 ✅。

**新发现（待办）**
- Swift `Transfer` 在 body 中途断连时**无运行内重试**（仅靠持久化 `.part` 重跑续传），与 Python 及 spec B2 不一致；GUI 无手动重跑，建议补。

### 2026-10-14 — pi（T1 收尾：Windows 真机 E2E）

**做了什么**
- Windows 真机（`ssh win`，收敛根 `E:\orzmc-verify\`）跑通 Python `orzmc` 服务端全链路：
  clone `OrzPythonMC`（`50ef96c`，含续传修复）→ `uv sync` → 部署 `1.20.4 vanilla` → `Done (` → `stop` → **退出码 0**、无残留 java、root 236MB。
- 新增可复用脚本 [`scripts/win/e2e-server.ps1`](scripts/win/e2e-server.ps1)（截获 stdout、等 `Done (` 后写 stdin `stop`）。
- 踩坑：Windows 上 `uv` 默认托管 Python 目录残留不可信装入点（`os error 448`），须 `UV_PYTHON_INSTALL_DIR` 指向干净目录（已记入 §2.4）。

**结果 / 产出**
- T1 macOS + Windows 两端实跑均 ✅；父仓库脚本 + HANDOFF。

**下一步**
- Swift 冒烟（OrzMCKit CI 真实小文件下载 + 哈希）。

### 2026-10-14 — pi（T1 端到端实跑 + 修复下载中断）

**做了什么**
- macOS 真机跑通 Python `orzmc` 服务端全链路（临时 root `/tmp/orzmc-e2e`，不动 `~/minecraft`）：
  真实下载 Java 17 + 服务端 → 世界生成 → `Done (12.578s)!` → 发 `stop` 优雅停止 → **退出码 0**、无残留 java。
- 首两次随机失败于 `Connection broken: IncompleteRead`（流式下载中途断连），定位为 **urllib3 Retry 不覆盖 body 读取**（只管建连）。
- 修复（`OrzPythonMC#36` → `50ef96c`）：`HttpClient.stream_range`/`fetch_range` 断连后按已落盘字节 `Range` 续传（最多 4 次），服务器忽略 Range 回 200 则整份重来；`download()` 与分块统一走该原语；新增续传/忽略Range/重试预算/loopback 截断测试。

**结果 / 产出**
- 父仓库 bump `python` → `50ef96c`（`eaf55e9`）；规范 B2 增「中断续传」契约；`RELEASES.md` 刷新。
- Python 门禁全绿（ruff/format/mypy/pytest + 6 平台 CI）；真实网络 49MB 两路径哈希一致。

**下一步**
- Windows 真机 E2E；Swift 冒烟（见第 4 章 T1）。

### 2026-10-14 — pi（阶段性收尾：产品统一化达成）

**总览**
- Phase 0/1/2/3 完成 + Phase 5 治理上线（`RELEASES.md` + `scripts/verify/check.py` + 父仓库 CI）+ Phase 4 起步（引擎共用 `Client.launchClient()`）。
- 一致性套件 **31 例**，参考 / Python / Swift 三适配器全绿（`OrzMCKit` CI 内跑）。
- Swift 侧 **B1–B11 全部实现**；`OrzSwiftKit` 收敛出 `CacheKit`/`RuntimeKit`/`TransferKit` + `ProcessRunner`，**移除 Alamofire**。
- 当前基线：父仓库 `cef9bdb`、`OrzMCKit=9bffcbc`、`app=4a4c6b4`、`python=55a4d62`、`plugin` 记录 `5eadd6e`(main)/检出 develop。

**下一步**：见第 4 章（增量、非阻塞）。

### 2026-10-14 — pi（Phase 4 前端收敛：共用 launchClient）

**做了什么**
- 引擎新增 `Client.launchClient()`：解析启动参数 → 托管 JRE（B5）→ 受管进程（B7），返回不等待。
- CLI `Launcher` 与 app `GUIClient` 均改用该共用流程（各自处理前台等待 / 后台运行）。
- 刷新 `RELEASES.md`（bump 后指针）。

**结果 / 产出**
- `OrzMCKit` `9bffcbc`（test + conformance 29/29 绿）；`app` `4a4c6b4`（构建 CI 绿）；父仓库 bump。

**下一步**
- 更多共用编排（如 `downloadClient`）可选。

### 2026-10-14 — pi（一致性扩到 31 例）

**做了什么**
- 新增 `layout/fabric-1.20.4-custom-root`（自定义 root + fabric 服务端 jar 名）、`layout/forge-1.20.4-windows`
  （forge jar 名 + `java.exe`）。
- 三适配器均无需改（已支持类型/自定义 root）；参考/Python 本地 31/31；Swift CI 31/31。

**结果 / 产出**
- 父仓库 `336016d`（fixtures + 计数 31）。

### 2026-10-14 — pi（产品伞治理：发版组合 + 父仓库 CI）

**做了什么**
- 新增 [`RELEASES.md`](RELEASES.md)：记录 `main` 基准组合的各子模块**记录指针**（gitlink，不受本地检出分支影响），
  由 `scripts/release/composition.py` 生成。
- 新增 `scripts/verify/check.py`：① `AGENTS.md` 登记表 与 `.gitmodules` 路径一致性；② 一致性参考自检（离线）；
  `--remote` 追加子模块指针远端存在性检查。
- 新增父仓库 CI（`.github/workflows/ci.yml`）跑该脚本。
- `AGENTS.md` §7/§8、`docs/README.md` 同步。

**结果 / 产出**
- 本地：`check.py` → 登记表一致（16）+ `PASS=29`。

**下一步**
- Phase 4 前端收敛（可选）：CLI/GUI 共用 `Game` 公共 API。

### 2026-10-14 — pi（B2 硬化：传输接缝 + 离线测试）

**做了什么**
- `TransferKit` 抽出可注入的 `TransferTransport`（生产 `URLSession`，测试假实现）；`Transfer` 走 transport。
- `TransferPolicy` 支持实例化配置（阈值/路数/上限），静态默认保留（一致性适配器不变）。
- 离线测试：单流、**4 路拼装**、**200 回退**、**断点续传**（预置 `.part` + 断言 `Range: bytes=4-`）、**哈希不符拒绝**。

**结果 / 产出**
- `OrzSwiftKit` `a7f9716`（CI 绿）；`OrzMCKit` `f0267a5`（跟进，CI 绿）；父仓库 bump `aee11b9`。

**说明**
- 未用 `URLProtocol`（download task 不保证走它），改用显式 `TransferTransport` 接缝，测试更稳定。

### 2026-10-14 — pi（退役 GameDir）

**做了什么**
- 新增 `GamePlan+Paths`：`clientDir/serverDir/serverPluginDir/…` 等便捷 API（委托 `GamePlan.layout`）。
- 迁移 `OrzMCKit`（Client/Server/Launcher/CLI）与 `app`（GameList/BasicInfo/GUIClient/GUIServer/ServerPluginDownloadService）调用点；
  `launchServer` 的 `workDirectory` 由 `GameDir` 改为 `String`。
- 删除 `GameDir.swift`；`GameType`/`GameError` 拆到独立文件保留。

**结果 / 产出**
- `OrzMCKit` `8d98ec0`（test + conformance 29/29 绿）；`app` `23e64e0`（构建 CI 绿）；父仓库 bump `19075f9`。

**踩坑**
- `GameType` 原在 `GameDir.swift` 里，删除时一并被删 → 拆出 `GameType.swift`。
- 若干 `.dirPath` 残留（迁移后为 `String`）由 app CI 拓出并修。

**下一步**
- 已做 B2 硬化（见下一条会话）。

### 2026-10-14 — pi（planServerLaunch + 服务端参数统一）

**做了什么**
- 新增一致性操作 `planServerLaunch` + 两个 fixture（`server-launch/`）：参数顺序与回退规则。
- **跨实现统一**服务端启动参数（以 Python `_build_server_command` 为准）：
  `java <userJvm…> -Xms<min> -Xmx<max> -jar <jar> [nogui] <userServerArgs…> [--forceUpgrade]`。
- Swift：新增 `ServerLaunchPlan`/`ServerLaunchOptions` + `GamePlan.planServerLaunch`；`Server+Launch` 改用该计划
  （去掉 `-server`、`--pidFile`、`--demo`/`--help` 位置调整、`--nogui` → 裸 `nogui`）。
- 三适配器实现（参考/Swift/Python）。

**结果 / 产出**
- 套件 **29/29**（参考本地自检；Python 本地 + 门禁绿）；`OrzMCKit` `52abfdc`（CI）；`OrzPythonMC#34` 已合（`55a4d62`）。

**下一步**
- 全量退役 `GameDir`（调用点 + app 迁到 `GamePlan`）。

### 2026-10-14 — pi（B9 非 TTY）

**做了什么**
- CLI 新增 `TerminalEnvironment.isInteractive`（`isatty(stdin)`）。
- `chooseGameVersion`：显式 `--version` 命中即用、找不到直接报错（不再回退交互）；非 TTY 用**最新 release**。
- 客户端：非 TTY 用户名默认 `guest`；非 TTY 不做交互式正版授权。

**结果 / 产出**
- `OrzMCKit` `1bc336d`（test + conformance 27/27 绿）；父仓库 bump `22e2bec`。

**踩坑**
- 自定义 `Terminal` 与 ConsoleKit 同名类型冲突 → 改名 `TerminalEnvironment`。

**下一步**
- `planServerLaunch` 样例；全量退役 `GameDir`。

### 2026-10-14 — pi（B7 接线：引擎生命周期）

**做了什么**
- `Server` 协议 / `launchServer` / `Vanilla`/`Paper` 的 `start()` 返回 `ManagedProcess`（不再用 `Shell.run` 的裸 `Process`）。
- CLI `ServerCommand` 改为**前台等待**服务端退出并打印归一化退出码；`--kill-all` 保留。
- app `GUIServer` 同步返回 `ManagedProcess`（`GUI` 仍以 PID 记录运行实例）。

**结果 / 产出**
- `OrzMCKit` `3bba300`（test + conformance 27/27 绿）；`app` `d4362bc`（构建 CI 绿）；父仓库 bump `8b29013`。

**下一步**
- B9 非 TTY 默认值；`planServerLaunch` 样例；全量退役 `GameDir`。

### 2026-10-14 — pi（B7 进程原语）

**做了什么**
- `OrzSwiftKit/JokerKits` 新增 `ProcessRunner` / `ManagedProcess`（B7 原语）：
  - 优雅停止（向 stdin 写 `stop`）→ 超时升级 `SIGTERM` → 再升级 `SIGKILL`；
  - 退出码归一（被杀信号 → `128 + signal`），取消退出码常量 `130`；
  - `onLine` 透传 stdout/stderr；`Policy` 可配 graceful/terminate 超时。
- 测试：正常退出码、优雅 stop 退出、忽略 TERM 时升级到 KILL（`128+9`）。

**结果 / 产出**
- `OrzSwiftKit` `10b4095`（CI 绿）；`OrzMCKit` `46b5499`（跟进依赖）；父仓库 bump `31374d6`。

**下一步**
- 把引擎 `Server+Launch` 与 CLI/app 的生命周期切到 `ManagedProcess`（会改 `Server.start` 返回类型，需同批改 app）。
- B9 非 TTY；`planServerLaunch` 样例。

### 2026-10-13 — pi（server-plan 一致性样例）

**做了什么**
- 新增一致性操作 `planServerDeploy` + fixture `server-plan/vanilla-1.20.4`（核心制品/落点/jar 名/eula）。
- 快照 `1.20.4.json` 补 `downloads.server`。
- 三适配器实现：参考 `reference.py`、Swift（`GamePlan.planServerDeploy` + `ServerDeployPlan`）、Python（`adapter.py`）。

**结果 / 产出**
- 套件 **27/27**（参考本地自检绿；Python 本地 27/27）；Swift `507d467`（CI conformance）；`OrzPythonMC#33` 已合（`9a96ac9`）。

**下一步**
- B7 `server-lifecycle`（优雅退出/退出码）与 `planServerLaunch`；B9 非 TTY 默认值。

### 2026-10-13 — pi（B8：结构化进度）

**做了什么**
- `TransferKit` 新增 `TransferProgress { kind: count|bytes, description?, total?, current }`（含 `fraction` 归一）。
- 单流用 `URLSessionDownloadDelegate.didWriteData` 报**字节**；批量报**计数**；4 路分块按块聚合字节。
- `JokerKits.Downloader` 进度回调改用 `TransferProgress`（`progressBar` 驱动不变，app 无感）。

**结果 / 产出**
- `OrzSwiftKit` `d6f4769`（CI 绿）；`OrzMCKit` `ab61ac6`（test + conformance 26/26 绿）；`app` 构建 CI 绿；父仓库 bump `ca4cf60`。

**下一步**
- B7/B9（服务端生命周期/非 TTY）样例与对齐；全量退役 `GameDir`；补 `server-plan`/`server-lifecycle` 样例。

### 2026-10-13 — pi（断点续传）

**做了什么**
- `TransferKit` 新增**断点续传**：进度持久化到与目标同级的 `.part` / `.partN`；
  - 单流：已有 `.part` 时用 `Range: bytes=<have>-` 续传；服务器返回 200（忽略 Range）则从零重下；
  - 4 路分块：每块独立 `.partN` 续传，全部就绪后按序拼接；
  - 完成后校验哈希再落盘，失败清理进度。

**结果 / 产出**
- `OrzSwiftKit` `d017efe`（CI 绿）；`OrzMCKit` `8dc6bb9`（test + conformance 26/26 绿）；`app` 构建 CI 绿；父仓库 bump `add4a15`。

**备注**
- 续传为运行时行为，目前无离线单测（`URLSession` download task 难以用 `URLProtocol` 模拟）；靠 CI 构建 + 代码审阅覆盖。

**下一步**
- B8 进度结构；B7/B9 样例与对齐；全量退役 `GameDir`。

### 2026-10-13 — pi（网络层统一：TransferKit，移除 Alamofire）

**做了什么**
- `OrzSwiftKit` 新增 **`TransferKit`**（B2）：`TransferPolicy` + `DownloadItem` + `Transfer`
  （**URLSession** 单一实现；哈希命中跳过；≥8MB **4 路 `Range` 并行**，服务器返回 200 时回退单流；
  连接池 ≥ 并发；`.part` 原子写 + 下载后校验）。
- `JokerKits.Downloader` 基于 `TransferKit` 重写（保留 `DownloadItemInfo` 公开 API）；`OracleJDK` 下载改走 `TransferKit`。
- **移除 Alamofire**（Swift 侧不再有三方 HTTP 客户端）；`TransferPolicy` 从 `JokerKits` 迁到 `TransferKit`。
- `OrzMCKit`：`ConformanceAdapter` 改用 `TransferKit.TransferPolicy`；`FabricCommand` 安装器下载改走 `TransferKit`。

**结果 / 产出**
- `OrzSwiftKit` `b642b55`（CI 绿）；`OrzMCKit` `a700ebd`（test + conformance 26/26 绿）；`app` 构建 CI 绿；父仓库 bump `3bc436a`。

**下一步**
- B8 进度结构；B7/B9 样例与对齐；全量退役 `GameDir`。

### 2026-10-13 — pi（运行时：Java 托管 JRE 接入，B5）

**做了什么**
- `OrzMCKit` 新增 `JavaRuntime`：托管路径 `java/<major>/bin/java` + `ensure(...)`
  （经 `RuntimeKit` 下载安装，并**拍平**运行时根到 `java/<major>`）。
- 服务端（Vanilla/Paper）、客户端（`Launcher`）、CLI、GUI 启动均改用托管 JRE；移除 `GameUtils.javaPath()`（`which java`）。
- app 同步适配（`GUIClient`/`GUIServer`：`GameType` 四值 switch、`launchServer` 传 `javaExecutable`）。

**结果 / 产出**
- `OrzMCKit` `db70ad8`（CI：`test` + `conformance` 26/26 绿）；`app` `2de27e7`（构建 CI 绿，19m）；父仓库 bump `87887dd`。

**踩坑（HEAD 制暴露的真实问题）**
- `Package.resolved` 需 `swift package update` 跟进分支；app 侧需删锁文件重解析（CI 已处理）。
- OpenAPI 生成的 `javaVersion.majorVersion` 是 **`Double`**（非 Int64）。
- app 重解析暴露外部缺陷：`OrzGeeker/OrzAppUpdater` 声明 macOS 11 却依赖需 12 的 Sparkle
  → 已改为 **macOS 13** 并发 tag **0.0.3**（app 的 `upToNextMajor 0.0.2` 可解析到）。
- `GameType` 扩展在 app 内也有穷尽 `switch`（`GUIServer`），已补 `.fabric/.forge` 分支。

**下一步**
- B2：`Downloader` 接入 `TransferPolicy`（4 路 Range）；B8 进度结构；B7/B9 样例与对齐。

### 2026-10-13 — pi（Phase 3：GameDir 兼容层切规范布局）

**背景**
- `app` 在 6+ 处重度依赖 `GameDir`，而 app **无 PR CI**、本地又无 Xcode → 直接大改风险高。

**做了什么**
- 把 `GameDir` 重写为**委托 `GamePlan` 的兼容层**：公开 API 不变，`dirPath` 全部按规范布局计算
  （`versions/<v>/{client,server/<type>}`、`client/assets|libraries|natives|profiles`…）。
- 结果：`OrzMC` CLI 与 `app` **无需改动**即切到规范布局（符合“不做迁移，旧目录提示重建”）。

**结果 / 产出**
- `OrzMC/OrzMCKit` main `1fd5934`，CI 双绿（`test` + `conformance` 26/26）；父仓库 bump `dc957f2`。

**风险 / 关注**
- 已补 **app 构建校验 CI**（`OrzMCApp` `ci.yml`，绿）——在最新 OrzMCKit 下 app 编译正常，布局切换得到验证。
- 既存安装在旧 `manifest/` 下的数据会“不可见”，符合既定“不迁移、提示重建”策略。
- 后续需把调用点（含 app）迁到 `GamePlan` 并退役 `GameDir`。

### 2026-10-13 — pi（Swift 适配器④：ConformanceAdapter + OrzMCKit CI）

**做了什么**
- `OrzMCKit` 新增可执行目标 `ConformanceAdapter`（stdin JSON → 纯计划接缝 → stdout JSON），覆盖 10 个 operation，
  复用 `GamePlan` / `MojangAPI` / `CacheKit` / `TransferPolicy`。
- OrzMCKit CI 新增 `conformance` job：checkout 父仓库 fixtures + 构建适配器 + 跑 `run.py --strict`（Q6）。

**结果 / 产出**
- `OrzMC/OrzMCKit` main `558dc70`，CI 双 job 绿：`test` + `conformance`（**PASS=26 FAIL=0**）。
- 父仓库 bump `2e6f77d`；`conformance.md`/`fixtures/README`/`design`/`plan`（Phase 2 Swift ✅、Q6 ✅）同步。

**踩坑**
- HEAD 制下 **`Package.resolved` 不会自动跟进**分支最新 revision → 需 `swift package update`
  （本次更新到 MojangAPI `bb8dbe8` / OrzSwiftKit `cd93070`）。已记入本文件 2.5。
- 套件又抓到一处：Swift `cacheDecision` 未使用 fixture 的 `ttl`（用了标准 TTL）——修正后全绿。

**下一步**
- ⑤ 产品面迁移（CLI/app → `GamePlan`，退役 `GameDir`）；⑥ 下载分块/进度接入。

### 2026-10-13 — pi（Swift 引擎③续：GamePlan.planClientLaunch）

**做了什么**
- 新增 `GamePlan.planClientLaunch`（B6 纯计划）：
  - 计划输入 `VersionPlan` / `ArgumentEntry` / `Rule` / `LibraryPlan`（**自带可解码子集**，解耦生成 schema，便于离线校验）
  - 库按 rules 过滤、classpath 由 artifact 推导（**jvmArgs 不含 `-cp`**）、令牌替换、
    legacy `minecraftArguments` 回退、`memory` 默认 `512M/2G`
- 单测与 conformance `client-plan/vanilla` 同构。

**结果 / 产出**
- `OrzMC/OrzMCKit` main `5c60238`，CI 绿；父仓库 bump `16cbedb`。

**下一步**
- ④ Swift 一致性适配器（大部分操作已有接缝：`GamePlan` / `MojangAPI` / `CacheKit` / `TransferPolicy`）。

### 2026-10-13 — pi（Swift 引擎③起步：GameType + GamePlan.layout）

**做了什么**
- `GameType` 扩到 `vanilla/fabric/forge/paper`，新增 `isClientCapable` / `isServerCapable` / `serverJarName`（对齐 spec §3）。
- 新增 [`GamePlan.layout`](swift/lib/OrzMCKit/Sources/Game/Plan/GamePlan.swift)：**规范对齐的纯计划契约**（D-a strangler-fig），
  对齐 `docs/spec/data-model.md` §1（`versions/<v>/{client,server/<type>}`、`java/<major>`、`cache/`、`backup/`，逻辑路径 `/`）。
- 单测：能力矩阵 / `serverJarName` / 规范布局。

**结果 / 产出**
- `OrzMC/OrzMCKit` main `f4aed31`，CI 绿；父仓库 bump `44b92bd`。

**踩坑**
- `ServerCommand.swift` 有对 `GameType` 的**穷尽 switch**（之前 grep 未显露）；
  CI 报 `switch must be exhaustive` 后，给 `.fabric/.forge` 加显式“暂未支持”提示（不静默，对齐 B4/类型能力）。

**下一步**
- `GamePlan`：`planClientLaunch`（把 `Client+Boot` 纯化）/ 下载计划 / 进度；随后 ④ 适配器。

### 2026-10-13 — pi（Swift 基础②：MojangAPI 渠道/离线/缓存）

**做了什么**
- 渠道归一：`BuildChannel` + `BuildKind.channel`（非 release → snapshot，B10）。
- 真实清单离线解码：`ManifestSummary` 自定义 `Codable` 兼容 Mojang 原生格式（`latest.release/snapshot`）；`resolve(channel:)`。
- `JavaRequirement` DTO + `Mojang.javaRequirement(fromVersionJSON:)`（读 `javaVersion.majorVersion`，缺失默认 8，B5）。
- **消费 `CacheKit`**（D-c）：`manifest` 改用落盘 `MetadataCache`（TTL 24h / `forceUpdate` 绕过 / 失败回退旧副本）；
  新增 `Mojang.configureCache(directory:/policy:)`；精简 `APICache`（仅剩 game-version/asset LRU）。
- **D12**：`MojangAPI` 平台下限抬到 macOS 13 / iOS 16（对齐 OrzSwiftKit）。

**结果 / 产出**
- `OrzMC/MojangAPI` main `3cbb04b` + `bb8dbe8`，CI 绿（macos-latest）。

**下一步**
- ③ `OrzMCKit`：`GameType` 四值 + `GamePlan` 纯计划契约（下一步开工）。

### 2026-10-13 — pi（Swift 基础① 续：RuntimeKit + TransferPolicy）

**做了什么**
- `OrzSwiftKit` 新增 **`RuntimeKit`**（D-b，Java 获取原语）：
  - `AdoptiumQuery`（`Utils.Platform` → Adoptium os/arch 映射 + `assets/latest` URL）
  - `AdoptiumAssetSelector`（纯选取）、`ArchiveExtractor`（tar.gz/tgz/zip）
  - `JavaRuntimeInstaller`（下载 → SHA-256 校验 → 解压 → 定位 `bin/java`，兼容 macOS `Contents/Home`）
- `JokerKits` 新增 **`TransferPolicy`**（B2 纯策略）：并发 clamp(1–64)、≥8MB 分 4 路、range 切分。
- 测试：Adoptium / Archive / TransferPolicy；CI 过滤扩展。

**结果 / 产出**
- `OrzGeeker/OrzSwiftKit` **PR #3 已合并**（squash，main `cd93070`），CI 绿（24 测试）。
- 本地：`swift build --target RuntimeKit/CacheKit` 通过（本机 SDK/链接限制见 2.5）。

**下一步**
- ② `MojangAPI`：消费 `CacheKit`（唯一缓存层）+ 离线快照接缝 + `oldAlpha/oldBeta → snapshot` 渠道归一。
- ③ `OrzMCKit`：`GameType` 四值 + `GamePlan`。

### 2026-10-13 — pi（Swift 基础 ①：OrzSwiftKit CacheKit 统一缓存）

**做了什么**
- 在 `OrzSwiftKit` 新增 `CacheKit`（决策 D-c）：
  - `CachePolicy`（纯策略）：`isFresh` / `decide`——TTL 24h、`ttl<=0` 不复用、`refresh` 绕过、容忍未来时间戳。
  - `MetadataCache`：落盘 JSON、原子写、命中优先；fetch 失败时**回退旧副本**并提示，无副本则抛出；`metaURL` 键清洗。
  - 对齐 `docs/spec/behavior.md` B1 与 Python `orzmc/infra/cache.py`。
- 修 `SwiftUIX/Web` 的 Swift 6 并发（补 `@MainActor`）；新增 `OrzSwiftKit` CI（`macos-15`）。
- 本地：`swift build --target CacheKit` 通过（本机 macOS 13 SDK 无法整包测试/链接）。

**结果 / 产出**
- `OrzGeeker/OrzSwiftKit` **PR #2 已合并**（squash，main `92bb455`）；CI 绿（build + CacheKit 7 例）。
- 按决策 B **关闭该仓库的 `enforce_admins`**（保留 review 给非管理员，管理员可绕过；OrzGeeker 与 OrzMC 保护策略不同）。
- **D11：外部 Swift 依赖改 HEAD 制** —— `OrzMCKit` 的 `MojangAPI`/`PaperMC`/`OrzSwiftKit` 由 tag 改为 `branch: main`
  （`d9babc9`，`Package.resolved` 已重解析）。

**下一步**
- ② `OrzSwiftKit`：`RuntimeKit`（Java 获取原语，D-b）、`Downloader` 并发/Range（B2）。
- ③ `MojangAPI`：消费 `CacheKit` + 离线快照接缝 + 渠道归一。

### 2026-10-13 — pi（Swift 工具链/CI 基座）

**做了什么**
- 固化 **D-a/D-b/D-c** 决策（以长期正确性为准），写入 [`docs/swift-conformance-design.md`](docs/swift-conformance-design.md) §7。
- 本机环境：macOS 13.7；CLT Swift 5.8；6.5-dev 工具链需 macOS 15 不可用。
  自行安装 **Swift 6.0.3** 到 `~/Library/Developer/Toolchains/swift-6.0.3-RELEASE.xctoolchain`（无 root，解包 pkg）。
- 但本机 SDK 仅 macOS 12/13，而 `OrzMCKit` 依赖的 OpenAPIKit 需 macOS 14 API → **本地无法编译整包**。
- 给 `OrzMCKit` 加 **CI（`macos-15`：`swift build` + `swift test`）**；把样板 `example` 测试换成确定性离线单测 → **CI 全绿**。

**结果 / 产出**
- OrzMCKit `328de49`（CI 绿）；父仓库 bump `OrzMCKit`。

**遗留 / 下一步**
- 按设计 §7.1 顺序：先 `OrzSwiftKit`（MetadataCache / RuntimeKit / Downloader）→ MojangAPI → Game、GamePlan → 适配器 → app 迁移。
- 本地验证受限；Swift 整包靠 OrzMCKit CI。

### 2026-10-13 — pi（依赖协作原则 + Swift 一致性设计）

**做了什么**
- 固化**依赖仓库协作原则**（`AGENTS.md` §7.1）：自有仓库（含 SwiftPM 依赖）必要时可直接拉本地修改，
  以能力划分清晰、跨模块配合为目标。
- 侦察 Swift 生态（`OrzMCKit` + `MojangAPI`/`PaperMC`/`OrzSwiftKit` 只读克隆）与 `app`。
- 产出 [`docs/swift-conformance-design.md`](docs/swift-conformance-design.md)：能力地图、与规范差距（布局/类型/Java/缓存/并发/启动/进度/
  非 TTY）、适配器设计、跨仓库改造清单与执行顺序。

**关键发现**
- Swift 布局是 `manifest/<v>/client/<type>/`（type 混入 client 路径），与规范 `versions/<v>/{client,server/<type>}` 不一致，
  **改造会级联到 `app`（HEAD 制）**。
- `MojangAPI` 有内存 `APICache`（TTL、`forceUpdate` 默认 true），**无落盘/离线回退**；`GameDir`/`GameType` 仅 `vanilla/paper`；
  Java 走 macOS `OracleJava` 检测，**无托管**；`parseBootArgs` 扫描文件系统拼 classpath（非纯函数）。

**待决策**
- **D-a** 先做非破坏的 `ConformancePlan` 骨架，还是先做破坏性的布局对齐（+app 级联）？
- **D-b** Java 托管放 `OrzSwiftKit` 还是 `swift/lib/OrzMCKit/Game`？ **D-c** 统一缓存策略归属？

### 2026-10-13 — pi（Q7=B：引擎跟随 main HEAD）

**做了什么**
- Q7 决策：**B / HEAD 制**（为快速迭代，伞内引擎版本 = `OrzMCKit` `main` HEAD，不依赖 tag）。
- `app`：`XCRemoteSwiftPackageReference "OrzMCKit"` 的 requirement 由 `upToNextMajorVersion 0.0.6`
  改为 `branch = main`；`Package.resolved` 的 orzmckit 钉子由 `version: 0.0.6` 改为 `branch: main @ 1244125`。
- 父仓库 bump app 指针至 `6555c10`（OrzMCKit 子模块已是 HEAD，无变化）。

**结果 / 产出**
- app `6555c10`；父仓库 `d55bdae`；docs：plan Q7/变更记录、架构 §7.1、本文件。

**遗留 / 关注点**
- HEAD 制意味着 `app` 需在引擎改动后重跑 `xcodebuild -resolvePackageDependencies` 跟进；必要时可在本地覆盖。

### 2026-10-13 — pi（依赖 URL 规范化 + 本地覆盖策略）

**做了什么**
- 重定向核查：`wangzhizhou/MojangAPI|PaperMC|ExarotonAPI` 与 `OrzGeeker/OrzMCKit|OrzMCApp` 均已转 `OrzMC/`；
  仅 `OrzGeeker/OrzSwiftKit`、`OrzGeeker/OrzAppUpdater` 仍外部。
- 把 `OrzMCKit`/`app` 内所有依赖与引用 URL（含 `Info.plist` 的 `SUFeedURL`、README 徽章、`release-macos.sh`）
  迁到规范 `OrzMC/*` 路径；保留 `Package.resolved` 的 Xcode 原生格式（避免反复 diff）。
- 明确**本地覆盖远端**：父仓库已检出 `OrzMCKit` 子模块，开发态可用本地包覆盖；但 `app` CI 独立检出，
  **不提交**本地路径依赖（D10 / 架构 §7.1）。

**结果 / 产出**
- 子模块：OrzMCKit `1244125`、app `49e4176`；父仓库 bump `4ee8a1e` / `518b52a`。
- docs：product-architecture §7.1、plan D10 / Q7 / 变更记录、本文件。

**踩坑**
- `app` main **受保护**，force-push 被拒；且 `gh api .../protection` 返回空（规则集不同）—— 只能追加提交。
- Python json 重排会改写 `Package.resolved` 的 `"k" : v` 风格，造成 231 行噪声；改用**纯文本替换**。

**遗留**
- Q7：伞内引擎版本（tag vs HEAD）未定；app 仍钉 `0.0.6` tag，子模块在 HEAD。
- 本地覆盖仅开发态使用，未提交。

### 2026-10-13 — pi（Q4：登记 OrzMCKit 子模块）

**做了什么**
- 核实事实：`OrzMCKit` 是 **组织自有**（`OrzMC/OrzMCKit`，PUBLIC，`main`），
  而非个人仓库；`OrzGeeker/OrzMCKit` 只是旧 URL（已重定向到 `OrzMC/`）。
  同时发现 `wangzhizhou/MojangAPI`、`wangzhizhou/PaperMC` 也已转入 `OrzMC/`；仅 `OrzGeeker/OrzSwiftKit` 仍在外部。
- **决策 Q4：登记为父仓库子模块**（符合“锁定产品组合”职责，并解锁 Q6）。
- `git submodule add -b main https://github.com/OrzMC/OrzMCKit.git OrzMCKit` → 钉 `e302d4e`。
- 更新 AGENTS 登记表（15→16）、架构角色地图/治理表、计划 Q4、docs 索引。

**结果 / 产出文件**
- 父仓库：`.gitmodules`、`OrzMCKit`（gitlink）、`AGENTS.md`、`docs/{product-architecture,product-unification-plan,README}.md`、本文件。

**遗留 / 关注点**
- `app` 以 SwiftPM 远程依赖消费引擎（`Package.resolved` 旧 URL @0.0.6），与父仓库子模块指针**双源**待 Phase 3 对齐。
- `OrzMCKit` 的 SwiftPM 依赖（MojangAPI/PaperMC/OrzSwiftKit）父仓库**不锁**版本。
- `app` 内部另有**同名本地包** “OrzMCKit”（OrzMCFoundation/Launcher/…）——命名冲突，建议改名（app 仓库工作）。

### 2026-10-13 — pi（Phase 2：Python 适配器接入）

**做了什么**
- 勘察 `orzmc` 库内部 API，确定纯计划接缝，并在过程中**发现参考/规范与 Python 现行语义的三处偏差**：
  `jvmArgs` 不含 `-cp`（classpath 单独装配）、`memory` 默认 `min=512M`、`userType=legacy`、
  `serverJarPath` 是路径而 `serverJarName` 才是文件名——已把参考与 fixtures 对齐 Python 现行。
- 新增 `python/orzmc/tests/conformance/adapter.py`（覆盖 10 个 operation，仅走内部 API、离线、无副作用）。
- 运行器新增注入 `ORZMC_CONFORMANCE_FIXTURES`，供子模块适配器定位快照。

**结果 / 产出文件**
- 子模块：`OrzPythonMC#32`（squash 合并 `645aace`）—— 6 平台 CI + `quality` 全绿。
- 父仓库：`scripts/conformance/{run.py,reference.py}`、`docs/spec/fixtures/**`、`docs/spec/conformance.md`、
  `docs/spec/fixtures/README.md`、`docs/product-unification-plan.md`、本文件。
- 一致性：参考适配器与 Python 适配器**各 26/26 绿**。

**踩坑 / 经验**
- PR 标题里 `(docs/spec fixtures)` 的**括号含空格**让 `pr-title` 报红（AGENTS 已知坑）；且 `pull_request` 默认不监听 `edited`，
  改完标题需 close/reopen 才重跑。子模块改动请遵守其 AGENTS（trunk-based + PR + `pr-title`）。

**遗留 / 下一步**
- Swift 适配器（OrzMCKit 非父仓库子模块，Q4 未决）；`server-plan`/`server-lifecycle` 样例。

### 2026-10-13 — pi（远程 Windows 验证环境）

**做了什么**
- 确认 `win`（`WangA@192.168.0.33`）免密可连；默认 shell 为 **PowerShell**。
- 建立**收敛工作根** `E:\orzmc-verify\`（`bin/ minecraft/ tmp/ logs/`），避免散落到 E: 根。
- 新增 [`scripts/win/run.sh`](scripts/win/run.sh)：用 `-EncodedCommand`(base64/UTF-16LE) 远程执行 PowerShell，
  规避引号与 `&` 陷阱，并静音进度流、统一 UTF-8 输出。
- 写入 [`AGENTS.md` §8.1](AGENTS.md) 与本文档 2.4。

**结果 / 产出文件**
- 新增：`scripts/win/run.sh`
- 修改：`AGENTS.md`、`HANDOFF.md`

**遗留 / 下一步**
- 尚未做实际 Windows 功能验证；待 Phase 2/3 需要时使用。

### 2026-10-13 — pi（Phase 2：一致性套件落地）

**做了什么**
- 建 `docs/spec/fixtures/`：4 个钉住快照（`version_manifest` / `1.20.4` / `1.16.5` / `no-java`）+ **26 个黄金样例**
  （layout / version-resolve / java / verify / cache / download / client-plan / non-tty / progress / error）+ `schema/fixture.schema.json` + `README.md`。
- 建 `scripts/conformance/`：语言无关**运行器** `run.py`（子集 / Contains / NotContains / Order / Count / Set / 点号路径 / `expectError`）
  与**规范参考适配器** `reference.py`（把规范纯计划语义编码为可执行参照）+ `README.md`（适配器协议）。
- 自检：`run.py --adapter reference.py` → **PASS=26 FAIL=0**。过程中抓到并修正一处歧义（`javaExecutable` 在 Windows 需带 `.exe`）。
- 回填 `conformance.md`（目录 / Harness / CI）与 `docs/README.md`、`spec/README.md`、plan Phase 2 状态。

**结果 / 产出文件**
- 新增：`docs/spec/fixtures/**`、`scripts/conformance/{run.py,reference.py,README.md}`
- 修改：`docs/spec/{conformance,README}.md`、`docs/README.md`、`docs/product-unification-plan.md`、`HANDOFF.md`

**遗留 / 下一步**
- 本批未提交；下一步把 Python/Swift 真实适配器接入并补 `server-plan`/`server-lifecycle` 样例。

### 2026-10-13 — pi（清理规范「待定」项）

**做了什么（用户拍板后落实）**
- CLI：`--root-dir`/`--verbose` 升全局；新增全局 `--json`；`--auth` 纳入规范；`server` 默认 `vanilla`；
  新增 §8「AI 调用与机器可读接口」（`capabilities` + 建议 MCP；核查后**不追 open-cli 名词**）。
- 安装：Windows 落点定为 `%LOCALAPPDATA%\Programs\orzmc`；引入 `beta` 渠道；
  App Store 细节（`macappstore://` 引导、需交互）与 appcast 版本口径对齐；GUI 在 Win/Linux 标为「计划中（未实施）」。
- 数据模型：`arch` 增加 `x86`；布局**一次性对齐、不做迁移**（旧目录提示删除重建）。

**结果 / 产出文件**
- 修改：`docs/spec/{cli-surface,install-update,data-model}.md`、`docs/product-architecture.md`、
  `docs/product-unification-plan.md`（新增 D9）、`HANDOFF.md`
- 定稿 `--json` 信封（`cli-surface.md` §6.1：`{ok,command,data,error}`）；`capabilities`/`orzmc mcp` 列为**计划、低优先级**。

**遗留 / 下一步**
- 本批未提交；下一步 Phase 2 fixtures + 双 harness。无阻塞性【待定】（仅余计划项）。

### 2026-10-13 — pi（Phase 1：规范草案完成）

**做了什么**
- 核验两个 CLI 的真实命令面（Python `orzmc-app` 全量；Swift `OrzMCKit` 的 `client/server/plugin/fabric`），
  以及 Python 安装器落点（`~/.local/bin`）、`install.conf` 字段、PATH/补全现状。
- 产出四份规范：
  - `docs/spec/cli-surface.md`：统一命令集（新增 `plugin`/`app`/`completion`）、选项命名冲突解决表、退出码、非 TTY、补全、迁移清单。
  - `docs/spec/install-update.md`：无 sudo 用户级安装、Shell 自动识别 + 补全、`install.conf` 扩展、自升级、GUI↔CLI 跨面安装与双渠道兑底。
  - `docs/spec/behavior.md`：行为契约 B1–B11（缓存/并发/校验/路径/Java/启动/生命周期/进度/非 TTY/版本/错误）。
  - `docs/spec/conformance.md`：黄金样例格式、断言规则、规范操作 API、覆盖矩阵、负向用例、CI 接线。
- 回填 `docs/spec/README.md` 目录、`docs/README.md` 索引、计划 Phase 1 状态与里程碑。

**结果 / 产出文件**
- 新增：`docs/spec/{behavior,cli-surface,install-update,conformance}.md`
- 修改：`docs/spec/README.md`、`docs/README.md`、`docs/product-unification-plan.md`、`HANDOFF.md`

**遗留 / 下一步**
- 本批未提交（见 2.1）；下一步 Phase 2：建 `fixtures/` 与双语言 harness；治理项 plan Q4。

### 2026-10-13 — pi（Phase 1 启动：`docs/spec/` 规范雏形）

**做了什么**
- 记录决策：Q2 规范落父仓库 `docs/spec/`（成熟后下沉独立仓库）；Q3 `OrzMCKit` 定位
  **Swift 可复用基础组件**；Q5 先 Markdown + JSON 样例。新增 D7（一个 `orzmc`、CLI+GUI 两面、
  共核、互相安装/打开）与 D8。
- 据产品形态更新 `docs/product-architecture.md`（§1.2 产品形态；L2 改称「产品面」；治理表重定位 `OrzMCKit`）。
- 启动 Phase 1：新建 `docs/spec/README.md`、`docs/spec/data-model.md`（含 `RootLayout`/版本/下载/
  Java/启动计划/安装记录等实体 + Python↔Swift 字段对照表）。

**结果 / 产出文件**
- 新增：`docs/spec/README.md`、`docs/spec/data-model.md`
- 修改：`docs/product-architecture.md`、`docs/product-unification-plan.md`、`docs/README.md`、`HANDOFF.md`

**遗留 / 下一步**
- 本批未提交（见 2.1）；下一步补 `behavior.md` / `cli-surface.md` / `conformance.md`，并处理 plan Q4（`OrzMCKit` 子模块登记）。

### 2026-10-13 — pi（Phase 0：产品架构与边界冻结）

**做了什么**
- 探得 Q1：`OrzMC/OrzMCKit` 可访问，已浅克隆核验，发现三项关键事实：
  1. `OrzMCKit` 自带同名 `orzmc` CLI（swift-argument-parser），与 Python CLI 功能重叠；
  2. Swift 引擎是依赖链：`OrzMCKit` → `MojangAPI` / `PaperMC` / `OrzSwiftKit`，**后三者是个人仓库**；
  3. 根目录布局两边不一致（Swift `manifest/<v>/...` vs Python `versions/<v>/...`），类型支持也不同。
- 产出 Phase 0 交付物 `docs/product-architecture.md`：
  仓库角色地图、L0–L3 分层、引擎六阶段映射、**允许依赖方向矩阵**、禁止事项、治理与已知差异。
- 回填 `docs/product-unification-plan.md`（第 2 章核验事实 / Q1 / Phase 0 状态）与 `docs/README.md` 索引。

**结果 / 产出文件**
- 新增：`docs/product-architecture.md`
- 修改：`docs/README.md`、`docs/product-unification-plan.md`、`HANDOFF.md`

**遗留 / 下一步**
- 本批未提交（见 2.1）；下一步清 Q2/Q3 → 开 Phase 1 `orzmc-spec`。

### 2026-10-13 — pi（提交、push 与 plugin 漂移决策）

**做了什么**
- 将 AI 协作结构整理为一次提交并 push `origin/main`（起始提交 `684d2ea`）。
- 处理 `plugin` 指针漂移：确认为**有意为之**——plugin 工作流先在 `develop` 迭代、
  里程碑合并 `main`；父仓库钉 `main` 发布线，故本地检出 `develop` 时显示 `M plugin` 属预期，**不 bump**。

**结果 / 产出文件**
- 提交并推送：`AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` / `HANDOFF.md` /
  `.github/PULL_REQUEST_TEMPLATE.md` / `docs/README.md` / `docs/product-unification-plan.md` / `README.md`
- 更新 `HANDOFF.md`：记录 Q4 决策与「父仓库钉发布线」策略。

**遗留 / 下一步**
- Phase 0 `docs/product-architecture.md`；清 Q1–Q3 以解阻塞 `orzmc-spec`。

### 2026-10-13 — pi（父仓库 AI 协作结构改造）

**做了什么**
- 核验 `python` 与 `app` 的真实分层：app 是 SwiftUI 前端、引擎在外部 `OrzMC/OrzMCKit`；
  python 是「引擎 + CLI + 安装器 + 自升级」全栈；真正重复在**引擎层**。
- 产出 `docs/product-unification-plan.md`：现状事实、决策 D1–D6、Phase 0–5、开放问题 Q1–Q6、上下文包。
- 为父仓库搭建 AI 协作结构：`AGENTS.md`（事实源）、`CLAUDE.md`（Claude 桥接）、
  `CONTRIBUTING.md`、`.github/PULL_REQUEST_TEMPLATE.md`、`docs/README.md`。
- 按工具偏好（pi / Codex / Claude）收敛：移除 `GEMINI.md`、`.cursor/rules/`。
- 更新 `README.md`（目录树 + 「协作与文档」入口）。

**结果 / 产出文件**
- 新增：`AGENTS.md`、`CLAUDE.md`、`CONTRIBUTING.md`、`.github/PULL_REQUEST_TEMPLATE.md`、
  `docs/README.md`、`docs/product-unification-plan.md`、`HANDOFF.md`
- 修改：`README.md`
- 删除：`GEMINI.md`、`.cursor/`

**遗留**
- 本批改动**尚未提交**（见 2.1）。
- `plugin` 子模块指针漂移未处理（见 2.2 / Q4）。
- 仅列计划，未开始 `orzmc-spec`。

---

## 6. 环境与设备差异（Environment）

| 设备 | 用途 | 已具备 | 备注 |
|---|---|---|---|
| macOS 开发机（`/Users/bot/OrzMC`） | 主力 | git / gh / pi / Swift 6.0.3 工具链 | **SDK 仅 macOS 12/13** → OrzMCKit 整包靠 CI |
| Windows 真机（`ssh win`） | 平台实测 | PowerShell / git | 工作根 `E:\orzmc-verify\`（见 2.4） |
| GitHub（`OrzMC` / `OrzGeeker`） | CI / 发布 | OrzMCKit / App / Python 均有 CI | OrzGeeker 需 admin 绕过 review |

**外部依赖仓库**（非父仓库子模块）：`OrzGeeker/OrzSwiftKit`、`OrzMC/MojangAPI`、`OrzMC/PaperMC`、`OrzGeeker/OrzAppUpdater`。

## 7. 禁忌 / 易错点（本仓库特有）

- ❌ 在父仓库直接提交子模块**内部**文件——代码改动必须进子模块仓库（`AGENTS.md` 铁律 1）。
- ❌ **`git add -A` / `git add .`**：会误暂存所有子模块指针（曾误 bump `plugin`）——始终显式 `git add <路径>`。
- ❌ 在子模块 detached HEAD 状态下改代码并提交——先 `git switch <分支>`。
- ❌ 把"只存在于本机/本会话"的关键信息留在脑子里——**一律写进本文件或 `docs/`**。
- ❌ 直接改 `tools/thanos`（外部上游仓库）。
- ❌ 修改 `AGENTS.md` 之外的桥接文件（`CLAUDE.md`）写内容——桥接不写内容。
- ⚠️ HEAD 制下改了 `OrzSwiftKit`/`MojangAPI`/`PaperMC` 后，依赖方需 `swift package update` 才会跟进 revision；`app` 侧 CI 已改为删 `Package.resolved` 重解析。

## 8. 交接模板（复制用）

> 开启一个新任务或结束一次会话时，用此模板在「第 5 章 会话日志」顶部追加一条。

```markdown
### YYYY-MM-DD — <agent/人>

**做了什么**
- 

**结果 / 产出文件**
- 

**遗留 / 下一步**
- 
```


### 2026-10-21 — Codex（启动器 UI 审查与交互复核补记）

- `swift/app` 仍在 main 未提交，未开分支、推送或 bump；本轮修正用户名 LabeledContent、满缓冲 Follow 触发、控制台行数中文、联系作者 Link，以及迁移远程窗口时遗漏的错误/结果提示。
- 全部修正后 air macOS/iOS 构建成功、平台无关单测 13/13、平台分层校验通过；最新产物 Settings 四页、控制台独立窗口/搜索/Follow 操作可达。
- 当前焦点与后续验收以 `swift/app/docs/ui-handoff.md` §11 为准：视觉截图缺失；1200 宽被 air 桌面裁至 1129；中文仍有玩家数/目录说明遗漏，MOTD 含格式码；停止全部、在线/满缓冲控制台与实际导出写入待受控验收。未操作远程服务器生命周期或凭证。


## 接力补充：2026-10-22 Swift app UI 转 Air

app UI 仍在 main 的未提交工作树中，基准 fa571e70c632ef1e514158b7deb5711001f8d111；新增三技能审查与 Air 交接文档。继续任务先读 swift/app/docs/air-ui-handoff-2026-10-22.md。交接包已准备到 Air `/Users/joker/orzmc-handoff/2026-10-22-ui-review/`，含 tracked patch、untracked 文件和规则快照。不要仅 git pull，也不要在会被同步覆盖的 `~/orzmc-build/app` 构建镜像中保留唯一改动。未提交、未推送、父指针未变。


### 2026-10-22 — Codex：Air UI 页面与导航交互优化

- app `feat/ui-refresh` 与父仓库 `feat/ui-refresh-handoff` 均已 fetch 核验与 origin 同步（0 ahead / 0 behind）；父 gitlink 仍 `b13b422`。本轮只改 app 子模块文档/代码与父 HANDOFF；`tools/OrzMCBackup` 既有脏状态保留。
- 按审查次序修正本地控制台 Follow、Exaroton 动作防重入与反馈、游戏目录草稿提交、远程日志清空缓冲；并处理内嵌控制台导航、RAM 保存顺序、列表空/错态、等待/断线状态、中文目录说明/MOTD、AX 提示条标签。代码与逐项理由见 `swift/app/docs/ui-review-2026-10-22.md`。
- Air 桌面读取最终构建的主窗口和 Settings/远程窗口 AX 树；验证四页设置、目录输入未提交/Escape 回滚、选版本更新详情、远程列表与离线详情。MOTD AX 文本不再含 `§` 样式码。没有真实远程生命周期操作，也没有代理截屏。
- 新增远程控制台缓冲 2 项单测；app XCTest 的 51 个 Launcher 测试 + DesignSystem 1 项通过，RemoteHosting 测试包含新增回归。macOS/iOS 最终增量构建均 `BUILD SUCCEEDED`；`scripts/check-platform-split.sh`、`scripts/verify/check.py`、本地化 JSON、`git diff --check` 通过。
- PR 保持草稿，无提交/推送/合并/发版。未完成项：真实日志/远程动作/RAM 失败受控验证，以及 960/1200pt 与亮暗/焦点视觉验收。

### 2026-10-22 — Codex：Air app 界面部分验收

- 使用 apple-native-product-design、swiftui-pro、swift-concurrency-pro；实时检查 Air Accessibility 树并交互验证控制台 Follow、设置路径草稿/回滚、Settings 四 pane 和 Remote 离线详情。细节及证据边界见 `swift/app/docs/ui-review-2026-10-22.md`。
- 功能/AX 部分通过。发现 BasicInfo 动态帮助提示仍显示英文 `Open Client console`；未发现明显的定向并发问题。没有截图、VoiceOver、真实日志或远程动作验证。
- 核实当前终端就在 MacBook Air (M1, macOS 27.0.1)，SSH `air` 别名未配置；`scripts/air/run.sh` 已退役，替换为 `scripts/swift-check.sh`。通过新脚本直接本机构建 macOS 与 iOS Simulator 均 `BUILD SUCCEEDED`（锁定依赖，DerivedData 在 `/tmp`）；app-test 73 项通过。`scripts/check-platform-split.sh` 与 app `git diff --check` 通过。视觉验收仍待维护者桌面截图与窗口尺寸、明暗、焦点检查。


### 2026-10-22 — Swift 检查车道迁移到本机

- 用户明确要求当前项目后续本机迭代，不再使用 `ssh air`，并清理相关逻辑与数据。新增 `scripts/swift-check.sh` 作为统一本机入口，覆盖 OrzMCKit build/test/accept、app macOS/iOS 构建、app-test 与打开构建产物；删除 `scripts/air/run.sh`，同步更新父仓库 AGENTS、pre-push 和活跃 app 操作文档。旧效率数据保留并标为历史。
- 验证：本机环境探测通过；app-test 73 项通过；macOS/iOS Simulator 构建均成功；本机脚本语法、app 平台分层与 diff whitespace 检查通过。OrzMCKit CLI build/test/release 构建与共享验收均通过；133 + 1 项 Swift 测试通过，25/25 CLI acceptance 通过。编译输出含既有依赖/源码 lint 与 deprecation warnings。
- 清理 `/Users/joker/orzmc-build` 中旧依赖镜像、CLI 镜像、状态数据约 7.1 GB，移除空 `/Users/joker/orzmc-handoff`。随后用户要求清除全部旧 app 实例并重建；通过 TERM 退出两个进程后，已彻底删除 `~/orzmc-build`、`/tmp/orzmc-ui-dd` 及旧 iOS DerivedData。新 macOS 与 iOS 构建产物位于 `~/Library/Developer/Xcode/DerivedData/OrzMC-local{,-ios}`，旧构建目录与 OrzMC 进程均确认不存在。
- macOS/iOS 冷构建与 app-test（73 项）均完成通过；旧 app 进程已退出且没有自动再次启动。工作树保持未提交；`swift/app` 和 `tools/OrzMCBackup` 原有改动保留。
