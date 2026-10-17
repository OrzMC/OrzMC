# 多前端与共享数据契约（N Frontends, One Dataset）

> **状态**：草案 `specVersion 0.1`｜**最后更新**：2026-10-17
> **定位**：定义「**规范唯一、数据唯一、前端多个**」的模型。Python CLI、Swift CLI、`OrzMCApp`(GUI)、
> `orzmc mcp`、agent / CI 脚本，**都是同一套数据的不同前端**，不是各自独立的工具。
> **上游**：[`../product-architecture.md`](../product-architecture.md) §1.2 / §3；
> **相关**：[`install-update.md`](install-update.md)（`install.conf` / 卸载）、[`auth.md`](auth.md) §5（`auth.json`）、
> [`data-model.md`](data-model.md)（游戏根布局）、[`behavior.md`](behavior.md)（下载/缓存并发）。

---

## 1. 模型（为什么可以共存）

```
         ┌──────────────── 规范层（唯一）docs/spec/*  ── 语言无关、可验证 ─────────────┐
         │  data-model · behavior · cli-surface · auth · install-update · frontends    │
         └───────────────▲───────────────────────────────▲────────────────────────────┘
                         │ 映射                          │ 映射
   ┌─────────────────────┴──────┐        ┌───────────────┴──────────────────┐
   │ 前端 A：Python CLI         │        │ 前端 B：Swift CLI / GUI / MCP …  │
   │ 前端 C：agent / CI / 脚本  │        │ 前端 D：将来任何新形态            │
   └─────────────┬──────────────┘        └───────────────┬──────────────────┘
                 │        读写同一套契约文件（无私有 IPC）  │
         ┌───────▼───────────────────────────────────────▼───────┐
         │ 数据层（唯一实例）：状态目录 + 游戏根 + 补全文件        │
         └───────────────────────────────────────────────────────┘
```

**F0（唯一性）**：一台机器上**规范唯一、数据唯一、前端可以有任意多个**。
前端之间**不互相调用、不各自维护状态格式**，而是读写同一套契约文件。
因此"同一台机器既装了 Python CLI 又装了 Swift CLI + App"是**被支持的形态**，
其约束由下面 F1–F9 给出（主要是**占位与写入权**，不是格式不兼容）。

**推论（规范驱动）**：新增一种前端**不需要新格式**；若某个前端确实需要新的持久化数据，
**必须先改本规范**（新增文件 + 字段 + 写入者 + 并发语义），再改实现。
**禁止**先实现、后补规范，或让某个前端"悄悄"往共享位置塞私有文件。

## 2. 数据归属（唯一位置 / 写入者 / 并发语义）

| 数据 | 唯一位置 | 写入者 | 并发语义 | 规范 |
|:--|:--|:--|:--|:--|
| 状态目录 | `${XDG_STATE_HOME:-$HOME/.local/state}/orzmc`（Windows `%LOCALAPPDATA%\orzmc`） | 各前端按需 | 共享目录 | §3 |
| 安装记录 | `<状态目录>/install.conf`（兜底 `<二进制目录>/.orzmc-manifest`） | 安装器 / `update` | **读多写少**，写入需护栏（F3） | [`install-update.md`](install-update.md) §3 |
| 认证会话 | `<状态目录>/auth.json`（`0600`，原子写） | 登录 / 刷新令牌的前端 | **同一时刻应只有一个前端刷新**（F4） | [`auth.md`](auth.md) §5 |
| 游戏根 | `~/minecraft`（`--root-dir` 可改） | 任意前端 | **元数据可并发，运行时目录独占**（F5） | [`data-model.md`](data-model.md) |
| 补全脚本 | `~/.local/share/bash-completion/completions/orzmc`、`~/.zsh/completions/_orzmc`、`~/.config/fish/completions/orzmc.fish` | `completion install` | 幂等覆盖（F6） | [`install-update.md`](install-update.md) §5 |
| 可执行体 | `${XDG_BIN_HOME:-$HOME/.local/bin}/orzmc` | 安装器 / `update` | **同一路径只能有一个**（F1） | [`install-update.md`](install-update.md) §2 |
| 前端私有状态 | 前端自有位置（如 GUI 的 `UserDefaults`、窗口/缓存设置） | 该前端 | 独占 | F7 |

> 机器可读版本见 [`fixtures/state/paths.json`](fixtures/state/paths.json)（供将来的 `state.paths` conformance 用例比对）。

## 3. 共存规则（条款）

**F1 二进制唯一**：所有前端共用同一个 `orzmc` 可执行文件名与默认目录，**后装者覆盖先装者**。
"同时安装"≠"同时可用"：PATH 上永远只有一个 `orzmc`。
判断当前装的是哪一份 → 读 `install.conf` 的 `source` / `version`，或 `orzmc version --json`；
**禁止**用文件名、文件大小、字节数推断身份（`0.11.0` 与 `0.11.1` 资产字节数曾恰好相同）。

**F2 记录共享、卸载一致**：`install.conf` 是**唯一的安装事实**。任一前端的 `uninstall` 都必须按它执行：
移除二进制、删除记录、清理补全文件、按 `path_line` 精确删除 PATH 行、可选删游戏根。
由于这会**连带拆掉另一份前端**，`uninstall` 必须保留二次确认（`--yes`）与危险目录护栏。

**F3 更新不越界**：`update` 只替换**自己正在运行的那份二进制**，且只有在
「记录里的 `binary` == 本次替换目标」时才回写记录（两侧均已实现同一护栏）。
**禁止**按"版本号更大"跨渠道替换，或按对方的发布源猜测渠道：Python 前端走
`OrzMC/OrzPythonMC`，Swift 前端走 `OrzMC/OrzMCKit`，这是**同一规范的两个发布通道**（见 §7）。

**F4 认证会话共享**：`auth.json` 的 schema 由 [`auth.md`](auth.md) §5 定义，**两个实现必须互相可读**。
因此在一个前端登录后，其他前端应能直接复用（这是特性，不是耦合）。
约束：**同一时刻应只有一个前端执行令牌刷新**——刷新会重写整份文件，后写者覆盖先写者；
实现应"先重读再决定是否刷新"（避免 TOCTOU），不得假设自己持有最新内存副本。

**F5 游戏数据共享、运行独占**：`root/versions/<v>/...` 的**元数据**（version JSON、assets、libraries、
`java/<major>`）可被多前端并发读写，因为写入是幂等的（sha1/hash 校验 + 唯一临时名 + 原子 rename）。
但**运行时目录**（`client/profiles/<profile>/` 的 `options.txt`/`saves`/`logs`、
`server/<type>/` 的 `worlds`/`plugins` 运行时写入）**同一时刻只允许一个进程**。
即：可以两个前端并存，但**不要同时启动同一个版本 + 同一个 profile**。

**F6 补全幂等**：`completion install` 覆盖同路径即为最新；内容由各自 `capabilityList()` 渲染，
命令面统一后两者内容等价。`powershell`/`pwsh` 目前仅生成脚本、不落盘安装（交互差异，不属契约）。

**F7 私有状态不污染共享层**：前端专有的持久化（GUI 窗口状态、同步/缓存偏好等）放在前端自有位置，
**不得**写进状态目录的契约文件、也不得写进游戏根的契约布局。

**F8 前端之间不直接调用**：不新增私有 IPC/socket/端口协作。跨前端协作只走契约面：
`capabilities`、`--json` 输出、`install.conf`、`auth.json`、游戏根布局。

**F9 数据实例可多套（但格式唯一）**：`XDG_STATE_HOME`（状态目录）、`--root-dir`（游戏根）、
`ORZMC_BIN`（二进制目录）表达的是"**同一规范下的另一套数据实例**"，用于对照测试、多用户配置、并行验证。
**不是**另一种格式，也不构成分叉。

## 4. 隔离矩阵

| 目的 | 手段 | 影响 | 不影响 |
|:--|:--|:--|:--|
| 两套前端各自独立的安装/认证状态 | `XDG_STATE_HOME=<dir>` | `install.conf`、`auth.json` | 游戏根、补全文件 |
| 二进制互不覆盖 | `ORZMC_BIN=<dir>`（安装器）/ 手动放置 + 别名 | PATH 上的 `orzmc` | 状态目录、游戏根 |
| 游戏数据分开 | `--root-dir <dir>` | 版本/世界/服务端数据 | 状态目录、二进制 |
| 单机对照验证（同版本不同实现） | 上述三者组合 | 全部 | — |

> 验证类使用**必须**组合隔离；只隔离其中一项仍会共享其余数据。

## 5. 新增一个前端的接入清单（Definition of Ready）

1. 读 [`README.md`](README.md)、本文件、[`data-model.md`](data-model.md)、[`behavior.md`](behavior.md)、[`cli-surface.json`](cli-surface.json)。
2. **只用 §2 的位置**；需要新数据 → 先改规范（F0 推论）。
3. 提供机器可读命令面（`capabilities`）与 `--json` 输出，并与 `cli-surface.json` `--strict` 比对无未声明差异。
4. 通过 `fixtures/` 一致性用例（`scripts/conformance`）。
5. 安装 / 自升级遵守 F1–F3（同护栏）。
6. 声明自己的"面"：`install.conf` 的 `surface = cli|gui`（见 §7 待补项）。

## 6. 反模式

| ❌ 反模式 | ✅ 正确做法 |
|:--|:--|
| 用二进制大小/哈希判断"装了哪份实现" | 读 `install.conf.source` / `version` 或 `version --json` |
| 前端各自维护一份"已安装版本清单" | 以游戏根 `versions/` 为准（`list` 只读它） |
| 假设自己独占 `~/minecraft` | 运行时目录独占，元数据并发（F5） |
| 为某前端新增私有文件到状态目录 | 先改规范再实现（F0） |
| `update` 时"顺便"把另一渠道的实现换掉 | 只替换自己运行的那份（F3） |
| 卸载时静默删掉共享二进制 | 保留二次确认与护栏（F2） |

## 7. 现状与校验

**已自动校验**

- 命令面 / enum：`scripts/verify/surface.py --strict`（两侧各 0 处未声明差异）。
- 行为与数据形状：`docs/spec/fixtures/`（76 例，两侧 CI 均接）。
- 组合与文档一致性：`scripts/verify/check.py`（子模块登记表、一致性参考、manifest、合规文案）。

**待补（按优先级）**

1. **`state.paths` conformance 用例**：两侧上报实际使用的状态目录 / 记录文件 / 认证文件 / 默认游戏根 /
   补全路径，与 [`fixtures/state/paths.json`](fixtures/state/paths.json) 比对 → 防路径漂移。
2. **`surface` 字段**：[`install-update.md`](install-update.md) §3 已声明 `surface = cli|gui`，
   但**两侧安装器都还没写**（Python `install.sh`、Swift `InstallManifest` 均缺）。这是"哪份前端装的"
   的唯一标记，补上后 F1/F2 的身份判断就不必靠猜。
3. **守卫并发写入**：`auth.json` 的"先重读再刷新"目前靠约定，尚未有跨进程锁。

**当前实现对照（Python `2.11.0` / Swift `0.11.1`）**

| 项 | Python | Swift | 结论 |
|:--|:--|:--|:--|
| 状态目录 | `${XDG_STATE_HOME:-$HOME/.local/state}/orzmc` | 同 | ✅ |
| `install.conf` | 同路径同 schema | 同 | ✅ |
| `auth.json` | 同路径同 schema | 同 | ✅ |
| 游戏根 | `~/minecraft` | 同 | ✅ |
| 补全安装路径 | bash/zsh/fish（+ powershell 仅生成） | bash/zsh/fish | ✅（powershell 交互差异） |
| 自升级渠道 | `OrzMC/OrzPythonMC` | `OrzMC/OrzMCKit` | ✅ 设计如此（两个发布通道，F3） |
