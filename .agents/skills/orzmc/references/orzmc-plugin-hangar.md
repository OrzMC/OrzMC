# OrzMC 插件版本渠道与升级（2026-08-04 实测，本地测试服）

## 版本号体系
- 格式：`主.补丁-[dev|pr].[构建号]`（如 `1.0.14-dev.237`、`1.0.13-pr.153.394`）
- `dev` = main 分支每日自动构建（GitHub Actions Publish workflow，一天可发多个）
- `pr` = PR 构建（如 pr.153 = PR #153）
- jar 内 `paper-plugin.yml`（**不是 plugin.yml**，Paper 插件格式）的 `version` 字段是主版本号（如 1.0.14），不带 dev/pr 后缀

## 发布渠道对比（2026-08-04）
| 渠道 | 状态 | 说明 |
|:--|:--|:--|
| **Hangar** | ✅ 活跃 | 每日自动发布 dev 版，GitHub Actions「publish to Hangar」成功 |
| GitHub Release | ⚠️ 滞后 | 手动 tag 才出，停在 1.0.12 |
| Modrinth | ❌ 失败 | gradlew modrinth 报 `TaskModrinthUpload` 异常，搜索不到项目 |

## Hangar API（查版本/拿下载链接）
```bash
# 版本列表（按时间倒序）
curl -s "https://hangar.papermc.io/api/v1/projects/OrzMC/versions?limit=10" | jq -r '.result[] | .name + " | " + (.createdAt[0:10])'
# 单版本详情 → 下载链接
curl -s "https://hangar.papermc.io/api/v1/projects/OrzMC/versions/1.0.14-dev.237" | jq -r '.downloads[].downloadUrl'
# 下载链接格式
# https://hangarcdn.papermc.io/plugins/OrzMC/OrzMC/versions/<版本>/PAPER/<jar名>.jar
```

## 本地升级流程（papermc-test，2026-08-04 实测 1.0.13→1.0.14）
<!-- ⚠️ 2026-09-03 注：文中本地测试服目录路径为迁 MCSM 前状态；现行路径见 testing.md（实例 InstanceData/<uuid>）-->

> ⚠️ **必须分清两条路径（PaperMC 官方机制，用户 2026-08-04 纠正）**：
> - 🆕 **首次新装** → jar **直接放 `plugins/`**（重启扫描加载；放 update/ 无效/非标准）
> - 🔄 **已有插件升级** → 新 jar 放 `plugins/update/` → 重启自动原子替换 → update/ 自动清空

```bash
# 升级已有插件（官方 plugins/update 机制）：
# 1. 下载新 jar 到 /tmp，unzip -p <jar> paper-plugin.yml | head -4 校验版本
# 2. ⚠️ 先删 plugins/ 下旧 jar（update 按【文件名】覆盖：带版本号 jar 新旧文件名不同
#    → 不覆盖 → 重启后新旧两个 jar 并存冲突）
rm plugins/OrzMC-1.0.13-pr.153.394.jar
# 3. 新 jar 放 plugins/update/
mv /tmp/OrzMC-1.0.14-dev.237.jar plugins/update/
# 4. 重启（./start.sh）→ PaperMC 自动替换 + update/ 自动清空
# 5. grep -iE "OrzMC" logs/latest.log 验证 `Loading server plugin OrzMC v<版本>`
```

- 三端差异：本地可不停服放 update/（重启时应用）；MCSM 运行中可上传 update/（jar 上传不触发锁定），玩家下线后 restart 自动替换；Exaroton 运行中禁写文件须先 stop
- 配置目录（plugins/OrzMC/ 下 config.yml 等）自动保留，无需迁移

## 注意
- 升级前先确认「哪端新」：本地测试服装的是 pr 构建（如 1.0.13-pr.153.394），Hangar 上可能已有更新的 dev 版——查 Hangar 版本列表对比，别默认本地就是最新
- 三端对齐（local/Exaroton/MCSM）的插件基线维护在 `orzmc` 技能 SKILL.md「关键事实」（该技能用户所有，更新需 `hermes curator adopt` 后由前台会话操作）
