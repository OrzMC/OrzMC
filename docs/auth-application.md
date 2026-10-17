# Minecraft Java Edition Game Service API —— 申请材料（OrzMC / orzmc）

> **状态**：**第 2 次提交（launcher-only 表述）— 已提交，待结果**｜ **最后更新**：2026-10-17
> **背景**：Mojang 要求第三方应用通过 *Java Edition Game Service API Review or Application Process* 才能使用
> `login_with_xbox`（`aka.ms/AppRegInfo` → <https://help.minecraft.net/hc/en-us/articles/16254801392141-Java-Edition-Game-Service-API-Review-or-Application-Process>；
> 实际提交入口 `aka.ms/mce-reviewappid` → <https://forms.cloud.microsoft/...>）。
> 未获批时 `login_with_xbox` 返回 `403 Invalid app registration`（详见 [`spec/auth.md`](spec/auth.md) §10 与 [`../HANDOFF.md`](../HANDOFF.md) §4 待办 A）。
>
> **历史**：第 1 次 2026-10-16 提交 → **2026-10-17 被拒**（未进白名单；邮件未给原因，声明无申诉/咨询通道）。
> **本次策略**：**只改材料表述与组织，不改产品行为、不改 Azure appID、不改技术实现** —— 主叙事收敛为「启动器」。
> 🔒 **邮箱已脱敏**：原 Azure 账号 / 联系邮箱写在维护者私有记录中；公开仓库不保留真实地址。

---

## 0. 本次为什么这样改（内部记录，**不提交**）

| 观察 | 推断 | 本次动作 |
|---|---|---|
| 第 1 次材料把 `server-management / deploy servers` 与启动器并列为**核心能力** | 评审可能把我们归类为「第三方服务器团队」——对方回信正好在讲 *“if you are part of a team working with a 3rd party server…”* 并推销服务器列表 | 主叙事只讲**启动器**；服务端工具降为“同一开源项目里的独立工具，**不调用** Game Service API” |
| 第 1 次材料主动强调 *“works offline by default”* | 可能被读成“可绕过正版账号启动” | **不再主动强调**默认离线；改为正面陈述「API 仅用于用户本人账号登录，不绕过 entitlement」 |
| 对方未给任何原因 | 无法针对性修复 | 不动产品；把不确定项留给对方追问时如实回答 |

> **诚实性边界**：本次所有陈述仍为**真**——服务端功能确实不调用该 API；我们也没有删改产品行为。
> 若对方追问「能否无账号启动」，如实回答（能做到，但那是本地单机/第三方认证场景，与申请用途无关）。

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
| Contact email | `<redacted>` |
| Azure account (app owner) | `<redacted>` |
| **Purpose** | **Third-party Minecraft: Java Edition launcher** |
| Commercial | No — free, open-source, non-commercial |
| Requested scopes | `XboxLive.signin offline_access` |
| Auth flow | OAuth 2.0 **Device Code** (public client, no client secret) |
| Redirect URI | none (device code flow) |

## 2. 项目描述（Project description，英文，直接粘贴）

> **OrzMC / orzmc** is an open-source, non-commercial **launcher for Minecraft: Java Edition**. Players run a single
> `orzmc client` command (or use the macOS/iOS app) to install and launch the official Minecraft client under
> **their own Microsoft account**. It is distributed as a cross-platform `orzmc` command-line tool (Python and native
> Swift builds) and a GUI app, all **Apache-2.0**, free of charge, with no ads and no monetization.
>
> We request access to the **Minecraft Java Edition Game Service API solely to authenticate the user and launch the
> game for that user**:
> `Microsoft OAuth (device code, scope XboxLive.signin) → Xbox Live (RPS) → XSTS → login_with_xbox → /minecraft/profile`.
> After that we only read the player's own profile (name/UUID/skin) to start the client — nothing else.
>
> The same open-source project also contains **separate server-deployment utilities**. They are unrelated to this
> request: they download official server jars from Mojang's CDN and **never call the Game Service API**.

## 3. 数据处理与安全（Data handling，英文，直接粘贴）

> - **All tokens are stored locally** on the user's device (state directory, file mode `0600`); they are **never transmitted to OrzMC servers** — we run no auth backend.
> - No telemetry, no analytics, no credential collection.
> - Tokens never appear in logs or machine-readable output (`--json`) by design.
> - **Public client / device code flow** — no client secret is embedded or transmitted.
> - The entire codebase is open source and auditable (link above).
> - Users authenticate with their **own** Microsoft account; the tool does not sell, transfer, rent, or share accounts.

## 4. 合规声明（英文，直接粘贴）

> OrzMC complies with the **Minecraft End User License Agreement** and the **Minecraft Usage Guidelines**.
> It is a launcher, not a cheat, crack, or piracy tool: **online play requires the user to own Minecraft: Java Edition**,
> and the tool **does not bypass authentication or entitlement checks** — every online session uses the token obtained
> from the user's own account. We do **not** redistribute Minecraft or any game files (they are downloaded at runtime
> from Mojang's official CDN), and we do **not** modify or hide Minecraft's EULA or dialogs.

## 5. 中文对照（便于核对；不必提交）

- 开源、免费、非商业的 Minecraft: Java 版**启动器**（跨平台 CLI + macOS/iOS App）。
- 申请 Game Service API **只为用户本人登录并启动游戏**：设备码（MSA→XBL→XSTS→`login_with_xbox`→`profile`），
  之后只读取玩家自己的档案（名字/UUID/皮肤）用于启动。
- **令牌只存本地**（`0600`），**无服务端**、无遥测、不收账号密码、不外传令牌。
- 同仓库另有**服务端部署工具**，与本申请无关，且**不调用** Game Service API。
- 合规：不重分发游戏文件、不改 EULA/对话、不绕过 entitlement、在线需用户**拥有** Java 版。

## 6. 表单逐字段（按实际表单填写）

| # | 字段 | 填写值 |
|---|---|---|
| 1 | 阅读并同意 EULA + Usage Guidelines | ☑ 勾选 |
| 2 | Contact Information → Azure Portal Email | `<redacted>` |
| 2 | Contact Information → Personal Email | `<redacted>` |
| 3 | What type of request is this? | **New AppID for Approval** |
| 4 | Application Name | `OrzMC` |
| 5 | Application (Client) ID | `1a3e628b-c9a5-4a7f-b7b7-562e22b9787e` |
| 6 | Tenant (Directory) ID | `ceed58ed-fbc2-40e5-b556-8c8903c24462` |
| 7 | Associated website or domain | `https://orzmc.jokerhub.cn` |
| 8 | Justification | 见 §6.1 |
| 9 | Any other information | 见 §6.2 |

### 6.1 Justification（英文，直接粘贴）

> OrzMC is an **open-source (Apache-2.0), non-commercial launcher for Minecraft: Java Edition**, distributed free of
> charge on GitHub and PyPI with **no ads, no in-app purchases, and no monetization**. It does not sell, transfer or
> rent Minecraft accounts. It ships as a cross-platform `orzmc` CLI plus a macOS/iOS app.
>
> We are requesting approval to use the **Minecraft Java Edition Game Service API for user sign-in only**: our client
> implements the standard Microsoft **device-code** flow (scope `XboxLive.signin offline_access`) → Xbox Live (RPS) →
> XSTS → `login_with_xbox` → `/minecraft/profile`, so a player can launch the game under **their own legitimate
> Microsoft account**. We use the resulting token **only** to start the client for that same user; we never use the API
> to grant online access to non-owners and we do not bypass entitlement checks.
>
> We do **not** collect usernames/passwords, we operate **no authentication backend**, and all tokens are stored
> **only on the user's device** (file mode `0600`) and never transmitted to us. We **do not redistribute Minecraft or
> any game files** (they are downloaded at runtime from Mojang's official CDN) and we do **not** modify or hide
> Minecraft's EULA or dialogs. We comply with the Minecraft EULA and Usage Guidelines, and we display the required
> “**NOT AN OFFICIAL MINECRAFT PRODUCT. NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT**” disclaimer in our
> README, website footer, and app settings, together with our public contact channel
> (https://github.com/OrzMC).
>
> The project also contains separate server-deployment tooling; it is **not** part of this request and **never calls**
> the Game Service API.

### 6.2 Any other information（英文，直接粘贴）

> Fully open source and auditable: https://github.com/OrzMC (CLI: https://github.com/OrzMC/OrzPythonMC and
> https://github.com/OrzMC/OrzMCKit; app: https://github.com/OrzMC/OrzMCApp; website: https://orzmc.jokerhub.cn).
>
> We have already exercised the full chain end-to-end: Microsoft device code → MSA token → Xbox Live (RPS) → XSTS all
> succeed; `login_with_xbox` returns `403 Invalid app registration`, which is why we are submitting this request.
> We are happy to provide any additional information, and we can add a DNS TXT record for domain verification on
> request.

## 7. 提交与跟踪

| 项 | 值 |
|---|---|
| Azure client_id | `1a3e628b-c9a5-4a7f-b7b7-562e22b9787e` |
| Directory (tenant) ID | `ceed58ed-fbc2-40e5-b556-8c8903c24462` |
| Azure 账号（应用所有者） | `<redacted>` |
| 联系邮箱 | `<redacted>` |
| 提交入口 | `aka.ms/mce-reviewappid`（Microsoft Forms） |
| **Forms ID（不是提交回执）** | `v4j5cvGGr0GRqy180BHbR-ajEQ1td1ROpz00KtS8Gd5UNVpPTkVLNFVROVQxNkdRMEtXVjNQQjdXVC4u` |
| 提交返回页 | <https://forms.cloud.microsoft/Pages/ResponsePage.aspx?id=v4j5cvGGr0GRqy180BHbR-ajEQ1td1ROpz00KtS8Gd5UNVpPTkVLNFVROVQxNkdRMEtXVjNQQjdXVC4u> |

> ⚠️ 更正：这个 `v4j5cvGG…` 是**表单本身的 ID**（所有人相同），**不是**本次提交的编号。
> 第 1 次（2026-10-16）曾把它误记为「提交回执」。第 2 次提交后的返回页也是这个 URL——
> 即**没有可引用的提交编号**，结果只能等邮件（发到表单里填的联系邮箱）。

| # | 日期 | 表述 | 结果 |
|---|---|---|---|
| 1 | 2026-10-16 | launcher + server-management（并列） | **被拒**（2026-10-17，未进白名单，无原因、无申诉） |
| 2 | 2026-10-17 | **launcher-only**；服务端能力降为“不调用该 API 的独立工具” | **已提交，待结果**（结果邮件到联系邮箱；无提交编号可查） |

## 8. 合规核对（内部核对，**不提交**）

**已符合**
- **命名**：产品/应用名 `OrzMC` / `orzmc` 不含 “Minecraft”，也未把 “Minecraft” 作为主导名；描述中仅作**描述性**引用。
- **非商业**：免费、开源（Apache-2.0）、无广告、无内购；不售卖 Minecraft 或账号。
- **不重分发游戏文件**：运行期从 Mojang 官方 CDN 下载；仓库与 Release 资产**不含** Mojang 游戏文件。
- **不改动官方对话 / EULA 提示**；无外挂/作弊；无恶意代码；无 NFT / play-to-earn。
- **不冒充官方**：应用名与域名均不显官方；授权走 Microsoft 官方设备码流程；令牌只存本地。
- **免责声明**（Guidelines 明确要求）已展示：仓库 README（父仓库 + python + OrzMCKit + app）、官网 `site-footer.html`、App `SettingsView`。
- **联系渠道**：用 GitHub 组织（合规声明的 `contact_url`），不展示个人邮箱。

**已知但本次不改（属产品决策，且与申请用途无关）**
1. 服务端 `online-mode` 默认值为 `false`（Python 未配置时、Swift Paper 显式传 `--online-mode=false`）——
   Guidelines 希望服务器只对正版开放；若日后要动，单独评估。
2. 客户端支持不带账号的启动（本地单机 / 第三方认证场景）——本次材料不主动强调；若被追问如实回答。

## 9. 提交步骤（维护者操作）

1. 打开 `aka.ms/mce-reviewappid`，按 §6 逐字段粘贴（§6.1 / §6.2 是英文段落，其余是短字段）。
2. `What type of request is this?` 选 **New AppID for Approval**（沿用同一 appID，不新建 Azure 应用）。
3. 提交后把结果回填到 §7 表格第 2 行（日期 + 结果），并同步 `spec/auth.md` §10 与 `HANDOFF.md`。
4. 若再次被拒：**停止重投**，转 authlib-injector / Yggdrasil 路线（见 `HANDOFF.md` §4）。

> ✅ **2026-10-17 已按本节提交**（launcher-only 表述）。等待邮件结果；**无论结果如何不再投第 3 次**。
> 参照：第 1 次 2026-10-16 提交 → 2026-10-17 出结果（约 1 天一个批次）；若两周内无任何邮件，按“未通过”处理并转 authlib。
