# 正版授权契约（Microsoft Account Auth）

> **状态**：草案 `specVersion 0.1` ｜ **最后更新**：2026-10-15
> **定位**：`orzmc client --auth` 的**语言无关契约**——定义 Microsoft 设备码流程、请求/响应映射、
> 令牌模型与持久化、非 TTY 行为、错误码与安全红线。实现（Python / Swift）必须映射到本契约，
> 并通过 [`conformance.md`](conformance.md) 的 `auth/*` 纯映射样例。
>
> **离线优先**：本契约、参考适配器与黄金样例**不依赖**真实 `client_id` 与网络；
> 两套实现的**离线部分已落地**（纯映射/存储/编排/CLI 接线）；真实 `client_id` 待维护者注册
> Azure 应用后注入（见 §10），真实登录 E2E 届时再补。

---

## 1. 范围

- **纳入规范**：设备码认证链路的纯映射、令牌生命周期语义、CLI `--auth` 行为面、错误码、安全要求。
- **不纳入规范**：具体网络实现（HTTP 客户端 / 重试细节）、令牌加密的具体手段（见 §5 下限）、
  具体 Azure 应用注册流程。

术语：

| 术语 | 含义 |
|:--|:--|
| MSA | Microsoft 账号（个人或组织） |
| `client_id` | Azure 应用（App registration）的 Application ID；**公开、非密钥**（公共客户端不设 secret） |
| uhs | Xbox User Hash（`DisplayClaims.xui[0].uhs`） |
| MC token | `api.minecraftservices.com/authentication/login_with_xbox` 返回的访问令牌（约 24h） |

---

## 2. 认证流程（OAuth 2.0 设备码 / Device Code Flow）

```
① 设备码请求   POST {AUTHORITY}/devicecode
② 设备码轮询   POST {AUTHORITY}/token    （用户完成授权前 authorization_pending）
③ Xbox Live    POST https://user.auth.xboxlive.com/user/authenticate      （RPS）
④ XSTS         POST https://xsts.auth.xboxlive.com/xsts/authorize          （RETAIL）
⑤ MC 登录      POST https://api.minecraftservices.com/authentication/login_with_xbox
⑥ 档案         GET  https://api.minecraftservices.com/minecraft/profile
```

- 设备码流程**不读 stdin**，因此天然适合 CLI 与无头环境（用户在其他设备打开 URL 输入 code）。
- 统一 authority：`{AUTHORITY} = https://login.microsoftonline.com/consumers/oauth2/v2.0`
  （个人账号用 `consumers`；规范实现写死该值即可，无需租户 id）。
- 缺省 scope：**`XboxLive.signin offline_access`**（`offline_access` 用于拿 refresh token）。

---

## 3. 请求 / 响应映射（规范表）

> 对应一致性操作见 §9；所有字段名在此表即规范字段名。

### 3.1 设备码请求

| 项 | 规范值 |
|:--|:--|
| 方法 / 端点 | `POST {AUTHORITY}/devicecode` |
| 方法体 | `application/x-www-form-urlencoded` |
| `client_id` | 实现内置（见 §10）或 `ORZMC_AZURE_CLIENT_ID` |
| `scope` | `XboxLive.signin offline_access`（可覆盖） |

设备码响应 → 抽取：

| 字段 | 说明 |
|:--|:--|
| `device_code` | 轮询用 |
| `user_code` | 展示给用户 |
| `verification_uri` | 展示给用户 |
| `expires_in` | 设备码有效期（秒，通常 900） |
| `interval` | 轮询间隔（秒，通常 5） |
| `message` | 上游人类可读提示（可选） |

### 3.2 令牌轮询 / 刷新

| 项 | 值 |
|:--|:--|
| 端点 | `POST {AUTHORITY}/token` |
| 轮询 | `grant_type=urn:ietf:params:oauth:grant-type:device_code` + `client_id` + `device_code` |
| 刷新 | `grant_type=refresh_token` + `client_id` + `refresh_token` + `scope` |

令牌响应 → 抽取：`access_token` / `refresh_token` / `expires_in` / `token_type` / `scope`。

错误处理见 §7.1（`authClassifyTokenError`）。

### 3.3 Xbox Live（RPS）

| 项 | 值 |
|:--|:--|
| 端点 | `POST https://user.auth.xboxlive.com/user/authenticate` |
| 头 | `Content-Type: application/json`；`Accept: application/json` |
| 方法体 | `{"Properties":{"AuthMethod":"RPS","SiteName":"user.auth.xboxlive.com","RpsTicket":"d=<MSA access_token>"},"RelyingParty":"http://auth.xboxlive.com","TokenType":"JWT"}` |

响应 → `Token` 与 `DisplayClaims.xui[0].uhs`。

> **RpsTicket 前缀**：个人 MSA 用 `d=`（本契约固定 `d=`）。

### 3.4 XSTS

| 项 | 值 |
|:--|:--|
| 端点 | `POST https://xsts.auth.xboxlive.com/xsts/authorize` |
| 方法体 | `{"Properties":{"SandboxId":"RETAIL","UserTokens":["<XBL Token>"]},"RelyingParty":"rp://api.minecraftservices.com/","TokenType":"JWT"}` |

响应 → `Token` 与 `DisplayClaims.xui[0].uhs`。错误（XErr）见 §7.2。

### 3.5 Minecraft 登录

| 项 | 值 |
|:--|:--|
| 端点 | `POST https://api.minecraftservices.com/authentication/login_with_xbox` |
| 方法体 | `{"identityToken":"XBL3.0 x=<uhs>;<XSTS Token>"}` |

响应 → `access_token` 与 `expires_in`（秒）。

### 3.6 档案

| 项 | 值 |
|:--|:--|
| 端点 | `GET https://api.minecraftservices.com/minecraft/profile` |
| 头 | `Authorization: Bearer <MC access_token>` |

响应 → `id`（32 位十六进制，**无连字符**）与 `name`。

> **UUID 规范化**：提供给启动参数的 `uuid` 必须是**带连字符的规范 UUID**
> （8-4-4-4-12）；实现负责把上游 32 位无连字符 `id` 转换为规范形式。

---

## 4. 令牌模型

```jsonc
{
  "schema": 1,
  "clientId": "<Azure Application ID>",
  "account": { "uuid": "8-4-4-4-12", "name": "PlayerName" },
  "msa": {
    "accessToken": "…",          // 短期，可用于刷新
    "refreshToken": "…",         // 长期（offline_access）
    "expiresAt": 1760000000       // Unix 秒
  },
  "minecraft": {
    "accessToken": "…",
    "expiresAt": 1760000000
  }
}
```

- 时间一律 **Unix 秒**（上游 `expires_in` → `expiresAt = now + expires_in`）。
- **绝不持久化密码**，也不持久化 XBL/XSTS Token（一次性）。

---

## 5. 持久化

| 项 | 规范 |
|:--|:--|
| 位置 | OrzMC **状态目录**（见 [`install-update.md`](install-update.md) §2）下 `auth.json` |
| 权限 | Unix：文件 `0600`、目录 `0700`；Windows：用户目录（`%LOCALAPPDATA%`） |
| 写入 | **原子写**（临时文件 + rename），失败不留半成品 |
| 加密 | **下限 = 文件权限保护**；可选叠加 OS 钥匙串，属实现细节，不影响本契约 |
| 日志 | 任何日志 / 错误信息 / `--json` **禁止**出现 token（见 §8） |

> 不把令牌放在游戏根目录（`--root-dir`），避免随世界/备份/分享外泄。

---

## 6. 刷新与失效

| 场景 | 规范动作 |
|:--|:--|
| MC token 剩余 `> skew` | 直接使用 |
| MC token 剩余 `<= skew`（skew 默认 `60s`） | 视为**需刷新**（`stale`） |
| MC token 已过期 | 用 `msa.refresh_token` 刷新 MSA → 重走 §2 ③④⑤ |
| 刷新被拒（`invalid_grant`） | 清除持久化令牌 → `E_AUTH_EXPIRED`，需重新登录 |
| 档案返回 `401` | 强制刷新一次；仍 `401` → `E_AUTH_NO_GAME` |

`authTokenState(expiresAt, now, skewSeconds=60)` → `valid` / `stale` / `expired`（见 §9）。

---

## 7. 错误分类

### 7.1 令牌端点错误（`authClassifyTokenError`）

| 上游 `error` | action | `code` |
|:--|:--|:--|
| `authorization_pending` | `wait` | — |
| `slow_down` | `slowDown` | — |
| `expired_token` | `fail` | `E_AUTH_EXPIRED` |
| `access_denied` / `authorization_declined` | `fail` | `E_AUTH_DENIED` |
| 其它 | `fail` | `E_AUTH` |

### 7.2 XSTS 错误（`authClassifyXstsError`）

`status != 200` 时读 `XErr`：

| XErr | `code` | 含义 |
|:--|:--|:--|
| `2148916233` | `E_AUTH_XBOX` | 该微软账号没有 Xbox 账号 |
| `2148916235` | `E_AUTH_XBOX` | 所在地区 Xbox Live 不可用 |
| `2148916238` | `E_AUTH_XBOX` | 未成年账号，需加入家庭组 |
| 其它 / 无 | `E_AUTH` | 其他认证失败 |

### 7.3 规范错误码（补充 [`cli-surface.md`](cli-surface.md) §6.1）

| `code` | 退出码 | 含义 |
|:--|:--:|:--|
| `E_AUTH` | 1 | 认证失败（通用） |
| `E_AUTH_NOT_CONFIGURED` | 1 | 未配置 `client_id`（离线/未注册阶段） |
| `E_AUTH_DENIED` | 1 | 用户拒绝授权 |
| `E_AUTH_EXPIRED` | 1 | 设备码过期 / refresh token 失效 |
| `E_AUTH_XBOX` | 1 | Xbox Live / XSTS 拒绝（无账号 / 地区 / 未成年） |
| `E_AUTH_NO_GAME` | 1 | 账号无 Minecraft 拥有权（profile 401） |

---

## 8. CLI 行为面

| 场景 | 规范 |
|:--|:--|
| `--auth` + 有有效持久化令牌 | 静默复用，不弹设备码；`source = cache` |
| `--auth` + 令牌 `stale`/过期 | 先刷新（`source = refresh`），失败再走设备码 |
| TTY + 无令牌 | 打印设备码 + `verification_uri`，按 `interval` 轮询 |
| **非 TTY + 无令牌** | **不读 stdin**：设备码/提示写 **stderr**，仍按 `interval` 轮询；受 `expires_in` 限制 |
| `--json` | 设备码/进度/日志一律 **stderr**；stdout **恰好一个**信封；`data` **不含任何 token** |
| Ctrl-C | `E_CANCELLED`，退出码 **130** |
| 用户名 | 认证成功后以档案 `name` 为准；`-u` 冲突则 warn 并以档案为准 |

`--json` 成功 `data`（`client` 命令）：

```jsonc
{ "authenticated": true, "uuid": "8-4-4-4-12", "name": "PlayerName",
  "expiresAt": 1760000000, "source": "cache" }   // source: cache|refresh|device_code
```

**启动参数注入**（见 [`data-model.md`](data-model.md) §8）：

| token | 离线 | 已认证 |
|:--|:--|:--|
| `auth_uuid` | 随机/占位 UUID | 档案 `uuid`（带连字符） |
| `auth_access_token` | `"0"` | MC `accessToken` |
| `auth_player_name` | `guest` / `-u` | 档案 `name` |
| `user_type` | `legacy` | `msa` |
| `auth_xuid` | `""` | （可选，当前留空） |

---

## 9. 一致性操作（conformance）

纯映射，**不打网络**；输入输出即 §3 表。fixtures 见 [`fixtures/auth/`](fixtures/README.md)。

| 操作 | 输入 | 输出 |
|:--|:--|:--|
| `authDeviceCodeRequest` | `clientId`、`scope?` | `{method,url,form}` |
| `authDeviceCodeResult` | `response` | `{deviceCode,userCode,verificationUri,expiresIn,interval,message}` |
| `authXboxRequest` | `msaAccessToken` | `{method,url,headers,body}` |
| `authXboxResult` | `response` | `{token,userHash}` |
| `authXstsRequest` | `xblToken`、`relyingParty?` | `{method,url,headers,body}` |
| `authXstsResult` | `response` | `{token,userHash}` |
| `authMinecraftLoginRequest` | `userHash`、`xstsToken` | `{method,url,headers,body}` |
| `authMinecraftLoginResult` | `response` | `{accessToken,expiresIn}` |
| `authProfileRequest` | `accessToken` | `{method,url,headers}` |
| `authProfileResult` | `response` | `{uuid,name}`（`uuid` 规范化为连字符形式） |
| `authTokenState` | `expiresAt`、`now`、`skewSeconds?` | `{state,remainingSeconds}`（`valid/stale/expired`） |
| `authClassifyTokenError` | `error` | `{action,code}`（`action: wait/slowDown/fail`） |
| `authClassifyXstsError` | `status`、`xerr?` | `{code}` |

---

## 10. 实现映射与待办

| 范围 | Python | Swift |
|:--|:--|:--|
| 纯映射 | `orzmc/core/auth.py` | `OrzMCKit/Sources/Game/Auth/AuthMapping.swift` |
| 数据形状 | `orzmc/domain/auth.py` | `Game/Auth/AuthModel.swift` |
| 令牌存储 | `orzmc/infra/auth_store.py` | `Game/Auth/AuthStore.swift` |
| 认证编排 | `orzmc/services/auth.py` | `Game/Auth/Authenticator.swift` |
| CLI 接线 | `orzmc_app/cli/app.py` `client --auth` | `OrzMC/Commands/ClientCommand.swift` |

**状态（2026-10-15）**：**离线部分已实现**——两端纯映射通过一致性样例（全量各 **76/76**，含 `auth/*` 20 例），
令牌存储/设备码编排/CLI `--auth` 已接线（未配置 `client_id` 时返回 `E_AUTH_NOT_CONFIGURED`）。
改动**保留在本地、尚未推送**。

**待办（`client_id` 依赖项，等维护者注册 Azure 应用后）**：

- [ ] 注册 Azure 公共客户端应用（`Supported account types = 组织目录 + 个人账号`，`Allow public client flows = Yes`），取得 `client_id`；
- [ ] 把 `client_id` 写入两套实现的内置默认值（当前仅支持 `ORZMC_AZURE_CLIENT_ID` 覆盖）；
- [ ] 真实账号 E2E（需账号拥有 Minecraft Java 版），记录到 `HANDOFF.md`。

> **`client_id` 是公开值**（公共客户端无 secret），可随代码提交；但它是应用身份，不要复用第三方值。
