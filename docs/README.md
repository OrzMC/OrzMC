# OrzMC 文档导航

> 父仓库（产品伞）的伞级文档总索引。按「读者角色 + 文档时效」组织。
> 每份文档头部标注「状态 / 最后更新」，先看状态再决定是否采信内容。
>
> **子模块文档不在此重复**——本索引给出入口，正文以各子模块仓库为准。

---

## 🧭 先读这些（所有人都需要）

| 文档 | 内容 | 位置 |
|:--|:--|:--|
| [README.md](../README.md) | 产品总览、目录结构、子项目一览 | 仓库根 |
| [AGENTS.md](../AGENTS.md) | **父仓库协作单一事实源**：仓库性质、三条铁律、子模块登记表、AI 协作流程 | 仓库根 |
| [HANDOFF.md](../HANDOFF.md) | **跨会话/跨设备交接文档**：当前焦点、状态快照、下一步、会话日志、待决策 | 仓库根 |
| [CONTRIBUTING.md](../CONTRIBUTING.md) | 人/机贡献指南：子模块工作流、提交规范、PR 流程 | 仓库根 |
| [LICENSE](../LICENSE) | 父仓库许可证（各子模块另有各自许可证） | 仓库根 |

---

## 📐 架构与方案（进行中）

| 文档 | 状态 | 内容 | 位置 |
|:--|:--|:--|:--|
| [product-architecture.md](product-architecture.md) | 现行 | **产品架构**：仓库角色地图、分层模型（L0 规范 / L1 引擎 / L2 前端 / L3 产品伞）、引擎六阶段、**允许依赖方向与禁止事项**、治理与已知差异 | docs/ |
| [product-unification-plan.md](product-unification-plan.md) | 草案 | 客户端/服务端工具（`python` × `app`）统一化推进计划：已核验事实、决策 D1–D9、Phase 0–5、开放问题、上下文包 | docs/ |
| [spec/README.md](spec/README.md) | 草案 | **语言无关规范**（`orzmc-spec` 雏形）：定位、原则、实现映射、已知差异 | docs/spec/ |
| [spec/data-model.md](spec/data-model.md) | 草案 | 核心数据模型（路径/版本/下载/Java/启动计划…）+ Python ↔ Swift 字段对照 | docs/spec/ |
| [spec/behavior.md](spec/behavior.md) | 草案 | 行为契约 B1–B11（缓存/并发/校验/路径/Java/启动/进度/非 TTY/错误） | docs/spec/ |
| [spec/cli-surface.md](spec/cli-surface.md) | 草案 | CLI 命令面契约：统一 Swift/Python 命令与参数、退出码、补全、迁移清单 | docs/spec/ |
| [spec/install-update.md](spec/install-update.md) | 草案 | 安装/自升级/跨面安装：无 sudo、Shell 自动识别、补全、GUI↔CLI 双渠道兜底 | docs/spec/ |
| [spec/conformance.md](spec/conformance.md) | 草案 | 一致性套件与黄金样例：fixture 格式、断言规则、覆盖矩阵、CI 接线 | docs/spec/ |
| [spec/fixtures/README.md](spec/fixtures/README.md) | 草案 | **黄金样例**（26 个 `given→expect`）+ 钉住快照 + 样例格式 schema | docs/spec/fixtures/ |
| [swift-conformance-design.md](swift-conformance-design.md) | 草案 | **Swift 引擎一致性设计**：能力地图、与规范差距、适配器设计、跨仓库改造清单与顺序 | docs/ |

---

## 🧩 子模块入口（按领域）

> 每个子模块有自己的文档体系。改某子模块前，**先读它的 `AGENTS.md`**（若有）。

### 服务器核心
| 子模块 | 一句话职责 | 文档入口 |
|:--|:--|:--|
| [`plugin`](../plugin) | PaperMC 核心插件 | [README](../plugin/README.md) · [AGENTS](../plugin/AGENTS.md) · [架构](../plugin/docs/architecture.md) · [文档索引](../plugin/docs/README.md) |

### 玩家端
| 子模块 | 一句话职责 | 文档入口 |
|:--|:--|:--|
| [`python`](../python) | `orzmc` CLI：客户端启动 / 服务端部署 | [README](../python/README.md) · [AGENTS](../python/AGENTS.md) |
| [`app`](../app) | macOS/iOS 启动器（SwiftUI） | [README](../app/README.md) · [项目文档](https://orzmc.github.io/OrzMCApp/) |
| [`OrzMCKit`](../OrzMCKit) | **Swift 引擎**（`Game`/`Fabric`）+ `orzmc` CLI | [README](../OrzMCKit/README.md) |
| [`webmc`](../webmc) | 浏览器连服实验 | [目录](../webmc) |

### 网络与部署
| 子模块 | 一句话职责 | 文档入口 |
|:--|:--|:--|
| [`proxy`](../proxy) | FRP 跨运营商中转 | [README](../proxy/README.md) · [架构](../proxy/docs/architecture.md) · [部署手册](../proxy/docs/setup-guide.md) |
| [`deploy`](../deploy) | Docker Compose 部署 | [README](../deploy/README.md) · [AGENTS](../deploy/AGENTS.md) · [架构/ADR](../deploy/docs/architecture.md) · [使用指南](../deploy/docs/usage.md) |

### 运维工具
| 子模块 | 一句话职责 | 文档入口 |
|:--|:--|:--|
| [`tools/OrzMCBackup`](../tools/OrzMCBackup) | 世界优化与备份（CLI + 库） | [README](../tools/OrzMCBackup/README.md) · [AGENTS](../tools/OrzMCBackup/AGENTS.md) |
| [`tools/rust-thanos`](../tools/rust-thanos) | Rust 区块清理 | [README](../tools/rust-thanos/README.md) · [AGENTS](../tools/rust-thanos/AGENTS.md) |
| [`tools/thanos`](../tools/thanos) | PHP 区块清理（**上游**） | [README](../tools/thanos/README.md) |

### 游戏内插件（工具集）
| 子模块 | 一句话职责 | 文档入口 |
|:--|:--|:--|
| [`tools/EzShops`](../tools/EzShops) | 商店插件（派生） | [README](../tools/EzShops/README.md) · [AGENTS](../tools/EzShops/AGENTS.md) |
| [`tools/GetMeHome`](../tools/GetMeHome) | 家的传送（派生） | [README](../tools/GetMeHome/README.md) |
| [`tools/LoginSecurity`](../tools/LoginSecurity) | 登录认证（派生） | [README](../tools/LoginSecurity/README.md) |
| [`tools/DeathChest`](../tools/DeathChest) | 死亡掉落箱子（派生） | [目录](../tools/DeathChest) |

### 站点与组织
| 子模块 | 一句话职责 | 文档入口 |
|:--|:--|:--|
| [`site`](../site) | 官方 Hugo 网站 | [README](../site/README.md) · [AGENTS](../site/AGENTS.md) |
| [`profile`](../profile) | GitHub 组织主页 | [目录](../profile) |

---

## 🗂️ 其它父仓库内容

| 路径 | 内容 |
|:--|:--|
| [`scripts/`](../scripts) | 服务器运维脚本（crontab / raspberrypi / rsync / ubuntu） |
| [`scripts/conformance/`](../scripts/conformance/README.md) | **一致性运行器** `run.py` + 规范参考适配器 `reference.py`（语言无关） |
| [`images/`](../images) | README 引用图片 |
| [`skins/`](../skins) | Minecraft 玩家皮肤 |

---

## 维护约定

- 新增父仓库文档 → 加入本索引，并按读者角色归类。
- 文档头部标「状态 / 最后更新」；状态建议用：`草案` / `现行` / `已归档`。
- AI 指引只维护 `AGENTS.md`（pi / Codex 读取）；`CLAUDE.md` 是 Claude 的桥接，不写内容。
- 子模块文档不在本仓库复制；本索引只给入口。
