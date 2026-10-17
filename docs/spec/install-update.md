# 安装 / 自升级 / 跨面安装契约（Install & Update Contract）

> **状态**：草案 `specVersion 0.1` ｜ **最后更新**：2026-10-14
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
| `surface` | | `cli` / `gui`（**新增**，用于跨面识别；**两侧安装器尚未写入**，见 [`frontends.md`](frontends.md) §7） |
| `completion_file` | | 补全脚本路径（**新增**，卸载时一并清理） |

- **PS 5.1 写 BOM** → 读取一律 `utf-8-sig`（沿用 Python 约定）。
- 可选字段为空则不写行。

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

安装 CLI 时**自动安装补全**，使命令/参数可 Tab 补全。

| shell | 落点（示例，实现按平台确认） |
|:--|:--|
| bash | `~/.local/share/bash-completion/completions/orzmc` 或 source 到 rc |
| zsh | `~/.zsh/completions/_orzmc`（并确保 `fpath` 含该目录） |
| fish | `~/.config/fish/completions/orzmc.fish` |
| powershell | 追加 `Register-ArgumentCompleter` 到 `$PROFILE` |

- 生成源：`orzmc completion <shell>` 输出脚本（见 `cli-surface.md` §8）。
- 记录 `completion_file` 到 manifest，卸载时清理。
- 关闭：安装器 `--no-completion`。
- **实现要点**：Python（typer）需开启补全生成；Swift（ConsoleKit）需补生成器或内置静态脚本。

---

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
- **appcast 口径对齐**：GUI 自更新走 appcast（Swift `OrzAppUpdater`）；`orzmc app install/update` 与 appcast **必须引用同一 App 版本号与产物**，避免两套版本源打架。

---

## 9. 卸载与安全护栏（复用 Python 规范）

| 场景 | 规范 |
|:--|:--|
| `orzmc uninstall` | 删二进制 → 还原 PATH → 删补全 → `rmdir` 空目录 → 删 manifest；游戏数据默认保留 |
| `--remove-root` | 连游戏根目录一并删除 |
| `--yes` | 免确认（脚本化） |
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
