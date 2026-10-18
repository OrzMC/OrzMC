# Windows 移植（Phase 6.5）——探针结论与路线

> **状态**：**W1–W6 全部完成**，Windows 资产已随 `v0.15.0` 发布并在真机（无 Swift 环境）验证通过 · **最后更新**：2026-10-18
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
| ~~W3~~ | ~~自升级~~ | ☑ **已完成**：资产名/平台标签按平台（顺带修了 Linux 上会去下 macOS 二进制的 bug）、魔数按平台（Mach-O/ELF/PE）、Windows「改名旧 exe → 放新 exe」+ 失败回滚 | — |
| ~~W4~~ | ~~备份/解压~~ | ☑ **已完成**：`PlatformTools` 升级为「命令+参数」（`zip`/`unzip` ↔ `tar.exe -a -c -f` / `-x -f` / `-x -O`） | — |
| ~~W5~~ | ~~安装器~~ | ☑ **已完成**：`scripts/install.ps1`（zip 资产、SHA256、PE 魔数、用户 PATH、`install.conf`、F6 提示、`-uninstall`） | — |
| ~~W6~~ | ~~CI + 发布~~ | ☑ **已完成**：`ci.yml` 的 `windows` job（build + 冒烟 + 98 单测，硬门禁）、`release.yml` 的 `build-windows` | — |

### 3.2 可选（可先以 `E_UNSUPPORTED` 收口）

- `orzmc app …`：已按 `E_UNSUPPORTED`（macOS 专属）；
- 命名管道/软链接（`server --symlink`）：Windows 需管理员或开发者模式 → 给 `E_UNSUPPORTED`；
- `completion install`：Windows/PowerShell 按 F6 **只生成脚本**，不落盘（现状已如此）。

## 3.3 发布形态：为什么 Windows 是 zip 而不是单 exe

`--static-swift-stdlib` **并不能**在 Windows 上把运行时静态链进去。`dumpbin /dependents` 实测产物仍依赖：

```
swiftCore.dll  Foundation.dll  FoundationNetworking.dll  swiftCRT.dll  swiftWinSDK.dll
swiftDispatch.dll  dispatch.dll  BlocksRuntime.dll  swift_Concurrency.dll  …
```

真机（**没装 Swift** 的 Windows）上直接 `0xC0000135 = STATUS_DLL_NOT_FOUND`，连 `--version` 都跑不了。

因此：**资产 = `orzmc-windows-<arch>.zip`**（exe + 32 个运行时 DLL，约 33 MB），
`install.ps1` 解压到安装目录，`orzmc update` 用内置 `tar.exe` 从 zip 里取 `orzmc.exe` 替换
（DLL 不随每次升级变化）。

## 3.4 真机验收（2026-10-18，`ssh win`，PS 5.1，**未安装 Swift**）

```
install.ps1 -version v0.15.0 -dir E:\orzmc-verify\bin -no-modify-rc -no-completion
  → 下载 zip → SHA256 校验通过 → 解压 32 个 DLL + orzmc.exe → install exit=0

干净 PATH（摘掉所有 Swift 目录）:
  orzmc --version            → orzmc 0.15.0            exit=0
  orzmc --json capabilities  → ok=true, commands=13
  orzmc completion bash      → function _orzmc()        ✓
install.conf                 → platform=windows-x86_64 / version=0.15.0 / surface=cli
```

## 4. 关键前提（必须写进 CI/发布）

| 项 | 值 | 原因 |
|---|---|---|
| runner | **`windows-2022`** | `windows-2025` 的 VS 18 STL 要求 Clang 20+，当前 Swift 工具链不满足 |
| Swift | **6.2** | 6.0 的 SwiftPM 在 Windows 上处理构建插件输出有缺陷（`missing inputs`） |
| 安装器开关 | `update-sdk-modules: true` | 否则依赖的 `Package.swift` 都编译不了 |
| 开发者模式 | `AllowDevelopmentWithoutDevLicense=1` | SwiftPM 需要建符号链接 |
| 打包 | `orzmc.exe` + Swift 运行时 DLL → **zip** | 单 exe 在无 Swift 的机器上 `STATUS_DLL_NOT_FOUND` |
| 验证方式 | 解压到临时目录 + **清掉 PATH 里的 Swift 目录** 再跑 | CI runner 自带 Swift，不这样测等于没测 |

## 5. 成本对比（更新后的 A vs B）

| 路线 | 剩余工作 | 估计 |
|---|---|---|
| **A. Windows 全量** | ☑ **已完成**（v0.15.0 起有 `orzmc-windows-x86_64.zip`，真机验证通过） | — |
| B. Windows 走 Python | 不需要了 | — |
