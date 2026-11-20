# 项目技能（Project Skills）

本目录存放**给 AI Agent 用的过程文档**（技能），与代码同仓、同 PR 评审。

## 约定

- 每个技能一个目录：`.agents/skills/<name>/SKILL.md`，可带 `references/`、`scripts/`、`templates/`。
- `SKILL.md` 用标准 frontmatter（`name`、`description`，可选 `version`、`tags`、`platforms`）。
- **真实值一律占位符化后再入库**：域名 `{DOMAIN}`、家宽 IP `{HOME_IP}`、云主机 `{CVM_IP}`、
  密码/Token `{PASSWORD}` / `{TOKEN}`。真实值只留在各人本机的私人技能副本里。
  公开信息确需保留的，逐条写进仓库根的 `.secretignore`。
- 改技能同样走「分支 → PR → CI 全绿 → squash 合并」，不直推 `main`。

## 目录里现在的技能

| 目录 | 说明 |
|---|---|
| `orzmc/` | **git submodule** → [`OrzMC/OrzMCAdmin`](https://github.com/OrzMC/OrzMCAdmin)：OrzMC 服务器运维统一技能（唯一入口），三端运维、插件构建升级、性能诊断、权限体系、测试、基岩支持。技能有独立版本线与 tag（当前 `v2.6.23`），可单独 `git clone` 复用。

## 技能是子模块：怎么改

```
改技能：本机技能目录 → 发布脚本 → OrzMCAdmin 的 PR + tag → 父仓库 bump 指针（第二个小 PR）
```

- `git clone` 本仓库后必须 `git submodule update --init --recursive`，否则 `.agents/skills/orzmc/` 是空目录。
- 更新到技能仓最新：`git submodule update --remote .agents/skills/orzmc`，然后把变化提交成 `chore(skills): bump …` 的 PR。
- **不要在父仓库里直接改技能文件**：父仓库只存一个 commit 指针，改了也不会进技能仓，下次 bump 就丢。
- 本机一键：`bash ~/AppData/Local/hermes/scripts/orzmc_publish.sh --merge`（脱敏 → 技能仓 PR → tag → 自动 bump 父仓库指针）。

## 在 Hermes 里启用

项目技能只在**会话的工作目录位于本仓库内**时生效，且首次需信任一次：

```bash
cd <本仓库>
hermes skills trust          # 信任当前仓库（写进 ~/.hermes/config.yaml 的 skills.trusted_project_dirs）
hermes skills untrust        # 撤销
```

载入优先级：**项目技能 > 个人 `~/.hermes/skills/` > external_dirs**。同名的项目技能会覆盖个人副本，
所以在本仓库里工作时用的是仓库里的版本。
