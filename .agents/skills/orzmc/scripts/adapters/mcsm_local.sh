#!/bin/bash
# PaperMC MCSManager 本机栈适配器（2026-09-03 建，本地测试服迁 MCSM 后用）
# 用法: adapters/mcsm_local.sh <action> [args]
# 依赖环境变量（~/.hermes/.env）: MCSM_LOCAL_URL MCSM_LOCAL_API_KEY MCSM_LOCAL_DAEMON_ID MCSM_LOCAL_INSTANCE_ID
#   daemon 节点 orzmc-local；本地端实例 = papermc-test（uuid 716c2fb7，三端审查基准）
# ⚠️ 本机测试服共享 world 严禁同跑——start 前须面板确认另一实例已停（docker ps --filter name=MCSM-）
set -euo pipefail

# ⚠️ 无条件 source：持久 shell 环境可能残留旧值（改 .env 后不刷新会误用旧 key）
if [ -f "$HOME/.hermes/.env" ]; then
  set -a; source "$HOME/.hermes/.env"; set +a
fi

MCSM_URL="${MCSM_LOCAL_URL:-https://mcs.{SERVER_NAME}.cn/}"
APIKEY="${MCSM_LOCAL_API_KEY:-}"
DAEMON="${MCSM_LOCAL_DAEMON_ID:-}"
INSTANCE="${MCSM_LOCAL_INSTANCE_ID:-716c2fb712154c36ba5ab0f1480d3f87}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HDRS=(-H "Content-Type: application/json; charset=utf-8" -H "X-Requested-With: XMLHttpRequest")

api_get() {
  local path="$1"
  curl -sL --max-time 15 "${MCSM_URL}${path}" "${HDRS[@]}" -G \
    --data-urlencode "apikey=${APIKEY}"
}

api_post() {
  local path="$1" body="${2:-{}}"
  curl -sL --max-time 15 -X POST "${MCSM_URL}${path}?apikey=${APIKEY}" \
    "${HDRS[@]}" -d "$body"
}

inst_status() {
  api_get "api/instance?daemonId=${DAEMON}&uuid=${INSTANCE}"
}

status() {
  local resp
  resp=$(inst_status)
  echo "$resp" | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    print('❌ API 响应异常'); sys.exit(1)
if d.get('status') != 200:
    print('❌ API 错误:', d.get('data', d.get('error', 'unknown')))
    sys.exit(1)
data = d['data']
status_map = {-1:'⏳ 忙碌', 0:'⏹️ 停止', 1:'⏹️ 停止中', 2:'🔄 启动中', 3:'🟢 运行中'}
s = status_map.get(data['status'], f\"状态码{data['status']}\")
info = data.get('info', {})
cfg = data.get('config', {})
print(f'{s} | {info.get(\"version\",\"?\")} | 玩家 {info.get(\"currentPlayers\",\"?\")}/{info.get(\"maxPlayers\",\"?\")}')
print(f'端口 {cfg.get(\"pingConfig\",{}).get(\"port\",\"?\")}')
"
}

check_no_players() {
  local resp info
  resp=$(inst_status)
  info=$(echo "$resp" | python3 -c "
import json, sys
d = json.load(sys.stdin)
if d.get('status') == 200:
    print(d['data'].get('info',{}).get('currentPlayers', 0))
else:
    print(-1)
")
  if [ "$info" -gt 0 ] 2>/dev/null; then
    echo "❌ 有 ${info} 名玩家在线，禁止破坏性操作"
    exit 1
  fi
}

start() {
  check_no_players
  echo "启动本机实例（⚠️ 确认另一实例已停）..."
  api_get "api/protected_instance/open?daemonId=${DAEMON}&uuid=${INSTANCE}" | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ 启动命令已发送' if d.get('status')==200 else '❌ '+str(d.get('data', d.get('error'))))"
}

stop() {
  check_no_players
  echo "停止实例..."
  api_get "api/protected_instance/stop?daemonId=${DAEMON}&uuid=${INSTANCE}" | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ 停止命令已发送' if d.get('status')==200 else '❌ '+str(d.get('data', d.get('error'))))"
}

restart() {
  check_no_players
  echo "重启实例..."
  api_get "api/protected_instance/restart?daemonId=${DAEMON}&uuid=${INSTANCE}" | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ 重启命令已发送' if d.get('status')==200 else '❌ '+str(d.get('data', d.get('error'))))"
}

command() {
  check_no_players
  local cmd="$*"
  echo "发送命令: $cmd"
  api_get "api/protected_instance/command?daemonId=${DAEMON}&uuid=${INSTANCE}&command=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1]))" "$cmd")" | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ 命令已发送' if d.get('status')==200 else '❌ '+str(d.get('data', d.get('error'))))"
}

case "${1:-}" in
  status)  status ;;
  start)   start ;;
  stop)    stop ;;
  restart) restart ;;
  command) command "${@:2}" ;;
  *) echo "用法: $0 <status|start|stop|restart|command>"; exit 1 ;;
esac
