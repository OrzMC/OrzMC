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
> **最后更新**：2026-10-13 by pi

---

## 0. 接手速查（Session Start Checklist）

```bash
git pull --recurse-submodules          # 拉到各设备一致状态
git submodule update --init --recursive
git status --porcelain                 # 有无未提交的父仓库/子模块变更
git submodule status                   # 子模块指针是否符合预期
```

然后按顺序读：

1. [`AGENTS.md`](AGENTS.md) —— 规则（三条铁律、子模块登记表、协作流程）
2. **本文件** —— 当前状态与下一步
3. [`docs/product-unification-plan.md`](docs/product-unification-plan.md) —— 进行中的方案（如有相关任务）

**结束会话前**：更新本文件第 1 / 2 / 5 章，并 `git add HANDOFF.md` 提交。

---

## 1. 当前焦点（Current Focus）

| 项 | 内容 |
|---|---|
| **主题** | 产品统一化 — Phase 2（一致性套件：Python 适配器已接入） |
| **状态** | 🟡 Phase 0/1 完成；Phase 2：fixtures **26 例** + 运行器/参考适配器 + **Python 适配器**（26/26 绿，PR #32 已合）；**Q4 已决**：引入 `OrzMCKit` 子模块 |
| **关联方案** | `docs/spec/`（规范）+ `docs/product-architecture.md` + `docs/product-unification-plan.md` |
| **涉及仓库** | `parent`（本轮改动全部在父仓库，未动任何子模块） |
| **下一步** | 见第 4 章 |

---

## 2. 状态快照（Repo State）

### 2.1 父仓库（OrzMC）

| 项 | 值 |
|---|---|
| 分支 | `main` |
| 已提交并推送 | AI 协作结构（`684d2ea`/`1142091`）+ Phase 0（`93fb39b`）+ Phase 1（`7b9165f`/`6640ea3`）+ 变更记录（`1b11a50`）+ 清待定（`2804af8`）+ 定稿 `--json`（`4b674e5`）+ Phase 2 fixtures/运行器（`ee0967b`）+ win 验证环境（`d5198e9`） |
| 本轮未提交 | Python 适配器接入：修改 `docs/spec/{conformance.md,fixtures/README.md}`、`docs/product-unification-plan.md`、`HANDOFF.md`；bump `python` 指针 |
| 已删除（历史） | `GEMINI.md`、`.cursor/rules/`（为不需要的 agent 预留，已移除） |
| 已知未提交 | 仅 `plugin` 子模块指针（**预期**，见 2.2） |

### 2.2 子模块在途状态

| 子模块 | 当前指针 | 分支 | 父仓库记录 | 说明 |
|---|---|---|---|---|
| `plugin` | `bd908b8` | `develop` | `5eadd6e`（main） | **有意为之，不要 bump**：plugin 工作流先在 `develop` 迭代、里程碑合并 `main`；父仓库**始终钉 `main` 发布线**，故本地检出 `develop` 时 `git status` 显示 `M plugin` 属预期 |
| `OrzMCKit` | `e302d4e` | `main` | `e302d4e` | **新增**（`08e6b76`）：Swift 引擎子模块，已对齐 |
| 其余 14 个 | 见 `git submodule status` | `main`/`master` | 一致 | 无偏离 |

> `git submodule status` 中行首 `+` = 当前检出与父仓库记录不一致；`-` = 未初始化。
> **父仓库指针钉发布线（`main`），不钉开发线（`develop`）。**

### 2.3 验证命令

```bash
git submodule status
git status --porcelain
git diff --submodule
```

### 2.4 远程真机验证环境（Windows）

| 项 | 值 |
|---|---|
| SSH 主机 | `win`（`WangA@192.168.0.33`，免密 key；主机名 `LAPTOP-APCBNCLR`） |
| 默认 shell | **PowerShell**（`&` 是后台运算符，注意引号） |
| 收敛工作根 | **`E:\orzmc-verify\`**（`bin/ minecraft/ tmp/ logs/`，已创建） |
| 执行助手 | `scripts/win/run.sh -c '<ps>'` / `-f <file.ps1>` / stdin |
| 清理 | `scripts/win/run.sh -c 'Remove-Item -Recurse -Force E:\orzmc-verify'` |

> ⚠️ `E:\orzmc` 是**生产部署**（caddy/cloudflared/database/mcsmanager），**勿动**。
> 详见 [`AGENTS.md` §8.1](AGENTS.md)。

### 2.5 Swift 构建与验证

| 项 | 值 |
|---|---|
| 本地工具链 | `~/Library/Developer/Toolchains/swift-6.0.3-RELEASE.xctoolchain`（Swift 6.0.3，已装） |
| 本地 SDK | 仅 macOS 12/13（CLT）→ `OrzMCKit` 整包 **无法本地编译**（OpenAPIKit 需 macOS 14 API） |
| 验证途径 | `OrzMCKit` CI（`macos-15`：`swift build` + `swift test`，已绿）；不依赖 OpenAPIKit 的独立包可本地编译 |
| 不可用 | `swift-latest` / 6.5-dev 工具链需 macOS 15；`swiftly` 在本机崩溃 |

---

## 3. 待决策 / 开放问题

> 产品统一化的开放问题以 `docs/product-unification-plan.md` 第 7 章为准；此处只列**当前阻塞推进**的。

| # | 问题 | 状态 | 建议默认 |
|---|---|---|---|
| Q1 | `OrzMCKit`（Swift 引擎）仓库能否拉取核对类型？ | ✅ 已决 | 可访问（`main`），已浅克隆核验：`Game`/`Fabric` + `orzmc` CLI；引擎依赖 `MojangAPI`/`PaperMC`/`OrzSwiftKit` 在个人仓库 |
| Q2 | `orzmc-spec` 落点？ | ✅ 已决 | 父仓库 `docs/spec/`；成熟后再下沉独立仓库 |
| Q3 | `OrzMCKit` 如何定位？ | ✅ 已决 | **Swift 可复用基础组件**（非 App 私有引擎），服务 Swift CLI 与 GUI；登记为子模块见 plan Q4 |
| Q4 | `plugin` 子模块指针漂移如何处理？ | ✅ 已决 | **不 bump**：`develop` 是迭代线、`main` 是发布线，父仓库钉 `main`；`M plugin` 属预期 |

---

## 4. 下一步（Next Actions，按优先级）

- [x] **P0｜提交并 push 父仓库 AI 协作结构**（`684d2ea` + `1142091`）。
- [x] **P0｜决定 `plugin` 指针漂移处理**：结论=**不 bump**（父仓库钉 `main` 发布线，本地检出 `develop` 属迭代常态）。
- [x] **P1｜Phase 0**：产出 `docs/product-architecture.md`（分层、所有权、允许依赖方向、禁止事项）。
- [x] **P1｜提交并 push Phase 0**（`93fb39b`）。
- [x] **P1｜Q2/Q3 已决**：规范落 `docs/spec/`；`OrzMCKit` 定位 Swift 可复用基础组件。
- [x] **P1｜Phase 1 规范草案**：产出 `docs/spec/{data-model,behavior,cli-surface,install-update,conformance}.md`。
- [x] **P1｜清「待定」+ 定稿 `--json`**（`2804af8` + `4b674e5`）。
- [x] **P2｜Phase 2 起步**：`docs/spec/fixtures/`（26 样例 + 快照 + schema）+ `scripts/conformance/{run.py,reference.py}`（自检 26/26 绿）。
- [x] **P2｜Python 适配器**：`OrzPythonMC#32` → `orzmc/tests/conformance/adapter.py`（26/26，已合并 `645aace`）。
- [ ] **P2｜提交本批父仓库改动 + bump `python` 指针**。
- [x] **P2｜Q4 已决**：登记 `OrzMCKit` 为父仓库子模块（`08e6b76`，钉 `e302d4e`）；核实 MojangAPI/PaperMC 已入组织。
- [ ] **P2｜Phase 0/1 评审**：确认决策 D1–D9 与规范。
- [x] **Swift 基础①**：`CacheKit`（PR #2 已合）；OrzGeeker 保护已放宽（`enforce_admins=false`）；D11 HEAD 制落地。
- [x] **P3｜Swift 基础①(续)**：`RuntimeKit`（D-b）+ `TransferPolicy`（B2）→ PR #3 已合（`cd93070`）。
- [ ] **P3｜B2 剩余**：把 `TransferPolicy` 接入 `Downloader`（实际 4 路 Range + 池）。
- [x] **P3｜Swift 基础②**：`MojangAPI` — 渠道归一 + 真实清单离线解码 + `JavaRequirement` + 消费 `CacheKit`（`bb8dbe8`，CI 绿）。
- [ ] **P3｜注意**：`MojangAPI` 平台下限现为 macOS 13 / iOS 16（D12）；OrzMCKit 需 `swift package update` 才会跟进新 revision。
- [x] **P3｜Swift 引擎③起步**：`OrzMCKit` `GameType` 四值 + 能力矩阵 + `GamePlan.layout`（`f4aed31`，CI 绿）。
- [x] **P3｜引擎③续**：`GamePlan.planClientLaunch`（B6 纯计划，`5c60238`，CI 绿）。
- [x] **P4｜一致性适配器（Swift）**：`OrzMCKit` `ConformanceAdapter` 26/26 绿；OrzMCKit CI `conformance` job（Q6 已决，`558dc70`）。
- [x] **P5｜布局切换**：`GameDir` 改为**委托 `GamePlan` 的兼容层**（`1fd5934`）——CLI/app 无需改动即得规范布局。
- [x] **P5｜app 构建校验 CI**：`OrzMCApp` 新增 `ci.yml`（xcodebuild build，无签名 + 跳过插件/宏校验），**绿**（`e23853d`）。
- [ ] **P5｜注全迁移**：逐步把调用点（含 app）迁到 `GamePlan`，再退役 `GameDir`。
- [x] **P3｜Java 托管（B5）**：`JavaRuntime` 接入服务端/客户端/CLI/GUI；移除 `which java`（`db70ad8`）。
- [x] **P3｜网络统一（B2）**：`TransferKit`（URLSession + 4 路 Range + 连接池 + 哈希跳过），**移除 Alamofire**（`b642b55`/`a700ebd`）。
- [x] **P3｜断点续传**：`.part` 持久化 + `Range` 续传（单流/4 路分块）（`d017efe`/`8dc6bb9`）。
- [x] **P3｜B8 进度结构**：`TransferProgress{kind:count|bytes}`，单流字节/批量计数（`d6f4769`/`ab61ac6`）。
- [x] **P3｜server-plan 样例**：`planServerDeploy`（27 例），Swift/参考/Python 三适配器均齐（`507d467`/`OrzPythonMC#33`）。
- [x] **P3｜B7 进程原语**：`OrzSwiftKit` `ProcessRunner`/`ManagedProcess`（优雅停止→TERM→KILL、退出码归一、`onLine`）（`10b4095`）。
- [x] **P3｜B7 接线**：`Server.start()`/`launchServer` 返回 `ManagedProcess`；CLI 前台等待并打印退出码；app `GUIServer` 同步（`3bba300`/`d4362bc`）。
- [x] **P3｜B9 非 TTY**：CLI 不阻塞（显式版本命中即用/找不到报错；非 TTY 最新 release；用户名 `guest`）（`1bc336d`）。
- [x] **P3｜B11 错误语义**：CLI 归一为用户可读信息、写 stderr、退出码 1（`82ff17c`）。
- [x] **P3｜planServerLaunch + 参数统一**：`GamePlan.planServerLaunch`（29 例）；`Server+Launch` 去掉 `-server`/`--pidFile`，对齐 Python 参数顺序（`52abfdc`/`OrzPythonMC#34`）。
- [x] **P3｜退役 `GameDir`**：新增 `GamePlan+Paths` 便捷 API；OrzMCKit CLI + app 调用点全部迁移；删除 `GameDir.swift`（`8d98ec0`/`23e64e0`）。
- [ ] **P3｜引擎③尾**：`GamePlan` 下载计划 / 进度；CLI/app 注迁到 `GamePlan`（退役 `GameDir`）。
- [ ] **P2｜Swift 适配器**：按 [`docs/swift-conformance-design.md`](docs/swift-conformance-design.md) §7.1 顺序推进。
- [x] **P2/3｜Q7 已决（B/HEAD 制）**：伞内引擎版本 = `OrzMCKit` `main` HEAD；`app` 改用 `branch = main`。
- [ ] **P2｜补样例**：`server-plan/`（`planServerDeploy`）与 `server-lifecycle/`（B7）。
- [ ] **P2｜可选**：加轻量 CI 校验 `AGENTS.md` 子模块登记表与 `.gitmodules` 一致；父仓库跑参考适配器自检。
- [ ] **P2｜Windows 真机验证**：需要时经 `scripts/win/run.sh` 在 `win` 上实测（产物限于 `E:\orzmc-verify\`）。
- [ ] **P2｜治理**：是否把 `OrzMCKit` 登记为子模块（plan Q4）。

---

## 5. 会话日志（Session Log，只追加，最新在最上）

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
- 新增 [`GamePlan.layout`](OrzMCKit/Sources/Game/Plan/GamePlan.swift)：**规范对齐的纯计划契约**（D-a strangler-fig），
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
- **D-b** Java 托管放 `OrzSwiftKit` 还是 `OrzMCKit/Game`？ **D-c** 统一缓存策略归属？

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

> 跨设备接手的常见坑：某设备缺工具/凭据、路径不同、子模块未初始化。新设备首次接手时补记。

| 设备 | 用途 | 已具备 | 备注 |
|---|---|---|---|
| （示例）macOS 开发机 | 主力 | git / pi / claude / 各语言工具链 | 路径 `/Users/bot/OrzMC` |
| （待补） | | | |

**通用注意**
- 首次 clone 必须 `--recurse-submodules`，否则子模块目录为空。
- 子模块默认分支各不相同（见 `AGENTS.md` 第 4 章）；`plugin` 开发用 `develop`，其余多为 `main`。
- 不要在**未初始化的子模块**目录里工作。

---

## 7. 禁忌 / 易错点（本仓库特有）

- ❌ 在父仓库直接提交子模块**内部**文件——代码改动必须进子模块仓库（`AGENTS.md` 铁律 1）。
- ❌ 在子模块 detached HEAD 状态下改代码并提交——先 `git switch <分支>`。
- ❌ 把"只存在于本机/本会话"的关键信息留在脑子里——**一律写进本文件或 `docs/`**。
- ❌ 直接改 `tools/thanos`（外部上游仓库）。
- ❌ 修改 `AGENTS.md` 之外的桥接文件（`CLAUDE.md`）写内容——桥接不写内容。

---

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
