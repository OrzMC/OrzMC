# 两套 CLI 的实测对比（Swift 实现 vs Python 实现）

> **状态**：生效中（实测快照 + 可复跑脚本；2026-10-20 更新：Linux 自包含已修）· **最后更新**：2026-10-20
> **结论先说**：**没有全面更优的一方** —— Swift 在「运行时效率」上碾压（**25–70× 启动、~9× 内存**），
> Python 在「独立可运行性 / 发布成本 / 迭代摩擦」上明显更好。**并行期按能力分工**（见 §7），
> 但 Swift 侧有两个**硬伤必须先修**（§6.1：Linux 资产不自包含；`verify-linux` 在"自带运行时"的容器里验）。
>
> 复跑：`python3 scripts/bench/cli.py --a "Python=…" --b "Swift=…"`（见 §8）

---

## 1. 方法与口径

| 项 | 取值 |
|---|---|
| 机器 | macOS（Intel x86_64），本机直跑，无容器 |
| 被测物 | **官方发布资产**：`orzmc-macos-x86_64` @ `OrzPythonMC v2.17.1` 与 `OrzMCKit v0.18.0`；另测 `pip install orzmc-app==2.17.0` 的源码形态 |
| 命令 | `--version` / `--json capabilities` / `--json list`（全部离线、无副作用） |
| 重复 | 每命令 7–9 次，取**中位数**；同时给最快/最慢 |
| 隔离 | 沙箱 `XDG_STATE_HOME` / `HOME`，并钉 `ORZMC_RUNTIME=python`（避免量到 M3 的"下载 + 转发"） |
| 指标 | 墙钟、**子进程 CPU**（区分"在等"与"在算"）、**峰值 RSS**（`ru_maxrss`）、体积 |
| 脚本 | [`scripts/bench/cli.py`](../scripts/bench/cli.py)（标准库，跨平台） |

> ⚠️ 只测**启动/元数据类**命令。真正的重活（下载、解压、启动 JVM）两边都是网络/IO 主导，
> 差异在启动开销而不是吞吐，故不在此列。

---

## 2. 运行效率（实测）

### 2.1 冻结二进制（一键安装器 / Releases 下载的那份）

| 命令 | Python（PyInstaller onefile） | Swift | 倍数 |
|---|---:|---:|---:|
| `--version` | **934 ms**（CPU 874 ms） | **13 ms**（CPU 10 ms） | **≈72×** |
| `--json capabilities` | **938 ms**（CPU 878 ms） | **28 ms**（CPU 21 ms） | **≈34×** |
| `--json list` | **904 ms**（CPU 844 ms） | **22 ms**（CPU 15 ms） | **≈41×** |
| 峰值 RSS | **37 MB** | **4 MB** | ≈9× |
| 体积（macOS） | 15.5 MB | 13.9 MB | 相当（Linux 侧 Swift 为 62–65 MB，见 §3） |

**为什么差这么多**：Python 资产是 PyInstaller **onefile** —— 每次运行都要把内嵌归档解到
`$TMPDIR/_MEIxxxx` 再执行（实测运行期确实创建 `_MEI*` 目录，退出后清理）。CPU 时间几乎等于墙钟，
说明**不是等待，是在解包**。

### 2.2 `pip install` 的源码形态（无解包成本）

| 命令 | Python（源码） | Swift | 倍数 |
|---|---:|---:|---:|
| `--version` | 628 ms（CPU 542 ms） | 14 ms | ≈45× |
| `--json capabilities` | 485 ms（CPU 458 ms） | 29 ms | ≈17× |
| `--json list` | 477 ms（CPU 450 ms） | 23 ms | ≈21× |
| 峰值 RSS | 30 MB | 4 MB | ≈8× |

> 参考：Python 侧大头是**解释器 + import**（`typer` / `rich` / `requests` / `prompt_toolkit`）。
> 这也是 M3 让「`pip` 新装默认走 Swift 真身」能立刻带来体验提升的原因。

---

## 3. 二进制能否独立运行（**关键差异**）

| 平台 | Python 资产 | Swift 资产 |
|---|---|---|
| **macOS** | ✅ 单文件；`otool -L` 只有 `libSystem` + `libz`；**最低 macOS 10.13** | ⚠️ 单文件，但依赖**系统 Swift 运行时**（`/usr/lib/swift/libswiftCore.dylib` 等）；**最低 macOS 13.0** |
| **Linux** | ✅ 单文件；只需要 `libc/libdl/libpthread/libz`；**glibc ≥ 2.14** | ✅ **0.19.0 起自包含**：`--static-swift-stdlib` + jammy 构建 → 无 `libswift*` 依赖，**glibc ≥ 2.35**；仍依赖系统 `libcurl4`；体积 62–65 MB（静态 Foundation/ICU 的代价） |
| **Windows** | ✅ 单个 `.exe`（16 MB） | ❌ **33 个文件的 zip**（35 MB，解压 100 MB）：exe + 32 个运行时 DLL（`Foundation.dll` / `_FoundationICU.dll` …） |

**怎么确认的**

```bash
# Linux：动态库 NEEDED 名字 + glibc 符号下限
strings -a orzmc-linux-x86_64 | grep -E '^lib[A-Za-z0-9_+.-]+\.so(\.[0-9]+)*$' | sort -u
strings -a orzmc-linux-x86_64 | grep -oE 'GLIBC_2\.[0-9]+' | sort -V -u | tail -1
# macOS：最低系统版本
otool -l orzmc-macos-x86_64 | grep -A4 LC_BUILD_VERSION | grep minos
```

**这条由 CI 意外证实**：`2.17.0` 首发时，Python 的 `binary` job 在干净 ubuntu runner 上执行
"下载下来的 Swift 真身"，直接报 `libswiftCore.so: cannot open shared object file`（→ §6.1）。

> 含义：**现在 M3 的「唯一实现」在干净的 Linux 机器上跑不起来**。这不影响 macOS/Windows
> （Windows 是 zip 形态，安装器会解压），但 Linux 用户是 `curl | sh` 或直接用资产的典型场景。

---

## 4. 依赖数

| 维度 | Python 实现 | Swift 实现 |
|---|---|---|
| **运行时第三方包（用户可见）** | 16–17 个 PyPI 包（`typer`/`click`/`rich`/`requests`/`prompt-toolkit`/`markdown-it-py`/`urllib3`… 含传递） | **0**（全部静态链进二进制） |
| **构建期依赖** | `uv` + PyPI 依赖树（含 PyInstaller 等，锁在 `uv.lock`） | **20 个 SwiftPM 包**（`console-kit` / `swift-nio` / `openapi-runtime` / `swift-crypto` / `yams` / `swift-algorithms` …；另有 2 个仅构建期插件：openapi-generator、SwiftLint） |
| **系统级依赖（发布物）** | 见 §3：macOS/Linux/Windows 均无（自带 CPython） | **Linux 需 Swift 运行时**；Windows 需随包 DLL；macOS 需系统 Swift 运行时（macOS 13+） |
| **外部工具** | `unzip`/`zip`（备份/音乐提取，缺失时降级或明确报错） | 同（`Game::PlatformTools` 解析） |

**解读**：Python 的依赖在**安装期**解析（用户要装 Python 3.10+，或用 15 MB 的冻结包）；
Swift 的依赖在**构建期**固化（用户侧零第三方，但换来的是 §3 的系统运行时需求 + 20 个包的构建成本）。

---

## 5. 迭代效率

| 维度 | Python 实现 | Swift 实现 |
|---|---|---|
| 本地门禁（一次全跑） | `pytest` **8.3 s** + `ruff` 0.2 s + `mypy` 1.6 s ≈ **10 s**，任意机器可跑 | `swift test` 约 **30 s**（本机直接跑，见 `scripts/swift-check.sh test`；不再 rsync 到远端） |
| 测试规模 | **473** 例 | **98** 例 |
| 反馈回路摩擦 | 改一行 → 秒级跑 | 改一行 → 编译（平台相关，Windows 需 VS+Swift 6.2+dev mode） |
| CI 单 job 中位耗时 | `quality` **43 s**、`test`（6 平台并行）**24 s**、`binary` 102 s、`installer` 55 s | `test` **100 s**、`linux` **131 s**、`conformance` **109 s**、`cli-acceptance` **77 s**、`ledger` **165 s**、`windows` **618 s**（源码变更才跑） |
| 一致性/验收 | 共享 harness（两侧同一份） | 共享 harness + conformance（79 例） |

**解读**：Python 迭代**更快更省机器**；Swift 的编译期把成本放在前面，换来运行期收益。
注意 Swift 的 `linux`/`conformance`/`cli-acceptance` 三个 job 加起来比 Python 全部 CI 还重。

---

## 6. 平台发布难易

| 维度 | Python 实现 | Swift 实现 |
|---|---|---|
| **整条发布流水线** | **2.7 分钟**（实测 `v2.17.1`） | **15.4 分钟**（实测 `v0.18.0`） |
| 单平台构建中位 | macOS 36–77 s / Linux 28–37 s / Windows 54–71 s | macOS **108–266 s** / Linux **220–316 s** / Windows **805–1037 s** |
| 交叉编译 | 无（PyInstaller 在目标平台构建） | macOS 不能交叉编译（openapi-generator 插件按 `ARCHS` 校验）→ 必须 2 个 runner |
| 工具链坑 | 无（`uv` + PyInstaller） | Windows 需要 **VS 2022+Swift 6.2+`update-sdk-modules`+开发者模式**；arm64 还要**选对 MSVC 工具集**（VS18 的 STL 要 Clang 20+）并铺 arm64 的 `INCLUDE/LIB`（见 `windows-port.md` §3.5） |
| 产物 | 6 × 15–18 MB，单文件 | 6 × 13.9–36 MB（Windows/Linux 明显更大） |
| 发布门禁 | PyPI OIDC + 6 平台 `binary` 验收 + `installer` e2e | 6 平台 `build` + 自报版本断言 + **`verify-linux`（在 `swift:6.0` 容器里跑）** + 验收 harness |

**解读**：Python 发布**便宜且稳**；Swift 发布**贵且脆**（今天新增 arm64 就踩了 3 个坑），
而且 `verify-linux` 用自带运行时的容器验，**掩盖了 §3 的问题**。

### 6.1 ✅ 两件硬伤已修（2026-10-20，`OrzMCKit v0.19.0`）

| 问题 | 修法 | 验证 |
|---|---|---|
| Linux 资产动态依赖 Swift 运行时、glibc 要 2.38 | `build-linux` 改在 **`swift:6.0-jammy`**（glibc 2.35）里构建 + **`--static-swift-stdlib`** + 链接期 strip；构建后断言 `ldd` 无 `libswift*` | 探针矩阵（x64/arm64 × 动态/静态）确认静态链在 Linux 上真实生效；`v0.19.0` 资产实测只剩 `libc/libcurl/libstdc++/libgcc/libm`，**GLIBC_2.35** |
| `verify-linux` 在自带运行时的 `swift:6.0` 镜像里验（等于没验） | 改用 **干净 `ubuntu:24.04`** + `binutils`：先断言 `ldd` 干净，再跑共享验收与安装器全链路 | `v0.19.0` 发布的 `verify-linux` **在干净容器里全绿**（含 `install → verify → uninstall`） |

> 附带产物：SwiftLint 的预编译二进制要求 GLIBC_2.38（在 jammy 上跑不起来、且插件失败会中止构建），
> 因此给自有依赖 `OrzSwiftLint` 加了 `ORZSWIFTLINT_SKIP=1` 逃生阀（仅发布流水线构建产物时使用，
> 日常 CI 仍跑 lint）。
>
> **代价**：Linux 资产 35 MB → **62–65 MB**（静态链把 Foundation/ICU 也带了进来）。
> 这是"能在干净系统上独立运行"换来的；对比 Python 的 18 MB 仍偏大，但已不再需要用户装运行时。

---

## 7. 结论：哪个更优？

**分维度看**（✅ 优 / ⚠️ 中 / ❌ 劣）：

| 维度 | Python 实现 | Swift 实现 | 谁更适合 |
|---|:--:|:--:|---|
| 启动速度 / CPU | ❌ 900–1600 ms | ✅ 13–30 ms | **Swift** |
| 内存占用 | ❌ 30–37 MB | ✅ 4 MB | **Swift** |
| 二进制体积 | ⚠️ 15–18 MB 单文件 | ⚠️ 13.9–36 MB | 平手（macOS 接近；Windows/Linux Swift 更大） |
| **独立可运行** | ✅ 三平台真自包含 | ❌ Linux 需运行时、Windows 需 33 文件 | **Python** |
| 系统版本要求 | ✅ macOS 10.13+ / glibc 2.14 | ⚠️ macOS 13+ / glibc 2.38 | **Python** |
| 依赖管理 | ⚠️ 16–17 个运行时包 | ✅ 用户侧 0（构建期 20 个） | **Swift**（用户视角） |
| 迭代速度 | ✅ 10 s 本地门禁，任意机器 | ⚠️ 26 s + 必须远端 Mac | **Python** |
| 测试密度 | ✅ 473 例 | ⚠️ 98 例 | **Python** |
| 发布成本/稳定性 | ✅ 2.7 min，无工具链坑 | ❌ 15.4 min，Windows/arm64 多坑 | **Python** |

**综合判断（并行期）**：

- **对外分发用 Python**：体积小（15–18 MB）、迭代快（本地门禁 10 s）、发布稳（2.7 min、无工具链坑），
  且三平台真自包含（glibc 2.14 / macOS 10.13+）。
- **Swift 保留但收敛为内部实验**：启动 13 ms、内存 4 MB、Linux 自包含（`0.19.0` 起）这些能力值得继续探索，
  但与 Python **同步迭代**、**不对外分发**（pre-release、不宣传）。
- 因此 `2.15–2.17` 试过的「`pip` 新装默认走 Swift」已**回退**（`2.17.2`）：默认 Python、零下载。

**一句话（2026-10-20 结论，已落地）**：**运行效率 Swift 完胜；体积/迭代/发布成本 Python 完胜。**
权衡后决定：**Python 是实现主体与唯一对外分发渠道；Swift 保留并与 Python 同步迭代，但不对外分发**
（Release 标 pre-release、不宣传），用于 Swift 生态样例与跨平台能力探索。
详见 [`two-cli-strategy.md`](two-cli-strategy.md) §6。

---

## 8. 复跑方法

```bash
# 1) 取两套官方资产
gh release download v2.17.1 --repo OrzMC/OrzPythonMC -p orzmc-macos-x86_64 -D /tmp/py
gh release download v0.18.0 --repo OrzMC/OrzMCKit   -p orzmc-macos-x86_64 -D /tmp/swift
chmod +x /tmp/py/orzmc-macos-x86_64 /tmp/swift/orzmc-macos-x86_64

# 2) 跑基准（中位数 + CPU + 峰值 RSS）
python3 scripts/bench/cli.py \
  --a "Python 冻结=/tmp/py/orzmc-macos-x86_64" \
  --b "Swift=/tmp/swift/orzmc-macos-x86_64" --runs 9

# 3) 独立运行性检查（Linux / macOS）
strings -a /tmp/py/orzmc-linux-x86_64   | grep -E '^lib.*\.so' | sort -u
strings -a /tmp/swift/orzmc-linux-x86_64 | grep -E '^lib.*\.so' | sort -u
otool -l /tmp/swift/orzmc-macos-x86_64 | grep -A4 LC_BUILD_VERSION | grep minos
```

> 换平台时把资产换成对应 `orzmc-<os>-<arch>`；Windows 上 `ru_maxrss` 分支自动跳过。
