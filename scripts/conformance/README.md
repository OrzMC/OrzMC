# 一致性运行器（Conformance Runner）

> spec-owned 工具（父仓库）。语言无关：用**同一批 fixtures** 驱动任意语言的适配器。

```
docs/spec/fixtures/**            黄金样例（given → expect）
scripts/conformance/run.py       运行器：发现样例、调适配器、子集比对、打印差异
scripts/conformance/reference.py 规范参考适配器（纯计划语义，验证样例自洽）
```

## 用法

```bash
# 自检：样例 vs 规范参考实现
python3 scripts/conformance/run.py --adapter "python3 scripts/conformance/reference.py"

# 列样例 / 过滤 / 严格（SKIP 计为失败）
python3 scripts/conformance/run.py --list
python3 scripts/conformance/run.py --adapter "<cmd>" --filter client-plan
python3 scripts/conformance/run.py --adapter "<cmd>" --strict
```

退出码：`0` 全部 PASS（或有 SKIP 且非 `--strict`）；`1` 有 FAIL（或 `--strict` 有 SKIP）。

## 适配器协议

- 运行器对**每个 fixture 调用一次**适配器：把请求 JSON 写入 stdin，读取 stdout 的响应 JSON。
- **请求** = fixture 的 `given` + `id` + `specVersion`：

  ```json
  { "id": "cache/fresh-hit", "specVersion": "0.1",
    "operation": "cacheDecision", "mtime": 1000, "ttl": 86400, "now": 4600,
    "refresh": false, "offline": false, "hasStale": true }
  ```

- **响应**：

  ```json
  { "ok": true,  "data": { "action": "hit" } }
  { "ok": false, "code": "E_UNSUPPORTED_TYPE", "message": "..." }
  ```

- `code = "E_UNSUPPORTED_OP"` → 运行器记为 **SKIP**（尚未实现该操作时用；`--strict` 视为失败）。
- 适配器**不得**打网络、不得触碰系统 Java、不得产生副作用（纯计划）。
- stdout 只输出**一个** JSON 对象；日志走 stderr。

## 规范操作（operation）

| operation | 输入要点 | 输出 |
|:--|:--|:--|
| `planLayout` | root/version/type/javaMajor/objectSha1/platform | 路径集合 |
| `resolveVersion` | channel/snapshot | `{id,channel,type}` |
| `requiredJava` | snapshot | `{majorVersion,distribution,runtimeKind}` |
| `verifyArtifact` | hashType/expectedSha1/dataUtf8 | `{valid}` |
| `cacheDecision` | mtime/ttl/now/refresh/offline/hasStale | `{action}` |
| `planDownloadConcurrency` | sizeBytes | `{mode,parts}` |
| `resolveConcurrency` | threads | `{concurrency}` |
| `planClientLaunch` | root/version/type/platform/options/snapshot | `ClientLaunchPlan` |
| `nonTtyDefaults` | snapshot/provided* | `{version,username,interactive,confirm}` |
| `normalizeProgress` | input | 归一化进度事件 |

完整语义以 `reference.py` 为准（它是规范的**可执行参照**）。

## 接入真实实现

| 语言 | 建议位置（在各自仓库内） | 适配器形态 |
|:--|:--|:--|
| Python | `orzmc/tests/conformance/adapter.py` | 复用 `domain/*`、`infra/cache.py` 等内部 API |
| Swift | `OrzMCKit/Sources/ConformanceAdapter`（或 Tests） | 复用 `Game`/`MojangAPI` 的**纯计划**入口 |

> 各实现运行器时通过 `--adapter "<该仓库内的命令>"` 指向自己的适配器，实现代码不落在父仓库。
