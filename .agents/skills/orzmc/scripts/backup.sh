#!/bin/bash
# PaperMC 服务器备份：打包 world/ + plugins/ + server.properties + 保留最近 N 份
# 用法: PAPER_DIR=~/minecraft-server backup.sh [份数，默认24]
set -euo pipefail

PAPER_DIR="${PAPER_DIR:-$HOME/minecraft-server}"
BACKUP_DIR="${BACKUP_DIR:-$PAPER_DIR/backups}"
MAX_BACKUPS="${1:-24}"

[ -d "$PAPER_DIR" ] || { echo "❌ 服务器目录不存在: $PAPER_DIR"; exit 1; }

# 运行中先提示
if pgrep -f "paper-.*\.jar" > /dev/null 2>&1; then
  echo "⚠️ 服务器正在运行，建议先 stop 再备份（防止 world 写入不一致）"
fi

mkdir -p "$BACKUP_DIR"
TIMESTAMP=$(date +%Y-%m-%d_%H-%M-%S)
JAR_NAME=$(ls -t "$PAPER_DIR"/paper-*.jar 2>/dev/null | head -1 | xargs basename 2>/dev/null || echo "unknown")

echo "📦 备份开始: $TIMESTAMP"
echo "  服务端: $JAR_NAME"

# 打包
tar -czf "$BACKUP_DIR/paper_${TIMESTAMP}.tar.gz" \
  -C "$PAPER_DIR" \
  world world_nether world_the_end plugins server.properties eula.txt \
  2>/dev/null || tar -czf "$BACKUP_DIR/paper_${TIMESTAMP}.tar.gz" \
  -C "$PAPER_DIR" \
  world plugins server.properties eula.txt 2>/dev/null || {
    echo "❌ 备份失败（无 world/ 目录？首次启动后才有）"
    exit 1
  }

SIZE=$(du -h "$BACKUP_DIR/paper_${TIMESTAMP}.tar.gz" | cut -f1)
echo "✅ 备份完成: $BACKUP_DIR/paper_${TIMESTAMP}.tar.gz ($SIZE)"

# 清理旧备份
COUNT=$(ls -1 "$BACKUP_DIR"/paper_*.tar.gz 2>/dev/null | wc -l | tr -d ' ')
if [ "$COUNT" -gt "$MAX_BACKUPS" ]; then
  REMOVE=$((COUNT - MAX_BACKUPS))
  ls -1t "$BACKUP_DIR"/paper_*.tar.gz | tail -n "$REMOVE" | xargs rm -f
  echo "🧹 清理了 $REMOVE 份旧备份（保留最近 $MAX_BACKUPS 份）"
fi

echo "当前备份数: $(ls -1 "$BACKUP_DIR"/paper_*.tar.gz 2>/dev/null | wc -l | tr -d ' ')"
