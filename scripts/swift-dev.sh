#!/usr/bin/env bash
# scripts/swift-dev.sh — Swift 本地联调助手（开发态；**不提交**任何本地覆盖）
#
# 伞内已检出 Swift 相关子模块：`swift/app`（GUI）+ `swift/lib/*`（引擎与依赖）。
# 本脚本用 SwiftPM 的“本地编辑覆盖（package edit）”把 `swift/lib/OrzMCKit` 的依赖
# （MojangAPI / PaperMC / OrzSwiftKit）指向本地 `swift/lib/*`，便于跨仓联调；
# `unedit` 一键还原（不会污染提交）。
#
# 用法：
#   scripts/swift-dev.sh sync      # 初始化/更新 swift/lib/* 子模块（--remote 拉最新）
#   scripts/swift-dev.sh pull      # == sync --remote
#   scripts/swift-dev.sh edit      # OrzMCKit 的依赖改用本地 swift/lib/*
#   scripts/swift-dev.sh status    # 列出当前本地编辑覆盖
#   scripts/swift-dev.sh unedit    # 还原（package unedit + 恢复 Package.resolved）
#   scripts/swift-dev.sh xcode     # 打印 app（Xcode）使用本地引擎的手动步骤
#
# 通用参数：--dry-run（只打印将执行的命令，不改动）；--remote（sync/pull 拉分支最新）。
#
# 说明：
# - `app` 是 Xcode 工程，Xcode 的“本地包覆盖”无法安全脚本化（需改 project.pbxproj），
#   因此这里只做 SwiftPM 侧 edit；GUI 联调见 `xcode` 子命令。
# - 远端引用（branch=main，HEAD 制）保留；所有本地覆盖仅存在于工作区，验证后还原。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LIB="$ROOT/swift/lib"
PKG="$LIB/OrzMCKit"

# 依赖 identity（= SwiftPM 依赖名）→ 本地目录名（同 identity）
DEPS=(MojangAPI PaperMC OrzSwiftKit)

DRY_RUN=false
REMOTE=false

usage() {
  awk 'NR>1 && /^#/ { sub(/^# ?/, ""); print; next } NR>1 { exit }' "${BASH_SOURCE[0]}"
}

log() { printf '%s\n' "$*"; }

# 执行或（--dry-run 时）只打印
run() {
  if $DRY_RUN; then
    log "[dry-run] $*"
  else
    "$@"
  fi
}

parse_flags() {
  for arg in "$@"; do
    case "$arg" in
      --dry-run) DRY_RUN=true ;;
      --remote|--pull) REMOTE=true ;;
      -h|--help|help) usage; exit 0 ;;
      *) echo "未知参数：$arg" >&2; usage; exit 1 ;;
    esac
  done
}

need_swift() {
  $DRY_RUN && return 0
  if ! command -v swift >/dev/null 2>&1; then
    echo "错误：PATH 中找不到 swift（可先 export PATH=\"\$HOME/Library/Developer/Toolchains/swift-6.0.3-RELEASE.xctoolchain/usr/bin:\$PATH\"）" >&2
    exit 1
  fi
}

cmd_sync() {
  if $REMOTE; then
    run git -C "$ROOT" submodule update --init --recursive --remote
  else
    run git -C "$ROOT" submodule update --init --recursive
  fi
  log "[ok] swift/lib/* 子模块已更新（remote=${REMOTE}, dry-run=${DRY_RUN}）"
}

cmd_edit() {
  need_swift
  [ -d "$PKG" ] || { echo "错误：$PKG 不存在（先跑 \`$0 sync\`）" >&2; exit 1; }
  for dep in "${DEPS[@]}"; do
    local path="$LIB/$dep"
    if [ ! -d "$path" ]; then
      echo "跳过 ${dep}：缺 ${path}" >&2
      continue
    fi
    if $DRY_RUN; then
      log "[dry-run] (cd $PKG && swift package edit --path $path $dep)"
    else
      ( cd "$PKG" && swift package edit --path "$path" "$dep" ) && log "[edit] $dep -> swift/lib/$dep"
    fi
  done
  $DRY_RUN || log "[ok] 本地覆盖已生效（仅工作区；勿提交 Package.resolved 变更）"
}

cmd_unedit() {
  need_swift
  [ -d "$PKG" ] || { echo "错误：$PKG 不存在" >&2; exit 1; }
  for dep in "${DEPS[@]}"; do
    if $DRY_RUN; then
      log "[dry-run] (cd $PKG && swift package unedit $dep)"
    else
      ( cd "$PKG" && swift package unedit "$dep" >/dev/null 2>&1 ) && log "[unedit] $dep" || true
    fi
  done
  if $DRY_RUN; then
    log "[dry-run] git -C $PKG checkout -- Package.resolved"
  else
    git -C "$PKG" checkout -- Package.resolved 2>/dev/null || true
    log "[ok] 已还原 OrzMCKit 的本地编辑"
  fi
}

cmd_status() {
  local resolved="$PKG/Package.resolved"
  if [ -f "$resolved" ] && grep -q '"path"' "$resolved"; then
    log "当前有本地编辑覆盖："
    grep -E '"(identity|path|location)"' "$resolved" | head -40
  else
    log "当前无本地编辑覆盖（或未解析）。"
  fi
  log "工作区未被提交的本地改动："
  git -C "$ROOT" status --porcelain -- swift/lib || true
}

cmd_xcode() {
  cat <<'EOS'
app（Xcode）使用本地引擎 swift/lib/OrzMCKit：
  1. 打开 swift/app/OrzMC.xcodeproj
  2. File → Add Package Dependencies… → Add Local… → 选择 swift/lib/OrzMCKit
     （对 swift/lib/{MojangAPI,PaperMC,OrzSwiftKit} 同理，需要时再指。）
  3. 在 target 的 Frameworks 里使用本地包的产品（如 Game）。
  ⚠️ 本地覆盖仅开发态使用：**不要提交** project.pbxproj / Package.resolved 的本地路径改动。
     还原：在 Xcode 中移除本地包并恢复远端引用，或 `git checkout -- swift/app/OrzMC.xcodeproj`。
EOS
}

sub="${1:-}"
[ $# -gt 0 ] && shift
parse_flags "$@"

case "$sub" in
  sync)   cmd_sync ;;
  pull)   REMOTE=true; cmd_sync ;;
  edit)   cmd_edit ;;
  unedit) cmd_unedit ;;
  status) cmd_status ;;
  xcode)  cmd_xcode ;;
  ""|-h|--help|help) usage ;;
  *) echo "未知子命令：$sub" >&2; usage; exit 1 ;;
esac
