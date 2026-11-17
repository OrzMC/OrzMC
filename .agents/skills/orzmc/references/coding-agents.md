# AI 编码智能体协作（Claude Code）

> **工作流决策（2026-08-29 定，2026-09-12 更新）**：编程/改代码/改配置**直接交给本地编码智能体——首选 `pi`（Pi Coding Agent；老板定：**比 claude 更省 token**）**，claude CLI 作为回退。Hermes 只做**编排**（任务拆分/规划/验收/测试/部署/git 推送/跨工具调度）。Hermes 不直接写业务代码。
> **Review 时机**：PR 仅在**最终决定合并前**做一次 code review（`git diff main...HEAD | pi -p '...'`），开发过程中不做（避免过多 review 消耗 token）。

## pi 用法（首选编码智能体，2026-09-12 启用）

| 事实 | 值 |
|:--|:--|
| 二进制 | `/usr/local/bin/pi`（npm 全局 `@earendil-works/pi-coding-agent`，v0.85.1） |
| 默认模型 | `~/.pi/agent/settings.json` → `deepseek` / `deepseek-v4-flash`（thinking=high；1M 上下文，384K 输出） |
| 非交互 | `pi -p "$(cat /tmp/brief.md)"`（冒烟实测 2.4s 返回 PONG） |
| 会话 | 存 `~/.pi/agent/sessions`；续跑 `pi -c -p "继续"`、`pi --session-id <id>`、`pi -r` 选会话 |
| 权限 | `-a/--approve` 信任项目本地文件（AGENTS.md 等）；`--mode json` 结构化输出；`-t <tools>` 工具白名单 |
| 任务书写法 | **与 claude 相同**：prompt 写文件 + `"$(cat file)"` 传参（避免反引号被 shell 求值），任务书要素见「编排要点」 |

```bash
# 一次性委派（推荐）
pi -p "$(cat /tmp/brief.md)"          # 复杂任务可加 --thinking high / -a
# 续跑同一会话
pi -c -p "继续完成剩余部分"
# 代码审查（合并前一次）
git diff main...HEAD | pi -p "审查这个改动：... 只报真实问题，无问题明确说通过"
```

⚠️ **仍要自己验收**：编码智能体自报不可信（2026-09-12 实测：claude 报「完成」，Py/单测一跑就红——本机 ffmpeg 无 drawtext 导致封面必挂）。委派后必须由 Hermes 亲自跑测试/编译/端到端。

## pi 委派标准流程（2026-09-12 两次实战定型）

```
① write_file 任务书  →  ② write_file runner.sh  →  ③ terminal(background=true,
   notify_on_complete=true) bash runner.sh  →  ④ process wait/poll  →  ⑤ Hermes 亲自复验
```

**① 任务书要素**（缺一项 pi 就容易跑偏）：目标一句话 ／ 精确文件清单（只改这些）／新增或修改的**路径优先级链** ／ 硬性要求（不引入依赖、不碰真实 HOME、不重构其他脚本）／ **必须跑的测试命令与当前基线** ／ 期望输出格式（文件清单 + 测试结果原文 + 真实 dry-run 证据）。

**② runner 模板**（`/tmp/run_pi_<topic>.sh`）：
```bash
#!/bin/bash
cd /path/to/repo || exit 1
SID=$(uuidgen | tr 'A-Z' 'a-z')            # 固定 id 才可续跑
echo "$SID" > /tmp/pi_session_<topic>.txt  # 存 id 供后续 --session-id 续跑
/usr/local/bin/pi -p --session-id "$SID" "$(cat /tmp/brief_pi_<topic>.md)"
```
⚠️ **必须经 `.sh` 文件启动**：裸内联 `pi -p "$(cat brief.md)"` 会把巨型 payload＋`$( )` 一起塞进
terminal → 踩 Hermes 解析门禁（见 `macos-bash-scripting/references/hermes-command-execution-pitfalls.md` §1）。

**③④ 观察到的正常现象**：首跑打印 `Warning: No project session found with id '<uuid>'; creating a new session with that id.` —— **不是错误**，是固定 id 建会话。单任务耗时约 **1.5–3 分钟**（本机 deepseek-v4-flash），用 `notify_on_complete` 别轮询。

**⑤ 复验纪律（本会话重复两次都抓到差距点）**：pi 的自报会附它自己跑的测试输出，但**仍必须 Hermes 亲自**：
`python3 -m unittest discover -s scripts/tests -t .`（对比基线条数）+ 真实环境 dry-run + **读改动的源码**（删除/安全类脚本逐行看门禁）+ 部署副本 `md5` 同源。见 `hermes-cron-ops/references/no-agent-job-authoring.md` §五「验收演练 recipe」。

## PR 合并流程（老板定，2026-08-29）

开发阶段只 commit 本地分支（不 push、不 review）→ 老板决定合并后：
1. **code review**（claude -p 一次）
2. **检查 PR 实际改动**（`git diff main...HEAD --stat` 核对，确认与 review 结论一致）
3. **更新 PR 标题/描述与改动匹配**（`gh pr edit`，覆盖全部 commit 内容）
4. **force push** 同步分支内容
5. **合并**（squash）

标题/描述更新必须在代码审查完成、确认实际改动之后做，避免描述与实际 diff 不符。

## 三种协作模式

| 模式 | 命令（首选 pi） | 适用 |
|:--|:--|:--|
| 一次性委派 | `pi -p "$(cat /tmp/brief.md)"`（claude 回退：`claude -p '...' --max-turns N --permission-mode acceptEdits`） | 有界单次任务（改配置/改代码）|
| 交互式会话 | terminal background + pty=true，process submit/poll（**pty 提交后需再 write `\r`**） | 多轮迭代 |
| 代码审查 | `git diff main...HEAD \| pi -p 'review...'` | 合并前审查 |

## 编排要点

1. **任务描述必须自包含**：文件路径、条目名、目标值、约束（只改 sell 不动 buy 等）、验证方式——子代理不知道对话上下文
2. **`--max-turns N` 限制**：防失控循环（改配置类 10 足够）
3. **`--permission-mode acceptEdits` 必带**（非交互模式默认不能写文件，否则产出零改动停在权限审批）；shell 验证命令也常被拦 → 验证/验收由 Hermes 编排层做
4. **子代理自报不可信**：委派后必须自己验收——`git diff` 核对 + YAML/语法验证 + 实际部署测试
5. **git 仓库上下文**：在对应 repo 目录运行，prompt 里给准相对路径
6. review prompt 要引导检查：漏洞路径/配置语义/漏网项，按严重级输出

## 坑

- ⚠️⚠️ **prompt 含反引号会触发 bash 命令替换**（2026-08-29 实测翻车）：`claude -p "...反引号..."` 里 Java 泛型/行内代码用反引号 → bash 把反引号内容当命令执行 → 语法错误 + prompt 损坏 → Claude Code 瞎跑。**正确姿势：prompt 写文件，用 `claude -p "$(cat /tmp/prompt.md)"` 传参**（命令替换结果不再递归求值，反引号安全）；或 prompt 里一律不用反引号（用普通引号/纯文本描述代码）
- ⚠️ **claude 会话沙箱只读工作目录内文件**（2026-09-02 实测）：`Read`/`cat` 读工作目录外（如 /tmp/pr_task4.md）被拦，Claude 拒绝用 python 绕过 → 任务规格文件必须放**仓库内**（如 `.task/`，实现完删）或直接粘贴进 prompt
- ⚠️ **实现会话可能整轮勘察耗尽 turns 零产出**（2026-09-02 实测两次）：大任务 `claude -p` 新会话 25-30 turns 全花在读文件分析，git status 无任何改动 → 耗尽是**正常退出**不是失败。续跑指令要点明「**勘察已足够，直接按序动手实现**」防再次空转；UUID 未固定时从 `~/.claude/projects/-Users-bot-OrzMC-plugin/*.jsonl` 按 mtime 取最新文件名即为 session UUID
- 非交互 `claude -p` 无文件写权限 → 加 `--permission-mode acceptEdits`
- shell 命令（python3 验证等）会被会话权限拦 → 验收交给 Hermes
- 模型提示 `deepseek-v4-flash is not a model this version recognizes` 为已知提示，可忽略（auto-compact 按 200k 处理）；设 `CLAUDE_CODE_MAX_CONTEXT_TOKENS` 为真实窗口可消除
- Codex 已卸载；OpenCode 可随时装（provider-agnostic 备选）

## max-turns 耗尽续跑（2026-08-29 实测验证）

`--max-turns` 耗尽报错退出，但**会话完整保存**（~/.claude/projects/）→ 可恢复：

```bash
# 委派：固定 UUID（关键！否则耗尽即弃无法续跑）
UUID=$(uuidgen)
claude -p --session-id $UUID --max-turns 20 "任务..."
# 超时/耗尽后：--resume 同 ID 续跑（上下文完整保留，实测 DeepSeek 端点可用）
claude -p --resume $UUID --max-turns 20 "继续完成剩余部分"
# 循环：耗尽→resume→再耗尽→再 resume 直到完成
```

其他恢复方式：`claude -c -p "继续"`（最近 -p 会话）；`claude -p --bg` + `claude respawn <id>`（后台会话重启）；`--name <名>` 按名 resume；`--fork-session` 分支探索。

**规避优先**：任务拆小（每个 <10 轮）；prompt 直接给执行路径（「读文件→改→构建」，减少确认磨轮次）；max-turns 按复杂度给足（配置 15-20 / 代码调试 25-30）。
