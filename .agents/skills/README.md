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
| `orzmc/` | OrzMC 服务器运维统一技能（唯一入口）：三端运维、插件构建升级、性能诊断、权限体系、测试、基岩支持。原 `OrzMC/OrzMCAdmin` 仓库迁移而来，该仓库仅作历史存档。 |

## 在 Hermes 里启用

项目技能只在**会话的工作目录位于本仓库内**时生效，且首次需信任一次：

```bash
cd <本仓库>
hermes skills trust          # 信任当前仓库（写进 ~/.hermes/config.yaml 的 skills.trusted_project_dirs）
hermes skills untrust        # 撤销
```

载入优先级：**项目技能 > 个人 `~/.hermes/skills/` > external_dirs**。同名的项目技能会覆盖个人副本，
所以在本仓库里工作时用的是仓库里的版本。
