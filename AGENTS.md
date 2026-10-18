# AGENTS.md — OrzMC 父仓库（产品伞）统一 AI 协作指引

> **本文件是父仓库 AI 指引的单一事实源**（AGENTS.md 开放标准）。
> 本组织主要使用 **pi / Codex / Claude**：**pi 与 Codex 直接读取本文件**，
> **Claude 读取 `CLAUDE.md`**（它 `@` 引入本文件）。因此只需维护 `AGENTS.md` 与薄桥接的
> `CLAUDE.md`；新增/修改指引**只改本文件**，`CLAUDE.md` 不写内容。
>
> 各子模块拥有**自己的** `AGENTS.md`，是本文件的下层事实源。改某个子模块前，
> **先读该子模块的 `AGENTS.md`**，冲突时以子模块的为准（它更贴近代码）。
>
> **接手/恢复工作时，先读 [`HANDOFF.md`](HANDOFF.md)**（跨会话/跨设备交接文档，记录
> 「现在到哪了、下一步做什么」）。本文件讲**规则**，`HANDOFF.md` 讲**状态**，`docs/` 讲**方案**。

---

## 1. 这个仓库是什么

**聚合型 monorepo / 产品伞**，本身几乎不含业务代码：

- 通过 **Git 子模块（submodule）** 汇集 21 个独立仓库（插件 / CLI / Swift（`swift/app` + `swift/lib/*`）/ 部署 / 中转 / 官网 / 工具集 / 组织主页）。
- 父仓库的职责只有三件事：
  1. **锁定版本**：记录各子模块的 commit 指针，对同一套产品定义一个可复现的组合。
  2. **承载伞级内容**：`README.md`、`docs/`、`scripts/`、`images/`、`skins/`、`LICENSE`。
  3. **协调跨仓方案**：如产品统一化（见 [`docs/product-unification-plan.md`](docs/product-unification-plan.md)）。
- **代码改动发生在子模块仓库里，不在父仓库。** 父仓库里你看到的所有子模块目录都是"挂载点"。

> 一句话铁律：**父仓库 bump 指针，子模块改代码。**

---

## 2. 三条不可破坏的铁律

### 铁律 1：代码改动进子模块，父仓库只 bump 指针

- 想改功能/修 bug → 进入对应子模块目录，在**子模块自己的仓库**里开分支、改代码、提 PR。
- 改完并合并后，回到父仓库把子模块指针**向上 bump**，作为一次 `chore(submodule): ...` 提交。
- **禁止**在父仓库里 `git add plugin/src/...` 这类操作——子模块内部文件由子模块仓库管理，
  父仓库只记录它的 HEAD commit。

### 铁律 2：改哪个子模块，先读哪个子模块的 AGENTS.md

- 子模块的构建命令、架构红线、分支模型**各不相同**（如 plugin 提交进 `develop`，python/site 进 `main`）。
- 有 `AGENTS.md` 的：`plugin` / `deploy` / `python` / `site` / `tools/EzShops` /
  `tools/OrzMCBackup` / `tools/rust-thanos`。没有的按该子模块 `README.md` / `CONTRIBUTING.md` 行事。
- 父仓库的规则是**下限**，子模块的规则是**上限**——两者都要满足。

### 铁律 3：子模块指针必须显式提交，且一次提交只 bump 一个子模块

- 子模块 HEAD 变化后，父仓库会出现"已修改内容"（`git status` 里子模块前有 `M`）。
  必须 `git add <子模块路径>` 再提交，否则指针漂移不会被记录。
- 现状惯例：**一次提交只 bump 一个子模块**，提交信息写清 bump 到了什么版本/里程碑。
  这样历史可读、可回滚。
- 提交前用 `git submodule status` 确认指针，用 `git diff --submodule` 查看子模块内部差异摘要。

---

## 3. AI 协作主流程

### 场景 A：把某个子模块更新到远端最新（最常见）

```bash
# 0. 确认子模块已初始化（首次或换机）
git submodule update --init --recursive

cd <子模块路径>                 # 如 plugin
git fetch origin
git switch <目标分支>            # 各子模块默认分支不同，见第 4 章登记表
git pull --ff-only

cd -                            # 回父仓库
git add <子模块路径>
git commit -m "chore(submodule): bump <名称> 指针到 <分支> 最新（<一句话说明>）"
```

> 现状提交信息样例：
> `chore(submodule): bump plugin 指针到 main 最新（1.0.29 正式版已发布 + 版本推进 1.0.30）`

### 场景 B：修改子模块的代码 / 文档

```bash
cd <子模块路径>
git switch -c feat/<主题>        # 或 fix/<主题>；分支模型以子模块 AGENTS.md 为准
# …按该子模块的 AGENTS.md / CONTRIBUTING.md 改代码、跑门禁、提交…
git push -u origin feat/<主题>
# 到该子模块的 GitHub 仓库开 PR → 走它自己的 CI → 合并
cd -
# 合并后在父仓库 bump 指针（同场景 A）
```

- **跨子模块改动**（如同时改 plugin 与 deploy）：分别在各自仓库开 PR，在父仓库用**一次 bump 提交**
  或**多个独立 bump 提交**记录；在提交信息里写清这次产品级变更涉及哪些子模块。

### 场景 C：只改父仓库自有内容（文档 / 脚本 / README）

```bash
# 直接改 docs/ scripts/ README.md images/ skins/ 等，不涉及子模块
git add docs/README.md
git commit -m "docs: ..."
```

---

## 4. 子模块登记表

> `性质`：**自研**=组织自有主仓；**派生**=组织内 fork，可自维护但注意与上游的差异；
> **上游**=外部主仓库引用，改动以上游为准、**不要在本地随意改**。
> `默认分支` 以 `.gitmodules` 的 `branch` 为准；未声明时按各仓实际默认分支（多为 `main`/`master`）。

| 路径 | 仓库 | 默认分支 | 性质 | 一句话职责 | 子模块 AGENTS |
|---|---|---|---|:--|:--|
| `plugin` | `OrzMC/OrzMCPlugin` | `main`（开发用 `develop`） | 自研 | PaperMC 核心插件（白名单/机器人/权限/维护） | ✅ |
| `python` | `OrzMC/OrzPythonMC` | `main` | 自研 | `orzmc` CLI：客户端启动 / 服务端部署 | ✅ |
| `swift/app` | `OrzMC/OrzMCApp` | `main` | 自研 | macOS/iOS 启动器（SwiftUI；引擎见 `swift/lib/OrzMCKit`） | — |
| `swift/lib/OrzMCKit` | `OrzMC/OrzMCKit` | `main` | 自研 | Swift 引擎（`Game`/`Fabric`）+ `orzmc` CLI | — |
| `swift/lib/MojangAPI` | `OrzMC/MojangAPI` | `main` | 自研 | Mojang 元数据（清单 / version JSON / assets） | — |
| `swift/lib/PaperMC` | `OrzMC/PaperMC` | `main` | 自研 | Paper 下载 / Hangar API | — |
| `swift/lib/ExarotonAPI` | `OrzMC/ExarotonAPI` | `main` | 自研 | Exaroton API 客户端 | — |
| `swift/lib/OrzSwiftKit` | `OrzGeeker/OrzSwiftKit` | `main` | 自研 | Swift 基础设施（`JokerKits`/`CacheKit`/`RuntimeKit`/`TransferKit`；外部组织 OrzGeeker，维护者自有） | — |
| `swift/lib/OrzAppUpdater` | `OrzGeeker/OrzAppUpdater` | `main` | 自研 | app 自升级（Sparkle 封装；外部组织 OrzGeeker，维护者自有） | — |
| `deploy` | `OrzMC/OrzMCDeploy` | `main` | 自研 | Docker Compose 部署（MCSManager/EasyBot/MariaDB/Gatus） | ✅ |
| `proxy` | `OrzMC/OrzMCProxy` | `main` | 自研 | FRP 跨运营商中转方案 | — |
| `site` | `OrzMC/OrzMCSite` | `main` | 自研 | Hugo 官方网站（GitHub Pages） | ✅ |
| `webmc` | `OrzMC/OrzWebMC` | `main` | 自研 | 浏览器连服实验 | — |
| `profile` | `OrzMC/.github` | `main` | 自研 | GitHub 组织主页 profile | — |
| `tools/OrzMCBackup` | `OrzMC/OrzMCBackup` | `main` | 自研 | 世界优化与备份（CLI + Kotlin/Java 库） | ✅ |
| `tools/rust-thanos` | `OrzMC/rust-thanos` | `main` | 自研 | Rust 版区块清理（对齐 OrzMCBackup） | ✅ |
| `tools/DeathChest` | `OrzMC/death-chest` | `main` | 派生 | 死亡掉落箱子插件 | — |
| `tools/EzShops` | `OrzMC/EzShops` | `main` | 派生 | 商店插件（上游 ez-plugins） | ✅ |
| `tools/GetMeHome` | `OrzMC/GetMeHome` | `main` | 派生 | 家的传送插件 | — |
| `tools/LoginSecurity` | `OrzMC/LoginSecurity` | `master` | 派生 | 登录认证插件（上游 lenis0012） | — |
| `tools/thanos` | `aternosorg/thanos` | `master` | 上游 | PHP 区块清理库（**外部主仓，勿本地改**） | — |

**完整 URL / 分支以 `.gitmodules` 为准**；本表漂移时以 `.gitmodules` 为准并回来修正本表。

---

## 5. 子模块通用操作与陷阱

```bash
# 首次克隆（父仓库）
git clone --recurse-submodules https://github.com/OrzMC/OrzMC.git

# 已克隆但子模块为空
git submodule update --init --recursive

# 一次性把所有子模块拉到 .gitmodules 记录的分支最新（谨慎，会移动多个指针）
git submodule foreach 'git fetch origin && git switch <branch> && git pull --ff-only'

# 查看每个子模块当前指针
git submodule status

# 查看某子模块相对父仓库记录的差异摘要
git diff --submodule <路径>
```

**常见陷阱**

- **detached HEAD**：`git submodule update` 后子模块常处于 detached HEAD。要改代码前先
  `git switch <分支>`，否则提交会"悬空"、推送后父仓库指针无法追踪。
- **忘记提交子模块指针**：在子模块里 commit 了但父仓库没 `git add`，等于这次变更没进产品组合。
- **误改上游**：`tools/thanos` 是外部上游仓库。若确需改动，应先 fork 到 `OrzMC/` 再改 `.gitmodules`，
  不要直接向上游推。
- **不要用 `git add -A` / `git add .`**：会把**所有**子模块的指针变更一并暂存（例如 `plugin` 本地在 `develop`、
  父仓库却应钉 `main`），造成误 bump。改父仓库自有内容时始终 **显式 `git add <路径>`**。
  （历史上真踩过：一次 `git add -A` 误把 `plugin` 的 `develop` 记录进了父仓库。）
- **分支同名不同义**：父仓库 `.gitmodules` 的 `branch` 只影响 `submodule update --remote`，
  不代表子模块的默认分支/开发分支。以各子模块 AGENTS/CONTRIBUTING 为准。

---

## 6. 父仓库自有内容

父仓库**真正直接管理**的只有这些路径，改动规则如下：

| 路径 | 内容 | 规则 |
|---|---|---|
| `README.md` | 产品总览与目录结构 | 改动同步 `docs/README.md` 索引 |
| `AGENTS.md` / `CLAUDE.md` | AI 协作指引（`AGENTS.md` 为源） | 只改 `AGENTS.md`；`CLAUDE.md` 是 Claude 桥接，不写内容 |
| `CONTRIBUTING.md` | 人/机贡献指南 | 流程变化时同步 |
| `docs/` | 伞级文档与进行中的方案 | 每份文档头部标「状态 / 最后更新」；索引进 `docs/README.md` |
| `scripts/` | 服务器运维脚本 + 校验/一致性工具 + 本地联调（`verify/`、`conformance/`、`release/`、`swift-dev.sh`） | 生产脚本改动需谨慎并说明 |
| `images/` / `skins/` | README 图片 / 玩家皮肤 | 资源类，避免无谓重编码 |
| `LICENSE` | 许可证 | **不要改**（子项目各自许可证见其仓库） |

**该放进子模块、而非父仓库的内容**：任何可构建产物、业务逻辑、子项目配置、子项目 CI、
会被独立发布的代码——一律进对应子模块。

---

## 7. 提交与协作规范

- **提交信息：Conventional Commits + 中文描述**（与各子模块一致）。
  - 子模块指针：`chore(submodule): bump <名称> 指针到 <分支> 最新（说明）`
  - 文档：`docs: ...`；父仓库脚本/杂项：`chore: ...` / `fix: ...`
- **一次提交一个子模块**（现状惯例，便于审查与回滚）。
- **不写无信息量的提交**（如 "update"）；说明"为什么 bump / 改了什么"。
- **发版列车**：父仓库是产品组合的锚点。跨子模块的一次产品级变更，记入 [`RELEASES.md`](RELEASES.md)
  （用 `python3 scripts/release/composition.py` 生成基准组合表）。
- **发版须知要面向用户**：任何**需要用户手动处理**的变更（自升级/安装器自身的 bug、破坏性变更、
  迁移、需改环境、已知问题与 workaround），发版时必须写入该子模块**对应版本的 `CHANGELOG.md`**
  **和** GitHub Release notes —— release-please 只渲染 commit 列表，**不会替你说“用户该怎么办”**。
  写法与同步命令见 [`python/CONTRIBUTING.md`](python/CONTRIBUTING.md) 的「升级须知」节；`orzmc 2.9.1` 是首个例子。

### 7.1 依赖仓库协作（自有仓库可直接改）

- 父仓库聚合的 21 个子模块，以及各模块的 SwiftPM 依赖（`OrzMC/MojangAPI`、`OrzMC/PaperMC`、
  `OrzMC/ExarotonAPI`、`OrzGeeker/OrzSwiftKit`、`OrzGeeker/OrzAppUpdater` 等）**均属维护者自有**。
- **必要时可直接把依赖仓库拉到本地修改**（clone → 改 → 各自仓库提交/PR → 上层 bump 指针），
  目标始终是**全局最优**：让各模块**能力划分清晰、彼此配合完成功能**，而不是局部将就或重复实现。
- 仍然遵守第 2 章铁律：改动发生在各自仓库、父仓库只 bump 指针、一次提交只 bump 一个子模块。
- 跨仓库的产品级变更，在提交信息 / [`HANDOFF.md`](HANDOFF.md) 中记清涉及哪些仓库与版本。

---

## 8. 构建与验证

- 父仓库**（可选）组合校验**：`python3 scripts/verify/check.py`（登记表与 `.gitmodules` 一致性 +
  一致性参考自检），已接父仓库 CI（`.github/workflows/ci.yml`）；`--remote` 追加远端指针存在性检查。
- 质量门禁在**各子模块内部**（业务构建/测试）：
  - `plugin` → `./gradlew check`
  - `python` → `ruff` / `mypy` / `pytest` / `uv build`
  - `site` → `./preview` / `./deploy -n`
  - `deploy` → `./orzmc.sh -e local init && ./orzmc.sh validate`
  - 其余见各自 `AGENTS.md` / `README.md`
- 父仓库的"验证"= 组合正确性：
  ```bash
  git submodule status          # 指针与预期一致
  git status --porcelain        # 工作区无意外未提交的子模块变更
  ```
- 子模块指针要指向**已存在于远端的分支/提交**（不要在子模块里留本地未推送的提交就 bump 父仓库）。

### 8.1 远程真机验证（Windows）

需要 Windows 平台实测（路径分隔 / `java.exe` / PATH / 补全 / `install.ps1` / 下载与启动）时，
通过 SSH 登录 Windows 真机执行。

| 项 | 值 |
|---|---|
| SSH 主机 | `win`（`WangA@192.168.0.33`，免密 key） |
| 默认 shell | **PowerShell**（不是 cmd；命令里的 `&` 会被当作后台运算符） |
| **收敛工作根** | **`E:\orzmc-verify\`**（子目录 `bin/` `minecraft/` `tmp/` `logs/`） |
| 清理 | `scripts/win/run.sh -c 'Remove-Item -Recurse -Force E:\orzmc-verify'` |

- **统一用 [`scripts/win/run.sh`](scripts/win/run.sh)** 执行（自动 `-EncodedCommand`，规避 bash→ssh→PowerShell 的引号与 `&` 陷阱）：
  ```bash
  scripts/win/run.sh -c 'Get-PSDrive E | Select-Object Used,Free'
  scripts/win/run.sh -f scripts/win/foo.ps1
  ```
- **产物一律放在 `E:\orzmc-verify\` 下**，不要散落到 `E:\` 根或系统目录，方便后续一次性清理。
- ⚠️ **`E:\orzmc` 是生产部署目录**（caddy / cloudflared / database / mcsmanager）——**绝对不要动**。
- 真机验证的结论/关键命令记入 [`HANDOFF.md`](HANDOFF.md)。

---

### 8.2 远端构建（`ssh air`）

本机（macOS 13 + CLT 13.3 + 剩余磁盘 <10GB）**无法全量构建** Swift 包（依赖要 macOS 14+ SDK），
Swift 相关的编译/测试/验收一律在 **`air`** 上做（Apple Silicon M1 / 8 核 / Swift 6.4 / SDK 27）。

| 项 | 值 |
|---|---|
| SSH 主机 | `air`（`joker@192.168.0.26`，免密 key，**arm64**） |
| 远端工作目录 | `~/orzmc-build/OrzMCKit`（`rsync --delete`，`.build` 保留 → 增量构建） |
| 统一入口 | **[`scripts/air/run.sh`](scripts/air/run.sh)** |

```bash
scripts/air/run.sh env            # 远端自检（swift / SDK / CPU / 磁盘）
scripts/air/run.sh build          # 同步 + swift build --product orzmc   ~25s（增量）
scripts/air/run.sh test           # 同步 + swift test（90+ 例）           ~25s
scripts/air/run.sh accept         # 同步 + release 构建 + CLI 验收 20 例   ~1m30s
scripts/air/run.sh all            # 三者全跑
scripts/air/run.sh sh '<cmd>'     # 远端自定义命令
```

- **改依赖仓库时**（`MojangAPI` / `PaperMC` / `OrzSwiftKit`）加 `ORZMC_LOCAL_DEPS=1`：脚本会把本地
  工作树同步过去并把**远端副本**的 `Package.swift` 改成 path 依赖（不改仓库、不要求先 push）。
- 依赖是 `branch: main`，默认用 `Package.resolved` 离线解析（`--only-use-versions-from-resolved-file`）；
  要拉依赖最新时用 `ORZMC_UPDATE_DEPS=1`。
- `air` 会休眠：`ssh` 连不上时先唤醒机器（本机 `ssh air true` 报 `This system is locked` 即此因）。
- 本机仍保留**秒级/分钟级**轻量检查：`swift/lib/OrzMCKit/scripts/dev/local-build.sh lint|check`
  （跨平台静态检查 1s、语法检查 50s）。

---

## 9. 进行中的计划与状态

- [`HANDOFF.md`](HANDOFF.md) —— **跨会话/跨设备交接文档**：当前焦点、状态快照、下一步、
  会话日志、待决策。每次会话结束前更新它。
- [`docs/product-unification-plan.md`](docs/product-unification-plan.md) —— 客户端/服务端工具
  （`python` 与 `app`）统一化：一份规范 + 多套实现 + 多个前端 + 一个产品伞。**推进前先读该文件**，
  它记录了已核验事实、决策 D1–D6、Phase 0–5、开放问题与上下文包。

---

## 10. 多智能体协作约定

- **单一事实源**：本文件是父仓库规则的源；子模块各自的 `AGENTS.md` 是其内部规则的源。
  改任意指引只改源文件，`CLAUDE.md`（Claude 桥接）不写内容。
- **交叉审查**：重要改动（尤其跨子模块/架构级）建议换一个厂商的 agent 交叉审查，
  或本地用 `/review` 自查后再提 PR。
- **上下文卫生**：接手任务时先读本文件 → 对应子模块 `AGENTS.md` → 该子模块 `docs/`；
  不要把父仓库所有子模块全量扫描一遍。
- **不要替维护者做决定**：涉及叉子仓库/上游仓库、许可证、发版的判断，先问再动。

---

## 11. 文档导航

- 跨会话/跨设备交接：[`HANDOFF.md`](HANDOFF.md)
- 父仓库文档索引：[`docs/README.md`](docs/README.md)
- 产品总览：[`README.md`](README.md)
- 贡献指南：[`CONTRIBUTING.md`](CONTRIBUTING.md)
- 子模块文档：见各子模块根目录的 `README.md` / `AGENTS.md` / `docs/`
