# 一致性样例（Fixtures）

> **状态**：草案 `specVersion 0.1` ｜ 最后更新 2026-10-15
> 本目录是 [conformance.md](../conformance.md) 定义的**黄金样例**：`given → expect` 的纯计划断言。
> 运行器见 [`scripts/conformance/`](../../../scripts/conformance/README.md)。

## 运行

```bash
# 用规范参考适配器自检（验证样例自洽，应全绿）
python3 scripts/conformance/run.py --adapter "python3 scripts/conformance/reference.py"

# 列样例 / 只看某域
python3 scripts/conformance/run.py --list
python3 scripts/conformance/run.py --adapter "<cmd>" --filter cache
```

## 目录

| 目录 | 断言的操作 | 对应契约 |
|:--|:--|:--|
| `snapshots/` | —（钉住的离线输入） | — |
| `layout/` | `planLayout` | B4 路径 |
| `version-resolve/` | `resolveVersion` | B10 版本解析 |
| `java/` | `requiredJava` | B5 Java |
| `verify/` | `verifyArtifact` | B3 校验 |
| `cache/` | `cacheDecision` | B1 缓存 |
| `download/` | `planDownloadConcurrency` / `resolveConcurrency` | B2 并发 |
| `client-plan/` | `planClientLaunch` | B6 客户端启动 |
| `client-download/` | `planClientDownload` | data-model §9 / B2 下载清单 |
| `non-tty/` | `nonTtyDefaults` | B9 非 TTY |
| `progress/` | `normalizeProgress` | B8 进度 |
| `error/` | `expectError`（如 `E_UNSUPPORTED_TYPE`） | B11 错误 |
| `server-plan/` | `planServerDeploy` | data-model §9 / B7 |
| `server-launch/` | `planServerLaunch` | data-model §10 / B7 |
| `server-lifecycle/` | `normalizeExit` | B7 退出码归一 |
| `auth/` | `auth*`（见 [`auth.md`](../auth.md) §9） | 正版授权纯映射（设备码流程 / 令牌 / 错误） |
| `state/` | —（待补 `state.paths`） | 多前端共享落点（见 [`frontends.md`](../frontends.md) §2）：仅供将来用例比对，当前为声明性快照 |

## 快照（离线输入）

| 文件 | 内容 |
|:--|:--|
| `snapshots/version_manifest.json` | 精简 `version_manifest_v2`（含 release/snapshot） |
| `snapshots/versions/1.20.4.json` | 现代版（有 `arguments`、含 OS rules 库） |
| `snapshots/versions/1.16.5.json` | 旧版（`minecraftArguments`，无 `arguments`） |
| `snapshots/versions/no-java.json` | 无 `javaVersion`（测默认 8） |
| `snapshots/versions/conditional-1.20.4.json` | 含 features/os 门控 `arguments` 与未知 token |
| `snapshots/versions/legacy-natives.json` | legacy `natives` classifier + 无 `downloads` 的库（Maven 回退） |
| `snapshots/assets/5.json` | 紧凑资源索引（`client-download` 用，2 个对象） |

> 所有快照为**构造数据**，哈希/大小为占位值；样例离线运行、不打网络。

## 样例格式

见 [`conformance.md` §3](../conformance.md) 与 [`schema/fixture.schema.json`](schema/fixture.schema.json)。
断言支持**子集**：普通键递归子集、`*Contains` / `*NotContains` / `*Order` / `*Count` / `*Set`、点号路径（如 `tokens.assets_index_name`）、以及 `"absent": [路径...]`（声明字段必须不存在）。
失败用例用 `expectError.code` 断言。

## 新增样例

1. 选目录（area）与 `id`（`<area>/<描述>`）。
2. 需要新输入 → 在 `snapshots/` 钉住；否则复用。
3. 写 `given`（`operation` + 参数 + 快照）与 `expect`（子集断言）。
4. 先跑参考适配器（应绿），再跑各语言适配器（见 Phase 2 计划）。

## 接入状态

| 适配器 | 状态 |
|:--|:--:|
| 规范参考 `scripts/conformance/reference.py` | ☑ 76/76 |
| Python `python/orzmc/tests/conformance/adapter.py` | ☑ 76/76 |
| Swift `OrzMCKit` | ☑ 76/76 |

## 待补（Phase 2 后续）

- 服务端 Forge/Fabric 装载、natives 解压的样例。
- `planClientDownload` 的更多平台/legacy（`natives` classifier）组合。
- `auth/*`（正版授权）：两端纯映射已实现；真实登录 E2E 待 `client_id` 注册（见 [`auth.md`](../auth.md) §10）。
