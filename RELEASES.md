# 发版组合（Release Composition）

> 父仓库是产品组合的锚点：本文件记录 `main` 上一次基准组合的各子模块**记录指针**（gitlink）。
> 更新：`python3 scripts/release/composition.py` 生成表格后粘贴至此；校验：`python3 scripts/verify/check.py`。

## 基准组合（2026-10-21）

| 子模块 | 仓库 | 分支 | 记录指针 |
|---|---|---|---|
| `deploy` | OrzMC/OrzMCDeploy | `main` | `e72ad9de9506` |
| `plugin` | OrzMC/OrzMCPlugin | `main` | `5eadd6e5b4c8` |
| `profile` | OrzMC/.github | `main` | `bb6b4ac4c66c` |
| `proxy` | OrzMC/OrzMCProxy | `main` | `087bb52129a1` |
| `python` | OrzMC/OrzPythonMC | `main` | `f8c6a67b55ae` |
| `site` | OrzMC/OrzMCSite | `main` | `31d215f6400e` |
| `swift/app` | OrzMC/OrzMCApp | `main` | `05603e7e634a` |
| `swift/lib/ExarotonAPI` | OrzMC/ExarotonAPI | `main` | `4f5c1a28985d` |
| `swift/lib/MojangAPI` | OrzMC/MojangAPI | `main` | `c5a0eadb4e83` |
| `swift/lib/OrzAppUpdater` | OrzGeeker/OrzAppUpdater | `main` | `b23e0c414d78` |
| `swift/lib/OrzMCKit` | OrzMC/OrzMCKit | `main` | `d1049600ee89` |
| `swift/lib/OrzSwiftKit` | OrzGeeker/OrzSwiftKit | `main` | `a009122d5de4` |
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
