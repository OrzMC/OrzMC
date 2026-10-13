# 一致性样例（Fixtures）

> **状态**：草案 `specVersion 0.1` ｜ 最后更新 2026-10-13
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
| `non-tty/` | `nonTtyDefaults` | B9 非 TTY |
| `progress/` | `normalizeProgress` | B8 进度 |
| `error/` | `expectError`（如 `E_UNSUPPORTED_TYPE`） | B11 错误 |

## 快照（离线输入）

| 文件 | 内容 |
|:--|:--|
| `snapshots/version_manifest.json` | 精简 `version_manifest_v2`（含 release/snapshot） |
| `snapshots/versions/1.20.4.json` | 现代版（有 `arguments`、含 OS rules 库） |
| `snapshots/versions/1.16.5.json` | 旧版（`minecraftArguments`，无 `arguments`） |
| `snapshots/versions/no-java.json` | 无 `javaVersion`（测默认 8） |

> 所有快照为**构造数据**，哈希/大小为占位值；样例离线运行、不打网络。

## 样例格式

见 [`conformance.md` §3](../conformance.md) 与 [`schema/fixture.schema.json`](schema/fixture.schema.json)。
断言支持**子集**：普通键递归子集、`*Contains` / `*NotContains` / `*Order` / `*Count` / `*Set`、点号路径（如 `tokens.assets_index_name`）。
失败用例用 `expectError.code` 断言。

## 新增样例

1. 选目录（area）与 `id`（`<area>/<描述>`）。
2. 需要新输入 → 在 `snapshots/` 钉住；否则复用。
3. 写 `given`（`operation` + 参数 + 快照）与 `expect`（子集断言）。
4. 先跑参考适配器（应绿），再跑各语言适配器（见 Phase 2 计划）。

## 接入状态

| 适配器 | 状态 |
|:--|:--:|
| 规范参考 `scripts/conformance/reference.py` | ☑ 26/26 |
| Python `python/orzmc/tests/conformance/adapter.py` | ☑ 26/26 |
| Swift `OrzMCKit` | ☐ 待接入 |

## 待补（Phase 2 后续）

- `server-plan/`（`planServerDeploy`）与 `server-lifecycle/`（B7）样例：待实现适配器具备纯计划入口后补。
- 服务端 Forge/Fabric 装载、natives 解压、asset 对象批量下载的样例。
- Swift 适配器接入本套件。
