#!/bin/bash
# 插件修复多轮回归测试循环（DeathChest 案例验证模式）
# 用法: BOT_PASSWORD=xxx bash regression-loop.sh [轮数，默认 8]
# 前置: 同目录需有 "死亡+下线" 脚本与查箱脚本（见下变量），服务器已运行
# 关键: 同账号重连有 20-30s 冷却（LoginSecurity/反垃圾），轮间必须 sleep

# ---- 可配置 ----
TEST_DIR=${TEST_DIR:-$(dirname "$0")}          # 脚本目录（含 precise + check3）
DEATH_SCRIPT=${DEATH_SCRIPT:-bugtest-precise.js} # 死亡+立即下线 → 写 /tmp/death_pos.json
CHECK_SCRIPT=${CHECK_SCRIPT:-bugtest-check3.js}  # 读坐标 → 3x3x3 查箱 → 输出"结果: N 个成功命中"
CHEST_ARCHIVE=${CHEST_ARCHIVE:-}                 # 存档路径（可选，用于物品完整性统计）
ROUNDS=${1:-8}
PASS=0; FAIL=0; FAIL_DETAILS=""

echo "========== 修复多轮回归（${ROUNDS} 轮）=========="
for ((i=1; i<=ROUNDS; i++)); do
  echo "--- 轮次 $i/$ROUNDS ($(date +%H:%M:%S)) ---"
  OUT1=$(cd "$TEST_DIR" && BOT_PASSWORD="$BOT_PASSWORD" node "$DEATH_SCRIPT" 2>&1)
  if echo "$OUT1" | grep -q "超时"; then
    echo "  ❌ 轮次 $i: 登录/死亡超时（冷却未过？）"; FAIL=$((FAIL+1)); FAIL_DETAILS="${FAIL_DETAILS} R${i}(timeout)"
    sleep 35; continue
  fi
  if ! echo "$OUT1" | grep -q "死亡坐标已存"; then
    echo "  ❌ 轮次 $i: 死亡流程未完成"; FAIL=$((FAIL+1)); FAIL_DETAILS="${FAIL_DETAILS} R${i}(no-death)"
    sleep 35; continue
  fi
  sleep 3  # 等建箱完成
  OUT2=$(cd "$TEST_DIR" && BOT_PASSWORD="$BOT_PASSWORD" node "$CHECK_SCRIPT" 2>&1)
  HITS=$(echo "$OUT2" | grep -oE "结果: [0-9]+ 个成功命中" | grep -oE "[0-9]+" | head -1)
  [ -z "$HITS" ] && HITS=0
  if [ "$HITS" -ge 1 ]; then
    echo "  ✅ 轮次 $i 通过: 箱子命中 $HITS"; PASS=$((PASS+1))
  else
    echo "  ❌ 轮次 $i 失败: 箱子 0 命中"; FAIL=$((FAIL+1)); FAIL_DETAILS="${FAIL_DETAILS} R${i}(0-hit)"
  fi
  [ $i -lt $ROUNDS ] && sleep 30   # 同账号重连冷却
done

echo "========== 汇总 =========="
echo "通过: $PASS/$ROUNDS  失败: $FAIL"
[ -n "$FAIL_DETAILS" ] && echo "失败详情:$FAIL_DETAILS"
[ "$FAIL" -eq 0 ] && echo "✅ 全部通过：修复稳定（非偶然）" || echo "🔴 有失败轮次需排查"

if [ -n "$CHEST_ARCHIVE" ]; then
  echo "--- 物品存档完整性 ---"
  grep -c "^-" "$CHEST_ARCHIVE" | xargs echo "箱子数:"
  grep -c "count: 5" "$CHEST_ARCHIVE" | xargs echo "count:5 记录数:"
fi
