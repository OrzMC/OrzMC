# 发版组合（Release Composition）

> 父仓库是产品组合的锚点：本文件记录 `main` 上一次基准组合的各子模块**记录指针**（gitlink）。
> 更新：`python3 scripts/release/composition.py` 生成表格后粘贴至此；校验：`python3 scripts/verify/check.py`。

## 基准组合（2026-10-16）

| 子模块 | 仓库 | 分支 | 记录指针 |
|---|---|---|---|
| `deploy` | OrzMC/OrzMCDeploy | `main` | `e72ad9de9506` |
| `plugin` | OrzMC/OrzMCPlugin | `main` | `5eadd6e5b4c8` |
| `profile` | OrzMC/.github | `main` | `bb6b4ac4c66c` |
| `proxy` | OrzMC/OrzMCProxy | `main` | `3cc949cdb2e7` |
| `python` | OrzMC/OrzPythonMC | `main` | `6e0f7e4b0000` |
| `site` | OrzMC/OrzMCSite | `main` | `88e14b1d178b` |
| `swift/app` | OrzMC/OrzMCApp | `main` | `eba6fd5521df` |
| `swift/lib/ExarotonAPI` | OrzMC/ExarotonAPI | `main` | `4f5c1a28985d` |
| `swift/lib/MojangAPI` | OrzMC/MojangAPI | `main` | `b4f0dd6c651b` |
| `swift/lib/OrzAppUpdater` | OrzGeeker/OrzAppUpdater | `main` | `b23e0c414d78` |
| `swift/lib/OrzMCKit` | OrzMC/OrzMCKit | `main` | `851f32200000` |
| `swift/lib/OrzSwiftKit` | OrzGeeker/OrzSwiftKit | `main` | `01dc67535939` |
| `swift/lib/PaperMC` | OrzMC/PaperMC | `main` | `44ef06df0ca2` |
| `tools/DeathChest` | OrzMC/death-chest | `main` | `71d257127c7e` |
| `tools/EzShops` | OrzMC/EzShops | `main` | `7fc73f750f2f` |
| `tools/GetMeHome` | OrzMC/GetMeHome | `main` | `fdbe86df0ab0` |
| `tools/LoginSecurity` | OrzMC/LoginSecurity | `main` | `d45fbcf377eb` |
| `tools/OrzMCBackup` | OrzMC/OrzMCBackup | `main` | `b0240890be56` |
| `tools/rust-thanos` | OrzMC/rust-thanos | `main` | `2dce309fb70d` |
| `tools/thanos` | aternosorg/thanos | `main` | `56772da33595` |
| `webmc` | OrzMC/OrzWebMC | `main` | `e9a585ebcac3` |

> 说明：Swift 相关子模块收拢在 `swift/`（`swift/app` + `swift/lib/*`，后者含引擎 `OrzMCKit` 与 Swift 依赖）；其余子模块指针与 `git ls-tree HEAD` 一致，不受本地检出分支影响。
