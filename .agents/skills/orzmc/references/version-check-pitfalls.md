# mc_version_check.py 已知坑（版本巡检脚本）

> 从 SKILL.md 外置（2026-11-10 整理）。脚本：`~/.hermes/scripts/mc_version_check.py`。
> 纪律：**凡出现「未识别 jar」告警必须当场补映射**，否则静默漏报升级项；补完当场跑一次确认告警消失。

1. Geyser jar 内 plugin.yml 固定显示 `2.11.1-SNAPSHOT`，版本以文件名构建号为准（正则 `-(\d+)\.jar$`）；**2026-08-12 已修复：脚本按 build 号比较部署 vs 最新（同 build 即 ✅，不再假阳性）**
2. OrzMC 用 `paper-plugin.yml`（非 plugin.yml）
3. Modrinth SkinsRestorer 需 loaders 过滤（否则返回 neoforge 假阳性）
4. WorldEdit/WorldGuard 版本带构建后缀（`7.4.4+7546-...`）需 strip
5. **CustomWorldHeight 只在 Modrinth（slug: customworldheight），Hangar 无此插件**（2026-08-15 实测：Hangar 查询失败 → Modrinth 正常 2.2.0）
6. LuckPerms 官方渠道是 metadata.luckperms.net（`downloads.bukkit` 直链），Modrinth 滞后（5.5.76 时 Modrinth 只有 5.5.71-bukkit）
7. Geyser build 号频繁更新（1222→1223 一天内），升级前必须查最新
8. **packetevents 多平台发布（fabric/velocity/sponge/spigot/bungeecord），须 loaders=["paper","spigot","bukkit","folia"] 过滤，否则返回第一个 fabric 版（version_number 形如 `2.13.0+spigot`，strip_build 剥离 `+...` 后比较）**
9. **自带版本号文件名变更（2026-09-14 修复）**：OrzMC 升到 `OrzMC-1.0.27-dev.422.jar` 后精确映射表 FNAME_NAME 未命中 → 该行显示「未部署」+ 未识别 jar 告警（假阴性）。已加 `PREFIX_NAME` 前缀兜底 + `resolve_name()`（精确表优先→最长前缀匹配），Geyser build 号改用扫描到的真实文件名（`RAW_FNAME`）解析——**升级插件后无需再改脚本**；**
10. 2026-10-12 补｜`PREFIX_NAME` 自身也会漏**：`GriefPrevention3D-18.4.8.jar` / `SkinsRestorer-15.12.6.jar` 改名后仍报「未识别 jar」（SkinsRestorer 因此误报「未部署」；**GriefPrevention3D 的 18.4.8→18.4.12 升级项被整条吞掉**）→ 已补 `GriefPrevention3D-`/`GriefPrevention-`/`SkinsRestorer-`/`deathchest-`/`BackOnDeath-`/`Vault-` 前缀。⚠️ **纪律：凡出现「未识别 jar」告警必须当场补映射**，否则静默漏报升级项；补完当场跑一次脚本确认告警消失。**另：本脚本只扫 MCSM 侧 jar，Exaroton 端 jar 版本从不检查**（2026-10-12 才发现 Exa 落后一大截）→ 待补 Exa 侧盘点；有差异时 cron agent 发飞书询问用户是否升级，升级走两端顺序：MCSM（测试）→ Exaroton（生产）（无玩家窗口）

## 覆盖范围缺口

本脚本**只扫 MCSM 侧 jar**，**Exaroton 端 jar 版本从不检查**（2026-10-12 才发现 Exa 落后一大截）→ 已用 `exa_sync_plugins.py` + 周巡检第③部分补位。

有差异时 cron agent 发飞书询问是否升级；升级顺序 = MCSM（测试）→ Exaroton（生产），无玩家窗口。
