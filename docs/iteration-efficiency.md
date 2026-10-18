# 迭代效率分析（Iteration Efficiency）

> **状态**：生效中（措施已落地）· **最后更新**：2026-10-18
> **适用**：本仓库的产品级迭代（父仓库 + `python` / `swift/*` 子模块）
> **缘起**：D14（Swift CLI 收敛为唯一跨平台实现）推进 Linux 支持时，9 轮 CI、约 2.5 小时，
> 其中绝大部分时间花在"等 CI 告诉我下一处编译错误"。本文记录实测数据、根因与已落地/建议的措施。

---

## 1. 实测数据（2026-10-18 那次跨平台推进）

| 观测项 | 数值 |
|---|---|
| CI 轮次 | **9 轮**（探针 dispatch + PR 触发） |
| 单轮墙钟（含排队） | **3–11 分钟**，中位数约 **7 分钟** |
| 其中"纯等编译报错"的轮次 | **5 轮**（每轮只暴露 1 类错误） |
| Linux job 冷构建 | 首次 **8m52s**；依赖编译占约 **300–960 步** |
| macOS 三件套（test/conformance/cli-acceptance） | 1m30s–2m30s（并行） |
| 本地 Swift 可用性 | ❌ 仅 5.8.1，包要求 6.0 → **本地无法编译** |
| Linux 门禁加缓存后 | **2m07s**（同一 job，降幅约 **76%**） |

### 1.1 时间都花在哪

```
总耗时 ≈ 轮次 × (排队 + 冷构建 3~4min + 编译到首个错误 + 运行门禁)
```

九轮里六轮的直接产出是"下一条错误信息"：

| 轮 | 花费 | 拿到的信息 |
|---|---|---|
| 1 | ~5m | `PaperMC` 缺 `FoundationNetworking` |
| 2 | ~7m | `Package.resolved` 钉住了旧提交（假阴性） |
| 3 | ~9m | `CryptoKit` ×2 + 8 处 `URLSession` |
| 4 | ~8m | `JokerKits.Shell` 被 `#if os(macOS)` 关掉 + 适配器 `CryptoKit` |
| 5 | ~8m | 编译通过（进入下一阶段） |

## 2. 根因

| # | 根因 | 影响 |
|---|---|---|
| R1 | **本地没有 Swift 6 工具链**，`swift build` 只能在 CI 跑 | 每次拼写/模块级错误都要 7 分钟往返 |
| R2 | **CI 冷构建无缓存**（容器每次全新，依赖全量编译） | 每轮固定浪费 2–4 分钟 |
| R3 | **SwiftPM 遇错即停**：第一个失败 target 就终止，看不到其余错误 | 一类错误一轮，无法一次看全 |
| R4 | **分支依赖 + `Package.resolved` 钉版本**（`branch: main`） | 依赖侧修了也进不来，白跑一轮 |
| R5 | **平台假设无静态门禁**：`CryptoKit` / `FoundationNetworking` / `/usr/bin/*` 全靠编译发现 | 只能"编译一次发现一类" |
| R6 | **发布链路与 CI 链路不一致**（容器里没有 `file`、默认 shell 是 `sh`） | 发布时才暴露，浪费一次发版 |

## 3. 已落地的措施

| 措施 | 位置 | 效果 |
|---|---|---|
| **本机快速迭代脚本** | `OrzMCKit/scripts/dev/local-build.sh`（`check`/`lint`/`parse`/`build`/`test`/`linux`，自动探测 swiftly 工具链 + SDK 诊断） | R1：语法级反馈 **50 s**、平台级 **1 s**，不必等 CI |
| **portability 独立快车道** | `.github/workflows/ci.yml` 的 `portability` job（宿主机，不建容器） | R5：**5 s** 出结论（此前要 8 分钟） |
| **秒级可移植性静态检查** | `OrzMCKit/scripts/verify/portability.py`，接入 CI `linux` job 首步 | 把 R5 从"8 分钟一轮"变成"**<1 秒**"；本轮扫描 89 个文件，当场抓出 4 处 |
| **Linux job 加 SwiftPM 缓存** | `.github/workflows/ci.yml`（`.build` + `/root/.cache/org.swift.swiftpm`，key 含 `Package.resolved` 哈希） | R2：**8m52s → 2m07s** |
| **本地 Linux 门禁脚本** | `OrzMCKit/scripts/dev/linux-build.sh`（docker/podman；`build`/`test`/`accept`/`all`/`lint`） | R1+R3：本地增量编译，一次看全错误 |
| **发布后自动验收** | `release.yml` 的 `verify-linux`（真实资产 → SHA256 → 验收 → 安装/卸载全链路） | R6：发布链路自身有门禁，不再靠人肉 |
| **跨平台边界显式化** | `Game.PlatformTools`、`app` 非 macOS → `E_UNSUPPORTED` | 减少"跑起来才炸"的隐性问题 |
| **发布链路容器适配** | `uname -m` 断言替代 `file`；容器内步骤 `shell: bash` | R6：容器环境差异提前修掉 |

## 3.1 本机 Swift 6 工具链（2026-10-18 实测）

按建议装了本机工具链（`swiftly`，免 sudo）：

```bash
swiftly install 6.0            # → swift-6.0.3-RELEASE.xctoolchain
export PATH="$HOME/Library/Developer/Toolchains/swift-6.0.3-RELEASE.xctoolchain/usr/bin:$PATH"
swift --version                 # Apple Swift version 6.0.3
```

**结论：工具链可用，但这台机器仍无法做完整本机构建**，三点客观限制（`scripts/dev/local-build.sh` 会把它们打印成诊断）：

| 限制 | 证据 | 影响 |
|---|---|---|
| macOS SDK **13.3** < 14 | 依赖 `OpenAPIKit 3.9.0` 的 `Container+DecodeURLAsString.swift` 调用 `URL(string:encodingInvalidCharacters:)`（macOS 14 SDK 才有；`#available` 无法绕过） | `swift build` 必失败 |
| 只有 CommandLineTools（无 Xcode） | SwiftLint 构建插件报 `sourcekitdInProc … not found`（预编译 SwiftLint 期望 Swift 6.2 目录布局） | 插件噪音/偶发失败 |
| 磁盘仅剩 ~9.8 GB | `df -h /` | 装 Xcode 16（~20 GB）不可行 |

**本机性能实测（2015 款 i5-5257U / 16 GB）**：

| 操作 | 耗时 | 说明 |
|---|---|---|
| `swift --version` | 2.2 s | syscall 开销主导 |
| 空项目首次构建 | 65 s | |
| 空项目 no-op 构建 | **16.7 s** | user 仅 1.7 s → 这台机器 I/O/系统调用极慢 |
| 本包冷构建（跑到 OpenAPIKit 失败处） | **35 分钟** | 依赖图全量编译 |

因此本机只做**秒级/分钟级**反馈，全量构建交给 CI：

| 反馈层级 | 手段 | 实测耗时 |
|---|---|---|
| 平台写法错误 | 本机 `local-build.sh lint` / CI `portability` job | **~1 s** / **5 s** |
| 语法错误 | 本机 `local-build.sh check`（`swiftc -parse` 80 文件） | **50 s** |
| 完整构建 + 单测 + 验收 | **`ssh air`**（`scripts/air/run.sh accept`） | **24s（build）/ 25s（test）/ 1m33s（accept）** |
| 完整构建 + 单测 + 验收 | CI `linux` job（带缓存） | **2m02s** |
| 完整构建 + 单测 + 验收 | CI macOS job | 1m07s–1m56s |

> 想在本机打通全量构建的唯一现实路径：**释放磁盘 + 装 Xcode 16+ 或更新 CommandLineTools**（需管理员），
> 或改用 Linux 容器（`scripts/dev/linux-build.sh`，需 docker/podman）把构建搬到 Linux 侧。

## 3.2 远端构建（`ssh air`）——本轮的最终答案

本机既然做不了全量构建，就把构建搬到达标的机器上。`air`（Apple Silicon M1 / 8 核 / Swift 6.4 / SDK 27 /
剩余 24GB）已接入：**[`scripts/air/run.sh`](../scripts/air/run.sh)**。

```bash
scripts/air/run.sh build     # rsync 工作树 + swift build --product orzmc
scripts/air/run.sh accept    # + release 构建 + CLI 验收
```

**实测（本轮真跑，2026-10-18）**：

| 任务 | 耗时 | 说明 |
|---|---|---|
| `build`（增量，含 rsync） | **24 s** | 远端编译本体 **1.5–15 s**；rsync ~15 s |
| `build`（首轮冷构建，含依赖拉取） | 1 m 08 s | 之后靠远端 `.build` 增量 |
| `test`（90 + 1 例） | **25 s** | |
| `accept`（release + 20 用例） | **1 m 33 s** | |
| `ORZMC_LOCAL_DEPS=1 build`（依赖走本地工作树） | **37 s** | 改依赖仓库时不必先 push |

**同一件事的四条路径对比**：

| 路径 | 时长 | 可行性 |
|---|---|---|
| 本机全量构建 | **不可行** | SDK 13.3 < 14（依赖要求） |
| 本机 `check`（lint + 语法） | 50 s | ✅ 只能抓语法/平台写法 |
| **`ssh air` 远端构建** | **24 s（增量）** | ✅ **日常主力** |
| CI（macOS / Linux，带缓存） | 1 m 07 s – 2 m 02 s | ✅ 合并前门禁 |

**两个关键优化**（否则远端也要 1 分钟以上）：
1. 依赖是 `branch: main`，SwiftPM 每次解析都联网刷新 → 默认加
   `--only-use-versions-from-resolved-file`（要更新依赖时用 `ORZMC_UPDATE_DEPS=1`）：24 s vs 1 m 07 s。
2. `rsync --delete` 但 **排除 `.build`** → 远端增量构建得以保留（否则每次都冷编译）。

## 4. 建议（尚未落地，按性价比排序）

1. ~~本地装 Swift 6 工具链~~ **已做**（见 §3.1）：工具链可用，但本机 SDK/磁盘不足以全量构建；
   现实路径是**释放磁盘 + 装 Xcode 16+/更新 CLT**（需管理员），或改用 Linux 容器构建。
2. **依赖侧改动走"可验证的 pin 刷新"**
   - 依赖是 `branch: main` 时，合并依赖仓库后**立刻**刷新 `Package.resolved`（本轮漏了一次，白跑一轮）。
   - 建议加小脚本 `scripts/dev/bump-deps.sh`：拉三个依赖仓库的 main → 更新 `Package.resolved` → 打印 diff。
3. **CI 分快慢车道**
   - 快车道（PR 必跑）：`portability.py` + `swift build --product orzmc`（不跑全 target、不跑 test）。
   - 慢车道（main / 影响面大时）：全量 build + test + conformance + cli-acceptance。
   - 现状：Linux job 会在 PR 上跑全套（2 分钟，尚可接受），暂不必拆；若再加 Windows matrix 就值得拆。
4. **matrix 扩张时优先"并行"而非"串行"**
   - Windows 阶段建议 `linux`/`windows` 各自独立 job（同 macOS 模式），单次等待 ≈ 最慢那一路，而不是相加。
5. **把"平台假设"写进代码规范而非口头**
   - PR 模板加一行：新增 `import CryptoKit` / `URLSession` / `/usr/bin/*` 必须走条件导入或 `PlatformTools`；静态检查已强制，评审时只需看是否滥用允许清单。

## 5. 度量方式（后续可量化）

| 指标 | 采集方式 | 目标 |
|---|---|---|
| PR 反馈时间（push → 首个绿/红） | `gh run list` 的 `createdAt`/`updatedAt` | Linux ≤ 3 分钟（缓存后已达 2m07s） |
| "纯等错误"轮次占比 | 人工记账（本文 §1.1） | ≤ 20%（本轮 5/9） |
| 发布流水线一次通过率 | `release.yml` 的 run 结论 | 100%（含 `verify-linux`） |
| 静态检查拦截数 | `portability.py` 输出 | 新增平台假设 0 漏网 |

---

**一句话**：这次最大的成本不是"改代码"，而是**反馈回路太长**——先把回路缩短（本地工具链 + 秒级静态检查 + 缓存），再谈改得多快。
