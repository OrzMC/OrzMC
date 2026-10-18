# Windows 移植（Phase 6.5）——探针结论与路线

> **状态**：编译+冒烟已过，**W1/W2 已完成**；W3–W6 待做 · **最后更新**：2026-10-18
> 关联：`docs/product-unification-plan.md` D14 / Phase 6.5，`docs/iteration-efficiency.md`

---

## 1. 结论（一句话）

**A 路线（全量 Windows 支持）可行**：Swift `orzmc` 已能在 `windows-2022 + Swift 6.2` 上
**编译通过的 `.exe`**，`--version` / `--json capabilities` / `--json list` / `completion bash` 均可运行。
剩余是**平台细节收尾**（约 5 项），不是"生态不可用"。

## 2. 探针实测（7 轮，`windows-probe.yml`）

| 轮 | 失败点 | 根因 | 处理 |
|---|---|---|---|
| 1 | `Invalid manifest … while building module 'ucrt'` | Windows SDK 的 module map 与工具链版本不匹配 | 开 `update-sdk-modules: true`（gha-setup-swift） |
| 2 | `Tool 'swiftlint' is not supported on the target platform` | SwiftLint artifactbundle 无 Windows 产物，且**插件失败会中止构建** | `OrzSwiftLint 0.0.9`：Windows 跳过 lint |
| 3 | `missing inputs: …GeneratedSources/{Server,Client,Types}.swift` | SwiftPM 在 Windows 上建插件输出符号链接失败 | 开开发者模式（`AllowDevelopmentWithoutDevLicense=1`） |
| 3b | 同上（仍失败） | SwiftPM 6.0 在 Windows 上插件输出处理有缺陷 | **换 Swift 6.2**（问题消失） |
| 4 | `STL1000: Unexpected compiler version, expected Clang 20 or newer` | `windows-2025`（VS 18）的 STL 比工具链新 | 用 `windows-2022`（VS 2022） |
| 5 | `no such module 'Crypto'` | `swift-crypto` 依赖条件只有 `.linux` | `[.linux, .windows]`（`OrzSwiftKit#14`、`MojangAPI#10`） |
| 6 | `cannot find 'SIGKILL'` / `cannot find 'kill'` | `ManagedProcess` 用 POSIX 信号；`JokerKits.Shell` 整块被 `#if !os(Windows)` 关掉 | `OrzSwiftKit#15`：Windows 走 `terminate()` / `tasklist` / `taskkill` / `powershell` |
| 7 | `run` 重载歧义（`Bool` 无 `contains`） | async 上下文选中了 `async -> Bool` 重载 | `OrzSwiftKit#16`：显式标注类型 |
| 8 | — | — | **`Build of product 'orzmc' complete!`（465s）+ 冒烟通过** ✅ |

### 冒烟结果（`windows-2022` / Swift 6.2）

```
orzmc 0.14.0                      ✅（含合规声明）
--json capabilities               ✅ 完整信封（13 命令 / 退出码 / 枚举）
--json list                       ✅ {"versions":[]}
completion bash                   ⚠️ 函数名带完整 .exe 路径（见 §3.1）
```

## 3. 剩余工作（按优先级）

### 3.1 必须做（不做就不算"支持 Windows"）

| # | 项 | 现状 | 做法 |
|---|---|---|---|
| ~~W1~~ | ~~`completion` 脚本函数名~~ | ☑ **已修**（`OrzMCKit#63`）：`programName(from:)` 切 `/` 与 `\`、去 `.exe`；Windows 实测输出 `function _orzmc()` | 函数名固定 `orzmc` |
| ~~W2~~ | ~~状态目录 / 游戏根~~ | ☑ **已修**（`OrzMCKit#63`）：新增 `Game.StatePaths`（平台判定可注入 → 可在 macOS/Linux 上单测），`InstallManifest`/`AuthStore`/`GamePlan.defaultRoot` 全部改走它 | Windows → `%LOCALAPPDATA%\orzmc`、`%USERPROFILE%\minecraft` |
| W3 | 自升级 | `SelfUpdate` 写 `/bin/sh` 脚本替换自身 | Windows → 重命名旧 exe + 移动新 exe（`FileManager.replaceItemAt`） |
| W4 | 备份 `zip` | `PlatformTools.zip()` 在 Windows 返回 `nil` → 明确报错 | Windows 用系统自带 `tar.exe -a -c -f x.zip`（10+ 内置） |
| W5 | 安装器 | 只有 `install.sh` | 写 `install.ps1`（资产 `orzmc-windows-<arch>.exe`、PATH、`completion install` 按 F6 只提示脚本） |
| W6 | CI + 发布 | 只有 macOS/Linux | `ci.yml` 加 `windows` job（`windows-2022` + Swift 6.2）；`release.yml` 加 Windows 资产 |

### 3.2 可选（可先以 `E_UNSUPPORTED` 收口）

- `orzmc app …`：已按 `E_UNSUPPORTED`（macOS 专属）；
- 命名管道/软链接（`server --symlink`）：Windows 需管理员或开发者模式 → 给 `E_UNSUPPORTED`；
- `completion install`：Windows/PowerShell 按 F6 **只生成脚本**，不落盘（现状已如此）。

## 4. 关键前提（必须写进 CI/发布）

| 项 | 值 | 原因 |
|---|---|---|
| runner | **`windows-2022`** | `windows-2025` 的 VS 18 STL 要求 Clang 20+，当前 Swift 工具链不满足 |
| Swift | **6.2** | 6.0 的 SwiftPM 在 Windows 上处理构建插件输出有缺陷（`missing inputs`） |
| 安装器开关 | `update-sdk-modules: true` | 否则依赖的 `Package.swift` 都编译不了 |
| 开发者模式 | `AllowDevelopmentWithoutDevLicense=1` | SwiftPM 需要建符号链接 |

## 5. 成本对比（更新后的 A vs B）

| 路线 | 剩余工作 | 估计 |
|---|---|---|
| **A. Windows 全量** | W1–W6（6 项，均为平台细节） | 中小：编译已通，剩下是路径/升级/安装器/CI |
| **B. Windows 走 Python** | 0（但永久保留一条窄口径双实现） | 小，但与 D14 目标相悖 |

**建议走 A**：探针证明"能编译、能跑"，剩余项都是确定性的工程量。
