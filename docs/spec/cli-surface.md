# CLI 命令面契约（CLI Surface Contract）

> **状态**：草案 `specVersion 0.1` ｜ **最后更新**：2026-10-15
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
| `plugin` | Hangar 搜索 / 下载服务端插件（**吸收自 Swift**） | ✅ | ✅ |
| `list` | 列出已安装版本 | ✅ | ❌ |
| `remove` | 移除已安装版本 | ✅ | ❌ |
| `backup` | 备份服务端世界 | ✅ | ❌ |
| `update` | 升级工具自身（非游戏版本） | ✅ | ❌ |
| `uninstall` | 卸载工具自身 | ✅ | ❌ |
| `app` | **跨面**：安装 / 打开 / 卸载 GUI 应用 | ✅ (macOS) | ✅ (macOS) |
| `completion` | 生成 / 安装 Shell 补全 | ✅ 新增 | ✅ 新增（bash/zsh） |
| `capabilities` | 机器可读的命令 / 选项 / 退出码清单（AI 能力发现） | ✅ 新增 | ✅ 新增 |
| `mcp` | 本地 MCP server（stdio JSON-RPC，把命令暴露为 AI tools） | ✅ 新增 | ✅ 新增 |
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
| `--auth` | | flag | false | 正版授权；**规范纳入（已决）**，契约见 [`auth.md`](auth.md)（Swift 已有 flag，Python 待补；两套实现链路均待实现） |

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
| `--type` | `-t` | `vanilla` | `vanilla\|paper\|fabric\|forge` | 两套 ✅ |
| `--nogui` | | false | 无窗口模式 | 两套 ✅ |
| `--yes` | | false | 跳过确认（自动接受 EULA） | 两套 ✅（Swift 默认自动接受 EULA，旗标为命令面兼容） |
| `--force-upgrade` | | false | `--forceUpgrade` | 两套 ✅ |
| `--symlink` | | false | 软链接备份世界 | 两套 ✅ |
| `--force-download` | | false | 强制重下核心 | 两套 ✅ |
| `--online-mode` | `-o` | false | 正版验证（Swift 传入启动，Python 写入 `server.properties`） | 两套 ✅ |
| `--demo` | | false | 演示模式 | 两套 ✅ |
| `--print-jar-help` | `-j` | false | 打印服务端 jar 帮助信息（服务端加 `--help`） | 两套 ✅（原名 `--jar-help`，2026-10-15 改名） |
| `--server-args` | | — | 服务端程序参数 | 两套 ✅ |
| `--kill-all` | `-k` | — | 杀掉所有运行中的服务端 | Swift ✅；Python 计划（需进程跟踪） |

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
| `update` | `-v/--version`（工具版本）、`--check`、`--channel release\|beta`、`--file`、`--yes`、`--force` | Python |
| `uninstall` | `--yes`、`--remove-root`、`--force` | Python |
| `version` | — | Python |
| `app` | `install\|open\|uninstall\|status`；`--channel release\|appstore`、`--version`、`--yes` | **新增（见 `install-update.md`）** |
| `completion` | `bash\|zsh\|fish\|powershell`；`install` | **新增** |
| `capabilities` | —（`--json` 输出命令 / 选项 / 退出码清单） | **新增（见 §8.1）** |
| `mcp` | 无参数；stdio JSON-RPC server | **新增（见 §8.2）** |

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

- `error.code`：稳定字符串，见下方**错误码表**。
- `--json` 隐含**非交互**：绝不等待输入（§7）。
- 退出码仍按上方（`0`/`1`/`130`）—— AI 可同时看 `ok` 与退出码。
- `--auth` 的 `data` **不含任何令牌**（见 [`auth.md`](auth.md) §8）。

#### 错误码表（已定稿）

`error.code` 取以下稳定值（两套实现均应使用此表；未知情况归 `E_RUNTIME`）：

| `code` | 退出码 | 含义 |
|:--|:--:|:--|
| `E_USAGE` | 1 | 参数 / 用法错误（缺必填、未知选项、非法值） |
| `E_UNSUPPORTED` | 1 | 不支持的能力（类型 / 平台 / 渠道） |
| `E_UNSUPPORTED_TYPE` | 1 | 具体类型不支持（如 forge 服务端） |
| `E_VERSION_NOT_FOUND` | 1 | 指定的 Minecraft / 插件 / 应用版本不存在 |
| `E_NOT_FOUND` | 1 | 目标不存在（已安装版本、应用、资源） |
| `E_VERIFY` | 1 | 校验失败（下载产物 magic / sha256 / 哈希不符） |
| `E_NETWORK` | 1 | 网络 / API 失败（含 GitHub 限流） |
| `E_AUTH` | 1 | 认证失败（通用，见 [`auth.md`](auth.md) §7） |
| `E_AUTH_NOT_CONFIGURED` | 1 | 未配置 `client_id`（离线/未注册阶段） |
| `E_AUTH_DENIED` | 1 | 用户拒绝授权 |
| `E_AUTH_EXPIRED` | 1 | 设备码过期 / refresh token 失效 |
| `E_AUTH_XBOX` | 1 | Xbox Live / XSTS 拒绝（无账号 / 地区 / 未成年） |
| `E_AUTH_NO_GAME` | 1 | 账号无 Minecraft 拥有权（profile 401） |
| `E_CANCELLED` | **130** | 用户取消（拒绝确认 / Ctrl-C） |
| `E_INTERNAL` | 1 | 内部错误（不应发生） |
| `E_RUNTIME` | 1 | 其它运行错误（默认） |

> 实现可返回表中未列的扩展码（如 `E_NO_SERVER_DOWNLOAD`），但必须保持 `大写 E_*` 命名；
> 调用方应以 `ok` / 退出码为主判据，`error.code` 作细分。`E_CANCELLED` **必须**退出 130。

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
| 能力发现 | `orzmc capabilities --json`：机器可读的命令 / 选项 / 退出码清单（schema 见 §8.1） | ✅ 两套实现 |
| 幂等/可重入 | 下载 / 安装类操作可安全重试，不产生半成品 |
| 退出码 | 稳定且语义化（§6），AI 据此判断成败 |

**关于 “open-cli”**：经核查，`open-cli` / `OpenCLI` **并非一个统一的“AI 可调用 CLI”标准**
（现存同名项目多为“把网站变 CLI”或聊天客户端）。**建议不追逐该名词**，而采用业界事实标准组合：

1. 机器可读输出：`--json`（信封见 §6.1，**已定稿**）；
2. **MCP（Model Context Protocol）**：提供 `orzmc mcp` 本地 MCP server，把核心操作暴露为工具
   ——这是当前 AI 工具集成的事实标准；
3. （可选）随 CLI 发布 agent skill / 使用说明文件，便于 AI 发现用法。

> **优先级（已决）**：`--json` 信封**现在定稿**（§6.1）；`capabilities` schema 见 §8.1；
> `orzmc mcp` 的 schema 见 §8.2（**server 为计划、低优先级**，不阻塞）。

### 8.1 `capabilities` schema（已实现）

`orzmc capabilities --json` 的 `data`：

```jsonc
{
  "tool": "orzmc",
  "version": "2.4.1",
  "exitCodes": [ { "code": 0, "meaning": "成功" }, /* … */ ],
  "envelope": { "ok": "bool", "command": "string", "data": "object|null", "error": "{code,message}|null" },
  "commands": [
    {
      "name": "client",
      "help": "运行 Minecraft 客户端",
      "options": [
        { "names": ["-v", "--version"], "type": null, "required": false,
          "flag": false, "default": null, "help": "游戏版本" }
      ]
    }
  ]
}
```

- `commands[].options[].names`：**长/短选项均列出**（短选项在前）；`argument` 类只有长名或位置名。
- 未知字段用 `null`，不省略（便于消费者固定 schema）。
- 两套实现对该 schema 保持一致；命令/选项随各自 CLI 自动生成（不手写）。

### 8.2 `orzmc mcp`（Python ✅ / Swift ✅）

`orzmc mcp` 在 **stdio** 上提供本地 **MCP server**，把 `capabilities` 中的核心命令暴露为 MCP tools，
供 AI 智能体直接调用。

**传输**：stdio，**换行分隔的 JSON-RPC 2.0**（每行恰好一条 UTF-8 JSON 消息，消息内不含裸换行）；
stdout **只**输出 JSON-RPC 消息，日志 / 进度一律走 stderr。非交互、不阻塞（同 §7）。

| MCP 方法 | 行为 |
|:--|:--|
| `initialize` | 返回 `protocolVersion`（回显客户端所报版本；缺省 `2025-06-18`）、`capabilities.tools`、`serverInfo {name:"orzmc", version}` |
| `notifications/initialized` | 无 `id` 的通知，静默处理（不回复） |
| `ping` | 返回空结果 `{}` |
| `tools/list` | 每个规范命令一个 tool；名称 = 命令名；`inputSchema` 由 `capabilities` 的 options / arguments 生成 |
| `tools/call` | 内部转调对应命令的 `--json` 路径，信封作为 tool 结果 |

**tools**

- tool 名 = 规范命令名；参数名 = 长选项去掉 `--` 前缀（位置参数用其名字，如 `app` 的 `action`）。
- `--json` 恒开启；`inputSchema` 中 flag → `boolean`（仅 `true` 时追加该旗标），`int` → `integer`，其余 → `string`；
  必填项（选项 / 位置参数）进 `required`。
- **不暴露**元 / 自毁命令：`capabilities`、`completion`、`mcp`、`uninstall`。
- 非交互：需要确认的命令（如 `remove`）在缺 `--yes` 时按 §7 返回取消（`E_CANCELLED`）。

**结果与错误**

- RPC 级错误用标准 JSON-RPC 错误码：`-32700` parse error、`-32600` invalid request、
  `-32601` method not found、`-32602` invalid params（未知 tool / 参数、类型不符）。
- 工具级失败**不**用 RPC 错误：`result.isError = !ok`，`result.content[0].text` 为 `--json` 信封
  （含 `error.code`）；成功同理（`isError = false`）。

- **实现状态**：Python（`orzmc_app/cli/mcp.py`，进程内转调）与 Swift（`MCPServer`/`MCPCommand`，子进程转调）均已实现，行为对齐本表。

### 8.3 命令面 manifest 与校验器（路线 A 的第一步）

[`cli-surface.json`](cli-surface.json) 是本章的**机器可读**形式（命令 / 选项 / 位置参数 / 全局选项）。
它是后续 codegen 与漂移检测的单一事实源（路线 A：先**只读校验**，稳定后再谈两侧生成）。

- **自检**（父仓库 CI，阻断）：`python3 scripts/verify/surface.py --self-check`
  （已包含在 `scripts/verify/check.py`）。
- **与实现对比**（只读、默认**不阻断**，仅报告漂移）：

  ```bash
  python3 scripts/verify/surface.py --implementation python \
    --command "uv run --directory python orzmc --json capabilities"
  python3 scripts/verify/surface.py --implementation swift --capabilities caps.json
  ```

  `--strict` 时发现差异退出 1（供命令面收敛完成后接入 CI）。

- 对比语义（见 `scripts/verify/surface.py` 头部）：以 manifest 为规范；`aliases` 视为同一选项；
  位置参数按**顺序**匹配（名字是实现细节）；实现多出的**全局选项**（如 `--root-dir`）不算漂移；
  选项的 `required` 不比较（ConsoleKit 无法表达，由运行时报错强制），仅位置参数比较。
- **枚举值也进比对（2026-10-17）**：实现须在 `capabilities` 的每个选项里上报 `enum`（实际支持值）；
  双方都上报时比较集合，**缺值/多值都算漂移**；实现未上报视为 unknown（只提示 `未上报枚举`，不阻塞）。
  这能抓到“manifest 声明了、实现没真支持”的档位（补全 shell、服务端类型这类）。
- **已声明差异（收敛 backlog）**：manifest 的 `deviations.<impl>` 列出各实现当前**已声明**的差异；
  validator 默认忽略、`--strict` 只对**未声明**漂移失败（已声明数在报告里提示）。当前：
  `python` **0 处（完全一致）**；`swift` **0 处（完全一致）**——客户端 `--type` 已落地（`vanilla`/`fabric`/`forge`；fabric 走 fabric-meta、forge 走官方安装器）；
  服务端 `--type` 两侧均已支持 `vanilla`/`paper`/`fabric`/`forge`（Swift 于 0.11.0 补齐 fabric/forge），补全均为 `bash`/`zsh`/`fish`/`powershell`/`pwsh`+`install`。
  仅 `app --channel` 的 `appstore` 未实现（App Store 未上架，两侧显式 `E_UNSUPPORTED`）——已在 `deviations.{python,swift}` 声明。
  **两侧 `--strict` 均已进 CI**：Python 在 `OrzPythonMC` 的 `quality` job、Swift 在 `OrzMCKit` 的 `conformance` job（均检出父仓库 manifest 后用真实 `capabilities` 对比）。
- **已收敛（累计）**：Python `server --demo`/`--online-mode`/`--print-jar-help`/`update --channel`/`--kill-all`；
  Swift `server --online-mode`/`--jvm-opts`/`--yes`/`--refresh`/`--symlink`/`--force-download`/`--download-threads`、
  client `--jvm-opts`/`--refresh`/`--extract-music`/`--download-threads`、`remove --yes`、`uninstall --root-dir`；
  `--jar-help` 改名 `--print-jar-help`（两侧）。
- **本轮已收敛**：Python `server --demo` / `--online-mode` / `--print-jar-help` / `update --channel` / `--kill-all`；Swift `server --online-mode`（Option→Flag）、
  `server --jvm-opts`/`--yes`/`--refresh`/`--symlink`/`--force-download`/`--download-threads`、`client --jvm-opts`/`--refresh`/`--extract-music`/`--download-threads`/`--type`（fabric+forge）、
  `remove --yes`、`uninstall --root-dir`；`--jar-help` 改名 `--print-jar-help`（两侧）。
- **codegen 评估（路线 A 第 3 步，2026-10-16）**：结论——**暂不做代码生成**，保留「manifest + 两侧 `--strict` 校验」为单一事实源的落地方式。理由：
  1. 两套实现宿主不同（Python `typer` / Swift `ConsoleKit`），生成代码需同时贴合两套框架的类型系统与帮助/补全机制，
     生成器自身会成为第三套「元实现」；
  2. 命令面已收敛为 **0 漂移**，`--strict` 已进 CI（两侧），漂移在合入前即被拦下，codegen 的主要收益
     （消除重复定义）已大幅贬值，而复杂度/耦合显著；
  3. 契约的权威信息是**行为**（`docs/spec/*.md` + conformance fixtures），manifest 只覆盖命令面这一薄层。
  **重估触发条件**：命令/选项数显著增长（如 >30 或大量按平台分叉），或两侧出现反复的手工同步成本；
  届时可先「只用 manifest 生成 `capabilities` 静态描述」，而非整命令生成。

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
2. 新增命令：`list` / `remove` / `backup` / `version` / `completion`（bash/zsh）/ `capabilities` / `update` / `uninstall` / `app` ✅。
3. 选项改名：`--ms/--mx` → `--min-mem/--max-mem`；`--debug` → `--verbose`；`--force_upgrade` → `--force-upgrade`；
   `--jar-opts` → `--server-args`；`--gui` → `--nogui`（反向）。✅
4. 全局 `--version` / `--verbose` / `--root-dir` / `--json` ✅（在 main 预解析 argv）。
5. `fabric` 已保留为隐藏别名 ✅（可用，不列入帮助/补全/capabilities）。
6. `mcp` 本地 MCP server（§8.2）✅。

**Python CLI**
1. 新增 `plugin` / `app` / `completion` / `capabilities`。—— 均 ✅（`app` macOS）。
2. 全局 `--version` / `--verbose` / `--root-dir`（**已决**）✅。
3. 新增全局 `--json` ✅ 与 `--auth`（正版授权；契约见 [`auth.md`](auth.md)，离线链路已实现；`client_id` 已注册但 **Mojang Game Service API 审核被拒（2026-10-17）**，真实登录暂不可用）。
4. 选项别名：`--minmem/--maxmem` 保留为 `--min-mem/--max-mem` 的别名 ✅。
5. 开启补全（`add_completion=True`）✅。
6. `mcp` 本地 MCP server（§8.2）✅。

> 收尾状态与勾选见 [`product-unification-plan.md`](../product-unification-plan.md) Phase 3/4。
