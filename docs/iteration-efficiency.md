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
| **秒级可移植性静态检查** | `OrzMCKit/scripts/verify/portability.py`，接入 CI `linux` job 首步 | 把 R5 从"8 分钟一轮"变成"**<1 秒**"；本轮扫描 89 个文件，当场抓出 4 处 |
| **Linux job 加 SwiftPM 缓存** | `.github/workflows/ci.yml`（`.build` + `/root/.cache/org.swift.swiftpm`，key 含 `Package.resolved` 哈希） | R2：**8m52s → 2m07s** |
| **本地 Linux 门禁脚本** | `OrzMCKit/scripts/dev/linux-build.sh`（docker/podman；`build`/`test`/`accept`/`all`/`lint`） | R1+R3：本地增量编译，一次看全错误 |
| **发布后自动验收** | `release.yml` 的 `verify-linux`（真实资产 → SHA256 → 验收 → 安装/卸载全链路） | R6：发布链路自身有门禁，不再靠人肉 |
| **跨平台边界显式化** | `Game.PlatformTools`、`app` 非 macOS → `E_UNSUPPORTED` | 减少"跑起来才炸"的隐性问题 |
| **发布链路容器适配** | `uname -m` 断言替代 `file`；容器内步骤 `shell: bash` | R6：容器环境差异提前修掉 |

## 4. 建议（尚未落地，按性价比排序）

1. **本地装 Swift 6 工具链**（最高性价比）
   - `swiftly install 6.0`（或官方 toolchain pkg），之后 `swift build` 本地跑，**单次编译循环从 7 分钟降到 1–2 分钟**，且 `swift build 2>&1 | grep error:` 一次看全。
   - 前提：macOS 13+ x86_64/arm64。装好后把 `swift --version` 写进 `HANDOFF.md` 的"环境"节。
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
