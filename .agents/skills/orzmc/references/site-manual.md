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

## server-status 卡片的数据源（mcstatus.io）── 两个必须知道的坑

卡片数字来自 `api.mcstatus.io/v2/status/java/<host>`（渲染在 `static/js/server-status.js`）。
**它不是权威数据源**，排障时先怀疑上游而不是 CSS：

| 坑 | 机制 | 规则 |
|:--|:--|:--|
| MOTD 颜色被「量化」 | 上游把 JSON `text`/`color` 树压成 **16 色 legacy `§` 码**，MiniMessage 的逐字渐变（`<gradient:a:b>`）塌成 2 段，切点可能落在词中间，任何 CSS 都还原不回来 | 需要网页+游戏内都正常的文案，MOTD 用**单一 legacy 色**（如 `<gold>`）；渐变只留给只给游戏内看的行 |
| `version.protocol` 恒为 47 | 对本服（真实 762）、Paper 26.3、Hypixel 一律返回 47 —— 上游字段是假值 | 卡片只显示「类型 · 版本」两段，**不显示协议号**；缺版本就不渲染该段（`normalize()` 可留字段仅供排障） |

排障顺序：`mc_ping_probe.py <host> <port>` 拿服务端真实 JSON（递归打印 `text`/`color` 逐节点）→
`curl -s api.mcstatus.io/v2/status/java/<host>:<port>` 对比 `raw` → 两边不一致即上游量化，改 MOTD 源文案；
两边一致才回头查前端/样式。改动落在站点仓库（现为父仓 `site/` 子模块），合并 `main` 后 CI 自动发 Pages。

## 验收

- 本地 `hugo -d` 构建通过（页数无异常下降）
- 发布后 `orzmc.{SERVER_NAME}.cn/user/` 检查：状态卡片有数据、无 HTML 残留、移动端不横向溢出
