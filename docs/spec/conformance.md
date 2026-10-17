# 一致性套件（Conformance Suite）

> **状态**：草案 `specVersion 0.2` ｜ **最后更新**：2026-10-20（新增 §12 CLI 行为验收）
> 用**黄金样例**把规范变成可断言对象：各语言实现跑同一批样例，**差异即红灯**。
> 这是"规范不漂移"的唯一长期保障（决策 D4）。

---

## 1. 为什么需要

`python` 与 Swift 引擎是**两套独立实现**。没有可执行的一致性校验时，规范会退化成文档，
实现悄悄分叉。conformance 把 `data-model.md` / `behavior.md` 的每条契约变成
**输入 → 期望输出**的样例，任何一方改动导致行为不同都会立刻暴露。

---

## 2. 目录结构

```
docs/spec/
  fixtures/
    README.md                  # 样例索引与用法
    schema/fixture.schema.json # 样例格式的 JSON Schema
    <area>/
      <case-id>.json           # given + expect（单文件，自包含）
    snapshots/                 # 钉住的上游输入快照（离线可跑）
      version_manifest.json
      versions/<id>.json
  conformance.md               # 本文件
scripts/conformance/           # spec-owned 运行器（父仓库）
  run.py                       # 发现样例 + 调适配器 + 子集比对 + 差异
  reference.py                 # 规范参考适配器（纯计划语义）
```

- `<area>` 对应契约域：`layout` / `version-manifest` / `client-plan` / `client-download` / `server-plan` / `server-launch` /
  `server-lifecycle` / `download` / `verify` / `cache` / `java` / `progress` / `non-tty` / `error` / `auth`。
- `snapshots/` 是**钉住版本**的上游 JSON，保证 fixture 离线、可复现。

---

## 3. Fixture 格式

单文件自包含：

```jsonc
{
  "specVersion": "0.1",
  "id": "client-plan/vanilla-1.20.4-macos-arm64",
  "area": "client-plan",
  "description": "vanilla 客户端在 macOS arm64 的启动参数",
  "given": {
    "operation": "planClientLaunch",
    "version": "1.20.4",
    "gameType": "vanilla",
    "platform": { "os": "osx", "arch": "arm64" },
    "root": "/tmp/orzmc-fixture",
    "snapshot": "snapshots/versions/1.20.4.json"
  },
  "expect": {
    "executable": "/tmp/orzmc-fixture/java/17/bin/java",
    "mainClass": "net.minecraft.client.main.Main",
    "jvmArgsContains": ["-XstartOnFirstThread"],
    "classpathOrder": ["...", "..."],
    "tokens": { "assets_index_name": "5", "version_type": "release" }
  }
}
```

| 字段 | 说明 |
|:--|:--|
| `given.operation` | 调用的规范操作名（见 §5） |
| `given.snapshot` | 引用的输入快照路径（相对 `fixtures/`） |
| `expect` | 期望输出；允许**子集断言**（见 §4） |

---

## 4. 断言规则（避免脆弱样例）

- **子集断言**：`expect` 只声明关心的字段/集合，不要求逐字节全等（路径绝对前缀由 `given.root` 决定）。
- `*Contains` / `*Order` / `*Count` 等后缀表示包含 / 顺序 / 计数断言。
- `"absent": ["serverDir", ...]`：声明**必须不存在**的字段路径（dotted，可嵌套）；用于「无 `type` 时省略 server 字段」这类反向断言。
- 时间戳、随机令牌（`auth_uuid` 等）**不参与**断言。
- 数值容差：仅 `bytes` 类允许 ±0（不允许），计数类精确。

---

## 5. 规范操作（conformance API）

实现须暴露可被 harness 调用的"纯计划"操作（**不执行 IO**）：

| 操作 | 输入 | 输出 |
|:--|:--|:--|
| `planLayout` | root/version/type | 路径集合 |
| `resolveVersion` | channel/version/snapshot | 版本条目 |
| `planClientDownload` | version/loader/platform/snapshot(+assetIndex) | `DownloadItem[]`（`{url,path,sha1,size}`） |
| `planServerDeploy` | version/type/snapshot | `ServerDeployPlan` |
| `planClientLaunch` | version/platform/options/snapshot | `ClientLaunchPlan` |
| `planServerLaunch` | version/type/options | `ServerLaunchPlan` |
| `normalizeExit` | returnCode | `{exitCode, signaled, signal}` |
| `requiredJava` | snapshot | `JavaRequirement` |
| `verifyArtifact` | bytes + sha1 | pass/fail |
| `cacheDecision` | mtime/ttl/refresh/now | hit/miss/refresh/fallback |
| `authDeviceCodeRequest` … `authClassifyXstsError` | 见 [`auth.md`](auth.md) §9 | 认证链路的请求/响应纯映射（**不打网络**） |

> Python 侧可用内部 API 暴露（测试接缝）；Swift 侧 `Game` 已有 `generateDownloadItemInfos()`，已补纯计划入口
> `GamePlan.planClientDownload`（含 legacy natives 选择与 rules 过滤）。
> `planClientDownload` 已实现：fixture `client-download/vanilla-1.20.4-macos-arm64`（客户端 jar / 资源索引 /
> 资源对象 / 库，含 `itemsContains`/`itemsNotContains` 与 `count`）。
>
> **版本源（已决）**：`planClientLaunch` / `planClientDownload` 以显式 `given.version` 为准（路径 / jar 名 /
> `--version` / 令牌），即使与 `snapshot.id` 不一致也以它为准（fixture `*/mismatched-version-id`）。
> `planLayout` 的 `type` 可选：缺省时只产出客户端路径，省略全部 server 字段（fixture `layout/no-type-*`）。

---

## 6. Harness

**统一契约**：读 `fixtures/**`，对每个 fixture 调对应 `operation`，规范化输出，与 `expect` 比对，输出差异。

**已落地（父仓库，语言无关）**

| 组件 | 位置 | 说明 |
|:--|:--|:--|
| 运行器 | [`scripts/conformance/run.py`](../../scripts/conformance/run.py) | 发现样例、调用适配器、子集比对、打印差异 |
| 参考适配器 | [`scripts/conformance/reference.py`](../../scripts/conformance/reference.py) | 把规范纯计划语义编码为**可执行参照**，并验证样例自洽 |

```bash
python3 scripts/conformance/run.py --adapter "python3 scripts/conformance/reference.py"
```

**各语言适配器（在各自仓库，通过 `--adapter` 接入）**

| 语言 | 位置 | 状态 |
|:--|:--|:--:|
| Python | `python/orzmc/tests/conformance/adapter.py` | ☑ 已接入（76/76） |
| Swift | `swift/lib/OrzMCKit/Sources/ConformanceAdapter` | ☑ 已接入（76/76，OrzMCKit CI 内运行） |

> **当前 76 例**：参考适配器 76/76；Python 适配器 76/76；Swift 适配器 76/76。
> `auth/*`（20 例）为**离线优先**新增，三者均已实现；另含 `layout/no-type-*`（无 type 省略 server 字段）
> 与 `client-plan|client-download/mismatched-version-id`（`given.version` 与 `snapshot.id` 不一致时以 `given.version` 为准）3 例。
> ⚠️ **合入顺序**：Swift CI 会检出**父仓库 main** 并 `--strict`。Python/Swift 的 `auth/*` 适配器改动目前
> **仅在本地**；在把它们合入子模块之前，**勿将 `auth/*` fixtures 合入父仓库 main**（否则子模块 CI 红灯）。

```bash
# Python 适配器（在父仓库根执行）
python3 scripts/conformance/run.py \
  --adapter "uv run --directory python python orzmc/tests/conformance/adapter.py" --strict

# Swift 适配器（需能编译 OrzMCKit）
BIN="$(swift build -c debug --package-path OrzMCKit --show-bin-path)/ConformanceAdapter"
python3 scripts/conformance/run.py --adapter "$BIN" --strict
```

> OrzMCKit 的 CI 已内置 `conformance` job：检出父仓库 fixtures → 构建适配器 → 跑 `run.py --strict`（Q6）。

> 运行器会向适配器子进程注入 `ORZMC_CONFORMANCE_FIXTURES=<父仓库 fixtures 绝对路径>`，
> 供子模块适配器定位快照。

**共同要求**
- **离线**：只用 `fixtures/snapshots/`，不打网络、不碰系统 Java。
- **可定位**：失败时打印 `id` + 字段级 diff。
- **确定性**：忽略时间/随机值（见 §4）。
- **无副作用**：只做“纯计划”，不执行下载/安装/启动。

---

## 7. 覆盖矩阵

样例需覆盖以下维度组合（不必穷举，但每维至少一条边界）：

| 维度 | 取值 |
|:--|:--|
| MC 版本 | 现代（有 `arguments`）/ 旧版（legacy 模板） |
| 类型 | client: `vanilla/fabric/forge`；server: `vanilla/paper/fabric/forge` |
| 平台 | `windows/linux/osx` × `x86_64/arm64` |
| 路径 | 默认 root / 自定义 `--root-dir` |
| 缓存 | 命中 / 过期 / `--refresh` / 离线回退 |
| 下载 | 单流 / 4 路分块 / Range 不支持回退 |
| 错误 | 哈希不符 / 类型不支持 / 网络失败 |

---

## 8. 负向用例（必须有）

- **B3**：哈希不符 → 必须拒绝，且不留半成品。
- **B2**：Range 返回 200 → 必须回退单流且**不重复下载**。
- **B1**：离线 + 有旧缓存 → 必须回退并 warn；离线 + 无缓存 → 必须报错。
- **B4/类型**：不支持的平台/类型 → 显式"不支持"，不静默。
- **B9**：非 TTY → 不阻塞。

---

## 9. CI 接线

| 仓库 | 触发 | 动作 |
|:--|:--|:--|
| `OrzPythonMC` | CI | 跑 Python 适配器（全网离线） |
| `OrzMCKit` | CI | 跑 Swift 适配器 |
| 父仓库 | 可跑 | 用参考适配器自检 fixtures（`run.py --adapter reference.py`），不需跨仓触发 |

- 规范变更（改 `docs/spec/**`）→ 应同步更新 fixtures；漏改由任一适配器红灯暴露。
- 【待定】是否在父仓库 CI 加一个 job 跑参考适配器自检（见 plan Q6）。

---

## 10. 新增一个 fixture 的步骤

1. 选定 `area` 与 `id`（`<area>/<描述>`）。
2. 钉住输入快照到 `fixtures/snapshots/`（不要引用会变的上游 URL）。
3. 写 `given`（操作 + 参数 + 快照）与 `expect`（**子集**断言）。
4. 本地跑 Python 与 Swift harness，双方均绿才算样例成立。
5. 若样例暴露实现差异 → 记入 [`behavior.md`](behavior.md) 对应契约的现状列，并按 Phase 3 对齐。

---

## 11. 与其他文档的关系

- 数据形状来自 [`data-model.md`](data-model.md)。
- 行为语义来自 [`behavior.md`](behavior.md)。
- 落地阶段与勾选见 [`product-unification-plan.md`](../product-unification-plan.md) Phase 2/3。

---

## 12. CLI 行为验收（acceptance）

fixtures 断言的是**库层**输入→输出（计划、下载、缓存、错误语义）。CLI 还有一批
**进程级行为**用 fixture 表达不了，但它们同样是契约，且历史上真出过事故
（2026-10：冻结二进制里 `completion install` 因 PyInstaller 漏打包动态 import 的
`shellingham.posix` 而崩，单测全绿、用户一跑就炸）。所以契约再加一层**可执行验收**。

### 12.1 规则

1. **每套实现都要有一个等价 harness**，用例分组、断言语义相同；实现语言/框架自选。
2. **断言按规范写**（`cli-surface.md` §4/§6/§7/§9、`behavior.md` B9/B11、`frontends.md` F2/F6），
   不按当前实现写。规范变了先改断言，再改实现。
3. 每个用例跑**真实子进程**（不是进程内调用），`stdin` 接 `/dev/null`（或固定脚本），带超时；
   「非交互不阻塞」本身就是被测行为。
4. 每个用例用**隔离沙箱**（`HOME` / `XDG_*` / 游戏根指向临时目录），不碰真实配置。
5. 必须能在**发布形态（冻结二进制）**上跑一遍 —— 那是唯一能发现「打包漏了模块」的地方。

### 12.2 分组（两套实现一致）

| 组 | 断言要点 | 对应规范 |
|:--|:--|:--|
| `surface` | 无参打印帮助并退 0；`-h` 与 `--help` 等价（根 + 每个子命令）；`version` 与 `--version` 一致；用法错误退 **1**；全局选项只能在子命令前 | §1 / §3 / §6 |
| `envelope` | 每个命令 `--json` 下 stdout **恰好一个**对象；`command` 正确；失败有稳定 `E_*` 且退出码匹配（`E_CANCELLED`→130，其余→1）；stdout 无 ANSI / 无人类可读行 | §6 / §6.1 |
| `contract` | 非交互破坏性操作缺 `--yes` → 130 且**数据不动**；`list` 能识别已安装版本；任何路径都不阻塞 | §7 / §8.2 / B9 |
| `completion` | 五个 shell 都能生成脚本；未知 shell → `E_USAGE`；`install` 落点/幂等/rc 只写一次；powershell/pwsh → `E_UNSUPPORTED`；`$SHELL` 缺失时给出可执行退路 | §4.5 / §9 / F6 |
| `mcp` | stdio JSON-RPC 全会话（`initialize`/`tools/list`/`tools/call`/`ping`/未知方法/坏 JSON）；排除集；`isError` 语义；缺 `--yes` 的 `remove` 是 tool 错误而非 RPC 错误 | §8.2 |
| `frozen` | 仅发布形态：动态补全（`_ORZMC_COMPLETE`）可用；框架自带的补全开关**不存在**；`completion install` 不崩 | §4.5 / §9 |
| `network` | 默认不跑；`--network` 才跑 `update --check` / `plugin --search`（限流也要「有信封地失败」） | §6.1 |

### 12.3 现状与接线

| 实现 | harness | CI |
|:--|:--|:--|
| Python | `python/scripts/accept_cli.py`（`--cli dist/orzmc` 跑冻结二进制） | `quality` 跑源码模式；`binary` 6 平台各跑一次 `--cli dist/orzmc` |
| Swift | ⚠️ 待建等价 harness（分组/断言照 §12.2） | 建议在 `OrzMCKit` CI 加 `conformance` 之后的一步 |

新增用例：先确认它属于**规范**要求（不是实现细节），再写进对应分组；断言失败信息里要能看出
「哪条规范、哪次调用、实际输出」。
