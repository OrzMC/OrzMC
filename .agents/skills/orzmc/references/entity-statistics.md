# 快速实体统计（替代计分板逐条刷）

> 2026-08-04 沉淀：定位「joker 周边实体构成 / 全服实体负载」的三种方法，按速度排序。

## 方法 1：`/paper entity list`（最快，一行命令）

```
/paper entity list * minecraft:overworld
# 输出: Total Ticking: 705, Total Non-Ticking: 7500
#        103 (583) : minecraft:zombie   ← 103 激活 + 583 休眠 = 686
# 语法: /paper entity list [filter] [world]；world 用 minecraft:overworld（不是 world）
```

- **Ticking（激活）** 吃服务端 CPU；**Non-Ticking（休眠）** 基本不吃服务器，但**客户端视野内仍渲染**——FPS 排查两者都要看
- 无参数会打印用法帮助
- ⚠️ filter 传 `*` 且 world 传 `world` 会报 `Could not load world`——world 必须是 `minecraft:overworld` 形式
- 通过 MCSM 发：`mcsm.sh command "paper entity list * minecraft:overworld"`，日志里读输出

## 方法 2：Spark JSON `world.entityCounts`（一次 profiler 顺带拿）

```
/spark profiler --timeout 30 → 链接加 ?raw → metadata.platformStatistics.world
# 结构: {totalEntities: 4812, entityCounts: {bat: 1575, glow_item_frame: 381, ...}}
# 全服 77 种类型精确计数，含 totalEntities 总数
```

- **优点**：零额外命令，profiler 报告自动含全服实体统计
- 适合全服负载评估（如「蝙蝠 1575 个是全服最大实体群」的结论）
- 详细见 `spark-analysis.md`

## 方法 3：计分板逐类型（慢，仅当需要玩家周边局部数据）

脚本：`scripts/cmp3/mcsm_entity_audit.py joker 32 x z`（水平框模式）

```bash
# 原理：scoreboard objectives add + execute as @e[...] run scoreboard players add
# 单类型一条命令（1.20.5+ 不支持逗号 OR），最后总数对照
```

### 计分板法踩坑（2026-08-04 实测）

- ⚠️ **Minecraft 1.20.5+ `type=` 参数不支持逗号多值 OR**（`type=zombie,type=skeleton` 全 0）——必须单类型一条命令
- ⚠️ `@e[x=X,z=Z,dx=D,dz=D]` 必须配 `y=`+`dy=`（不配 y 默认 y=0 单层，结果几乎为 0）
- ⚠️ `distance=..N` 是 3D 欧氏距离（球体）——高空玩家统计不到下方地面实体；水平区域用 dx/dz+y 范围
- ⚠️ **玩家不在线时统计全 0**（选择器基于玩家位置）——先确认在线
- ⚠️ **MCSM 命令长度限制**：过长命令被截断，日志出现 `<--[HERE]` 标记——命令保持短
- ⚠️ 每次统计前要 `scoreboard objectives add <name> dummy`（重启后丢失，需重建）

## 全服实体负载参考（2026-08-04 实测，空闲状态）

| 类型 | 数量 | 说明 |
|:--|:--|:--|
| 蝙蝠 bat | 1,575 | 全服最大实体群！洞穴堆积，无收益纯吃 tick |
| 发光框 glow_item_frame | 381 | 玩家建筑装饰 |
| 苦力怕/骷髅/僵尸 | 287/266/256 | 刷怪残留 |
| 村民 | 178 | 村庄 |
| 掉落物 item | 109 | 可安全清理 |
| 鸡/兔/羊/猪/牛 | 146/134/100/72/66 | 养殖 |

**清理建议**：蝙蝠 + 掉落物零风险可清（`/kill @e[type=bat]`、`/kill @e[type=item]`）；怪物按需；装饰类（画/框/盔甲架）**不可恢复**，清前必须备份 world。
