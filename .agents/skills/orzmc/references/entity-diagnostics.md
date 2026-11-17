# 服务器侧实体统计与卡顿定位（配合 bot 使用，2026-08-04 实测）

## 为什么和 bot 相关
- bot 是常驻锚点：`execute as <bot名> at @s` 随时可统计任意位置（真人下线也能用）
- 但**纯统计不需要 bot**——`execute at <x> <y> <z>` 以坐标锚点即可，玩家在线与否无关
- bot 场景真正需要的是**玩家身份命令**（/home 等），统计只是附带能力

## 首选：`/paper entity list`（一行命令，双计数）
```
/paper entity list * minecraft:overworld
# 输出: Total Ticking: 705, Total Non-Ticking: 7500
#   103 (583) : minecraft:zombie   ← 103 激活(Ticking) + 583 休眠(Non-Ticking) = 686
```
- 语法：`/paper entity list [filter] [world]`；filter=`*` 全类型，world 用**命名空间 key**（`minecraft:overworld`，不是 `world`；`world` 会报 Could not load world）
- **休眠实体（Non-Ticking）才是大头**：`/mem` 只统计激活实体（4,210 vs 实际 8,205，严重低估）；paper entity list 双计数才是全貌
- 服务器在线 0 人时也可执行（全服统计不依赖玩家）

## 次选：Spark JSON 自带实体构成（零额外成本）
任何 `/spark profiler` 报告加 `?raw` 的 JSON 里就有：
```json
metadata.platformStatistics.world.totalEntities  // 全服实体总数
metadata.platformStatistics.world.entityCounts   // 按类型精确计数(83+ 类型)
```
无需计分板逐条刷，一次采样顺带拿到。

## 计分板逐条统计的坑（本会话实测踩遍，勿重走）
- ❌ **`type=A,type=B` 多值 OR 在 1.20.5+ 失效**——同一 key 重复，选择器静默返回空！必须**一个类型一条命令**
- ❌ **`distance=..N` 是 3D 球形距离**——玩家在高空(y=122)时下方地面实体不计入，统计严重失真
- ✅ **用水平框全高**：`@e[x=X,y=0,z=Z,dx=D,dy=320,dz=D]`（必须带 y/dy！只带 dx/dz 默认 y=0 单层，结果≈0）
- ⚠️ 计分板 objective 每次服务器重启后需重新 `scoreboard objectives add`（否则 Unknown objective）
- ⚠️ 统计期间玩家下线 → 结果全 0；先确认目标玩家在线再统计

## FPS vs TPS（定位卡顿先分清概念）
- **FPS = 客户端显卡渲染**，服务端拿不到渲染实体数/渲染距离（F3 面板是客户端功能）
- **TPS = 服务端处理速度**，服务端实体多影响 TPS、不影响 FPS
- 服务端 TPS 20 满帧 + MSPT <50ms = 服务端健康；玩家 FPS 低 → 客户端问题（装 Sodium/Lithium、降渲染距离）
- 服务端能间接帮的：清视野内实体（装饰类除外）、调低 spawn-limits

## 清理建议分级（按安全性）
| 方案 | 命令 | 安全性 |
|:--|:--|:--|
| 只清掉落物 | `/kill @e[type=item]` | 🟢 100% 安全 |
| 按类型清怪 | `/kill @e[type=zombie,type=skeleton,...]` | 🟢 安全 |
| 排除装饰类 | `/kill @e[type=!player,type=!painting,type=!item_frame,type=!armor_stand,type=!villager,type=!minecart,type=!boat]` | 🟡 较安全 |
| 限生成（治本）| paper 配置 spawn-limits 调低 | 🟢 需重启 |

⚠️ **裸 `/kill @e[type=!player]` 会清掉画/展示框/盔甲架/村民/动物——不可恢复，禁止盲用**；实体被 kill 永久删除，无撤销。
