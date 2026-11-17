#!/bin/bash
# DeathChest 修复多轮回归测试
# 每轮: bugtest-precise(死亡+下线) → bugtest-check3(查箱子) → 统计
# 同账号重连有 20-30s 冷却，轮间 sleep
cd ~/minecraft-bot

ROUNDS=${1:-8}   # 默认 8 轮
PASS=0
FAIL=0
FAIL_DETAILS=""

echo "========== DeathChest 修复多轮回归测试（${ROUNDS} 轮）=========="
for ((i=1; i<=ROUNDS; i++)); do
  echo ""
  echo "--- 轮次 $i/${ROUNDS} ($(date +%H:%M:%S)) ---"

  # 1. 死亡+立即下线
  OUT1=$(BOT_PASSWORD={BOT_PASSWORD} node bugtest-precise.js 2>&1)
  if echo "$OUT1" | grep -q "超时"; then
    echo "  ❌ 第 $i 轮: 登录/死亡超时（可能冷却未过）"
    FAIL=$((FAIL+1)); FAIL_DETAILS="${FAIL_DETAILS} R${i}(timeout)"
    sleep 35; continue
  fi
  if ! echo "$OUT1" | grep -q "死亡坐标已存"; then
    echo "  ❌ 第 $i 轮: 未完成死亡流程"
    echo "$OUT1" | tail -2
    FAIL=$((FAIL+1)); FAIL_DETAILS="${FAIL_DETAILS} R${i}(no-death)"
    sleep 35; continue
  fi

  sleep 3  # 等建箱完成

  # 2. 查箱子
  OUT2=$(BOT_PASSWORD={BOT_PASSWORD} node bugtest-check3.js 2>&1)
  HITS=$(echo "$OUT2" | grep -oE "结果: [0-9]+ 个成功命中" | grep -oE "[0-9]+")
  if [ -z "$HITS" ]; then HITS=0; fi

  if [ "$HITS" -ge 1 ]; then
    echo "  ✅ 轮次 $i 通过: 箱子命中 $HITS 个"
    PASS=$((PASS+1))
  else
    echo "  ❌ 轮次 $i 失败: 箱子 0 命中"
    echo "$OUT2" | tail -2
    FAIL=$((FAIL+1)); FAIL_DETAILS="${FAIL_DETAILS} R${i}(0-hit)"
  fi

  # 轮间冷却（同账号重连）
  [ $i -lt $ROUNDS ] && sleep 30
done

echo ""
echo "========== 结果汇总 =========="
echo "通过: $PASS / $ROUNDS   失败: $FAIL"
[ -n "$FAIL_DETAILS" ] && echo "失败详情:$FAIL_DETAILS"
if [ "$FAIL" -eq 0 ]; then
  echo "✅✅ 全部通过：DeathChest 修复稳定（非偶然）"
else
  echo "🔴 有失败轮次，需排查"
fi

# 3. 物品存档完整性统计
echo ""
echo "--- 物品存档统计 ---"
grep -c "diamond" ~/minecraft-server/world/dimensions/minecraft/overworld/death-chests.yml | xargs echo "death-chests.yml 中 diamond 记录数:"
grep -c "count: 5" ~/minecraft-server/world/dimensions/minecraft/overworld/death-chests.yml | xargs echo "count:5 记录数:"
