#!/bin/bash
# 探针：对比「带 src」与「不带 src」策略路由在 eth4 地址抖动下的存活
# table 101 = 不带 src（候选修法）；table 102 = 带 src（现状对照）
LOG=/tmp/route-survive.log
: >"$LOG"
while true; do
  ts=$(date -Is)
  r101=$(ip route show table 101 | tr '\n' ';' | sed 's/;[[:space:]]*/; /g')
  r102=$(ip route show table 102 | tr '\n' ';' | sed 's/;[[:space:]]*/; /g')
  addr=$(ip -4 -o addr show dev eth4 2>/dev/null | awk '{print $4}' | head -1)
  maindef=$(ip route show default 2>/dev/null | awk '$3 !~ /^198\.18\./{print $3" metric="$NF; exit}')
  echo "$ts | addr4=${addr:-NONE} | main=${maindef:-NONE} | t101=[$r101] | t102=[$r102]" >>"$LOG"
  sleep 5
done
