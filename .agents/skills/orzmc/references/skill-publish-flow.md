# 技能发布流（B → 项目仓库）

**状态**：已落地（2026-11-18）｜**取代**：`orzmc_bisync.sh` 双向镜像 + `OrzMC/OrzMCAdmin` 独立仓库

## 模型

```
本机技能目录 B（真实值）               项目仓库 R（占位符版，公开）
~/AppData/Local/hermes/skills/gaming/orzmc  →  E:/dev/OrzMC/.agents/skills/orzmc/
        ↑ 会话在仓库外用它                        ↑ 会话在仓库内优先用它
```

- **单向**：只从 B 推到 R，绝不反向拉取（R 里是脱敏版，拉回来会污染真实值）。
- **B 是唯一真源**；R 只是可公开的镜像。想改技能改 B，然后发布。
- 同一台机器上两个副本同时存在是**故意的**：仓库外需要真实域名/IP 才能操作服务器，
  仓库内用占位符避免泄露。

## 发布

```bash
bash ~/AppData/Local/hermes/scripts/orzmc_publish.sh            # 建分支 + 开 PR（默认）
bash ~/AppData/Local/hermes/scripts/orzmc_publish.sh --merge    # 等 CI 绿后自动 squash 合并
bash ~/AppData/Local/hermes/scripts/orzmc_publish.sh --status   # 只看差异，不提交
```

脚本做的事：镜像 B→R（保持目录结构）→ `enc` 脱敏 → leak 门禁 → 先 `git add` 再判断
是否有真实改动（**无变化静默退出**，可安全放 cron）→ 分支 `chore/skill-sync-<时间>`
→ commit → push → `gh pr create`。

`OrzMC/OrzMC` 的 `main` 要求走 PR（`required_pull_request_reviews`），所以**不能**直推；
`--merge` 会 `gh pr checks --watch` 后 `gh pr merge --squash --delete-branch`。

## 脱敏规则（enc）

真实值 → 占位符，规则在脚本 `ENC_RULES`：域名 `{SERVER_HOST}`、仓库名 `{SERVER_NAME}`、
内网 `{LAN_IP}`、机器人密码 `{BOT_PASSWORD}`、API `{API_TOKEN}`、邮箱 `{EMAIL}`。
公网 IP 单独处理：家宽 WAN → `{HOME_IP}`，云主机 → `{CVM_IP}`（**必须手工改**，脚本只硬拦
已知 IP 段、其它四段数字只报警——插件版本号如 `3.26.11.2` 也会命中，硬拦会天天误杀）。

判据：**enc 是黑名单，leak 门禁只能证明「黑名单里的没漏」**。新增一类敏感值时先补 `ENC_RULES`
再发布，否则门禁全绿也会漏。

## 仓库侧约定

- `.agents/skills/README.md`：目录约定与 `hermes skills trust` 用法。
- `AGENTS.md` §6.1：项目技能规则（真实值禁止入库、改技能走 PR）。
- 技能目录里保留仓库自有的 `README.md` / `LICENSE`，脚本镜像时不动它们。

## Hermes 侧

- 首次需信任仓库：`cd E:/dev/OrzMC && hermes skills trust`（写进 `config.yaml`
  的 `skills.trusted_project_dirs`）。
- 载入优先级：**项目技能 > 个人 `~/.hermes/skills/` > external_dirs**；同名时仓库版覆盖本机版。
  `hermes skills list` 只列已安装（个人/hub）技能，**不显示**项目技能，别用它判断是否生效。

## 已退役

- `OrzMC/OrzMCAdmin` 仓库：只作历史存档，不再更新。
- `orzmc_bisync.sh`：双向镜像，方向已改为单向发布，勿再用。
