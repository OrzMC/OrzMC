#!/usr/bin/env bash
# 本机 Swift 构建、测试与验收入口（不使用 SSH，也不复制工作树）。
#
# 用法：
#   scripts/swift-check.sh env
#   scripts/swift-check.sh build|test [SwiftPM 参数…]
#   scripts/swift-check.sh accept|all
#   scripts/swift-check.sh app|app-ios|app-test|app-run
#   scripts/swift-check.sh clean|app-clean
#
# ORZMC_DERIVED_DATA 可覆盖 Xcode 缓存目录；默认使用用户级专用 DerivedData。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KIT="$ROOT/swift/lib/OrzMCKit"
APP="$ROOT/swift/app"
DERIVED_DATA="${ORZMC_DERIVED_DATA:-$HOME/Library/Developer/Xcode/DerivedData/OrzMC-local}"
RESOLVED=(--only-use-versions-from-resolved-file)

usage() {
  sed -n '2,12s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"
}

need() {
  command -v "$1" >/dev/null 2>&1 || { echo "缺少命令：$1" >&2; exit 1; }
}

cli_build() { (cd "$KIT" && swift build --product orzmc "${RESOLVED[@]}" "$@"); }
cli_test() { (cd "$KIT" && swift test "${RESOLVED[@]}" "$@"); }
cli_accept() {
  (cd "$KIT" && swift build -c release --product orzmc "${RESOLVED[@]}" "$@")
  python3 "$ROOT/scripts/accept/cli.py" --cli "$KIT/.build/release/orzmc"
}

app_test_target() {
  (cd "$APP" && xcodebuild test \
    -project OrzMC.xcodeproj \
    -scheme OrzMC \
    -destination "platform=macOS" \
    -derivedDataPath "$DERIVED_DATA" \
    -only-testing:OrzMCTests \
    -onlyUsePackageVersionsFromResolvedFile \
    -skipPackageUpdates \
    -skipPackagePluginValidation \
    -skipMacroValidation \
    CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY='' \
    "$@" 2>&1 | tail -25)
}

app_build() {
  local destination="$1"
  shift
  local derived_data="$DERIVED_DATA"
  [[ "$destination" == *"iOS"* ]] && derived_data="${DERIVED_DATA}-ios"
  (cd "$APP" && xcodebuild build \
    -project OrzMC.xcodeproj \
    -scheme OrzMC \
    -destination "$destination" \
    -derivedDataPath "$derived_data" \
    -onlyUsePackageVersionsFromResolvedFile \
    -skipPackageUpdates \
    -skipPackagePluginValidation \
    -skipMacroValidation \
    CODE_SIGNING_ALLOWED=NO CODE_SIGNING_REQUIRED=NO CODE_SIGN_IDENTITY='' \
    "$@" 2>&1 | tail -40)
}

TASK="${1:-all}"
shift || true
case "$TASK" in
  env)
    need swift; need xcodebuild
    printf 'host: '; scutil --get ComputerName 2>/dev/null || hostname
    printf 'architecture: '; uname -m
    swift --version
    xcodebuild -version
    xcrun --show-sdk-version
    df -h "$ROOT" | tail -1
    ;;
  build) need swift; cli_build "$@" ;;
  test) need swift; cli_test "$@" ;;
  accept) need swift; need python3; cli_accept ;;
  all)
    [[ $# -eq 0 ]] || { echo 'all 不接受额外参数' >&2; exit 2; }
    need swift; need python3
    cli_build; cli_test; cli_accept
    ;;
  app) need xcodebuild; app_build 'platform=macOS' "$@" ;;
  app-ios) need xcodebuild; app_build 'generic/platform=iOS Simulator' "$@" ;;
  app-test) need swift; need xcodebuild
    # 两套：SwiftPM 包单测（Sources/*）+ 应用层测试 target（OrzMCTests，`@testable import OrzMC`）。
    # 后者以前**从来没有人跑**，于是悄悄腐烂（引用了已删除的服务）；CI 现在也会跑它。
    (cd "$APP" && swift test "${RESOLVED[@]}" "$@")
    app_test_target "$@" ;;
  app-run)
    local_app="$(find "$DERIVED_DATA/Build/Products" -name OrzMC.app -print -quit 2>/dev/null || true)"
    [[ -n "$local_app" ]] || { echo '找不到本机构建产物；先运行 app' >&2; exit 1; }
    open "$local_app"
    ;;
  clean) rm -rf "$KIT/.build" ;;
  app-clean) rm -rf "$DERIVED_DATA" "${DERIVED_DATA}-ios" ;;
  -h|--help|help) usage ;;
  *) echo "未知子任务：$TASK" >&2; usage; exit 2 ;;
esac
