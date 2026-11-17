#!/bin/bash
# 带时间戳重新武装 netlink 监视器
LOG=${1:-/tmp/netmon2.log}
: >"$LOG"
setsid nohup bash -c "ip monitor route rule addr link | while read -r l; do printf '%s %s\n' \"\$(date -Is)\" \"\$l\"; done" >>"$LOG" 2>&1 &
sleep 3
printf 'armed %s lines -> %s\n' "$(wc -l <"$LOG")" "$LOG"
