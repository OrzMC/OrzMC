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
> **最后更新**：2026-10-16 by pi

---

## 0. 接手速查（Session Start Checklist）

```bash
git pull --recurse-submodules          # 拉到各设备一致状态
git submodule update --init --recursive
git status --porcelain                 # 有无未提交的父仓库/子模块变更
git submodule status                   # 子模块指针是否符合预期
python3 scripts/verify/check.py        # 父仓库组合校验（登记表一致 + 一致性参考自检）
```


## 0.1 接力提示词（新会话直接复制这段）

> 读 `AGENTS.md` 与 `HANDOFF.md`，从 §4「待办 A / 剩余项」继续。
>
> **当前状态（2026-10-16）**
> - **正版授权**：Azure `client_id` 已内置两端；**Mojang Game Service API 审核被拒（2026-10-17，无申诉通道）** → `login_with_xbox` 仍 `403`，**真实登录不可用**；下一步三选一（A. authlib-injector / B. BYO client id / C. 降级）见 §4 待办 A 与 §5 最新记录。
> - **合规**：免责声明/隐私政策/CLI 声明已落地，**单一来源** `docs/compliance/`（`compliance.json` + `privacy.md`），由 `scripts/sync_compliance.py` 生成到各引用；`check.py` 校验漂移。**改文案只改 `docs/compliance/` 再跑一次脚本。**
> - **命令面**：**两侧 0 偏差**（Python 完全一致；Swift `client --type fabric` 已落地并随 `v0.7.0` 发布；`forge` 命令面接受、引擎待落地）。
>
> **请按顺序**
> 1. `python3 scripts/verify/check.py`（登记表 + 一致性 76/76 + manifest + 合规漂移）确认基线绿；`git submodule status` 21 个齐全。
> 2. **若 Mojang 有回信**：按其要求处理；通过后立刻跑真实 E2E（上文脚本）+ `ssh air`/`ssh win` 真机，更新 `docs/spec/auth.md` 与 `HANDOFF.md`（§4 A4、§5）。
> 3. **否则**推进 `client --type forge`（Forge installer + patched jar，属新引擎能力；fabric 已完成，见 `v0.7.0`），走 `OrzMCKit` PR + `ssh air` 验证 + 发版。
>
> 铁律：代码改子模块、父仓库只 bump；不用 `git add -A`；一次提交只 bump 一个子模块。

然后按顺序读：

1. [`AGENTS.md`](AGENTS.md) —— 规则（三条铁律、子模块登记表、协作流程；**§5 含「禁止 git add -A」**）
2. **本文件** —— 当前状态与下一步
3. [`docs/spec/README.md`](docs/spec/README.md)（规范）+ [`docs/swift-conformance-design.md`](docs/swift-conformance-design.md)（Swift 侧设计）
4. [`docs/product-unification-plan.md`](docs/product-unification-plan.md)（方案/决策）

**结束会话前**：更新本文件第 1 / 2 / 4 / 5 章，并 `git add HANDOFF.md` 提交。

## 1. 当前焦点（Current Focus）

| 项 | 内容 |
|---|---|
| **主题** | 产品统一化 — Phase 0–5 完成；T1 端到端完成；**T2 命令面统一完成且两侧 0 偏差**（Swift `client --type` vanilla/fabric/forge 全落地）；一致性 **76/76**（三适配器）；**行为契约 B1–B11 两侧全 ✅**；`--auth` 离线部分完成但** Mojang 审核被拒**（2026-10-17，内置 client_id 实际不可用）；**`orzmc mcp` 两端完成**；剩余：**正版登录后续路线（A/B/C 待拍板）**、codegen（已评估：暂不做） |
| **状态** | 🟢 一份规范 + 多实现 + 前端共用核心；一致性套件 **76/76**（三适配器全绿）；`--auth` 两端**离线**链路就绪，但 **Game Service API 审核被拒 → 真实登录不可用**；`orzmc mcp` 两端就绪；命令面 **两侧 0 偏差且 `--strict` 已进 CI**（含 enum 比对）；**元数据缓存已统一到 `<root>/cache`**；**最近发布**：Python `2.11.0` / Swift **`v0.11.1`** |
| **关联方案** | `docs/spec/`（6 份）+ `docs/product-architecture.md` + `docs/product-unification-plan.md` + `docs/swift-conformance-design.md` |
| **当前基线** | 父仓库 `main`（以 `git ls-tree HEAD` 为准，不钉死哈希）；子模块记录指针见 §2.2；发版组合见 [`RELEASES.md`](RELEASES.md) |
| **下一步** | ① ~~App Phase A/B~~ **均已合并并 bump**（A：`0d36e26`/`23b4130`；B：python `3974436`、OrzMCKit `329230f`、app `50b08a6`，已发 Swift CLI `v0.12.0`）；剩余 Phase C（GUI 认证 UI）**等 authlib-injector 决策**；② **第 2 次申请已于 2026-10-17 提交，等邮件结果**（无提交编号；两周无回信按未通过处理，不再投第 3 次）；③ 并行推进 **authlib-injector / Yggdrasil**（不依赖白名单的正版联机主路） |

## 2. 状态快照（Repo State）

### 2.1 父仓库（OrzMC）

| 项 | 值 |
|---|---|
| 分支 | `main`（跟随远端；子模块指针以 `git ls-tree HEAD` / `RELEASES.md` 为准） |
| 工作区 | `M plugin`（本地常检出 develop，**预期**）；`python` / `OrzMCKit` 已合并且与记录指针一致 |
| 父仓库 CI | ✅ `.github/workflows/ci.yml` → `python3 scripts/verify/check.py` |
| 已删除（历史） | `GEMINI.md`、`.cursor/rules/` |

> ⚠️ 父仓库禁用 `git add -A`/`git add .`——会误暂存**所有**子模块指针（曾误将 `plugin` 的 develop 记入），**始终显式 `git add <路径>`**。

### 2.2 子模块记录指针（`git ls-tree HEAD`，钉 `main` 发布线）

| 子模块 | 记录指针 | 说明 |
|---|---|---|
| `plugin` | `5eadd6e` | 本地常检出 `develop`（`bd908b8`）→ `M plugin` **预期，不要 bump** |
| `python` | `a57fb6f` | `OrzPythonMC`；适配器 + 下载续传 + 全局选项 + `--json` + `completion` + `capabilities` + `plugin`/`app` + `planClientDownload` + 退出码归一；**已发布 `2.9.1`**；**内置 client_id**：`--auth` 离线链路 + `orzmc mcp` + `auth/*` 适配器 + 服务端 `--demo`/`--online-mode`；**`quality` job 追加 CLI 命令面 `--strict` 校验**；**README/落地页对齐命令面**；**`2.9.1` 修复 `orzmc update` 裸名 `argv[0]` 误把 CWD 同名文件当目标（`running_binary()` + 验收步骤 5b）；CHANGELOG/Release notes 补「升级须知」并固化约定** |
| `swift/app` | `efbb665` | `OrzMCApp`；有构建校验 CI；GUI 共用引擎 `launchClient`/`downloadClient`（Phase 4） |
| `swift/lib/OrzMCKit` | `c42f677` | **Swift 引擎 + `orzmc` CLI（发行产品，D13）**；含 `ConformanceAdapter`（76/76）；**已发布 `v0.9.1`**；**内置 client_id** + `orzmc mcp` + **`client --type` vanilla/fabric（fabric-meta）/forge（官方安装器）** + 命令面全量收敛 + `--strict` 进 CI；**Mojang 元数据缓存指向 `<root>/cache`（与 Python/app 共享）**；**CI SwiftPM 缓存 + OrzSwiftKit 预编译 SwiftLint（lint 插件回归）**；此前已发 `v0.1.0`…`v0.9.0` |
| `swift/lib/{MojangAPI,PaperMC,ExarotonAPI,OrzSwiftKit,OrzAppUpdater}` | 见 [`RELEASES.md`](RELEASES.md) | Swift 依赖（引擎依赖 + 基础设施 + 自升级），随 `swift/` 收拢；HEAD 制，本地改后各自仓库提交 → 上层 bump |
| `site`/`deploy`/`proxy`/`webmc`/`profile`/`tools/*` | 见 [`RELEASES.md`](RELEASES.md) | 均钉 `main`（`LoginSecurity`/`tools/thanos` 为 `master`） |

> `git submodule status` 行首 `+` = 检出与记录不一致（plugin 正常）；`-` = 未初始化。

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
| 验证途径 | `OrzMCKit` CI（`macos-15`：`swift build`+`swift test`+`conformance`）；不依赖 OpenAPIKit 的包（`OrzSwiftKit` 的 kit）可本地编译 |
| **远程 Mac（`ssh air`）** | macOS 27 / Swift 6.4 / Xcode 27（arm64）——**可本地编译 OrzMCKit**（本机 SDK 太旧时的替代）。Swift 验证两条路：`ssh air` 本地编译 / `OrzMCKit` **CI**（`conformance` job 检出父仓库 fixtures 跑 `--strict`，权威）。构建目录 air `~/orzmc-build/{OrzMCKit,parent,OrzSwiftKit}`（`parent` 下放了 fixtures+conformance 供适配器跑） |
| Air 上的 SwiftLint 坑 | 单独构建 `OrzSwiftKit` 时，新解析的 SwiftLint 在 Swift 6.4 下编译失败（`MemberImportVisibility`）；但 `OrzMCKit` 的 `.build` 用钉住版本可正常构建 |
| 本地联调 | `scripts/swift-dev.sh {sync,edit,status,unedit,xcode}` —— 把 `swift/lib/OrzMCKit` 的依赖本地覆盖到 `swift/lib/*`（开发态、不提交；app 的 Xcode 覆盖见 `xcode` 子命令） |
| 不可用 | `swift-latest`/6.5-dev 工具链需 macOS 15；`swiftly` 在本机崩溃 |

### 2.6 Swift 依赖（现为 `swift/lib/*` 子模块）

> 2026-10-15 起这些仓库已作为父仓库子模块收拢到 `swift/lib/*`（路径/指针见 §2.2 与 `RELEASES.md`）。
> 消费侧（`app`/`OrzMCKit`）仍以 SwiftPM `branch=main` 远端解析；开发态用 `scripts/swift-dev.sh` 本地覆盖。

| 子模块 | 当前 | 说明 |
|---|---|---|
| `swift/lib/OrzSwiftKit` | `main`（`d71cc57`） | 基础设施：`CacheKit`/`RuntimeKit`/`TransferKit`/`JokerKits`(含 `ProcessRunner`)；CI 含 `network-smoke`；**#8 修复 `ArchiveExtractor`（`.tmp` 临时名按魔数回退）**；**#10 lint 插件改用 SwiftLint 预编译二进制（插件回归：本地/CI 每次构建自动 lint，但不再编译 swift-syntax）** |
| `swift/lib/MojangAPI` | `main`（`0f11294`） | 元数据；平台 macOS 13 / iOS 16（D12）；**版本 JSON 可选磁盘缓存（原始字节，`configurePackageCache`）**；**CI 加缓存 + 修重复触发；联网用例门控 `ORZMC_NETWORK_SMOKE`（离线确定性）** |
| `swift/lib/PaperMC` | `main`（`19ae5af`） | Paper/Hangar |
| `swift/lib/ExarotonAPI` | `main`（`1eea571`，tag `0.0.9`） | Exaroton API 客户端 |
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
- [ ] **App Phase C（等决策）** —— GUI 认证 UI：等 authlib-injector / BYO client id 拍板后再做（现在做会返工）。
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
