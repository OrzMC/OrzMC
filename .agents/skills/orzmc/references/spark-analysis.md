# Spark 性能分析

> **三端 spark 部署现状（2026-08-06 核对）**：**本地测试服 + Exaroton 装有 spark 插件**（plugins/spark）；**MCSM 未装 spark**（plugins/ 无 spark.jar）——MCSM 上用 spark 需先装插件（上传到 plugins/update/ 或 plugins/）。老 Paper 曾内置 spark，但当前 26.2 三端基线**以插件形式存在**。

## 命令速查（控制台/玩家均可执行）

| 命令 | 用途 | 输出 |
|:----|:----|:----|
| `/spark health` | 一键健康报告 | TPS/MSPT/CPU/内存/磁盘 + 进度条 |
| `/spark tps` | TPS 历史 | last 5s/10s/1m/5m/15m |
| `/spark profiler --timeout 60` | CPU 采样（主线程热点）| 生成报告链接 |
| `/spark profiler --timeout 60 --only-ticks-over 100` | 只采卡顿 tick（>100ms）| 聚焦卡顿原因 |
| `/spark tickmonitor` | 实时 tick 监测 | 卡顿 tick 时长+增幅（输出到控制台）|
| `/spark gc` | GC 统计 | Young/Concurrent/Old 次数+平均时长+频率 |
| `/spark heapsummary` | 堆内存对象分布 | 写 .sparkheap 文件（需 viewer 解析）|
| `/spark healthreport --upload` | 上传健康报告 | 链接 |

## 读取报告数据（关键技巧）

- **报告链接后加 `?raw` 直接得 JSON**（2026-08-03 实测）：
  ```bash
  curl -sL "https://spark.lucko.me/{code}?raw" -o report.json
  # JSON 结构: metadata.systemStatistics (CPU/内存/GC/磁盘/Java 参数)
  #           metadata.platformStatistics (tps/mspt/memory 均值+峰值)
  #           metadata.platformStatistics.world (全服实体统计: totalEntities + entityCounts 按类型!)
  ```
- **`world.entityCounts` 是全服实体精确构成**（一次 profiler 顺带拿到，无需计分板）：`{totalEntities: 4812, entityCounts: {bat: 1575, glow_item_frame: 381, ...}}`——77 种类型精确计数
- 报告页本身是 Next.js SPA（无内嵌数据），web_extract 会拦截 spark.lucko.me，**必须用 `?raw`**
- profiler 完成后控制台输出 `https://spark.lucko.me/{code}` 链接
- ⚠️ `?raw` 只含 metadata + platformStatistics，**无 classContributions/threads 采样明细**（实体热点精确定位受限；`"threads":24` 是 CPU 核数不是线程数）
- ✅ serverConfigurations 是原始字符串，可解析验证服务器配置

## 判断标准

| 指标 | 健康 | 需关注 | 严重 |
|:--|:--|:--|:--|
| TPS | 20.0（满帧）| <19 | <15 |
| MSPT 中位 | <50ms | 50-60ms | >60ms |
| MSPT 95% | <60ms | 60-100ms | >100ms |
| 内存占用 | <70% | 70-85% | >85% |
| 磁盘 | <80% | 80-90% | >90% |

## 典型诊断流程（卡顿排查）

1. `/spark health` 看整体：TPS/MSPT/内存/磁盘
2. 内存高 → `/spark gc` 看 GC 频率：Young 每 <30s 满 = 堆太小；Old 有 Full GC = 泄漏/堆不足
3. TPS 低但 CPU 低（如 5%）→ **主线程被阻塞**（实体 AI/插件同步/GC）
4. `/spark profiler --only-ticks-over 100` 采 60-90s → `?raw` 拿 JSON 分析主线程热点
5. `/spark tickmonitor` 持续观察卡顿 tick 模式（时长+增幅）

## 通过 MCSM API 执行 spark 命令

```bash
# 空格直接用原始字符（不要 URL 编码成 %20，MCSM 不解析）
python3 scripts/cmp3/mcsm_env.py 调 mcsm_api_post(cfg, "api/protected_instance/command",
    {"daemonId":..., "uuid":..., "command": "spark health"})
# 输出在日志里，读 logs 即可
```

## Spark 踩坑（2026-08-03 实测）

- ⚠️ **Windows 服务器（windowsserver2022/amd64）async-profiler 引擎不可用**，自动降级 built-in Java 引擎（功能正常，采样精度略低）——日志提示属正常
- ⚠️ **`/spark activity` 报 `NoClassDefFoundError: net/kyori/examination/Examinable`**：Paper 内置 Spark 1.10.152 的 bug（缺 kyori examination 库）——**别用 activity**，用 profiler/tickmonitor 替代
- ⚠️ `/spark exporter` 不是子命令（会打印帮助）——导出数据用报告链接 `?raw` 即可
- ⚠️ heapsummary 生成的 `.sparkheap` 是二进制 protobuf，需官方 viewer（spark.lucko.me 上传）解析，命令行拿不到对象明细
- ✅ profiler 有轻微性能开销（采样），选玩家少时段；`--only-ticks-over` 可减少开销
- ✅ tickmonitor 会在卡顿 tick 后输出 `Tick #N lasted Xms (Y% increase from avg)`——先跑 6s 基线，之后持续报告
