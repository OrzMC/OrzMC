# 两套 CLI 的并行策略（Two CLIs, One Product）

> **状态**：生效中 · **最后更新**：2026-10-20（新增 §5.1 M3 评估）
> **结论先说**：不冻结 Python CLI，但**改并行规则**——「规范先行 + 一个功能只在一侧写 + 台账显式记录落后」，
> 把"要不要两边都改"从**人记忆**变成**机器可校验**。中期目标是 **M3：Python 变成发行通道，功能委托 Swift**。
>
> 台账（机器校验）：[`spec/parity.json`](spec/parity.json) · 校验器：`scripts/verify/parity.py`（已接父仓库 CI）

---

## 1. 现在到底贵在哪

| 成本 | 现状证据 |
|---|---|
| **同一份判据写两遍** | 两个 `scripts/accept_cli.py`：842 + 724 行；早期用例数还不一致（26 vs 22） |
| **每次改契约要改两处** | CLI 契约 0.2（退出码/`--yes`/stderr/补全）在两侧各改一遍 |
| **不知道谁落后** | 只有 `surface.py` 比对命令面（0 漂移），**能力/行为差异没有台账** |
| **平台差异被当成"两边都要做"** | Windows 上 Swift 要打包 DLL，Python 只要 PyInstaller；反之 PyPI 分发只有 Python 有 |

## 2. 四种可选模型（含代价）

| 模型 | 做法 | 迭代成本 | 风险 | 结论 |
|---|---|---|---|---|
| **A. 冻结 Python** | 只维护 Swift | 最低 | Windows/PyPI 用户立刻受影响；你已否掉 | ❌ 暂不采用 |
| **B. 并行 + 单一主导 + 台账**（本文） | 每个功能指定 lead；另一侧 `parity`/`behind`；台账 CI 校验 | 中（新增功能只写一遍） | 需要纪律（但已机器化） | ✅ **现在采用** |
| **C. Python 作发行通道** | Python CLI 只做「装/升级/委托」：`pip install orzmc` → 下载对应平台 Swift 二进制 → 转发命令 | 最低（功能只有一份） | 需 6 平台资产（Windows arm64 缺）；`uvx`/离线场景变重 | 🎯 **中期目标（M3）** |
| **D. 代码生成** | 从 spec 生成两侧 CLI 骨架 | 低（长期） | 生成器本身要维护；行为语义仍手写 | ⏳ 观察 |

## 3. 并行期规则（R1–R5，必须遵守）

| 规则 | 内容 | 谁保证 |
|---|---|---|
| **R1 规范先行** | 任何行为/契约变化先改 `docs/spec/*`，再改实现 | 评审 + conformance |
| **R2 一个功能只在一侧写** | 写在该命令的 `lead` 侧；另一侧要么跟随（`parity`），要么登记 `behind`（写 `reason` + `review_by`） | `parity.py`（CI 失败） |
| **R3 平台差异归平台侧** | 桌面/Win 打包、PyPI/uvx 分发 → Python 侧自由发挥；引擎语义、CLI 契约 → **Swift 为准** | 见 §4 分工表 |
| **R4 共用件只有一份** | `docs/spec/`、`fixtures/`、命令面 manifest、合规文案 | `check.py` + `parity.py` |
| **R5 落后要交差** | `behind` 过期（`review_by` 到期）→ CI 失败，逼你补齐或改台账 | `parity.py` |

### 分工表（当前 `lead` 分配）

| 领域 | lead | 另一侧 |
|---|---|---|
| 引擎语义（client/server/backup/update/remove/list/version） | **Swift**（`Game` 是唯一长期引擎） | Python 跟随 |
| CLI 契约（信封/退出码/`--yes`/补全 F6/MCP） | **Swift** | Python 跟随 |
| 插件市场（`plugin` 搜索/下载） | **Python** | Swift 兼容实现 |
| Windows 打包/安装器（zip + DLL、`install.ps1`） | **Swift**（平台细节写在各自仓库） | Python 用 PyInstaller 那套 |
| PyPI / `uvx` 分发、纯 Python 环境 | **Python** | Swift 不参与 |
| `app`（macOS GUI 安装） | **Swift** | Python 无此命令（`na`） |

> 台账里 `na` 是**明示**的"不打算做"，不是遗漏——`parity.py` 会反向校验：标了 `na` 的实现里
> 真出现了该命令也会失败（防止偷偷漂移）。

## 4. 已落地的机制（本轮）

1. **`docs/spec/parity.json`**：13 个命令 × 2 实现的台账（`lead`/`parity`/`behind`/`na` + 说明）。
2. **`scripts/verify/parity.py`**（接入 `check.py` → 父仓库 CI）：
   - 覆盖率：manifest 每个命令必须登记（漏登记失败）；
   - 状态合法性：`lead` 与另一侧状态必须自洽；
   - `behind` 必须写 `reason` + `review_by`，**过期即失败**；
   - **验收用例对齐**：两个 `accept_cli.py` 的用例集合必须一致，实现独有的必须登记原因；
   - 可选动态校验：喂两侧 `capabilities --json` → 台账写 `parity` 就必须真有该命令，写 `na` 就不许有。
3. **M2 落地时，共享判据当场抓出 Swift 侧 3 个真 bug**：`client -m nope` 先联网再失败（沙箱 90s 超时）、
   `client -j 0` 直接挂住、补全 rc 行缺 `# added by orzmc` 标记 —— 已全部修复并回归（`OrzMCKit#76`）。
   这正是"判据只有一份"的直接收益：同一份断言同时压两个实现。
4. **本轮就抓到两处真实漂移**（这正是台账的价值）：
   - Python 有 4 个 Swift 没有的验收用例（typer 自动选项、冻结二进制、动态补全、补全落点 vs `state-paths.json`）
     → 前三条登记为"实现独有"，最后一条标 `review_by: 2026-12-31`（M2 解决）；
   - 台账把 `app` 记成 `python: na`，而 **Python 其实也有 `app` 命令** → Python 侧 `ledger` job 当场报错，
     已修正为 `parity`（并给非 macOS 的 `E_UNSUPPORTED` 语义留了注）。
5. **三处门禁的分工**：
   | 位置 | 跑什么 | 抓什么 |
   |---|---|---|
   | 父仓库 `check.py`（CI） | `parity.py` 静态 + 两个 harness 用例对齐（浅检出两个子模块） | 台账覆盖/状态/到期、判据漂移 |
   | `OrzMCKit` CI `ledger` job | `parity.py --swift-caps` | 台账声明 vs Swift 实际 capabilities |
   | `python` CI `ledger` job | `parity.py --python-caps` | 台账声明 vs Python 实际 capabilities |

## 5. 中期路线（M1–M3）

| 里程碑 | 内容 | 收益 | 状态 |
|---|---|---|---|
| **M1** | 台账 + 校验器 + **三处 CI 门禁**（父仓库 `check.py`、两个子模块各自的 `ledger` job） | 不再"凭记忆决定两边改不改"；落后可见、可到期；**台账与真实 capabilities 双向对账** | ☑ 已完成 |
| **M2** | **共享验收 harness** | ☑ **已完成（2026-10-19）**：`scripts/accept/cli.py` 一份，两侧 CI 稀疏检出父仓库调用；删除两份副本（842 + 724 行）；`--frozen` 表达冻结二进制专属用例 |
| **M3** | **Python 作发行通道**：`orzmc` (PyPI) 负责装/升级 Swift 二进制并**转发**命令（自研 shim，非重写引擎） | 功能只有一份；PyPI/uvx 生态保留；Windows/Linux 用户拿到的就是 Swift 实现 | 🟡 **阶段 1 已落地（2026-10-20，opt-in）**：`ORZMC_RUNTIME=swift` + `orzmc runtime status/install`；切默认待拍板（D-M3-1）。详见 §5.1 |

### 5.1 M3 评估（2026-10-20）

**前置条件核对**

| # | 条件 | 状态 |
|---|---|---|
| 1 | `orzmc-{macos,linux,windows}-{x86_64,arm64}` 六类资产齐 | 🟡 构建链路**六条全通**（2026-10-20 dry-run 全绿）；Windows arm64 资产随 OrzMCKit `0.18.0` 发布落地 |
| 2 | 干净环境可运行 | ✅ Windows zip+DLL 真机验过；Linux 每版 `verify-linux` 自动验收；macOS `install.sh` 全链路 |
| 3 | shim 的离线/受限网络降级 | ☐ 未做（M3 才需要） |

**建议方案（shim 转发，不是重写引擎）**

1. PyPI 仍发 `orzmc` / `orzmc-app`，但把**实现体**换成 ~300 行 shim（标准库 only，零新依赖）。
2. shim 首次运行：按 `platform` + `arch` 从 `OrzMC/OrzMCKit` 的 release 取
   `orzmc-<os>-<arch>`（Windows 是 zip），用同一 Release 的 `SHA256SUMS` 校验，
   解到 `<状态目录>/bin/`（Windows 另解运行时 DLL），**然后 `exec` 它**。
3. 之后每次运行**直接 exec**，Python 只做「找真身 + 转发 argv / 退出码 / 信号 / 三股流」。
   没有任何命令语义落在 Python 侧——避免又变成两份实现。
4. `orzmc update` / `self-uninstall` 交给**真身**（Swift 自升级，走 OrzMCKit 通道）。
5. `--json` 信封、`capabilities`、`mcp` 全部来自真身，天然与规范一致；
   共享验收 harness 对 shim 与真身跑同一套判据。

**必须先解决的三处规范冲突**（否则做出来就不合规范）

| 冲突 | 说明 | 建议 |
|---|---|---|
| **F1**「同一路径只能有一个可执行体」 | shim 与真身必然是两条路径 | 规范承认第三类角色：`~/.local/bin/orzmc` = **launcher**，`<状态目录>/bin/orzmc` = 真身；`install.conf` 记真身路径 + 新增 `channel=wrapper` |
| **F3**「`update` 只替换自己」 | shim 不参与版本号，否则两套版本打架 | `orzmc --version` 一律报**真身**版本；shim 版本只在 `orzmc version --json` 的 `wrapper` 字段暴露 |
| 版本号语义 | PyPI 包版本 vs Swift 版本 | shim 用 `0.x` 包装版本（或 `+swift.0.18.0` 本地标识），**不**跟随 Swift 版本号 |

**主要风险与缓解**

| 风险 | 缓解 |
|---|---|
| 首次运行要下载几十 MB（体验倒退） | 安装器（`pip install` 之后首次 `orzmc`）明确进度；也提供 `orzmc install-runtime` 预取 |
| 受限网络/企业离线 | 保留「已缓存真身则完全离线可用」；无缓存时报 `E_NETWORK` 并给出手动安装指引 |
| 存量 Python 实现用户被静默换实现 | 必须写**升级须知**（CHANGELOG + Release notes），并保留一版 `orzmc legacy` 逃生阀 |
| shim 自身出 bug 就全挂 | shim 足够薄（找真身 + exec）；`orzmc legacy` 可直接跑旧实现 |
| Windows 上 exec 语义弱（无 `exec`） | `subprocess` 转发 + 原样透传退出码；`Ctrl-C` 转 `CTRL_BREAK`/终止树（`ProcessRunner` 已有同类实现可参考） |
| PyInstaller 冻结的 shim？ | 不需要：shim 是 pip 安装的普通 Python 包；冻结二进制通道（`binary` job）在 M3 里**下线**，资产改由 OrzMCKit 唯一提供 |
| 双通道版本对账 | 台账 `parity.json` 增加 `channel` 维度：`OrzPythonMC` 的发布物 = shim 版本，`OrzMCKit` = 真身版本 |

**需要维护者拍板（拍板后才有 M3 实施 PR）**

- **D-M3-1**：切换方式——硬切（下一个 major 直接把实现换成 shim）还是软切（先 `orzmc legacy` 默认、`ORZMC_RUNTIME=swift` 预演一版）？
- **D-M3-2**：旧 Python 引擎的维护承诺——安全修复保多久（如「M3 发布后 6 个月」）？
- **D-M3-3**：真身落点是否就用 `<状态目录>/bin/`（对 F1/F3 的影响最小），还是装到 `~/.local/bin/orzmc` 并让 shim 改名？
- **D-M3-4**：PyPI `binary` 通道（6 平台 PyInstaller 资产）是否随 M3 一起下线（省一半发布矩阵）？
- **D-M3-5**：`orzmc`（库）是否仍独立发版给第三方当库用（当前 `orzmc` 库与 app 双包发布）？

**结论**：M3 技术上可行、前置基本就绪；真正的成本不在转发（那部分很小），而在
①**规范三处冲突的裁定**、②**存量用户的迁移叙事**。

### 5.2 阶段 1 已落地（2026-10-20，opt-in）

按「先让 shim 可用可验证、不强制用户切换」推进（即 D-M3-1 的**软切**方向先走一步）：

| 项 | 落地形态 |
|---|---|
| 规范 | `install-update.md` **§10.1**：launcher / payload 两个角色（F1 裁定）、`ORZMC_RUNTIME` 开关、`SHA256SUMS` 强校验、转发语义、版本号语义 |
| PyPI CLI | `feat(runtime)`（`OrzPythonMC#80`）：`ORZMC_RUNTIME=swift` 时转发；`orzmc runtime status|install` 管理真身 |
| 台账 | `parity.json`：`runtime` = python `lead` / swift `na`（真身自己就是被转发方） |
| 验收 | 共享 harness `contract/runtime-status-shape`（只有实现该命令的一侧跑） |
| 端到端 | 真实资产实测：`ORZMC_RUNTIME=swift orzmc --version` → 首次下载 `orzmc-macos-x86_64`（SHA256 校验）→ 输出**真身** `0.18.0`；`install.conf` 记 `channel=wrapper` |

**仍然待拍板**：D-M3-1（是否把默认切到 `swift`，需要一版带「升级须知」的迁移窗口）、D-M3-2..5。
阶段 1 **不动**默认行为、**不下线** PyPI 的 6 平台 PyInstaller 资产。

## 6. 反模式（并行期禁止）

- ❌ **"顺手两边都改"**：除非该命令的 `lead` 不是你，或你已把另一侧登记 `parity` 并同步更新验收用例。
- ❌ **在 Python 侧加独有功能却不登记**：会让 `parity.py` 的 `na`/`parity` 校验失真。
- ❌ **绕过 spec 直接改实现**：conformance 76 例会红，但更贵的是"两边语义不一致"要在用户那里才发现。
- ❌ **把平台差异当契约差异**：Windows 的 zip+DLL、macOS 的 `.app`、Linux 的 `zip` 依赖都是**平台细节**，写进各自仓库与 `docs/windows-port.md`，不进 CLI 契约。

## 7. 决策检查点

| 时点 | 检查 | 若满足 |
|---|---|---|
| 每次发版前 | `python3 scripts/verify/check.py`（含台账）绿 | 允许发版 |
| 2026-12-31 | M2（共享 harness）落地？ | 否则台账把 `review_by` 顺延并写明原因 |
| Windows arm64 资产就绪后 | 评估 M3 可行性（§5 前置 1–3） | 立项做 shim，Python 引擎进入冻结倒计时 |
