# CLI 命令面契约（CLI Surface Contract）

> **状态**：草案 `specVersion 0.1` ｜ **最后更新**：2026-10-14
> 目标：Swift CLI（`OrzMCKit` 的 `orzmc`）与 Python CLI（`orzmc-app`）收敛为**同一个工具**——
> 用户看到的命令、参数、输出、退出码一致。实现可不同，**命令面必须相同**。

---

## 1. 通用约定

| 约定 | 规范 |
|:--|:--|
| 调用形式 | `orzmc <command> [options] [args]` |
| 无子命令 | **打印帮助到 stdout 并退出 0**（不隐式启动客户端） |
| 帮助 | `-h` / `--help`（每个命令与全局均支持） |
| 工具版本 | 全局 `orzmc --version` → 打印 `orzmc <ver>`；同时保留 `orzmc version` 子命令 |
| 游戏版本 | 子命令内 `-v` / `--version`（**与全局 `--version` 语义不同**，靠位置区分） |
| 语言 | 输出默认跟随 `LANG`/`LC_ALL`；【待定】强制语言开关 `--lang en\|zh` |
| 前缀 | 不要求前缀；`orzmc` 本身就是命令名 |

> **注意 `--version` 的二义性**：`orzmc --version` = 工具版本；`orzmc client --version 1.21` = 游戏版本。
> 全局选项必须出现在子命令**之前**。

---

## 2. 命令总览（规范命令集）

| 命令 | 作用 | Python 现状 | Swift 现状 |
|:--|:--|:--|:--|
| `client` | 启动客户端（缺文件自动下载即安装） | ✅ | ✅ |
| `server` | 部署并启动服务端 | ✅ | ✅ |
| `plugin` | Hangar 搜索 / 下载服务端插件（**吸收自 Swift**） | ❌ 无 | ✅ |
| `list` | 列出已安装版本 | ✅ | ❌ |
| `remove` | 移除已安装版本 | ✅ | ❌ |
| `backup` | 备份服务端世界 | ✅ | ❌ |
| `update` | 升级工具自身（非游戏版本） | ✅ | ❌ |
| `self-uninstall` | 卸载工具自身 | ✅ | ❌ |
| `app` | **跨面**：安装 / 打开 / 卸载 GUI 应用 | ❌ 新增 | ❌ 新增 |
| `completion` | 生成 / 安装 Shell 补全 | ✅ 新增 | ✅ 新增（bash/zsh） |
| `version` | 打印工具版本 | ✅ | ✅ |

> `fabric` 不设独立命令：统一用 `client/server -t fabric`（Python 现行做法）。
> Swift 的 `fabric` 命令保留为**隐藏别名**，内部转 `client/server -t fabric`。

---

## 3. 全局选项

| 选项 | 说明 | 状态 |
|:--|:--|:--|
| `--verbose` | 输出调试日志 | **全局（已决）**；Swift `--debug` 已改名，`-d` 保留别名（Swift ✅ / Python ✅） |
| `--root-dir <path>` | 游戏根目录（默认 `~/minecraft`） | **全局（已决）**；子命令仍接受（Swift ✅ / Python ✅） |
| `--json` | 机器可读输出（见 §6 / §8） | **全局（已决）**；非 TTY/脚本/AI 场景使用（Swift ✅ / Python ✅） |
| `--version` | 打印工具版本 | **全局（已决）**；与子命令 `-v`（游戏版本）靠位置区分（Swift ✅ / Python ✅） |
| `-h` / `--help` | 帮助 | 两者需补齐 |

---

## 4. 各命令契约

### 4.1 `client`

```
orzmc client [-v VER] [-u USER] [-t TYPE] [-m MIN] [-x MAX]
             [--jvm-opts "..."] [--extract-music] [--refresh] [-j THREADS]
             [--root-dir DIR] [--auth] [--debug]
```

| 选项 | 短 | 类型 | 默认 | 说明 |
|:--|:--|:--|:--|:--|
| `--version` | `-v` | str | 交互选择 / Mojang 最新 release | 游戏版本 |
| `--username` | `-u` | str | `guest`（TTY 交互询问） | 玩家名 |
| `--type` | `-t` | enum | `vanilla` | `vanilla\|fabric\|forge` |
| `--min-mem` | `-m` | str | `512M` | 最小内存 |
| `--max-mem` | `-x` | str | `2G` | 最大内存 |
| `--jvm-opts` | | str | — | 附加 JVM 旗标（空格分隔） |
| `--extract-music` | | flag | false | 提取音乐后退出 |
| `--refresh` | | flag | false | 忽略元数据缓存 |
| `--download-threads` | `-j` | int | 16（1–64） | 下载并发 |
| `--auth` | | flag | false | 正版授权；**规范纳入（已决）**（Swift 已有，Python 待补） |

> **命名收敛**：Python 现为 `--minmem/--maxmem`，Swift 现为 `--ms/-s`、`--mx/-x`。
> 规范统一为 `--min-mem/-m`、`--max-mem/-x`；旧名保留为**弃用别名**。

### 4.2 `server`

```
orzmc server [-v VER] [-t TYPE] [-m MIN] [-x MAX] [--nogui] [--yes]
             [--force-upgrade] [--symlink] [--force-download] [--online-mode]
             [--demo] [--jvm-opts "..."] [--server-args "..."] [--kill-all]
             [--refresh] [-j THREADS] [--root-dir DIR]
```

| 选项 | 短 | 默认 | 说明 | 备注 |
|:--|:--|:--|:--|:--|
| `--type` | `-t` | `vanilla` | `vanilla\|paper\|fabric\|forge` | **默认 `vanilla`（已决）**；Swift 现默认 `paper`，需改 |
| `--nogui` | | false | 无窗口模式 | Swift 现为 `--gui`（反向），需改名 |
| `--yes` | | false | 跳过确认（自动接受 EULA） | Python ✅ |
| `--force-upgrade` | | false | `--forceUpgrade` | Swift 现为 `--force_upgrade` |
| `--symlink` | | false | 软链接备份世界 | Python ✅ |
| `--force-download` | | false | 强制重下核心 | Python ✅ |
| `--online-mode` | `-o` | false | 正版验证 | Swift ✅ |
| `--demo` | | false | 演示模式 | Swift ✅ |
| `--server-args` | | — | 服务端程序参数 | Swift 现为 `--jar-opts` |
| `--kill-all` | `-k` | — | 杀掉所有运行中的服务端 | Swift ✅ |

### 4.3 `plugin`（吸收自 Swift）

```
orzmc plugin [--search TEXT] [--list] [--output DIR] [--version VER] [--count N]
```

- `--search TEXT`：Hangar 搜索；`--list`：列出全部；缺省 + `--output`：下载到目录。
- 缺省 `--count` = 3。

### 4.4 其它命令

| 命令 | 关键选项 | 来源 |
|:--|:--|:--|
| `list` | `--root-dir` | Python |
| `remove` | `-v`（必填）、`--server`、`-t`（移除服务端时必填）、`--yes` | Python |
| `backup` | `-v`（可推断）、`-t` | Python |
| `update` | `-v/--version`（工具版本）、`--check`、`--file`、`--yes`、`--force` | Python |
| `self-uninstall` | `--yes`、`--remove-root`、`--force` | Python |
| `version` | — | Python |
| `app` | `install\|open\|uninstall\|status`；`--channel release\|appstore`、`--version`、`--yes` | **新增（见 `install-update.md`）** |
| `completion` | `bash\|zsh\|fish\|powershell`；`install` | **新增** |

---

## 5. 选项命名冲突解决表

| 语义 | 规范名 | 短 | Python 现名 | Swift 现名 | 动作 |
|:--|:--|:--|:--|:--|:--|
| 最小内存 | `--min-mem` | `-m` | `--minmem` | `--ms` (`-s`) | Swift 改名；Python 旧名留别名 |
| 最大内存 | `--max-mem` | `-x` | `--maxmem` | `--mx` (`-x`) | Swift 改名；Python 旧名留别名 |
| 类型 | `--type` | `-t` | `--type` | `--type` | ✅ 一致 |
| 调试日志 | `--verbose` | | `--verbose` | `--debug` (`-d`) | Swift 改名，`--debug` 留别名 |
| 无窗口 | `--nogui` | | `--nogui` | `--gui`（反向） | Swift 改名 |
| 强制升级 | `--force-upgrade` | | `--force-upgrade` | `--force_upgrade` (`-f`) | Swift 改名 |
| 服务端程序参数 | `--server-args` | | `--server-args` | `--jar-opts` (`-e`) | Swift 改名 |
| 工具版本 | `--version`（全局） | | `version` 子命令 | ❌ | 两者补全局 |

---

## 6. 退出码与输出

| 退出码 | 含义 |
|:--|:--|
| `0` | 成功 |
| `1` | 运行错误（用户可读错误信息写 **stderr**） |
| `130` | 用户取消（Ctrl-C / 拒绝确认） |

- 人类可读输出到 **stdout**；错误到 **stderr**。
- **机器可读输出**：全局 `--json`（**已决**）→ 结构化 JSON，字段与 `data-model.md` 对齐；
  非 TTY 时**默认仍为人类可读**（不破坏现状），显式 `--json` 才切换。

### 6.1 `--json` 信封（已定稿）

单条命令输出**恰好一个** JSON 对象（首尾无其它 stdout 内容；进度 / 日志一律走 stderr）：

```jsonc
// 成功
{ "ok": true,  "command": "client", "data": { /* 命令结果 */ }, "error": null }

// 失败
{ "ok": false, "command": "server", "data": null,
  "error": { "code": "E_UNSUPPORTED_TYPE", "message": "类型 forge 不能用于服务端" } }
```

| 字段 | 类型 | 必填 | 说明 |
|:--|:--|:--:|:--|
| `ok` | bool | ✅ | 成功与否 |
| `command` | string | ✅ | 规范命令名（根命令用 `"_root"`） |
| `data` | object\|null | ✅ | 成功时为结果对象（随命令而定），失败为 `null` |
| `error` | object\|null | ✅ | 失败时为 `{code, message}`，成功为 `null` |
| `schemaVersion` | string | | 信封版本（**建议**，如 `"1"`） |

- `error.code`：稳定字符串（如 `E_USAGE` / `E_NETWORK` / `E_VERIFY` / `E_UNSUPPORTED` / `E_CANCELLED`）；
  完整错误码表 —— **计划（低优先级）**。
- `--json` 隐含**非交互**：绝不等待输入（§7）。
- 退出码仍按上方（`0`/`1`/`130`）—— AI 可同时看 `ok` 与退出码。

---

## 7. 交互与非 TTY 行为

| 场景 | 规范 |
|:--|:--|
| TTY + 缺版本 | 交互式版本选择器（键盘导航、可搜索、切正式/测试版） |
| 非 TTY（管道/CI） | **不阻塞**：用 Mojang 最新 release + 默认值 |
| TTY + 缺用户名 | 交互询问（回车用 `guest`） |
| 非 TTY + 缺用户名 | 静默用 `guest` |
| 需确认（EULA/删除/升级） | TTY 弹确认；非 TTY 用默认（`--yes` 明确跳过） |

> **规范红线**：任何非 TTY 场景**禁止等待输入**。

---

## 8. AI 调用与机器可读接口

CLI 需支持**被 AI 智能体调用**：确定性、非交互、可发现、可解析。

| 能力 | 规范 |
|:--|:--|
| 非交互 | 非 TTY 不阻塞（§7）；AI 调用一律走此路径 |
| 结构化输出 | 全局 `--json`，字段与 [`data-model.md`](data-model.md) 对齐 |
| 能力发现 | `orzmc capabilities --json`：机器可读的命令 / 选项 / 退出码清单 —— **计划（低优先级）** |
| 幂等/可重入 | 下载 / 安装类操作可安全重试，不产生半成品 |
| 退出码 | 稳定且语义化（§6），AI 据此判断成败 |

**关于 “open-cli”**：经核查，`open-cli` / `OpenCLI` **并非一个统一的“AI 可调用 CLI”标准**
（现存同名项目多为“把网站变 CLI”或聊天客户端）。**建议不追逐该名词**，而采用业界事实标准组合：

1. 机器可读输出：`--json`（信封见 §6.1，**已定稿**）；
2. **MCP（Model Context Protocol）**：提供 `orzmc mcp` 本地 MCP server，把核心操作暴露为工具
   ——这是当前 AI 工具集成的事实标准；
3. （可选）随 CLI 发布 agent skill / 使用说明文件，便于 AI 发现用法。

> **优先级（已决）**：`--json` 信封**现在定稿**（§6.1）；`capabilities` 与 `orzmc mcp` 的 JSON schema
> **先定为计划、优先级排在后面**，不阻塞 Phase 2。

## 9. Shell 自动补全（用户要求）

| 能力 | 规范 |
|:--|:--|
| 生成脚本 | `orzmc completion <shell>` 输出补全脚本到 stdout |
| 安装补全 | `orzmc completion install` 自动写入对应 shell 的补全目录 |
| 安装器集成 | 安装 CLI 时**自动安装补全**（见 `install-update.md`） |
| 支持 shell | `bash`、`zsh`、`fish`、`powershell` |

- Python（typer）已开启补全(`add_completion=True`),并提供 `orzmc completion <shell>` / `orzmc completion install`;Swift（ConsoleKit）已提供 `completion`(`bash`/`zsh` 原生;`fish`/`powershell` 显式不支持)。
- 全局选项（`--root-dir/--verbose/--json`）需在所有子命令中可用（可能需在解析层提升）。

---

## 10. 迁移清单（实现需做的改动）

**Swift CLI**
1. 无子命令 → 打印帮助并退出 0（去掉默认 `client`）。✅
2. 新增命令：`list` / `remove` / `backup` / `version` / `completion`（bash/zsh）/ `capabilities` / `update` / `self-uninstall` ✅；`app` 待办。
3. 选项改名：`--ms/--mx` → `--min-mem/--max-mem`；`--debug` → `--verbose`；`--force_upgrade` → `--force-upgrade`；
   `--jar-opts` → `--server-args`；`--gui` → `--nogui`（反向）。✅
4. 全局 `--version` / `--verbose` / `--root-dir` / `--json` ✅（在 main 预解析 argv）。
5. `fabric` 已保留为隐藏别名 ✅（可用，不列入帮助/补全/capabilities）。

**Python CLI**
1. 新增 `plugin` / `app` / `completion` / `capabilities`。—— `completion` ✅、`capabilities` ✅；`plugin`/`app` 待办。
2. 全局 `--version` / `--verbose` / `--root-dir`（**已决**）✅。
3. 新增全局 `--json` ✅ 与 `--auth`（正版授权，待办：需库支持）。
4. 选项别名：`--minmem/--maxmem` 保留为 `--min-mem/--max-mem` 的别名 ✅。
5. 开启补全（`add_completion=True`）✅。

> 收尾状态与勾选见 [`product-unification-plan.md`](../product-unification-plan.md) Phase 3/4。
