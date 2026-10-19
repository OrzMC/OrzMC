# 两套 CLI 的并行策略（Two CLIs, One Product）

> **状态**：生效中 · **最后更新**：2026-10-18
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
3. **本轮就抓到的真实漂移**：Python 有 4 个 Swift 没有的用例（typer 自动选项、冻结二进制、动态补全、补全落点 vs `state-paths.json`）。已按"实现独有"登记，其中最后一条标了 `review_by: 2026-12-31`（M2 解决）。

## 5. 中期路线（M1–M3）

| 里程碑 | 内容 | 收益 | 状态 |
|---|---|---|---|
| **M1** | 台账 + 校验器 + CI（本轮） | 不再"凭记忆决定两边改不改"；落后可见、可到期 | ☑ 已完成 |
| **M2** | **共享验收 harness**：`scripts/accept/cli.py` 放父仓库，两侧 CI 通过 checkout 父仓库调用 | 少维护 ~750 行；判据真正只有一份；独有用例用 `--only`/条件表达 | ☐ 待做（review_by 2026-12-31） |
| **M3** | **Python 作发行通道**：`orzmc` (PyPI) 负责装/升级 Swift 二进制并**转发**命令（自研 shim，非重写引擎） | 功能只有一份；PyPI/uvx 生态保留；Windows/Linux 用户拿到的就是 Swift 实现 | ☐ 待评估（前置：Windows arm64 资产 + 全平台资产齐） |

**M3 的前置检查**（做之前必须满足，否则用户会掉进"装了 Python 包却跑不起来"）：

1. `orzmc-{macos,linux,windows}-{x86_64,arm64}` 六类资产齐（当前缺 Windows arm64）；
2. 每个平台的二进制都能在**干净环境**跑（Windows 已验证 zip+DLL 方案）；
3. `orzmc` (Python) 的 shim 在无网络/受限网络下的降级路径（缓存已装二进制、明确报错）。

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
