# 玩家手册（OrzMCSite）

> 官方站 `orzmc.{SERVER_NAME}.cn/user/` 的内容源 = 独立仓库 **OrzMCSite** 的 `content/user.md`。
> 从 SKILL.md 外置（2026-11-10 整理）。

## 维护链路

改手册 = 改 `user.md` → 单独 push `main` → CI 自动发布（Pages）；**主仓只 bump submodule 指针**（`git-submodule-sync.md`）。

- 本地预览用 **brew 版 Hugo**：`/usr/local/bin/hugo` → Cellar 0.165.0（`+extended+withdeploy` 已在 PATH）。
- `./preview` 用 `command -v hugo` 查路径（不要写死）。
- 2026-09-12 实测：`hugo -d` 构建通过（93 页产物）。
- 历史：`~/usr/local/bin/hugo` 是 brew 被 go pin 卡住时期的孤儿副本（119MB），2026-09-12 已清理。

## 内容结构（2026-08-15 合并的新手指南）

进服 3 步 / 基本操作 / 协作生态 / 四级权限成长 / 避坑 FAQ / 自定义皮肤。
服务器地址一律用 **server-status 组件动态卡片**，不写死 IP。

2026-08-30 发布四级玩家指南：四组各含职责 / 指令表 / ✅可做 / ❌不可做（独立小节 + bullet）/ 升级路径，与权限重规划（L0 23 / L1 19 / L2 35 / L3 37）联动。

## 两个必须遵守的写法

| 事项 | 正确 | 错误 |
|:--|:--|:--|
| 服务器状态卡片 | `{{< server-status tags="players" >}}`，`params.toml` 每台服配 `tags = ["players"]` / `["dev"]`（**单点维护**：名称/地址变化只改 params.toml，文档零改动） | 旧 `servers=` 参数——按 name/host 精确匹配，中文名带 emoji 匹配不上 → `servers:[]` 空数组、卡片空白；且名称/域名变化要改每篇文档 |
| 排版 | 纯 Markdown 列表 / 表格（移动端友好） | 裸 HTML（`<br>` 等）——Hugo 默认**静默省略 raw HTML**，不渲染也不报错 |

## 验收

- 本地 `hugo -d` 构建通过（页数无异常下降）
- 发布后 `orzmc.{SERVER_NAME}.cn/user/` 检查：状态卡片有数据、无 HTML 残留、移动端不横向溢出
