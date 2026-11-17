# 插件发布渠道清单（Modrinth / Hangar 覆盖情况）

> 用途：判断某插件能否通过 Modrinth/Hangar 平台升级，不能的话从哪手动升级。
> 实测时间：2026-08-04，对照三端 17 插件基线。

## 结论速查

### ✅ 双平台可升级（Modrinth + Hangar 都有官方项目）
ViaVersion / ViaBackwards / ViaRewind / Geyser / WorldEdit / DeathChest / EzShops / EssentialsX / GriefPrevention / SkinsRestorer

### ⚠️ 单平台可升级
| 插件 | Modrinth | Hangar | 说明 |
|:--|:--:|:--:|:--|
| LuckPerms | ✅ | ❌ | Hangar 只有第三方（Luckperms-Supporter 等），**官方只在 Modrinth** |
| WorldGuard | ✅ | ❌ | Hangar 只有第三方（WorldGuardExtraFlagsPlus 等），官方在 Modrinth + Bukkit |
| OrzMC | ❌ | ✅ | 自有插件，只发 Hangar（Modrinth 发布报错、GitHub Release 滞后） |
| GetMeHome | ❌ | ⚠️ | Hangar 有但 owner=wangzhizhou666（自己的 fork，非官方）；**官方源是 GitHub SimonOrJ/GetMeHome** |

### ❌ 双平台都无（必须手动升级）
| 插件 | 实际渠道 | 备注 |
|:--|:--|:--|
| **LoginSecurity** | GitHub `lenis0012/LoginSecurity` | jar 内 manifest-url 指向 GitHub，Spigot 页面 403 无法直查，**升级=GitHub Releases** |
| **BackOnDeath** | SpigotMC / 个人站 jsapphire.tk | 无官方 GitHub 仓库，版本 0.4 已稳定 |
| **Vault** | Bukkit dev.bukkit.org | 经典老插件，只有 Bukkit 官方 |

## 官方渠道版本查询端点（2026-08-06 实测，平台滞后官方！）

> ⚠️ **Hangar/Modrinth 平台更新滞后官方**（LuckPerms 平台显示 5.5.53-bukkit，官方已 5.5.71，差 18 版）。用户要求：**Essentials / Geyser / LuckPerms 优先从官网查版本**。

```bash
# LuckPerms 官方（download.luckperms.net 是 SPA 无版本号，用 metadata API）
curl -s https://metadata.luckperms.net/data/all | jq -r '.version'          # 最新版号
curl -s https://metadata.luckperms.net/data/all | jq -r '.downloads.bukkit' # 下载 URL
# → https://download.luckperms.net/<id>/bukkit/loader/LuckPerms-Bukkit-<ver>.jar

# Geyser 官方（download.geysermc.org v2 API）
curl -s https://download.geysermc.org/v2/projects/geyser/versions/latest/builds/latest | jq -r '.version, .build'
# 下载: https://download.geysermc.org/v2/projects/geyser/versions/<ver>/builds/<build>/downloads/spigot
# （jar 内 plugin.yml 仍显示 2.11.1-SNAPSHOT，但 build 号即稳定构建标识）

# EssentialsX 官方（GitHub releases）
curl -s https://api.github.com/repos/EssentialsX/Essentials/releases/latest | jq -r '.tag_name'

# ViaVersion 系列：稳定版=5.11.0/4.1.3（5.12.0 仅 SNAPSHOT，生产不升）
```

## PaperMC update/ 机制实测（2026-08-06 修正此前错误认知）

> ⚠️⚠️ **「先删旧 jar 再放 update/」是错的**——2026-08-06 实测：删掉 plugins/ 旧 jar 后，update/ 里的新 jar **不会被消费**（PaperMC update/ 按【插件名】替换：旧 jar 没了 → 无事可做 → 重启后 update/ 原样保留、plugins/ 无新插件）。正确做法：
> - **升级**：旧 jar **保留**在 plugins/ + 新 jar 放 update/（重启自动原子替换，update/ 清空）
> - **新装/旧 jar 已删**：新 jar **直接放 plugins/**（放 update/ 无效）
> - 带版本号 jar 升级：新文件名 ≠ 旧文件名 → update/ 按插件名（plugin.yml name）匹配仍会替换，无需同名；但若旧 jar 已删则必须直接放 plugins/
> - 判据：重启后 `ls plugins/update/` 为空 = 消费成功；非空 = 没匹配到旧插件

## MCSM 重启与验证（2026-08-06 实测）

- `adapters/mcsm.sh restart` 有安全保护：**有玩家在线时拒绝**（`❌ 有 N 名玩家在线，禁止破坏性操作`）
- 用户已通知玩家并同意重启时，**直连 API 绕过保护**：`GET api/protected_instance/restart?apikey=...&daemonId=...&uuid=...` → `{"status":200,...}`
- 重启后等待：status 显示 `已运行 0h0m`/`玩家 0/0` = 仍在启动；`Done (Xs)!` 日志 = 就绪
- **重启后验证清单**：① update/ 已清空（=更新已应用）② server.properties 值正确（mcsm_download 读回）③ 日志 `Enabling X vY` 行确认新版本——⚠️ 只查 plugins/ jar 存在 ≠ 加载成功，必须看 Enabling 日志行

## 验证方法（对任意插件）

```bash
# Modrinth：HTTP 200=有官方项目
curl -s -o /dev/null -w "%{http_code}" "https://api.modrinth.com/v2/project/<slug>"
# Hangar：HTTP 200=有官方项目（注意：slug 大小写敏感）
curl -s -o /dev/null -w "%{http_code}" "https://hangar.papermc.io/api/v1/projects/<Slug>"
```

> ⚠️ 坑：Modrinth 搜索 API 会返回**同名第三方**（如 essentials 搜到 inventory-essentials、vault 搜到 create-vibrant-vaults）——必须用**精确 slug 直查**（`/v2/project/<slug>`）而非搜索。Hangar 同理（LuckPerms 搜到 Luckperms-Supporter）。判断"官方"看 namespace owner 是否原作者。

## 功能覆盖判定（2026-08-05 实测修正：**结论已推翻，勿删**）

> ⚠️⚠️ 2026-08-04 曾误判「BackOnDeath/GetMeHome 被 EssentialsX 覆盖可删」，**2026-08-05 实测推翻**——以下是正确结论。

| 插件 | 覆盖方 | 实测证据 | 结论 |
|:--|:--|:--|:--|
| **BackOnDeath** | ❌ EssentialsX `/back` **不能覆盖** | Essentials 的 `setLastLocation` **只在 PlayerTeleportEvent（PLUGIN/COMMAND 原因）更新，死亡事件不更新**。实测：原地 kill 死 @ (8.5,65,-466.5)，复活后 `/back` 回 (6.5,64,-470.5)，差 4.5 格——**`/back` 回的是"最后传送前的位置"，不是死亡点**。`back.ondeath` 权限只是"允许 /back"，不改变记录机制 | 🟢 **保留**（功能真实需要：回死亡点）|
| **GetMeHome** | ❌ 不能删 | 「homes.yml 空」是**本地测试服**（没人玩）；**线上 MCSM homes.yml 有 60+ 玩家**（laojue 4 个家：1/2/3/default），坐标远至 (18755, 780)——**线上核心功能** | 🟢 **保留**（迁移 Essentials 需另做方案）|

### 教训（判定"插件可删"的完整流程）
1. **查使用痕迹必须查线上（MCSM/Exaroton）数据，不能只看本地测试服**——测试服没人玩，数据文件为空 ≠ 线上无人用（homes.yml 本地空/线上 60+ 玩家的教训）
2. **"命令名相同/权限相同" ≠ 功能相同**——BackOnDeath vs Essentials `/back` 名字相似，但**记录机制不同**（死亡事件 vs 传送事件）。判断覆盖必须**实测行为**（死一次→/back 看是否回死亡点），不能只看 jar 描述
3. 反编译确认机制：`javap -c` 看监听器在哪个事件调 `setLastLocation`（EssentialsPlayerListener 里 PlayerTeleportEvent 分支），即可确认记录时机

### GetMeHome 数据格式（迁移 Essentials 用，2026-08-05 实证）
```yaml
# plugins/GetMeHome/homes.yml（线上真实结构）
d67212ac-985d-3401-9f67-d977f5cb6b72:   # 玩家 UUID（顶层 key）
  n: laojue                            # 玩家名（小写）
  h:                                   # homes
    '1':                               # 家名（数字或命名）
      w: world                         # 世界
      c: [165.6, 73.0, 160.08]         # x,y,z
      y: [-90.89, 12.74]               # yaw,pitch
names:                                 # 名字→UUID 索引表
  laojue: d67212ac-...
```
- 迁移 Essentials 需转换：UUID → `plugins/Essentials/userdata/<uuid>.yml` 的 `homes:` 段（world-name/x/y/z/yaw/pitch 独立字段，格式不同）
- 多 home 需 `essentials.sethome.multiple` 权限（默认只给 1 个）——laojue 有 4 个家，迁移要给权限
- 线上读取法：MCSM `GET /api/files/download`（见 papermc 技能 mcsm-backend.md，**必须 GET 非 POST**）→ `GET http://{SERVER_HOST}:24444/download/{pwd}/homes.yml`
