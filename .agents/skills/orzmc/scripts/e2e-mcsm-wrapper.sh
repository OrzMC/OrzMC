#!/bin/bash
# e2e-mcsm-wrapper.sh —— OrzMC E2E ↔ MCSM 本机栈实例 对接层（技能侧，2026-09-03 测试服迁 MCSM 后）
# 插件仓库 e2e/ 保持独立（零本机路径/MCSM 布局假设），本 wrapper 负责环境适配：
#   实例状态校验（面板 API）→ 注入环境变量（CORE/TEST_DIR/CONSOLE_URL/API_KEY…）→ 调仓库 run-all.sh
# 用法: e2e-mcsm-wrapper.sh [paper|folia] [run-all.sh 参数...]
#   例: e2e-mcsm-wrapper.sh paper -c 01          # Paper 实例跑 01 用例
#       e2e-mcsm-wrapper.sh folia -c 05 -c 06    # Folia 实例跑群消息用例
# 依赖: ~/.hermes/.env（MCSM_LOCAL_URL/API_KEY/DAEMON_ID）+ 仓库 ~/OrzMC/plugin/e2e
# ⚠️ 共享 world 严禁同跑：目标实例必须已在面板启动，且另一实例已停
set -uo pipefail

SKILL=~/.hermes/skills/gaming/orzmc
E2E=~/OrzMC/plugin/e2e
ENV=~/.hermes/.env
PY=/usr/bin/python3
DATA_ROOT=/Users/Shared/orzmc
INSTANCE_DIR=$DATA_ROOT/mcsmanager/daemon/data/InstanceData

CORE="${1:-paper}"
[ $# -gt 0 ] && shift
case "$CORE" in
  paper) UUID=716c2fb712154c36ba5ab0f1480d3f87 ;;
  folia) UUID=8A932DD47F4D42AAAD6A6A9A5FAD2A91 ;;
  *) echo "用法: $0 [paper|folia] [run-all 参数...]"; exit 1 ;;
esac

env_get() { grep -E "^$1=" "$ENV" | head -1 | cut -d= -f2- | tr -d '"'"'"' '; }
URL=$(env_get MCSM_LOCAL_URL)
KEY=$(env_get MCSM_LOCAL_API_KEY)
DAEMON=$(env_get MCSM_LOCAL_DAEMON_ID)
if [ -z "$KEY" ] || [ -z "$DAEMON" ]; then
  echo "❌ .env 缺少 MCSM_LOCAL_API_KEY / MCSM_LOCAL_DAEMON_ID（#1 审计改造已加）" >&2
  exit 1
fi

# 1. 实例状态（面板 API status: 3=运行中）
RESP=$(curl -sL --max-time 15 "${URL}api/instance?daemonId=${DAEMON}&uuid=${UUID}" \
  -H "Content-Type: application/json" -H "X-Requested-With: XMLHttpRequest" \
  -G --data-urlencode "apikey=${KEY}" 2>/dev/null)
ST=$(echo "$RESP" | $PY -c 'import sys,json
try:
    d = json.load(sys.stdin)
    print(d.get("data",{}).get("status",-2))
except Exception:
    print(-3)' 2>/dev/null)
if [ "$ST" != "3" ]; then
  echo "❌ 实例 ${CORE}（${UUID}）未运行（status=${ST}）——先经面板启动（共享 world 严禁双开，另一实例须已停）" >&2
  exit 1
fi
echo "✅ 实例 ${CORE} 运行中（${UUID}）"

# 2. 仓库依赖（node_modules 不入库，首次自动 npm install）
if [ ! -d "$E2E/node_modules" ]; then
  echo "首次运行：安装 e2e 依赖（仓库内 npm install，版本锁 package-lock.json）..."
  (cd "$E2E" && npm install --no-audit --no-fund) || { echo "❌ npm install 失败" >&2; exit 1; }
fi

# 3. 注入环境变量（日志/备份路径由 run-all 按 TEST_DIR 推断，可显式覆盖）
export ORZMC_CORE="$CORE"
export ORZMC_TEST_DIR="$INSTANCE_DIR/$UUID"
export ORZMC_TEST_PORT="${ORZMC_TEST_PORT:-25565}"
export ORZMC_RCON_MODE="${ORZMC_RCON_MODE:-http}"
export ORZMC_CONSOLE_URL="${URL}api/protected_instance/command"
export ORZMC_API_KEY="$KEY"
echo "注入: CORE=${CORE} | TEST_DIR=${INSTANCE_DIR}/${UUID} | console=${URL}api/protected_instance/command"
cd "$E2E" && bash run-all.sh "$@"
