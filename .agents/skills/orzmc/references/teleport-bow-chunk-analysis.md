# 传送弓「未加载区块无法传送」根因分析（2026-08-08 实测定案）

> 场景：OrzMC 传送弓 `/tpb`（射箭 → 箭落地 ProjectileHitEvent → 传送）。玩家报告：射向未加载区块无法传送，跑到目标区块（触发加载）后才能传送。

## 根因（已复现证实）

- **依赖链**：射箭 → 箭实体飞行 → 落地触发 `ProjectileHitEvent` → `TeleportBowService.handleArrowHit` → 传送
- **失败点**：箭落点超出 **view-distance（区块加载半径）** → 目标区块未加载 → **箭实体被卸载/移除 → hit 事件永不触发** → 无任何回显（既无「传送完成」也无「目标位置不可站立」）
- **不是 simulation-distance**：实测 simulation-distance=3（48 格模拟区）时 60 格落点的箭仍正常 hit——Paper 对弹射物模拟区外行为与直觉不同，**区块加载半径才是硬边界**
- **MCSM 场景吻合**：MCSM `view-distance=6`（96 格）< 箭最大射程 ~120 格 → 玩家射向加载区外（仰射/站在加载边缘）→ 失败；跑近后玩家位置重新加载区块 → 成功

## 复现配方（本地测试服，2026-08-08 实测）

```
1. server.properties: view-distance=3（48 格）→ 重启（改完记得恢复原值 view-distance=8）
2. bot 进服（HermesBot/{BOT_PASSWORD}，本地已知密码账号）
3. /login → /tpb → 验证 bot.heldItem.name === 'bow'
4. bot.look(yaw, 0, true) 等 600ms → activateItem() → 等 2s → deactivateItem()（满蓄力射出）
5. 对照：射 60 格目标（平射实际落点 ~45 格 < 48）→ message 收到插件回显 = hit ✅
6. 复现：射 110 格目标（平射实际落点 ~80 格 > 48）→ **无任何 message = 无 hit** ✅
```

- 判定：**有/无 hit 消息**（如「[传送弓] 箭射进了水里!」）；「传送弓」前缀出现在所有消息里，**不能用 t.includes('传送') 判定传送成功**，要用 `bot.entity.position.distanceTo(射前) > 3`
- ⚠️ 平射落点远小于瞄准距离（重力）：瞄准 110 格实际 ~60-80 格；想射更远用仰射 pitch -35~-45°，但出生点附近树/建筑会截住箭（落点就近 hit）——**临时调小 view-distance 是最干净的复现方式**

## 修复选项（未实施，待用户确认）

| 方案 | 做法 | 评价 |
|:--|:--|:--|
| A（推荐） | 射箭瞬间**异步预加载飞行路径区块**（Paper `getChunkAtAsync`，3-6 个 chunk）——箭飞抵时区块已加载 → hit 正常触发 | 保持「箭落地传送」玩法，根治 |
| B | 发射即传（射线落点直接传送，不依赖箭落地） | 绕开问题但改变玩法（无飞行延迟） |
| C | 线上 view-distance 6→8（96→128 格，覆盖箭射程 120） | 治标 + 玩家视野/性能开销 |

## 相关代码位置

- `TeleportBowService.handleArrowHit`（hit 处理：水/岩浆/跨世界/高度/可站立检查 → teleport）
- `TeleportBowEventService.handleProjectileHit`（ProjectileHitEvent 入口）
- `FeatureModule` ~276 行注册 `/tpbow`（别名 `/tpb`）→ `giveAndEquip`

## 测试遗留

- 本地测试服 `server.properties` 已在测试后恢复 `view-distance=8 / simulation-distance=6`（原值）
- bot 射箭链路验证通过（activateItem+deactivateItem 蓄力释放；详见 SKILL.md「射箭/弹射物测试」节）
