# HANDOFF.md — OrzMC 跨会话 / 跨设备交接文档

> **用途**：任何 AI 智能体或维护者在**新会话 / 新设备**接手父仓库工作时，先读
> [`AGENTS.md`](AGENTS.md)（规则）+ 本文件（状态）+ 进行中方案，即可无损恢复上下文。
>
> **为什么必须有**：聊天记录不跨会话、不跨设备；本地未提交状态不跨设备。
> **凡是"下次还要知道"的信息，都必须落到 Git 里的文件**——本文件就是那个落点。
>
> **维护规则**：
> 1. 每次会话**结束前**更新第 1 章「当前焦点」、第 2 章「状态快照」、第 5 章「会话日志」。
> 2. 会话日志**只追加不删改历史**，最新在最上。
> 3. 本文件是**状态**，不是**规则**（规则在 `AGENTS.md`）也不是**方案**（方案在 `docs/`）。
>    只放"现在到哪了、下一步做什么"，不复制规则与方案正文。
>
> **最后更新**：2026-10-13 by pi

---

## 0. 接手速查（Session Start Checklist）

```bash
git pull --recurse-submodules          # 拉到各设备一致状态
git submodule update --init --recursive
git status --porcelain                 # 有无未提交的父仓库/子模块变更
git submodule status                   # 子模块指针是否符合预期
```

然后按顺序读：

1. [`AGENTS.md`](AGENTS.md) —— 规则（三条铁律、子模块登记表、协作流程）
2. **本文件** —— 当前状态与下一步
3. [`docs/product-unification-plan.md`](docs/product-unification-plan.md) —— 进行中的方案（如有相关任务）

**结束会话前**：更新本文件第 1 / 2 / 5 章，并 `git add HANDOFF.md` 提交。

---

## 1. 当前焦点（Current Focus）

| 项 | 内容 |
|---|---|
| **主题** | 产品统一化 — Phase 1（`docs/spec/` 规范启动） |
| **状态** | 🟡 Phase 0 完成；Phase 1 已启动（`docs/spec/README.md` + `data-model.md` 草案） |
| **关联方案** | `docs/spec/`（规范）+ `docs/product-architecture.md` + `docs/product-unification-plan.md` |
| **涉及仓库** | `parent`（本轮改动全部在父仓库，未动任何子模块） |
| **下一步** | 见第 4 章 |

---

## 2. 状态快照（Repo State）

### 2.1 父仓库（OrzMC）

| 项 | 值 |
|---|---|
| 分支 | `main` |
| 已提交并推送 | AI 协作结构（`684d2ea`/`1142091`）+ Phase 0 架构（`93fb39b`） |
| 本轮未提交 | 新增 `docs/spec/README.md`、`docs/spec/data-model.md`；修改 `docs/product-architecture.md`（产品形态 §1.2 + OrzMCKit 重定位）、`docs/product-unification-plan.md`（D7/D8 + Q2/Q3/Q5）、`docs/README.md`、`HANDOFF.md` |
| 已删除（历史） | `GEMINI.md`、`.cursor/rules/`（为不需要的 agent 预留，已移除） |
| 已知未提交 | 仅 `plugin` 子模块指针（**预期**，见 2.2） |

### 2.2 子模块在途状态

| 子模块 | 当前指针 | 分支 | 父仓库记录 | 说明 |
|---|---|---|---|---|
| `plugin` | `bd908b8` | `develop` | `5eadd6e`（main） | **有意为之，不要 bump**：plugin 工作流先在 `develop` 迭代、里程碑合并 `main`；父仓库**始终钉 `main` 发布线**，故本地检出 `develop` 时 `git status` 显示 `M plugin` 属预期 |
| 其余 14 个 | 见 `git submodule status` | `main`/`master` | 一致 | 无偏离 |

> `git submodule status` 中行首 `+` = 当前检出与父仓库记录不一致；`-` = 未初始化。
> **父仓库指针钉发布线（`main`），不钉开发线（`develop`）。**

### 2.3 验证命令

```bash
git submodule status
git status --porcelain
git diff --submodule
```

---

## 3. 待决策 / 开放问题

> 产品统一化的开放问题以 `docs/product-unification-plan.md` 第 7 章为准；此处只列**当前阻塞推进**的。

| # | 问题 | 状态 | 建议默认 |
|---|---|---|---|
| Q1 | `OrzMCKit`（Swift 引擎）仓库能否拉取核对类型？ | ✅ 已决 | 可访问（`main`），已浅克隆核验：`Game`/`Fabric` + `orzmc` CLI；引擎依赖 `MojangAPI`/`PaperMC`/`OrzSwiftKit` 在个人仓库 |
| Q2 | `orzmc-spec` 落点？ | ✅ 已决 | 父仓库 `docs/spec/`；成熟后再下沉独立仓库 |
| Q3 | `OrzMCKit` 如何定位？ | ✅ 已决 | **Swift 可复用基础组件**（非 App 私有引擎），服务 Swift CLI 与 GUI；登记为子模块见 plan Q4 |
| Q4 | `plugin` 子模块指针漂移如何处理？ | ✅ 已决 | **不 bump**：`develop` 是迭代线、`main` 是发布线，父仓库钉 `main`；`M plugin` 属预期 |

---

## 4. 下一步（Next Actions，按优先级）

- [x] **P0｜提交并 push 父仓库 AI 协作结构**（`684d2ea` + `1142091`）。
- [x] **P0｜决定 `plugin` 指针漂移处理**：结论=**不 bump**（父仓库钉 `main` 发布线，本地检出 `develop` 属迭代常态）。
- [x] **P1｜Phase 0**：产出 `docs/product-architecture.md`（分层、所有权、允许依赖方向、禁止事项）。
- [x] **P1｜提交并 push Phase 0**（`93fb39b`）。
- [x] **P1｜Q2/Q3 已决**：规范落 `docs/spec/`；`OrzMCKit` 定位 Swift 可复用基础组件。
- [x] **P1｜Phase 1 启动**：产出 `docs/spec/README.md` + `docs/spec/data-model.md`（含字段对照）。
- [ ] **P1｜提交本批 Phase 1 改动**（未提交，否则跨设备丢失）。
- [ ] **P1｜Phase 0 评审**：确认决策 D1–D8 与架构文档。
- [ ] **P1｜Phase 1 续**：补 `docs/spec/behavior.md`、`cli-surface.md`、`install-update.md`、`conformance.md`。
- [ ] **P2｜可选**：加轻量 CI 校验 `AGENTS.md` 子模块登记表与 `.gitmodules` 一致。
- [ ] **P2｜治理**：是否把 `OrzMCKit` 登记为子模块（plan Q4）。

---

## 5. 会话日志（Session Log，只追加，最新在最上）

### 2026-10-13 — pi（Phase 1 启动：`docs/spec/` 规范雏形）

**做了什么**
- 记录决策：Q2 规范落父仓库 `docs/spec/`（成熟后下沉独立仓库）；Q3 `OrzMCKit` 定位
  **Swift 可复用基础组件**；Q5 先 Markdown + JSON 样例。新增 D7（一个 `orzmc`、CLI+GUI 两面、
  共核、互相安装/打开）与 D8。
- 据产品形态更新 `docs/product-architecture.md`（§1.2 产品形态；L2 改称「产品面」；治理表重定位 `OrzMCKit`）。
- 启动 Phase 1：新建 `docs/spec/README.md`、`docs/spec/data-model.md`（含 `RootLayout`/版本/下载/
  Java/启动计划/安装记录等实体 + Python↔Swift 字段对照表）。

**结果 / 产出文件**
- 新增：`docs/spec/README.md`、`docs/spec/data-model.md`
- 修改：`docs/product-architecture.md`、`docs/product-unification-plan.md`、`docs/README.md`、`HANDOFF.md`

**遗留 / 下一步**
- 本批未提交（见 2.1）；下一步补 `behavior.md` / `cli-surface.md` / `conformance.md`，并处理 plan Q4（`OrzMCKit` 子模块登记）。

### 2026-10-13 — pi（Phase 0：产品架构与边界冻结）

**做了什么**
- 探得 Q1：`OrzMC/OrzMCKit` 可访问，已浅克隆核验，发现三项关键事实：
  1. `OrzMCKit` 自带同名 `orzmc` CLI（swift-argument-parser），与 Python CLI 功能重叠；
  2. Swift 引擎是依赖链：`OrzMCKit` → `MojangAPI` / `PaperMC` / `OrzSwiftKit`，**后三者是个人仓库**；
  3. 根目录布局两边不一致（Swift `manifest/<v>/...` vs Python `versions/<v>/...`），类型支持也不同。
- 产出 Phase 0 交付物 `docs/product-architecture.md`：
  仓库角色地图、L0–L3 分层、引擎六阶段映射、**允许依赖方向矩阵**、禁止事项、治理与已知差异。
- 回填 `docs/product-unification-plan.md`（第 2 章核验事实 / Q1 / Phase 0 状态）与 `docs/README.md` 索引。

**结果 / 产出文件**
- 新增：`docs/product-architecture.md`
- 修改：`docs/README.md`、`docs/product-unification-plan.md`、`HANDOFF.md`

**遗留 / 下一步**
- 本批未提交（见 2.1）；下一步清 Q2/Q3 → 开 Phase 1 `orzmc-spec`。

### 2026-10-13 — pi（提交、push 与 plugin 漂移决策）

**做了什么**
- 将 AI 协作结构整理为一次提交并 push `origin/main`（起始提交 `684d2ea`）。
- 处理 `plugin` 指针漂移：确认为**有意为之**——plugin 工作流先在 `develop` 迭代、
  里程碑合并 `main`；父仓库钉 `main` 发布线，故本地检出 `develop` 时显示 `M plugin` 属预期，**不 bump**。

**结果 / 产出文件**
- 提交并推送：`AGENTS.md` / `CLAUDE.md` / `CONTRIBUTING.md` / `HANDOFF.md` /
  `.github/PULL_REQUEST_TEMPLATE.md` / `docs/README.md` / `docs/product-unification-plan.md` / `README.md`
- 更新 `HANDOFF.md`：记录 Q4 决策与「父仓库钉发布线」策略。

**遗留 / 下一步**
- Phase 0 `docs/product-architecture.md`；清 Q1–Q3 以解阻塞 `orzmc-spec`。

### 2026-10-13 — pi（父仓库 AI 协作结构改造）

**做了什么**
- 核验 `python` 与 `app` 的真实分层：app 是 SwiftUI 前端、引擎在外部 `OrzMC/OrzMCKit`；
  python 是「引擎 + CLI + 安装器 + 自升级」全栈；真正重复在**引擎层**。
- 产出 `docs/product-unification-plan.md`：现状事实、决策 D1–D6、Phase 0–5、开放问题 Q1–Q6、上下文包。
- 为父仓库搭建 AI 协作结构：`AGENTS.md`（事实源）、`CLAUDE.md`（Claude 桥接）、
  `CONTRIBUTING.md`、`.github/PULL_REQUEST_TEMPLATE.md`、`docs/README.md`。
- 按工具偏好（pi / Codex / Claude）收敛：移除 `GEMINI.md`、`.cursor/rules/`。
- 更新 `README.md`（目录树 + 「协作与文档」入口）。

**结果 / 产出文件**
- 新增：`AGENTS.md`、`CLAUDE.md`、`CONTRIBUTING.md`、`.github/PULL_REQUEST_TEMPLATE.md`、
  `docs/README.md`、`docs/product-unification-plan.md`、`HANDOFF.md`
- 修改：`README.md`
- 删除：`GEMINI.md`、`.cursor/`

**遗留**
- 本批改动**尚未提交**（见 2.1）。
- `plugin` 子模块指针漂移未处理（见 2.2 / Q4）。
- 仅列计划，未开始 `orzmc-spec`。

---

## 6. 环境与设备差异（Environment）

> 跨设备接手的常见坑：某设备缺工具/凭据、路径不同、子模块未初始化。新设备首次接手时补记。

| 设备 | 用途 | 已具备 | 备注 |
|---|---|---|---|
| （示例）macOS 开发机 | 主力 | git / pi / claude / 各语言工具链 | 路径 `/Users/bot/OrzMC` |
| （待补） | | | |

**通用注意**
- 首次 clone 必须 `--recurse-submodules`，否则子模块目录为空。
- 子模块默认分支各不相同（见 `AGENTS.md` 第 4 章）；`plugin` 开发用 `develop`，其余多为 `main`。
- 不要在**未初始化的子模块**目录里工作。

---

## 7. 禁忌 / 易错点（本仓库特有）

- ❌ 在父仓库直接提交子模块**内部**文件——代码改动必须进子模块仓库（`AGENTS.md` 铁律 1）。
- ❌ 在子模块 detached HEAD 状态下改代码并提交——先 `git switch <分支>`。
- ❌ 把"只存在于本机/本会话"的关键信息留在脑子里——**一律写进本文件或 `docs/`**。
- ❌ 直接改 `tools/thanos`（外部上游仓库）。
- ❌ 修改 `AGENTS.md` 之外的桥接文件（`CLAUDE.md`）写内容——桥接不写内容。

---

## 8. 交接模板（复制用）

> 开启一个新任务或结束一次会话时，用此模板在「第 5 章 会话日志」顶部追加一条。

```markdown
### YYYY-MM-DD — <agent/人>

**做了什么**
- 

**结果 / 产出文件**
- 

**遗留 / 下一步**
- 
```
