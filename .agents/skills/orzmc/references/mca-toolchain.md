# MCA 级世界工具链（扫描 / 高度分析 / 槽位合并）

> 溯源：2026-09-11 清理 `E:\mc\recover`（OrzMCBackup 优化备份研究的临时工作区）时，把三个**上游仓库没有、技能里也缺**的纯 stdlib 脚本归档到此。其余文件（命令方块梳理报告/CSV/扫描器/合并日志/smoke_out/bench-scripts/旧 OrzMCAdmin clone）均已在技能或上游沉淀，见文末「已清理项对照」。

三个脚本共同点：**只用 Python 标准库**（zlib/gzip/struct/csv），不依赖 anvil-parser 等第三方库，可直接在服务器宿主机离线跑。

## 1. `scripts/merge_worlds.py` — 槽位粒度世界合并（关键工具）

**问题**：OrzMCBackup 优化备份（`--inhabited-time-seconds` 阈值）会删掉低活跃 chunk，其 region 文件是「部分占用」的。**把这种 region 同名覆盖到全量备份上会产生空洞**（优化备份里不存在的槽位被覆盖成空，历史区块全丢）。

**解法**：以全量备份为底，按 **chunk 槽位（每 region 1024 槽）** 逐个判定来源——patch 有则该槽取 patch（较新），否则取 base——再重新拼出 sector 对齐的 `.mca`：

```bash
python merge_worlds.py --base <全量旧世界> --patch <优化新世界> --out <输出> --verify
```

- `--verify`：复核每个共同 region 的槽位数 == |patch ∪ base|，不一致即报错（合并验收就靠它）
- **entities / poi 必须与 region 锁步合并**：三者同名文件用同一份槽位来源表（`sources`），否则会出现「区块有数据但实体文件空」或反之（`merge_linked()`）；合并后全空的 entities/poi 文件要删除，避免残留 base 旧实体
- 实现要点：直接搬 **原始 chunk payload 字节**（不解压 NBT），只改 location(4KiB) + timestamp(4KiB) 头 + 重新扇区对齐；单 chunk >255 扇区报错（region 格式上限）
- 别忘 `session.lock`：从 base 复制过去后要删掉，否则服务端认为世界被占用

**上游对应**（权威实现是 Kotlin，本脚本是等价离线复跑原型）：OrzMCBackup `docs/papermc-map-backup-recovery-case.md` 明确记载「一次性原型脚本 `merge_worlds.py`（纯 stdlib Python，便于离线复跑）」；正式实现 = `WorldMerger.kt` / `MergeCommand.kt`。阈值基准数据见同仓 `docs/threshold-benchmark-report.md`、`docs/real-world-backup-validation.md`。

## 2. `scripts/mca_scan_fast.py` — 加速命令方块扫描

```bash
python mca_scan_fast.py <world_dir> <out_csv>
```

流式 NBT walker：**跳过巨大的 sections / palette 数据**，只解析 `block_entities` 列表里的 `command_block` / `chain_command_block` / `repeating_command_block`。

- 用途：命令方块全量梳理（技能 `references/command-block-inventory.md` 那份清单的生成器升级版）。常规解析器要把每个 chunk 的方块调色板全解出来，大世界上百 GB 时慢得不可用；此脚本把「不解压 sections」当核心优化。
- 兼容 `dimensions/minecraft/<dim>/region` 与旧式 `world/region`。
- 与 `scripts/scan_cmdblocks.py` / `analyze_cmdblocks.py` 的关系：后两者是初版（功能全但慢），本脚本是性能版；**大世界优先用这个**。

## 3. `scripts/mca_height_scan.py` — 区块垂直范围分析

```bash
python mca_height_scan.py probe <region_file>        # 单个 region 的 chunk sections 概览
python mca_height_scan.py scan <dim_dir> [out.csv]   # 整维度扫描
```

自包含 NBT+MCA 读取器，输出每个 chunk 的 sections 高度范围与调色板信息。

**用途**：排查世界高度图异常——如 `Ignoring heightmap data ... expected: 37, got: 52`（见 `references/folia-experiment.md` 第 7 条：CustomWorldHeight 启用前后旧区块混存会导致此报错，无害但吓人）。用本脚本可实测目标区块实际高度范围，判断是「模板高度配置不一致」还是「世界内新旧区块混存」。

## 已清理项对照（2026-09-11）

| 原 `E:\mc\recover` 项 | 去向 |
|---|---|
| `命令方块全量梳理报告.md`、`command_blocks.csv`（1127 条） | 结论已沉淀于 `references/command-block-inventory.md`；CSV 可用脚本重生成 |
| `command-block-scanner/mc_cb_scan.py` | 已在 `scripts/mc_cb_scan.py`（此处仅作对照） |
| `merge_worlds.py` / `compare_merges.py` / `scan_fast.py` / `height_analyze/mca_scan.py` | 前三个已归档为上面的 1/2/3；对比脚本 `compare_merges.py` 的职能被 `merge_worlds.py --verify` 覆盖 |
| `bench-scripts/`（19 个阈值 sweep harness） | 数据与结论在上游 `docs/threshold-benchmark-report.md`，harness 为一次性 infra |
| `smoke_out/`(1.4M)、`*.log`、`merge_v2_report.json` | 测试产物，无保留价值 |
| `OrzMCAdmin/`（旧独立 clone） | 冗余：公共仓 `github.com/OrzMC/OrzMCAdmin` + 活跃同步副本 `~/AppData/Local/hermes/skill-repo/OrzMCAdmin`（`references/git-submodule-sync.md` 的「独立 clone 去重」先例） |
