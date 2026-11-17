# WorldEdit 防崩服（Litematica 投影调研 + 方案 A/B 实施）

> 2026-08-30 调研+实施沉淀。触发：玩家用投影模组（Litematica）粘贴大原理图，或直接用 WE `//set`/`//paste` 大编辑。
> 现状：本地 Paper+Folia 已实施 ✅，Exaroton/MCSM 待老板手动同步（Cloudflare challenge / 面板 API 开关阻塞）。

## 核心结论（谁会调 WE，风险等级）

| 场景 | 走 WE？ | 命令 | 风险 |
|:--|:--|:--|:--|
| Litematica 默认粘贴（`pasteUseFillCommand`=true）| ❌ | 原版 `/fill` `/setblock` 命令流 | 🟢 低（命令流被踢=chat-spam 阈值已解决；单条 /fill 硬上限 **32768 方块**，永不触发 Watchdog）|
| Litematica `commandUseWorldEdit`=true（1.18+ 选项）| ✅ | `//pos1 //pos2 //set` | 🔴 高（**builder 权限已被现有通配覆盖**，文档确认无需新权限即能用；wiki 明确不推荐此模式）|
| 玩家直接 WE `//paste`/`//schem paste` | ✅ | `//copy //paste` | 🔴 高（builder 有 `worldedit.clipboard.*`/`schematic.*`）|

## 崩服机制（官方 FAQ + 本地实测）

| 机制 | 原理 | 本地现状 |
|:--|:--|:--|
| Watchdog 杀服 | 原版 WE 编辑**主线程同步执行** → 超大编辑单 tick 阻塞 >60s → spigot.yml `timeout-time: 60` 杀服（GitHub #2562 实证）| timeout-time=60 |
| OOM | 官方公式：**1GB + 2GB×(方块数/千万)**（5000 万方块需 11G）| 本地测试服 **-Xmx2G** → 500 万方块就可能 OOM |
| 物理方块级联 | `//set` 沙/水/TNT → 方块更新级联刷实体 | 默认 disallowed 只防树苗/床类，**没防沙/水/岩浆** |
| undo 历史 | history.size=15，大操作存历史占内存 | -Xmx2G 雪上加霜 |

**不走 WE 的安全闸**：原版 `/fill` 单条 32768 硬限制 + Litematica 客户端 `commandLimitPerTick`/`commandTaskInterval` 速率双闸 → Watchdog/OOM 基本不会发生，剩余风险=连续命令流 TPS 假死（观感=崩服，进程实际存活，命令流跑完恢复）。

## 防护方案（2026-08-30 实施）

### 方案 A：编辑限额（config.yml limits）

```yaml
limits:
    max-blocks-changed:
        default: 1000000    # 原 -1 无限
        maximum: 2000000    # //limit 可调上限
```

**关键实测**：builder 权限组**没有 `worldedit.limit` 权限**（`//limit` 对 builder 显示 Unknown/被隐藏）→ 玩家无法调大 → **100 万就是实际硬上限**，maximum 只是给未来授权的上限。RCON 控制台可设更大（管理员特权，属预期）。

### 方案 B：物理方块禁用（disallowed-blocks 追加）

列表末尾（`minecraft:bedrock` 后）追加：
```yaml
    - "minecraft:sand"
    - "minecraft:red_sand"
    - "minecraft:gravel"
    - "minecraft:water"
    - "minecraft:lava"
```
TNT/fire **已在默认列表**（无需重复）。效果：`//set sand` 在**命令解析层**直接拒绝（`Invalid value for <pattern> (不允许方块"sand"（参见WorldEdit配置）)`）。

## 验证方法（本地实测通过的流程）

1. **限额生效**：RCON `//limit`（无参）→ 显示 `方块变更限制已设定成 1000000`（= default 生效）
2. **玩家无法调大**：mineflayer bot 登录 builder 账号 → `//limit 9999999` → `Unknown or incomplete command`（无 worldedit.limit 权限）
3. **物理方块拦截**：bot `//set sand` → 命令解析层拒绝（无需选区即验证）
4. **builder 正常**：bot `//wand` → 返回选区提示（权限正常）；`//set stone` → `Make a region selection first`（命令可识别）
5. **default 无权限**：default 组执行任何 WE 命令 → Unknown

### 测试账号快速搭建（2026-08-30 实测）

- RCON `whitelist add <名>` → bot 首登（自动 /register，密码 orztest2026）→ 退出 → RCON `lp user <名> parent set builder`（无回显正常）→ 等冷却 → 重进验证
- ⚠️ **防重登冷却**：GriefPrevention3D `Spam.LoginCooldownSeconds` 默认 60s，连续登录被踢 `You must wait X seconds before logging-in again` → 重试间隔 >60s
- ⚠️ 测试账号 `test`/`test1` 的密码**不是** orztest2026（历史账号），新账号最干净
- bot 脚本：`~/minecraft-bot/exec-cmds.js <名> <命令1> [命令2...]`（自动 register/login/执行/退出，打印聊天响应）
- ⚠️ WE `//pos1`/`//pos2` **不接受坐标参数**（`Usage: //pos2 [coordinates]`），选区必须木斧点击——命令解析层验证（//set sand）不需要选区

## 三端同步状态

| 端 | 状态 |
|:--|:--|
| 本地 Paper 实例（716c2fb7）| ✅ 已改 + 重启验证；2026-09-03 随迁移保留生效 |
| 本地 Folia 实例（8A932DD4）| ✅ 已同步（config.yml 复制，2026-09-03 随迁移生效）|
| Exaroton | ⏳ **未同步**（2026-09-10 巡检确认：`disallowed-blocks` 仍缺、限额仍 -1）→ 待同步配置 = `templates/worldedit-exa-config-tosync.yml`（2026-09-10 基于巡检拉取的 Exa 现配置**最小改动**重建：改 2 行限额 + 插 6 行方块；保留 Exa 端 `grass` 等版本差异不覆盖）。PUT 曾被 Cloudflare challenge 拦截 → 老板面板手动或风控解除 |
| MCSM | ✅ **已生效**（2026-09-10 巡检确认：限额 100万/200万 + sand/red_sand/gravel/water/lava 已加固）|

待同步/备份文件：`templates/worldedit-exa-config-tosync.yml`（exa 加固版）
⚠️ 原 `~/backups/we-config/`（local + exa 修改版）于 2026-09-10 清理备份时删除——**注意「备份目录里的文件不一定是纯备份，可能是待用产物（如待同步配置）」**，清理前须逐项核对用途与文档引用

## 玩家规范建议（未实施，需群公告）

1. Litematica 保持默认（**不开 commandUseWorldEdit**——wiki 明确不推荐，WE 命令 overhead 更大更慢且 block replace 行为不生效）
2. 大图分块粘贴；别调大 `commandLimitPerTick`
3. 粘贴时开 `pasteIgnoreEntities`；存投影前关红石/清流体
4. 若遇「服务器假死」：Spark 定位连续 /fill 玩家，等命令流跑完自动恢复
