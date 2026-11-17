# DeathChest 回归测试（死亡瞬间下线 → 物品丢失）✅ 已修复

> **fix3（2026-08-12 MCSM 卡服事件）**：DeathChest 方块破坏动画 `sendBlockDamage` progress 越界 → 每秒刷屏抛异常 → 拖垮服务器 → 玩家集体超时掉线（"卡出服"）。**已本地复现（旧版 266 异常）并验证修复（0 异常）**，详见文末「fix3 动画 bug」。

> **背景**：DeathChest 3.0.1 存在「玩家死亡瞬间下线 → 掉落物清空但箱子未创建 → 物品永久丢失」的 bug。
> 2026-08-05 在测试服实测复现、定位根因并**已修复**（自编译版 v3.0.1-fix1）。
> 脚本：`scripts/regression/`（bugtest-death3.js / bugtest-check3.js / bugtest-fall.js / bugtest-precise.js / bugtest-data.js）
> 修复代码：`~/death-chest/`（fork devcyntrix/death-chest）

## 根因（源码级定位，2026-08-05）

DeathChest 建箱是**分步异步**流程：

```
onDeath (PlayerDeathEvent)
  → createChest() 模型创建（内存）✅
  → listener.onCreate(model)
    → new BukkitRunnable().runTask(plugin)  ← 箱子方块【延迟到下一 tick】！
  → event.getDrops().clear()  ← 掉落物【同步立即清空】
```

**致命点**：`BlockCreationChestListener.onCreate` 用 `runTask` 把 `location.getBlock().setType(CHEST)` 延迟到**下一 tick**（作者注释：防下界睡觉爆炸破坏箱子）。**玩家死亡瞬间下线 → 下一 tick 时区块已卸载 → setType 写入无效区块被静默丢弃 → 但掉落物已在死亡事件同步清空 → 物品永久丢失**。

### 实测证据
| 场景 | 掉落物 | 箱子 | 结果 |
|:--|:--|:--|:--|
| 保持在线死亡 | 清空 | ✅ ~1 tick 后建成 | 正常 |
| **死亡 + 立即下线** | 清空 | ❌ setType 写入已卸载区块 | **物品丢失** 🔴 |

- debug 日志：`Creating death chest block...` 出现但 `Death chest block created at...` 位置查无箱子（原版无此确认日志，修复版新增）
- 滞留现象：重启时 `[null] Creating death chest block...` —— 死亡事件的滞留建箱任务重启补建

## ✅ 修复方案（自编译 v3.0.1-fix1）

**文件**：`src/main/java/com/github/devcyntrix/deathchest/feature/chest/views/BlockCreationChestListener.java`

**改动**：`onCreate` 的 runnable 内，`setType(CHEST)` 前**检查区块是否加载**：
- 未加载 → `world.getChunkAt(chunkX, chunkZ)` 同步强制加载
- 仍未加载 → `runTaskTimer` 每 tick 重试，最多 40 tick（2s）
- 加载后 → `placeChest()` 放箱子 + 打印确认日志

**编译**：`cd ~/death-chest && ./gradlew shadowJar --no-daemon`（需 JDK 25，build.gradle toolchain 已改 25；产物 `build/libs/deathchest.jar`）

## 测试流程（回归）

### 前置
- 测试服运行中（本地 papermc 测试目录）
- 玩家账号（HermesBot）已注册，密码用环境变量注入：`BOT_PASSWORD=xxx node <脚本>`
- DeathChest debug 保持开启（`plugins/DeathChest/config.yml` → `debug: true`）便于定位

### 脚本分工
| 脚本 | 场景 | 预期（正常）| 预期（bug）|
|:--|:--|:--|:--|
| `bugtest-fall.js` | 坠落死亡 + **保持在线** + 查箱子 | ✅ 收到通知 + 箱子命中 ≥1 | ❌ 命中 0 |
| `bugtest-precise.js` | kill + **2s 内下线** + 记坐标 | ✅ 死亡坐标写入 /tmp/death_pos.json | — |
| `bugtest-check3.js` | 读坐标 → 3x3x3 查箱子（/execute if block）| ✅ 命中 ≥1 | ❌ 命中 0 |
| `bugtest-data.js` | 读箱子 NBT/存档确认物品 | ✅ Items 含 diamond x5 | ❌ 空 |

### 执行步骤
```bash
cd ~/minecraft-bot   # 或技能 scripts/regression/

# 1. 对照组：保持在线死亡（基本功能）
BOT_PASSWORD=xxx node bugtest-fall.js

# 2. 复现组：死亡瞬间下线
BOT_PASSWORD=xxx node bugtest-precise.js
# 期望：输出"死亡坐标已存"，服务器日志 [HermesBot: Killed HermesBot]

# 3. 查箱子（等 2-3s 让建箱完成）
BOT_PASSWORD=xxx node bugtest-check3.js
# bug 判定：命中 0 → 🔴（旧版）
# 修复判定：命中 ≥1（Test passed）→ 🟢 回归通过

# 4. 物品完整性：查存档（或 bugtest-data.js）
grep -A 5 "diamond" <服务器>/world/dimensions/minecraft/overworld/death-chests.yml
# 期望：count: 5（无丢失）
```

### 判定标准
- **回归通过**：步骤 3 箱子命中 ≥1 + 步骤 4 物品 count 完整（死亡+下线也不丢物品）
- **回归失败**：命中 0 且日志有 `Creating death chest block...` 无 `created at` 确认

## 多轮回归实测记录（2026-08-05，修复版 v3.0.1-fix1）

自动化循环：`regression-loop.sh`（每轮 death3/precise + check3，轮间 30s 冷却防同账号重连拦截）

| 批次 | 轮次 | 场景 | 结果 |
|:--|:--|:--|:--|
| 1 | 1-4 | 死亡+2s 下线 | ✅ 4/4 通过（命中 1/1/1/1）|
| 2 | 5-8 | 死亡+2s 下线 | ✅ 4/4 通过（命中 2/2/2/2）|
| — | — | **累计 8/8 = 100%** | ✅ 物品 0 丢失 |

存档校验（world/dimensions/minecraft/overworld/death-chests.yml）：
- 12 个箱子条目全部含 diamond（count 5 或 10），**空箱 0**
- 修复前该场景 100% 失败（0 命中 + 物品丢失），修复后 100% 通过 → **非偶然**

> ⚠️ fall.js（保持在线对照）命中 0 是**脚本查错坐标**（记录坠落起点而非死亡落地位置）——用服务器日志 `Death chest block created at` 确认实际建箱位置即可，不影响判定。

## 阶段 4 完整回归记录（2026-08-05，修复版 v3.0.1-fix1）

| 回归项 | 结果 | 说明 |
|:--|:--|:--|
| TPS | ✅ 20.0/20.0/20.0 | 满 TPS 无退化 |
| 插件加载 | ✅ 18 全加载 | Bukkit 17 + Paper 1（含 floodgate）|
| 启动错误 | ⚠️ 2 条已知 | Essentials 版本警告 / EzShops YAML 回退（原版就有）|
| 死亡+下线建箱 | ✅ 8/8 (100%) | 核心修复场景 |
| 物品完整性 | ✅ 0 丢失 | 存档全有物品 |
| 过期机制 | ✅ 60s 测试通过 | 到期自动销毁+存档延迟写盘（关服时 saveChests）|
| 远距离建箱 | ✅ (100,61,100) | 区块加载修复覆盖 |
| 重启滞留补建 | ✅ 正常 | 过期滞留箱补建后清理 |

## 压力测试记录（2026-08-05，fix2 = 区块加载 + destroyChest 幂等双修复）

| 场景 | 数据 | 结果 |
|:--|:--|:--|
| 密集死亡+下线 | 6 轮（10:30-10:37）| ✅ 6/6 通过（命中 2/1/2/2/1/2）|
| 并发死亡+下线 | 2 bot 同时 | ✅ HermesBot 3 命中；TestPlayer kill 未生效（命令时序）非修复问题 |
| 累计回归 | 8（早前）+ 6 = **14 轮** | ✅ **14/14 = 100%** |
| TPS（压力后）| 20.0/20.0/19.9 | ✅ 满 |
| 异常（压力后）| Invalid model / exception | ✅ 0 |
| JVM 内存 | 2.55GB RSS | ✅ 稳定无泄漏 |
| 日志新增错误 | — | ✅ 无（仅已知 EasyBot/Essentials/EzShops）|

**并发测试注意**：新账号会被白名单拦（EasyBot whitelist）——并发测试须用已有白名单账号（HermesBot/joker/TestPlayer，`/whitelist list` 可查）；kill 命令偶发未生效（区块加载时序）→ 判定以服务器日志 `Killed` + `created at` 为准

**已知问题（已修复）**：
1. ~~**Invalid model 启动竞态**~~ ✅ 已修复（commit 3572396，已入 PR #101）：
   - **复现条件**：服务器有已过期滞留箱子（expireAt 已过）+ 重启 → 必现 1 条 `IllegalArgumentException: Invalid model`
   - **根因**：启动 loadChests 先 `listener.onLoad(model)`（调度 ExpirationRunnable 到下一 tick）后 `loadedChests.put()`；ExpirationRunnable 抢先执行 → destroyChest 里 `loadedChests.remove()` 返回 null → 抛异常
   - **修复**：`DeathChestService.destroyChest` 中 remove 返回 null 时静默返回（销毁幂等），不再抛异常
   - **验证**：同条件（11 过期箱重启）修复前 1 次异常 → 修复后连续 2 次 0 异常，过期清理功能正常
2. **mineflayer 开箱失败**：DeathChest 用自定义 inventory holder（非方块原生 NBT），mineflayer openContainer 等不到 windowOpen——**真人客户端正常**，验证物品用存档（death-chests.yml）而非开箱

**测试辅助**：`regress-tps.js`（TPS/插件查询）、`regress-expire.js`（精确坐标查箱）、`bugtest-world.js`（跨世界死亡）、`regression-loop.sh`（自动化多轮）

## 坑（实测踩过）

## fix3 动画 bug（2026-08-12 MCSM 卡服事件）✅ 已修复

**现象**：MCSM 服 20:45 起 `[DeathChest] java.lang.reflect.InvocationTargetException` + `Caused by: IllegalArgumentException: progress must be between 0.0 and 1.0` **每秒刷屏** → 异步线程池/日志 IO 洪水 → TPS 崩（7-8）→ 玩家超时掉线 → 重连被 LoginSecurity「此用户已经在线」拒绝 → **集体卡出服**。

**根因（源码 + 复现实证）**：
- `BreakAnimationRunnable.run()`：`process = (now - createdAt)/(expireAt - createdAt)` → `state = (int)(9 * process)` → `PaperBreakAnimation` → `sendBlockDamage(progress = state/9f)`（**progress 要求 0.0-1.0，Guava 硬校验**）
- **process 非法时必抛**：① `expireAt < createdAt`（数据异常/-1 永不过期 + 远古 createdAt）→ process 大幅负 → state 负 → progress 负；② **过期后销毁滞后** → process > 1.111 → state ≥ 10 → progress > 1
- **MCSM 触发链**：`ExpirationChestListener` 用 `runTaskLater((untilDeletion/1000)*20)` **按 tick 调度销毁**——TPS 7-8 时 600s 的销毁任务实际 ~1600s 才执行；**动画任务（`runTaskTimerAsynchronously` 异步、真实时间每秒跑）在箱子过期后继续跑** → process 增长超 1.111 → 每秒抛；活动期玩家频繁死亡箱子多 → 异常洪水
- **动画只发给附近 20 格玩家**（`getNearbyEntities(..., 20,20,20, PLAYER)`）——没人旁观不抛（本地早期复现失败原因之一）

**修复（v3.0.1-fix3，源码 `~/OrzMC/tools/DeathChest/`）**：
1. `PaperBreakAnimation.spawnBlockBreakAnimation`：`state = Math.max(0, Math.min(9, state))` + `progress = Math.max(0f, Math.min(1f, finalState / 9f))`（防御任何非法输入）
2. `BreakAnimationRunnable.run()`：`process = Math.min(1.0, Math.max(0.0, ...))`（源头钳制）
- 构建：`./gradlew shadowJar --no-daemon`（JDK 25）→ `build/libs/deathchest.jar`（269100 字节，旧版 268951）

**本地复现方法（确定性）**：
1. `write_file` 手写 `death-chests.yml`（**必须用 write_file/文本原样，PyYAML safe_dump 会破坏 `==: org.bukkit.Location` 类型标记导致反序列化失败！**）造 `createdAt: 1000`（1970）+ `expireAt: -1` 的箱子 @ 出生点附近
2. `/deathchest reload` 热加载（onLoad→onCreate 启动动画任务，expireAt=-1 不调度销毁→永续）
3. **bot 必须 tp 站箱子 20 格内**（否则 getNearbyEntities 空不抛）——HermesBot 登录后 `/minecraft:tp HermesBot 21 64 -470`
4. 数日志 `progress must`：**旧版 266 条/秒刷，修复版 0 条**

**本地测试服坑（2026-08-12 实测）**：
- ⚠️ **本地玩家对所有伤害类型免疫**（`/damage` 全类型报 `Target is invulnerable`；原版 kill 只回显 Killed 无 died；Essentials /kill 偶发 died 玄学）→ **死亡建箱复现基本不可用**，用手写箱子
- ⚠️ `/damage` 对玩家无效可能是原版限制（对非玩家实体也需选择器）
- ⚠️ 加载箱子 `getWorld()` 可能 null（world_key 反序列化）→ 动画任务 cancel——手写格式必须与真实存档一致
- ✅ `/deathchest reload` 热重载有效（不必重启）；debug 日志在 config `debug: true`
- ✅ 恢复现场：config expiration 600 / debug false / death-chests.yml 清空

## 坑（实测踩过）
- **粒子崩溃**：26.2→1.21.11 边界，坠亡掉落粒子触发 `PartialReadError: f32` —— 脚本需内置粒子 patch（115/116 映射）或 `hideErrors: true` 绕过
- **OP 默认创造模式**：创造模式死亡不掉落物品/不触发 DeathChest —— 必须先 `/minecraft:gamemode survival`
- **kill 命令**：`/minecraft:kill` 有效（日志 `Killed`），但触发不了 `death` 事件（mineflayer）——死亡检测用 health < 0.5 或 kill+计时断线
- **spawn 事件重复触发**：kill/坠落后 respawn 会再触发 spawn handler → 脚本需 `started` 标志防重入
- **/execute if block 回显**：结果发给执行者 chat（非控制台日志）→ 检查脚本需监听 message 收集；**中文服回显是 "Test passed"/"Test failed"**（非英文服 "Successfully"）——check3 已适配
- **登录检测**：message 事件可能在 spawn 前错过 → spawn 触发即可认为已登录，勿依赖 message
- **kill 后立即下线会丢命令**：kill 后需等 ≥2s 再 quit，否则命令可能未送达（tp 到未加载区块时尤其明显）
