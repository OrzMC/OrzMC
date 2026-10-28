# 发版组合（Release Composition）

> 父仓库是产品组合的锚点：本文件记录 `main` 上一次基准组合的各子模块**记录指针**（gitlink）。
> 更新：`python3 scripts/release/composition.py` 生成表格后粘贴至此；校验：`python3 scripts/verify/check.py`。

## 基准组合（2026-10-28）—— B1/B2 已合入（**未发版**）

| 子模块 | 仓库 | 分支 | 记录指针 |
|---|---|---|---|
| `deploy` | OrzMC/OrzMCDeploy | `main` | `e72ad9de9506` |
| `plugin` | OrzMC/OrzMCPlugin | `main` | `5eadd6e5b4c8` |
| `profile` | OrzMC/.github | `main` | `bb6b4ac4c66c` |
| `proxy` | OrzMC/OrzMCProxy | `main` | `087bb52129a1` |
| `python` | OrzMC/OrzPythonMC | `main` | `7f5f8f704069` |
| `site` | OrzMC/OrzMCSite | `main` | `b1500b753152` |
| `swift/app` | OrzMC/OrzMCApp | `main` | `24f803e3b7e8` |
| `swift/lib/ExarotonAPI` | OrzMC/ExarotonAPI | `main` | `4f5c1a28985d` |
| `swift/lib/MCSManagerAPI` | OrzMC/MCSManagerAPI | `main` | `061866fd4ccd` |
| `swift/lib/MojangAPI` | OrzMC/MojangAPI | `main` | `c5a0eadb4e83` |
| `swift/lib/OrzAppUpdater` | OrzGeeker/OrzAppUpdater | `main` | `b23e0c414d78` |
| `swift/lib/OrzMCKit` | OrzMC/OrzMCKit | `main` | `f004baabb69b` |
| `swift/lib/OrzSwiftKit` | OrzGeeker/OrzSwiftKit | `main` | `f35e4dc38a5c` |
| `swift/lib/PaperMC` | OrzMC/PaperMC | `main` | `14df3289ed74` |
| `tools/DeathChest` | OrzMC/death-chest | `main` | `71d257127c7e` |
| `tools/EzShops` | OrzMC/EzShops | `main` | `7fc73f750f2f` |
| `tools/GetMeHome` | OrzMC/GetMeHome | `main` | `fdbe86df0ab0` |
| `tools/LoginSecurity` | OrzMC/LoginSecurity | `main` | `d45fbcf377eb` |
| `tools/OrzMCBackup` | OrzMC/OrzMCBackup | `main` | `f8188a224237` |
| `tools/rust-thanos` | OrzMC/rust-thanos | `main` | `1c6e85cf3f4a` |
| `tools/thanos` | aternosorg/thanos | `main` | `56772da33595` |
| `webmc` | OrzMC/OrzWebMC | `main` | `f0541165bc34` |

> 相比 2026-10-27：`swift/app` → `24f803e3`（PR #122 强杀 + 停止进度，PR #121 开发包安装）、`swift/lib/MCSManagerAPI` → `061866f`（tag **0.5.0**，kill 端点）。
> 下一步：写 `docs/release-notes/0.1.7.md` → `scripts/dev/release.sh --version 0.1.7`。

## 基准组合（2026-10-27）—— B1 控制台实时流已合入（**未发版**）

| 子模块 | 仓库 | 分支 | 记录指针 |
|---|---|---|---|
| `deploy` | OrzMC/OrzMCDeploy | `main` | `e72ad9de9506` |
| `plugin` | OrzMC/OrzMCPlugin | `main` | `5eadd6e5b4c8` |
| `profile` | OrzMC/.github | `main` | `bb6b4ac4c66c` |
| `proxy` | OrzMC/OrzMCProxy | `main` | `087bb52129a1` |
| `python` | OrzMC/OrzPythonMC | `main` | `7f5f8f704069` |
| `site` | OrzMC/OrzMCSite | `main` | `b1500b753152` |
| `swift/app` | OrzMC/OrzMCApp | `main` | `5e33e74feb24` |
| `swift/lib/ExarotonAPI` | OrzMC/ExarotonAPI | `main` | `4f5c1a28985d` |
| `swift/lib/MCSManagerAPI` | OrzMC/MCSManagerAPI | `main` | `1206aba3ea9c` |
| `swift/lib/MojangAPI` | OrzMC/MojangAPI | `main` | `c5a0eadb4e83` |
| `swift/lib/OrzAppUpdater` | OrzGeeker/OrzAppUpdater | `main` | `b23e0c414d78` |
| `swift/lib/OrzMCKit` | OrzMC/OrzMCKit | `main` | `f004baabb69b` |
| `swift/lib/OrzSwiftKit` | OrzGeeker/OrzSwiftKit | `main` | `f35e4dc38a5c` |
| `swift/lib/PaperMC` | OrzMC/PaperMC | `main` | `14df3289ed74` |
| `tools/DeathChest` | OrzMC/death-chest | `main` | `71d257127c7e` |
| `tools/EzShops` | OrzMC/EzShops | `main` | `7fc73f750f2f` |
| `tools/GetMeHome` | OrzMC/GetMeHome | `main` | `fdbe86df0ab0` |
| `tools/LoginSecurity` | OrzMC/LoginSecurity | `main` | `d45fbcf377eb` |
| `tools/OrzMCBackup` | OrzMC/OrzMCBackup | `main` | `f8188a224237` |
| `tools/rust-thanos` | OrzMC/rust-thanos | `main` | `1c6e85cf3f4a` |
| `tools/thanos` | aternosorg/thanos | `main` | `56772da33595` |
| `webmc` | OrzMC/OrzWebMC | `main` | `f0541165bc34` |

> 相比 2026-10-26 的基准：`swift/app` → `5e33e74f`（PR #120，实时流 + DX）、`swift/lib/MCSManagerAPI` → `1206aba`（tag **0.4.0**，新增 `MCSMStream`）。

## 基准组合（2026-10-26）—— **app 0.1.6 (58) 已发布**

| 子模块 | 仓库 | 分支 | 记录指针 |
|---|---|---|---|
| `deploy` | OrzMC/OrzMCDeploy | `main` | `e72ad9de9506` |
| `plugin` | OrzMC/OrzMCPlugin | `main` | `5eadd6e5b4c8` |
| `profile` | OrzMC/.github | `main` | `bb6b4ac4c66c` |
| `proxy` | OrzMC/OrzMCProxy | `main` | `087bb52129a1` |
| `python` | OrzMC/OrzPythonMC | `main` | `7f5f8f704069` |
| `site` | OrzMC/OrzMCSite | `main` | `b1500b753152` |
| `swift/app` | OrzMC/OrzMCApp | `main` | `4eb10ebf1d2e` |
| `swift/lib/ExarotonAPI` | OrzMC/ExarotonAPI | `main` | `4f5c1a28985d` |
| `swift/lib/MCSManagerAPI` | OrzMC/MCSManagerAPI | `main` | `7428340b4ffd` |
| `swift/lib/MojangAPI` | OrzMC/MojangAPI | `main` | `c5a0eadb4e83` |
| `swift/lib/OrzAppUpdater` | OrzGeeker/OrzAppUpdater | `main` | `b23e0c414d78` |
| `swift/lib/OrzMCKit` | OrzMC/OrzMCKit | `main` | `f004baabb69b` |
| `swift/lib/OrzSwiftKit` | OrzGeeker/OrzSwiftKit | `main` | `f35e4dc38a5c` |
| `swift/lib/PaperMC` | OrzMC/PaperMC | `main` | `14df3289ed74` |
| `tools/DeathChest` | OrzMC/death-chest | `main` | `71d257127c7e` |
| `tools/EzShops` | OrzMC/EzShops | `main` | `7fc73f750f2f` |
| `tools/GetMeHome` | OrzMC/GetMeHome | `main` | `fdbe86df0ab0` |
| `tools/LoginSecurity` | OrzMC/LoginSecurity | `main` | `d45fbcf377eb` |
| `tools/OrzMCBackup` | OrzMC/OrzMCBackup | `main` | `f8188a224237` |
| `tools/rust-thanos` | OrzMC/rust-thanos | `main` | `1c6e85cf3f4a` |
| `tools/thanos` | aternosorg/thanos | `main` | `56772da33595` |
| `webmc` | OrzMC/OrzWebMC | `main` | `f0541165bc34` |

---

## 基准组合（2026-10-21）

| 子模块 | 仓库 | 分支 | 记录指针 |
|---|---|---|---|
| `deploy` | OrzMC/OrzMCDeploy | `main` | `e72ad9de9506` |
| `plugin` | OrzMC/OrzMCPlugin | `main` | `5eadd6e5b4c8` |
| `profile` | OrzMC/.github | `main` | `bb6b4ac4c66c` |
| `proxy` | OrzMC/OrzMCProxy | `main` | `087bb52129a1` |
| `python` | OrzMC/OrzPythonMC | `main` | `f8c6a67b55ae` |
| `site` | OrzMC/OrzMCSite | `main` | `31d215f6400e` |
| `swift/app` | OrzMC/OrzMCApp | `main` | `81d0525d1a1c` |
| `swift/lib/ExarotonAPI` | OrzMC/ExarotonAPI | `main` | `4f5c1a28985d` |
| `swift/lib/MojangAPI` | OrzMC/MojangAPI | `main` | `c5a0eadb4e83` |
| `swift/lib/OrzAppUpdater` | OrzGeeker/OrzAppUpdater | `main` | `b23e0c414d78` |
| `swift/lib/OrzMCKit` | OrzMC/OrzMCKit | `main` | `6944afb518c6` |
| `swift/lib/OrzSwiftKit` | OrzGeeker/OrzSwiftKit | `main` | `616212d07310` |
| `swift/lib/PaperMC` | OrzMC/PaperMC | `main` | `14df3289ed74` |
| `tools/DeathChest` | OrzMC/death-chest | `main` | `71d257127c7e` |
| `tools/EzShops` | OrzMC/EzShops | `main` | `7fc73f750f2f` |
| `tools/GetMeHome` | OrzMC/GetMeHome | `main` | `fdbe86df0ab0` |
| `tools/LoginSecurity` | OrzMC/LoginSecurity | `main` | `d45fbcf377eb` |
| `tools/OrzMCBackup` | OrzMC/OrzMCBackup | `main` | `2d1060686c48` |
| `tools/rust-thanos` | OrzMC/rust-thanos | `main` | `c4ffc4cb95dd` |
| `tools/thanos` | aternosorg/thanos | `main` | `56772da33595` |
| `webmc` | OrzMC/OrzWebMC | `main` | `e9a585ebcac3` |

> 说明：Swift 相关子模块收拢在 `swift/`（`swift/app` + `swift/lib/*`，后者含引擎 `OrzMCKit` 与 Swift 依赖）；其余子模块指针与 `git ls-tree HEAD` 一致，不受本地检出分支影响。

## 基准组合（2026-10-25 · 0.1.4 发版后的锚点）

| 子模块 | 仓库 | 分支 | 记录指针 |
|---|---|---|---|
| `deploy` | OrzMC/OrzMCDeploy | `main` | `e72ad9de9506` |
| `plugin` | OrzMC/OrzMCPlugin | `main` | `5eadd6e5b4c8` |
| `profile` | OrzMC/.github | `main` | `bb6b4ac4c66c` |
| `proxy` | OrzMC/OrzMCProxy | `main` | `087bb52129a1` |
| `python` | OrzMC/OrzPythonMC | `main` | `544a7738d847` |
| `site` | OrzMC/OrzMCSite | `main` | `b1500b753152` |
| `swift/app` | OrzMC/OrzMCApp | `main` | `8bc96ed12a12` |
| `swift/lib/ExarotonAPI` | OrzMC/ExarotonAPI | `main` | `4f5c1a28985d` |
| `swift/lib/MojangAPI` | OrzMC/MojangAPI | `main` | `c5a0eadb4e83` |
| `swift/lib/OrzAppUpdater` | OrzGeeker/OrzAppUpdater | `main` | `b23e0c414d78` |
| `swift/lib/OrzMCKit` | OrzMC/OrzMCKit | `main` | `16f29d56c1dd` |
| `swift/lib/OrzSwiftKit` | OrzGeeker/OrzSwiftKit | `main` | `f35e4dc38a5c` |
| `swift/lib/PaperMC` | OrzMC/PaperMC | `main` | `14df3289ed74` |
| `tools/DeathChest` | OrzMC/death-chest | `main` | `71d257127c7e` |
| `tools/EzShops` | OrzMC/EzShops | `main` | `7fc73f750f2f` |
| `tools/GetMeHome` | OrzMC/GetMeHome | `main` | `fdbe86df0ab0` |
| `tools/LoginSecurity` | OrzMC/LoginSecurity | `main` | `d45fbcf377eb` |
| `tools/OrzMCBackup` | OrzMC/OrzMCBackup | `main` | `2d1060686c48` |
| `tools/rust-thanos` | OrzMC/rust-thanos | `main` | `1c6e85cf3f4a` |
| `tools/thanos` | aternosorg/thanos | `main` | `56772da33595` |
| `webmc` | OrzMC/OrzWebMC | `main` | `f0541165bc34` |

## 基准组合（2026-10-25 · 0.1.5 发版后的锚点）

| 子模块 | 仓库 | 分支 | 记录指针 |
|---|---|---|---|
| `deploy` | OrzMC/OrzMCDeploy | `main` | `e72ad9de9506` |
| `plugin` | OrzMC/OrzMCPlugin | `main` | `5eadd6e5b4c8` |
| `profile` | OrzMC/.github | `main` | `bb6b4ac4c66c` |
| `proxy` | OrzMC/OrzMCProxy | `main` | `087bb52129a1` |
| `python` | OrzMC/OrzPythonMC | `main` | `544a7738d847` |
| `site` | OrzMC/OrzMCSite | `main` | `b1500b753152` |
| `swift/app` | OrzMC/OrzMCApp | `main` | `c58ed60236a0` |
| `swift/lib/ExarotonAPI` | OrzMC/ExarotonAPI | `main` | `4f5c1a28985d` |
| `swift/lib/MojangAPI` | OrzMC/MojangAPI | `main` | `c5a0eadb4e83` |
| `swift/lib/OrzAppUpdater` | OrzGeeker/OrzAppUpdater | `main` | `b23e0c414d78` |
| `swift/lib/OrzMCKit` | OrzMC/OrzMCKit | `main` | `16f29d56c1dd` |
| `swift/lib/OrzSwiftKit` | OrzGeeker/OrzSwiftKit | `main` | `f35e4dc38a5c` |
| `swift/lib/PaperMC` | OrzMC/PaperMC | `main` | `14df3289ed74` |
| `tools/DeathChest` | OrzMC/death-chest | `main` | `71d257127c7e` |
| `tools/EzShops` | OrzMC/EzShops | `main` | `7fc73f750f2f` |
| `tools/GetMeHome` | OrzMC/GetMeHome | `main` | `fdbe86df0ab0` |
| `tools/LoginSecurity` | OrzMC/LoginSecurity | `main` | `d45fbcf377eb` |
| `tools/OrzMCBackup` | OrzMC/OrzMCBackup | `main` | `2d1060686c48` |
| `tools/rust-thanos` | OrzMC/rust-thanos | `main` | `1c6e85cf3f4a` |
| `tools/thanos` | aternosorg/thanos | `main` | `56772da33595` |
| `webmc` | OrzMC/OrzWebMC | `main` | `f0541165bc34` |
