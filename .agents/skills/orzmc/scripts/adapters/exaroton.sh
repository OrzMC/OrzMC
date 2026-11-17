#!/bin/bash
# Exaroton 云端适配器：status / start / stop / restart / logs / command / plugin
# 依赖: EXAROTON_API_KEY（exaroton.com/account 生成）+ EXAROTON_SERVER_ID
# 用法: EXAROTON_API_KEY=xxx EXAROTON_SERVER_ID=xxx adapters/exaroton.sh <action> [args]
set -euo pipefail

API="https://api.exaroton.com/v1"
KEY="${EXAROTON_API_KEY:-}"
SID="${EXAROTON_SERVER_ID:-}"

[ -n "$KEY" ] || { echo "❌ 未设置 EXAROTON_API_KEY"; exit 1; }
[ -n "$SID" ] || { echo "❌ 未设置 EXAROTON_SERVER_ID"; exit 1; }

req() { # req <method> <path> [data]
  local method="$1" path="$2" data="${3:-}"
  if [ -n "$data" ]; then
    curl -sL -X "$method" -H "Authorization: Bearer $KEY" \
      -H "Content-Type: application/json" -d "$data" "$API$path"
  else
    curl -sL -X "$method" -H "Authorization: Bearer $KEY" "$API$path"
  fi
}

status() {
  local resp
  resp=$(req GET "/servers/$SID")
  echo "$resp" | python3 -c "
import json,sys
STATUS_MAP = {
    0: '⏹️ 停止', 1: '🔄 启动中', 2: '🟢 在线', 3: '⏹️ 停止中',
    4: '💥 崩溃', 5: '📦 安装中', 6: '🔁 等待重启', 7: '🧹 清理中'
}
d=json.load(sys.stdin)
if d.get('data'):
    s=d['data']
    st=s.get('status')
    sw=s.get('software',{})
    pl=s.get('players',{})
    print(f\"名称: {s.get('name')}\")
    print(f\"状态: {STATUS_MAP.get(st, st)}\")
    print(f\"地址: {s.get('address')}:{s.get('port')}\")
    print(f\"软件: {sw.get('name')} {sw.get('version')}\")
    print(f\"玩家: {pl.get('count')}/{pl.get('max')}\")
else:
    print('响应:', d)
"
}

do_action() { # start|stop|restart
  req POST "/servers/$SID/$1" > /dev/null
  echo "✅ 已发送 $1 指令"
}

logs() {
  local n="${1:-50}"
  req GET "/servers/$SID/logs" | python3 -c "
import json,sys
d=json.load(sys.stdin)
content=d.get('data',{}).get('content','') if d.get('data') else ''
lines=content.split('\n')
print('\n'.join(lines[-${n}:]))
" 2>/dev/null || req GET "/servers/$SID/logs"
}

command() {
  req POST "/servers/$SID/command" "{\"command\": \"$*\"}" > /dev/null
  echo "✅ 已发送命令: $*"
}

plugin() { # plugin <install|remove|list> [文件名.jar] [本地路径]
  local act="${1:-}"
  case "$act" in
    list)
      req GET "/servers/$SID/files/info/plugins/" | python3 -c "
import json,sys
d=json.load(sys.stdin)
if d.get('data'):
    for c in d['data'].get('children',[]):
        if c.get('name','').endswith('.jar'):
            print(f\"  {c['name']} ({c.get('size',0)//1024}KB)\")
else:
    print('响应:', d)
"
      ;;
    install|remove)
      local fname="${2:-}"
      [ -n "$fname" ] || { echo "❌ 用法: plugin $act <文件名.jar> [本地路径]"; exit 1; }
      local path="plugins/$fname"
      if [ "$act" = "install" ]; then
        local src="${3:-$fname}"
        [ -f "$src" ] || { echo "❌ 本地文件不存在: $src"; exit 1; }
        echo "⬆️ 上传 $fname 到 Exaroton..."
        # Exaroton 上传用 PUT 方法 + raw body（非 multipart）
        curl -sL -X PUT -H "Authorization: Bearer $KEY" \
          -H "Content-Type: application/octet-stream" \
          --data-binary "@$src" "$API/servers/$SID/files/data/$path/"
        echo ""
        echo "✅ 上传完成（需 restart 生效）"
      else
        req DELETE "/servers/$SID/files/data/$path/"
        echo "✅ 已删除 ${fname}（需 restart 生效）"
      fi
      ;;
    *) echo "❌ 用法: plugin <install|remove|list>"; exit 1 ;;
  esac
}

case "${1:-}" in
  status)  status ;;
  start)   do_action start ;;
  stop)    do_action stop ;;
  restart) do_action restart ;;
  logs)    logs "${2:-50}" ;;
  command) command "${@:2}" ;;
  plugin)  plugin "${@:2}" ;;
  *) echo "用法: $0 <status|start|stop|restart|logs|command|plugin>"; exit 1 ;;
esac
