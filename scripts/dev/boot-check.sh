#!/usr/bin/env bash
# 新会话**开机自检**：确认"仓库是不是最新的、能不能直接开工"。
#
# 为什么需要它：交接文档（HANDOFF/AGENTS）是可靠的，但**代码可能是旧的** ——
# 换了设备没拉、父仓库落后远端、子模块没初始化、或指针指向一个本地不存在的提交。
# 这个脚本把"能不能开工"变成一条命令，避免接手的人（或 AI）在旧代码上白干。
#
# 用法：
#   ./scripts/dev/boot-check.sh              # 只读自检（不联网、不动任何东西）
#   ./scripts/dev/boot-check.sh --fetch       # 先 fetch 父仓库 + 各子模块，再做（含远端指针校验）
#
# 只读保证：**不** pull、**不** checkout、**不** submodule update。要同步时脚本只打印建议命令，
# 由人（或 AI）确认后再执行 —— 因为子模块常有"故意不在记录指针上"的情况（如 plugin 常驻 develop）。
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"

FETCH=0
[[ "${1:-}" == "--fetch" ]] && FETCH=1

c() { printf '\033[%sm%s\033[0m' "$1" "$2"; }
ok()   { printf '%s %s\n' "$(c '32' '✓')" "$1"; }
warn() { printf '%s %s\n' "$(c '33' '!')" "$1"; }
bad()  { printf '%s %s\n' "$(c '31' '✗')" "$1"; }
step() { printf '\n\033[1m▶ %s\033[0m\n' "$1"; }

NEED_SYNC=0     # 需要同步才能开工（硬性问题）
WARNINGS=0      # 需要人确认、但不阻塞

if [[ "$FETCH" == "1" ]]; then
  step "fetch（父仓库 + 子模块）"
  git fetch --all --prune --quiet && ok "父仓库已 fetch" || warn "父仓库 fetch 失败（离线？）"
  git submodule foreach --quiet 'git fetch --all --prune --quiet || true' >/dev/null 2>&1 \
    && ok "子模块已 fetch" || warn "部分子模块 fetch 失败"
fi

# ── 1. 父仓库 ────────────────────────────────────────────────
step "父仓库"
BRANCH="$(git rev-parse --abbrev-ref HEAD)"
printf '  分支：%s\n' "$BRANCH"
UPSTREAM="$(git rev-parse --abbrev-ref --symbolic-full-name '@{u}' 2>/dev/null || true)"
if [[ -n "$UPSTREAM" ]]; then
  read -r AHEAD BEHIND < <(git rev-list --left-right --count 'HEAD...@{u}' 2>/dev/null || echo "0 0")
  if [[ "$BEHIND" != "0" ]]; then
    bad "落后远端 $BEHIND 个提交（$UPSTREAM） → 先 \`git pull --ff-only\`"
    NEED_SYNC=1
  fi
  if [[ "$AHEAD" != "0" ]]; then
    warn "本地领先远端 $AHEAD 个提交 → 记得 push，否则换设备会丢"
  fi
  [[ "$BEHIND" == "0" && "$AHEAD" == "0" ]] && ok "与 $UPSTREAM 同步"
else
  warn "当前分支没有 upstream（$BRANCH）→ 确认这是不是有意为之"
fi

DIRTY="$(git status --porcelain --untracked-files=normal | wc -l | tr -d ' ')"
if [[ "$DIRTY" != "0" ]]; then
  warn "工作区有 $DIRTY 处未提交改动："
  git status --porcelain --untracked-files=normal | head -8 | sed 's/^/      /'
  [[ "$DIRTY" -gt 8 ]] && printf '      …（共 %s 处）\n' "$DIRTY"
else
  ok "工作区干净"
fi

# ── 2. 子模块 ────────────────────────────────────────────────
step "子模块（记录指针 vs 检出）"
UNINIT=0; OFFPOINTER=(); MISSING=(); SUBDIRTY=()
while IFS= read -r line; do
  [[ -z "$line" ]] && continue
  flag="${line:0:1}"
  rest="${line:1}"
  sha="$(printf '%s' "$rest" | awk '{print $1}')"
  path="$(printf '%s' "$rest" | awk '{print $2}')"

  if [[ "$flag" == "-" ]]; then
    UNINIT=$((UNINIT + 1)); MISSING+=("$path:$sha")
    continue
  fi
  # 指针提交在本仓库对象库里存在吗？（换设备后常见：没 fetch 到）
  if ! git -C "$path" cat-file -e "${sha}^{commit}" 2>/dev/null; then
    MISSING+=("$path:$sha")
  fi
  if [[ "$flag" == "+" ]]; then
    sub_branch="$(git -C "$path" rev-parse --abbrev-ref HEAD 2>/dev/null)"
    sub_sha="$(git -C "$path" rev-parse --short HEAD 2>/dev/null)"
    OFFPOINTER+=("$path|${sha:0:8}|$sub_branch|$sub_sha")
  fi
  sub_dirty="$(git -C "$path" status --porcelain --untracked-files=no 2>/dev/null | wc -l | tr -d ' ')"
  [[ "$sub_dirty" != "0" ]] && SUBDIRTY+=("$path|$sub_dirty")
done < <(git submodule status --recursive)

if [[ "$UNINIT" != "0" ]]; then
  bad "$UNINIT 个子模块未初始化 → \`git submodule update --init --recursive\`"
  NEED_SYNC=1
else
  ok "所有子模块已初始化"
fi

if [[ ${#MISSING[@]} -gt 0 ]]; then
  bad "以下子模块的「记录指针」在本地不存在（需要 fetch）："
  printf '      %s\n' "${MISSING[@]}"
  NEED_SYNC=1
fi

if [[ ${#OFFPOINTER[@]} -gt 0 ]]; then
  warn "检出的提交 ≠ 父仓库记录（多数是**故意的**，如 plugin 常驻 develop；确认后再决定要不要对齐）："
  for entry in "${OFFPOINTER[@]}"; do
    IFS='|' read -r p rec br cur <<<"$entry"
    printf '      %-28s 记录 %s · 当前 %s@%s\n' "$p" "$rec" "$br" "$cur"
  done
  WARNINGS=$((WARNINGS + 1))
fi

if [[ ${#SUBDIRTY[@]} -gt 0 ]]; then
  warn "以下子模块有未提交改动（可能是别人的接力工作，别清理）："
  for entry in "${SUBDIRTY[@]}"; do
    IFS='|' read -r p n <<<"$entry"
    printf '      %-28s %s 处改动\n' "$p" "$n"
  done
fi

# ── 3. 组合校验 ──────────────────────────────────────────────
step "组合校验（scripts/verify/check.py）"
if python3 scripts/verify/check.py >/tmp/orzmc-boot-check.log 2>&1; then
  tail -3 /tmp/orzmc-boot-check.log | sed 's/^/  /'
  ok "登记表/一致性/命令面均通过"
else
  bad "组合校验失败："
  tail -15 /tmp/orzmc-boot-check.log | sed 's/^/      /'
  NEED_SYNC=1
fi

if [[ "$FETCH" == "1" ]]; then
  step "远端指针校验（--remote，需网络）"
  if python3 scripts/verify/check.py --remote >/tmp/orzmc-boot-remote.log 2>&1; then
    ok "所有子模块指针均存在于远端"
  else
    bad "有子模块指针不在远端（先在该子模块 push，或重新 bump 指针）："
    tail -10 /tmp/orzmc-boot-remote.log | sed 's/^/      /'
    NEED_SYNC=1
  fi
fi

# ── 4. 结论 ──────────────────────────────────────────────────
step "结论"
if [[ "$NEED_SYNC" == "1" ]]; then
  bad "现在**不能**直接开工，先按上面的提示同步。常用命令："
  cat <<'MSG'

        git pull --ff-only                        # 父仓库落后远端（不要用 merge/reset）
        git submodule update --init --recursive   # 子模块未初始化（若子模块有本地改动，先确认再动）
        git -C <子模块> fetch origin              # 只有个别子模块指针缺失时

    换设备第一次拉：git clone --recurse-submodules https://github.com/OrzMC/OrzMC.git
MSG
  exit 1
fi

if [[ "$WARNINGS" != "0" ]]; then
  warn "可以开工（上面标 ! 的需要你自己判断，不要无脑 submodule update）"
else
  ok "可以开工：仓库是当前状态"
fi
echo
printf '  下一步做什么 → HANDOFF.md §1；红线与环境 → §0.1；上次到哪 → §5 最新一条\n'
