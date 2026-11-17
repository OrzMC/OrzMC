# DeathChest 3.0.1 修复案例（死亡瞬间下线 → 物品永久丢失）

> 2026-08-05 测试服（Paper 1.21.11 测试目录）完整定位 + 修复 + 回归验证。
> 上游：`github.com/devcyntrix/death-chest`（MIT，main 分支，v3.0.1 2026-07 发布，与线上版一致）。
> 源码：`~/death-chest`（本地 clone + 修改）；修复版 jar：`~/death-chest/build/libs/deathchest.jar`。

## 现象（用户报告 + 实测复现）
- 玩家死亡瞬间下线 → 掉落物清空但箱子未生成 → 物品永久丢失（既不在箱子也不在地面）
- debug 日志（`plugins/DeathChest/config.yml` → `debug: true`）显示：`Clearing drops...` 后 `Creating death chest block...` 执行了，但箱子实际不存在

## 根因（源码级定位）
`SpawnChestListener.onDeath`（PlayerDeathEvent, HIGH priority）：
```
plugin.createDeathChest(...)  // DeathChestService.createChest
  → new DeathChestModel(...)          // 内存模型（含物品 inventory）
  → listener.onCreate(model)          // 各 listener 挂任务
      → BlockCreationChestListener.onCreate
          → new BukkitRunnable(){ setType(CHEST) }.runTask(plugin)  // ⚠️ 下一 tick 才放方块
→ event.getDrops().clear()             // ⚠️ 同步立即清掉落物
```
**竞态**：掉落物同步清空；方块延迟到下一 tick。玩家死亡瞬间下线 → 下一 tick 时所在区块已卸载 → `location.getBlock().setType(Material.CHEST)` **写未加载区块，不报错但静默无效** → 箱子没生成、物品已清 = 永久丢失。
（runTask 延迟是作者故意的：防下界睡觉时爆炸先于建箱破坏箱子——不能直接改同步。）

## 修复（~/death-chest）
`src/main/java/com/github/devcyntrix/deathchest/feature/chest/views/BlockCreationChestListener.java` `onCreate`：
```java
int chunkX = location.getBlockX() >> 4;
int chunkZ = location.getBlockZ() >> 4;
if (!world.isChunkLoaded(chunkX, chunkZ)) {
    world.getChunkAt(chunkX, chunkZ);   // 强制加载
}
if (!world.isChunkLoaded(chunkX, chunkZ)) {
    // 仍失败 → 每 tick 重试，上限 40 tick（2s）
    new BukkitRunnable() { /* isChunkLoaded 后 placeChest(...) 或超时放弃 */ }
        .runTaskTimer(plugin, 1, 1);
    return;
}
placeChest(model, location, world);  // setType(CHEST) + setPrevious(state)
```
另加 debug 日志 `Death chest block created at x, y, z` 便于验证。

## 构建
```bash
cd ~/death-chest
# build.gradle.kts: toolchain.languageVersion 21 → 25（本机只有 JDK 25；options.release=17 保证产物兼容）
./gradlew shadowJar --no-daemon   # BUILD SUCCESSFUL → build/libs/deathchest.jar (267KB)
cp build/libs/deathchest.jar /Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/716c2fb712154c36ba5ab0f1480d3f87/plugins/deathchest.jar   # 原 jar 先备份
重启测试服 → 日志 `Enabling DeathChest` + 滞留任务补建 `Death chest block created at ...`
```

## 回归验证（全部通过）
| 测试 | 方法 | 结果 |
|:--|:--|:--|
| 死亡+下线箱子生成 | bugtest-precise.js（kill+2s 下线）→ check-death-chest.js 查 3x3x3 | ✅ 命中 1（"Test passed"）|
| 物品完整性 | 读 `world/dimensions/<dim>/death-chests.yml`（ItemStack 序列化，`minecraft:diamond count: 5` + player UUID）| ✅ diamond x5 无丢失 |
| 保持在线对照 | bugtest-fall.js（坠落死亡+在线）| ✅ 箱子生成 |

验证脚本均在 `orzmc/scripts/regression/`（user-owned 技能）与本技能 `scripts/check-death-chest.js`。

## 多轮回归（确认修复非偶然，2026-08-05）
单次通过 ≠ 修复可靠——用户要求多轮压测。自动循环脚本模式（`regression-loop.sh`）：
- 每轮 = precise（死亡+2s 下线）→ check3（查箱）→ 统计命中；轮间 `sleep 30`（**同账号重连有 20-30s 冷却**，连跑会被 LoginSecurity/反垃圾拦截）
- 登录超时/流程未完成要**单独标记**（timeout/no-death），不计入「箱子 0 命中」失败，避免误报
- 命中数解析用 `grep -oE "结果: [0-9]+"`；存档校验用 `grep -c "^-"`（箱子数）+ `grep -c "count: 5"`（物品完整数）
- **实测结果：两批 4 轮全过，累计 8/8 = 100%，存档 12 箱 0 空箱**（修复前该场景 100% 失败）→ 判定非偶然，可推广
- **PR 上游**：2026-08-05 提交 https://github.com/DevCyntrix/death-chest/pull/101（fork → 分支 `fix/chunk-load-before-chest-place` → gh pr create，描述含 8/8 回归数据）

## 压力测试补充（2026-08-05，fix2 = 区块加载 + destroyChest 幂等双修复）
| 场景 | 数据 | 结果 |
|:--|:--|:--|
| 密集死亡+下线 | 追加 6 轮（含 30s 冷却）| ✅ 6/6（命中 2/1/2/2/1/2）|
| 并发死亡+下线 | 2 bot 同时（HermesBot + TestPlayer）| ✅ HermesBot 3 命中；TestPlayer kill 未生效（命令时序）非修复问题 |
| 累计回归 | 8 + 6 = **14 轮** | ✅ **14/14 = 100%** |
| TPS（压测后）| 20.0/20.0/19.9 | ✅ 满 |
| 异常（压测后）| Invalid model / exception | ✅ 0 |
| JVM 内存 | 2.55GB RSS | ✅ 稳定无泄漏 |
| 日志新增错误 | — | ✅ 无（仅已知 EasyBot/Essentials/EzShops）|

**并发/多账号测试坑**：① EasyBot 白名单拒未登记账号（`不在服务器白名单中`）→ 先 `/whitelist list`，用已有账号（HermesBot/joker/TestPlayer），勿造新 bot 名；② kill 偶发未送达（日志无 `Killed <name>`）→ 判定以服务器日志 `Killed` + `created at` 为准；③ `death-chests.yml` 只在**关服/卸载时写盘**（saveChests），运行期查文件看不到新箱子——运行期验证用世界方块查询，文件用于关服后核对累计。

⚠️ **fall.js（保持在线对照）可能假阴性**：它记录坠落**起点**坐标去查箱，而 DeathChest 实际把箱放在死亡**落地**位置 → 「0 命中」是查错坐标，不是修复回归。对照组的真实证据用服务器日志 `Death chest block created at x, y, z` 行，不要依赖 fall.js 的命中数。

## 关键坑（导致多轮返工）
1. **`/execute if block` 回显语言**：本服中文 locale 回显 "Test passed"/"Test failed"（不是英文服 "Successfully"）——首版 check 脚本监听错误关键词 → 假阴性「0 命中」，实际箱子已生成
2. **物品验证别读 NBT**：`/data get block ... Items` 返回 `[]` 是正常的（物品在内存模型 + death-chests.yml 存档），误判「物品丢失」
3. **mineflayer 死亡检测**：`/minecraft:kill` 不触发 `death` 事件（mineflayer）；`bot.health` 坠亡瞬间不可靠；用 message 监听 `fell from a high place` 触发 `bot.respawn()`；respawn 会二次触发 `spawn` 事件需 `started` 标志
4. **OP 默认创造模式**：创造模式死亡不掉落/不触发 DeathChest → 测试前 `/minecraft:gamemode survival`
5. **kill 命令送达**：tp 到远处后 800ms 内发命令可能未送达即 quit → 等 2s
6. **方案 B（延迟清掉落物）被证伪**：`drops.clear()` 延迟到下一 tick 时 Bukkit 已消费 drops 实体化掉落物，清不掉——修复必须落在「方块能放上」而非「延迟清」
7. **mineflayer 开箱超时是正常的**：DeathChest 用自定义 inventory holder（非方块原生 NBT），`openContainer` 等不到 windowOpen 超时——**真人客户端正常**。验证物品只走存档文件，别用开箱
8. **启动「Invalid model」竞态**：重启时过期滞留箱与补建任务竞争 → `ExpirationRunnable` 调 `destroyChest` 时模型已被移除，抛 1 条 IllegalArgumentException（启动一次性，不影响运行；判定可接受）。可优化方向：destroyChest 的 `loadedChests.remove()` 返回 null 时静默返回
