# 服务器列表展示：MOTD / 人数 / 图标（统一代理拓扑）

老板说「MOTD 和玩家人数优化一下」时的完整落点与验收法。**改一处不够、验证方式三端各不相同**，按本文顺序做。

## 1. 三端真源（代理模式下）

| 端 | 文件 | 格式 | 生效方式 |
|:--|:--|:--|:--|
| Java（含基岩继承） | `E:/orzmc/eagler/proxy/velocity.toml` 的 `motd` | **MiniMessage**（`<gradient:#a:#b>…`、`\n` 表示换行） | `docker restart orzmc-velocity` |
| 基岩 | 无需单独配 | — | 代理侧 `Geyser-Velocity/config.yml` 的 `passthrough-motd: true` + `passthrough-player-counts: true` 自动继承 Java 端 |
| 网页（EaglercraftX） | `E:/orzmc/eagler/proxy/plugins/eaglerxserver/listeners.toml` 的 `server_motd` | **字符串数组**（每行一项，最多两行）+ 旧式 `&` 颜色码，不支持 MiniMessage | 同上重启 |

`velocity.toml` 相关三键：`motd`、`show-max-players`（**只是列表里展示的上限数字**，与真实满员无关）、`sample-players-in-ping`（悬停是否显示在线名单）。

> **客户端只显示两行**，每行约 48 格后截断 → 第一行放身份信息，第二行放标语；超了就是白写。

## 2. 老板定案的 MOTD 口径（测试服）

- 第一行：**OrzMC 品牌**（渐变加粗）+ `多版本` + `Java/基岩/网页端` —— 目的是让三端玩家一眼确认自己能进。
- 第二行：官网标语 **「一个人是冒险，一群人是传奇」**（暖色渐变当情感钩子）。
- **不写域名**：官网 `show_address=false`（地址隐藏），MOTD 里公开 `dev.{SERVER_NAME}.cn` 与官网口径矛盾。
- 配色：第一行品牌青蓝**渐变** `#09add3→#7ee8fa`；**第二行必须用 legacy 纯色 `<gold>`，不要用渐变**（原因见 §7：渐变在官网状态卡上会被第三方 API 量化成两截色块）。
- 基岩端**不要单独配 MOTD**（passthrough 继承即可，单独改会造成三端不一致）。

可直接粘贴：

```toml
motd = "<gradient:#09add3:#7ee8fa><bold>OrzMC</bold></gradient> <dark_gray>·</dark_gray> <white>多版本 <dark_gray>·</dark_gray> <aqua>Java/基岩/网页端\n<gold>一个人是冒险，一群人是传奇"
```

```toml
server_motd = [
  "&b&lOrzMC &8· &f多版本 &8· &bJava/基岩/网页端",
  "&6一个人是冒险，一群人是传奇",
]
```

## 3. 人数显示

- `show-max-players: 500`（Velocity 默认）在空服时显示 `0/500`，观感荒凉 → 按实际承载改成 **30** 一档。
- `sample-players-in-ping = true`：有人在线时悬停可见名单，人少时不至于显得没人玩。
- 真实满员/踢人由后端 `max-players` 决定，改 `show-max-players` 不影响能否进服 —— 老板问「上限多少」时要说清这个区别。

## 4. 改法（TOML 精确替换，别用 sed）

写一个带 `assert` 的 Python 小脚本改，比 sed 稳（`motd` 是跨引号的单行长串，正则容易截断）：

1. `mkdir -p /e/orzmc/tmp/bak-motd-<日期>`，把 `velocity.toml` 与 `listeners.toml` 各 `cp` 一份 `.bak`；回滚 = 覆盖后重启。
2. 按 `t.index('"\n', i)` 定位 `motd` 的**结束引号**整行替换；`listeners.toml` 按行匹配 `server_motd` 起止重写，保留原缩进。
3. `write_text(..., newline="\n")`，跑完回显改后的行确认。
4. **`docker restart orzmc-velocity`** —— 没有 reload，改文件不重启等于没改。约 10–20s；挑 0 人在线时做。

⚠️ 重启属审批门动作（会踢掉在线玩家）：先把「文案已落盘、待重启生效」讲清楚，等老板明确同意再执行；被 `BLOCKED` 就地停下，不要换命令绕。

## 5. 验收（三端各一种，缺一不可）

| 端 | 方法 | 期望 |
|:--|:--|:--|
| Java | `PYTHONPATH="" PYTHONUTF8=1 python scripts/mc_ping_probe.py 127.0.0.1 25565` | 两行文本 + `x/30` |
| 基岩 | `curl -s -m 6 http://127.0.0.1:19132/v1/join` | JSON：`name`=第一行、`level`=第二行、`players/maxPlayers`=人数 —— **一次请求同时验 MOTD 与上限，最好用的一条** |
| 网页 | `curl -s -o /dev/null -w '%{http_code} %header{server}' -m 8 --resolve dev.{SERVER_NAME}.cn:443:127.0.0.1 https://dev.{SERVER_NAME}.cn/` | `404 + Server: EaglercraftXServer/…`（404 是入口正常的形态，不是故障） |

网页端用 `-k https://127.0.0.1:443 -H 'Host: …'` 会 `exit 35`（SSL connect error）—— **TLS 握手要看 SNI**，必须用 `--resolve` 把域名解析指到 127.0.0.1，协议与证书才对得上。

## 6. 坑

- 🔴 **探针读不到 MOTD ≠ MOTD 没生效**：chat component 的文本常在 `extra` 子节点里（渐变/多行必然如此），只取 `description["text"]` 会打印空。`mc_ping_probe.py` 已改为递归 `flatten_text()`（str/list/dict + `extra`/`with`）并用 `⏎` 标换行 —— 验证前先确认探针是这版，否则会误判成配置没生效、白重启一次。
- 🔴 **`server_motd` 是数组不是字符串**：写成单字符串 EaglerX 只当一行；写在数组里每项一行、最多两行。
- 🔴 **两套颜色语法别混**：Velocity/Velocity 侧是 MiniMessage（`<gradient>`、`<bold>`），EaglerX 侧是 `&` 码（`&b&l`）。把 `&` 码贴进 `velocity.toml` 会原样显示；把 MiniMessage 贴进 `listeners.toml` 会显示成标签。
- 🟡 **`server-icon.png`** 放在代理根目录即可显示自定图标；没有就是客户端默认灰图。老板当时的决定是「先只改文字」，别自作主张塞图。
- 🟡 代理启动日志里 `EaglercraftXServer` / `Geyser b####` 正常加载即可，MiniMessage 解析失败会在 `docker logs` 里出现 parse/无效标签字样 —— 重启后 grep 一次 `error|invalid|parse` 确认无报错。

## 7. 官网状态卡（mcstatus.io 转发）的显示一致性

官网 `OrzMCSite`（本地克隆 `E:/dev/OrzMCSite`，状态卡 = `layouts/partials/server-status.html` + `static/js/server-status.js`）**不直连服务器**，走 `api.mcstatus.io/v2/status/java/<host>`。这条转发链路会毁掉两样东西，设计 MOTD 时必须提前避开：

- 🔴 **渐变被量化成 16 色 legacy 码**：平滑渐变（每字一色）经 API 变成 `§e`/`§c` 这类粗色段，切点常落在词中间（实例：第二行一半黄一半红）。**网页端永远还原不了渐变**，跨词渐变 = 官网卡片必错位。结论：**会被官网展示的那一行用 legacy 单色**（`<gold>` / `§6`），渐变只留给游戏内才看得见的元素或容忍度高的短词。改前先用 `curl -s https://api.mcstatus.io/v2/status/java/<host>` 看它返回的 `description.html`/`raw` 实际色段，不要靠猜。
- 🔴 **`version.protocol` 恒返回 47，不可信**：本服真实 762，而本服、国内服 Paper 26.3、`mc.hypixel.net`、`play.mineville.org` 实测全部返回 47（上游是默认值而非解析结果）。**前端不得把协议号拼进版本标签**（会出现「Velocity 1.7.2-26.3 · 47」这种假信息）；`normalize()` 可保留字段供排障，但不上卡片。

判定原则：**「游戏内正确」≠「官网卡片正确」**。改 MOTD 文案/配色时先想一遍它经 mcstatus 量化后的样子；发现官网上颜色错乱或多出怪数字，先怀疑数据源转发（API 返回值），不要先去改站点 CSS —— 颜色信息是在 API 层丢的，样式改不回来。

站点侧改动纪律：先 `node --check static/js/server-status.js` 过语法；本机没 `hugo` 就不做本地预览，走分支 → PR → CI（合入后自动发布 Pages），提交范围只含改动的那一个文件。玩家手册的同类改动见 `references/site-manual.md`。
