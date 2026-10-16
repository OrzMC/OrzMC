# Minecraft Java Edition Game Service API —— 申请材料（OrzMC / orzmc）

> **状态**：申请材料（待提交 / 跟踪工单号）｜ **最后更新**：2026-10-15
> **背景**：Mojang 要求第三方应用通过 *Java Edition Game Service API Review or Application Process* 才能使用
> `login_with_xbox`（`aka.ms/AppRegInfo` → <https://help.minecraft.net/hc/en-us/articles/16254801392141-Java-Edition-Game-Service-API-Review-or-Application-Process>）。
> 未获批时 `login_with_xbox` 返回 `403 Invalid app registration`（详见 [`spec/auth.md`](spec/auth.md) §10 与 [`../HANDOFF.md`](../HANDOFF.md) §4 待办 A）。
>
> ⚠️ 本文件含**两个邮箱**（Azure 账号 `wangzhizhou2014@outlook.com`、联系 `824219521@qq.com`）；仓库为公开仓库，如需可改为占位符。

---

## 1. 表单短答（英文，逐字段粘贴）

| Field | Value |
|---|---|
| Application / Project name | `orzmc` (OrzMC) |
| Azure Application (client) ID | `1a3e628b-c9a5-4a7f-b7b7-562e22b9787e` |
| Website | https://orzmc.jokerhub.cn |
| Source code | https://github.com/OrzMC/OrzMC |
| License | Apache-2.0 (open source) |
| Contact email | `824219521@qq.com` |
| Azure account (app owner) | `wangzhizhou2014@outlook.com` |
| Purpose | Third-party Minecraft: Java Edition launcher & server-management CLI/GUI |
| Commercial | No — free, open-source, non-commercial |
| Requested scopes | `XboxLive.signin offline_access` |
| Auth flow | OAuth 2.0 **Device Code** (public client, no client secret) |
| Redirect URI | none (device code flow) |

## 2. 项目描述（Project description，英文，直接粘贴）

> **OrzMC / orzmc** is an open-source, non-commercial tool suite for **Minecraft: Java Edition**. It lets players launch the official Minecraft client and deploy/manage Minecraft servers (vanilla, Paper, Fabric, Forge). It ships as a cross-platform `orzmc` command-line tool (Python and native Swift builds), a macOS/iOS app, and server-ops tooling — all **Apache-2.0**, free of charge, with no ads or monetization.
>
> We request access to the **Minecraft Java Edition Game Service API** solely to let users **sign in with their own Microsoft account** ("premium/online mode"), so the game launches under their legitimate account. The flow is the standard Microsoft **device code** flow:
> `Microsoft OAuth (device code, scope XboxLive.signin) → Xbox Live (RPS) → XSTS → Minecraft login_with_xbox → /minecraft/profile`.
>
> We do **not** collect usernames/passwords, we operate **no authentication backend**, and we never ask users to share accounts. Authentication is **opt-in**; the tool's default mode is offline and it never uses the API to grant online access to non-owners.

## 3. 数据处理与安全（Data handling，英文，直接粘贴）

> - **All tokens are stored locally** on the user's device (state directory, file mode `0600`); they are **never transmitted to OrzMC servers** — we run no auth backend.
> - No telemetry, no analytics, no credential collection.
> - Tokens never appear in logs or machine-readable output (`--json`) by design.
> - **Public client / device code flow** — no client secret is embedded or transmitted.
> - The entire codebase is open source and auditable (link above).
> - Users authenticate with their **own** Microsoft account; the tool does not sell, transfer, rent, or share accounts.

## 4. 合规声明（英文，直接粘贴）

> OrzMC complies with the **Minecraft End User License Agreement** and the **Minecraft Usage Guidelines**. It is a launcher/server-management tool, not a cheat, crack, or piracy tool: online play requires the user to own **Minecraft: Java Edition**, and the tool does not bypass authentication or entitlement checks. Offline mode is limited to local single-player.

## 5. 中文对照（便于核对；不必提交）

- 开源、免费、非商业的 Minecraft: Java 版**启动器 + 服务端部署工具**（跨平台 CLI + macOS/iOS App）。
- 申请 Game Service API 仅为让用户**用本人微软账号正版登录**（设备码：MSA→XBL→XSTS→`login_with_xbox`→`profile`）。
- **令牌只存本地**（`0600`），**无服务端**、无遥测、不收账号密码；默认离线，`--auth` 才认证。
- 合规：遵守 Minecraft EULA / Usage Guidelines；非外挂/破解；在线仍需用户**拥有** Java 版。

## 6. 可能需要额外验证（如对方要求）

- **发布者 / 域名验证**：本站点域名 **`orzmc.jokerhub.cn`**（可加 DNS TXT 或放置验证文件）。
- **预期调用量**：user-initiated sign-ins only；low volume，开源社区（数百用户量级）。

## 7. 提交与跟踪

| 项 | 值 |
|---|---|
| Azure client_id | `1a3e628b-c9a5-4a7f-b7b7-562e22b9787e` |
| Azure 账号（应用所有者） | `wangzhizhou2014@outlook.com` |
| 联系邮箱 | `824219521@qq.com` |
| 提交日期 | `[待填]` |
| 工单号 / 回执 | `[待填]` |
| 结果 | `[待填]`（通过后重跑真实 E2E，见 `HANDOFF.md` §4 待办 A4） |
