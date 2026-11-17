# OrzMCAdmin

Minecraft 运维**统一 AI 技能包**（技能名 `orzmc`）——丢给任何 AI Agent（Claude Code / Hermes / OpenClaw / Cursor 等）即可处理 Minecraft Paper 服务器全部运维工作。

> **一个入口覆盖全部 MC 运维场景**：服务器运维 / 插件构建升级 / 性能诊断 / 权限体系 / 测试 / 基岩支持，45 个知识体系 + 29 个脚本。

## 能力全景

### 🖥 服务器运维（三后端统一动作）
- ✅ 服务器创建 / 状态 / 启动 / 停止 / 重启 / 日志 / 命令
- ✅ PaperMC 核心升级（fill-data 新机制 + sha256 校验）
- ✅ 插件安装 / 更新（plugins/update 热更新）/ 卸载
- ✅ 备份（world + plugins + 配置）
- ✅ 多服务器配置对齐（语义级 diff）与插件版本一致性（sha256 对比）
- ✅ MCSManager 文件 API 全集（12/12 端点实测）

### 🔧 插件构建与升级
- ✅ 源码构建（Gradle/Maven 工具选择、构建坑、shaded 产物）
- ✅ 插件升级与配置迁移（三端范式：本地→Exaroton→MCSM）
- ✅ 自维护插件修复（本地化/上游 bug 修复）+ PR 提交流程

### 📊 诊断与排障
- ✅ Spark 性能分析（五步法、实体审计、Aikar Flags、修复方案）
- ✅ 插件 Bug 排查（本地复现、命令/权限分离、版本兼容矩阵）
- ✅ 实体/传送门行为（事件继承、白名单策略）

### 🔐 权限体系（LuckPerms）
- ✅ LP API 集成（track 升降级、AMBIGUOUS_CALL 排障、saveUser 落库）
- ✅ 权限审计验收（权限名核实、子权限陷阱、bot 实测验收）
- ✅ 三端权限同步（perm_commands.txt 蓝本）
- ✅ 装即用 Bootstrap（自动建 track/组，幂等校正）

### 🧪 测试体系
- ✅ E2E 自动化测试（测试分层原则、三大通道：RCON/orzdebug/Mineflayer）
- ✅ 跨服 transfer 测试（双服搭建、传送门机制）
- ✅ Paper 26 踩坑全集

### 🎮 专项
- ✅ 基岩版支持（Geyser，版本兼容排查）
- ✅ 机器人玩家（Mineflayer bot，玩家身份操作）
- ✅ DeathChest 回归测试

## 目录结构

```
OrzMCAdmin/
├── SKILL.md                  # 技能主文件（frontmatter + 决策路由 + 操作步骤）
├── references/               # 45 个知识体系（按专注方向沉淀）
│   ├── local/exaroton/mcsm-backend.md   # 三后端 API 表
│   ├── plugin-build.md       # 插件源码构建/开发/发布
│   ├── plugin-mgmt.md        # 插件升级/配置迁移
│   ├── performance.md        # Spark 性能诊断
│   ├── plugin-debugging.md   # 插件 Bug 排查
│   ├── testing.md            # E2E + 跨服测试
│   ├── permission.md         # LuckPerms 权限体系
│   ├── entity-portal.md      # 实体/传送门
│   ├── geyser-floodgate.md   # 基岩支持
│   ├── mineflayer-bot.md     # 机器人玩家
│   └── ...（共 45 个）
├── scripts/                  # 29 个工具
│   ├── adapters/             # 三后端适配器（local.sh / exaroton.sh / mcsm.sh）
│   ├── cmp3/                 # 多服务器配置对比/同步/文件操作
│   ├── rcon.py / rcon.js     # RCON 客户端
│   ├── regression-loop.sh    # 多轮回归
│   ├── mcsm_entity_audit.py  # 实体审计
│   └── ...
├── templates/                # 模板（migrate_keys.py / mineflayer bot 等）
└── sync.sh                   # 一键同步（本地 orzmc skill → 本仓库，自动脱敏）
```

## 使用方式（AI Agent）

```bash
# 加载技能
skill_view(name='orzmc')

# 三端统一操作（环境变量选后端）
PAPER_BACKEND=local  PAPER_DIR=~/minecraft-server  scripts/adapters/local.sh status
PAPER_BACKEND=exaroton EXAROTON_API_KEY=$KEY EXAROTON_SERVER_ID=$ID scripts/adapters/exaroton.sh status
PAPER_BACKEND=mcsm  MCSM_URL=$URL MCSM_API_KEY=$KEY MCSM_INSTANCE_ID=$ID scripts/adapters/mcsm.sh status
```

凭据约定：全部从 `~/.hermes/.env` 读取（`scripts/cmp3/mcsm_env.py` 共享模块），**禁止硬编码 API key**。脚本默认值已参数化（`{SERVER_HOST}` / `{BOT_PASSWORD}` 等占位符）。

## 同步与维护

- `sync.sh` 一键把本地完整版技能同步到本仓库（自动脱敏私有信息）
- 同步前必须检查：私有域名/密码/邮箱/局域网 IP 已全部占位符化

## 兼容性

- 平台：macOS / Linux
- 技能格式：Claude Skills / OpenClaw / Hermes / Cursor 通用（frontmatter + markdown + scripts/）
- License: MIT
