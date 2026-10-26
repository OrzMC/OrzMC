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
| 构建 `orzmc`（本机） | `lipo -archs` = arm64；`otool -l` → **`minos 13.0`** ✅ |
| 官方发布包 `OrzMC-official-0.1.5.app` | `lipo -archs` = **`x86_64 arm64`**，`minos 14.0` ✅ |

**CI 门禁（2026-10-26 已生效并首次跑绿）**

| 仓库 | job | 断言 | 首次结果 |
|---|---|---|---|
| `swift/app` | `intel` | `xcodebuild build -destination 'platform=macOS,arch=x86_64'` | ✅ **`BUILD SUCCEEDED`**（3m18s）→ **GUI 的 Intel 切片能编过** |
| `swift/lib/OrzMCKit` | `platform` | 声明下限 = 13 / native `minos` ≤ 13 / `swift build --arch x86_64` | ✅ `声明下限: macOS 13`、`orzmc minos = 13.0`、`x86_64 产物架构 = x86_64`（4m02s） |
| 父仓库 | `verify`（ubuntu） | `scripts/dev/check-platforms.sh --declarations-only` | ✅ 分层一致（GUI 14 / 逻辑层 ≤13 / 无写死 ARCHS） |

> runner 上 **Rosetta 2 已预装**（日志里是 `Rosetta 已安装`）；两个 job 都保留了"缺失就装"的分支。

Intel 相关的运行时证据（代码层面）：

| 环节 | 实现 | 位置 |
|---|---|---|
| JRE 下载 | Adoptium 按架构：`arch=x64` / `aarch64` | `OrzSwiftKit/RuntimeKit/AdoptiumQuery.archName` |
| MC natives | 按 `os.arch` 过滤 rules（Intel 拿 `natives-macos`） | `OrzMCKit/Game/Plan/ClientLaunchPlan.swift:382` |
| 自升级资产 | `#if arch(arm64)` 选资产名 | `OrzMCKit/OrzMC/SelfUpdate.swift` |
| 内嵌 Sparkle | universal（`x86_64 arm64`） | `OrzMC.app/Contents/Frameworks/Sparkle.framework` |

---

### 3.1 真机实测（Intel + macOS 13）

维护者提供的真机（SSH 别名 `pro`）：

| 项 | 值 |
|---|---|
| 机型 | **MacBookPro12,1**（13" 2015） |
| CPU | Intel Core i5-5257U @ 2.70GHz（Broadwell，双核） |
| 内存 | 16 GB |
| 系统 | **macOS 13.7.8**（22H730） |
| SSH | `ssh pro`（`bot@192.168.0.35`），验证用目录 `~/orzmc-smoke` |

**结果（2026-10-26）**

| 层 | 验证内容 | 结果 |
|---|---|---|
| **分发层**（Python CLI） | 官方一键安装器 `curl … install.sh \| sh --dir … --no-completion --no-modify-rc` | ✅ 自动选中 **`orzmc-macos-x86_64`**（`file` → `Mach-O 64-bit executable x86_64`） |
| 分发层 | `orzmc --version` / `--json capabilities` / `list`（2.18.1） | ✅ 启动 ~1.2s，全部正常 |
| **逻辑层**（Swift CLI，旧版） | 本机已有真身 `~/.local/state/orzmc/bin/orzmc` 0.18.0 | ✅ `x86_64`、`minos 13.0`、`--version`/`capabilities`/`list`/`app status` 正常 |
| 逻辑层（Swift CLI，**main 构建**） | 下载 CI `orzmc-x86_64-macos13` artifact（`ci` 的 `platform` job）→ scp 上去跑 | ✅ 0.21.0、`x86_64`、`minos 13.0`，`--version` **21ms** |
| **GUI** | 官方 0.1.5 包 | ⛔ **启动失败（符合预期）**：`dyld: … (built for macOS 14.0 which is newer than running OS)` |
| **分发层 · 真正启动游戏** | `orzmc client -v 1.20.1 -u guest --root-dir …` | ✅ **进到主菜单**：`下载 Temurin JRE 17 (mac/x64)` → 窗口 `Minecraft 1.20.1`（854×508）、`OpenAL initialized`、纹理图集全建、CPU ~30% |

**顺带确认的两件事**

1. **GUI 的 Intel 切片是真的**：0.1.5 包 `lipo -archs` = `x86_64 arm64`（只是 minos 14.0，Ventura 起不来）。
2. **逻辑层在 13 上只能"跑"，不能"编"**：Ventura 最高装 Xcode 15（Swift 5.9/5.10），
   而 `OrzMCKit` 是 `swift-tools-version:6.0` → 真机没有可用工具链。
   所以真机验证一律用 CI 的 `platform` job 产物（artifact `orzmc-x86_64-macos13`，保留 14 天）。

**启动细节（1.20.1 vanilla，离线 `guest`）**

| 项 | 值 |
|---|---|
| JRE | 日志 `下载 Temurin JRE 17 (mac/x64)`；`file java` → **`Mach-O 64-bit executable x86_64`**；`java -version` → Temurin 17.0.20.1 |
| natives | `versions/1.20.1/client/natives/` 里 `liblwjgl.dylib` / `libglfw.dylib` / `libopenal.dylib` 全是 **`x86_64`** |
| 体积 / 耗时 | 合计 866 MB（JRE 109 MB + 游戏 757 MB）；从启动到窗口出现约 **1.5 分钟**（千兆内网） |
| 渲染 | `Backend library: LWJGL 3.3.1`、`OpenAL initialized on device CoreAudio Default`、各纹理图集创建成功 |
| 已知无害项 | `Failed to verify authentication … 401`（离线 `guest` 启动的预期日志）、`screencapture` 抓 GL 窗口得到黑图（不影响判定，用窗口标题 + CPU + 日志作证） |

**结论：Intel + macOS 13 这条路径**（安装器 → 分发层 → JRE/natives 选架构 → 进游戏）**全链路跑通**。
GUI 在这台机器上按设计不可用（§4）。

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
| 逻辑层能在 macOS 13 上**运行** | 用 CI 产物：`gh run download <run> --name orzmc-x86_64-macos13` → scp 到真机 → `orzmc --version` | ✅ **Intel 真机已验**（0.18.0 与 main 的 0.21.0，见 §3.1） |
| 逻辑层能在 macOS 13 上**构建** | 需要 Swift 6 工具链；Ventura 只能装 Xcode 15（Swift 5.10） | ❌ 不可行（`swift-tools-version:6.0`）；构建在 CI（Xcode 26）完成 |
| Intel 编译通过（GUI） | CI `swift/app` 的 `intel` job（`-destination arch=x86_64`） | ✅ 已跑绿（`BUILD SUCCEEDED`） |
| Intel 编译通过（CLI） | CI `swift/lib/OrzMCKit` 的 `platform` job（`swift build --arch x86_64`） | ✅ 已跑绿（`x86_64 产物架构 = x86_64`） |
| Intel 编译（本机复跑） | `./scripts/dev/check-platforms.sh --arch`（需 Rosetta：`softwareupdate --install-rosetta --agree-to-license`） | ⚠️ 本机无 Rosetta → 本地跳过（CI 已覆盖） |
| Intel 运行时行为（CLI/GUI 能不能起） | 真机 `ssh pro`（MacBookPro12,1 / macOS 13.7.8） | ✅ 已验：CLI 正常、GUI 按预期拒绝（§3.1） |
| Intel 运行时行为（真正启动游戏：JRE `x64` / natives `x86_64`） | 真机 `ssh pro` 跑 `orzmc client -v 1.20.1 -u guest`（离线，无需登录） | ✅ **已验**：JRE/ natives 均 `x86_64`，进到主菜单（§3.1） |
| 发布包是 Universal | `./scripts/dev/check-platforms.sh` 的分发审计（读已发布 `.app` 的 `lipo -archs`） | ✅ 0.1.5 已验 |

---

## 6. Intel 冒烟清单（有一台 Intel Mac 时照着做，约 20 分钟）

> 已有真机：`ssh pro`（MacBookPro12,1 / macOS 13.7.8 / 16 GB）。**第 1–6 步已在 2026-10-26 全部跑过**，
> 结论见 §3.1（离线 `guest` 即可，不需要正版登录；`--root-dir` 指到 `~/orzmc-smoke/minecraft` 收敛）。
> 验证目录约定：`~/orzmc-smoke`（含 866 MB 下载物，用完可 `ssh pro 'rm -rf ~/orzmc-smoke'`）。

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
