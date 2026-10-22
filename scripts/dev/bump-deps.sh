#!/usr/bin/env bash
# 依赖漂移检查 / 刷新：把 app 的 `Package.resolved` 与依赖仓库的真实 HEAD 对账。
#
# 背景（docs/iteration-efficiency.md R4/R7）：app 对 OrzMCKit / OrzSwiftKit / MojangAPI /
# PaperMC 用的是 **分支依赖**（`branch = main`, Q7 已决 HEAD 制）。分支依赖本身没错，
# 但 `Package.resolved` 是另一份"事实"：依赖侧合并了修复，而 app 的锁文件没刷新，
# 本机/CI 就还在编旧提交——表现是"依赖明明修了，这里却是假阴性"，白跑一轮。
#
# 用法：
#   scripts/dev/bump-deps.sh --check   # 只报告漂移，不写文件（可在 pre-push / CI 用）
#   scripts/dev/bump-deps.sh           # 重新解析并写回 Package.resolved，然后打印 diff
#
# 说明：
# - 版本号依赖（ExarotonAPI / OrzAppUpdater / …）不在此列，它们由 SwiftPM 语义化版本管。
# - 刷新走 `xcodebuild -resolvePackageDependencies`（真正的依赖声明在 Xcode 工程里，
#   app 自己的 `Package.swift` 只描述本仓库的库与测试）。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
APP="$ROOT/swift/app"
DERIVED_DATA="${ORZMC_DERIVED_DATA:-$HOME/Library/Developer/Xcode/DerivedData/OrzMC-local}"
RESOLVED_FILE="$APP/OrzMC.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved"

# identity → 本地子模块路径（分支依赖的仓库都在伞内，可直接比对 HEAD）
declare -a BRANCH_DEPS=(
  "orzmckit:swift/lib/OrzMCKit"
  "orzswiftkit:swift/lib/OrzSwiftKit"
  "mojangapi:swift/lib/MojangAPI"
  "papermc:swift/lib/PaperMC"
)

need() { command -v "$1" >/dev/null 2>&1 || { echo "缺少命令：$1" >&2; exit 1; }; }

mode="update"
case "${1:-}" in
  --check) mode="check" ;;
  -h|--help) sed -n '2,17s/^# \{0,1\}//p' "${BASH_SOURCE[0]}"; exit 0 ;;
  "") ;;
  *) echo "未知参数：$1（用 --check 或留空）" >&2; exit 2 ;;
esac

need python3
[[ -f "$RESOLVED_FILE" ]] || { echo "找不到 $RESOLVED_FILE" >&2; exit 1; }

# 打印「identity  锁文件rev  远端/本地HEAD  状态」
report() {
  python3 - "$RESOLVED_FILE" "${BRANCH_DEPS[@]}" <<'PY'
import json, subprocess, sys
resolved, deps = sys.argv[1], sys.argv[2:]
pins = {p["identity"]: p["state"] for p in json.load(open(resolved))["pins"]}
drift = 0
for entry in deps:
    identity, path = entry.split(":", 1)
    state = pins.get(identity)
    if state is None:
        print(f"{identity:12} -            (未在锁文件中)")
        continue
    locked = state.get("revision", "")[:10]
    branch, version = state.get("branch"), state.get("version")
    if branch:
        head = ""
        for ref in (f"origin/{branch}", "HEAD"):
            head = subprocess.run(["git", "-C", path, "rev-parse", "--short=10", ref],
                                  capture_output=True, text=True).stdout.strip()
            if head:
                break
        same = locked == head
        drift += 0 if same else 1
        print(f"{identity:12} {locked:12} {head:12} {'ok' if same else 'DRIFT'}  {path}  (branch {branch})")
    elif version:
        # 版本号依赖：锁文件写的是 tag 提交，落后 main 是**预期**，不算漂移。
        print(f"{identity:12} {locked:12} {'-':12} ok      {path}  (版本 {version})")
    else:
        print(f"{identity:12} {locked:12} {'?':12} ?       {path}  (未知需求类型)")
sys.exit(1 if drift else 0)
PY
}

echo "锁文件：$RESOLVED_FILE"
if report; then
  echo "=> 分支依赖与本地子模块 HEAD 一致。"
  exit 0
fi

if [[ "$mode" == "check" ]]; then
  echo "=> 有漂移（依赖侧有新提交，锁文件没跟上）。执行 scripts/dev/bump-deps.sh 刷新。" >&2
  exit 1
fi

# 说明：`xcodebuild -resolvePackageDependencies` **不会**移动分支依赖的钉
# （相当于 Xcode 的 "Update to Latest Package Versions"，CLI 没有等价开关）。
# 所以这里直接把分支依赖的 revision 改写成依赖仓库的 `origin/<branch>`，
# 再由 SwiftPM 在解析/构建时校验并拉取该提交——钉的内容就是分支头本身，确定性没问题。
echo "=> 改写分支依赖的钉…"
python3 - "$RESOLVED_FILE" "${BRANCH_DEPS[@]}" <<'PY'
import json, subprocess, sys
resolved, deps = sys.argv[1], sys.argv[2:]
data = json.load(open(resolved))
pins = {p["identity"]: p for p in data["pins"]}
for entry in deps:
    identity, path = entry.split(":", 1)
    pin = pins.get(identity)
    if pin is None or "branch" not in pin["state"]:
        continue
    branch = pin["state"]["branch"]
    rev = subprocess.run(["git", "-C", path, "rev-parse", f"origin/{branch}"],
                         capture_output=True, text=True).stdout.strip()
    if rev:
        pin["state"]["revision"] = rev
        print(f"  {identity}: {branch} -> {rev[:10]}")
json.dump(data, open(resolved, "w"), indent=2)
open(resolved, "a").write("\n")
PY

# 两套 DerivedData 各有一份 SwiftPM 缓存（macOS / iOS），都要让它重新认钉，
# 否则另一侧会拿着旧 checkout 报 "Couldn't check out revision"。
for dd in "$DERIVED_DATA" "${DERIVED_DATA}-ios"; do
  rm -f "$dd/SourcePackages/workspace-state.json"
done
echo "=> 解析依赖（校验钉并拉取提交）…"
for destination in "platform=macOS" "generic/platform=iOS Simulator"; do
  (cd "$APP" && xcodebuild -resolvePackageDependencies \
    -project OrzMC.xcodeproj \
    -scheme OrzMC \
    -destination "$destination" \
    -derivedDataPath "$([[ "$destination" == platform=macOS ]] && echo "$DERIVED_DATA" || echo "${DERIVED_DATA}-ios")" >/dev/null)
done

echo "=> 刷新后的差异："
git -C "$ROOT" --no-pager diff --stat -- "swift/app/OrzMC.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved"
git -C "$ROOT" --no-pager diff -U0 -- "swift/app/OrzMC.xcodeproj/project.xcworkspace/xcshareddata/swiftpm/Package.resolved" \
  | grep -E "^[-+] *\"revision\"|^[-+] *\"version\"" || true
echo "=> 记得：这次刷新要和父仓库的子模块指针 bump 放在同一次提交里（AGENTS.md §2 铁律 1）。"
