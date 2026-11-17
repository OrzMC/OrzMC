#!/bin/bash
# PaperMC 本地部署适配器：create / status / start / stop / restart / logs / upgrade / command
# 用法: PAPER_DIR=~/minecraft-server [PAPER_JAVA=java] adapters/local.sh <action> [args]
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARSE_SCRIPT="$SCRIPT_DIR/../parse_papermc.py"
PAPER_DIR="${PAPER_DIR:-$HOME/minecraft-server}"
JAVA_BIN="${PAPER_JAVA:-java}"
SERVER_JAR=""
MEMORY="${PAPER_MEMORY:-2G}"

# 找到服务器 jar
find_jar() {
  SERVER_JAR=$(ls -t "$PAPER_DIR"/paper-*.jar 2>/dev/null | head -1 || true)
  [ -n "$SERVER_JAR" ] && echo "发现服务端: $(basename "$SERVER_JAR")"
}

# 下载最新 PaperMC jar 到指定目录
download_latest() {
  local dest_dir="$1"
  local info
  info=$("$PARSE_SCRIPT" 2>/dev/null) || { echo "❌ 获取最新版本失败"; return 1; }
  local fname sha
  fname=$(echo "$info" | awk '{print $1}')
  sha=$(echo "$info" | awk '{print $2}')
  local url="https://fill-data.papermc.io/v1/objects/$sha/$fname"
  echo "下载 $fname ..."
  curl -sL --max-time 300 -o "$dest_dir/$fname" "$url"
  # 校验
  local got
  got=$(shasum -a 256 "$dest_dir/$fname" | awk '{print $1}')
  if [ "$got" != "$sha" ]; then
    echo "❌ sha256 校验失败: $got != $sha"
    rm -f "$dest_dir/$fname"
    return 1
  fi
  echo "✅ 下载完成并校验通过: $fname ($(du -h "$dest_dir/$fname" | cut -f1))"
}

create() {
  mkdir -p "$PAPER_DIR"
  download_latest "$PAPER_DIR"
  find_jar
  # EULA
  echo "eula=true" > "$PAPER_DIR/eula.txt"
  # server.properties 基础配置
  if [ ! -f "$PAPER_DIR/server.properties" ]; then
    cat > "$PAPER_DIR/server.properties" << 'EOF'
motd=\u00a7b\u00a7lPaperMC Server \u00a7r\u00a78|\u00a7a welcome
server-port=25565
online-mode=true
difficulty=normal
view-distance=8
simulation-distance=6
max-players=5
spawn-protection=0
enable-command-block=false
EOF
    echo "✅ server.properties 已生成（参考配置）"
  fi
  # 启动脚本
  cat > "$PAPER_DIR/start.sh" << EOF
#!/bin/bash
cd "$PAPER_DIR"
exec $JAVA_BIN -Xms${MEMORY} -Xmx${MEMORY} -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -jar "$SERVER_JAR" nogui
EOF
  chmod +x "$PAPER_DIR/start.sh"
  echo "✅ 服务器已创建: $PAPER_DIR"
  echo "   jar: $(basename "$SERVER_JAR")"
  echo "   启动: $PAPER_DIR/start.sh"
  echo "   EULA 已接受，server.properties 已生成"
}

status() {
  local pid
  pid=$(pgrep -f "paper-.*\.jar" | head -1 || true)
  if [ -n "$pid" ]; then
    echo "✅ 运行中 (PID $pid)"
    local port
    port=$(grep -E "^server-port=" "$PAPER_DIR/server.properties" 2>/dev/null | cut -d= -f2 || echo 25565)
    curl -s --max-time 3 "localhost:$port" 2>/dev/null | head -c 20 | xxd | head -1 && echo " (端口 $port 在线)" || echo "   (进程在但端口未监听)"
  else
    echo "⏹️ 未运行"
  fi
}

start() {
  find_jar
  if [ -z "$SERVER_JAR" ]; then echo "❌ 无服务端 jar，先 create"; exit 1; fi
  if status | grep -q "运行中"; then echo "已在运行"; exit 0; fi
  echo "启动中..."
  cd "$PAPER_DIR"
  mkdir -p "$PAPER_DIR/logs"
  nohup $JAVA_BIN -Xms${MEMORY} -Xmx${MEMORY} -XX:+UseG1GC -XX:MaxGCPauseMillis=100 -jar "$SERVER_JAR" nogui > "$PAPER_DIR/logs/latest.log" 2>&1 &
  echo $! > "$PAPER_DIR/server.pid"
  echo "PID: $!"
  # 等待启动完成（最多 90s）
  for i in $(seq 1 30); do
    sleep 3
    if grep -q 'Done (' "$PAPER_DIR/logs/latest.log" 2>/dev/null; then
      echo "✅ 启动完成: $(grep 'Done (' "$PAPER_DIR/logs/latest.log" | tail -1)"
      return 0
    fi
    if ! kill -0 "$!" 2>/dev/null; then
      echo "❌ 启动失败，日志尾部："
      tail -20 "$PAPER_DIR/logs/latest.log"
      return 1
    fi
  done
  echo "⚠️ 90s 未确认启动完成，请查看日志"
}

stop() {
  local pid
  pid=$(pgrep -f "paper-.*\.jar" | head -1 || true)
  if [ -z "$pid" ]; then echo "未运行"; return 0; fi
  echo "发送 stop 命令..."
  echo "stop" > "/proc/$pid/fd/0" 2>/dev/null || kill "$pid"
  for i in $(seq 1 20); do
    sleep 2
    if ! kill -0 "$pid" 2>/dev/null; then echo "✅ 已停止"; return 0; fi
  done
  echo "强制终止..."
  kill -9 "$pid"
  echo "✅ 已强制停止"
}

restart() {
  stop
  sleep 2
  start
}

logs() {
  local n="${1:-50}"
  tail -n "$n" "$PAPER_DIR/logs/latest.log" 2>/dev/null || echo "无日志文件（服务器未启动过）"
}

command() {
  local pid
  pid=$(pgrep -f "paper-.*\.jar" | head -1 || true)
  if [ -z "$pid" ]; then echo "❌ 服务器未运行"; exit 1; fi
  # 通过 FIFO 或直接 kill -USR? 简单方案：使用 rcon 不可用时提示
  echo "向控制台发送: $*"
  # 使用 jattach 不可用，用 /proc 写入 stdin（需要 root）
  # 简化：通过 signals 无法传命令，提示使用 rcon
  echo "⚠️ 本机无 rcon 配置，建议: echo \"$*\" > /dev/null （或用 screen/tmux 运行服务器）"
}

upgrade() {
  find_jar
  local old_jar="$SERVER_JAR"
  if [ -z "$old_jar" ]; then echo "❌ 无现有 jar，先 create"; exit 1; fi
  local running=0
  if status | grep -q "运行中"; then
    running=1
    echo "服务器运行中，先停止（保存世界）..."
    stop
  fi
  # 备份旧 jar 到 backups/
  mkdir -p "$PAPER_DIR/backups"
  cp "$old_jar" "$PAPER_DIR/backups/$(basename "$old_jar")"
  echo "📦 旧版本已备份: backups/$(basename "$old_jar")"
  # 下载新 jar（download_latest 内部已做 sha256 校验）
  if ! download_latest "$PAPER_DIR"; then
    echo "❌ 升级中止（下载/校验失败），旧版本保留"
    exit 1
  fi
  local new_jar
  new_jar=$(ls -t "$PAPER_DIR"/paper-*.jar | head -1)
  # 若新旧相同则跳过删除
  if [ "$old_jar" != "$new_jar" ]; then
    rm -f "$old_jar"
    echo "✅ 已移除旧版本: $(basename "$old_jar")"
  fi
  # 同步更新 start.sh（保持与当前 jar 一致）
  if [ -f "$PAPER_DIR/start.sh" ]; then
    sed -i '' "s|paper-[0-9.]*-[0-9]*\.jar|$(basename "$new_jar")|g" "$PAPER_DIR/start.sh"
    echo "🔧 start.sh 已同步到 $(basename "$new_jar")"
  fi
  echo "✅ 升级完成: $(basename "$old_jar") → $(basename "$new_jar")"
  if [ "$running" -eq 1 ]; then
    echo "重启服务器..."
    start
  fi
}

case "${1:-}" in
  create)   create ;;
  status)   status ;;
  start)    start ;;
  stop)     stop ;;
  restart)  restart ;;
  logs)     logs "${2:-50}" ;;
  command)  command "${@:2}" ;;
  upgrade)  upgrade ;;
  *) echo "用法: $0 <create|status|start|stop|restart|logs|upgrade|command>"; exit 1 ;;
esac
