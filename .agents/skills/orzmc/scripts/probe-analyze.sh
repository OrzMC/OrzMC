#!/bin/bash
# 分析 /tmp/route-survive.log：哪张表在 eth4 地址抖动下活下来了
L=/tmp/route-survive.log
echo "样本数: $(wc -l <"$L")"
printf 't101(无src) 空表次数: %s\n' "$(grep -c 't101=\[\]' "$L")"
printf 't102(带src) 空表次数: %s\n' "$(grep -c 't102=\[\]' "$L")"
printf 'addr4=NONE 次数: %s\n' "$(grep -c 'addr4=NONE' "$L")"
printf 'main metric 取值: %s\n' "$(grep -oE 'metric=[0-9]+' "$L" | sort -u | tr '\n' ' ')"
echo "--- 出现空表/地址消失的样本（含前后各1行）---"
grep -n -B1 -A1 -E 't101=\[\]|t102=\[\]|addr4=NONE' "$L" | head -40
echo "--- 首样本 ---"; head -1 "$L"
echo "--- 末样本 ---"; tail -1 "$L"
