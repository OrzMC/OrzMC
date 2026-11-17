#!/bin/bash
# PaperMC 插件管理器：install / update / remove / list
# 支持来源：Modrinth API（slug 或直链）、URL 直链、本地文件
# 用法:
#   plugin_manager.sh install <slug|URL|本地路径> [--beta]
#   plugin_manager.sh update
#   plugin_manager.sh remove <文件名.jar>
#   plugin_manager.sh list
set -euo pipefail

PAPER_DIR="${PAPER_DIR:-$HOME/minecraft-server}"
PLUGINS_DIR="$PAPER_DIR/plugins"
MC_VERSION="${MC_VERSION:-}"  # 例如 26.2，留空自动检测
USER_AGENT="papermc-maintainer/1.0 (hermes)"

mkdir -p "$PLUGINS_DIR"

# 自动检测 MC 版本（从 jar 名）
detect_version() {
  if [ -n "$MC_VERSION" ]; then echo "$MC_VERSION"; return; fi
  local jar
  jar=$(ls -t "$PAPER_DIR"/paper-*.jar 2>/dev/null | head -1 || true)
  if [ -n "$jar" ]; then
    basename "$jar" | grep -oE '\d+\.\d+(\.\d+)?' | head -1
  else
    echo ""
  fi
}

# Modrinth 搜索：slug → 最新兼容版本 jar URL
modrinth_resolve() {
  local slug="$1"
  local version
  version=$(detect_version)
  local api_url="https://api.modrinth.com/v2/project/$slug/version"
  if [ -n "$version" ]; then
    # 尝试精确版本，不行就回退到不带版本过滤（拿最新版）
    local resp
    resp=$(curl -sL --max-time 30 "$api_url?game_versions=%5B%22$version%22%5D")
    if [ "$resp" = "[]" ] || [ -z "$resp" ]; then
      echo "⚠️ MC $version 无直接匹配，取最新版本" >&2
      resp=$(curl -sL --max-time 30 "$api_url")
    fi
  else
    resp=$(curl -sL --max-time 30 "$api_url")
  fi
  echo "🔍 Modrinth 搜索: $slug ..." >&2
  local file_url fname
  # 取第一个版本的第一个 primary 文件
  file_url=$(echo "$resp" | python3 -c "
import json,sys
try:
    data=json.load(sys.stdin)
    if not data: sys.exit(1)
    v=data[0]
    for f in v.get('files',[]):
        if f.get('primary'):
            print(f['url'])
            print(f['filename'])
            sys.exit(0)
    f=v.get('files',[{}])[0]
    print(f.get('url',''))
    print(f.get('filename',''))
except Exception as e:
    sys.exit(1)
" 2>/dev/null) || { echo "❌ 未找到 $slug 的兼容版本"; return 1; }
  echo "$file_url"
}

install() {
  local src="${1:-}"
  [ -n "$src" ] || { echo "❌ 用法: install <slug|URL|本地文件>"; exit 1; }
  
  local url="" fname=""
  
  if [[ "$src" == http* ]]; then
    # URL 直链
    url="$src"
    fname=$(basename "$src")
  elif [ -f "$src" ]; then
    # 本地文件
    cp "$src" "$PLUGINS_DIR/"
    echo "✅ 已复制本地文件: $(basename "$src")"
    return 0
  else
    # Modrinth slug
    local resolved
    resolved=$(modrinth_resolve "$src") || exit 1
    url=$(echo "$resolved" | head -1)
    fname=$(echo "$resolved" | tail -1)
  fi
  
  [ -n "$url" ] || { echo "❌ 无法解析下载地址"; exit 1; }
  echo "⬇️ 下载: $fname"
  curl -sL --max-time 120 -o "$PLUGINS_DIR/$fname" "$url"
  if [ -s "$PLUGINS_DIR/$fname" ] && file "$PLUGINS_DIR/$fname" | grep -qiE "zip|jar"; then
    echo "✅ 插件已安装: $PLUGINS_DIR/$fname"
    echo "⚠️ 重启服务器后生效（或运行 /reload confirm）"
  else
    echo "❌ 下载失败或非 jar 文件"
    rm -f "$PLUGINS_DIR/$fname"
    exit 1
  fi
}

update() {
  echo "🔍 检查更新中..."
  local updated=0
  for jar in "$PLUGINS_DIR"/*.jar; do
    [ -f "$jar" ] || continue
    local fname
    fname=$(basename "$jar")
    # 尝试 Modrinth 搜索同名 slug
    local slug="${fname%.jar}"
    echo "--- $fname ---"
    if modrinth_resolve "$slug" > /dev/null 2>&1; then
      local resolved
      resolved=$(modrinth_resolve "$slug") || continue
      local new_url new_fname
      new_url=$(echo "$resolved" | head -1)
      new_fname=$(echo "$resolved" | tail -1)
      if [ "$new_fname" != "$fname" ]; then
        echo "⬆️ $fname → $new_fname"
        curl -sL --max-time 120 -o "$PLUGINS_DIR/$new_fname" "$new_url"
        rm -f "$jar"
        updated=$((updated+1))
      else
        echo "已是最新"
      fi
    else
      echo "跳过（无法在 Modrinth 找到: ${slug}）"
    fi
  done
  echo "✅ 更新完成，共更新 $updated 个插件（重启后生效）"
}

remove() {
  local target="${1:-}"
  [ -n "$target" ] || { echo "❌ 用法: remove <文件名.jar>"; exit 1; }
  if [ -f "$PLUGINS_DIR/$target" ]; then
    rm -f "$PLUGINS_DIR/$target"
    echo "✅ 已删除: $target"
  else
    echo "❌ 文件不存在: $PLUGINS_DIR/$target"
    exit 1
  fi
}

list_plugins() {
  if ls "$PLUGINS_DIR"/*.jar > /dev/null 2>&1; then
    echo "已安装插件 ($(ls "$PLUGINS_DIR"/*.jar | wc -l | tr -d ' ')):"
    ls -lh "$PLUGINS_DIR"/*.jar | awk '{printf "  %s (%s)\n", $NF, $5}'
  else
    echo "暂无插件"
  fi
}

case "${1:-}" in
  install) install "${2:-}" ;;
  update)  update ;;
  remove)  remove "${2:-}" ;;
  list)    list_plugins ;;
  *) echo "用法: $0 <install|update|remove|list>"; exit 1 ;;
esac
