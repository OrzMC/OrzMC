# 贡献指南 — OrzMC 父仓库（产品伞）

> 本文件面向**人与 AI 智能体**。AI 智能体的规则事实源是 [`AGENTS.md`](AGENTS.md)，
> 本文件是同一套流程的人类可读版；冲突时以 `AGENTS.md` 为准。
>
> 你要改的是**某个子模块的代码**？请直接去那个子模块仓库的 `CONTRIBUTING.md` / `AGENTS.md`。
> 本文件只讲**父仓库**（子模块指针 + 伞级内容）的贡献方式。

---

## 1. 先理解仓库性质

父仓库 `OrzMC/OrzMC` 是**聚合型 monorepo / 产品伞**，通过 Git 子模块汇集多个独立产品：

- 父仓库几乎不含业务代码，职责是**锁定子模块版本**、承载伞级文档/脚本、协调跨仓方案。
- **代码改动发生在子模块仓库**，父仓库只 bump 指针。
- 每个子模块有自己的构建、测试、CI、分支模型与发布节奏。

一句话：**父仓库 bump 指针，子模块改代码。**

---

## 2. 获取代码

```bash
# 推荐：连同子模块一起克隆
git clone --recurse-submodules https://github.com/OrzMC/OrzMC.git
cd OrzMC

# 已克隆但子模块为空
git submodule update --init --recursive
```

各子模块的默认分支见 [`AGENTS.md`](AGENTS.md) 第 4 章登记表。

---

## 3. 三种常见改动

### A. 只改父仓库自有内容（文档 / 脚本 / README）

直接改 `docs/`、`scripts/`、`README.md`、`images/`、`skins/` 等，然后：

```bash
git add docs/xxx.md
git commit -m "docs: 说明改了什么"
git push
```

### B. 更新某个子模块到远端最新

```bash
git submodule update --init --recursive
cd <子模块路径>
git fetch origin && git switch <目标分支> && git pull --ff-only
cd -
git add <子模块路径>
git commit -m "chore(submodule): bump <名称> 指针到 <分支> 最新（说明）"
git push
```

### C. 修改子模块代码 / 文档

1. 进入子模块，**先读它的** `AGENTS.md` / `CONTRIBUTING.md`。
2. 在子模块里开分支（命名与目标分支按子模块规范，如 `feat/*` / `fix/*`）。
3. 改代码 → 跑该子模块的质量门禁 → 提交（Conventional Commits）→ 推送到子模块远端。
4. 到**子模块的 GitHub 仓库**开 PR，走它自己的 CI 与评审，合并。
5. 回到父仓库，把子模块指针 bump 上去（同 B）。

> ⚠️ 不要在子模块处于 **detached HEAD** 时提交；先 `git switch <分支>`。

---

## 4. 父仓库的提交规范

- **Conventional Commits + 中文描述**（与各子模块保持一致）。
- 子模块指针提交格式：
  ```
  chore(submodule): bump <名称> 指针到 <分支> 最新（<一句话说明>）
  ```
  例：`chore(submodule): bump deploy 指针到 main 最新（v0.0.6：easybot 上限回调 512M）`
- **一次提交只 bump 一个子模块**（现状惯例，便于审查与回滚）。
- 提交前自查：
  ```bash
  git submodule status          # 指针与预期一致
  git status --porcelain        # 无意外未提交的子模块变更
  git diff --submodule          # 确认子模块内部差异摘要
  ```

---

## 5. 父仓库的"验证"

父仓库**没有**根级构建/测试。它的验证 = **组合正确性**：

- [ ] `git submodule status` 指针符合预期，且都指向**远端已存在**的分支/提交。
- [ ] `git status` 干净，没有忘记提交的子模块指针变更。
- [ ] 若改了伞级文档，已更新 [`docs/README.md`](docs/README.md) 索引。
- [ ] 子模块自身的门禁已在对应仓库跑过（父仓库不代跑）。

---

## 6. PR 流程

- 使用 [PR 模板](.github/PULL_REQUEST_TEMPLATE.md) 填写变更类型与检查清单。
- 跨子模块的产品级变更：在 PR 说明里列清涉及哪些子模块、各自 PR/版本。
- 重要或架构级改动建议换一个厂商的 AI 智能体交叉审查，或本地 `/review` 自查后再提。

---

## 7. 文档治理

- 每份父仓库文档头部标注「**状态 / 最后更新**」（如「草案」「现行」「已归档」）。
- 新文档加入 [`docs/README.md`](docs/README.md) 索引，按读者角色归类。
- **单一事实源**：AI 指引只维护 `AGENTS.md`（pi / Codex 直接读取）；`CLAUDE.md` 是 Claude
  的桥接入口，`@AGENTS.md` 引入，不写内容。

---

## 8. 许可证

- 父仓库自身见根 `LICENSE`。
- **各子模块有各自的许可证**，贡献对应子模块时以该子模块的 `LICENSE` 为准。

---

## 9. 相关文档

- AI 智能体指引（事实源）：[`AGENTS.md`](AGENTS.md)
- 跨会话/跨设备交接：[`HANDOFF.md`](HANDOFF.md)
- 文档索引：[`docs/README.md`](docs/README.md)
- 产品总览：[`README.md`](README.md)
- 进行中的计划：[`docs/product-unification-plan.md`](docs/product-unification-plan.md)
