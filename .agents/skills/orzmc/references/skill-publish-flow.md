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
公网 IP：家宽 WAN → `{HOME_IP}`、云主机 → `{CVM_IP}`，**按 IP 段写成正则规则，不要靠发布前手改文档**
（已落 `114\.240\.<x>\.[0-9]{1,3}`→`{HOME_IP}`、`121\.5\.164\.<x>`/`1\.117\.58\.<x>`→`{CVM_IP}`）。
只对**完整公网 IP 形态**写规则：四段数字通配会命中插件版本号（`3.26.11.2`）造成日常误杀，
所以规则按已知网段前缀写，未知网段交给门禁报警。

判据：**enc 是黑名单，leak 门禁只能证明「黑名单里的没漏」**。新增一类敏感值时先补 `ENC_RULES`
再发布，否则门禁全绿也会漏。

### 门禁中止了怎么办

leak 门禁中止发布是**设计行为，不是故障**——说明某个真实值没有对应规则。处理顺序固定：

1. **不要**去改本机真源里的值（B 侧必须保留真实域名/IP 才能操作服务器）。
2. 从门禁输出里认出被拦的那个值，判断它属于哪一类（域名 / 内网 / 家宽 WAN / 云主机 / 密钥）。
3. 在 `orzmc_publish.sh` 的 `ENC_RULES` 补一条**按网段前缀**的规则，重跑 `--status` 确认差异里只剩占位符，再正式发布。
4. 发布后回本机仓库 `grep -rn "<该值>" .agents/skills/orzmc --include='*.md'` 必须为空，并 `grep -rl "{HOME_IP}\|{CVM_IP}"` 有命中才算脱敏真落地。

**已经进了 git 历史的真实值不会因为新增规则而消失**：规则只作用于本次镜像产出的文件内容。
要清历史必须改写 commit + `force push`，成本大于收益（家宽 IP 本身会变），
正确做法是**明确告诉老板「历史里那一条还在，要不要清」**，由他拍板，不要默默 force push，
也不要假装已清干净。

## 发布后

1. 回读合并结果：`gh pr view <n> --json state,mergeCommit`（命令回显可能被截成 `1 lines output`，不可信）。
2. 本机开发克隆同步：`git switch main && git pull --ff-only`（squash 合并后本地 main 会 diverged，属正常）。
3. 清理 `chore/skill-sync-*` 本地分支：`git branch -D` 属审批门、老板常不在跟前 → **先做 1、2 两步（不删分支照样能 pull）**，分支清理留到下次，别为删一个分支把整轮验证卡死。

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
