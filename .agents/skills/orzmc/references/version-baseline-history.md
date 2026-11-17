# 版本基线历史（逐轮快照 · 仅作演进参考）

> ⚠️ **本文全部是历史快照，不构成当前口径**。当前权威基线只有一处：`SKILL.md` § 关键事实 →「当前基线（2026-11-09 第七轮）」。
> 逐轮升级的完整实录与新坑见 `test-server-upgrade-sop.md` §2d–§2j。

## 2026-11-02 第六轮（历史）

**paper** = Paper **26.3-237（STABLE）** + Geyser **1280** + LuckPerms **5.5.90** + ViaVersion/ViaBackwards **5.12.2** + voicechat **2.6.25（release，已从 beta 回退）** + GriefPrevention **16.18.8** + GrimAC **2.3.74（release）**；
**folia** = Folia **26.2-7** + 同批 Geyser/LuckPerms/Via + GP3D **19.0.5** + WorldEdit **7.4.6**（WorldGuard 保持 **7.0.19**：7.0.20 的 `game_versions` 只声明 26.3）。
**海外服 Exaroton** 插件已同步同版本（核心由面板管，已是 26.3-237）；**国内服 MCSM 因 apikey 失效未同步，需人工**。交付包：`S:\orzmc-upgrade-20261102\`（+ `.zip`）。

## 2026-10-26（历史 · 巡检实查，非升级）

**papermc-test 核心已到 Paper 26.3-223**（= fill 最新 STABLE）；folia-test 仍 **Folia 26.2-7**（26.3-5 仍 ALPHA，按纪律不动）。
待升项：Geyser b1265→**b1271**、LuckPerms 5.5.87→**5.5.88**、voicechat 2.6.24→**2.6.25**；folia 侧 EssentialsC 4.3.4→**4.3.5**、GP3D 18.4.14→**19.0.1**、SCore 5.26.10.17→**5.26.10.20**。其余 20 项一致。

## 2026-10-19 第四轮（历史）

**papermc-test** = Paper **26.3-205（STABLE）+ WorldEdit 7.4.6 正式版 + WorldGuard 7.0.20 + Geyser 2.12.0-b1265（26.3 上首次成功启用）+ OrzMC 1.0.29-dev.427 + LuckPerms 5.5.87 + Via 5.12.1 + packetevents 2.14.0 + GrimAC 2.3.74-abb95b6 + voicechat 2.6.24**；
**folia-test** = Folia **26.2-7**（26.3 仅 ALPHA 未采用）+ Geyser 1265 + EssentialsC 4.3.4 + ExecutableEvents 3.26.10.17 + SCore 5.26.10.17 + GP3D 18.4.14 + **WorldEdit 7.4.5 / WorldGuard 7.0.19（故意不升）**。
→ 26.3 就绪门槛 6 项解除 2 项（WE 正式版 ✅ / Geyser ✅），仍缺 EssentialsX 正式版、GrimAC 正式 release、F3F4Perms/SimpleLogin 元数据。

## 2026-10-12 第三轮（历史）

**papermc-test** = **26.3 实验态：Paper 26.3-177 + WorldEdit 7.4.6-beta-02**（Geyser 1251 在 26.3 上不可用被迫禁用；**后由 b1265 解决**）。26.3 之前 26.2 态 = Paper 26.2-133 + WE 7.4.5（产物与备份在 `/upgrade-bak-20261012-263/`、`/tmp/orzmc_263_check/`）。
**folia-test** = Folia **26.2-7** + Geyser **b1251** + Via 双件 **5.12.1** + EssentialsC **4.3.3** + ExecutableEvents **3.26.10.10** + SCore **5.26.10.10** + GP3D **18.4.12** + AxGraves 1.32.1 + OrzMC 1.0.29-dev.427。
26.2 态（26.3 之前）：paper 26.2-133 + Geyser 1251 + Via 5.12.1 + OrzMC 1.0.29-dev.427 + LuckPerms 5.5.87 + packetevents 2.14.0 + voicechat 2.6.24 + WE 7.4.5 + WG 7.0.19 + GrimAC 2.3.74-abb95b6。备份 `/upgrade-bak-20261012` 保留、实例停回停止态。

## 2026-09-20（历史 · 早期基线）

两实例均 **26.2 线 + Java 25**，插件走 **dev/beta 轨道**（老板决策：测试服用于开发测试验证插件功能）——Geyser-Spigot **build 1245（2.11.3）**、LuckPerms **5.5.85**、ViaVersion/ViaBackwards **5.12.0**、ViaRewind **4.2.0**、WorldGuard **7.0.19**；OrzMC paper **1.0.27-dev.422** / folia **1.0.25-dev.416**；papermc-test 额外 Paper **26.2-126（STABLE）** + voicechat **2.6.23**；folia-test 额外 Folia **26.2-7** + AxGraves **1.31.0** + EssentialsC **4.3.0** + GP3D **18.4.4** + ExecutableEvents **3.26.9.17** + SCore **5.26.9.17** + VaultUnlocked **2.20.3**。

## 协议生态演进（历史结论，均已被后续版本解决）

| 时间 | 当时结论 | 现状 |
|:--|:--|:--|
| 2026-09-20 | 26.3 客户端「能进却被 GrimAC 踢」（GrimAC 2.3.74 内置 packetevents 只到 26.2 → `Unknown entity metadata type id: 105 version V_26_2`） | **已解决**：packetevents 2.14.0 发版、GrimAC 2.3.74 release 支持 26.3；三端现均 26.3 且无此报错 |
| 2026-10-12 | 三端维持 26.2 线，用 Via `block-versions: [">26.2"]` 干净拒绝 26.3 客户端 | **已解除**：核心升到 26.3-246；`block-versions` 现在用于安全性（堵 1.20.5–1.21.4），语义不同，别照抄 |
| 2026-09 | Via 三件套必须 ≥ 5.12.0（5.11.0 只支持到 26.2） | 仍成立，现部署 5.12.2 |
| 2026-10 | Exaroton 端 jar 严重落后（OrzMC 1.0.24 / Geyser 1230 / Via 5.11.0） | **已追平**：Exa 现 Paper 246 + Geyser 1298 + LP 5.5.91 + OrzMC 1.0.30 |
