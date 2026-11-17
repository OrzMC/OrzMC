# 实体/传送门行为（entity-portal）

> 合并自：minecraft-entity-portal-behavior（2026-08-10 阶段二整合）
> 触发：实体（村民/动物）无法通过下界传送门而玩家正常；「实体传送被禁用」日志；设计「禁止实体传送 + 白名单豁免」配置。

## 关键机制：Bukkit 事件继承（判断拦截来源的核心）

| 事件 | 继承关系 | 谁触发 |
|:--|:--|:--|
| `EntityPortalEvent` | extends **EntityTeleportEvent** | 实体（村民/动物/怪物）过传送门 |
| `PlayerPortalEvent` | extends **PlayerTeleportEvent**（**不是** EntityTeleportEvent 子类） | 玩家过传送门 |

**推论**：监听 `EntityTeleportEvent` 的插件拦截所有实体传送门事件（含村民），**不影响玩家**。
→ 「玩家正常 + 村民被拦」= 有插件在 EntityTeleportEvent 层 setCancelled(true)。排查 grep 插件代码的 `EntityTeleportEvent`（不是 EntityPortalEvent——多数插件监听父类）。

## 原版规则（测试防坑）

1. **下界传送门最小内尺寸 2×3**（宽 2 高 3）——**2×2 无效**（fill 建测试门极易建错）
2. **NoAI 实体不触发传送**（`NoAI:1b` 村民站门内 10 秒也不传——不代表插件问题）；验证必须用普通村民（有 AI）
3. 实体需在传送门方块内持续停留（约 80 tick）才触发
4. ⚠️ **Folia 26.2 下 `PlayerPortalEvent` 不触发**（portalAsync 新路径绕过 Bukkit 事件，反编译实证 `callPlayerPortalEvent` 无调用者）——玩家跨服 transfer 依赖该事件会静默失效；OrzMC 已用 PlayerMoveEvent 补偿（PR #195）。几何关键：地面传送门内部格在**脚底+1 起**（`cy=baseY+2`），玩家身体两格匹配（脚底+躯干），水平精确命中防路过误触发。详见 `folia-experiment.md`「传送门 transfer 补偿方案」小节

## 插件策略设计参考（OrzMC 2026-08 落地）

- 默认不禁止：`entity_teleport_enabled: false`（所有实体可传送，兼容原版）
- 开启时白名单豁免：`entity_teleport_whitelist` 列表——大写 EntityType 名（`VILLAGER`）或特殊接口键（`TAMEABLE`/`ENDERMAN`/`ARMOR_STAND`/`SHULKER`）

## 排查步骤

1. 确认玩家过传送门正常（排除结构问题）
2. 查日志「实体传送被禁用」→ 定位取消事件的插件
3. grep 插件代码 `EntityTeleportEvent` 监听器 + 策略类
4. 本地复现：`scripts/villager_portal_test.js`（自动建标准门 + 召唤村民 + 验证）

## 验证工具限制（重要坑）

- **orzdebug `$e` 会拆坏引号与 @e 选择器逗号**：`CustomName="..."`、`@e[type=villager,limit=3]` 报 CommandException——`kill @e[type=villager]` 这类单条件可以，复杂选择器/引号不行
- **验证实体位置不要用 `data get entity` 命令**——用 mineflayer `bot.entities` 扫描（按 `e.name`/`e.kind` 过滤，打印坐标）；村民从传送门位置消失 = 传送成功
- 村民可能被传送到远处（下界生成新门/偏移）——只看「是否离开传送门位置」即可

## 支持文件

- `scripts/villager_portal_test.js`：本地一键复现（建 4×5 门 + 村民 + mineflayer 验证）
- `references/orzmc-entity-teleport-tnt.md`：实体传送可配置化 + TNT 通知纯聚合案例（从 paper-plugin-development 迁入）
- 跨服传送门 transfer 机制见 `references/testing.md`
