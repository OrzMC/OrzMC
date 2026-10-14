# 发版组合（Release Composition）

> 父仓库是产品组合的锚点：本文件记录 `main` 上一次基准组合的各子模块**记录指针**（gitlink）。
> 更新：`python3 scripts/release/composition.py` 生成表格后粘贴至此；校验：`python3 scripts/verify/check.py`。

## 基准组合（2026-10-14）

| 子模块 | 仓库 | 分支 | 记录指针 |
|---|---|---|---|
| `OrzMCKit` | OrzMC/OrzMCKit | `main` | `d5084868526e` |
| `app` | OrzMC/OrzMCApp | `main` | `4a4c6b4e67bf` |
| `deploy` | OrzMC/OrzMCDeploy | `main` | `e72ad9de9506` |
| `plugin` | OrzMC/OrzMCPlugin | `main` | `5eadd6e5b4c8` |
| `profile` | OrzMC/.github | `main` | `10fc4e1dbc87` |
| `proxy` | OrzMC/OrzMCProxy | `main` | `3cc949cdb2e7` |
| `python` | OrzMC/OrzPythonMC | `main` | `b6886fbb8c95` |
| `site` | OrzMC/OrzMCSite | `main` | `436e4b96bea4` |
| `tools/DeathChest` | OrzMC/death-chest | `main` | `71d257127c7e` |
| `tools/EzShops` | OrzMC/EzShops | `main` | `7fc73f750f2f` |
| `tools/GetMeHome` | OrzMC/GetMeHome | `main` | `fdbe86df0ab0` |
| `tools/LoginSecurity` | OrzMC/LoginSecurity | `main` | `d45fbcf377eb` |
| `tools/OrzMCBackup` | OrzMC/OrzMCBackup | `main` | `b0240890be56` |
| `tools/rust-thanos` | OrzMC/rust-thanos | `main` | `2dce309fb70d` |
| `tools/thanos` | aternosorg/thanos | `main` | `56772da33595` |
| `webmc` | OrzMC/OrzWebMC | `main` | `e9a585ebcac3` |

> 说明：`OrzMCKit` 为 Swift 引擎；其余子模块指针与 `git ls-tree HEAD` 一致，不受本地检出分支影响。
