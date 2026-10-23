#!/usr/bin/env bash
# 推前快速验证（pre-push 钩子的实体）——把「推一次等 3 分钟 CI」换成「本地 25 秒」。
#
# 为什么：2026-10-19 取证显示 OrzMCKit 单日 CI 58 次 / 257 分钟，其中大量是
# 「改一行 → 推 → 等 3.3 分钟 → 再改一行」（一个分支推了 14 次）。见
# `docs/iteration-efficiency.md` §3.5–3.7。
#
# 行为：
#   * 只改文档（`*.md` / `docs/`）→ 直接放行（CI 也已跳过，见 `push.paths-ignore`）；
#   * `OrzMCKit` → 跨平台静态检查（1 秒）+ `scripts/swift-check.sh test`（本机构建/单测）；
#   * `OrzPythonMC` → `uv run pytest -q` + `scripts/verify` 类快检；
#   * 其它仓库 / 无变更 → 放行。
#
# 逃生阀（都要求显式、且会打印提示）：
#   SKIP_PREPUSH=1        跳过（急用；CI 仍会跑）
#   ORZMC_PREPUSH_STRICT=0  本机 Swift 检查失败时**不阻断**（默认阻断）
#
# 安装：scripts/dev/install-hooks.sh（写入各子模块的 pre-push）
set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
REPO_ROOT="$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")"
NAME="$(basename "$REPO_ROOT")"

if [[ "${SKIP_PREPUSH:-0}" == "1" ]]; then
    echo "⚠️  SKIP_PREPUSH=1：跳过推前验证（CI 仍会跑）" >&2
    exit 0
fi

# 变更文件（对比上游；没有上游时对比 origin/main）
changed="$(git -C "$REPO_ROOT" diff --name-only '@{upstream}..HEAD' 2>/dev/null \
    || git -C "$REPO_ROOT" diff --name-only origin/main..HEAD 2>/dev/null || true)"

if [[ -z "$changed" ]]; then
    exit 0
fi

# 纯文档改动：CI 也不会跑，直接放行。
non_doc="$(printf '%s\n' "$changed" | grep -vE '(^|/)(docs?/|.*\.md$|LICENSE$)' || true)"
if [[ -z "$non_doc" ]]; then
    echo "✔ 仅文档改动，跳过推前验证"
    exit 0
fi

echo "→ 推前验证（${NAME}，变更 $(printf '%s\n' "$non_doc" | wc -l | tr -d ' ') 个非文档文件）"
printf '%s\n' "$non_doc" | sed 's/^/    /' | head -10

run_or_warn() {
    local label="$1"
    shift
    echo "→ ${label}"
    if "$@"; then
        echo "✔ ${label} 通过"
        return 0
    fi
    echo "✘ ${label} 失败——请修好再推（或 SKIP_PREPUSH=1 强推，CI 会复核）" >&2
    return 1
}

# 用**仓库路径**判定（checkout 目录名可能是 `python` 而非 `OrzPythonMC`，靠名字会漏）。
case "$REPO_ROOT" in
    "$ROOT/swift/lib/OrzMCKit")
        # 1) 秒级：跨平台可移植性（抓 CryptoKit / FoundationNetworking / 写死路径）
        if ! run_or_warn "可移植性静态检查" python3 "$REPO_ROOT/scripts/verify/portability.py"; then
            exit 1
        fi
        # 2) 本机构建 + 单测（不再 rsync 到远端：`scripts/air/run.sh` 已删除）。
        if ! out="$("$ROOT/scripts/swift-check.sh" test 2>&1)"; then
            printf '%s\n' "$out" | tail -5 >&2
            if [[ "${ORZMC_PREPUSH_STRICT:-1}" == "0" ]]; then
                echo "⚠️  本机 Swift 检查失败，按 ORZMC_PREPUSH_STRICT=0 放行（CI 会复核）" >&2
                exit 0
            fi
            echo "✘ 本机构建/单测未通过" >&2
            exit 1
        fi
        printf '%s\n' "$out" | grep -E "Test run with|Build complete" | tail -2
        echo "✔ 本机构建 + 单测通过"
        ;;
    "$ROOT/python")
        # 本机（老 i5 + 慢盘）跑 pytest 要 1 分 40 秒、单次 CLI 进程启动约 13 秒——
        # 比 CI 还慢，所以本地只跑秒级的 ruff；完整单测交给 CI（GH runner 上 20–50 秒）。
        # 想本地跑全量：ORZMC_PREPUSH_TESTS=1。
        if ! run_or_warn "ruff" bash -lc "cd '$REPO_ROOT' && uv run ruff check ."; then
            exit 1
        fi
        if [[ "${ORZMC_PREPUSH_TESTS:-0}" == "1" ]]; then
            if ! run_or_warn "pytest" bash -lc "cd '$REPO_ROOT' && uv run pytest -q -x"; then
                exit 1
            fi
        else
            echo "ℹ️  跳过 pytest（本机较慢；ORZMC_PREPUSH_TESTS=1 可开启，CI 会跑全量）"
        fi
        ;;
    *)
        echo "✔ ${NAME} 无推前验证规则，放行"
        ;;
esac
