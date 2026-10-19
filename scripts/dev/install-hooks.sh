#!/usr/bin/env bash
# 安装推前验证钩子（pre-push）到父仓库与需要它的子模块。
#
# 为什么要有安装器：git 钩子**不入版本库**（每个 clone 各一份），
# 所以规则没法靠提交传播——只能靠"一条命令装好 + AGENTS 里的约定"。
#
# 用法：
#   scripts/dev/install-hooks.sh              # 装到 python / swift/lib/OrzMCKit
#   scripts/dev/install-hooks.sh --all        # 装到全部已检出的子模块
#   scripts/dev/install-hooks.sh --check      # 只报告哪些仓库已装
#   scripts/dev/install-hooks.sh --uninstall  # 卸载（带标记的钩子才会被删）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
MARKER="# orzmc-pre-push-hook v1"
TARGETS=(python swift/lib/OrzMCKit)

HOOK_BODY=$(cat <<EOF
#!/bin/sh
$MARKER
exec "$ROOT/scripts/dev/prepush.sh" "\$@"
EOF
)

mode="${1:-install}"
if [[ "$mode" == "--all" ]]; then
    mapfile -t TARGETS < <(git -C "$ROOT" submodule status | awk '$1 !~ /^-/ {print $2}')
    mode="install"
fi

installed=0
missing=0
for rel in "${TARGETS[@]}"; do
    dir="$ROOT/$rel"
    [[ -d "$dir" ]] || { echo "跳过（未检出）: $rel"; continue; }
    git_dir="$(git -C "$dir" rev-parse --git-dir)"
    [[ "$git_dir" != /* ]] && git_dir="$dir/$git_dir"
    hook="$git_dir/hooks/pre-push"

    case "$mode" in
        --check)
            if [[ -f "$hook" ]] && grep -qF "$MARKER" "$hook"; then
                echo "✔ 已安装: $rel"
                installed=$((installed + 1))
            else
                echo "✘ 未安装: $rel（跑 scripts/dev/install-hooks.sh）"
                missing=$((missing + 1))
            fi
            ;;
        --uninstall)
            if [[ -f "$hook" ]] && grep -qF "$MARKER" "$hook"; then
                rm -f "$hook"
                echo "已卸载: $rel"
            else
                echo "跳过（非本工具安装）: $rel"
            fi
            ;;
        *)
            mkdir -p "$(dirname "$hook")"
            if [[ -f "$hook" ]] && ! grep -qF "$MARKER" "$hook"; then
                cp "$hook" "$hook.bak.$(date +%s)"
                echo "⚠️  已备份原有钩子: $rel"
            fi
            printf '%s\n' "$HOOK_BODY" > "$hook"
            chmod +x "$hook"
            echo "✔ 已安装: $rel"
            installed=$((installed + 1))
            ;;
    esac
done

if [[ "$mode" == "--check" && "$missing" -gt 0 ]]; then
    exit 1
fi
[[ "$mode" == "--uninstall" ]] || echo "完成（$installed 个仓库）"
