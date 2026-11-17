# 世界高度调整（world-height）

> 2026-08-15 本地测试服实测通过（paper-26.2-111 + CustomWorldHeight 2.2.0）
> 触发：需要扩大/限制 Minecraft 世界垂直高度（如建筑上限 319 不够用）

## 背景认知（关键）

- **1.18 起高度是「世界属性」不是「服务器属性」**：`server.properties` 的 `max-build-height` 已被删除（1.18+ 写了也不生效，网上旧教程全是这个坑）
- `paper-world-defaults.yml` 的 `anti-xray.max-block-height` 只是防透视扫描高度，与可建高度无关
- 高度存在 level.dat 的 `WorldGenSettings`（维度生成设置）里，由 `min_y` + `height` 决定

## 硬限制（原版引擎天花板，26.x 一致）

| 参数 | 限制 |
|:--|:--|
| `min_y` | ≥ **-2032** |
| `height` | ≤ **4064**，必须 16 的倍数 |
| `min_y + height` | ≤ **2032** |
| 默认 | min_y=-64, height=384（-64 ~ 319） |

## 三条方案对比（2026-08-15 结论）

| 方案 | 已有世界 | 新世界 | 原生? | 难度 | 说明 |
|:--|:--:|:--:|:--:|:--:|:--|
| **CustomWorldHeight 插件** ⭐ | ✅ | ✅ | 插件 | 低 | yaml 配置重启生效；**扩高度安全，缩高度丢数据** |
| level.dat NBT 编辑 | ✅ | ✅ | ✅ 纯原版 | 高 | NBTExplorer 改 WorldGenSettings→overworld→settings→min_y/height；停机+易手抖 |
| 数据包 | ⚠️有限 | ✅ | ✅ 纯原版 | 中 | 已有世界读 level.dat 固化副本，数据包对老世界效果有限 |

## CustomWorldHeight 实操（已验证流程）

**插件信息**：v2.2.0（2026-07-28），api-version 1.20，`load: STARTUP`，jar 名 `CustomWorldHeight-2.2.0+1.20.5-26.2.jar`（官方支持 26.2），GitHub `Lumine1909/CustomWorldHeight`

**安装**（新插件首次装，jar 直接放 plugins/）：
```bash
cp CustomWorldHeight.jar /Users/Shared/orzmc/mcsmanager/daemon/data/InstanceData/716c2fb712154c36ba5ab0f1480d3f87/plugins/
# 启动一次 → 插件生成 config 模板后日志提示「first time... restart after finish your config」
# （插件已移除 2026-08-18；上行为历史实验步骤，路径已按 MCSM 实例化）
```

**配置** `plugins/CustomWorldHeight/config.yml`：
```yaml
main-world:
  world: 'world'           # 世界名（多世界按名匹配）
  min-y: -64               # 世界最低点
  height: 1088             # 总高度 → max Y = min-y+height-1 = 1023
  logical-height: 1024     # 紫颂果传送等逻辑高度（≤ height）
  cloud-height: 'default'  # 云层（1.21.6+，空=无云，default=默认）
  dimension-type: 'overworld'  # overworld/the_nether/the_end/overworld_cave/custom
```

**生效**：改完重启服务器。启动日志 `Loaded config: value=world, regex=\b\B, height=1088, minY=-64, ...`

**验证**（RCON setblock 边界测试，实测可靠）：
```bash
# 高度内应成功
rcon.py "execute in minecraft:overworld run setblock 0 1000 0 minecraft:stone" 25575 <pw>
# → Changed the block at 0, 1000, 0
# 高度外应拒绝
rcon.py "execute in minecraft:overworld run setblock 0 1024 0 minecraft:stone" 25575 <pw>
# → That position is out of this world!
# 测完清理：setblock 0 1000 0 minecraft:air
```

## 实测信号（2026-08-15 本地）

- 启动日志出现 `Ignoring heightmap data for chunk [...], size does not match; expected: 52, got: 37` —— **高度图段数变化（37→52）正是高度生效的直接证据**（384/16+1=25? 1088/16+4=72 段换算，有出入但 size 变化即高度变了）
- 边界全对：y=1024 拒绝、y=-65 拒绝、y=-64 接受、y=1000 接受
- 高度 1088 下 RCON setblock 正常，无 TPS 异常（本地 i5 测试机 2G）

## Pitfalls

- ⚠️ **只扩不缩**：缩小 height / 降低 min-y 会丢数据（插件 README 红字警告）；老区块地形不重生成，上方虚空可正常建造，新区块才用新高度
- ⚠️ 先本地测试服验证 → Exaroton → MCSM（玩家全下线）三端节奏
- ⚠️ 高度变大 → 光照/渲染计算量上升，低配机留意 TPS（spark 分析）
- ⚠️ 测试方块记得清（setblock air），保持测试服干净
