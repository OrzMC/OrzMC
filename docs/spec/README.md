# OrzMC 规范（`orzmc-spec` 雏形）

> **状态**：草案 `specVersion 0.1` ｜ **最后更新**：2026-10-13
> **落点**：父仓库 `docs/spec/`（决策 Q2：成熟稳定后再下沉独立仓库 `OrzMC/orzmc-spec`）。
> **定位**：语言无关的**产品规范**——定义「一个 `orzmc` 产品」的核心数据、行为契约与产品面契约。

---

## 1. 这个规范是什么

OrzMC 的工具产品（见 [`../product-architecture.md`](../product-architecture.md) §1.2）目标是
**一个 `orzmc`、CLI 与 GUI 两面、共用核心逻辑、可互相安装/打开**。本规范定义那个"核心逻辑"的
**语言无关契约**：

- **数据模型**：版本、下载、Java、路径、计划表的纯数据形状。
- **行为契约**：下载/校验/缓存/并行/启动等必须一致的行为。
- **产品面契约**：CLI 命令面、GUI 与 CLI 的互相安装/打开接口。
- **一致性样例**：黄金样例（golden fixtures），供各实现跨语言验证。

> 规范的**唯一目的**：让不同语言、不同平台的实现**行为一致**，且可被独立验证。

## 2. 原则

1. **规范不依赖实现**，实现必须可映射到规范；不把某语言的实现当成标准。
2. **语言无关**：以 Markdown + JSON 样例表达；稳定后再补 JSON Schema。
3. **可验证**：每个契约都有对应的一致性样例，实现跑样例即可证伪。
4. **最小**：只规范化"核心逻辑"；各产品面的差异化交互不进规范。
5. **版本化**：`specVersion` 独立演进，破坏性变更升 major。

## 3. 目录

| 文件 | 内容 | 状态 |
|:--|:--|:--|
| [`README.md`](README.md) | 本文件：定位、原则、目录、贡献方式 | 草案 |
| [`data-model.md`](data-model.md) | 核心数据模型 + 字段对照（Python ↔ Swift） | 草案 |
| [`behavior.md`](behavior.md) | 行为契约 B1–B11（缓存/并发/校验/路径/Java/启动/进度/非 TTY/错误） | 草案 |
| [`cli-surface.md`](cli-surface.md) | CLI 命令面契约（统一 Swift/Python 命令与参数） | 草案 |
| [`install-update.md`](install-update.md) | 安装 / 自升级 / 跨面安装（GUI↔CLI、双渠道兜底、补全） | 草案 |
| [`conformance.md`](conformance.md) | 一致性套件与黄金样例 | 草案 |
| [`fixtures/`](fixtures/README.md) | 黄金样例（`given→expect`）+ 快照 + schema + 运行器说明 | 草案 · 已落地 27 例 |

## 4. 实现映射（谁实现这份规范）

| 规范范围 | Python 实现 | Swift 实现 |
|:--|:--|:--|
| 数据模型 | `orzmc/domain/*`、`orzmc/core/*` | `OrzMCKit` `Game`/`Fabric` + `MojangAPI`/`PaperMC` |
| 行为契约 | `orzmc/services/*`、`orzmc/infra/*` | `Game` + `OrzSwiftKit` |
| CLI 面 | `orzmc-app`（typer） | `OrzMCKit` 的 `orzmc` 可执行 |
| GUI 面 | —（无） | `OrzMCApp`（SwiftUI） |
| 安装/自升级 | `orzmc/services/selfinstall.py`、`selfupdate.py`、`docs/install.sh|ps1` | App 安装器 + `OrzAppUpdater`（待对齐） |

## 5. 已知差异（规范要统一的靶子）

见 [`../product-architecture.md`](../product-architecture.md) 第 8 章。首当其冲：

- **根目录布局**：Python `versions/<v>/...` vs Swift `manifest/<v>/...` —— 规范选定唯一布局。
- **类型支持**：Python 客户端 `vanilla/fabric/forge`、服务端 `vanilla/paper/fabric/forge`；
  Swift 客户端 `vanilla/fabric`、服务端 `vanilla/paper`。
- **Java 获取**：Python 托管 JRE 到 `java/<major>/`；Swift 依赖外部 Java。
- **进度模型 / 缓存策略**：两边不同，规范统一。

## 6. 如何贡献 / 修改规范

1. 改规范前先读 [`../product-architecture.md`](../product-architecture.md) 与 `data-model.md`。
2. 任何规范变更**必须**同步对应的一致性样例（后续 `conformance.md`）。
3. 规范变更记录在 [`../product-unification-plan.md`](../product-unification-plan.md) 的变更记录，并同步 `HANDOFF.md`。
4. 未定项用 **`【待定】`** 显式标注，不要用实现细节"悄悄"充当标准。
