# 平台支持矩阵（macOS 版本 / 芯片架构）

> **状态**：现行 · **最后更新**：2026-10-26
> **适用**：OrzMC 的 GUI（`swift/app`）、Swift 逻辑层（`swift/lib/*`）、对外分发的 Python CLI（`python`）。
> 相关：[`two-cli-strategy.md`](two-cli-strategy.md)（分发口径）、[`product-architecture.md`](product-architecture.md)（分层模型）。

---

## 1. 结论（三句话）

1. **Intel 芯片：支持**。发布包是 Universal（`x86_64 + arm64`），运行时依赖全部按架构选取（JRE / MC natives / 自升级资产）。
2. **macOS 13（Ventura）：按层支持**。**逻辑层（`orzmc` CLI + Swift 库）钉在 macOS 13**；**GUI（OrzMC.app）要求 macOS 14**。
3. 这条边界是**有意的折中**，不是历史遗留：见 §4 为什么不做「GUI 降到 13」。

---

## 2. 矩阵

| 层 | 产物 | 最低 macOS | 架构 | 分发 |
|:--|:--|:--|:--|:--|
| **分发层** | Python `orzmc`（`python/`） | 任何能跑 Python 3.10+ 的系统 | 与系统无关 | ✅ **唯一对外分发** |
| **逻辑层** | Swift `orzmc` CLI（`swift/lib/OrzMCKit`） | **13.0** | arm64 / x86_64 | pre-release（不分发，见 two-cli-strategy §6） |
| **逻辑层** | Swift 库（MojangAPI / PaperMC / MCSManagerAPI / OrzSwiftKit / OrzAppUpdater / ExarotonAPI） | **13.0**（ExarotonAPI 10.15） | arm64 / x86_64 | 走各自仓库 |
| **GUI 层** | `OrzMC.app`（macOS） | **14.0** | Universal（x86_64 + arm64） | ✅ 随 Release 分发 |
| **GUI 层** | `OrzMC`（iOS） | iOS 17 / 18（见工程设置） | device + simulator | TestFlight/开发包 |

**机型含义**：macOS 14 Sonoma 覆盖 **2018 年及以后**的 Intel Mac（MBP/Air/mini 2018+、iMac 2019+、iMac Pro 2017、Mac Pro 2019）。更老的 Intel Mac 卡在 Ventura → 它们能用的部分是 **Python CLI / Swift CLI**，不是 GUI。

---

## 3. 证据（可复跑的检查）

```bash
# 一条命令看全貌（声明 + 产物 minos + 发布包架构）
./scripts/dev/check-platforms.sh

# 只查声明（Linux 也能跑；父仓库 CI 用这个）
./scripts/dev/check-platforms.sh --declarations-only

# 额外做 Intel 交叉编译（需要 Rosetta）
./scripts/dev/check-platforms.sh --arch
```

实测输出（2026-10-26，本机 Apple Silicon）：

| 检查 | 结果 |
|---|---|
| 7 个逻辑层包的 `Package.swift` 下限 | 6 个 `macOS 13` + ExarotonAPI `10.15` ✅ |
| `swift/app/Package.swift` | `macOS 14`（GUI，使用 `@Observable`）✅ |
| `MACOSX_DEPLOYMENT_TARGET` | `14.0` ✅ |
| `ARCHS` / `EXCLUDED_ARCHS` / `VALID_ARCHS` | 均**未写死** → Release 走 `ARCHS_STANDARD` = arm64 + x86_64 ✅ |
| `scripts/release-macos.sh` | 只有 `ARCHIVE_ONLY_ACTIVE_ARCH` 开关（默认不设）✅ |
| 构建 `orzmc` | `lipo -archs` = arm64；`otool -l` → **`minos 13.0`** ✅ |
| 官方发布包 `OrzMC-official-0.1.5.app` | `lipo -archs` = **`x86_64 arm64`**，`minos 14.0` ✅ |

Intel 相关的运行时证据（代码层面）：

| 环节 | 实现 | 位置 |
|---|---|---|
| JRE 下载 | Adoptium 按架构：`arch=x64` / `aarch64` | `OrzSwiftKit/RuntimeKit/AdoptiumQuery.archName` |
| MC natives | 按 `os.arch` 过滤 rules（Intel 拿 `natives-macos`） | `OrzMCKit/Game/Plan/ClientLaunchPlan.swift:382` |
| 自升级资产 | `#if arch(arm64)` 选资产名 | `OrzMCKit/OrzMC/SelfUpdate.swift` |
| 内嵌 Sparkle | universal（`x86_64 arm64`） | `OrzMC.app/Contents/Frameworks/Sparkle.framework` |

---

## 4. 为什么不做「GUI 降到 macOS 13」

GUI 的最小系统是 **14.0**，硬性卡点是 **Observation 宏**（`@Observable`，要求 macOS 14）：

| 依赖点 | 数量 |
|---|---|
| `@Observable` 模型类 | 16（app 14 + `OrzMCLauncher` 2） |
| `@ObservationIgnored` / `@Bindable` | 18 / 7 |
| `@Environment(Model.self)` 读取 | 23 |
| `.environment(model)` 注入 | 19 |
| 全仓 `ObservableObject` / `@Published` | **0**（已全部迁到宏） |

注意 `@Environment(_: T.Type)` 这个初始化器本身要求 macOS 14 —— 所以「给模型加 backport」不够，环境注入那一整套也要改回 `@EnvironmentObject`。

其余 14-only API 只是收尾工作（9 处 + 3 处预览）：`.defaultScrollAnchor` ×2、`ContentUnavailableView` ×4、
`.contentTransition(.symbolEffect)` ×1、`.onKeyPress` ×2。

**代价 vs 收益**：改造成本约 1–2 周（含回归风险：细粒度失效变全量刷新，控制台高频刷新可能掉帧），
收益只覆盖 2017 款及更老的 Intel Mac —— 而它们的 **CLI 已经可用**。因此决定：**逻辑层保 13，GUI 保 14**。

如果将来维护者判断收益足够，改造清单与估时见 §7。

---

## 5. 验收路径（谁在什么机器上验什么）

| 要验的 | 怎么做 | 现状 |
|---|---|---|
| 逻辑层能在 macOS 13 上构建/运行 | `swift build --package-path swift/lib/OrzMCKit --product orzmc`，然后 `otool -l` 看 `minos 13.0`；在 Ventura 机器/虚拟机上直接跑 | ✅ 构建与 minos 已验；**Ventura 实机运行未验** |
| Intel 编译通过 | `./scripts/dev/check-platforms.sh --arch`（需 Rosetta：`softwareupdate --install-rosetta --agree-to-license`）；或 CI 的 `intel` job | ⚠️ 本机无 Rosetta → 本地跳过；CI 已加 job |
| Intel 运行时行为 | 见 §6 冒烟清单，需一台 Intel Mac（或云 Mac） | ❌ **无机器，未验** |
| 发布包是 Universal | `./scripts/dev/check-platforms.sh` 的分发审计（读已发布 `.app` 的 `lipo -archs`） | ✅ 0.1.5 已验 |

---

## 6. Intel 冒烟清单（有一台 Intel Mac 时照着做，约 20 分钟）

以官方 Release 包为例（`OrzMC_x.y.z.dmg`）：

1. **系统信息**：`sw_vers`（应为 14.x）+ `uname -m`（应为 `x86_64`）+ `sysctl -n machdep.cpu.brand_string`（Intel）。
2. **架构**：`lipo -archs /Applications/OrzMC.app/Contents/MacOS/OrzMC` → 必须含 `x86_64`；
   `otool -l … | grep -A3 LC_BUILD_VERSION` → `minos 14.0`。
3. **能启动**：首次打开（Gatekeeper 公证检查）→ 主窗口出现，无崩溃、无「无法打开」。
4. **Java 运行时**：装一个版本 → `~/Library/Application Support/…/java/<major>/bin/java -version`
   应输出 **x86_64**（Adoptium `arch=x64`）。若是 `aarch64` 就是选错架构。
5. **Minecraft 启动**：启动一次，检查 `…/natives/` 里是 **x86_64** 的 `liblwjgl*.dylib`
   （不是 `arm64`），游戏能进主菜单。
6. **自升级**：`orzmc update` / app 内检查更新 → 下载的资产名应带 `x86_64`。
7. 记录结论到 `HANDOFF.md` §5（哪台机器、哪个版本、哪几步过了）。

---

## 7. 如果将来要把 GUI 降到 macOS 13（改造清单）

1. 16 个 `@Observable` 模型 → `ObservableObject` + `@Published`；23 处 `@Environment(Model.self)` → `@EnvironmentObject`；
   19 处 `.environment(model)` → `.environmentObject(model)`；7 处 `@Bindable` → `@ObservedObject`/`@Binding`。
   - 备选：`pointfreeco/swift-perception`（backport 到 macOS 10.15）——但环境注入仍要改，且给发布物引入第三方观察层，**不推荐**。
2. `swift/app/Package.swift` 的 `.macOS(.v14)` → `.v13`（5 个内部模块），`MACOSX_DEPLOYMENT_TARGET` → 13.0。
3. 收尾 9 处 14-only UI（§4 列表）+ 3 处 `@Previewable`。
4. 完整编译一轮，清理编译器报出的其余 14-only API；过 `check.sh` / `--ios` / `--ui`（73 + UI 用例）。
5. 验证：macOS 13 虚拟机（Apple Silicon 上可行）验 API 可用性；Intel 行为仍需真机。
6. 更新本文档 §2 矩阵与 `scripts/dev/check-platforms.sh` 里的断言（`GUI 14` → `GUI 13`）。

---

## 8. 维护约定

- **改动平台下限 = 改产品承诺**：动 `Package.swift` 的 `platforms:` 或工程的 `*_DEPLOYMENT_TARGET` 时，
  必须同步更新本文档 §2，并跑 `./scripts/dev/check-platforms.sh`。
- 逻辑层**不许**抬到 14+（`check-platforms.sh` 会红）；GUI 不许静默降到 13（会编不过，脚本也会红）。
- 不许写死 `ARCHS` / `EXCLUDED_ARCHS` / `VALID_ARCHS` —— 那会让发布包丢掉 Intel 或 Apple Silicon 切片。
- 新增依赖时看一眼它的 `platforms:`：不得超过该层的下限（Sparkle 12、其它 ≤13，均有记录）。
