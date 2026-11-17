# mineflayer 协议层验证 Tab 补全（tab_complete 包）

（2026-09-12 由独立技能 paper-26-plugin-dev 的 reference 合并入 orzmc）

用于自动化验证服务器命令补全行为（如 GetMeHome `/home` 补全被抢占问题），无需真客户端。

## 关键协议事实（1.21.x，2026-08-31 实测）

1. **1.21 起 tab_complete 包格式是 `{transactionId, text}`** —— 旧格式的 `assumeCommand` / `lookedAtBlock` 字段**已移除**。写旧格式 → 服务端静默无响应。
2. **协议版本必须与服务器一致**：Paper 26.2 = 协议 776 = MC 1.21.10。用更高协议（1.21.11=777）连 → ViaVersion 降级转换可能吞包 → 无响应。**用 `version: '1.21.10'` 连**。
3. 响应（clientbound）：`{transactionId, start, length, matches: [{match, tooltip}]}` —— `match` 即补全候选。

## 脚本

`~/minecraft-bot/tab-single.js`（单请求，最稳）：
```bash
cd ~/minecraft-bot && node tab-single.js "/home "   # 单测一个命令的补全
```
- 登录流程：自动 `/login orztest2026`（GrimTest02 等测试号），spawn 后 4s 发请求
- 输出：`[RESP] tid=1 start=6 len=0 matches=["test1"]` = 补全正常返回家名
- 输出 `[-] 超时无响应` = 无补全响应（先检查协议版本/包格式，再怀疑服务器）

`~/minecraft-bot/tab-complete-test.js`（多命令对照，一次性测多个）；`~/minecraft-bot/tab-single-1210.js`（1.21.10 专用）。

## 可靠性判断

- 若**连原版命令**（`/gamemode `、`/list `）也无响应 → **工具本身不可靠**（协议/版本问题），结论以真客户端实测为准
- 若原版命令有响应而插件命令无 → 插件命令补全确实失效（Brigadier 抢占等），结论可信
- 已知案例：Essentials 禁用 home 命令前 `/home ` 补全错位返回 `["default"]`（诡异内容 = 被抢占的信号）；禁用后返回 `["test1"]`（玩家自己的家）✅

## 注意

- GriefPrevention 防重登：连续登录间隔须 >60s，否则 `You must wait N seconds before logging-in again`
- 测试 bot 须授 `grim.exempt`（LP：`lp user <bot> permission set grim.exempt true`），否则被 GrimAC 误踢（mineflayer 登录基线 ~10VL/s）
