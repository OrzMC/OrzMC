#!/bin/bash
# OrzMC: 事件驱动自愈 —— 监听 netlink，一旦发现策略路由缺失立刻修复（亚秒级）
#
# 为什么需要它（2026-10-04 机制级定位）:
#   WSL2 mirrored 模式下，宿主 Hyper-V VmSwitch 会周期性重建 WSL 的虚拟网卡
#   （Microsoft-Windows-Hyper-V-VmSwitch 事件 ID 291；由 Docker/HNS 端口活动驱动），
#   客机 eth4 的地址被删除→重加，内核随即清掉**所有引用 dev eth4 的路由**
#   （无论 table 100/101、带不带 src），而 ip rule 因不引用网卡得以存活
#   → 现象即「规则在、路由丢」，外网入站应答改走 Clash TUN → 超时。
#   此抖动不可阻止，只能毫秒/秒级跟随修复。
#
# 设计: 任何 netlink route/rule/addr/link 事件 → 校验 → 缺失才修复（幂等、带节流防自激）
# 用法: orzmc-mc-reply-route-watch.sh        (由 systemd 服务常驻)
set -u
APPLY=/usr/local/bin/orzmc-mc-reply-route.sh
LOG=${ORZMC_WATCH_LOG:-/var/log/orzmc-mc-reply-route-watch.log}
THROTTLE=${ORZMC_WATCH_THROTTLE:-2}   # 秒：修复后静默期，避免修复动作触发的事件自激

log() {
  if [ -f "$LOG" ] && [ "$(wc -c <"$LOG" 2>/dev/null || echo 0)" -gt 200000 ]; then
    tail -200 "$LOG" >"$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG" 2>/dev/null
  fi
  echo "$(date -Is) $*" >>"$LOG" 2>/dev/null
}

# ── 单实例 + pidfile（避免 pgrep -f 字符串误匹配；供主脚本精确判断存活）──
PIDFILE=/run/orzmc-mc-reply-route-watch.pid
LOCK=/run/orzmc-mc-reply-route-watch.lock
exec 9>"$LOCK" 2>/dev/null || true
if ! flock -n 9 2>/dev/null; then
  log "SKIP 已有实例在运行（锁 $LOCK），本进程退出"
  exit 0
fi
echo $$ >"$PIDFILE" 2>/dev/null || true
trap 'rm -f "$PIDFILE" 2>/dev/null' EXIT

# 启动即修一次，保证服务起来就是对的
if ! "$APPLY" --check >/dev/null 2>&1; then
  "$APPLY" >>"$LOG" 2>&1
  log "STARTUP 修复完成"
fi

last=0
ip monitor route rule addr link 2>/dev/null | while read -r _line; do
  now=$(date +%s)
  [ $((now - last)) -lt "$THROTTLE" ] && continue
  if ! "$APPLY" --check >/dev/null 2>&1; then
    last=$now
    if out="$("$APPLY" 2>&1)"; then
      log "HEAL netlink 事件触发修复成功: $(echo "$out" | tail -1)"
    else
      log "FAIL netlink 事件触发修复未通过: $(echo "$out" | tail -1)"
    fi
  fi
done
