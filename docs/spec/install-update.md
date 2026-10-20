# 安装 / 自升级 / 跨面安装契约（Install & Update Contract）

> **状态**：草案 `specVersion 0.3` ｜ **最后更新**：2026-10-18
> 支撑产品形态「一个 `orzmc`、CLI 与 GUI 两面、可互相安装/打开」（见 [`../product-architecture.md`](../product-architecture.md) §1.2）。
> **基线**：复用 Python 现有安装体验（用户认可），并吸收 Swift 亮点。

---

## 1. 目标与原则

- **无 sudo**：全部为用户级安装（写入用户目录），不触碰系统目录、不要求管理员权限。
- **装完即可用**：安装后 Shell **自动识别**（PATH），并**自动补全**，减轻用户记忆负担。
- **可卸载**：只删自己登记过的内容（沿用 Python `uninstall` 安全护栏）。
- **跨面**：GUI 能装 CLI，CLI 能装 GUI；渠道可互相兜底。
- **单一事实**：安装记录格式、PATH 修改、补全落点都写入 `install.conf`，卸载据此还原。

---

## 2. 目录约定

| 用途 | Unix（macOS/Linux） | Windows |
|:--|:--|:--|
| 二进制目录 | `${XDG_BIN_HOME:-$HOME/.local/bin}` | `%LOCALAPPDATA%\Programs\orzmc`（Python 现行） |
| 状态/记录目录 | `${XDG_STATE_HOME:-$HOME/.local/state}/orzmc` | `%LOCALAPPDATA%\orzmc` |
| 安装记录 | `<状态目录>/install.conf` | `<状态目录>\install.conf` |
| 记录兜底位置 | 二进制同目录 `.orzmc-manifest` | 同左 |
| GUI 应用目录（macOS） | `~/Applications`（用户级，免 sudo） | — |
| 游戏根目录 | `~/minecraft`（`--root-dir` 可改） | `%USERPROFILE%\minecraft` |

> 规范默认二进制目录 = `${XDG_BIN_HOME:-$HOME/.local/bin}`（Python 现行），**不使用** `/usr/local/bin`。
>
> ⚠️ 这些位置是**所有前端共享的唯一落点**（Python CLI / Swift CLI / GUI / MCP）：
> 共存、写入权与隔离手段见 [`frontends.md`](frontends.md) §2–§4。

---

## 3. 安装记录 `install.conf`（复用 Python 规范）

格式：**key=value 文本**（非 JSON）。沿用 Python `InstallManifest` 字段，并扩展 `surface` 等。

| 字段 | 必填 | 说明 |
|:--|:--:|:--|
| `tool` | ✅ | 固定 `orzmc` |
| `schema` | ✅ | 记录格式版本（整数） |
| `platform` | ✅ | 如 `macos-arm64` / `linux-x86_64` / `windows-x86_64` |
| `install_dir` | ✅ | 二进制所在目录 |
| `binary` | ✅ | 二进制绝对路径 |
| `source` | | 来源（版本 tag / 本地文件 / 渠道） |
| `path_file` | | 被修改的 shell 配置文件 |
| `path_line` | | 写入的 PATH 行（卸载按其精确匹配删除） |
| `root_dir` | ✅ | 游戏根目录 |
| `surface` | | `cli` / `gui`：**装出这条记录的前端**（语义与写入规则见 §3.1） |
| `completion_file` | | 补全脚本路径；由 `completion install` 写入，`uninstall` 据此删除（P ✅ / S ✅） |

- **PS 5.1 写 BOM** → 读取一律 `utf-8-sig`（沿用 Python 约定）。
- 可选字段为空则不写行。

### 3.1 `surface` 语义与写入规则

`surface` 回答一个问题：**PATH 上的 `orzmc` 是哪份前端装上去的？**（[`frontends.md`](frontends.md) F1/F2 的身份判断依据）

| 项 | 规则 |
|:--|:--|
| 取值 | `cli` / `gui`；**缺失 = 未知**（兼容旧记录，不得据此报错） |
| 语义 | 只是「这条安装记录的写入者」，**不是** GUI 应用本体登记：`.app` / dmg / appcast 的安装**不写** `install.conf` |
| 写入 | 安装器（含 GUI 内触发的安装）**必须**写；`update` **保留原值不改写**（升级不改变"谁装的"） |
| 选择 | 安装器读环境变量 `ORZMC_SURFACE`（缺省 `cli`，接受 `gui`）；GUI 以其为 `gui` 调用官方安装器 |
| 读取 | 缺失容忍；**不得**用文件名/大小推断前端身份（F1） |

> GUI 侧的「安装 CLI」入口只是**调用官方安装器**（Python / Swift 任一通道），
> 不复制安装逻辑——因此 `surface=gui` 也意味着"这条记录由 GUI 触发安装"，
> 而 `source` 仍指向真实发布通道（`OrzMC/OrzPythonMC` 或 `OrzMC/OrzMCKit`）。

---

## 4. PATH 集成（Shell 自动识别，无 sudo）

| 步骤 | 规范 |
|:--|:--|
| 选择 rc 文件 | 按 `$SHELL`：zsh→`~/.zshrc`，bash→`~/.bashrc`，其余→`~/.profile` |
| 写入行 | `export PATH="<install_dir>:$PATH"` |
| 幂等 | 运行期 `case ":$PATH:"` 判已在；写前 `grep -Fqx` 判行重复 |
| 卸载 | `grep -Fvx` 删精确行（仅当行存在才写回） |
| 关闭 | `--no-modify-rc` / `ORZMC_NO_RC=1` |
| Windows | 追加到 **User PATH** 环境变量（`;` 分 token 判重）+ 广播 `WM_SETTINGCHANGE` |

> 若 `$PATH` 已含 `install_dir`，**不修改** rc（只需新开 shell 即可用）。

---

## 5. Shell 补全安装（用户要求）

**两层**：(a) 用户随时可 `orzmc completion install`（行为契约见 [`cli-surface.md`](cli-surface.md) §4.5）；
(b) 安装器**应当**在装完 CLI 后自动调用一次（免去用户手动一步）。

| shell | 落点 | 额外动作 |
|:--|:--|:--|
| bash | `~/.local/share/bash-completion/completions/orzmc` | 装了 bash-completion 会自动加载；否则幂等追加一行 `source` 到 `~/.bashrc` |
| zsh | `~/.zsh/completions/_orzmc` | 必须确保 `fpath` 含该目录（幂等追加一行带 `orzmc` 标记） |
| fish | `~/.config/fish/completions/orzmc.fish` | 自动加载，无需 rc |
| powershell / pwsh | —（只生成脚本） | 不落盘；`install` 明确报 `E_UNSUPPORTED`，提示手动加入 `$PROFILE` |

- **禁止**：改 PowerShell 执行策略（`Set-ExecutionPolicy`）、重写用户的 rc 文件、做 shell 进程探测
  （冻结/沙箱环境下不可靠，见 `cli-surface.md` §4.5）。
- 生成源：`orzmc completion <shell>`（同一份 `capabilities`，两套实现内容等价）。
- **登记**：落盘后把路径写入 `install.conf` 的 `completion_file`，`uninstall` 按它删除（§9 / `frontends.md` F2）。
- 关闭：安装器 `--no-completion`。

| 项 | Python | Swift |
|:--|:--|:--|
| `orzmc completion install`（幂等 + 登记） | ✅ | ✅ |
| 安装器自动装补全 | ✅（Unix `docs/install.sh` 装完即调用） | ✅（`scripts/install.sh` 装完即调用） |
| 安装器关闭开关 | ✅ `--no-completion` / `ORZMC_NO_COMPLETION=1` | ✅ `ORZMC_NO_COMPLETION=1` |
| 安装器写 `completion_file` | ✅（Unix） | ✅ |
| 安装器 e2e 覆盖 | ✅（`scripts/accept_selfupdate.py` 3b 步骤） | —（安装器脚本由 release 流程跑） |

> 现状说明（2026-10-18 补齐）：
> - **Unix 两侧**都自动装补全并登记 `completion_file`；`--no-modify-rc` / `ORZMC_NO_RC=1`
>   会**一并跳过补全**（该开关承诺不碰 shell 配置，而补全可能补一行 rc）。
> - **Windows**：`install.ps1` 解析 `-no-completion`，但按 `frontends.md` F6
>   （powershell/pwsh 只生成脚本、不落盘）**不调用** `completion install`，因此也不写
>   `completion_file` —— 这是规范要求的行为，不是缺口。
> - 旧版二进制没有 `completion` 子命令时，安装器静默跳过，不影响安装。

## 6. 自升级 `orzmc update`（复用 Python 规范）

| 项 | 规范 |
|:--|:--|
| 语义 | `update` = 升级**工具自身**；`remove/list` = 游戏版本；`uninstall` = 卸载工具 |
| 版本解析 | 首选 GitHub REST `releases/latest`；失败/限流回退**非 API 的 302** `releases/latest` 的 `Location` |
| 指定版本 | `-v/--version vX.Y.Z`（完全绕过 API，限流回退） |
| 校验 | 下载产物 magic 校验（ELF/Mach-O/PE；拒绝 HTML/JSON）+ sha256 |
| 落地 | **分离助手在父进程退出后**替换（PyInstaller/Swift 运行中自替换不安全）；暂存 `<install_dir>/.orzmc-update.tmp` 同卷原子 rename |
| 当前版本判定 | 以**运行中二进制**内嵌版本为准（`install.conf` 可能滞后） |
| 记录 | 升级后重写 `install.conf` |
| 托管拒绝 | pip/pipx/venv 托管一律拒绝，提示对应包管理器升级 |
| 渠道 | `release`（默认）/ `beta`（**已决引入**）：`orzmc update --channel beta`；beta 为预发布通道，与插件口径一致 |

- GUI 侧：走自己的更新通道（Swift `OrzAppUpdater` / appcast）；【待定】与 CLI 渠道口径对齐。

---

## 7. 跨面安装：GUI → CLI

**目标**：用户在 GUI 内一键获得命令行工具（无 sudo、自动 PATH、自动补全）。

| 步骤 | 规范 |
|:--|:--|
| 触发 | GUI 内「安装命令行工具」入口 |
| 动作 | 复用**同一安装逻辑**（下载 CLI 二进制 → 落 `install_dir` → PATH → 补全 → 写 manifest） |
| 权限 | 用户级，无 sudo |
| 记录 | `install.conf` 写 `surface=cli` |
| 反馈 | 安装后提示「重启 shell 或 `source <rc>` 即可使用 `orzmc`」 |

> 复用原则：GUI 不重新实现安装器，而是**调用/内嵌同一份安装逻辑与 manifest 契约**。

---

## 8. 跨面安装：CLI → GUI

**目标**：`orzmc app install/open/uninstall/status`，渠道可互相兜底。

| 子命令 | 作用 |
|:--|:--|
| `orzmc app install [--channel release\|appstore] [--version] [--yes]` | 安装图形应用 |
| `orzmc app open` | 打开已安装应用 |
| `orzmc app uninstall` | 卸载应用 |
| `orzmc app status` | 显示安装状态与渠道 |

**渠道与兜底**

| 渠道 | 来源 | 说明 |
|:--|:--|:--|
| `release`（默认） | **GitHub Release** 资产 | 下载 macOS 应用包（zip/dmg），sha256 校验 |
| `appstore` | App Store | 之后发布后支持；作为 `release` 不可达时的**兜底**，反之亦可 |

- **互相兜底**：某渠道网络不可达/失败时，自动尝试另一渠道并提示；`--channel` 可强制。
- **安装落点**：macOS 用户级 `~/Applications`（免 sudo，`release` 渠道）；App Store 渠道由系统装到系统位置。
- **App Store 渠道细节**：通过 `macappstore://` URL（或 `mas`）打开产品页，**需用户交互**（Apple ID）；CLI 只负责引导，**不做静默安装**。
- **`app open`**：`open -a` 打开应用（macOS）。
- **非 macOS 平台（normative）**：`app install / open / uninstall / status` **一律**返回
  `E_UNSUPPORTED`（退出码 1、日志走 stderr、`--json` 时 `ok:false`、`data:null`），消息固定为：

  ```
  「orzmc app」仅支持 macOS;当前平台不支持,请从 Release 下载应用包
  ```

  即：**不假装成功**（不许 `ok:true` + 空 path）、**不降级成 `E_RUNTIME`**（那不是运行时故障，
  是平台边界）、**不联网**（不要先去查 release 再报错）。两侧实现必须逐字一致，
  由 `scripts/accept/cli.py` 的 `contract/app-unsupported-outside-macos` 用例在 Linux/Windows CI 上兜住。
- **appcast 口径对齐**：GUI 自更新走 appcast（Swift `OrzAppUpdater`）；`orzmc app install/update` 与 appcast **必须引用同一 App 版本号与产物**，避免两套版本源打架。

---

## 9. 卸载与安全护栏（复用 Python 规范）

| 场景 | 规范 |
|:--|:--|
| `orzmc uninstall` | 删二进制 → 还原 PATH → 删补全 → `rmdir` 空目录 → 删 manifest；游戏数据默认保留 |
| `--remove-root` | 连游戏根目录一并删除 |
| `--yes` | 免确认（脚本化）。**非交互调用必须带它**，否则 `E_CANCELLED`（130）且不做任何修改（`frontends.md` F2 / `behavior.md` B9） |
| **开发环境护栏** | 路径含 `.venv`/`venv`/`env`/`site-packages`/`dist-packages`/`_MEI*` 或 `_MEIPASS` 同目录 → 拒绝；`--force` 放行 |
| **pip/pipx 托管** | 二进制旁有 `*.dist-info` 或路径含 site-packages → 不删，提示用 pip 卸载 |
| **只删自登记内容** | 只 `rmdir` **空**目录，绝不递归删共享目录（如 `~/.local/bin`） |
| 运行中二进制 | 删除必须是**最后一步**；Windows 锁定则 `rename` + 重启后删除 |

---

## 10. 平台能力矩阵

| 能力 | macOS | Windows | Linux | iOS |
|:--|:--:|:--:|:--:|:--:|
| CLI 独立安装 | ✅ | ✅ | ✅ | ❌（不适用） |
| GUI 应用 | ✅ | 🔜 计划中（未实施） | 🔜 计划中（未实施） | ✅ |
| GUI → 安装 CLI | ✅ | 🔜 计划中 | 🔜 计划中 | ❌（系统限制） |
| CLI → 安装 GUI | ✅（`~/Applications`） | 🔜 计划中 | 🔜 计划中 | ❌ |
| 双渠道兜底（Release ↔ App Store） | ✅ | —（无 GUI） | —（无 GUI） | —（无 CLI） |

> **红线**：能力不支持时**显式报"该平台不支持"**，不静默失败。

---

## 10.1 运行时分发（wrapper 通道，M3）

> 目标（`docs/two-cli-strategy.md` §5.1 M3）：**PyPI 上的 `orzmc` 只做发行通道**——安装/升级
> Swift 实现的真身并**转发**命令，功能语义仍然只有一份（Swift 侧）。

**角色划分（对 F1 的裁定）**

| 角色 | 路径 | 谁写 | 说明 |
|:--|:--|:--|:--|
| **launcher（shim）** | `${XDG_BIN_HOME:-$HOME/.local/bin}/orzmc`（Windows `%LOCALAPPDATA%\Programs\orzmc\orzmc.exe`） | `pip install orzmc-app` | PATH 上的入口；**不含任何命令语义** |
| **payload（真身）** | `<stateDir>/bin/orzmc`（Windows `<stateDir>\bin\orzmc.exe`） | shim（首次运行或 `orzmc runtime install`） | 真正干活的 Swift 二进制 |
| 安装记录 | `<stateDir>/install.conf` | 写 payload 的一方 | 记 `binary=<payload>`、`channel=wrapper`、`version=<真身版本>` |

F1「PATH 上只有一个 `orzmc`」仍然成立：**只有 launcher 在 PATH 上**，payload 不在 PATH。
两者是不同路径、不同职责，因此不构成"同时安装两份实现"。

**开关（软切，默认关闭）**

| 变量 | 值 | 行为 |
|:--|:--|:--|
| `ORZMC_RUNTIME` | 未设置 / `python` | 走 Python 实现（**当前默认**，存量行为不变） |
| `ORZMC_RUNTIME` | `swift` | 走 shim：解析/安装真身 → **转发** argv 与退出码 |

切默认是单独的产品决策（D-M3-1），需要一版带「升级须知」的迁移窗口，不在本阶段。

**资产与校验**

- 真身来自 **`OrzMC/OrzMCKit` 的 release**，资产名沿用 Swift 侧约定：
  `orzmc-<os>-<arch>`（macOS/Linux）、`orzmc-windows-<arch>.zip`（Windows，含运行时 DLL）。
- **必须**用同一 Release 的 `SHA256SUMS` 校验（缺失或校验失败 → `E_VERIFY`，不落盘）。
- Windows 的 zip 解到 `<stateDir>/bin`，`orzmc.exe` 与 DLL 同行（缺 DLL 会 `STATUS_DLL_NOT_FOUND`）。
- 落盘是**原子替换**（临时目录 + rename），失败不得破坏已有可用真身。

**转发语义（`ORZMC_RUNTIME=swift` 时）**

- argv **原样**透传（含全局选项位置、`--json`）；
- stdin / stdout / stderr 直连，不改写内容（`--json` 信封由真身产出）；
- 退出码**等价转发**（含 `130` 取消语义）；
- 信号：POSIX 上 `execv` 直接用真身替换进程（最干净）；Windows 上 `subprocess` 转发并把 `Ctrl-C` 传下去；
- 真身缺失且无网络 → `E_NETWORK`，提示手动安装或 `ORZMC_RUNTIME=python` 回退；
- **版本号**：`orzmc --version` 报**真身**版本；launcher 版本只在 `orzmc runtime status --json` 里以
  `wrapper` 字段暴露（避免两套版本打架）。

**与「原生安装」共存（优先级，normative）**

同一台机器上可能同时存在两种真身来源：① 用户用 `install.sh` / `install.ps1` 装的**原生** Swift 版
（在 `~/.local/bin`，`source` 指向 `OrzMC/OrzMCKit`）；② 本通道自管的副本（`<stateDir>/bin`）。

| 规则 | 说明 |
|---|---|
| **R1 复用优先** | 若 `install.conf` 记录的真身 `source` 指向 `OrzMC/OrzMCKit`（或 `channel=wrapper`）**且文件可执行** → 直接 `exec` 它，**不再下载、不再写记录** |
| **R2 绝不复用 Python 实现** | `source` 指向 `OrzPythonMC` 时不得复用——那会把命令转发回 Python，等于自己转自己 |
| **R3 记录不覆盖** | 复用时不改写 `install.conf`；只有在**没有可用真身**、本通道自己下载并落盘时才写记录（`channel=wrapper`） |
| **R4 记录失效则回退** | 记录里的 `binary` 不存在或不可执行 → 视为无真身，走「自己装一份」 |
| **R5 单份优先** | `orzmc runtime install` 在 R1 成立时是 **no-op**（打印复用了哪份），不制造第二份 13–35 MB 副本 |

> 这样 F1/F2/F3 仍成立：PATH 上只有一个 `orzmc`（launcher）；`install.conf` 仍是唯一事实；
> `update` 仍只替换自己那份。`orzmc runtime status --json` 的 `reused` 字段直接暴露「是否复用了原生安装」。

**管理命令（本阶段，Python 侧 lead）**

| 命令 | 行为 |
|:--|:--|
| `orzmc runtime status [--json]` | 报 `{enabled, installed, version, path, source}`；不联网 |
| `orzmc runtime install [--version vX.Y.Z] [--yes]` | 下载 + 校验 + 落盘 + 写 `install.conf`（`channel=wrapper`） |

- 台账（`docs/spec/parity.json`）：`runtime` 记为 **Python lead / Swift `na`**——它是发行通道的职责，
  Swift 侧不需要等价实现（真身自己就是被转发方）。
- 上线时**不**下线 PyPI 的 6 平台 PyInstaller 资产（D-M3-4 未拍板）。

---

## 11. 吸收 Swift 的亮点

| 亮点 | 出处 | 处理 |
|:--|:--|:--|
| `plugin`：Hangar 搜索 / 下载服务端插件 | Swift `PluginCommand` | **纳入** CLI 命令面（见 `cli-surface.md` §4.3） |
| 下载完成后 `open` 目标目录 | Swift `PluginCommand` | 建议纳入（`--open` 或默认提示），【待定】 |
| 进度条 / 加载条 UI | Swift ConsoleKit | 纳入进度契约（见 `behavior.md`） |
| 正版授权（`--auth`） | Swift `ClientCommand` | **纳入**：契约见 [`auth.md`](auth.md)（设备码流程 + 令牌持久化 + 安全要求；待实现） |
| App 自更新（appcast） | Swift `OrzAppUpdater` | GUI 侧保留，口径与 CLI 对齐【待定】 |

---

## 12. 与实现的差异（迁移方向）

| 项 | Python | Swift | 规范 |
|:--|:--|:--|:--|
| 安装记录 | `install.conf`（完整） | App 安装器/`OrzAppUpdater`（部分） | 复用 Python 格式，Swift 对齐 |
| 自升级 | 完整（延迟替换） | 无 CLI 自升级 | Swift 补（发版链路已就绪） |
| 补全 | 可生成但未开启 | 无 | 两者补 |
| `app` 跨面 | 无 | 无 | 两者补 |
| PATH 还原 | 完整 | 部分 | 对齐 |

> 2026-10-14：Swift 侧已建**发版链路**（release-please + `release.yml` → `orzmc-macos-<arch>` + `SHA256SUMS` +
> `scripts/install.sh`，见 `OrzMCKit#6`）；`update` / `uninstall` / `app` / `completion` 命令待实现。

> 落地与勾选见 [`product-unification-plan.md`](../product-unification-plan.md) Phase 4。
