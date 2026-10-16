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
| Application name (Azure app display name) | `OrzMC` |
| CLI / command / product name | `orzmc` (OrzMC) |
| Azure Application (client) ID | `1a3e628b-c9a5-4a7f-b7b7-562e22b9787e` |
| Directory (tenant) ID | `ceed58ed-fbc2-40e5-b556-8c8903c24462` |
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
| Directory (tenant) ID | `ceed58ed-fbc2-40e5-b556-8c8903c24462` |
| Azure 账号（应用所有者） | `wangzhizhou2014@outlook.com` |
| 联系邮箱 | `824219521@qq.com` |
| 提交日期 | 2026-10-16 |
| 提交回执（Microsoft Forms 提交 ID） | `v4j5cvGGr0GRqy180BHbR-ajEQ1td1ROpz00KtS8Gd5UNVpPTkVLNFVROVQxNkdRMEtXVjNQQjdXVC4u` |
| 结果 | 待审核（人工审核；回执/结果通常发到联系邮箱） |

## 8. 合规核对（对照 [Minecraft Usage Guidelines](https://www.minecraft.net/usage-guidelines)）

**已符合**
- **命名**：产品/应用名 `OrzMC` / `orzmc` 不含 “Minecraft”，也未把 “Minecraft” 作为主导名；描述中仅作**描述性**引用（“for Minecraft: Java Edition”）。
- **非商业**：免费、开源（Apache-2.0）、无广告、无内购；不售卖 Minecraft 或账号。
- **不重分发游戏文件**：运行期从 Mojang 官方 CDN 下载客户端/服务端核心；仓库与 Release 资产**不含** Mojang 游戏文件（assets / textures / sounds / client jar）。
- **不改动官方对话 / EULA 提示**；无外挂/作弊；无恶意代码；无 NFT / play-to-earn。
- **不冒充官方**：应用名与域名 `orzmc.jokerhub.cn` 均不显官方；授权走 Microsoft 官方设备码流程；令牌只存本地。

**需补齐 / 注意（提交时建议一并说明，或先修）**
1. **必须显著展示官方免责声明**（Guidelines 明确要求）：
   `NOT AN OFFICIAL MINECRAFT PRODUCT. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT`
   **已补**：仓库 `README.md`（父仓库 + python + OrzMCKit + app）、官网页脚（`site` 的 `site-footer.html`）、App 设置页（`SettingsView` 的 Disclaimer 区块）。
2. **责任主体 + 联系渠道**（不能用聊天/论坛链接）：发布者 `OrzMC`，联系邮箱 `824219521@qq.com`——**已随免责声明一同展示**。
3. **品牌素材**：确认 Logo / App 图标（`images/orzmc.png`、`profile/assets/OrzMC.png`、App icon）**均为自创**，不含 Mojang 素材。
4. **服务器正版验证默认**：Guidelines 要求“服务器访问仅授予正版玩家”。当前默认 `online-mode=false`（Python 未配置时写 false；Swift Paper `--online-mode=false`）。**建议改为默认 `online-mode=true`**（或至少不在引导里默认离线）——属产品决策。

## 9. 表单逐字段（按实际表单填写）

| # | 字段 | 填写值 |
|---|---|---|
| 1 | 阅读并同意 EULA + Usage Guidelines | ☑ 勾选 |
| 2 | Contact Information → Azure Portal Email | `wangzhizhou2014@outlook.com` |
| 2 | Contact Information → Personal Email | `824219521@qq.com` |
| 3 | What type of request is this? | **New AppID for Approval** |
| 4 | Application Name | `OrzMC` |
| 5 | Application (Client) ID | `1a3e628b-c9a5-4a7f-b7b7-562e22b9787e` |
| 6 | Tenant (Directory) ID | `ceed58ed-fbc2-40e5-b556-8c8903c24462` |
| 7 | Associated website or domain | `https://orzmc.jokerhub.cn` |
| 8 | Justification | 见下方英文段落 |
| 9 | Any other information | 见下方英文段落 |

### 8. Justification（英文，直接粘贴）

> OrzMC is an **open-source (Apache-2.0), non-commercial** launcher and server-management tool for **Minecraft: Java Edition**. It is distributed free of charge on GitHub and PyPI, with **no ads, no in-app purchases, and no monetization**, and it does not sell or transfer Minecraft accounts. It ships as a cross-platform `orzmc` CLI plus a macOS/iOS app.
>
> We are requesting approval to use the **Minecraft Java Edition Game Service API for user sign-in only**. Our tools implement the standard Microsoft **device-code** flow (scope `XboxLive.signin offline_access`) → Xbox Live (RPS) → XSTS → `login_with_xbox` → `/minecraft/profile`, so users can launch the game under their **own legitimate Microsoft account** (“online mode”). Authentication is **opt-in**; the tool works offline by default for local single-player and never uses the API to grant online access to non-owners.
>
> We do **not** collect usernames/passwords, we operate **no authentication backend**, and all tokens are stored **only on the user’s device** (file mode `0600`) and never transmitted to our servers. We **do not redistribute Minecraft or any game files** — files are downloaded at runtime from Mojang’s official CDN — and we do **not** modify or hide Minecraft’s EULA or dialogs. We comply with the Minecraft EULA and Usage Guidelines and will display the required “**NOT AN OFFICIAL MINECRAFT PRODUCT. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT**” disclaimer and our contact email on our website, app, and repository.
>
> Contact: **824219521@qq.com**. Azure portal account: **wangzhizhou2014@outlook.com**. The app is registered in tenant `ceed58ed-fbc2-40e5-b556-8c8903c24462`.

### 9. Any other information（英文，直接粘贴）

> The project is fully **open source** and auditable: https://github.com/OrzMC (CLI: https://github.com/OrzMC/OrzPythonMC and https://github.com/OrzMC/OrzMCKit; app: https://github.com/OrzMC/OrzMCApp; website: https://orzmc.jokerhub.cn).
>
> We have already run the full authentication chain end-to-end: Microsoft device code → MSA token → Xbox Live (RPS) → XSTS all succeed; `login_with_xbox` currently returns `403 Invalid app registration`, which is exactly why we are submitting this request. We are happy to provide any further information and will add the required disclaimer and contact details prominently upon approval.
