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
| **主题** | 父仓库 AI 协作结构改造（已完成）+ 产品统一化计划启动 |
| **状态** | 🟡 协作结构已完成、待提交；产品统一化处于 Phase 0 |
| **关联方案** | `docs/product-unification-plan.md`（Phase 0 文档落地，Phase 1 阻塞于 Q1/Q2/Q3） |
| **涉及仓库** | `parent`（本轮改动全部在父仓库，未动任何子模块） |
| **下一步** | 见第 4 章 |

---

## 2. 状态快照（Repo State）

### 2.1 父仓库（OrzMC）

| 项 | 值 |
|---|---|
| 分支 | `main` |
| 本轮新增（**未提交**） | `AGENTS.md`、`CLAUDE.md`、`CONTRIBUTING.md`、`.github/PULL_REQUEST_TEMPLATE.md`、`docs/README.md`、`docs/product-unification-plan.md`、`HANDOFF.md` |
| 本轮修改（**未提交**） | `README.md`（目录树 + 协作入口章节） |
| 本轮删除 | `GEMINI.md`、`.cursor/rules/`（为不需要的 agent 预留，已移除） |
| 已知未提交 | `plugin` 子模块指针漂移（见 2.2） |

> ⚠️ **本批次尚未提交**。新设备 pull 时如果看不到上面这些文件，说明还没 push——
> 需先在**原设备**提交并 push，否则跨设备会丢失。

### 2.2 子模块在途状态

| 子模块 | 当前指针 | 分支 | 是否偏离父仓库记录 | 备注 |
|---|---|---|---|---|
| `plugin` | `bd908b8` | `develop` | ✅ **偏离**（父仓库记录 `5eadd6e`） | 工作区干净；父仓库 `git status` 显示 `M plugin`。**需决策**：bump 到 develop 还是还原为记录指针 |
| 其余 14 个 | 见 `git submodule status` | `main`/`master` | 否 | 指针与父仓库记录一致 |

> `git submodule status` 中行首 `+` = 当前检出与父仓库记录不一致；`-` = 未初始化。

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
| Q1 | `OrzMCKit`（Swift 引擎）仓库能否拉取核对类型？ | ☐ 未决 | 需拉取（阻塞 plan Phase 1） |
| Q2 | `orzmc-spec` 落点：独立仓库 + `spec/` 子模块，还是父仓库 `docs/spec/`？ | ☐ 未决 | 独立仓库 |
| Q3 | 是否把 `OrzMCKit` 登记为父仓库子模块？ | ☐ 未决 | 登记 |
| Q4 | `plugin` 子模块指针漂移如处理？ | ☐ 未决 | 若 develop 是有意为之则 bump，否则 checkout 还原 |

---

## 4. 下一步（Next Actions，按优先级）

- [ ] **P0｜提交本批父仓库改动**（AGENTS/CLAUDE/CONTRIBUTING/HANDOFF/docs/README），否则跨设备丢失。
- [ ] **P0｜决定 `plugin` 指针漂移处理**（Q4）。
- [ ] **P1｜Phase 0**：写 `docs/product-architecture.md`（分层、所有权、允许依赖方向、禁止事项）。
- [ ] **P1｜清 Q1–Q3**，解阻塞 Phase 1 的 `orzmc-spec`。
- [ ] **P2｜可选**：加轻量 CI 校验 `AGENTS.md` 子模块登记表与 `.gitmodules` 一致。
- [ ] **P2｜Phase 1**：`orzmc-spec` 数据模型 + 字段对照表。

---

## 5. 会话日志（Session Log，只追加，最新在最上）

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
