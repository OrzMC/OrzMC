# 一致性套件（Conformance Suite）

> **状态**：草案 `specVersion 0.1` ｜ **最后更新**：2026-10-13
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
    <area>/
      <case-id>.json          # given + expect（单文件，自包含）
    snapshots/                 # 钉住的上游输入快照（离线可跑）
      version_manifest.json
      versions/<id>.json
  conformance.md               # 本文件
```

- `<area>` 对应契约域：`layout` / `version-manifest` / `client-plan` / `server-plan` /
  `download` / `verify` / `cache` / `java` / `progress` / `non-tty` / `error`。
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
- 时间戳、随机令牌（`auth_uuid` 等）**不参与**断言。
- 数值容差：仅 `bytes` 类允许 ±0（不允许），计数类精确。

---

## 5. 规范操作（conformance API）

实现须暴露可被 harness 调用的"纯计划"操作（**不执行 IO**）：

| 操作 | 输入 | 输出 |
|:--|:--|:--|
| `planLayout` | root/version/type | 路径集合 |
| `resolveVersion` | channel/version/snapshot | 版本条目 |
| `planClientDownload` | version/loader/platform/snapshot | `DownloadItem[]` |
| `planServerDeploy` | version/type/snapshot | `ServerDeployPlan` |
| `planClientLaunch` | version/platform/options/snapshot | `ClientLaunchPlan` |
| `planServerLaunch` | version/type/options | `ServerLaunchPlan` |
| `requiredJava` | snapshot | `JavaRequirement` |
| `verifyArtifact` | bytes + sha1 | pass/fail |
| `cacheDecision` | mtime/ttl/refresh/now | hit/miss/refresh/fallback |

> Python 侧可用内部 API 暴露（测试接缝）；Swift 侧 `Game` 已有 `generateDownloadItemInfos()`，需补纯计划入口。

---

## 6. Harness（各语言一个）

**统一契约**：读 `fixtures/**`，对每个 fixture 调对应 `operation`，规范化输出，与 `expect` 比对，输出差异。

| 语言 | 位置 | 运行 |
|:--|:--|:--|
| Python | `orzmc/tests/conformance/`（复用 `tests/fakes.py`） | `pytest` |
| Swift | `OrzMCKit/Tests/ConformanceTests/` | `swift test` |

**共同要求**
- **离线**：只用 `fixtures/snapshots/`，不打网络、不碰系统 Java。
- **可定位**：失败时打印 `id` + 字段级 diff。
- **确定性**：忽略时间/随机值（见 §4）。

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
| `OrzPythonMC` | CI | 跑 Python harness（全网离线） |
| `OrzMCKit` | CI | 跑 Swift harness |
| 父仓库 | 【待定】 | 仅汇总状态（不跨仓触发，见 plan Q6） |

- 规范变更（改 `docs/spec/**`）→ 应同步更新 fixtures；漏改由任一 harness 红灯暴露。
- 【待定】是否在父仓库加一个轻量 job 校验"fixtures 与 spec 版本一致"。

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
