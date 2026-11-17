# OrzMC 权限系统设计（LuckPerms 4 组方案，2026-08-06 本地验证）

## ⚠️ gamemode 权限真值（2026-08-29 bot 实测确立，勿再猜）
- `/gamemode` 是 **Essentials 命令**：权限节点 `essentials.gamemode`（父=命令基础）+ **子权限独立**（`.creative`/`.survival`/`.spectator`/`.adventure` 各自判断，父权限**不含**子模式）
- 实测矩阵（bot 玩家身份，gamemode-test.js）：default 全拒 / builder = creative✅ survival✅ spectator❌ adventure❌ / admin = creative✅ survival✅ spectator✅（**需显式 `essentials.gamemode.spectator`**，2026-08-29 补，文档 permission-groups.md PR#229）adventure❌
- `minecraft.command.gamemode`/`bukkit.command.gamemode` 仅 admin 配（改他人模式；原版命令被 Paper 接管 /minecraft:gamemode Unknown）
- **限制普通玩家 = 不授予**（Essentials 默认拒绝）；**勿 default 显式 set false**（覆盖子组 true）
- 测试方法：`~/minecraft-bot/gamemode-test.js <玩家> <密码>`（bot 执行 /gamemode ×4，chat 反馈「将X设置为创造模式/你没有切换X模式的权限」判断）；临时换组用 `lp user X parent add/remove`（**勿用 parent set**——只剩 default 坑）+ 恢复
- **矫正场景**（2026-08-29 已落地，PR#230 四通道）：builder/admin 降级后 gamemode 残留（创造/观察不匹配）→ OrzMC 插件自动矫正。实现：GamemodeCorrectionService（权限推导零配置：CREATIVE/SPECTATOR/ADVENTURE 无对应 essentials.gamemode.* 权限 → 切 SURVIVAL；SPECTATOR 矫正前安全位置处理；compute 原子防抖）；**四通道**：①ReviewService 审核通过后 ②RankService 升降级后 ③LP UserPromoteEvent/DemoteEvent（track 事件，软依赖；**手动 lp parent 改组不触发**）④30s 周期扫描（覆盖手动改组）+ 登录兜底。⚠️ **Folia 实体操作线程红线**：所有通道经 correctAsync（player.getScheduler().execute 投递到玩家 region 线程），global 线程直接 setGameMode/teleport 在 Folia 抛异常（Review 发现 🔴）；EntityScheduler.execute 需 4 参（plugin, task, retired, delayTicks）。配置 config.yml gamemode-correction 段（/config set 可调）。bot 实测闭环：builder 切创造 → lp parent remove 降级 → 30s 内自动回生存+权限拒绝 ✅

## 组结构（继承链）
```
admin (全权限) → builder (创造建造) → member (进阶) → default (新手)
```

| 组 | 定位 | 关键权限 | 验证结果 |
|:--|:--|:--|:--|
| default | 新手生存 | sethome/home/back/spawn/tpa/msg/kit + griefprevention 圈地 | fly=false ✅ gamemode 拒绝 ✅ |
| member | 进阶 | +tpa/warp/kit/mail/getmehome 家 + playershop + GP 圈地 | 进阶功能 ✅ |
| builder | 创造建造 | +gamemode.creative/survival +worldedit 系列通配 +worldguard 区域 +**Litematica 粘贴（setblock/fill/data）** | gamemode=true ✅ worldedit=true ✅ |
| admin | 管理 | +luckperms.* +* | — |

## 关键命令
```bash
# 创建组 + 继承
lp creategroup <name>
lp group member parent add default
lp group builder parent add member
lp group admin parent add builder
# 权限设置（组）——以 perm_commands.txt / docs/permission-groups.md 为唯一参考
lp group builder permission set worldedit.selection.* true   # 系列通配（不用大通配 worldedit.*）
lp group builder permission set minecraft.command.setblock true   # Litematica 粘贴（2026-08-12）
# 全量对齐：lp group <G> permission clear + 逐条 set（permission set 是加法，不会移除旧节点）
# 玩家分配
lp user <name> parent add builder
lp user <name> parent set default
```

## ⚠️ 核心坑（实测 2026-08-06）
1. **LuckPerms 继承优先级：子组设置 > 父组设置，但同一权限在父子组都设时，查的是最具体的**。default 设 `fly false` + member 设 `fly true` → 玩家**继承 false**（default 赢了，因为"具体权限优先于通配"，且 LP 的 DirectProcessor 取**第一个匹配**）。**修正：default 不显式设 false**（Essentials 的 fly 默认拒绝，PermissionMapProcessor 返回 false），让 member 的 true 生效
2. **RCON 不回显 LuckPerms 命令输出**（LP 用 Adventure 组件发到 sender，Paper RCON 丢弃）——命令**实际执行**（H2 数据库 mtime 变化），但看不到输出。验证必须用 **bot 进服（玩家身份）** 或数据库
3. **LP 命令执行验证法**：`stat -f %m plugins/LuckPerms/luckperms-h2-v2.mv.db` 前后对比（mtime 变化 = 命令执行写库）
4. **H2 数据库读不了**（运行中被锁 + 文件密码），停服也读不了（未知密码）——别浪费时间，用 bot 验证
5. Essentials 大部分权限**默认拒绝**（非默认授予）——不设权限 = 无权限，`fly`/`gamemode` 都是
6. **⚠️ `parent set` 语法坑（实测）**：`lp user X parent set admin` 会把玩家**只保留 default 组**（set=替换为指定组，但 admin 没被正确加？实测结果是 X 只剩 default）。**正确用 `parent add` 追加 + `parent remove` 移除**：`lp user X parent add admin` + `lp user X parent remove default`
7. **⚠️ Bukkit `*` 通配符只对 OP 生效**：`lp group admin permission set * true` 不赋予非 OP 玩家全权限——OP 级命令（/kick /ban /stop）需要 `minecraft.command.*` 显式权限或玩家在 ops.json。admin 组实测：LP 管理命令（luckperms.*）✅，但 /gamemode 靠继承 builder 的 essentials.gamemode，/kick 需额外 `minecraft.command.kick`（**8-08 验收已确认**：admin 组显式配置 minecraft/bukkit.command.kick/ban 等，节点明细见仓库 `docs/permission-groups.md`）
8. **/gamemode 是 Essentials 命令**（需 `essentials.gamemode`），不是原版 `minecraft.command.gamemode`（Paper 上原版命令被接管，`/minecraft:gamemode` 会 Unknown）；**//wand 是双斜杠**（单斜杠 /wand 不存在）

## 测试账号分配（本地测试服）
- joker → builder（测试创造/WE/Litematica 粘贴）
- TestNewbie → builder（权限验收）
- TestPlayer → member（测试进阶功能）
- Newbie → default（新手基线）
- HermesBot → default（运维 bot，不用特权）
- **WeTestBot → 四组切换验证账号（2026-08-30 新增）**：`lp user WeTestBot parent set <组>` 切组 + bot 实测（RCON 发 LP 命令偶发丢，parent set 后必须 bot 实测命令确认切换；实测 `//limit` Unknown 确认无 worldedit.limit、`/speed` 确认 builder 权限等）；密码 orztest2026

## 验证方法（bot 玩家身份）
```bash
cd ~/minecraft-bot && node perm-check.js 25565
# 输出: [LP] Permission check for essentials.fly: Result: true/false
```
