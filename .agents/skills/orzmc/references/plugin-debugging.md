# 插件 Bug 排查（plugin-debugging）

> 合并自：papermc-plugin-debugging（2026-08-10 阶段二整合）
> 触发：插件功能在特定环境失效（远距离/未加载区块/特定核心构建号）；升级 Paper 大版本后命令未注册、权限异常；本地复现生产问题。

## 核心方法论

1. **本地复现优先，配置对齐生产**
   - 关键参数逐项比对：核心构建号、view-distance、simulation-distance
   - 调小 view-distance 可短距离复现「未加载区块」类问题（如 3=48 格模拟生产 6=96 格）
   - 构建号不同行为可能不同（26.2-92 vs 26.2-111）——必须对齐生产构建号

2. **命令可用性 vs 权限分开排查**
   - 先实测 `/<命令>`：`Unknown or incomplete command` = **命令未注册**（≠权限问题，重启无效）
   - 再 LP 验证：`lp group <组> permission check <节点>`——**LP 权限变更即时生效，无需重启**
   - 命令注册了但「无权限」才是权限问题；命令不存在是插件注册/兼容问题

3. **实体事件依赖类 bug**（箭/掉落物/弹射物落地事件）
   - 根因模式：实体只能存在于已加载区块——飞出 view-distance → 被卸载 → 事件永不触发
   - simulation-distance 对弹射物**豁免**（实测模拟区外箭仍 hit）——真正边界是 view-distance
   - ❌ 预加载路径区块方案无效（Paper 立即卸载视距外区块）
   - ✅ **射线替代**：`rayTraceBlocks` → 落点找安全点 → `teleportAsync`（玩家传送强制加载目标区块）；`rayTraceBlocks` 遇未加载区块返回 null——沿视线逐个 `getChunkAtAsync` 在回调内重试

4. **版本兼容矩阵（升级核心前必查）**
   - 实验版核心（Paper 26.2）插件支持滞后：EssentialsX 2.22.0 官方仅支持 26.1.2/1.21.11
   - 症状：日志 `unsupported server version` + **部分命令未注册**（spawn 缺失而 fly/gamemode 正常）
   - 升级大版本先 `web_search「<插件> 支持 <核心版本>」`

5. **测试账号纪律**：勿用 op 账号测权限（部分核心版本 op 权限检查全拒误导）；用目标权限组账号实测

## 通知聚合设计（防刷屏，2026-08-09 实测）

- **用户报「防刷屏无效」先核对设计，不一定是 bug**：原设计「批次首事件立即发送 + 窗口尾部补发 ×N」→ 每类型 2 条（3 TNT = 4 条）——聚合生效了但双条设计感知上是刷屏
- **用户验证过的正解（纯聚合）**：窗口内不立即发，窗口结束**只发一条**（多事件带 ×N、单发不带次数）——3 TNT 从 4 条降到 2 条；代价是通知延迟一个窗口（~1s）
- 排查顺序：先看聚合键（同区域+同类型）+ 窗口逻辑，判断「聚合没生效」还是「生效但设计双条」；测试驱动改（聚合相关单测全量适配新语义）

## 核心下载通道（2026-08 变化）

- PaperMC API **v2 已 sunset**（`api.papermc.io/v2/...` 返回 `{"ok":false,"error":"sunset"}`）——走 v3/fill-data 新通道；`fill-data.papermc.io/v1/objects/<sha256>/<文件名>` 下载仍可用
- GitHub/papermc.io 直连常失败时：优先用本地已有 jar 或 MCSM 面板文件

## 支持文件

- `references/tpbow-ray-teleport.md`：传送弓射线传送完整案例（根因/方案演进/API 坑/bot 测试/RCON 协议）
