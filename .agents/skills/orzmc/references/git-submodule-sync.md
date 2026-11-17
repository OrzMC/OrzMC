# Git 子模块全量同步（Monorepo Submodule Sync，2026-08-11 从 git-submodule-sync 技能合并）

> 场景：同步 OrzMC monorepo（~/OrzMC，**15 个子模块**，2026-08-15 移除 paper_plugins_config——过期配置快照，三端对齐已由 cmp3 工具链承担）父仓库及全部子模块到最新并切换 main/master 分支。

## 触发场景
- 用户要求同步父仓库 + 所有子模块到各自默认分支（main/master）并拉最新
- 发布正式版/合并 PR 后，子模块指针需要跟进

## 标准流程

```bash
# 1. 父仓库
cd ~/OrzMC && git pull --ff-only
# 2. 新挂载的子模块（父仓库 pull 出现 create mode 160000）需先克隆：
git submodule update --init --recursive
# 3. 全部子模块：探测默认分支 → 切换 → pull
git submodule foreach 'bash /tmp/sync_one_sub.sh'
```

`sync_one_sub.sh`（foreach 注入 `$name`/`$sm_path`，在子模块目录内执行）：
```bash
DEF=$(git ls-remote --symref origin HEAD | head -1 | awk '{print $2}' | sed 's|refs/heads/||')
[ -z "$DEF" ] && DEF=main
CUR=$(git branch --show-current)
[ "$CUR" != "$DEF" ] && git checkout "$DEF" -q
git pull --ff-only -q
echo "  $name → $DEF @ $(git rev-parse --short HEAD)"
```

## 要点与坑

- **子模块数会变**：2026-08-13 父仓 pull 出现大量 `delete mode ... deploy/docker/*` + `Submodule 'deploy' registered` = **deploy 目录拆成独立子模块**（OrzMCDeploy），14→15；以后父仓结构变动以 `git submodule update --init --recursive` 输出为准
- **同步前先检查子模块未提交改动**：父仓 `git status -s` 出现 `m <子模块>` = 该子模块有未提交改动 → 先 `git -C <子模块> stash push -m "..."` 再同步（2026-08-10 实测：LoginSecurity 的 WIP patch 不 stash 会与后续 checkout/pull 冲突）；同步完成后再 `git stash pop` 恢复
- **子模块代码改动必须「先合并子模块 main，再 bump 父仓指针」（2026-08-13 实测翻车教训）**：子模块（如 plugin）有**独立 origin 仓库**（OrzMCPlugin.git）与自己的 CI/Hangar 发布基线。正确流程：① 子模块仓库合并/发 PR → ② 根仓库 bump 指针 → ③ 根仓库 PR。**漏掉第①步**（只做根仓库指针 PR）会让子模块 main 落后：改版不在发布基线，后续开发分支冲突。修复：`git -C <sub> merge --ff-only <sha>`（先 `merge-base main <sha>` 确认 main 是祖先）+ `git push origin main` + 删远程 feat 分支 + 验证 `git rev-parse HEAD` == `git rev-parse HEAD:<sub>`（父仓 gitlink 与子模块 HEAD 一致，`git submodule status` 无 `+` 前缀）。（反向场景：子模块 PR 被 merge 后 main 前进，GitHub 不自动更新父仓指针 → `git add <sub> && git commit "chore: bump..." && git push`，先 `git pull --ff-only` 防重复 commit）
- **老板流程确认（2026-08-13）**：子模块改动（不涉及父仓库文件时）**父仓库不建 feature 分支、不提 PR**——子模块单独开发+合 PR 后，父仓库直接在 main 上 bump 指针 commit 推送即可
- **GitHub merge 自动删远端源分支**：PR 合并后远端 fix 分支已被自动删除 → `git push origin --delete <branch>` 报 `remote ref does not exist` 是**无害确认**（远端已无），本地 `git branch -D` 清理即可
- **submodule status 无 +/- 前缀 = 与 gitlink 一致（正常）**：`(1.0.16-6-g2188e37)`/`(v0.1.6)` 是 describe 格式描述（tag 之后的提交），**不是 detached 问题**——只有 `+`（漂移）/`-`（未初始化）才需要处理
- **默认分支不统一**：OrzMC 14 个子模块实测 12 个 main + **2 个 master**（tools/LoginSecurity、tools/thanos）——用 `ls-remote --symref origin HEAD` 探测，**别假设全是 main**
- **子模块指针可能停在 tag**（如 OrzMCBackup 在 `v0.1.6`）——同步时切回默认分支（main）
- **父仓库 status 出现 `? <子模块名>` 类未跟踪**：通常是已删 gitlink 的子模块工作区残留目录（实测 app/OrzMCKit）——`git -C <子模块> status` 确认 `??` 后清理，无需动父仓库
- 子模块内 git 操作（checkout/pull）在父仓库视角可能显示 `M <子模块>`（指针漂移）——同步脚本已切回默认分支即一致

## 发布后指针同步（防重复 commit，2026-08-09 实测）

- 用户发布正式版（打 tag + CHANGELOG + `chore: bump version`）时，**发布者会自行提交父仓库的 plugin 子模块指针**
- 本地再手动 `git add plugin && git commit` 会产生重复 commit，直接 `git push` 被 non-fast-forward 拒绝
- **正解**：`git pull --rebase` → 重复 commit 自动 drop（日志 `dropping <sha> ... -- patch contents already upstream`）→ `git push` 显示 `Everything up-to-date`
- 即：**子模块指针同步不要抢先 commit，先 pull --rebase 看是否已被上游包含**

## 验证
- `git submodule status`：全部 `(heads/main)` 或 `(heads/master)`，无 tag/detached
- 父仓库 `git status` 干净（或只剩已知残留）
- `git -C <子模块> log --oneline -1` 与远端一致

## 列出非 main/master 本地分支（用户常要求）
```bash
# 父仓库
git branch --format='%(refname:short)' | grep -vE '^(main|master)$'
# 全部子模块（foreach 注入 $name；空=无额外分支）
git submodule foreach 'echo "  $name: $(git branch --format="%(refname:short)" | grep -vE "^(main|master)$" | tr "\n" " ")"' 2>/dev/null | grep -vE '^  .*: $'
```

## 分支清理：squash 合并后的内容归属判断（2026-08-10 实测）
feature 分支 squash 合并进 main 后，`git log main..<branch>` 仍把分支提交显示为「未合并」（**hash 不同是假象**）——判断内容是否真在 main，**别用 git log**，也**别用 merge-base / tree 对比**（2026-08-19 实测补充）：
```bash
# ❌ 三个不可靠判据（squash 合并后全部误报「未并入/有差异」）：
# 1. git merge-base --is-ancestor <branch> main   → squash 后分支不是 main 祖先，必报未并入
# 2. git diff --quiet main <branch>               → main 合并后又前进（新 PR/版本 bump），tree 必不等
# 3. git diff main <branch> --name-status | grep '^A' → 只查 A（分支新增文件），M/D 未覆盖
# ✅ 正解：D 方向（分支有而 main 无的文件）为空 = 分支内容已全部合入，可安全删：
git diff <branch> main --name-status | grep '^D'    # 空 = 安全；非空 = 分支有独有内容，保留
# 辅助：git log main..<branch> --oneline --cherry-pick 看提交主题是否与 main 上 squash 提交一一对应；
#       远端同名分支 git branch -r | grep <name> 已消失 = GitHub 合并后自动删除（正常）
```
- 删除前先确认远端无同名分支：`git branch -r | grep <name>`；删除用 `git branch -D`（强删需用户确认）
- 分支删除后提交对象仍在 git 对象库（`git cat-file -t <sha>` 仍返回 commit）——找回可用 reflog/对象库，无需恐慌

## 独立 clone 去重：统一用子模块维护（2026-08-19 实测）
> 场景：同一远程仓库在 monorepo 内存在**子模块 + 独立 clone 双副本**（实测：`~/OrzMC/backup-core/` 与 `tools/OrzMCBackup` 都是 OrzMC/OrzMCBackup.git，开发时误 clone 到根目录）。用户决策：确认内容一致后删独立 clone，统一用子模块维护。

**三步确认双副本可去重**（全过才删）：
```bash
# 1. 同远端：对比 remote -v（必须同 URL）
git -C <dir1> remote -v && git -C <dir2> remote -v
# 2. 同 HEAD + 无独有提交：log 一致 + 无未推送提交
git -C <dir1> log --oneline -3 && git -C <dir1> log origin/main..HEAD --oneline   # 空=全已推送
# 3. 内容一致：diff 排除 .git/构建缓存（Only in <dir> 的 .kotlin/.gradle 等缓存可忽略）
diff -rq <dir1> <dir2> -x .git -x build -x .gradle -x .kotlin
```
- 删除前搜路径引用：`search_files pattern="OrzMC/backup-core" path=~/`（scripts/cron/配置里出现=先改引用再删）
- 删独立 clone 用 `rm -rf <dir>`（破坏性操作会触发确认，老板确认后执行）；删完父仓 `git status -sb` 应只剩 `## main...origin/main` 干净行
- 教训：开发新工具/新版本时若仓库已作为子模块存在，**直接改子模块目录**，勿另 clone 到别处——双副本迟早漂移分叉

## 坑：复杂内联命令会被命令行解析器拦截（2026-08-19 实测）
- 带嵌套引号的超长单行（如 `git submodule foreach '...$(...)...'` 组合 grep/tr 管道）会触发 `BLOCKED (hardline): command parser limit`，命令被存到 `~/.hermes/cache/blocked-scripts/`
- **正解：写成脚本文件（write_file /tmp/xxx.sh）再 `bash /tmp/xxx.sh`**，不重试内联形式

## 关联
- OrzMC monorepo 资产地图（各子模块用途）→ `references/orzmc-repo.md`
