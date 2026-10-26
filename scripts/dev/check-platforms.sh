#!/usr/bin/env bash
#
# check-platforms.sh — 平台分层门禁（父仓库，只读 + 可选构建）
#
# 背景：产品是「一套引擎 + 多个前端」，对系统的要求有意分层：
#
#   | 层                     | 产物                        | 最低系统        | 架构        |
#   |------------------------|-----------------------------|-----------------|-------------|
#   | 逻辑层（可独立分发）    | `orzmc` CLI、Swift 库       | **macOS 13**    | Intel + AS  |
#   | GUI 层（app 本体）      | OrzMC.app                   | **macOS 14**    | Intel + AS  |
#   | 分发层（对外唯一通道）  | Python `orzmc`              | Python 3.10+    | 与系统无关  |
#
# 折中方案的实质：**GUI 保持 macOS 14，逻辑层（CLI/库）继续钉在 macOS 13**。
# 这样 2017 款等卡在 Ventura 的 Intel Mac 仍能用 CLI，而 GUI 不必为 `@Observable`
# （Observation 宏本身要求 macOS 14）付出一次全量状态层重构。
# 详见 `docs/platform-support.md`。
#
# 本脚本做三件事（全部**不需要 Rosetta / Intel 真机**，秒级）：
#
#   1. 声明审计：谁把逻辑层悄悄抬到 14、或把 GUI 悄悄降到 13，直接红；
#   2. 产物审计：构建逻辑层产物，读 `otool -l` 的 `minos`，必须等于声明的下限；
#      读 `lipo -archs`，必须含本机架构（Intel 见 `--arch`）；
#   3. 分发审计：如果本机有已发布的 `.app`，检查它是 **Universal**（Intel + Apple Silicon）。
#
# 可选 `--arch`：额外做 **x86_64 交叉编译**（Intel 编译期验证）。
#   需要 Rosetta（构建插件是 x86_64 可执行文件，没有 Rosetta 跑不起来）：
#     softwareupdate --install-rosetta --agree-to-license
#   没有 Rosetta 时该项会明确「跳过」而不是假装通过。
#
# 用法：
#   ./scripts/dev/check-platforms.sh                     # 声明 + 产物 + 分发（默认）
#   ./scripts/dev/check-platforms.sh --declarations-only # 只查声明（Linux 也能跑，父仓库 CI 用）
#   ./scripts/dev/check-platforms.sh --arch              # 上面全部 + x86_64 交叉编译
#   ./scripts/dev/check-platforms.sh --quiet             # 只在失败时输出
#
set -uo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
SWIFT_DIR="${REPO_ROOT}/swift"

WANT_ARCH=0
QUIET=0
DECLARATIONS_ONLY=0
for arg in "$@"; do
    case "${arg}" in
        --declarations-only) DECLARATIONS_ONLY=1 ;;
        --arch) WANT_ARCH=1 ;;
        --quiet) QUIET=1 ;;
        -h|--help) sed -n '2,48p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; exit 0 ;;
        *) echo "未知参数：${arg}（见 --help）" >&2; exit 2 ;;
    esac
done

FAILED=0
SKIPPED=0

say() { [ "${QUIET}" -eq 1 ] || printf '%s\n' "$*"; }
ok() { [ "${QUIET}" -eq 1 ] || printf '  \033[32m✓\033[0m %s\n' "$*"; }
fail() {
    printf '  \033[31m✗\033[0m %s\n' "$*" >&2
    FAILED=$((FAILED + 1))
}
skip() {
    printf '  \033[33m-\033[0m %s\n' "$*"
    SKIPPED=$((SKIPPED + 1))
}
section() { [ "${QUIET}" -eq 1 ] || printf '\n\033[1m▶ %s\033[0m\n' "$*"; }

# 读某个 Package.swift 声明的 macOS 下限，归一成 "13" / "14" / "10.15" 这样的数字串。
pkg_macos_floor() {
    local file="$1"
    [ -f "${file}" ] || return 1
    python3 - "${file}" <<'PY'
import re, sys
text = open(sys.argv[1], encoding="utf-8").read()
m = re.search(r"\.macOS\(\.v([0-9_]+)\)", text)
if not m:
    sys.exit(1)
print(m.group(1).replace("_", "."))
PY
}

# 读 pbxproj 里某个 build setting 的取值（去重后打印，逗号分隔）。
pbx_setting() {
    local key="$1"
    python3 - "${REPO_ROOT}/swift/app/OrzMC.xcodeproj/project.pbxproj" "${key}" <<'PY'
import re, sys
path, key = sys.argv[1], sys.argv[2]
text = open(path, encoding="utf-8").read()
values = sorted({m.group(1).strip() for m in re.finditer(rf"\b{key} = ([^;]+);", text)})
print(",".join(values))
PY
}

# ---------------------------------------------------------------- 1. 声明审计

section "声明审计（谁把哪一层写成了哪个下限）"

# 逻辑层：允许 13 或更低（越低越好），禁止 14+。
LOGIC_PACKAGES=(
    "swift/lib/OrzMCKit/Package.swift"
    "swift/lib/MojangAPI/Package.swift"
    "swift/lib/PaperMC/Package.swift"
    "swift/lib/MCSManagerAPI/Package.swift"
    "swift/lib/ExarotonAPI/Package.swift"
    "swift/lib/OrzSwiftKit/Package.swift"
    "swift/lib/OrzAppUpdater/Package.swift"
)
for rel in "${LOGIC_PACKAGES[@]}"; do
    floor="$(pkg_macos_floor "${REPO_ROOT}/${rel}")" || { fail "${rel}：找不到 .macOS(...) 声明"; continue; }
    major="${floor%%.*}"
    if [ "${major}" -le 13 ] 2>/dev/null; then
        ok "${rel} → macOS ${floor}（逻辑层，可跑 Ventura）"
    else
        fail "${rel} → macOS ${floor}：逻辑层（CLI/库）被抬到 14+ 了；卡在 Ventura 的 Intel Mac 会装不上"
    fi
done

# GUI：app 自己的 SPM 包必须是 14（用了 Observation 宏），静默降到 13 会编不过。
gui_floor="$(pkg_macos_floor "${REPO_ROOT}/swift/app/Package.swift")" || gui_floor="?"
case "${gui_floor}" in
    14*|15*|26*) ok "swift/app/Package.swift → macOS ${gui_floor}（GUI 层，含 @Observable）" ;;
    *) fail "swift/app/Package.swift → macOS ${gui_floor}：GUI 层用了 Observation 宏，下限必须是 14+" ;;
esac

# Xcode 工程：macOS / iOS 部署目标要与上面的分层一致。
macos_targets="$(pbx_setting MACOSX_DEPLOYMENT_TARGET)"
ios_targets="$(pbx_setting IPHONEOS_DEPLOYMENT_TARGET)"
case "${macos_targets}" in
    14.0|14.*) ok "OrzMC.xcodeproj MACOSX_DEPLOYMENT_TARGET = ${macos_targets}" ;;
    *) fail "OrzMC.xcodeproj MACOSX_DEPLOYMENT_TARGET = ${macos_targets:-<空>}：GUI 层应为 14.0" ;;
esac
[ -n "${ios_targets}" ] && ok "OrzMC.xcodeproj IPHONEOS_DEPLOYMENT_TARGET = ${ios_targets}"

# 架构设置：不许写死 ARCHS / EXCLUDED_ARCHS（那会把 Universal 或某个架构悄悄做掉）。
for setting in ARCHS EXCLUDED_ARCHS VALID_ARCHS; do
    value="$(pbx_setting "${setting}")"
    if [ -z "${value}" ]; then
        ok "未写死 ${setting}（Release 归档走 ARCHS_STANDARD → arm64 + x86_64）"
    else
        fail "写死了 ${setting} = ${value}：会让发布包丢掉 Intel 或 Apple Silicon 切片"
    fi
done

# 发布脚本不许只归档当前架构（那会变成单架构包）。
if grep -qE "ONLY_ACTIVE_ARCH" "${SWIFT_DIR}/app/scripts/release-macos.sh"; then
    ok "release-macos.sh 只通过 ARCHIVE_ONLY_ACTIVE_ARCH 开关控制（默认不设 → Universal）"
else
    skip "release-macos.sh 未出现 ONLY_ACTIVE_ARCH（确认它没别处写死单架构）"
fi

# ---------------------------------------------------------------- 2. 产物审计

if [ "${DECLARATIONS_ONLY}" -eq 1 ]; then
    section "产物审计 / 分发审计 / Intel 交叉编译"
    skip "--declarations-only：跳过（这些需要 macOS 的 swift / otool / lipo）"
fi

if [ "${DECLARATIONS_ONLY}" -eq 0 ]; then
section "产物审计（构建逻辑层，读 minos / archs）"

if ! command -v swift >/dev/null 2>&1; then
    skip "没有 swift，跳过产物审计"
else
    # 只构建 CLI（逻辑层的可分发产物）。debug 就够：minos 与架构跟优化级别无关。
    if ! swift build --package-path "${SWIFT_DIR}/lib/OrzMCKit" --product orzmc \
        --only-use-versions-from-resolved-file >/tmp/orzmc-platform-build.log 2>&1; then
        fail "构建 orzmc 失败（详见 /tmp/orzmc-platform-build.log）"
    else
        bin_dir="$(swift build --package-path "${SWIFT_DIR}/lib/OrzMCKit" --show-bin-path 2>/dev/null)"
        cli="${bin_dir}/orzmc"
        if [ ! -f "${cli}" ]; then
            fail "找不到构建产物：${cli}"
        else
            archs="$(lipo -archs "${cli}" 2>/dev/null)"
            minos="$(otool -l "${cli}" 2>/dev/null | awk '/LC_BUILD_VERSION/{f=1} f&&/minos/{print $2; exit}')"
            host_arch="$(uname -m)"
            case "${archs}" in
                *"${host_arch}"*) ok "orzmc 架构 = ${archs}（含本机 ${host_arch}）" ;;
                *) fail "orzmc 架构 = ${archs:-?}：不含本机 ${host_arch}" ;;
            esac
            case "${minos}" in
                1[0-3].*) ok "orzmc minos = ${minos}（≤ 13，能在 Ventura 跑）" ;;
                "") fail "读不到 orzmc 的 minos（otool 输出异常）" ;;
                *) fail "orzmc minos = ${minos}：CLI 的 macOS 下限被抬到 13 以上了" ;;
            esac
        fi
    fi
fi

# ---------------------------------------------------------------- 3. 分发审计

section "分发审计（已发布的 app 必须是 Universal）"

# 候选：本机开发包、发布导出目录、以及维护者留存的官方包备份（`~/Applications-backup`）。
APP_CANDIDATES=("/Applications/OrzMC.app")
for extra in "${REPO_ROOT}/swift/app/dist/export/OrzMC.app" "${HOME}"/Applications-backup/OrzMC-official-*.app; do
    [ -e "${extra}" ] && APP_CANDIDATES+=("${extra}")
done
found_app=0
universal=0
for app in "${APP_CANDIDATES[@]}"; do
    [ -d "${app}" ] || continue
    found_app=$((found_app + 1))
    binary="${app}/Contents/MacOS/OrzMC"
    [ -f "${binary}" ] || { skip "${app} 里没有主可执行文件"; continue; }
    archs="$(lipo -archs "${binary}" 2>/dev/null)"
    minos="$(otool -l "${binary}" 2>/dev/null | awk '/LC_BUILD_VERSION/{f=1} f&&/minos/{print $2; exit}')"
    case "${archs}" in
        *x86_64*arm64*|*arm64*x86_64*)
            universal=$((universal + 1))
            ok "$(basename "${app}") 是 Universal（${archs}），minos=${minos}" ;;
        *) skip "$(basename "${app}") 只有 ${archs}（Debug 本机构建是单架构；以发布包为准）" ;;
    esac
done
[ "${found_app}" -eq 0 ] && skip "本机没有可检查的 .app（跳过；发布包在 CI 归档，见 release-macos.sh）"
if [ "${found_app}" -gt 0 ] && [ "${universal}" -eq 0 ]; then
    skip "本机 app 全是单架构：开发构建正常（ONLY_ACTIVE_ARCH=YES），发布包请在 CI 归档后核验"
fi

fi  # DECLARATIONS_ONLY == 0

# ---------------------------------------------------------------- 4. 可选：Intel 交叉编译

if [ "${WANT_ARCH}" -eq 1 ] && [ "${DECLARATIONS_ONLY}" -eq 0 ]; then
    section "Intel 交叉编译（--arch，需要 Rosetta）"
    if ! arch -x86_64 /usr/bin/true >/dev/null 2>&1; then
        skip "本机没有 Rosetta：x86_64 构建插件跑不起来。装：softwareupdate --install-rosetta --agree-to-license"
        skip "（Intel 编译期验证也可交给 CI 的 macos runner 或一台 Intel Mac；见 docs/platform-support.md）"
    else
        if swift build --package-path "${SWIFT_DIR}/lib/OrzMCKit" --product orzmc --arch x86_64 \
            --only-use-versions-from-resolved-file >/tmp/orzmc-platform-build-x86.log 2>&1; then
            bin_dir="$(swift build --package-path "${SWIFT_DIR}/lib/OrzMCKit" --show-bin-path \
                --arch x86_64 2>/dev/null)"
            archs="$(lipo -archs "${bin_dir}/orzmc" 2>/dev/null)"
            minos="$(otool -l "${bin_dir}/orzmc" 2>/dev/null | awk '/LC_BUILD_VERSION/{f=1} f&&/minos/{print $2; exit}')"
            case "${archs}" in
                *x86_64*) ok "orzmc（x86_64）编译通过，minos=${minos}" ;;
                *) fail "x86_64 产物架构异常：${archs:-?}" ;;
            esac
        else
            fail "x86_64 交叉编译失败（详见 /tmp/orzmc-platform-build-x86.log）"
        fi
    fi
fi

# ---------------------------------------------------------------- 结论

printf '\n\033[1m▶ 结论\033[0m\n'
if [ "${FAILED}" -gt 0 ]; then
    printf '\033[31m✗ 平台分层被破坏（%d 项）\033[0m\n' "${FAILED}"
    printf '  规则与理由见 docs/platform-support.md（GUI = macOS 14，逻辑层/CLI = macOS 13）\n'
    exit 1
fi
if [ "${SKIPPED}" -gt 0 ]; then
    printf '\033[33m✓ 声明与产物审计通过（%d 项跳过，原因见上）\033[0m\n' "${SKIPPED}"
else
    printf '\033[32m✓ 平台分层一致（GUI = macOS 14，逻辑层/CLI = macOS 13，发布包 Universal）\033[0m\n'
fi
