# 命令方块全量梳理（世界扫描）

## 使用时机
- 需要盘点某个 Minecraft 世界（存档）里**所有命令方块**：数量、坐标、类型、完整指令、触发方式。
- Paper → Folia 迁移前，评估命令方块及其指令是否受 Folia 禁用/不支持指令影响。
- 迁移/恢复后核对命令方块是否完整、是否有损坏残留（超大坐标异常点）、是否有 `/op` 提权后门等风险。

## 工具对比（scripts/ 下两套，按需选用）

| 工具 | 输出 | 特点 |
|---|---|---|
| `scan_cmdblocks.py` | **JSON**（原始方块列表，含 id/x/y/z/Command/auto/region 等） | 底层扫描器；多进程；支持旧版(≤1.17 `Level`/`TileEntities`)与新版区块格式；输出每个 region 的原始命令方块 |
| `analyze_cmdblocks.py` | 控制台统计 | 吃 `scan_cmdblocks.py` 的 JSON；分类指令/类型/触发方式；**交叉核对 `DISABLED_CMDS`（Folia 禁用指令集）** |
| `mc_cb_scan.py` | **CSV + 自动 Markdown 报告** | 一体化：扫描→CSV→自动生成统计/空间集群/指令分类/异常风险/迁移要点的 Markdown 报告；自带禁用指令交叉核对 |

> 三件套均**纯标准库，零第三方依赖**。若只需原始数据或做一次性统计，用前两个；若要"全量梳理成文档"，用 `mc_cb_scan.py`。

## 使用（mc_cb_scan.py）

```bash
# 一步：扫描 + CSV + 报告
python scripts/mc_cb_scan.py run --world <世界目录> --out-dir ./out

# 分两步（复用旧 CSV 只重新出报告）
python scripts/mc_cb_scan.py scan   --world <世界目录> --out command_blocks.csv --dims overworld --jobs 4
python scripts/mc_cb_scan.py report --csv command_blocks.csv --out 命令方块梳理报告.md

# 参数
#   --world          世界目录（含 dimensions/ 或 region/）
#   --dims           限定维度，逗号分隔：overworld,the_end,the_nether
#   --jobs N         多进程并行（大世界提速明显）
#   --cluster-threshold  空间聚类阈值，默认 256（Chebyshev 格）
#   --max-coord      坐标异常阈值，默认 1,000,000（超过判为损坏/残留，聚类时剔除）
```

## 原理（为什么快）
- 直接解析 `dimensions/<d>/region/*.mca` 文件头，只读取**确实存在**的区块。
- 用**自定义流式 NBT 解析器**只提取区块根节点的 `block_entities` 列表，**跳过庞大的区块体 `Sections`**（方块状态调色板）数据——这是体积最大的部分。
- 纯标准库 `zlib/gzip/csv`，无重型依赖。
- 实测：10,713 个 region / 约 10GB 主世界，全量扫描约 **49 分钟**（多进程更快）。

## 扫描输出字段（CSV）
`dimension` · `region_file` · `x/y/z` · `type_id`(命令方块类型) · `Command`(完整指令) ·
`auto`(0=需红石/1=持续) · `ConditionalMode`(新格式为 `conditionMet` 运行时状态，非配置) ·
`CustomName` · `powered` · `TrackOutput` · `successCount` · `LastOutput`

## 报告自动产出的分析维度
1. **总体统计**：总数、按维度/类型/触发方式、选择器使用（`@a/@e/@p/@s` 等）。
2. **空间集群**：按坐标聚出各"功能机制/建筑区"（含 bbox 与指令构成），便于定位每处建筑。
3. **指令分类**：kill/tp/title/give/execute/spawnpoint/... 各自数量。
4. **异常与风险项**（自动检测）：
   - `/op` 提权命令方块（安全后门风险，务必移除）；
   - 超大坐标命令方块（`|coord| > --max-coord`，多为恢复/合并产生的损坏残留）；
   - 超大跨度 `fill`（`fill x1 y1 z1 x2 y2 z2` 中某轴跨度 >200，参数疑似笔误）。
5. **迁移评估**：
   - 区域/距离选择器指令（`dx=`/`distance=`）——Folia 分区线程模型下跨区块实体扫描行为与 Paper 有差异，需逐个验证；
   - `@e` 全实体扫描；跨维度传送（`execute in <dim> run teleport`）；
   - **命中 Folia 禁用指令集（`DISABLED_CMDS`）的命令方块清单**——这些需重点评估替换/模拟方案。

## Folia 禁用指令集（DISABLED_CMDS，与 analyze_cmdblocks.py 一致）
`bossbar, clone, data, datapack, debug, function, item, loot, reload, return, ride, rotate, schedule, scoreboard, spectate, spreadplayers, tag, team, teammsg, tick, trigger, perf, save-all, saveall, restart`

> 命令方块内**通常只存原版指令**；插件指令（Essentials/WorldEdit 等）不落在命令方块里，属于服务器/插件层面被禁，需结合插件清单与报错日志定位。

## 实测样例（恢复存档，1,127 个命令方块）
- 全为**脉冲型**（`command_block`），无连锁/循环。
- 主世界 1,117 / 末地 9 / 下界 1。
- 约 10 个功能集群：奖励房(title/give/kill)、主线传送(tp/say/title)、跑酷死亡区(kill:160)、出生点主城(spawnpoint/scoreboard)、游戏倒计时(say/title)、通关点("恭喜通关")等。
- 命中 Folia 禁用指令的命令方块 32 个：`tag`×18、`scoreboard`×14 → 迁移需重点评估。
- 检测到异常：1 个 `/op` 提权命令方块；region `r.39006.39006.mca` 116 个坐标超 1,000 万的损坏残留；1 个跨 3,892 格的超大 `fill`。
- 结论：命令方块本身全原版脉冲，无常驻循环逻辑需重写；被禁 24 条指令应为插件层面，不在命令方块内。

## Pitfalls
- **坐标异常 ≠ 有效命令方块**：`|x|`/`|z|` 超过数百万的集群，几乎确定是地图恢复/合并产生的残留，迁移前单独核实，确认无用再清理。
- **`/op` 命令方块是严重安全后门**：任何玩家触发即被提权，必须移除，不能随迁移带到新服。
- **`ConditionalMode` 在新版已不是配置字段**：它由区块方块状态(palette)决定；方块实体里的 `conditionMet` 是运行时状态，报告该列仅供参考。
- **Windows 下用 MSYS 路径会失败**：`mc_cb_scan.py` 是原生 Python，传入路径用 `E:/recover/...` 而不要用 `/e/recover/...`；`--world` 同理。
- **扫描只读不写**：不会改动原存档；但为准确，请先确保存档处于已停服/已保存状态。

## 迭代与扩展
分析逻辑集中在 `analyze()`（异常检测规则、聚类、禁用指令核对）与 `render_report()`（Markdown 模板）。新增检测/改版式只改这两处。底层扫描器 `scan_region_file()`/`scan_world()` 返回标准行字典列表，便于接其他下游。
