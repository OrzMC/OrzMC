#!/bin/bash
# OrzMC: 让本机对外服务的应答包绕开 Clash TUN（通用版，与端口无关）
#
# 背景（2026-09-11 实测）:
#   Clash TUN 网卡(198.18.0.1) 默认路由 metric=1 优先于 Wi-Fi 的 metric=45，
#   本机发出的包（含"入站连接的应答"）会走 TUN：出口错网卡、源地址还被定成 198.18.0.1
#     - Java(TCP)   ：SYN-ACK 钻进隧道 → 外网玩家超时
#     - Bedrock(UDP)：pong 从 198.18.0.1 发出 → 客户端丢弃
#   局域网内直连不受影响 → 表现为"内网通、外网不通"。
#
# 核心修复（通用、零维护）:
#   ip rule: from <LAN IP> lookup <TABLE>  +  该表里配好 LAN 出口/网关
#   语义 = 凡是"源地址是本机 LAN IP"的包（即所有监听在 LAN IP 上的服务，无论端口），
#          一律用 Wi-Fi 出口 + Wi-Fi 源地址。代理流量源地址是 TUN(198.18.x) → 不受影响。
#   → 以后新增/自定义任何端口都无需改这里。
#
# 兜底（可选）: 对已知游戏端口再加按源端口的规则，防极端情况下源地址未被选中的场景。
#
# ⚠️ v2（2026-10-04）教训：ip rule 会「存活」而表里的路由会「丢」。
#   旧版在路由丢失时照样 exit 0 → 计划任务显示"成功"，自愈静默失效，外网全超时。
#   v2 起：应用后**自验证**（路由 + 全部规则逐条核对，最多重试 3 次），
#          失败 → 日志 + exit 1（计划任务 LastTaskResult 非 0，可见）；
#          并自动探测 LAN 网卡/网关/本机 IP（不再硬编码 eth4 / 192.168.0.33）。
#
# ⚠️ v3（2026-10-04 同日第二次复发）教训：**不要用 table 100**。
#   WSL mirrored 网络栈自带规则 `100: from all fwmark 0x9 lookup 100`（非本脚本添加），
#   说明 table 100 归 WSL/HNS 管；实测我们的路由在该表里被反复清掉（规则却留着），
#   两次造成外网中断。v3 改用**私有表 101**，并顺手清理指向 100 的历史遗留规则。
#   同时：Windows 计划任务的"重复间隔"会失效（`NextRun` 为空 → 再也不会触发，
#   任务却仍是 Ready/上次 Result=0）→ 必须定期核对 `Get-ScheduledTaskInfo.NextRunTime`。
#
# ⚠️ v4（2026-10-04 第三次复发，机制级定位）教训：**表号不是问题，网卡地址抖动才是**。
#   带时间戳的 netlink 实测: 宿主 Hyper-V VmSwitch 周期性重建 WSL 虚拟网卡
#   （Windows 事件源 Microsoft-Windows-Hyper-V-VmSwitch，由 Docker/HNS 端口活动驱动），
#   客机 eth4 地址被「删除 → 1 秒后重加」，内核随即清掉**所有引用 dev eth4 的路由**
#   （table 100/101 完全相同，带不带 src 也完全相同），而 ip rule 不引用网卡 → 规则留存。
#   现象即「规则在、路由丢」，抖动间隔 12 秒~2 分钟不等，**无法阻止**。
#   → v4 起不再依赖"每分钟轮询"，改为**事件驱动自愈守护**（亚秒级）：
#     orzmc-mc-reply-route-watch.sh 监听 netlink(route/rule/addr/link)，
#     发现路由缺失立刻调本脚本修复；本脚本每次 apply 也会确保守护存活。
#
# 幂等；供开机/登录自愈（Windows 计划任务 OrzMC-MC-Reply-Route 每分钟调一次，
# 现在它主要是"WSL 重启后把守护拉起来"的兜底，实时修复由守护负责）。
# 用法: orzmc-mc-reply-route.sh [--check|--force]
# 环境变量: ORZMC_IFACE / ORZMC_GW / ORZMC_SIP / ORZMC_TCP_PORTS / ORZMC_UDP_PORTS / ORZMC_TABLE
#           ORZMC_NO_DAEMON=1 可禁用守护自启（仅调试用）
# 退出码: 0=正常（已就位或应用并验证通过） / 1=校验失败或缺失(--check)

set -u

TABLE="${ORZMC_TABLE:-101}"          # 私有表，勿用 100（WSL mirrored 占用）
LEGACY_TABLES="100"                  # 历史遗留表，发现我们的规则就清掉
FROM_PREF=85
SPORT_PREF=90
LOG="${ORZMC_ROUTE_LOG:-/var/log/orzmc-mc-reply-route.log}"
MAX_TRY=3
TCP_PORTS="${ORZMC_TCP_PORTS:-25565 25566 25567}"
UDP_PORTS="${ORZMC_UDP_PORTS:-19132 19133 19134}"

MODE="${1:-apply}"

log() {
  if [ -f "$LOG" ] && [ "$(wc -c <"$LOG" 2>/dev/null || echo 0)" -gt 200000 ]; then
    tail -200 "$LOG" >"$LOG.tmp" 2>/dev/null && mv "$LOG.tmp" "$LOG" 2>/dev/null
  fi
  echo "$(date -Is) $*" | tee -a "$LOG" 2>/dev/null || echo "$*"
}

# ── 自动探测 LAN 网卡 / 网关 / 本机 IP（排除 Clash TUN 的 198.18.0.0/15） ──
detect_lan() {
  local line d_if d_gw d_sip
  line="$(ip -4 route show default 2>/dev/null | awk '$3 !~ /^198\.18\./ {print; exit}')"
  d_gw="$(echo "$line" | awk '{print $3}')"
  d_if="$(echo "$line" | awk '{print $5}')"
  [ -n "$d_if" ] || return 1
  d_sip="$(ip -4 -o addr show dev "$d_if" scope global 2>/dev/null | awk '{print $4}' | cut -d/ -f1 | head -1)"
  [ -n "$d_sip" ] || return 1
  IFACE="${ORZMC_IFACE:-$d_if}"
  GW="${ORZMC_GW:-$d_gw}"
  SIP="${ORZMC_SIP:-$d_sip}"
}

IFACE="${ORZMC_IFACE:-}"; GW="${ORZMC_GW:-}"; SIP="${ORZMC_SIP:-}"
if [ -z "$IFACE" ] || [ -z "$GW" ] || [ -z "$SIP" ]; then detect_lan || true; fi

if [ -z "${IFACE:-}" ] || [ -z "${GW:-}" ] || [ -z "${SIP:-}" ]; then
  log "FAIL 无法探测 LAN 出口（iface='${IFACE:-}' gw='${GW:-}' sip='${SIP:-}'）；用 ORZMC_IFACE/ORZMC_GW/ORZMC_SIP 显式指定"
  exit 1
fi

LAN="$(echo "$SIP" | cut -d. -f1-3).0/24"

route_def_ok() { ip route show table "$TABLE" 2>/dev/null | grep -qE "^default via ${GW//./\\.}( |$)"; }
route_lan_ok() { ip route show table "$TABLE" 2>/dev/null | grep -qE "^${LAN//./\\.}( |$)"; }
rule_from_ok() { ip rule show | grep -q "from $SIP lookup $TABLE"; }
rule_sport_ok() { ip rule show | grep -q "ipproto $1 sport $2 lookup $TABLE"; }

verify() {
  # ⚠️ 两条路由必须分别校验：早先只 grep "src $SIP"，任一存在即通过，
  #    实测出现「default 在、/24 丢」（或反之）却报 OK 的漏检。
  route_def_ok || { echo "route table $TABLE 缺 default via $GW（src $SIP）"; return 1; }
  route_lan_ok || { echo "route table $TABLE 缺 $LAN（src $SIP）"; return 1; }
  rule_from_ok || { echo "缺 ip rule 'from $SIP lookup $TABLE'"; return 1; }
  for p in $TCP_PORTS; do rule_sport_ok tcp "$p" || { echo "缺 tcp sport $p 规则"; return 1; }; done
  for p in $UDP_PORTS; do rule_sport_ok udp "$p" || { echo "缺 udp sport $p 规则"; return 1; }; done
  return 0
}

# ── 事件驱动自愈守护（v4）：确保 watcher 常驻（亚秒级修复）──
WATCHER="${ORZMC_WATCHER:-/usr/local/bin/orzmc-mc-reply-route-watch.sh}"
WATCH_PIDFILE="${ORZMC_WATCH_PIDFILE:-/run/orzmc-mc-reply-route-watch.pid}"
daemon_alive() {
  local p
  [ -f "$WATCH_PIDFILE" ] || return 1
  p="$(cat "$WATCH_PIDFILE" 2>/dev/null)"
  [ -n "$p" ] && kill -0 "$p" 2>/dev/null
}
ensure_daemon() {
  [ "${ORZMC_NO_DAEMON:-0}" = "1" ] && return 0
  [ -x "$WATCHER" ] || return 0
  daemon_alive && return 0
  setsid nohup "$WATCHER" >/dev/null 2>&1 </dev/null &
  sleep 1
  if daemon_alive; then
    log "DAEMON 已拉起 $WATCHER (pid $(cat "$WATCH_PIDFILE" 2>/dev/null))"
  else
    log "WARN 守护拉起失败（$WATCHER 不存在/不可执行/锁被占）"
  fi
}
# ⚠️ 必须放在「已就位就 exit 0」之前：路由正常但守护已死时，任务不能直接退出。
[ "$MODE" = "--check" ] || ensure_daemon

if [ "$MODE" = "--check" ]; then
  if out="$(verify)"; then echo "OK"; exit 0; else echo "MISSING: $out"; exit 1; fi
fi

if [ "$MODE" != "--force" ]; then
  if out="$(verify)"; then log "OK 已就位（iface=$IFACE gw=$GW src=$SIP table=$TABLE）"; exit 0; fi
  log "DETECT 需要修复: $out"
fi

# 等网卡就绪（开机自愈场景）
for i in $(seq 1 30); do
  ip link show "$IFACE" >/dev/null 2>&1 && ip -4 addr show "$IFACE" | grep -q "$SIP" && break
  [ "$i" = 30 ] && log "WARN 网卡 $IFACE/$SIP 60s 内未就绪，仍尝试配置"
  sleep 2
done

cleanup_legacy() {
  local t p
  for t in $LEGACY_TABLES; do
    [ "$t" = "$TABLE" ] && continue
    ip rule del from "$SIP" table "$t" 2>/dev/null
    for p in $TCP_PORTS; do ip rule del ipproto tcp sport "$p" table "$t" 2>/dev/null; done
    for p in $UDP_PORTS; do ip rule del ipproto udp sport "$p" table "$t" 2>/dev/null; done
    # 只清"我们的"残留路由，不碰 WSL 自带的 fwmark 规则/其它表内容
    ip route del "$LAN" dev "$IFACE" table "$t" 2>/dev/null
    ip route del default via "$GW" dev "$IFACE" src "$SIP" table "$t" 2>/dev/null
  done
}

apply_once() {
  ip route replace default via "$GW" dev "$IFACE" src "$SIP" table "$TABLE" 2>&1
  ip route replace "$LAN" dev "$IFACE" src "$SIP" table "$TABLE" 2>&1

  # ① 通用规则：源 = LAN IP 的所有包（覆盖任意端口）
  ip rule del from "$SIP" table "$TABLE" 2>/dev/null
  ip rule add from "$SIP" table "$TABLE" pref "$FROM_PREF" 2>&1

  # ② 兜底：已知游戏端口按源端口
  for p in $UDP_PORTS; do
    ip rule del ipproto udp sport "$p" table "$TABLE" 2>/dev/null
    ip rule add ipproto udp sport "$p" table "$TABLE" pref "$SPORT_PREF" 2>&1
  done
  for p in $TCP_PORTS; do
    ip rule del ipproto tcp sport "$p" table "$TABLE" 2>/dev/null
    ip rule add ipproto tcp sport "$p" table "$TABLE" pref "$SPORT_PREF" 2>&1
  done

  cleanup_legacy
}

for attempt in $(seq 1 $MAX_TRY); do
  apply_once
  if out="$(verify)"; then
    log "APPLIED table=$TABLE iface=$IFACE gw=$GW src=$SIP rule='from $SIP' + sport=[tcp:$TCP_PORTS udp:$UDP_PORTS] (attempt $attempt) 校验通过"
    exit 0
  fi
  log "FAIL attempt $attempt/$MAX_TRY 校验未通过: $out"
  sleep 3
done

log "FAIL 应用 $MAX_TRY 次后仍未通过校验（外网入口会不通！）iface=$IFACE gw=$GW src=$SIP"
exit 1
