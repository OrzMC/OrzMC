# OrzMC 实体传送可配置化 + TNT 通知聚合（2026-08-09）

## 实体传送策略（EntityTeleportPolicyService → config 可配置化）

**背景**：村民无法过下界传送门。根因 = `OrzTPEvent` 监听 `EntityTeleportEvent`，`EntityTeleportPolicyService.shouldCancel` 只放行 TAMEABLE/Enderman/ArmorStand/Shulker，其余实体全取消（日志 `[OrzMC] 实体传送被禁用:<实体名>`）。

**事件继承关键**：Bukkit 的 `EntityPortalEvent extends EntityTeleportEvent`（实体过传送门被拦）；而 `PlayerPortalEvent extends PlayerTeleportEvent`（**不是** EntityTeleportEvent 子类）→ 玩家不受影响。所以「玩家能过、村民不能」= 实体传送被插件禁，玩家事件独立。

**用户拍板方案（PR #164）**：新增配置（config.yml）：
```yaml
entity_teleport_enabled: false   # 默认不禁止 = 所有实体可传送（兼容原版村民过门）
entity_teleport_whitelist:
  - TAMEABLE
  - ENDERMAN
  - ARMOR_STAND
  - SHULKER
```
- 白名单项：大写 EntityType 名（如 `VILLAGER`）或特殊键 TAMEABLE（接口映射）
- `MainConfig` record 新增两字段 + `from()` 读取（空白名单 fallback 默认四类）
- `FeatureModule` 装配：`new OrzTPEvent(plugin, server, new EntityTeleportPolicyService(mainConfig.entityTeleportEnabled(), mainConfig.entityTeleportWhitelist()))`；FeatureModule 构造器加 `mainConfig = MainConfig.from(platform.configService().getConfig("config"))`
- 无参构造 `EntityTeleportPolicyService()` 保留旧行为（enabled=true + 旧四类）——测试兼容

**传送门测试踩坑**：
- **原版下界传送门最小内尺寸 2×3**（2 宽 3 高），`fill` 建 2×2 门面=无效传送门（村民站里面不传）——测试必须先确认门结构有效（玩家能过才算）
- **NoAI 实体不触发传送门传送**（Paper/原版：NoAI 实体不做传送检查）——测村民传送必须用普通村民（无 NoAI），NoAI 村民站传送门内 10s 也不传
- **orzdebug $e 的 `data get entity @e[...]` 带选择器/CustomName 引号必炸**（CommandException——orzdebug 拆引号/逗号；`kill @e[type=villager]` 简单选择器可用但 data get 不行）——验证实体位置用 **mineflayer 实体扫描**：bot tp 到目标点，遍历 `bot.entities` 按 `e.name` 含 villager 计数/打印坐标
- 验证维度切换：`bot.game.dimension`（mineflayer）

## TNT 通知聚合改造（aggregateNotify 纯聚合）

**用户报告**：3 TNT 同时点燃 → 4 条消息（点燃×1 + 点燃×3 + 爆炸×1 + 爆炸×3）「防刷屏无效」。

**根因**：原设计 = 批次**首事件立即发** + 窗口尾部（`notifyAggregateMs` 默认 1000ms）**补发 ×N 汇总**——每个类型两条，视觉刷屏。节流实际生效（计数到了 ×3），是「立即+汇总」双条设计。

**用户选方案 A（纯聚合，PR 中）**：事件**不立即发送**，窗口结束 flushTail **只发 1 条**：
```java
// aggregateNotify：去掉 notifyAggregated 立即发送，只入表 + 调度 flushTail
// flushTail：count<=1 也发（不带 ×），count>1 发 " ×N"（不再 return 跳过单发）
String suffix = alert.count > 1 ? " ×" + alert.count : "";
notifyAggregated(alert.epicenter, alert.message + suffix, ...);
```
- 单发事件 = 尾部发不带次数的单条（仅延迟一个窗口）
- 更新 11 个单测：`verify(notifier, never())`（事件后）+ runTail 后断言；多区域/多类型独立测试只断言 `never()` + `runLater times(N)`（runTail helper 只适配恰好调度一次的场景）

## tnt.enable 语义（反直觉，易踩坑）

```yaml
tnt:
  enable: false   # = TNT 禁用：非白名单区域 放置/点燃/爆炸 全取消
  enable: true    # = 允许 TNT（爆炸随便）
```
- **`enable: false` 才是拦截**（`if (!policy.isEnableTnt() && policy.isNotInWhiteList(loc)) setCancelled(true)`），用户测爆炸功能要临时改 `true`，测完恢复 `false`
- 临时改配置**无需重启**：`/config reload <name>`（OrzConfigCommand，`config reload tnt`）——bot 走 `$e config reload tnt` 热重载

## 验收要点
- 本地验证村民传送：标准 4×5 门（内 2×3）+ 普通村民 → 8s 内传送（位置离开传送门），日志无「实体传送被禁用」
- 测完清理测试产物：`kill @e[type=villager]` + `fill ... air` 拆门（用户规范：测试遗留必须清理）
