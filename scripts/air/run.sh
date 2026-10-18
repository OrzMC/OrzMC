#!/usr/bin/env bash
# 远端构建（ssh host: air）——把构建/测试搬到更快的机器上，本机只做轻量检查。
#
# 为什么：本机（2015 i5 / macOS 13 / CLT 13.3 / 剩余磁盘 <10GB）无法全量构建
# （依赖 OpenAPIKit 需要 macOS 14+ SDK），且单次 no-op 构建就要 16s。见
# `docs/iteration-efficiency.md` §3.1。
#
# 用法:
#   scripts/air/run.sh env                 # 远端环境自检（swift / SDK / CPU / 磁盘）
#   scripts/air/run.sh sync                # 只同步工作树（不含 .build）
#   scripts/air/run.sh build [额外参数…]    # 同步 + swift build --product orzmc
#   scripts/air/run.sh test                # 同步 + swift test
#   scripts/air/run.sh accept              # 同步 + release 构建 + CLI 验收
#   scripts/air/run.sh all                 # 同步 + build + test + accept
#   scripts/air/run.sh sh '<命令>'          # 在远端同步目录里执行自定义命令
#   scripts/air/run.sh clean               # 删除远端 .build
#
# 环境变量:
#   ORZMC_BUILD_HOST   远端主机（缺省 air；可用 pi4 之类）
#   ORZMC_REMOTE_DIR   远端工作目录（缺省 ~/orzmc-build/OrzMCKit）
#   ORZMC_PKG_DIR      本地待同步目录（缺省 <repo>/swift/lib/OrzMCKit）
#   ORZMC_LOCAL_DEPS=1 依赖也用**本地工作树**（把 swift/lib/{MojangAPI,PaperMC,OrzSwiftKit} 同步过去，
#                      并在**远端副本**的 Package.swift 里改成 path 依赖）；改依赖仓库时用这个，
#                      不必先 push 到 main。远端改动每次同步都会被覆盖，不会污染仓库。
#
# 约定:
#   - 只同步**工作树**；依赖（MojangAPI / PaperMC / OrzSwiftKit）由远端按 `branch: main` 拉取，
#     所以改依赖仓库必须先各自 push 到 main（或改用 `scripts/swift-dev.sh` 的本地覆盖思路）。
#   - `.build` 不参与 rsync（--delete + exclude），远端增量构建得以保留。
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
HOST="${ORZMC_BUILD_HOST:-air}"
LOCAL_DIR="${ORZMC_PKG_DIR:-$ROOT/swift/lib/OrzMCKit}"
REMOTE_DIR="${ORZMC_REMOTE_DIR:-orzmc-build/OrzMCKit}"
# 依赖是 `branch: main`：SwiftPM 每次解析都会联网刷新。默认用 Package.resolved 离线解析，
# 需要拉依赖最新时用 `ORZMC_UPDATE_DEPS=1`。
if [[ "${ORZMC_UPDATE_DEPS:-0}" == "1" ]]; then RESOLVE_FLAG=""; else RESOLVE_FLAG="--only-use-versions-from-resolved-file"; fi
SSH=(ssh -o BatchMode=yes -o ConnectTimeout=10)

usage() { awk 'NR>1 && /^#/ { sub(/^# ?/, ""); print; next } NR>1 { exit }' "${BASH_SOURCE[0]}"; }

need_host() {
    if ! "${SSH[@]}" "$HOST" true 2>/dev/null; then
        cat >&2 <<EOF
连不上远端主机 '$HOST'。
排查:
  1) 机器是否开机/联网（macOS 休眠后不响应 SSH，需要唤醒或关闭休眠）；
  2) '\$HOME/.ssh/config' 里的 Host 别名与密钥是否正确；
  3) 手动试: ssh $HOST 'swift --version'
换主机: ORZMC_BUILD_HOST=pi4 scripts/air/run.sh env
EOF
        exit 1
    fi
}

sync_tree() {
    need_host
    "${SSH[@]}" "$HOST" "mkdir -p $(dirname "$REMOTE_DIR")"
    printf '同步 %s → %s:%s\n' "$LOCAL_DIR" "$HOST" "$REMOTE_DIR"
    rsync -az --delete \
        --exclude '.build/' \
        --exclude '.build-linux/' \
        --exclude '.git/' \
        -e "ssh -o BatchMode=yes" \
        "$LOCAL_DIR/" "$HOST:$REMOTE_DIR/"
    if [[ "${ORZMC_LOCAL_DEPS:-0}" == "1" ]]; then
        sync_local_deps
    fi
}

remote() { "${SSH[@]}" "$HOST" "cd \"$REMOTE_DIR\" && $*"; }

# 把依赖仓库也同步过去，并把远端 Package.swift 的 url 依赖改成 path 依赖（只改远端副本）。
sync_local_deps() {
    local dep
    for dep in MojangAPI PaperMC OrzSwiftKit; do
        local src="$ROOT/swift/lib/$dep"
        [[ -d "$src" ]] || { echo "⚠️  本地缺 $dep，跳过" >&2; continue; }
        "${SSH[@]}" "$HOST" "mkdir -p \"$REMOTE_DIR/deps\""
        rsync -az --delete --exclude '.build/' --exclude '.git/' -e "ssh -o BatchMode=yes" \
            "$src/" "$HOST:$REMOTE_DIR/deps/$dep/"
        printf '依赖(本地): %s\n' "$dep"
    done
    # 远端副本里把 `.package(url: ".../<dep>.git", branch: "main")` 换成 `.package(path: "deps/<dep>")`
    "${SSH[@]}" "$HOST" "cd \"$REMOTE_DIR\" && bash -s" <<'REMOTE_PATCH'
set -eu
for d in MojangAPI PaperMC OrzSwiftKit; do
  sed -i.bak -E "s|\.package\(url: \"https://github.com/[^\"]*/${d}\.git\", *branch: \"main\"\)|.package(path: \"deps/${d}\")|g" Package.swift
done
rm -f Package.swift.bak
printf '远端已改为本地依赖: %s 处\n' "$(grep -c 'path: "deps/' Package.swift)"
REMOTE_PATCH
}

env_report() {
    need_host
    "${SSH[@]}" "$HOST" 'bash -lc "
        echo \"host: \$(uname -a)\";
        echo \"cpus: \$(nproc 2>/dev/null || sysctl -n hw.ncpu)\";
        if command -v swift >/dev/null 2>&1; then
            echo \"swift: \$(swift --version 2>&1 | head -1)\";
            command -v xcrun >/dev/null 2>&1 && echo \"sdk: \$(xcrun --show-sdk-version 2>/dev/null)\";
        else
            echo \"swift: 未安装（远端需 Swift 6：https://github.com/swiftlang/swiftly）\";
        fi;
        df -h . | tail -1
    "'
}

TASK="${1:-all}"
shift || true

case "$TASK" in
    env) env_report ;;
    sync) sync_tree ;;
    build)
        sync_tree
        remote "swift build --product orzmc $RESOLVE_FLAG $*"
        ;;
    test)
        sync_tree
        remote "swift test $RESOLVE_FLAG $*"
        ;;
    accept)
        sync_tree
        remote "swift build -c release --product orzmc $RESOLVE_FLAG && python3 scripts/accept_cli.py --cli .build/release/orzmc"
        ;;
    all)
        sync_tree
        remote "swift build --product orzmc $RESOLVE_FLAG && swift test $RESOLVE_FLAG && swift build -c release --product orzmc $RESOLVE_FLAG && python3 scripts/accept_cli.py --cli .build/release/orzmc"
        ;;
    sh)
        [ $# -ge 1 ] || { echo "用法: $0 sh '<命令>'" >&2; exit 2; }
        remote "$*"
        ;;
    clean)
        need_host
        remote "rm -rf .build .build-linux"
        ;;
    -h|--help) usage ;;
    *)
        echo "未知子任务: $TASK（可用 env|sync|build|test|accept|all|sh|clean）" >&2
        exit 2
        ;;
esac
