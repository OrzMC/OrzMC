# 服务器性能诊断（performance）

> 合并自：minecraft-server-performance-analysis（2026-08-10 阶段二整合）
> 触发：用户反馈卡顿/掉帧/TPS 低，要求定位卡顿原因、对比优化前后效果（本地/Exaroton/MCSM 三端）。

## 核心事实

- **Spark 部署现状**：**Paper 26 内置 spark**（`/spark` 命令无需插件，2026-08-13 日志实证 `me.lucko.spark.paper`）；本地测试服 + Exaroton 可用；**MCSM 未装**（需先上传 plugins/ 或 update/）；⚠️ 服务器停止时 spark 采样线程报 `Uncaught exception thrown in thread spark-java-sampler` 属**正常关闭噪音**（世界保存照常完成），别误判崩溃
- ⚠️ Spark 1.10.152 `/spark activity` 有 bug（NoClassDefFoundError Examinable）——其余模块正常
- Windows Server 不支持 async-profiler 引擎（自动回退 built-in Java 引擎，功能正常）
- **判断标准**：TPS < 20 或 MSPT > 50ms 需定位；TPS < 16 严重
- **报告数据获取（关键）**：Spark 报告链接后加 **`?raw`** 直接返回完整 JSON（165KB+）——普通 GET 只回 Next.js 壳 HTML，web_extract/curl 拿不到数据

## 诊断流程（五步）

1. **总览**：`/spark health`（TPS 5s/10s/1m/5m/15m、MSPT min/med/95%/max、CPU、内存、磁盘）或 `/mem`
2. **确认模式**：`/spark tickmonitor` → 先算基线（~120 ticks）→ 报告超过均值 100% 的 tick，跑 2-3 分钟
3. **精确定位**：`/spark profiler --timeout 60 --only-ticks-over 100` → 报告链接 + `?raw` 分析
4. **GC 判断**：`/spark gc`——Young GC 每 25s 一次说明堆太小；Old Gen Full GC 单次 >500ms 是「世界瞬卡」元凶
5. **堆对象分析**（可选）：`/spark heapsummary`（二进制 .sparkheap，需 viewer）

## 实体审计（FPS 低排查）

- **方法 0（首选）**：`/paper entity list * minecraft:overworld`——一行出全服实体构成；**world 必须用命名空间 key**（`minecraft:overworld` 不是 `world`）；**Ticking/Non-Ticking 双计数是核心**——Non-Ticking 不吃服务端 CPU 但客户端照样渲染
- **方法 1**：Spark 报告 `?raw` → `metadata.platformStatistics.world.entityCounts`（全服 77-83 种精确字典，零命令）
- **方法 2（兜底）**：计分板逐类型计数（`scripts/mcsm_entity_audit.py <玩家> <半径>`）
- ⚠️ 选择器坑：`type=A,type=B` 多值在 1.20.5+ 失效（必须每类型单条命令）；`distance=..N` 是 3D 球体（高空玩家漏掉下方地面实体，用水平框 `x,y=0.0,z,dx,dy=320.0,dz`）；`dx/dz` 必须配 `y/dy`
- **FPS vs TPS 独立**：FPS 低=客户端渲染（装饰实体是渲染大头：展示框/画/盔甲架）；TPS 低=服务端忙（实体 tick 负载）。验证服务端健康：0 玩家时 `/spark health`（空闲 TPS=20、MSPT<10ms = 服务端无问题）
- 治本在客户端（Sodium/Lithium）；服务端零风险清掉落物（`/kill @e[type=item]`）

## Spark JSON 结构（?raw）

- 所有数据在 `metadata` 内：`platformStatistics.{tps,mspt,memory,gc,world}` + `systemStatistics.{cpu,memory,disk,java.vmArgs}` + `serverConfigurations`
- `platformStatistics.world` = 实体统计首选；`systemStatistics.java.vmArgs` 直接看 -Xmx 实际值

## 远程端执行（MCSM）

- 通过 command API 发送 spark 命令，等 5-8s 读日志
- ⚠️ 含空格命令**勿预先 URL 编码**（quote 后原样显示无法解析）——直接传原始字符串
- 只读命令（tps/mem/spark health）可在线执行；profiler 有采样开销选玩家少时段

## 修复方案（按根因）

| 根因信号 | 修复 | 需重启 |
|:--|:--|:--:|
| 堆 89%+、Young GC 每 25s | JVM 堆调大（Start.bat -Xms/-Xmx） | ✅ |
| Full GC 单次 >500ms | 堆调大 + 重启清碎片 | ✅ |
| CPU 低但 TPS 低 | 主线程被阻塞 → profiler 定位针对性处理 | 视情况 |
| 磁盘 90%+ | 清宿主机磁盘（磁盘满导致保存卡顿/崩溃） | ❌ |
| 长时间未重启 | 重启清内存碎片 | ✅ |

**Aikar's Flags**：mcflags.emc.gs 模板适合 8G+ 堆——4G 太小会 Young GC 每 25s + Full GC 546ms → TPS 12；**实测 4G→8G 后 TPS 12→20、MSPT 82→37ms、内存 89%→23%**

## Pitfalls

- Spark 报告链接不要用 web_extract/普通 curl（Next.js SPA）——**?raw 一步到位**
- `/spark activity` 1.10.152 报 ClassNotFound（库缺失），别浪费时间排查环境
- tickmonitor >100% 阈值基于当前均值——基线偏高时小卡顿不触发，结合 health MSPT 中位看
- MCSM files/list 必须带 `page`（从 0）+`page_size`+`file_name`（缺参数 400/空列表）

## 支持文件

- `scripts/mcsm_entity_audit.py`：MCSM 实体审计（走 cmp3 command API）
- `scripts/mcsm_apply_config_template.py`：MCSM 批量改配置模板
- `references/entity-statistics.md`：快速实体统计（现有）
