# 行为契约（Behavior Contracts）

> **状态**：草案 `specVersion 0.2` ｜ **最后更新**：2026-10-20（B9/B11 按 2026-10 的 CLI 契约增补重新定稿）
> 定义实现必须一致的**行为**（而非数据形状）。每条契约都应有对应一致性样例（见 [`conformance.md`](conformance.md)）。
> 标注：`P`=Python 现状、`S`=Swift 现状；✅ 已符合 / ⚠️ 需对齐 / ❌ 缺失。

---

## B1 元数据缓存与刷新

| 项 | 契约 |
|:--|:--|
| 缓存对象 | 版本清单、version JSON、fabric-meta、Paper、Forge promotions |
| TTL | 默认 `86400s`（24h）；`ttl<=0` 表示永不复用 |
| 刷新 | `--refresh` 绕过**所有缓存读** |
| 失败回退 | 拉取失败 → 回退磁盘上（可能过期的）旧副本并 warn；完全无缓存才报错 |
| 时钟容忍 | `-_FUTURE_SKEW(300s) <= now - mtime < ttl`（容忍小幅未来时间戳） |

- 现状：`P` ✅（`infra/cache.py`）；`S` ✅（`OrzSwiftKit/CacheKit` 的 `MetadataCache`：同一 TTL/refresh/离线回退契约，`Mojang+Cache` 注入目录与策略）。
- 样例：过期/未过期/刷新/离线回退/未来时间戳 5 组。

## B2 下载并发

| 项 | 契约 |
|:--|:--|
| 默认并发 | `16`（`--download-threads/-j`，范围 `1–64`） |
| 连接池 | `max(pool_default, concurrency)`；池 < 并发会导致连接反复重建 |
| 小文件 | 资源阶段几千个小文件，耗时 ≈ 每请求延迟 × 并发数 |
| 大文件分块 | ≥ `8MB` 分 `4` 路 `Range` 并行取再拼接 |
| 回退 | 服务器忽略 `Range`（返回 200）→ 直接单流写完 |
| 中断续传 | 流式 body 中途断连（代理重置/丢包）→ 按已落盘字节 `Range: bytes=<have>-` 续传（有限次重试）；服务器对续传回 200 则整份重来 |
| 清理 | 拼接后校验总字节数，`.part*`/`.tmp` 在 `finally` 清理 |

- 现状：`P` ✅（`infra/transfer.py` + `infra/http.py` `stream_range`/`fetch_range`）；`S` ✅（`TransferKit`，含 `.part` + `Range` 续传）。
- 样例：单流、4 路、Range 不支持回退、字节数不符拒绝。

## B3 完整性校验

| 项 | 契约 |
|:--|:--|
| 默认算法 | SHA-1（携带 `hashType`） |
| 时机 | **写入前/后校验，不匹配即拒绝**，不留半成品 |
| 覆盖 | 客户端 jar、库、asset、服务端核心、Java 运行时 |

- 现状：`P` ✅（`infra/hashing.py`）；`S` ✅（`DownloadItemInfo(hash:hashType:.sha1)`）。
- 样例：正确/错误哈希各一。

## B4 路径与目录

| 项 | 契约 |
|:--|:--|
| 路径函数 | **纯函数、无副作用**（只拼字符串，不建目录） |
| 建目录 | 统一在 service 层 `ensure_dir` |
| 布局 | 由 [`data-model.md`](data-model.md) §1 `RootLayout` 唯一规定 |

- 现状：`P` ✅（`domain/paths.py`）；`S` ✅（`GamePlan.Layout`：`<root>/versions/<v>/client/…`，与 §1 一致；`layout/*` 6 例通过）。
- 样例：给定版本/类型 → 期望路径集合（见 conformance 布局样例）。

## B5 Java 运行时

| 项 | 契约 |
|:--|:--|
| 需求推导 | 读 version JSON `javaVersion.majorVersion`，**缺失默认 8**；不按 MC 版本硬编码 |
| 获取 | 托管到 `java/<major>/`（应用目录内），**不依赖系统 Java** |
| 启动 | 用 `java/<major>/bin/java` |
| 运行时 | JRE 即可满足所有类型 |

- 现状：`P` ✅（`domain/java.py` + `services/java.py`）；`S` ✅（`Game/Java/JavaRuntime.swift` 托管到 `java/<major>`，经 `RuntimeKit` 装 Adoptium JRE 并拍平，不依赖系统 java）。

## B6 客户端启动

| 项 | 契约 |
|:--|:--|
| 参数来源 | version JSON `arguments.jvm` / `arguments.game`，按 `rules`（OS/arch/features）过滤 |
| 旧格式 | 无 `arguments` 时用 legacy 模板 |
| 令牌替换 | `${natives_directory}` `${classpath}` 等按 `data-model.md` §8 |
| 平台差异 | macOS 需 `-XstartOnFirstThread`（由 rules 决定） |
| 类路径 | 库 + 客户端 jar + loader 附加库；分隔符按平台（`;` / `:`） |

- 现状：`P` ✅（`domain/launch.py`）；`S` ✅（`GamePlan.planClientLaunch` / `ClientLaunchPlan`，`client-plan/*` 5 例通过）。
- 样例：同 version JSON → 期望 `LaunchPlan`。

## B7 服务端生命周期

| 项 | 契约 |
|:--|:--|
| 关闭 | 终端 `stop` 或 Ctrl-C 优雅保存退出 |
| 超时 | 60s 未退 → SIGTERM → SIGKILL |
| 孤儿 | **不遗留孤儿进程** |
| 退出码 | Ctrl-C 取消 → `130` |

- 现状：`P` ✅（`ProcessRunner.run_stream`）；`S` ✅（`Server+Launch`：优雅 `stop` → `SIGTERM` → `SIGKILL`；`E_CANCELLED` 归一为退出码 `130`）。
- 样例：启动→stop→退出码；启动→SIGINT→130。

## B8 进度事件

| 项 | 契约 |
|:--|:--|
| 两类任务 | `count`（文件数）与 `bytes`（字节）**必须区分** |
| 不定长 | `total=null` 时渲染不定长进度（`status`） |
| 归属 | 进度由**调用线程**独占喂给 sink（多线程只做原子累加） |

- 现状：`P` ✅（`ProgressSink.start / start_bytes / status`）；`S` ✅（`TransferKit.TransferProgress` → `Downloader.onEvent` → `Game/Progress/ProgressReporter`：count/bytes 分开，`total == nil` 只输出一行状态、不画 0%）。
  > 交互差异（非契约）：Python 用 rich 的不定长脉冲条，Swift 输出一行状态；两边都满足「不静默、不假装 0%」。

## B9 非 TTY 行为

| 项 | 契约 |
|:--|:--|
| 禁止阻塞 | 任何非 TTY 场景**不得等待输入** |
| 版本缺省 | 用 Mojang 最新 release |
| 用户名缺省 | `guest` |
| 确认项 | 见下方「非 TTY 确认规则」 |
| 破坏性操作 | 非 TTY 且缺 `--yes` → **取消**（`E_CANCELLED` / 130），**不做任何修改** |
| 有默认意图的操作 | `update` 直接执行；`server` 的 EULA 必须显式 `--yes`，不被“默认”代为接受 |

**非 TTY 确认规则**（与 [`cli-surface.md`](cli-surface.md) §7 同一条契约）：

| 命令 | 缺 `--yes` 的非 TTY 行为 |
|:--|:--|
| `remove` / `uninstall` / `app uninstall` | `E_CANCELLED`（130），数据/二进制保持原样 |
| `update` | 直接执行（用户显式调用即意图） |
| `server`（EULA） | 报错要求 `--yes`（法律同意不能默认） |

- 现状：`P` ✅（`remove`/`uninstall` 非 TTY 缺 `--yes` 退 130；`update` 直接执行；`server` 报错）；
  `S` ⚠️ 待对齐（`RemoveCommand`/`UninstallCommand` 当前在非交互下**直接执行**；`update`/`server` 已符合）。

## B10 版本解析与渠道

| 项 | 契约 |
|:--|:--|
| 渠道 | `release` / `snapshot`（非 release 一律 snapshot） |
| 最新版 | `latest.release` |
| 版本选择器 | TTY：键盘导航 + 搜索 + 切渠道；非 TTY：最新 release |

- 现状：`P` ✅（prompt_toolkit 全屏选择器）；`S` ✅（`VersionPickerState` + `runVersionPicker`：release/snapshot 切换、子串搜索、分页、序号选择；非 TTY 仍是最新 release；显式 `-v` 同时查 release/snapshot）。
  > 交互差异（非契约）：Python 方向键全屏 TUI，Swift 行式导航（`n`/`p`/`t`/`x` + 序号）；契约要求的「导航 / 搜索 / 切渠道」两边都具备。

## B11 错误语义

| 项 | 契约 |
|:--|:--|
| 归一化 | 网络/文件错误在 service 层统一转为**用户可读**信息（不裸抛底层异常） |
| 去向 | **错误 / 日志 / 进度一律 stderr**；人类可读**结果**才进 stdout |
| 退出码 | 只有 `0`（成功）/ `1`（运行 / 用法错误）/ `130`（`E_CANCELLED`）；框架默认值（click 的 `2`、ConsoleKit 的默认值）必须归一 |
| 信封 | `--json` 下 stdout **恰好一个** JSON 对象；解析阶段（未知命令/选项、缺必填）不要求信封，但必须退 `1` 且 stderr 可读 |
| 不静默 | 任何降级（如缓存回退、类型不支持）都要有明确提示 |

- 现状：`P` ✅（`_console_err` + `_reporter` 切 stderr；`main()` 收敛退出码）；`S` ✅（`ErrorPresentation` + `StderrConsole`）。
- 用例：`error/*`；CLI 层行为见 [`conformance.md`](conformance.md) §7 的 acceptance `envelope` / `surface` 组。

---

## 契约 × 实现 × 样例 对照

| 契约 | Python | Swift | 一致性样例（见 conformance） |
|:--|:--:|:--:|:--|
| B1 缓存 | ✅ | ✅ | `cache/*` |
| B2 并发/分块 | ✅ | ⚠️ | `download/*` |
| B3 校验 | ✅ | ✅ | `verify/*` |
| B4 路径 | ✅ | ✅ | `layout/*` |
| B5 Java | ✅ | ✅ | `java/*` |
| B6 客户端启动 | ✅ | ✅ | `client-plan/*` |
| B7 服务端生命周期 | ✅ | ✅ | `server-lifecycle/*` |
| B8 进度 | ✅ | ✅ | `progress/*` |
| B9 非 TTY | ✅ | ⚠️ 取消语义待对齐 | `non-tty/*` |
| B10 版本解析 | ✅ | ✅ | `version-resolve/*` |
| B11 错误语义 | ✅ | ✅ | `error/*` |

> 说明：`⚠️` 不等于错误，而是"行为需按契约固化并被样例覆盖"。
> **2026-10-17 复核结论**：Swift 侧 B1–B11 **全部落地**（早前标 ❌/⚠️ 的条目源于 2026-10-13 快照，已全部过期）；
> 仅存的交互性差异（进度渲染形态、选择器 TUI vs 行式）不属契约项，已在 B8/B10 下注明。
