# CLAUDE.md — Claude Code 入口

> 父仓库统一 AI 指引见 [`AGENTS.md`](AGENTS.md)（**单一事实源**，Claude Code 自动加载）。
> 本文件仅为 Claude Code 桥接入口，**不重复内容**；新增/修改指引只改 `AGENTS.md`。
>
> 各子模块还有自己的 `AGENTS.md`（改某个子模块前先读它）。

## 使用约定

1. **父仓库铁律**：父仓库只 bump 子模块指针，**代码改动进子模块**——详见 `AGENTS.md` 第 2 章。
2. **改哪个子模块，先读哪个子模块的 `AGENTS.md`**（分支模型/构建命令各不同）。
3. **接手/恢复工作先读** `HANDOFF.md`（跨会话/跨设备交接：当前状态、下一步、会话日志）。
4. **进行中的计划**：`docs/product-unification-plan.md`（推进前先读）。
5. **提交纪律**：Conventional Commits + 中文；一次提交只 bump 一个子模块。
6. **会话结束前更新** `HANDOFF.md`；**修改指引**只改 `AGENTS.md`，本文件是桥接、不新增内容。

@AGENTS.md
