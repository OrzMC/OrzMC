#!/bin/bash
# PaperMC MCSManager 面板适配器：status / logs / players（只读）/ start / stop / restart / command
# 用法: adapters/mcsm.sh <action> [args]
# 依赖环境变量（~/.hermes/.env）: MCSM_URL MCSM_API_KEY MCSM_DAEMON_ID MCSM_INSTANCE_ID
set -euo pipefail

# 载入 .env（无条件：持久 shell 环境可能残留旧值，改 .env 后不刷新会误用旧 key）
if [ -f "$HOME/.hermes/.env" ]; then
  set -a; source "$HOME/.hermes/.env"; set +a
fi

MCSM_URL="${MCSM_URL:-http://{SERVER_HOST}:23333/}"
APIKEY="${MCSM_API_KEY:-}"
DAEMON="${MCSM_DAEMON_ID:-}"
INSTANCE="${MCSM_INSTANCE_ID:-}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HDRS=(-H "Content-Type: application/json; charset=utf-8" -H "X-Requested-With: XMLHttpRequest")

api_get() {
  # api_get <path> -> 输出 JSON 到 stdout
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
  # 用 python3 解析（无 jq 依赖）
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
proc = data.get('processInfo', {})
cfg = data.get('config', {})
print(f'{s} | {info.get(\"version\",\"?\")} | 玩家 {info.get(\"currentPlayers\",\"?\")}/{info.get(\"maxPlayers\",\"?\")}')
if proc.get('pid'):
    mem = proc.get('memory', 0)//1024//1024
    hrs = proc.get('elapsed', 0)//3600000
    mins = proc.get('elapsed', 0)%3600000//60000
    print(f'PID {proc[\"pid\"]} | {mem}MB | 已运行 {hrs}h{mins}m')
print(f'端口 {cfg.get(\"pingConfig\",{}).get(\"port\",\"?\")} | autoStart={cfg.get(\"eventTask\",{}).get(\"autoStart\")} autoRestart={cfg.get(\"eventTask\",{}).get(\"autoRestart\")}')
"
}

players() {
  local resp
  resp=$(api_get "api/protected_instance/outputlog?daemonId=${DAEMON}&uuid=${INSTANCE}")
  echo "$resp" | python3 "$SCRIPT_DIR/../parse_mcsm_players.py"
}

logs() {
  local n="${1:-50}"
  local resp
  resp=$(api_get "api/protected_instance/outputlog?daemonId=${DAEMON}&uuid=${INSTANCE}")
  echo "$resp" | python3 "$SCRIPT_DIR/../parse_mcsm_logs.py" "$n"
}

# 玩家数检查（破坏性操作前调用）
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
    echo "❌ 有 ${info} 名玩家在线，禁止破坏性操作（遵守安全约束）"
    exit 1
  fi
  if [ "$info" -lt 0 ]; then
    echo "❌ 无法确认玩家数，中止"
    exit 1
  fi
}

start() {
  check_no_players
  echo "启动实例..."
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

kill() {
  echo "强制终止实例 (kill)..."
  api_get "api/protected_instance/kill?daemonId=${DAEMON}&uuid=${INSTANCE}" | python3 -c "import json,sys; d=json.load(sys.stdin); print('✅ 已终止' if d.get('status')==200 else '❌ '+str(d.get('data', d.get('error'))))"
}

case "${1:-}" in
  status)  status ;;
  players) players ;;
  logs)    logs "${2:-50}" ;;
  start)   start ;;
  stop)    stop ;;
  restart) restart ;;
  kill)    kill ;;
  command) command "${@:2}" ;;
  *) echo "用法: $0 <status|players|logs|start|stop|restart|kill|command>"; exit 1 ;;
esac
