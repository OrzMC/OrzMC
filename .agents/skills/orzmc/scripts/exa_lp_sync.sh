#!/bin/bash
# Exaroton LP 权限同步模板（2026-08-08 实测）
# 用法：先停服上传 plugins/update/ → start → 等 ONLINE → 本脚本
# 依赖：~/.hermes/.env 含 EXAROTON_API_KEY / EXAROTON_SERVER_ID
# 输入：~/minecraft-bot/perm_commands.txt（每行一条 "lp group <G> permission set <node> true"）
set -e
source ~/.hermes/.env 2>/dev/null
UA="User-Agent: Mozilla/5.0"
AUTH="Authorization: Bearer $EXAROTON_API_KEY"
BASE="https://api.exaroton.com/v1/servers/$EXAROTON_SERVER_ID"

echo "=== extend-time +600s（防无玩家自动停）==="
curl -s -X POST -H "$AUTH" -H "$UA" -H "Content-Type: application/json" -d '{"time":600}' "$BASE/extend-time/" | head -c 80
echo ""

echo "=== parent 链（Bootstrap 自动校正，手动幂等保险）==="
for cmd in "lp group member parent set default" "lp group builder parent set member" "lp group admin parent set builder"; do
  curl -s -X POST -H "$AUTH" -H "$UA" -H "Content-Type: application/json" -d "{\"command\": \"$cmd\"}" "$BASE/command/" | head -c 60
  echo " <- $cmd"
  sleep 1.2
done

echo "=== permission set 全量（perm_commands.txt）==="
grep "permission set" /Users/bot/minecraft-bot/perm_commands.txt | while IFS= read -r cmd; do
  curl -s -X POST -H "$AUTH" -H "$UA" -H "Content-Type: application/json" -d "{\"command\": \"$cmd\"}" "$BASE/command/" | head -c 40
  echo ""
  sleep 1.2
done
echo "=== 完成——事后必须 LP check 验证（输出进服务器日志）==="
